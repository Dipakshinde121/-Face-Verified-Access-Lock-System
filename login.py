import sys
from datetime import datetime
from src.database import get_student_by_roll, get_face_by_roll, log_event, init_db

class SessionState:
    """
    Stores the active user session data.
    Structured as a class so that future periodic verification
    scripts (Day 3/4) can easily access and validate the current state.
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
                break # Go back to main login prompt

        except KeyboardInterrupt:
            # Handle Ctrl+C at the main login prompt
            print("\nExiting application.")
            sys.exit(0)

if __name__ == "__main__":
    main()
