import sys
import time
from datetime import datetime
from typing import Optional, Callable
from config import load_config
from src.api_client import (
    get_student_by_roll, 
    get_face_by_roll, 
    get_totp_secret_by_roll, 
    log_event, 
    ServerUnreachableError
)

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


def authenticate_student(
    roll_input: str,
    auth_mode: Optional[str] = None,
    totp_input_provider: Optional[Callable[[str], str]] = None,
    biometric_verifier: Optional[Callable] = None,
    config: Optional[dict] = None,
    failed_attempts: Optional[dict] = None
) -> tuple[bool, str, Optional[SessionState], Optional[float]]:
    """
    Core authentication gateway supporting fast 2FA (Roll + Live Biometrics)
    and strict 3FA Exam Mode (Roll + TOTP + Live Biometrics).
    Returns (success: bool, status_reason: str, session: SessionState | None, confidence: float | None).
    """
    if not roll_input:
        return False, "EMPTY_ROLL", None, None
        
    if failed_attempts is not None and failed_attempts.get(roll_input, 0) >= 3:
        return False, "LOCKED_OUT", None, None

    # Fetch student details from encrypted store
    student_info = get_student_by_roll(roll_input)
    if not student_info:
        return False, "UNREGISTERED", None, None

    face_encoding = get_face_by_roll(roll_input)
    if face_encoding is None:
        return False, "CORRUPT_ENCODING", None, None

    name = student_info['name']

    # Resolve configuration policy
    if config is None:
        config = load_config()
    raw_mode = auth_mode if auth_mode is not None else config.get("auth_mode", "2FA")
    if isinstance(raw_mode, str):
        auth_mode = raw_mode.strip().upper()
    else:
        auth_mode = "2FA"

    if auth_mode not in ("2FA", "3FA"):
        print(f"[Config Warning] Unrecognized auth_mode '{auth_mode}', defaulting to 2FA.")
        auth_mode = "2FA"

    tolerance = float(config.get("face_match_tolerance", 0.60))
    totp_window = int(config.get("totp_valid_window", 1))

    # --- MULTI-FACTOR AUTHENTICATION POLICY GATE ---
    if auth_mode == "3FA":
        print(f"\n[SECURITY] [3FA Exam Mode] Initiating Multi-Factor Authentication for {name}...")
        totp_secret = get_totp_secret_by_roll(roll_input)
        if not totp_secret:
            print(f"[Error] No TOTP secret found for '{roll_input}'. MFA is required.")
            print("Please re-register your profile to set up Google Authenticator.")
            return False, "NO_TOTP_SECRET", None, None

        import pyotp
        totp = pyotp.TOTP(totp_secret)
        if totp_input_provider is not None:
            user_code = totp_input_provider(name)
        else:
            user_code = input(f"Enter 6-digit MFA Code for {name}: ").strip()

        if not user_code or not totp.verify(user_code, valid_window=totp_window):
            print("\n[SECURITY ALERT] Invalid MFA Code! Access Denied.")
            log_event(roll_input, "LOGIN_DENIED_INVALID_TOTP", severity="MEDIUM")
            if failed_attempts is not None:
                failed_attempts[roll_input] = failed_attempts.get(roll_input, 0) + 1
            import alerting
            alerting.trigger_high_severity_alert(roll_input, "Failed MFA Code (Invalid TOTP)")
            return False, "INVALID_TOTP", None, None

        print("[Success] MFA Code Verified.")
    else:
        # Default 2FA Mode: Fast, engaging lab login
        print(f"\n[SECURITY] [2FA Mode] Fast Authentication Policy Active (Roll + Live Biometrics).")
        print("Skipping mobile TOTP prompt for daily lab session.")

    # --- STREAMLINED BIOMETRIC VERIFICATION (FACE + LIVENESS HUD) ---
    print(f"\n[SECURITY] Initiating Streamlined Face Verification & Anti-Spoofing for {name}...")
    if biometric_verifier is not None:
        bio_success, best_confidence, reason = biometric_verifier(
            name=name, expected_encoding=face_encoding, tolerance=tolerance
        )
    else:
        from liveness_check import run_streamlined_biometrics
        bio_success, best_confidence, reason = run_streamlined_biometrics(
            name=name, expected_encoding=face_encoding, tolerance=tolerance
        )

    if not bio_success:
        if reason == "CAMERA_FAILURE":
            print("[Error] Camera failure. Cannot verify face.")
            return False, "CAMERA_FAILURE", None, None
        elif reason == "NO_FACE":
            print("\n[SECURITY ALERT] No face detected at terminal!")
            log_event(roll_input, "LOGIN_DENIED_NO_FACE", severity="MEDIUM")
            if failed_attempts is not None:
                failed_attempts[roll_input] = failed_attempts.get(roll_input, 0) + 1
            return False, "NO_FACE", None, None
        elif reason == "MULTIPLE_FACES":
            print(f"\n[SECURITY ALERT] Multiple faces detected! Possible piggybacking attempt.")
            log_event(roll_input, "LOGIN_DENIED_MULTIPLE_FACES", severity="HIGH")
            if failed_attempts is not None:
                failed_attempts[roll_input] = failed_attempts.get(roll_input, 0) + 1
            return False, "MULTIPLE_FACES", None, None
        elif reason == "FACE_MISMATCH":
            print(f"\n[SECURITY ALERT] Face Mismatch! (Conf: {best_confidence:.2f}). Access Denied.")
            log_event(roll_input, "LOGIN_DENIED_FACE_MISMATCH", severity="HIGH", confidence_score=best_confidence)
            if failed_attempts is not None:
                failed_attempts[roll_input] = failed_attempts.get(roll_input, 0) + 1
            import alerting
            alerting.trigger_high_severity_alert(roll_input, f"Failed Face Match (Conf: {best_confidence:.2f})")
            return False, "FACE_MISMATCH", None, best_confidence
        elif reason in ("LIVENESS_TIMEOUT", "LIVENESS_IDENTITY_MISMATCH"):
            print("\n[SECURITY ALERT] Liveness check failed! Possible presentation attack.")
            log_event(roll_input, "LOGIN_DENIED_LIVENESS_FAIL", severity="HIGH", confidence_score=best_confidence)
            if failed_attempts is not None:
                failed_attempts[roll_input] = failed_attempts.get(roll_input, 0) + 1
            import alerting
            alerting.trigger_high_severity_alert(roll_input, "Failed Liveness Check (Possible Presentation/Spoofing Attack)")
            return False, reason, None, best_confidence
        else:
            print(f"\n[SECURITY ALERT] Biometric verification failed: {reason}")
            if failed_attempts is not None:
                failed_attempts[roll_input] = failed_attempts.get(roll_input, 0) + 1
            return False, reason, None, best_confidence

    # Reset failed attempts upon successful verification
    if failed_attempts is not None:
        failed_attempts[roll_input] = 0

    # Build active session
    active_session = SessionState(roll_input, name, face_encoding)

    # Forensic Audit Trail: Log LOGIN_2FA or LOGIN_3FA with severity INFO and confidence score
    login_event = f"LOGIN_{auth_mode}"
    log_event(roll_input, login_event, severity="INFO", confidence_score=best_confidence)

    # Log matching band for risk scoring
    if best_confidence > 0.60:
        print(f"[Success] Face Match HIGH CONFIDENCE ({best_confidence:.2f})")
        log_event(roll_input, "MATCH", severity="LOW", confidence_score=best_confidence)
    else:
        print(f"[Warning] Face Match MEDIUM CONFIDENCE ({best_confidence:.2f})")
        log_event(roll_input, "MATCH_LOW_CONFIDENCE", severity="MEDIUM", confidence_score=best_confidence)

    return True, "SUCCESS", active_session, best_confidence


