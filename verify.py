import threading
import time
import cv2
import face_recognition
import _thread
import os
import platform
import json
from src.database import log_event

def load_config():
    try:
        with open("config.json", "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {
            "verification_interval": 30,
            "grace_period_missed_checks": 2,
            "face_match_tolerance": 0.6,
            "max_pause_duration_seconds": 60
        }

class ContinuousVerificationThread(threading.Thread):
    def __init__(self, session_state):
        super().__init__()
        self.session_state = session_state
        
        # Load configurable policies
        self.config = load_config()
        self.check_interval = self.config.get("verification_interval", 30)
        self.max_missed_checks = self.config.get("grace_period_missed_checks", 2)
        self.tolerance = self.config.get("face_match_tolerance", 0.6)
        self.max_pause_duration = self.config.get("max_pause_duration_seconds", 60)
        
        self.daemon = True
        self.running = True
        self.missed_checks = 0
        
        # Anti-Tamper & Pause State
        self.is_paused = False
        self.pause_start_time = 0

    def stop(self):
        self.running = False

    def pause_monitoring(self):
        """Auditable policy override to temporarily pause webcam checks."""
        if not self.is_paused:
            self.is_paused = True
            self.pause_start_time = time.time()
            log_event(self.session_state.roll_number, "POLICY_OVERRIDE", severity="MEDIUM")

    def resume_monitoring(self):
        """Manually resumes monitoring."""
        if self.is_paused:
            self.is_paused = False
            self.pause_start_time = 0
            self.missed_checks = 0 # Reset grace period when resuming
            log_event(self.session_state.roll_number, "POLICY_RESUMED", severity="INFO")

    def run(self):
        # Initial sleep so we don't check instantly after login
        self._sleep_interval()
        
        while self.running:
            # --- FAIL-SAFE / ANTI-TAMPER CHECK ---
            if self.is_paused:
                if time.time() - self.pause_start_time > self.max_pause_duration:
                    self.is_paused = False
                    self.pause_start_time = 0
                    self.missed_checks = 0
                    log_event(self.session_state.roll_number, "AUTO_RESUME_FAILSAFE", severity="HIGH")
                else:
                    time.sleep(1)
                    continue

            # 1. Capture a fresh frame
            cap = cv2.VideoCapture(0)
            if not cap.isOpened():
                log_event(self.session_state.roll_number, "PERIODIC_CHECK_ERROR_CAMERA", severity="MEDIUM")
                self._sleep_interval()
                continue
                
            # Read a few frames to let the camera sensor adjust to lighting
            for _ in range(5):
                cap.read()
            ret, frame = cap.read()
            cap.release()

            if not ret or frame is None:
                log_event(self.session_state.roll_number, "PERIODIC_CHECK_ERROR_FRAME", severity="MEDIUM")
                self._sleep_interval()
                continue

            # 2. Process frame for face detection
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            face_locations = face_recognition.face_locations(rgb_frame)
            
            # --- THREAT MODEL A: No face detected (User stepped away) ---
            if len(face_locations) == 0:
                self.missed_checks += 1
                log_event(self.session_state.roll_number, f"PERIODIC_CHECK_NO_FACE (Missed: {self.missed_checks})", severity="INFO")
                
                if self.missed_checks >= self.max_missed_checks:
                    print(f"\n\n[SECURITY] Grace period expired. No face detected for {self.check_interval * self.max_missed_checks}s. Locking session.")
                    log_event(self.session_state.roll_number, "LOCK_NO_FACE_TIMEOUT", severity="LOW")
                    self.trigger_lock()
            else:
                # 3. Face(s) detected, extract encodings
                encodings = face_recognition.face_encodings(rgb_frame, known_face_locations=face_locations)
                match_found = False
                
                for face_encoding in encodings:
                    matches = face_recognition.compare_faces([self.session_state.face_encoding], face_encoding, tolerance=self.tolerance)
                    if matches[0]:
                        match_found = True
                        break

                # --- THREAT MODEL C: Face Matches (Authorized User) ---
                if match_found:
                    self.missed_checks = 0 # Reset grace period
                    log_event(self.session_state.roll_number, "PERIODIC_CHECK_SUCCESS", severity="INFO")
                    
                # --- THREAT MODEL B: Different Face (Impersonation Attempt) ---
                else:
                    print("\n\n[SECURITY ALERT] Unrecognized face detected at terminal! Locking immediately.")
                    log_event(self.session_state.roll_number, "LOCK_FACE_MISMATCH", severity="HIGH")
                    self.trigger_lock()

            # Wait for next interval if still running
            self._sleep_interval()

    def _sleep_interval(self):
        """Sleeps for the check interval, but can be interrupted quickly if stopped."""
        for _ in range(self.check_interval):
            if not self.running:
                break
            time.sleep(1)

    def _lock_os_workstation(self):
        """Executes the OS-level workstation lock."""
        sys_os = platform.system()
        try:
            if sys_os == "Windows":
                import ctypes
                ctypes.windll.user32.LockWorkStation()
            elif sys_os == "Linux":
                exit_code = os.system("dbus-send --type=method_call --dest=org.gnome.ScreenSaver /org/gnome/ScreenSaver org.gnome.ScreenSaver.Lock > /dev/null 2>&1")
                if exit_code != 0:
                    exit_code = os.system("loginctl lock-session > /dev/null 2>&1")
                if exit_code != 0:
                    os.system("xdg-screensaver lock > /dev/null 2>&1")
            elif sys_os == "Darwin":
                os.system("pmset displaysleepnow")
        except Exception as e:
            print(f"\n[Warning] Failed to execute OS lock command: {e}")

    def trigger_lock(self):
        """Forces the OS to lock and the main application to exit, securing the terminal."""
        self.running = False
        self._lock_os_workstation()
        # Interrupts the main thread cleanly
        _thread.interrupt_main()
