import sys
import time
from datetime import datetime
from src.api_client import get_student_by_roll, get_face_by_roll, log_event, init_db, ServerUnreachableError

class SessionState:
    """
    Stores the active user session data.
    Structured as a class so that future periodic verification
    scripts can easily access and validate the current state.
    """
    def __init__(self, roll_number, name, face_encoding):
        self.roll_number = roll_number
        self.name = name
        self.face_encoding = face_encoding
        self.login_time = datetime.now()
        
    def __str__(self):
        return f"Session: {self.name} ({self.roll_number}) - Started at {self.login_time.strftime('%Y-%m-%d %H:%M:%S')}"


def main():
    print("=== System Login ===")
    
    # Initialize DB just in case it hasn't been created yet
    init_db()
    
    failed_attempts = {}

    while True:
        try:
            # 1 & 2: Prompt and handle whitespace/empty inputs
            roll_input = input("\nEnter Roll Number to login (or 'q' to quit application): ").strip()
            
            if roll_input.lower() == 'q':
                print("Exiting application.")
                sys.exit(0)
                
            if not roll_input:
                print("[Error] Roll number cannot be empty. Please try again.")
                continue
                
            if failed_attempts.get(roll_input, 0) >= 3:
                print("\n[SECURITY] ACCOUNT LOCKED OUT. Too many failed attempts.")
                print("Brute-force protection enabled. Please contact administrator.")
                continue
                
            # Fetch student details (name, registered_date)
            student_info = get_student_by_roll(roll_input)
            
            # 3: Handle unregistered roll numbers
            if not student_info:
                print(f"[Error] Roll number '{roll_input}' not registered. Please register first.")
                continue
                
            # If we get here, student exists. Fetch their face encoding for the session
            face_encoding = get_face_by_roll(roll_input)
            if face_encoding is None:
                # Edge case handling in case DB entry is corrupted
                print(f"[Error] Corrupted database entry for '{roll_input}': Face encoding missing.")
                continue

            name = student_info['name']
            
            # --- MFA CHALLENGE (TOTP) ---
            print("\n[SECURITY] Initiating Multi-Factor Authentication...")
            import pyotp
            from src.api_client import get_totp_secret_by_roll
            
            totp_secret = get_totp_secret_by_roll(roll_input)
            if not totp_secret:
                print(f"[Error] No TOTP secret found for '{roll_input}'. MFA is required.")
                print("Please re-register your profile to set up Google Authenticator.")
                continue
                
            totp = pyotp.TOTP(totp_secret)
            user_code = input(f"Enter 6-digit MFA Code for {name}: ").strip()
            
            # valid_window=1 allows for 1 interval (30s) of clock drift for usability vs replay attack tradeoff
            if not totp.verify(user_code, valid_window=1):
                print("\n[SECURITY ALERT] Invalid MFA Code! Access Denied.")
                log_event(roll_input, "LOGIN_DENIED_INVALID_TOTP", severity="HIGH")
                failed_attempts[roll_input] = failed_attempts.get(roll_input, 0) + 1
                import alerting
                alerting.trigger_high_severity_alert(roll_input, "Failed MFA Code (Invalid TOTP)")
                continue
                
            print("[Success] MFA Code Verified.")
            
            # --- LIVENESS CHALLENGE (ANTI-SPOOFING) ---
            print(f"\n[SECURITY] Initiating Liveness Detection for {name}...")
            from liveness_check import run_liveness_challenge
            liveness_passed = run_liveness_challenge()
            
            if not liveness_passed:
                print("\n[SECURITY ALERT] Liveness check failed! Possible presentation attack.")
                log_event(roll_input, "LOGIN_DENIED_LIVENESS_FAIL", severity="HIGH")
                failed_attempts[roll_input] = failed_attempts.get(roll_input, 0) + 1
                
                # Dispatch real-time alert for this high-severity spoofing attempt
                import alerting
                alerting.trigger_high_severity_alert(roll_input, "Failed Liveness Check (Possible Presentation/Spoofing Attack)")
                continue
            
            # Reset failed attempts on success
            failed_attempts[roll_input] = 0
            
            # 4 & 5: Setup Session and Log Event
            active_session = SessionState(roll_input, name, face_encoding)
            log_event(roll_input, "LOGIN")
            
            print(f"\n[Success] Welcome back, {name}!")
            print(active_session)
            print("Session active - Continuous authentication running in background.")
            
            # Start continuous verification
            from verify import ContinuousVerificationThread
            verification_thread = ContinuousVerificationThread(active_session)
            verification_thread.start()
            
            # 6: Start system tray app
            from tray_app import SystemTrayApp
            print("\nMonitoring started in Background.")
            print("Check your System Tray (Taskbar) for controls.")
            tray_app = SystemTrayApp(active_session, verification_thread)
            
            try:
                # The pystray icon.run() blocks the main thread
                tray_app.run()
            except KeyboardInterrupt:
                # Handle Ctrl+C or security lock (raised by verification thread) cleanly
                print(f"\nEnding session for {name}...")
                verification_thread.stop()
                if tray_app.icon:
                    tray_app.icon.stop()
                log_event(roll_input, "LOGOUT_OR_LOCK")
                print("Session terminated.")
                
                # Explicitly tear down session state to prevent cross-user leakage (Session Fixation risk)
                del active_session
                del verification_thread
                del tray_app
                
                continue # Go back to main login prompt

        except KeyboardInterrupt:
            # Handle Ctrl+C at the main login prompt
            print("\nExiting application.")
            sys.exit(0)
        except ServerUnreachableError as e:
            print(f"\n[SECURITY] API Server is Unreachable: {e}")
            print("System is operating in FAIL-CLOSED mode. Logins are disabled until connection is restored.")
            time.sleep(2)

if __name__ == "__main__":
    main()