def main():
    print("=== System Login ===")
    failed_attempts = {}

    while True:
        try:
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

            success, reason, active_session, conf = authenticate_student(
                roll_input,
                failed_attempts=failed_attempts
            )
            
            if not success or active_session is None:
                if reason == "UNREGISTERED":
                    print(f"[Error] Roll number '{roll_input}' not registered. Please register first.")
                elif reason == "CORRUPT_ENCODING":
                    print(f"[Error] Corrupted database entry for '{roll_input}': Face encoding missing.")
                continue

            name = active_session.name
            print(f"\n[Success] Welcome back, {name}!")
            print(active_session)
            print("Session active - Continuous authentication running in background.")
            
            # Start continuous verification
            from verify import ContinuousVerificationThread
            verification_thread = ContinuousVerificationThread(active_session)
            verification_thread.start()
            
            # Start system tray app
            from tray_app import SystemTrayApp
            print("\nMonitoring started in Background.")
            print("Check your System Tray (Taskbar) for controls.")
            tray_app = SystemTrayApp(active_session, verification_thread)
            
            try:
                tray_app.run()
            except KeyboardInterrupt:
                print(f"\nEnding session for {name}...")
                verification_thread.stop()
                if tray_app.icon:
                    tray_app.icon.stop()
                log_event(roll_input, "LOGOUT_OR_LOCK")
                print("Session terminated.")
                del active_session
                del verification_thread
                del tray_app
                continue

        except KeyboardInterrupt:
            print("\nExiting application.")
            sys.exit(0)
        except ServerUnreachableError as e:
            print(f"\n[SECURITY] API Server is Unreachable: {e}")
            print("System is operating in FAIL-CLOSED mode. Logins are disabled until connection is restored.")
            time.sleep(2)


if __name__ == "__main__":
    main()
