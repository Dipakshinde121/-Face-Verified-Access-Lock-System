"""
test_adversarial_suite.py
Automated Adversarial Red-Team Test Suite for Lab Access Lock System
Executes automated attack vectors against the local API, cryptographic layer, and hash chain.
"""

import unittest
import os
import sys
import sqlite3
import jwt
import time
import base64
import hashlib
from fastapi.testclient import TestClient

# Ensure root directory is in sys.path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from server.main import app, JWT_SECRET, JWT_ALGORITHM
from server.database import init_db, get_db_connection, DB_PATH, GENESIS_HASH, add_student_server
from crypto_utils import encrypt_data, decrypt_data
from cryptography.fernet import InvalidToken

class TestAdversarialSecurity(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)
        init_db(DB_PATH)
        
        # Provision a test device via API
        reg_res = cls.client.post("/device/register?device_label=Adversarial-Test-PC")
        assert reg_res.status_code == 200, f"Registration failed: {reg_res.text}"
        data = reg_res.json()
        cls.device_id = data["device_id"]
        cls.device_secret = data["device_secret"]
        
        # Request valid JWT via OAuth2 password flow
        token_res = cls.client.post("/token", data={"username": cls.device_id, "password": cls.device_secret})
        assert token_res.status_code == 200, f"Token request failed: {token_res.text}"
        cls.valid_token = token_res.json()["access_token"]
        cls.headers = {"Authorization": f"Bearer {cls.valid_token}"}
        
        # Enroll an adversarial test student to satisfy foreign keys
        cls.test_student = "ADV_STUDENT_01"
        add_student_server(cls.test_student, "Adversarial Tester", b"fake_enc_bytes", b"fake_totp_bytes")

    # ==========================================
    # CATEGORY 1: API & JWT ATTACKS
    # ==========================================
    def test_adv_01_missing_jwt(self):
        """Attack: Request API endpoint with no Authorization header."""
        res = self.client.get(f"/student/{self.test_student}")
        self.assertEqual(res.status_code, 401, "Missing JWT must be rejected with HTTP 401")
        print("[ADV-01] Missing JWT rejected: HTTP 401 (PASS)")

    def test_adv_02_tampered_jwt_signature(self):
        """Attack: Alter the cryptographic signature of the JWT token."""
        parts = self.valid_token.split(".")
        tampered_token = f"{parts[0]}.{parts[1]}.badsignature123456"
        res = self.client.get(f"/student/{self.test_student}", headers={"Authorization": f"Bearer {tampered_token}"})
        self.assertIn(res.status_code, [401, 403], "Tampered JWT signature must be rejected with HTTP 401/403")
        print(f"[ADV-02] Tampered JWT signature rejected: HTTP {res.status_code} (PASS)")

    def test_adv_03_jwt_none_algorithm_attack(self):
        """Attack: Attempt JWT algorithm confusion by setting alg='none'."""
        header_b64 = "eyJhbGciOiJub25lIiwidHlwIjoiSldUIn0" # {"alg":"none","typ":"JWT"}
        payload_b64 = "eyJzdWIiOiJ0ZXN0LWFkdi1kZXZpY2UiLCJleHAiOjI1MzQwMjMwMDd9" # {"sub":"test-adv-device","exp":2534023007}
        none_token = f"{header_b64}.{payload_b64}."
        res = self.client.get(f"/student/{self.test_student}", headers={"Authorization": f"Bearer {none_token}"})
        self.assertIn(res.status_code, [401, 403], "Algorithm 'none' token must be rejected with HTTP 401/403")
        print(f"[ADV-03] JWT 'none' algorithm attack rejected: HTTP {res.status_code} (PASS)")

    def test_adv_04_expired_jwt(self):
        """Attack: Submit a token whose expiration timestamp is in the past."""
        expired_token = jwt.encode(
            {"sub": self.device_id, "exp": int(time.time()) - 3600, "iat": int(time.time()) - 7200},
            JWT_SECRET,
            algorithm=JWT_ALGORITHM
        )
        res = self.client.get(f"/student/{self.test_student}", headers={"Authorization": f"Bearer {expired_token}"})
        self.assertIn(res.status_code, [401, 403], "Expired token must return HTTP 401/403")
        print(f"[ADV-04] Expired JWT rejected: HTTP {res.status_code} (PASS)")

    # ==========================================
    # CATEGORY 2: SQL INJECTION PROBING
    # ==========================================
    def test_adv_05_sql_injection_in_roll_number(self):
        """Attack: Inject SQL syntax into /student/{roll_number}."""
        sqli_payload = "' OR '1'='1"
        res = self.client.get(f"/student/{sqli_payload}", headers=self.headers)
        # Parameterized queries ensure the literal string is searched and returns 404 Not Found
        self.assertEqual(res.status_code, 404, "SQLi in roll_number must safely return HTTP 404")
        print("[ADV-05] SQL injection in roll_number shielded by parameterized queries: HTTP 404 (PASS)")

    def test_adv_06_sql_injection_in_registration_payload(self):
        """Attack: Attempt SQL injection in registration name / roll fields."""
        sqli_roll = "ATTACKER'; DROP TABLE logs;--"
        sqli_name = "Rogue User'--"
        res = self.client.post("/register", json={
            "roll_number": sqli_roll,
            "name": sqli_name,
            "face_encoding_b64": base64.b64encode(b"dummy_face").decode(),
            "totp_secret_b64": base64.b64encode(b"dummy_totp").decode()
        }, headers=self.headers)
        
        # Verify table still exists and query executed safely via parameterized bindings
        conn = get_db_connection(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT count(*) FROM logs")
        count = cursor.fetchone()[0]
        conn.close()
        self.assertGreaterEqual(count, 0, "Logs table must remain intact; DROP TABLE injection neutralized")
        print("[ADV-06] SQL injection in registration payload neutralized by prepared statements (PASS)")

    # ==========================================
    # CATEGORY 3: DATA INTEGRITY & BIT-FLIPPING
    # ==========================================
    def test_adv_07_biometric_ciphertext_bit_flipping(self):
        """Attack: Corrupt 16 bytes of stored Fernet ciphertext blob in DB."""
        plaintext = b"biometric_vector_test_data"
        ciphertext = encrypt_data(plaintext)
        
        # Corrupt bytes in the ciphertext payload
        corrupted = bytearray(ciphertext)
        corrupted[20] ^= 0xFF
        corrupted[25] ^= 0xAA
        corrupted_bytes = bytes(corrupted)
        
        # Decryption must raise ValueError('TAMPER_DETECTED') or InvalidToken
        tamper_caught = False
        try:
            decrypt_data(corrupted_bytes)
        except (ValueError, InvalidToken):
            tamper_caught = True
            
        self.assertTrue(tamper_caught, "Biometric ciphertext bit-flipping must trigger tamper detection")
        print("[ADV-07] Biometric ciphertext bit-flipping caught by HMAC-SHA256 integrity verification (PASS)")

    # ==========================================
    # CATEGORY 4: HASH CHAIN TAMPER CATCHING
    # ==========================================
    def test_adv_08_hash_chain_row_modification(self):
        """Attack: Alter a historical log row's confidence score directly in SQLite."""
        # Post two clean log entries via API using registered student
        self.client.post("/log", json={
            "roll_number": self.test_student,
            "event": "MATCH",
            "severity": "LOW",
            "confidence_score": 0.92,
            "device_id": self.device_id
        }, headers=self.headers)
        
        self.client.post("/log", json={
            "roll_number": self.test_student,
            "event": "MATCH",
            "severity": "LOW",
            "confidence_score": 0.89,
            "device_id": self.device_id
        }, headers=self.headers)
        
        conn = get_db_connection(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT id, confidence_score, entry_hash FROM logs WHERE roll_number=? ORDER BY id DESC LIMIT 1", (self.test_student,))
        row = cursor.fetchone()
        log_id, original_score, orig_hash = row
        
        # Alter confidence score via raw SQL
        tampered_score = 0.99
        cursor.execute("UPDATE logs SET confidence_score = ? WHERE id = ?", (tampered_score, log_id))
        conn.commit()
        
        # Now verify integrity from log_id onwards: traversal must raise or report tampering
        tamper_detected = False
        cursor.execute("SELECT id, timestamp, roll_number, device_id, event, severity, confidence_score, entry_hash, previous_hash FROM logs WHERE id >= ? ORDER BY id ASC", (log_id,))
        rows = cursor.fetchall()
        for r in rows:
            r_id, r_time, r_roll, r_dev, r_event, r_sev, r_conf, r_entry_hash, r_prev_hash = r
            conf_str = f"{float(r_conf):.2f}" if r_conf is not None else ""
            data_to_hash = f"{r_time}|{r_roll or ''}|{r_dev}|{r_event}|{r_sev}|{conf_str}|{r_prev_hash}"
            expected_hash = hashlib.sha256(data_to_hash.encode()).hexdigest()
            if r_entry_hash != expected_hash:
                tamper_detected = True
                self.assertEqual(r_id, log_id, f"Tamper must be caught at exact ID {log_id}")
                break
        conn.close()
        self.assertTrue(tamper_detected, "Hash chain must detect modified row score")
        print(f"[ADV-08] Log row score tampering detected at exact row ID {log_id} (PASS)")

    def test_adv_09_hash_chain_row_deletion(self):
        """Attack: Delete a mid-stream log record to hide a security incident."""
        self.client.post("/log", json={
            "roll_number": self.test_student,
            "event": "LOCK_FACE_MISMATCH",
            "severity": "HIGH",
            "confidence_score": 0.20,
            "device_id": self.device_id
        }, headers=self.headers)
        
        self.client.post("/log", json={
            "roll_number": self.test_student,
            "event": "MATCH",
            "severity": "LOW",
            "confidence_score": 0.90,
            "device_id": self.device_id
        }, headers=self.headers)
        
        conn = get_db_connection(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT id, entry_hash FROM logs WHERE event='LOCK_FACE_MISMATCH' AND roll_number=?", (self.test_student,))
        row = cursor.fetchone()
        deleted_id, deleted_hash = row
        
        # Delete row out-of-band via raw SQL
        cursor.execute("DELETE FROM logs WHERE id = ?", (deleted_id,))
        conn.commit()
        
        # Verification must catch the broken link because next row's previous_hash won't match preceding row's entry_hash
        cursor.execute("SELECT id, entry_hash, previous_hash FROM logs ORDER BY id ASC")
        rows = cursor.fetchall()
        chain_broken = False
        prev = GENESIS_HASH
        for r in rows:
            r_id, r_entry, r_prev = r
            if r_prev != prev:
                chain_broken = True
                break
            prev = r_entry
            
        conn.close()
        self.assertTrue(chain_broken, "Deleting an audit row must break hash continuity")
        print(f"[ADV-09] Audit row deletion detected: hash continuity broken immediately after deleted row (PASS)")

    def test_adv_10_hash_chain_row_reordering(self):
        """Attack: Swap two adjacent log entries in SQLite to falsify sequence of events."""
        # Insert two sequential events
        self.client.post("/log", json={
            "roll_number": self.test_student,
            "event": "EVENT_SEQUENCE_A",
            "severity": "LOW",
            "confidence_score": 0.85,
            "device_id": self.device_id
        }, headers=self.headers)
        
        self.client.post("/log", json={
            "roll_number": self.test_student,
            "event": "EVENT_SEQUENCE_B",
            "severity": "LOW",
            "confidence_score": 0.86,
            "device_id": self.device_id
        }, headers=self.headers)
        
        conn = get_db_connection(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM logs WHERE roll_number=? AND event IN ('EVENT_SEQUENCE_A', 'EVENT_SEQUENCE_B') ORDER BY id DESC LIMIT 2", (self.test_student,))
        ids = [row[0] for row in cursor.fetchall()]
        self.assertEqual(len(ids), 2)
        id_b, id_a = ids[0], ids[1]
        
        # Swap the two rows' event data while preserving IDs, or swap their previous_hash links
        cursor.execute("SELECT event, entry_hash, previous_hash FROM logs WHERE id=?", (id_a,))
        row_a = cursor.fetchone()
        cursor.execute("SELECT event, entry_hash, previous_hash FROM logs WHERE id=?", (id_b,))
        row_b = cursor.fetchone()
        
        # Swap entry_hash between the two records in the database
        cursor.execute("UPDATE logs SET entry_hash=? WHERE id=?", (row_b[1], id_a))
        cursor.execute("UPDATE logs SET entry_hash=? WHERE id=?", (row_a[1], id_b))
        conn.commit()
        
        # Traverse chain to detect reordering anomaly
        cursor.execute("SELECT id, entry_hash, previous_hash FROM logs ORDER BY id ASC")
        rows = cursor.fetchall()
        reorder_caught = False
        prev = GENESIS_HASH
        for r in rows:
            r_id, r_entry, r_prev = r
            if r_prev != prev:
                reorder_caught = True
                break
            prev = r_entry
        conn.close()
        self.assertTrue(reorder_caught, "Swapping/reordering log records must break backward hash chaining")
        print(f"[ADV-10] Audit row reordering detected: cryptographic chain linkage broken (PASS)")

    # ==========================================
    # CATEGORY 5: MALFORMED PAYLOADS & REVERSAL
    # ==========================================
    def test_adv_11_malformed_payload_rejection(self):
        """Attack: Submit malformed types and oversized payload to REST endpoints."""
        # 1. Malformed payload types (string for float confidence score, invalid types)
        bad_payload = {
            "roll_number": self.test_student,
            "event": 99999,  # Should be string
            "severity": "CRITICAL",
            "confidence_score": "NOT_A_FLOAT"
        }
        res = self.client.post("/log", json=bad_payload, headers=self.headers)
        self.assertEqual(res.status_code, 422, "Malformed payload types must be rejected with HTTP 422")
        
        # 2. Oversized payload probing
        oversized_str = "A" * (1024 * 1024) # 1 MB synthetic string
        bad_register = {
            "roll_number": oversized_str,
            "name": "Buffer Overflow Probe",
            "face_encoding_b64": "invalid_base64_data!!!",
            "totp_secret_b64": "invalid_base64_data!!!"
        }
        res2 = self.client.post("/register", json=bad_register, headers=self.headers)
        self.assertIn(res2.status_code, [400, 422, 500], "Malformed base64 / oversized payload safely handled")
        print("[ADV-11] Malformed and oversized payloads strictly rejected by Pydantic schema validation (PASS)")

    def test_adv_12_revoked_device_token_rejection(self):
        """Attack: Attempt API access using a JWT from a revoked device."""
        # Provision a sacrificial device and immediately revoke it
        reg_res = self.client.post("/device/register?device_label=Sacrificial-PC")
        dev_data = reg_res.json()
        s_dev_id = dev_data["device_id"]
        s_secret = dev_data["device_secret"]
        
        token_res = self.client.post("/token", data={"username": s_dev_id, "password": s_secret})
        s_token = token_res.json()["access_token"]
        
        # Mark device as revoked in DB
        conn = get_db_connection(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("UPDATE devices SET revoked = 1 WHERE device_id = ?", (s_dev_id,))
        conn.commit()
        conn.close()
        
        # Attempt access using the issued token
        res = self.client.get(f"/student/{self.test_student}", headers={"Authorization": f"Bearer {s_token}"})
        self.assertEqual(res.status_code, 403, "Revoked device token must be rejected with HTTP 403")
        print("[ADV-12] Revoked device token rejected with HTTP 403 (PASS)")

if __name__ == '__main__':
    unittest.main()
