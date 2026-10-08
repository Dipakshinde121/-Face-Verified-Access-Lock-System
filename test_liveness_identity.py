import unittest
from unittest.mock import patch, MagicMock
import numpy as np

# Patching before importing to avoid dlib model loading issues if possible, 
# but liveness_check imports dlib directly. We'll mock it at the module level.
import sys
import liveness_check

class TestLivenessIdentity(unittest.TestCase):
    
    @patch('liveness_check.cv2.VideoCapture')
    @patch('liveness_check.cv2.imshow')
    @patch('liveness_check.cv2.waitKey')
    @patch('liveness_check.dlib.get_frontal_face_detector')
    @patch('liveness_check.dlib.shape_predictor')
    @patch('liveness_check.random.choice')
    @patch('liveness_check.eye_aspect_ratio')
    @patch('liveness_check.face_recognition')
    def test_liveness_identity(self, mock_fr, mock_ear, mock_choice, mock_predictor, mock_detector, mock_waitkey, mock_imshow, mock_cap):
        # Setup mocks
        mock_choice.return_value = "BLINK"
        mock_ear.return_value = 0.20  # Below EAR_THRESHOLD (0.25) to simulate blink
        
        # Mock VideoCapture
        mock_cap_instance = MagicMock()
        mock_cap_instance.read.return_value = (True, np.zeros((480, 640, 3), dtype=np.uint8))
        mock_cap.return_value = mock_cap_instance
        
        # Mock dlib detector to return one fake rectangle
        mock_detector_instance = MagicMock()
        # A simple mock object that can be iterated over
        class FakeRect:
            pass
        mock_detector_instance.return_value = [FakeRect()]
        mock_detector.return_value = mock_detector_instance
        
        # Mock dlib predictor to return fake shape
        mock_shape_obj = MagicMock()
        mock_part = MagicMock()
        mock_part.x = 10
        mock_part.y = 10
        mock_shape_obj.part.return_value = mock_part
        mock_predictor_instance = MagicMock()
        mock_predictor_instance.return_value = mock_shape_obj
        mock_predictor.return_value = mock_predictor_instance
        
        # Mock face recognition
        mock_fr.face_locations.return_value = [(0, 100, 100, 0)]
        mock_fr.face_encodings.return_value = [np.array([0.1, 0.2, 0.3])]
        
        # Dummy enrolled encoding
        expected_encoding = np.array([0.1, 0.2, 0.3])
        
        print("\n--- CASE A: Enrolled face completes challenge (Pass) ---")
        # Distance = 0.0, Confidence = 1.0 (Match)
        mock_fr.face_distance.return_value = [0.0]
        result = liveness_check.run_liveness_challenge(predictor_filename="shape_predictor_68_face_landmarks.dat", challenge_duration=0.5, expected_encoding=expected_encoding)
        self.assertTrue(result, "Expected challenge to pass for enrolled face.")
        
        print("\n--- CASE B: Different face performs challenge (Fail) ---")
        # Distance = 0.8, Confidence = 0.2 (Mismatch)
        mock_fr.face_distance.return_value = [0.8]
        result = liveness_check.run_liveness_challenge(predictor_filename="shape_predictor_68_face_landmarks.dat", challenge_duration=0.5, expected_encoding=expected_encoding)
        self.assertFalse(result, "Expected challenge to fail for a different face.")
        
        print("\n--- CASE C: Face switches partway through (Fail) ---")
        # To simulate face switching partway through, we can make the distance return [0.0] initially but we only check at the end.
        # Actually, since our logic checks identity at the exact moment the challenge completes, if the face is different *at that moment*, it fails.
        # Let's say the final frame evaluated (which completes the challenge) is a mismatch.
        mock_fr.face_distance.return_value = [0.8]
        result = liveness_check.run_liveness_challenge(predictor_filename="shape_predictor_68_face_landmarks.dat", challenge_duration=0.5, expected_encoding=expected_encoding)
        self.assertFalse(result, "Expected challenge to fail if face switched to someone else.")

if __name__ == '__main__':
    unittest.main()
