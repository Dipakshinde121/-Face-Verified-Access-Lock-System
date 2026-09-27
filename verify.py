import threading
import time
import cv2
import face_recognition
import _thread
import os
from src.api_client import log_event
from lock import lock_workstation
from config import load_config

class ContinuousVerificationThread(threading.Thread):
    def __init__(self, session_state):
        super().__init__()
        self.session_state = session_state
        
        # Load configurable policies from config module (TRD §6)
        self.config = load_config()
        self.check_interval = self.config.get("verification_interval", 30)
        self.max_missed_checks = self.config.get("grace_period_missed_checks", 2)
        self.tolerance = self.config.get("face_match_tolerance", 0.6)
        self.max_pause_duration = self.config.get("max_pause_duration_seconds", 300)
        
        self.daemon = True
        self.running = True
        self.missed_checks = 0
        self.stop_event = threading.Event()
        
        # Anti-Tamper & Pause State
        self.is_paused = False
        self.pause_start_time = 0
        
        # Concurrency Lock
        self.state_lock = threading.Lock()

    def stop(self):
        self.running = False
        self.stop_event.set()

    def pause_monitoring(self):
        """Auditable policy override to temporarily pause webcam checks (Schema §4)."""
        with self.state_lock:
            if not self.is_paused:
                self.is_paused = True
                self.pause_start_time = time.time()
                self._log_and_check("POLICY_OVERRIDE_PAUSE", severity="MEDIUM")

    def resume_monitoring(self):
        """Manually resumes monitoring."""
        with self.state_lock:
            if self.is_paused:
                self.is_paused = False
                self.pause_start_time = 0
                self.missed_checks = 0 # Reset grace period when resuming
                self._log_and_check("POLICY_RESUMED", severity="INFO")

    def _log_and_check(self, event, severity="INFO", confidence_score=None):
        """Wrapper for API logging that implements a strict FAIL-CLOSED policy."""
        success = log_event(
            self.session_state.roll_number, 
            event, 
            severity=severity, 
            confidence_score=confidence_score
        )
        if not success:
            print("\n[SECURITY] Central API Unreachable! Triggering Fail-Closed lockdown.")
            self.trigger_lock()

    def run(self):
        # Initial sleep so we don't check instantly after login
        self._sleep_interval()
        
        while self.running:
            # --- FAIL-SAFE / ANTI-TAMPER CHECK ---
            with self.state_lock:
                if self.is_paused:
                    if time.time() - self.pause_start_time > self.max_pause_duration:
                        self.is_paused = False
                        self.pause_start_time = 0
                        self.missed_checks = 0
                        self._log_and_check("AUTO_RESUME_FAILSAFE", severity="HIGH")
                    else:
                        time.sleep(1)
                        continue

            # 1. Capture a fresh frame
            cap = cv2.VideoCapture(0)
            if not cap.isOpened():
                self._log_and_check("PERIODIC_CHECK_ERROR_CAMERA", severity="MEDIUM")
                self._sleep_interval()
                continue
                
            try:
                # Read a few frames to let the camera sensor adjust to lighting
                for _ in range(5):
                    cap.read()
                ret, frame = cap.read()
            except Exception as e:
                print(f"[Error] Camera read failed: {e}")
                ret, frame = False, None
            finally:
                cap.release()

            if not ret or frame is None:
                self._log_and_check("PERIODIC_CHECK_ERROR_FRAME", severity="MEDIUM")
                self._sleep_interval()
                continue

            # 2. Process frame for face detection
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            face_locations = face_recognition.face_locations(rgb_frame)
            
            # --- THREAT MODEL A: No face detected (User stepped away) ---
            if len(face_locations) == 0:
                with self.state_lock:
                    self.missed_checks += 1
                    current_missed = self.missed_checks
                self._log_and_check(f"PERIODIC_CHECK_NO_FACE (Missed: {current_missed})", severity="INFO")
                
                if current_missed >= self.max_missed_checks:
                    print(f"\n\n[SECURITY] Grace period expired. No face detected for {self.check_interval * self.max_missed_checks}s. Locking session.")
                    self._log_and_check("LOCK_NO_FACE_TIMEOUT", severity="LOW")
                    self.trigger_lock()
                    
            # --- THREAT MODEL D: Multiple Faces (Piggybacking / Shoulder Surfing) ---
            elif len(face_locations) > 1:
                print(f"\n\n[SECURITY ALERT] Multiple faces detected! ({len(face_locations)} faces). Possible piggybacking attempt. Locking immediately.")
                self._log_and_check("LOCK_MULTIPLE_FACES", severity="HIGH")
                
                # Dispatch real-time alert
                import alerting
                alerting.trigger_high_severity_alert(self.session_state.roll_number, f"Piggybacking Attempt ({len(face_locations)} faces detected)")
                
                self.trigger_lock()
                
            else:
                # 3. Face(s) detected, extract encodings
                encodings = face_recognition.face_encodings(rgb_frame, known_face_locations=face_locations)
                
                best_confidence = 0.0
                
                for face_encoding_live in encodings:
                    dist = face_recognition.face_distance([self.session_state.face_encoding], face_encoding_live)[0]
                    conf = 1.0 - dist
                    if conf > best_confidence:
                        best_confidence = conf

                # --- CONFIDENCE RISK BANDING (TRD §3.3 & Schema §4) ---
                # HIGH CONFIDENCE (> 0.60): Normal Accept
                if best_confidence > 0.60:
                    with self.state_lock:
                        self.missed_checks = 0 # Reset grace period
                    self._log_and_check("MATCH", severity="LOW", confidence_score=best_confidence)
                    
                # MEDIUM CONFIDENCE (0.50 - 0.60): Accept but flag
                elif best_confidence >= 0.50:
                    with self.state_lock:
                        self.missed_checks = 0 # Reset grace period
                    self._log_and_check("MATCH_LOW_CONFIDENCE", severity="MEDIUM", confidence_score=best_confidence)
                    print(f"\n[Warning] Borderline face match detected during periodic check (Conf: {best_confidence:.2f}).")
                    
                # --- THREAT MODEL B: LOW CONFIDENCE (< 0.50): Impersonation Attempt ---
                else:
                    print(f"\n\n[SECURITY ALERT] Unrecognized face detected at terminal! (Conf: {best_confidence:.2f}). Locking immediately.")
                    self._log_and_check("LOCK_FACE_MISMATCH", severity="HIGH", confidence_score=best_confidence)
                    
                    # DISPATCH REAL-TIME ALERT (Fail-Safe: will not block if network is down)
                    import alerting
                    alerting.trigger_high_severity_alert(self.session_state.roll_number, f"Unrecognized Face (Conf: {best_confidence:.2f})")
                    
                    self.trigger_lock()

            # Wait for next interval or immediate exit if stopped
            if self.stop_event.wait(timeout=self.check_interval):
                break

    def trigger_lock(self):
        """Forces the OS to lock and the main application to exit, securing the terminal."""
        self.running = False
        self.stop_event.set()
        lock_workstation()
        # Interrupts the main thread cleanly
        _thread.interrupt_main()
