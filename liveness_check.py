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

import face_recognition

def run_liveness_challenge(predictor_filename="shape_predictor_68_face_landmarks.dat", challenge_duration=4.0, expected_encoding=None):
    """
    Runs a randomized Challenge-Response anti-spoofing challenge.
    Reduces the time window to 4.0 seconds to defeat pre-recorded staging attacks.
    If expected_encoding is provided, it verifies the identity of the face performing the challenge.
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
                if expected_encoding is not None:
                    # Verify identity
                    face_locations = face_recognition.face_locations(rgb_frame)
                    if not face_locations:
                        print("\n[SECURITY ALERT] No face detected for identity confirmation.")
                        return False
                    
                    encodings = face_recognition.face_encodings(rgb_frame, known_face_locations=face_locations)
                    best_match = False
                    for enc in encodings:
                        dist = face_recognition.face_distance([expected_encoding], enc)[0]
                        if (1.0 - dist) > 0.60:
                            best_match = True
                            break
                            
                    if not best_match:
                        print("\n[SECURITY ALERT] Liveness identity mismatch! The face performing the challenge is not the enrolled student.")
                        cv2.putText(frame, "IDENTITY MISMATCH!", (10, 90),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                        cv2.imshow("Liveness Challenge (Anti-Spoofing)", frame)
                        cv2.waitKey(800)
                        return False
                        
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

def draw_hud_overlay(frame, main_text, sub_text=None, color=(0, 255, 0), time_left=None):
    """Draws a semi-transparent HUD banner with status text at the top of the camera frame."""
    if frame is None or not hasattr(frame, 'shape'):
        return frame
    h, w = frame.shape[:2]
    overlay = frame.copy()
    banner_height = 80 if sub_text else 52
    cv2.rectangle(overlay, (0, 0), (w, banner_height), (20, 20, 20), -1)
    cv2.addWeighted(overlay, 0.75, frame, 0.25, 0, frame)
    
    cv2.putText(frame, main_text, (15, 32), cv2.FONT_HERSHEY_SIMPLEX, 0.70, color, 2, cv2.LINE_AA)
    if sub_text:
        cv2.putText(frame, sub_text, (15, 65), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (220, 220, 220), 1, cv2.LINE_AA)
    if time_left is not None:
        t_str = f"{max(0.0, time_left):.1f}s"
        t_col = (0, 255, 0) if time_left > 2.0 else (0, 165, 255) if time_left > 1.0 else (0, 0, 255)
        cv2.putText(frame, t_str, (max(10, w - 85), 32), cv2.FONT_HERSHEY_SIMPLEX, 0.70, t_col, 2, cv2.LINE_AA)
    return frame

def run_streamlined_biometrics(
    name="Student",
    expected_encoding=None,
    tolerance=0.60,
    challenge_duration=4.0,
    face_detect_duration=4.0,
    predictor_filename="shape_predictor_68_face_landmarks.dat",
    cap=None
):
    """
    Unified camera window for Face Matching (128-d Euclidean distance) and Anti-Spoofing Liveness.
    Provides clear visual HUD feedback with green status overlays:
    - 'Authenticating Student...'
    - 'Face Verified (Score: X.XX)'
    - 'Liveness Confirmed'
    - 'Access Granted'
    Returns: (success: bool, confidence_score: float, reason: str)
    """
    base_dir = os.path.dirname(os.path.abspath(__file__))
    predictor_path = os.path.join(base_dir, predictor_filename)
    if not os.path.exists(predictor_path):
        print(f"\n[ERROR] Missing '{predictor_path}'!")
        return False, 0.0, "PREDICTOR_MISSING"
        
    detector = dlib.get_frontal_face_detector()
    predictor = dlib.shape_predictor(predictor_path)
    
    # Landmark indexes
    (lStart, lEnd) = (42, 48)
    (rStart, rEnd) = (36, 42)
    (mStart, mEnd) = (48, 68)
    
    EAR_THRESHOLD = 0.25  
    MAR_THRESHOLD = 0.50
    
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

    window_name = "Lab Access Verification"
    owns_cap = False
    if cap is None:
        cap = cv2.VideoCapture(0)
        owns_cap = True
        
    if not cap.isOpened():
        return False, 0.0, "CAMERA_FAILURE"

    def _show(f):
        if f is None:
            return
        try:
            cv2.imshow(window_name, f)
        except Exception:
            pass

    def _wait(ms):
        try:
            return cv2.waitKey(ms)
        except Exception:
            return -1

    try:
        # --- STAGE 1: Real-time Face Detection & Recognition ---
        face_match_start = time.time()
        best_confidence = 0.0
        face_found = False
        face_detected_any = False
        camera_error = False
        last_stage1_frame = None

        while time.time() - face_match_start < face_detect_duration:
            ret, frame = cap.read()
            if not ret or frame is None:
                camera_error = True
                break
                
            last_stage1_frame = frame
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            face_locations = face_recognition.face_locations(rgb_frame)
            
            if len(face_locations) == 0:
                draw_hud_overlay(frame, "Authenticating Student...", "Position face before camera", color=(0, 255, 255))
                _show(frame)
                _wait(1)
                continue
                
            if len(face_locations) > 1:
                draw_hud_overlay(frame, "MULTIPLE FACES DETECTED", "Piggybacking risk: Only 1 person allowed", color=(0, 0, 255))
                _show(frame)
                _wait(800)
                return False, 0.0, "MULTIPLE_FACES"

            face_detected_any = True
            encodings = face_recognition.face_encodings(rgb_frame, known_face_locations=face_locations)
            if not encodings:
                continue

            if expected_encoding is not None:
                dist = face_recognition.face_distance([expected_encoding], encodings[0])[0]
                conf = float(1.0 - dist)
                best_confidence = max(best_confidence, conf)
                if dist <= tolerance:
                    # Verified face!
                    face_found = True
                    draw_hud_overlay(frame, f"Face Verified (Score: {best_confidence:.2f})", "Initiating Anti-Spoofing Challenge...", color=(0, 255, 0))
                    _show(frame)
                    _wait(300)
                    break
                else:
                    draw_hud_overlay(frame, "Authenticating Student...", f"Matching... (Score: {conf:.2f})", color=(0, 255, 255))
                    _show(frame)
                    _wait(1)
            else:
                best_confidence = 1.0
                face_found = True
                draw_hud_overlay(frame, f"Face Verified (Score: {best_confidence:.2f})", "Initiating Anti-Spoofing Challenge...", color=(0, 255, 0))
                _show(frame)
                _wait(300)
                break

        if camera_error and not face_detected_any:
            return False, 0.0, "CAMERA_FAILURE"

        if not face_found:
            if face_detected_any:
                if last_stage1_frame is not None:
                    draw_hud_overlay(last_stage1_frame, f"Face Mismatch (Score: {best_confidence:.2f})", "Access Denied: Unrecognized User", color=(0, 0, 255))
                    _show(last_stage1_frame)
                    _wait(800)
                return False, best_confidence, "FACE_MISMATCH"
            else:
                return False, 0.0, "NO_FACE"

        # --- STAGE 2: Anti-Spoofing Challenge in the same camera window ---
        counter = 0
        consec_frames_required = 2
        challenge_start = time.time()
        liveness_passed = False
        last_valid_frame = None

        while time.time() - challenge_start < challenge_duration:
            ret, frame = cap.read()
            if not ret or frame is None:
                # Camera read failure / disconnect during challenge
                return False, best_confidence, "CAMERA_FAILURE"

            last_valid_frame = frame
            time_left = max(0.0, challenge_duration - (time.time() - challenge_start))
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            rects = detector(rgb_frame, 0)
            challenge_step_passed = False

            for rect in rects:
                shape_obj = predictor(rgb_frame, rect)
                shape = [(shape_obj.part(i).x, shape_obj.part(i).y) for i in range(68)]

                leftEye = shape[lStart:lEnd]
                rightEye = shape[rStart:rEnd]
                mouth = shape[mStart:mEnd]

                cv2.drawContours(frame, [cv2.convexHull(np.array(leftEye))], -1, (0, 255, 0), 1)
                cv2.drawContours(frame, [cv2.convexHull(np.array(rightEye))], -1, (0, 255, 0), 1)
                cv2.drawContours(frame, [cv2.convexHull(np.array(mouth))], -1, (255, 255, 0), 1)

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
                    if ratio > 1.5:
                        counter += 1
                    else:
                        counter = 0
                elif target_challenge == "TURN_RIGHT":
                    ratio = get_head_turn_ratio(shape)
                    if ratio < 0.6:
                        counter += 1
                    else:
                        counter = 0

                if counter >= consec_frames_required:
                    challenge_step_passed = True

            draw_hud_overlay(
                frame,
                f"Face Verified (Score: {best_confidence:.2f})",
                f"Challenge: {prompt_text}",
                color=(0, 255, 0),
                time_left=time_left
            )
            _show(frame)
            _wait(1)

            if challenge_step_passed:
                # Identity continuity confirmation
                if expected_encoding is not None:
                    face_locations = face_recognition.face_locations(rgb_frame)
                    if not face_locations:
                        return False, best_confidence, "LIVENESS_IDENTITY_MISMATCH"

                    encodings = face_recognition.face_encodings(rgb_frame, known_face_locations=face_locations)
                    best_match = False
                    for enc in encodings:
                        dist = face_recognition.face_distance([expected_encoding], enc)[0]
                        conf = float(1.0 - dist)
                        if dist <= tolerance:
                            best_match = True
                            best_confidence = max(best_confidence, conf)
                            break

                    if not best_match:
                        draw_hud_overlay(frame, "Identity Mismatch during Liveness!", "Possible Presentation Attack", color=(0, 0, 255))
                        _show(frame)
                        _wait(800)
                        return False, best_confidence, "LIVENESS_IDENTITY_MISMATCH"

                draw_hud_overlay(frame, "Liveness Confirmed", "Access Granted", color=(0, 255, 0))
                _show(frame)
                _wait(600)
                liveness_passed = True
                break

        if liveness_passed:
            return True, best_confidence, "SUCCESS"
        else:
            if last_valid_frame is not None:
                draw_hud_overlay(last_valid_frame, "Liveness Challenge Failed", "Timeout: No response detected", color=(0, 0, 255))
                _show(last_valid_frame)
                _wait(800)
            return False, best_confidence, "LIVENESS_TIMEOUT"

    finally:
        if owns_cap:
            cap.release()
            try:
                cv2.destroyAllWindows()
            except Exception:
                pass

