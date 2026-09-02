import cv2
import dlib
import numpy as np
import time
import os
import random

def euclidean_dist(ptA, ptB):
    """Calculates the Euclidean distance between two points."""
    return np.linalg.norm(np.array(ptA) - np.array(ptB))

def eye_aspect_ratio(eye):
    """Calculates the Eye Aspect Ratio (EAR) for blink detection."""
    A = euclidean_dist(eye[1], eye[5])
    B = euclidean_dist(eye[2], eye[4])
    C = euclidean_dist(eye[0], eye[3])
    ear = (A + B) / (2.0 * C)
    return ear

def mouth_aspect_ratio(mouth):
    """Calculates the Mouth Aspect Ratio (MAR) for open mouth detection."""
    # Vertical distance (inner top lip to inner bottom lip)
    A = euclidean_dist(mouth[14], mouth[18])
    # Horizontal distance (outer left corner to outer right corner)
    C = euclidean_dist(mouth[0], mouth[6])
    mar = A / C
    return mar

def get_head_turn_ratio(shape):
    """
    Calculates horizontal head turn ratio based on the distance 
    from the nose tip (30) to the left edge of the jaw (0) vs right edge (16).
    """
    nose_x = shape[30][0]
    left_jaw_x = shape[0][0]
    right_jaw_x = shape[16][0]
    
    # Distance from nose to left side of the image (user's right jaw)
    dist_left = abs(nose_x - left_jaw_x)
    # Distance from nose to right side of the image (user's left jaw)
    dist_right = abs(right_jaw_x - nose_x)
    
    # Avoid division by zero
    if dist_right == 0:
        dist_right = 0.1
        
    return dist_left / dist_right

def run_liveness_challenge(predictor_filename="shape_predictor_68_face_landmarks.dat", challenge_duration=4.0):
    """
    Runs a randomized Challenge-Response anti-spoofing challenge.
    Reduces the time window to 4.0 seconds to defeat pre-recorded staging attacks.
    """
    base_dir = os.path.dirname(os.path.abspath(__file__))
    predictor_path = os.path.join(base_dir, predictor_filename)
    if not os.path.exists(predictor_path):
        print(f"\n[ERROR] Missing '{predictor_path}'!")
        return False
        
    print("\nLoading facial landmark predictor...")
    detector = dlib.get_frontal_face_detector()
    predictor = dlib.shape_predictor(predictor_path)
    
    # Landmark indexes
    (lStart, lEnd) = (42, 48)
    (rStart, rEnd) = (36, 42)
    (mStart, mEnd) = (48, 68)
    
    EAR_THRESHOLD = 0.25  
    MAR_THRESHOLD = 0.50
    # Head turn ratios: 
    # Ratio > 1.5 implies turning to look at their left (image right)
    # Ratio < 0.6 implies turning to look at their right (image left)
    
    challenges = ["BLINK", "OPEN_MOUTH", "TURN_LEFT", "TURN_RIGHT"]
    target_challenge = random.choice(challenges)
    
    if target_challenge == "BLINK":
        prompt_text = "Please BLINK"
    elif target_challenge == "OPEN_MOUTH":
        prompt_text = "Please OPEN YOUR MOUTH"
    elif target_challenge == "TURN_LEFT":
        prompt_text = "Please TURN HEAD TO YOUR LEFT"
    elif target_challenge == "TURN_RIGHT":
        prompt_text = "Please TURN HEAD TO YOUR RIGHT"
        
    counter = 0
    consec_frames_required = 2
    
    cap = cv2.VideoCapture(0)
    start_time = time.time()
    
    print(f"\n[LIVENESS CHALLENGE] {prompt_text}...")
    
    try:
        while time.time() - start_time < challenge_duration:
            ret, frame = cap.read()
            if not ret:
                break
                
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            rects = detector(rgb_frame, 0)
            
            challenge_passed = False
            
            for rect in rects:
                shape_obj = predictor(rgb_frame, rect)
                shape = [(shape_obj.part(i).x, shape_obj.part(i).y) for i in range(68)]
                
                # Draw facial contours for UI feedback
                leftEye = shape[lStart:lEnd]
                rightEye = shape[rStart:rEnd]
                mouth = shape[mStart:mEnd]
                
                cv2.drawContours(frame, [cv2.convexHull(np.array(leftEye))], -1, (0, 255, 0), 1)
                cv2.drawContours(frame, [cv2.convexHull(np.array(rightEye))], -1, (0, 255, 0), 1)
                cv2.drawContours(frame, [cv2.convexHull(np.array(mouth))], -1, (255, 255, 0), 1)
                
                # Check challenge condition
                if target_challenge == "BLINK":
                    ear = (eye_aspect_ratio(leftEye) + eye_aspect_ratio(rightEye)) / 2.0
                    if ear < EAR_THRESHOLD:
                        counter += 1
                    else:
                        counter = 0
                        
                elif target_challenge == "OPEN_MOUTH":
                    mar = mouth_aspect_ratio(mouth)
                    if mar > MAR_THRESHOLD:
                        counter += 1
                    else:
                        counter = 0
                        
                elif target_challenge == "TURN_LEFT":
                    ratio = get_head_turn_ratio(shape)
                    # Turning left means nose moves right in the image (ratio > 1.5)
                    if ratio > 1.5:
                        counter += 1
                    else:
                        counter = 0
                        
                elif target_challenge == "TURN_RIGHT":
                    ratio = get_head_turn_ratio(shape)
                    # Turning right means nose moves left in the image (ratio < 0.6)
                    if ratio < 0.6:
                        counter += 1
                    else:
                        counter = 0
                
                if counter >= consec_frames_required:
                    challenge_passed = True
                    
                time_left = max(0, challenge_duration - (time.time() - start_time))
                cv2.putText(frame, f"CHALLENGE: {prompt_text}", (10, 30),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
                cv2.putText(frame, f"Time left: {time_left:.1f}s", (10, 60),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
                            
            cv2.imshow("Liveness Challenge (Anti-Spoofing)", frame)
            cv2.waitKey(1)
            
            if challenge_passed:
                cv2.putText(frame, "LIVENESS CONFIRMED!", (10, 90),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                cv2.imshow("Liveness Challenge (Anti-Spoofing)", frame)
                cv2.waitKey(800)
                return True
                
        # If loop finishes without returning True, challenge failed
        return False
    finally:
        cap.release()
        cv2.destroyAllWindows()
