import cv2
import sys

def main():
    print("Initializing Haar Cascade Face Detector...")
    # Load OpenCV's built-in Haar Cascade XML for frontal face detection
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    
    if face_cascade.empty():
        print("[Error] Failed to load Haar Cascade XML file.")
        sys.exit(1)

    print("Opening webcam...")
    # Start capture on the default camera (index 0)
    cap = cv2.VideoCapture(0)
    
    if not cap.isOpened():
        print("[Error] Could not open webcam. Please verify connection and permissions.")
        sys.exit(1)
        
    print("\nWebcam started successfully!")
    print("Instructions:")
    print(" - Look at the camera. Bounding boxes will outline detected faces.")
    print(" - A counter will display the number of detected faces in the top-left corner.")
    print(" - Press 'q' key in the webcam window to exit the application.")
    
    try:
        while True:
            ret, frame = cap.read()
            if not ret or frame is None:
                print("[Error] Failed to read frame from webcam.")
                break
                
            # Convert frame to grayscale (Haar Cascades work on grayscale images)
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            # Detect faces in the frame
            # scaleFactor: how much the image size is reduced at each image scale
            # minNeighbors: how many neighbors each candidate rectangle should have to retain it
            # minSize: minimum possible object size to be detected
            faces = face_cascade.detectMultiScale(
                gray, 
                scaleFactor=1.1, 
                minNeighbors=5, 
                minSize=(40, 40)
            )
            
            # Draw bounding boxes around detected faces
            for (x, y, w, h) in faces:
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
            
            # Render the "Faces detected: N" overlay on the frame
            num_faces = len(faces)
            text = f"Faces detected: {num_faces}"
            
            # Put dark background rectangle behind text for better readability
            cv2.rectangle(frame, (8, 5), (320, 45), (0, 0, 0), -1)
            # Overlay text
            cv2.putText(
                frame, 
                text, 
                (15, 33), 
                cv2.FONT_HERSHEY_SIMPLEX, 
                1.0, 
                (0, 255, 0), 
                2, 
                cv2.LINE_AA
            )
            
            # Display the frame in a window
            cv2.imshow("Webcam Face Detection Test", frame)
            
            # Wait for key press; break if 'q' key is pressed
            if cv2.waitKey(1) & 0xFF == ord('q'):
                print("Exit requested by user.")
                break
                
    finally:
        # Release the camera and close all GUI windows
        print("Releasing camera resources...")
        cap.release()
        cv2.destroyAllWindows()
        print("Webcam closed.")

if __name__ == "__main__":
    main()
