import cv2
import dlib
import numpy as np
import time
import os

def euclidean_dist(ptA, ptB):
    """Calculates the Euclidean distance between two points."""
    return np.linalg.norm(np.array(ptA) - np.array(ptB))

def eye_aspect_ratio(eye):
    """
    Calculates the Eye Aspect Ratio (EAR).
    Formula: (Vertical Dist 1 + Vertical Dist 2) / (2 * Horizontal Dist)
    When the eye is open, EAR is relatively constant. 
    When a blink occurs, EAR drops significantly toward zero.
    """
    # Vertical distances
    A = euclidean_dist(eye[1], eye[5])
    B = euclidean_dist(eye[2], eye[4])
    # Horizontal distance
    C = euclidean_dist(eye[0], eye[3])
    
    ear = (A + B) / (2.0 * C)
    return ear

def run_liveness_challenge(predictor_filename="shape_predictor_68_face_landmarks.dat", challenge_duration=5.0):
    """
    Runs a live webcam feed for a set duration, forcing the user to blink 
    to prove they are a live human and not a static photograph (Anti-Spoofing).
    
    Returns True if a blink is detected, False otherwise.
    """
    base_dir = os.path.dirname(os.path.abspath(__file__))
    predictor_path = os.path.join(base_dir, predictor_filename)
    if not os.path.exists(predictor_path):
        print(f"\n[ERROR] Missing '{predictor_path}'!")
        print("Please download it from: http://dlib.net/files/shape_predictor_68_face_landmarks.dat.bz2")
        print("Extract the .bz2 file and place the .dat file in this directory.")
        return False
        
    print("\nLoading facial landmark predictor...")
    detector = dlib.get_frontal_face_detector()
    predictor = dlib.shape_predictor(predictor_path)
    
    # Indexes for left and right eyes in the 68-point model
    (lStart, lEnd) = (42, 48)
    (rStart, rEnd) = (36, 42)
    
    EAR_THRESHOLD = 0.22  # Drop below this means eye is closed
    EAR_CONSEC_FRAMES = 2 # Must be closed for at least 2 consecutive frames
    
    counter = 0
    total_blinks = 0
    
    cap = cv2.VideoCapture(0)
    start_time = time.time()
    
    print("\n[LIVENESS CHALLENGE] Please look at the camera and BLINK to log in...")
    
    try:
        while time.time() - start_time < challenge_duration:
            ret, frame = cap.read()
            if not ret:
                break
                
            # Convert to RGB for dlib processing to avoid "Unsupported image type" errors
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            rects = detector(rgb_frame, 0)
            
            for rect in rects:
                shape = predictor(rgb_frame, rect)
                shape = [(shape.part(i).x, shape.part(i).y) for i in range(68)]
                
                leftEye = shape[lStart:lEnd]
                rightEye = shape[rStart:rEnd]
                
                leftEAR = eye_aspect_ratio(leftEye)
                rightEAR = eye_aspect_ratio(rightEye)
                
                # Average EAR of both eyes
                ear = (leftEAR + rightEAR) / 2.0
                
                # Draw eye contours for UI feedback
                leftEyeHull = cv2.convexHull(np.array(leftEye))
                rightEyeHull = cv2.convexHull(np.array(rightEye))
                cv2.drawContours(frame, [leftEyeHull], -1, (0, 255, 0), 1)
                cv2.drawContours(frame, [rightEyeHull], -1, (0, 255, 0), 1)
                
                if ear < EAR_THRESHOLD:
                    counter += 1
                else:
                    if counter >= EAR_CONSEC_FRAMES:
                        total_blinks += 1
                    counter = 0
                    
                cv2.putText(frame, "LIVENESS CHECK: Please BLINK", (10, 30),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
                            
            cv2.imshow("Liveness Challenge (Anti-Spoofing)", frame)
            cv2.waitKey(1)
            
            if total_blinks > 0:
                cv2.putText(frame, "LIVENESS CONFIRMED!", (10, 60),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                cv2.imshow("Liveness Challenge (Anti-Spoofing)", frame)
                cv2.waitKey(500)
                return True
                
        return False
    finally:
        cap.release()
        cv2.destroyAllWindows()
