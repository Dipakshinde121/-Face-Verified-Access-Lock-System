import cv2
import face_recognition
import numpy as np
import time
import sys
from src.api_client import init_db, add_student, get_student_by_roll, log_event, ServerUnreachableError

def get_valid_input(prompt, error_msg="Input cannot be empty. Please try again."):
    """
    Prompts the user for input and ensures it is non-empty.
    """
    while True:
        value = input(prompt).strip()
        if value:
            return value
        print(f"[Validation Error] {error_msg}")

def main():
    print("=== Student Registration System ===")
    
    # Initialize the database if not already done
    init_db()
    
    # 1. Prompt for Roll Number and Name with validation
    roll_number = get_valid_input("Enter Roll Number (e.g. 21BCE001): ", "Roll number is required.")
    name = get_valid_input("Enter Student's Full Name: ", "Student name is required.")
    
    # 2. Check for duplicate roll number and warn the user
    existing_student = get_student_by_roll(roll_number)
    if existing_student:
        print(f"\n[WARNING] Roll number '{roll_number}' is already registered.")
        print(f"Details: Name: {existing_student['name']} | Registered On: {existing_student['registered_date']}")
        overwrite = input("Do you want to overwrite this registration? (y/n): ").strip().lower()
        if overwrite not in ['y', 'yes']:
            print("Registration cancelled by user.")
            sys.exit(0)
        print("Overwrite confirmed. Proceeding to camera capture...")
    
    print("\nInitializing camera...")
    # Open default webcam (index 0)
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("[Error] Could not open webcam. Please verify connection and permissions.")
        sys.exit(1)
        
    # Load Haar Cascade for real-time framing help
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    
    print("\nCamera opened. Look at the camera.")
    print(" - Press 'c' to capture photo and register.")
    print(" - Press 'q' to cancel registration.")
    
    status_text = ""
    status_color = (0, 0, 255) # Red default
    status_expiry = 0
    
    try:
        while True:
            ret, frame = cap.read()
            if not ret or frame is None:
                print("[Error] Failed to read frame from webcam.")
                break
                
            display_frame = frame.copy()
            h_h, w_h, _ = display_frame.shape
            
            # Run fast Haar Cascade for live visual framing aid (optional helper)
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = face_cascade.detectMultiScale(gray, 1.1, 5, minSize=(50, 50))
            
            # Draw framing rectangles around detected faces
            for (x, y, w, h) in faces:
                cv2.rectangle(display_frame, (x, y), (x + w, y + h), (255, 191, 0), 2) # Light blue/cyan box for framing
            
            # UI Overlays
            # Top dark bar for registering name
            cv2.rectangle(display_frame, (0, 0), (w_h, 45), (0, 0, 0), -1)
            cv2.putText(
                display_frame, 
                f"Registering: {name} ({roll_number})", 
                (15, 30), 
                cv2.FONT_HERSHEY_SIMPLEX, 
                0.7, 
                (255, 255, 255), 
                2, 
                cv2.LINE_AA
            )
            
            # Bottom dark bar for instructions
            cv2.rectangle(display_frame, (0, h_h - 45), (w_h, h_h), (0, 0, 0), -1)
            cv2.putText(
                display_frame, 
                "Press 'c' to Capture & Save | 'q' to Cancel", 
                (15, h_h - 15), 
                cv2.FONT_HERSHEY_SIMPLEX, 
                0.6, 
                (0, 255, 255), 
                1, 
                cv2.LINE_AA
            )
            
            # Handle temporary status messages (like errors / success)
            if status_text and time.time() < status_expiry:
                # Draw status background box
                cv2.rectangle(display_frame, (10, h_h - 90), (w_h - 10, h_h - 55), (0, 0, 0), -1)
                cv2.putText(
                    display_frame, 
                    status_text, 
                    (20, h_h - 68), 
                    cv2.FONT_HERSHEY_SIMPLEX, 
                    0.6, 
                    status_color, 
                    2, 
                    cv2.LINE_AA
                )
                
            cv2.imshow("Student Registration", display_frame)
            
            key = cv2.waitKey(1) & 0xFF
            
            # Press 'q' to cancel
            if key == ord('q'):
                print("Registration cancelled.")
                break
                
            # Press 'c' to capture
            elif key == ord('c'):
                print("\nCapturing photo...")
                # Freeze frame with a "Processing..." indicator
                processing_frame = display_frame.copy()
                cv2.rectangle(processing_frame, (10, h_h - 90), (w_h - 10, h_h - 55), (0, 0, 0), -1)
                cv2.putText(
                    processing_frame, 
                    "Processing... Please keep still", 
                    (20, h_h - 68), 
                    cv2.FONT_HERSHEY_SIMPLEX, 
                    0.6, 
                    (0, 165, 255), # Orange
                    2, 
                    cv2.LINE_AA
                )
                cv2.imshow("Student Registration", processing_frame)
                cv2.waitKey(100) # Give time for window refresh
                
                # Convert captured frame to RGB for face_recognition library
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                
                print("\nProcessing biometric data...")
                face_locations = face_recognition.face_locations(rgb_frame)
                num_faces = len(face_locations)
                
                if num_faces == 0:
                    print("[Capture Error] No face detected. Please adjust lighting and try again.")
                    status_text = "No face detected! Adjust lighting & retake."
                    status_color = (0, 0, 255) # Red
                    status_expiry = time.time() + 3.0 # Show for 3 seconds
                    
                elif num_faces > 1:
                    print(f"[Capture Error] Multiple faces detected ({num_faces}). Only one person allowed.")
                    status_text = f"Multiple faces detected ({num_faces})! Retake."
                    status_color = (0, 0, 255) # Red
                    status_expiry = time.time() + 3.0 # Show for 3 seconds
                    
                else: # Exactly 1 face
                    print("Face detected! Generating 128-d face encoding...")
                    face_location = face_locations[0]
                    encodings = face_recognition.face_encodings(rgb_frame, known_face_locations=[face_location])
                    
                    if not encodings:
                        print("[Capture Error] Failed to generate encoding for the face.")
                        status_text = "Encoding generation failed! Try again."
                        status_color = (0, 0, 255) # Red
                        status_expiry = time.time() + 3.0
                        continue
                        
                    face_encoding = encodings[0]
                    
                    # --- MFA PROVISIONING (TOTP) ---
                    import pyotp
                    import qrcode
                    
                    print("\n" + "="*50)
                    print("SECURITY SETUP: MULTI-FACTOR AUTHENTICATION (MFA)")
                    print("="*50)
                    print("1. Open Google Authenticator or Authy on your phone.")
                    print("2. Scan the QR code below to link your account.")
                    
                    # Generate a unique base32 secret for this student
                    totp_secret = pyotp.random_base32()
                    
                    # Create the provisioning URI
                    totp_uri = pyotp.totp.TOTP(totp_secret).provisioning_uri(
                        name=roll_number,
                        issuer_name="Lab Access Control"
                    )
                    
                    # Print QR code to terminal
                    qr = qrcode.QRCode(version=1, box_size=2, border=1)
                    qr.add_data(totp_uri)
                    qr.make(fit=True)
                    qr.print_ascii()
                    
                    print(f"\nIf you cannot scan the QR code, manually enter this setup key: {totp_secret}")
                    print("Make sure you save this in your authenticator app BEFORE proceeding!")
                    input("\nPress Enter to complete registration...")
                    
                    print(f"Saving to database for student '{name}' ({roll_number})...")
                    success = add_student(roll_number, name, face_encoding, totp_secret)
                    
                    if success:
                        log_event(roll_number, "REGISTRATION_SUCCESS")
                        print(f"SUCCESS: Student '{name}' (Roll Number: {roll_number}) registered successfully!")
                        
                        # Show success message overlay
                        success_frame = display_frame.copy()
                        cv2.rectangle(success_frame, (10, h_h - 90), (w_h - 10, h_h - 55), (0, 0, 0), -1)
                        cv2.putText(
                            success_frame, 
                            "Registration Successful!", 
                            (20, h_h - 68), 
                            cv2.FONT_HERSHEY_SIMPLEX, 
                            0.6, 
                            (0, 255, 0), # Green
                            2, 
                            cv2.LINE_AA
                        )
                        cv2.imshow("Student Registration", success_frame)
                        cv2.waitKey(1500) # Show success screen for 1.5 seconds
                        break
                    else:
                        print("[Database Error] Failed to write student data to the database.")
                        status_text = "Database write failed! Try again."
                        status_color = (0, 0, 255)
                        status_expiry = time.time() + 3.0
                        
    finally:
        # Clean up
        cap.release()
        cv2.destroyAllWindows()
        print("Registration process finished.")

if __name__ == "__main__":
    try:
        main()
    except ServerUnreachableError as e:
        print(f"\n[SECURITY] API Server is Unreachable: {e}")
        print("Registration is disabled until connection is restored.")
