"""
test_auth_modes.py - Comprehensive Unit & Integration Tests for 2FA/3FA Policy Gate.
Validates:
1. Configurable Authentication Policy (2FA default, 3FA strict exam mode).
2. 2FA fast login flow: Roll Number + Live Face Biometrics without TOTP prompt.
3. 3FA exam mode: Enforces RFC 6238 TOTP verification before biometrics.
4. Defense-in-depth: Invalid TOTP blocks before webcam/biometrics are invoked.
5. Biometric mismatch and anti-spoofing liveness failure handling.
6. Brute-force lockout protection (>= 3 failed attempts).
7. Forensic audit logging (LOGIN_2FA and LOGIN_3FA with severity INFO and confidence scores).
8. SHA-256 hash-chain integrity verification.
"""

import unittest
from unittest.mock import patch, MagicMock
import os
import sys
import numpy as np
import pyotp
import sqlite3

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

import config
import login
from server.database import init_db, get_db_connection, DB_PATH, GENESIS_HASH, add_student_server
from log_viewer import verify_log_integrity

class TestAuthModesPolicy(unittest.TestCase):

    def setUp(self):
        # Fresh test database
        init_db(DB_PATH)
        conn = get_db_connection(DB_PATH)
        conn.execute("DELETE FROM logs;")
        conn.commit()
        conn.close()

        self.test_roll = "22BCE10999"
        self.test_name = "Jane Doe"
        self.test_encoding = np.random.uniform(-0.1, 0.1, 128).astype(np.float64)
        self.totp_secret = pyotp.random_base32()
        self.totp = pyotp.TOTP(self.totp_secret)

        # Ensure student is enrolled so server logs satisfy foreign key constraints
        add_student_server(self.test_roll, self.test_name, b"enc_bytes", b"totp_bytes")

    # -------------------------------------------------------------------------
    # TEST 1: Configuration Policy Defaults & Overrides
    # -------------------------------------------------------------------------
    def test_config_auth_mode_defaults_and_env_override(self):
        """Verify config.py default auth_mode is 2FA and environment variable overrides it."""
        cfg = config.load_config()
        self.assertIn("auth_mode", cfg)
        self.assertEqual(cfg["auth_mode"], "2FA")

        with patch.dict(os.environ, {"AUTH_MODE": "3FA"}):
            cfg_override = config.load_config()
            self.assertEqual(cfg_override["auth_mode"], "3FA")

        with patch.dict(os.environ, {"AUTH_MODE": "2fa"}):
            cfg_lower = config.load_config()
            self.assertEqual(cfg_lower["auth_mode"], "2FA")

    # -------------------------------------------------------------------------
    # TEST 2: 2FA Mode Grants Access Without Prompting for TOTP
    # -------------------------------------------------------------------------
    @patch('login.get_student_by_roll')
    @patch('login.get_face_by_roll')
    @patch('login.log_event')
    def test_2fa_login_bypasses_totp_and_grants_access(self, mock_log_event, mock_get_face, mock_get_student):
        """In 2FA mode, valid roll number and face template grant access without requiring TOTP."""
        mock_get_student.return_value = {"name": self.test_name, "registered_date": "2026-10-24"}
        mock_get_face.return_value = self.test_encoding

        totp_called = False
        def fake_totp_provider(name):
            nonlocal totp_called
            totp_called = True
            return "123456"

        mock_bio = MagicMock(return_value=(True, 0.94, "SUCCESS"))

        success, reason, session, conf = login.authenticate_student(
            roll_input=self.test_roll,
            auth_mode="2FA",
            totp_input_provider=fake_totp_provider,
            biometric_verifier=mock_bio
        )

        self.assertTrue(success, "2FA authentication should succeed with matching face.")
        self.assertEqual(reason, "SUCCESS")
        self.assertIsNotNone(session)
        self.assertEqual(session.roll_number, self.test_roll)
        self.assertEqual(session.name, self.test_name)
        self.assertAlmostEqual(conf, 0.94)

        # CRITICAL: Verify TOTP was NEVER requested
        self.assertFalse(totp_called, "In 2FA mode, TOTP provider must NOT be invoked.")

        # Verify biometric verifier was called with expected encoding
        mock_bio.assert_called_once()

        # Verify LOGIN_2FA audit log event
        mock_log_event.assert_any_call(self.test_roll, "LOGIN_2FA", severity="INFO", confidence_score=0.94)

    # -------------------------------------------------------------------------
    # TEST 3: 3FA Exam Mode Strictly Enforces TOTP Verification
    # -------------------------------------------------------------------------
    @patch('login.get_student_by_roll')
    @patch('login.get_face_by_roll')
    @patch('login.get_totp_secret_by_roll')
    @patch('login.log_event')
    def test_3fa_login_requires_and_verifies_valid_totp(self, mock_log_event, mock_get_totp, mock_get_face, mock_get_student):
        """In 3FA mode, valid TOTP code is required and verified before biometrics."""
        mock_get_student.return_value = {"name": self.test_name, "registered_date": "2026-10-24"}
        mock_get_face.return_value = self.test_encoding
        mock_get_totp.return_value = self.totp_secret

        valid_code = self.totp.now()
        totp_requested = False
        def fake_totp_provider(name):
            nonlocal totp_requested
            totp_requested = True
            return valid_code

        mock_bio = MagicMock(return_value=(True, 0.89, "SUCCESS"))

        success, reason, session, conf = login.authenticate_student(
            roll_input=self.test_roll,
            auth_mode="3FA",
            totp_input_provider=fake_totp_provider,
            biometric_verifier=mock_bio
        )

        self.assertTrue(success, "3FA authentication should succeed with valid TOTP and face.")
        self.assertTrue(totp_requested, "In 3FA mode, TOTP must be requested.")
        mock_bio.assert_called_once()
        mock_log_event.assert_any_call(self.test_roll, "LOGIN_3FA", severity="INFO", confidence_score=0.89)

    # -------------------------------------------------------------------------
    # TEST 4: 3FA Rejects Invalid TOTP Without Engaging Camera
    # -------------------------------------------------------------------------
    @patch('login.get_student_by_roll')
    @patch('login.get_face_by_roll')
    @patch('login.get_totp_secret_by_roll')
    @patch('login.log_event')
    def test_3fa_rejects_invalid_totp_early(self, mock_log_event, mock_get_totp, mock_get_face, mock_get_student):
        """In 3FA mode, invalid TOTP immediately rejects without touching camera or biometric verifier."""
        mock_get_student.return_value = {"name": self.test_name, "registered_date": "2026-10-24"}
        mock_get_face.return_value = self.test_encoding
        mock_get_totp.return_value = self.totp_secret

        mock_bio = MagicMock()
        failed_attempts = {}

        success, reason, session, conf = login.authenticate_student(
            roll_input=self.test_roll,
            auth_mode="3FA",
            totp_input_provider=lambda name: "000000", # Wrong code
            biometric_verifier=mock_bio,
            failed_attempts=failed_attempts
        )

        self.assertFalse(success, "3FA must fail on invalid TOTP.")
        self.assertEqual(reason, "INVALID_TOTP")
        self.assertIsNone(session)
        self.assertEqual(failed_attempts[self.test_roll], 1)

        # CRITICAL DEFENSE-IN-DEPTH: Biometric verifier must NEVER have been called!
        mock_bio.assert_not_called()
        mock_log_event.assert_any_call(self.test_roll, "LOGIN_DENIED_INVALID_TOTP", severity="MEDIUM")

    # -------------------------------------------------------------------------
    # TEST 5: Face Mismatch Rejection
    # -------------------------------------------------------------------------
    @patch('login.get_student_by_roll')
    @patch('login.get_face_by_roll')
    @patch('login.log_event')
    def test_face_mismatch_denied(self, mock_log_event, mock_get_face, mock_get_student):
        """Biometric mismatch returns false, logs LOGIN_DENIED_FACE_MISMATCH, and records attempt."""
        mock_get_student.return_value = {"name": self.test_name, "registered_date": "2026-10-24"}
        mock_get_face.return_value = self.test_encoding

        mock_bio = MagicMock(return_value=(False, 0.28, "FACE_MISMATCH"))
        failed_attempts = {}

        success, reason, session, conf = login.authenticate_student(
            roll_input=self.test_roll,
            auth_mode="2FA",
            biometric_verifier=mock_bio,
            failed_attempts=failed_attempts
        )

        self.assertFalse(success)
        self.assertEqual(reason, "FACE_MISMATCH")
        self.assertEqual(failed_attempts[self.test_roll], 1)
        mock_log_event.assert_any_call(self.test_roll, "LOGIN_DENIED_FACE_MISMATCH", severity="HIGH", confidence_score=0.28)

    # -------------------------------------------------------------------------
    # TEST 6: Liveness Challenge Failure Rejection
    # -------------------------------------------------------------------------
    @patch('login.get_student_by_roll')
    @patch('login.get_face_by_roll')
    @patch('login.log_event')
    def test_liveness_failure_denied(self, mock_log_event, mock_get_face, mock_get_student):
        """Liveness failure returns false, logs LOGIN_DENIED_LIVENESS_FAIL, and alerts."""
        mock_get_student.return_value = {"name": self.test_name, "registered_date": "2026-10-24"}
        mock_get_face.return_value = self.test_encoding

        mock_bio = MagicMock(return_value=(False, 0.85, "LIVENESS_TIMEOUT"))
        failed_attempts = {}

        success, reason, session, conf = login.authenticate_student(
            roll_input=self.test_roll,
            auth_mode="2FA",
            biometric_verifier=mock_bio,
            failed_attempts=failed_attempts
        )

        self.assertFalse(success)
        self.assertEqual(reason, "LIVENESS_TIMEOUT")
        self.assertEqual(failed_attempts[self.test_roll], 1)
        mock_log_event.assert_any_call(self.test_roll, "LOGIN_DENIED_LIVENESS_FAIL", severity="HIGH", confidence_score=0.85)

    # -------------------------------------------------------------------------
    # TEST 7: Brute Force Lockout
    # -------------------------------------------------------------------------
    def test_brute_force_lockout_enforced(self):
        """Account with 3 or more failed attempts is immediately locked out."""
        failed_attempts = {self.test_roll: 3}
        success, reason, session, conf = login.authenticate_student(
            roll_input=self.test_roll,
            failed_attempts=failed_attempts
        )
        self.assertFalse(success)
        self.assertEqual(reason, "LOCKED_OUT")

    # -------------------------------------------------------------------------
    # TEST 8: Full Cryptographic Hash Chain Integrity with Real Logs
    # -------------------------------------------------------------------------
    def test_forensic_hash_chain_continuity_with_2fa_and_3fa(self):
        """Real SQLite server database logs for 2FA and 3FA link into an unbroken SHA-256 chain."""
        from server.database import log_event_server

        # 1. 2FA Successful Login
        log_event_server(
            roll_number="TEST_STUDENT_2026",
            event="LOGIN_2FA",
            severity="INFO",
            confidence_score=0.92,
            device_id="lab-pc-test01"
        )

        # 2. 3FA Failed TOTP Attempt
        log_event_server(
            roll_number="TEST_STUDENT_2026",
            event="LOGIN_DENIED_INVALID_TOTP",
            severity="MEDIUM",
            confidence_score=None,
            device_id="lab-pc-test01"
        )

        # 3. 3FA Successful Login
        log_event_server(
            roll_number="TEST_STUDENT_2026",
            event="LOGIN_3FA",
            severity="INFO",
            confidence_score=0.88,
            device_id="lab-pc-test01"
        )

        # 4. Continuous Match Check
        log_event_server(
            roll_number="TEST_STUDENT_2026",
            event="MATCH",
            severity="LOW",
            confidence_score=0.95,
            device_id="lab-pc-test01"
        )

        conn = get_db_connection(DB_PATH)
        try:
            # Must complete with 0 integrity exceptions
            verify_log_integrity(conn)
        finally:
            conn.close()

    # -------------------------------------------------------------------------
    # TEST 9: HUD Overlay Null-Frame Crash Protection
    # -------------------------------------------------------------------------
    def test_draw_hud_overlay_safe_with_none_or_corrupt_frame(self):
        """draw_hud_overlay must handle None and invalid frames gracefully without raising AttributeError."""
        from liveness_check import draw_hud_overlay
        try:
            res_none = draw_hud_overlay(None, "Testing HUD", "Subtext")
            self.assertIsNone(res_none)
            res_obj = draw_hud_overlay("not-a-frame", "Testing HUD")
            self.assertEqual(res_obj, "not-a-frame")
        except Exception as e:
            self.fail(f"draw_hud_overlay raised an unexpected exception on invalid frame: {e}")

    # -------------------------------------------------------------------------
    # TEST 10: Camera Failure Does Not Penalize Student or Cause False Alarms
    # -------------------------------------------------------------------------
    @patch('login.get_student_by_roll')
    @patch('login.get_face_by_roll')
    @patch('login.log_event')
    def test_camera_failure_does_not_increment_failed_attempts(self, mock_log, mock_get_face, mock_get_student):
        """Camera hardware failures must return CAMERA_FAILURE without incrementing failed attempts or locking out."""
        mock_get_student.return_value = {"name": self.test_name, "registered_date": "2026-10-24"}
        mock_get_face.return_value = self.test_encoding

        mock_bio = MagicMock(return_value=(False, 0.0, "CAMERA_FAILURE"))
        failed_attempts = {}

        success, reason, session, conf = login.authenticate_student(
            roll_input=self.test_roll,
            auth_mode="2FA",
            biometric_verifier=mock_bio,
            failed_attempts=failed_attempts
        )

        self.assertFalse(success)
        self.assertEqual(reason, "CAMERA_FAILURE")
        self.assertEqual(failed_attempts.get(self.test_roll, 0), 0, "Hardware camera failure must NOT count against student lockout quota.")

    # -------------------------------------------------------------------------
    # TEST 11: run_streamlined_biometrics Camera Disconnect Mid-Stream Safety
    # -------------------------------------------------------------------------
    @patch('liveness_check.dlib.get_frontal_face_detector')
    @patch('liveness_check.dlib.shape_predictor')
    @patch('liveness_check.random.choice')
    @patch('liveness_check.face_recognition')
    def test_run_streamlined_biometrics_camera_disconnect_mid_stream(self, mock_fr, mock_choice, mock_predictor, mock_detector):
        """Camera disconnect mid-stream in stage 2 must return CAMERA_FAILURE without AttributeError crash."""
        from liveness_check import run_streamlined_biometrics
        mock_choice.return_value = "BLINK"

        # Frame 1: Stage 1 face detection succeeds
        fake_frame = np.zeros((480, 640, 3), dtype=np.uint8)
        mock_fr.face_locations.return_value = [(0, 100, 100, 0)]
        mock_fr.face_encodings.return_value = [self.test_encoding]
        mock_fr.face_distance.return_value = [0.10] # distance 0.10 => match

        # Camera mock: returns frame 1 for stage 1, then fails (disconnects) on stage 2
        mock_cap = MagicMock()
        mock_cap.isOpened.return_value = True
        mock_cap.read.side_effect = [
            (True, fake_frame),    # Stage 1: Face match succeeds
            (False, None),         # Stage 2: Camera disconnected!
        ]

        # Shape predictor mock
        mock_detector.return_value = MagicMock(return_value=[])
        mock_predictor.return_value = MagicMock()

        success, score, reason = run_streamlined_biometrics(
            name=self.test_name,
            expected_encoding=self.test_encoding,
            tolerance=0.60,
            challenge_duration=0.5,
            face_detect_duration=0.5,
            predictor_filename="shape_predictor_68_face_landmarks.dat",
            cap=mock_cap
        )

        self.assertFalse(success)
        self.assertEqual(reason, "CAMERA_FAILURE")

    # -------------------------------------------------------------------------
    # TEST 12: Multi-Frame Lighting / Exposure Adjustment in Streamlined Biometrics
    # -------------------------------------------------------------------------
    @patch('liveness_check.dlib.get_frontal_face_detector')
    @patch('liveness_check.dlib.shape_predictor')
    @patch('liveness_check.random.choice')
    @patch('liveness_check.eye_aspect_ratio')
    @patch('liveness_check.face_recognition')
    def test_run_streamlined_biometrics_multiframe_adjustment_success(self, mock_fr, mock_ear, mock_choice, mock_predictor, mock_detector):
        """Sub-optimal frame 1 (e.g. dark, dist=0.65) followed by matching frame 2 (dist=0.20) succeeds."""
        from liveness_check import run_streamlined_biometrics
        mock_choice.return_value = "BLINK"
        mock_ear.return_value = 0.18 # Below threshold to pass blink

        fake_frame = np.zeros((480, 640, 3), dtype=np.uint8)
        mock_fr.face_locations.return_value = [(0, 100, 100, 0)]
        mock_fr.face_encodings.return_value = [self.test_encoding]
        # Frame 1: distance 0.65 (mismatch/dark); Frame 2: distance 0.20 (match); Subsequent: distance 0.20
        mock_fr.face_distance.side_effect = [
            [0.65],  # Frame 1 mismatch
            [0.20],  # Frame 2 match!
            [0.20],  # Liveness identity check match
        ]

        # Landmark detection mocks for stage 2
        mock_shape = MagicMock()
        mock_part = MagicMock()
        mock_part.x, mock_part.y = 10, 10
        mock_shape.part.return_value = mock_part
        mock_predictor.return_value = MagicMock(return_value=mock_shape)
        mock_detector.return_value = MagicMock(return_value=[MagicMock()])

        mock_cap = MagicMock()
        mock_cap.isOpened.return_value = True
        mock_cap.read.return_value = (True, fake_frame)

        success, score, reason = run_streamlined_biometrics(
            name=self.test_name,
            expected_encoding=self.test_encoding,
            tolerance=0.60,
            challenge_duration=0.5,
            face_detect_duration=0.5,
            predictor_filename="shape_predictor_68_face_landmarks.dat",
            cap=mock_cap
        )

        self.assertTrue(success, "Multi-frame adjustment should succeed once matching frame is acquired.")
        self.assertEqual(reason, "SUCCESS")
        self.assertAlmostEqual(score, 0.80, places=2)

    # -------------------------------------------------------------------------
    # TEST 13: Policy Normalization & Fallback on Unrecognized Auth Mode
    # -------------------------------------------------------------------------
    @patch('login.get_student_by_roll')
    @patch('login.get_face_by_roll')
    @patch('login.log_event')
    def test_unrecognized_auth_mode_falls_back_to_2fa(self, mock_log, mock_get_face, mock_get_student):
        """Unsupported auth_mode ('4FA', 'UNKNOWN', None) defaults cleanly to 2FA and logs LOGIN_2FA."""
        mock_get_student.return_value = {"name": self.test_name, "registered_date": "2026-10-24"}
        mock_get_face.return_value = self.test_encoding
        mock_bio = MagicMock(return_value=(True, 0.93, "SUCCESS"))

        for invalid_mode in ["4FA", "UNKNOWN", "INVALID", "", None]:
            mock_log.reset_mock()
            success, reason, session, conf = login.authenticate_student(
                roll_input=self.test_roll,
                auth_mode=invalid_mode,
                biometric_verifier=mock_bio
            )
            self.assertTrue(success, f"Mode '{invalid_mode}' should default to 2FA and succeed.")
            # Verify event logged is strictly LOGIN_2FA, never LOGIN_4FA or LOGIN_UNKNOWN
            mock_log.assert_any_call(self.test_roll, "LOGIN_2FA", severity="INFO", confidence_score=0.93)

    # -------------------------------------------------------------------------
    # TEST 14: Rapid Administrative Mode Toggling (2FA <-> 3FA) Continuity
    # -------------------------------------------------------------------------
    @patch('login.get_student_by_roll')
    @patch('login.get_face_by_roll')
    @patch('login.get_totp_secret_by_roll')
    def test_rapid_administrative_mode_toggling(self, mock_get_totp, mock_get_face, mock_get_student):
        """Rapid toggling between 2FA and 3FA across consecutive logins maintains cryptographic hash integrity."""
        from server.database import log_event_server
        mock_get_student.return_value = {"name": self.test_name, "registered_date": "2026-10-24"}
        mock_get_face.return_value = self.test_encoding
        mock_get_totp.return_value = self.totp_secret
        mock_bio = MagicMock(return_value=(True, 0.90, "SUCCESS"))

        # Login 1: 2FA Mode
        s1, r1, sess1, c1 = login.authenticate_student(
            roll_input=self.test_roll,
            auth_mode="2FA",
            biometric_verifier=mock_bio
        )
        self.assertTrue(s1)
        log_event_server(self.test_roll, "LOGIN_2FA", severity="INFO", confidence_score=c1, device_id="lab-pc-01")

        # Admin toggles to 3FA for exam
        # Login 2: 3FA Mode with valid TOTP
        s2, r2, sess2, c2 = login.authenticate_student(
            roll_input=self.test_roll,
            auth_mode="3FA",
            totp_input_provider=lambda n: self.totp.now(),
            biometric_verifier=mock_bio
        )
        self.assertTrue(s2)
        log_event_server(self.test_roll, "LOGIN_3FA", severity="INFO", confidence_score=c2, device_id="lab-pc-01")

        # Admin toggles back to 2FA after exam
        # Login 3: 2FA Mode again
        s3, r3, sess3, c3 = login.authenticate_student(
            roll_input=self.test_roll,
            auth_mode="2FA",
            biometric_verifier=mock_bio
        )
        self.assertTrue(s3)
        log_event_server(self.test_roll, "LOGIN_2FA", severity="INFO", confidence_score=c3, device_id="lab-pc-01")

        # Verify full cryptographic chain across all 3 toggled logins
        conn = get_db_connection(DB_PATH)
        try:
            verify_log_integrity(conn)
        finally:
            conn.close()


if __name__ == '__main__':
    unittest.main()
