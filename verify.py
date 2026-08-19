import threading
import time
import cv2
import face_recognition
import _thread
from src.database import log_event

class ContinuousVerificationThread(threading.Thread):
    def __init__(self, session_state, check_interval=30):
        super().__init__()
        self.session_state = session_state
        self.check_interval = check_interval
        self.daemon = True  # Allows thread to exit automatically when main program exits
        self.running = True
        self.missed_checks = 0
        self.max_missed_checks = 2

    def stop(self):
        self.running = False

    def run(self):
        # Initial sleep so we don't check instantly after login
        # We loop sleeping in 1s intervals so we can exit quickly if stop() is called
        for _ in range(self.check_interval):
            if not self.running: return
            time.sleep(1)
        
        while self.running:
            # 1. Capture a fresh frame
            # Opening and releasing the camera in the loop prevents the camera 
            # buffer from serving stale frames from 30 seconds ago.
            cap = cv2.VideoCapture(0)
            if not cap.isOpened():
                log_event(self.session_state.roll_number, "PERIODIC_CHECK_ERROR_CAMERA")
                self._sleep_interval()
                continue
                
            # Read a few frames to let the camera sensor adjust to lighting
            # NOTE: Poor lighting is a major cause of False Rejection Rates (FRR)
            for _ in range(5):
                cap.read()
            ret, frame = cap.read()
            cap.release()

            if not ret or frame is None:
                log_event(self.session_state.roll_number, "PERIODIC_CHECK_ERROR_FRAME")
                self._sleep_interval()
                continue

            # 2. Process frame for face detection
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            face_locations = face_recognition.face_locations(rgb_frame)
            
            # --- THREAT MODEL A: No face detected (User stepped away) ---
            if len(face_locations) == 0:
                self.missed_checks += 1
                log_event(self.session_state.roll_number, f"PERIODIC_CHECK_NO_FACE (Missed: {self.missed_checks})")
                
                if self.missed_checks >= self.max_missed_checks:
                    print(f"\n\n[SECURITY] Grace period expired. No face detected for {self.check_interval * self.max_missed_checks}s. Locking session.")
                    log_event(self.session_state.roll_number, "SESSION_LOCKED_TIMEOUT")
                    self.trigger_lock()
            else:
                # 3. Face(s) detected, extract encodings
                encodings = face_recognition.face_encodings(rgb_frame, known_face_locations=face_locations)
                match_found = False
                
                for face_encoding in encodings:
                    # Compare using 0.6 tolerance (industry standard baseline for this library)
                    matches = face_recognition.compare_faces([self.session_state.face_encoding], face_encoding, tolerance=0.6)
                    if matches[0]:
                        match_found = True
                        break

                # --- THREAT MODEL C: Face Matches (Authorized User) ---
                if match_found:
                    self.missed_checks = 0 # Reset grace period
                    log_event(self.session_state.roll_number, "PERIODIC_CHECK_SUCCESS")
                    
                # --- THREAT MODEL B: Different Face (Impersonation Attempt) ---
                else:
                    print("\n\n[SECURITY ALERT] Unrecognized face detected at terminal! Locking immediately.")
                    log_event(self.session_state.roll_number, "SESSION_LOCKED_IMPERSONATION")
                    self.trigger_lock()

            # Wait for next interval if still running
            self._sleep_interval()

    def _sleep_interval(self):
        """Sleeps for the check interval, but can be interrupted quickly if stopped."""
        for _ in range(self.check_interval):
            if not self.running:
                break
            time.sleep(1)

    def trigger_lock(self):
        """Forces the main application to exit, securing the terminal."""
        self.running = False
        # Interrupts the main thread (which is likely blocked on input()) by raising a KeyboardInterrupt
        _thread.interrupt_main()
