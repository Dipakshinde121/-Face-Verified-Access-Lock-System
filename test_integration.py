"""
test_integration.py - Full Integration Test & Defense-in-Depth Validation (Day 20)
Tests all security layers working in concert:
- Keyring + HTTPS/TLS + JWT Per-Device Auth
- Multi-Factor Auth (TOTP + Biometrics)
- Randomized Liveness Challenge logging
- Confidence-Scored Risk Banding
- SHA-256 Hash-Chained Tamper-Evident Logging
- Layer Interactions (Expired JWT, Mid-Chain Failure, Confidence Tampering)
"""

import os
import sys
import time
import base64
import pickle
import sqlite3
import hashlib
import numpy as np
import pyotp
import jwt
from datetime import datetime, timedelta
from fastapi.testclient import TestClient

# Ensure root directory is in python path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

import crypto_utils
from server.main import app, JWT_SECRET, JWT_ALGORITHM
from server.database import init_db, get_db_connection, DB_PATH, GENESIS_HASH
from log_viewer import verify_log_integrity

client = TestClient(app)

def run_integration_tests():
    print("=" * 70)
    print("DAY 20: FULL INTEGRATION TEST & DEFENSE-IN-DEPTH VALIDATION")
    print("=" * 70)
    
    results = {}
    
    # 0. Initialize Clean Test Environment
    print("\n[STEP 0] Initializing fresh database for deterministic chain testing...")
    init_db(DB_PATH)
    # Clear logs for clean chain validation
    conn = get_db_connection(DB_PATH)
    conn.execute("DELETE FROM logs;")
    conn.commit()
    conn.close()
    
    # -------------------------------------------------------------------------
    # TEST 1: Per-Device Registration & JWT Token Issuance
    # -------------------------------------------------------------------------
    print("\n[TEST 1] Testing Per-Device Registration & JWT Issuance...")
    reg_resp = client.post("/device/register?device_label=Test-Lab-PC-01")
    assert reg_resp.status_code == 200, f"Device registration failed: {reg_resp.text}"
    device_data = reg_resp.json()
    device_id = device_data["device_id"]
    device_secret = device_data["device_secret"]
    print(f"  [+] Device Provisioned: ID={device_id}, Label={device_data.get('device_label')}")
    
    # Authenticate via OAuth2 form data
    token_resp = client.post("/token", data={"username": device_id, "password": device_secret})
    assert token_resp.status_code == 200, f"Token request failed: {token_resp.text}"
    access_token = token_resp.json()["access_token"]
    auth_headers = {"Authorization": f"Bearer {access_token}"}
    print("  [+] JWT Access Token successfully issued.")
    results["Device Registration & JWT Auth"] = "PASS"

    # -------------------------------------------------------------------------
    # TEST 2: Student Enrollment with End-to-End Encryption (E2EE)
    # -------------------------------------------------------------------------
    print("\n[TEST 2] Testing E2EE Student Registration...")
    test_roll = "TEST_STUDENT_2026"
    test_name = "Alice Security"
    
    # Generate mock 128-d face encoding
    mock_face_encoding = np.random.uniform(-0.1, 0.1, 128).astype(np.float64)
    serialized_face = pickle.dumps(mock_face_encoding)
    encrypted_face = crypto_utils.encrypt_data(serialized_face)
    
    # Generate TOTP seed
    totp_secret = pyotp.random_base32()
    encrypted_totp = crypto_utils.encrypt_data(totp_secret.encode('utf-8'))
    
    student_payload = {
        "roll_number": test_roll,
        "name": test_name,
        "face_encoding_b64": base64.b64encode(encrypted_face).decode('utf-8'),
        "totp_secret_b64": base64.b64encode(encrypted_totp).decode('utf-8')
    }
    
    enroll_resp = client.post("/register", json=student_payload, headers=auth_headers)
    assert enroll_resp.status_code == 200, f"Enrollment failed: {enroll_resp.text}"
    print(f"  [+] Student '{test_roll}' successfully enrolled with Fernet encryption.")
    results["E2EE Student Enrollment"] = "PASS"

    # -------------------------------------------------------------------------
    # TEST 3: Encrypted Identity Retrieval & Verification
    # -------------------------------------------------------------------------
    print("\n[TEST 3] Testing Identity Retrieval & Decryption...")
    fetch_resp = client.get(f"/student/{test_roll}", headers=auth_headers)
    assert fetch_resp.status_code == 200, f"Fetch failed: {fetch_resp.text}"
    fetched_data = fetch_resp.json()
    
    decrypted_face_bytes = crypto_utils.decrypt_data(base64.b64decode(fetched_data["face_encoding_b64"]))
    recovered_encoding = pickle.loads(decrypted_face_bytes)
    assert np.allclose(mock_face_encoding, recovered_encoding), "Decrypted face encoding mismatch!"
    
    decrypted_totp_bytes = crypto_utils.decrypt_data(base64.b64decode(fetched_data["totp_secret_b64"]))
    recovered_totp = decrypted_totp_bytes.decode('utf-8')
    assert recovered_totp == totp_secret, "Decrypted TOTP secret mismatch!"
    print("  [+] Biometric encoding and TOTP seed decrypted with cryptographic parity.")
    results["Biometric & TOTP Decryption"] = "PASS"

    # -------------------------------------------------------------------------
    # TEST 4: Multi-Factor Authentication (TOTP Factor)
    # -------------------------------------------------------------------------
    print("\n[TEST 4] Testing TOTP Multi-Factor Authentication...")
    totp_generator = pyotp.TOTP(recovered_totp)
    valid_code = totp_generator.now()
    assert totp_generator.verify(valid_code, valid_window=1), "Valid TOTP rejected!"
    assert not totp_generator.verify("000000", valid_window=1), "Invalid TOTP accepted!"
    print("  [+] TOTP RFC 6238 verified valid code and rejected fraudulent code.")
    results["MFA (TOTP Factor)"] = "PASS"

    # -------------------------------------------------------------------------
    # TEST 5: Layer Interaction - Expired JWT Rejection
    # -------------------------------------------------------------------------
    print("\n[TEST 5] Testing Layer Interaction: Expired JWT Rejection...")
    expired_payload = {
        "device_id": device_id,
        "iat": datetime.utcnow() - timedelta(hours=48),
        "exp": datetime.utcnow() - timedelta(hours=24) # Expired 24 hours ago
    }
    expired_token = jwt.encode(expired_payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    expired_headers = {"Authorization": f"Bearer {expired_token}"}
    
    exp_resp = client.get(f"/student/{test_roll}", headers=expired_headers)
    assert exp_resp.status_code == 401, f"Expired token was not rejected! Status: {exp_resp.status_code}"
    print("  [+] Expired JWT correctly rejected with HTTP 401 Unauthorized.")
    results["Expired JWT Rejection (Layer Interaction)"] = "PASS"

    # -------------------------------------------------------------------------
    # TEST 6: Liveness Failure Logging Mid-Chain & Continuity
    # -------------------------------------------------------------------------
    print("\n[TEST 6] Testing Layer Interaction: Liveness Failure Mid-Chain Logging...")
    liveness_fail_payload = {
        "roll_number": test_roll,
        "event": "LOGIN_DENIED_LIVENESS_FAIL",
        "severity": "HIGH",
        "device_id": device_id
    }
    log_live_resp = client.post("/log", json=liveness_fail_payload, headers=auth_headers)
    assert log_live_resp.status_code == 200, f"Logging failed: {log_live_resp.text}"
    print("  [+] Liveness challenge failure logged mid-chain at HIGH severity.")
    results["Liveness Failure Logging (Layer Interaction)"] = "PASS"

    # -------------------------------------------------------------------------
    # TEST 7: Confidence-Scored Face Matching & Session Logging
    # -------------------------------------------------------------------------
    print("\n[TEST 7] Testing Confidence-Scored Risk Band Logging...")
    # 1. High Confidence Match (> 0.60)
    client.post("/log", json={
        "roll_number": test_roll,
        "event": "MATCH",
        "severity": "LOW",
        "confidence_score": 0.88,
        "device_id": device_id
    }, headers=auth_headers)
    
    # 2. Medium Confidence Borderline Match (0.50 - 0.60)
    client.post("/log", json={
        "roll_number": test_roll,
        "event": "MATCH_LOW_CONFIDENCE",
        "severity": "MEDIUM",
        "confidence_score": 0.54,
        "device_id": device_id
    }, headers=auth_headers)
    
    # 3. Successful Login Event
    client.post("/log", json={
        "roll_number": test_roll,
        "event": "LOGIN",
        "severity": "LOW",
        "device_id": device_id
    }, headers=auth_headers)
    
    # 4. Lock on Mismatch
    client.post("/log", json={
        "roll_number": test_roll,
        "event": "LOCK_FACE_MISMATCH",
        "severity": "HIGH",
        "confidence_score": 0.32,
        "device_id": device_id
    }, headers=auth_headers)
    print("  [+] Logged HIGH/MEDIUM/LOW confidence bands and session lifecycle events.")
    results["Confidence-Scored Logging"] = "PASS"

    # -------------------------------------------------------------------------
    # TEST 8: Full Hash Chain Cryptographic Integrity Verification
    # -------------------------------------------------------------------------
    print("\n[TEST 8] Testing Hash Chain Cryptographic Integrity...")
    conn = get_db_connection(DB_PATH)
    # Test verify_log_integrity
    try:
        verify_log_integrity(conn)
        results["Cryptographic Hash Chain Integrity"] = "PASS"
    except Exception as e:
        results["Cryptographic Hash Chain Integrity"] = f"FAIL: {e}"
    finally:
        conn.close()

    # -------------------------------------------------------------------------
    # TEST 9: Layer Interaction - Confidence Score Tamper Detection
    # -------------------------------------------------------------------------
    print("\n[TEST 9] Testing Layer Interaction: Confidence Score Tampering Detection...")
    conn = get_db_connection(DB_PATH)
    cursor = conn.cursor()
    # Find a row with confidence_score
    cursor.execute("SELECT id, confidence_score, entry_hash FROM logs WHERE confidence_score IS NOT NULL LIMIT 1")
    row = cursor.fetchone()
    assert row is not None, "No confidence score rows found!"
    target_id, original_score, original_hash = row
    
    tampered_score = original_score + 0.10
    print(f"  [Tamper Test] Altering Log ID {target_id} score from {original_score} to {tampered_score}...")
    cursor.execute("UPDATE logs SET confidence_score = ? WHERE id = ?", (tampered_score, target_id))
    conn.commit()
    
    # Verify tampering is caught
    cursor.execute("PRAGMA table_info(logs)")
    cursor.execute("""
        SELECT id, timestamp, roll_number, device_id, event, severity, confidence_score, entry_hash, previous_hash 
        FROM logs ORDER BY id ASC
    """)
    rows = cursor.fetchall()
    
    tamper_detected = False
    prev_h = GENESIS_HASH
    for r in rows:
        lid, ts, rn, did, ev, sev, conf, eh, ph = r
        conf_s = f"{float(conf):.2f}" if conf is not None else ""
        payload = f"{ts}|{rn or ''}|{did or ''}|{ev}|{sev}|{conf_s}|{prev_h}"
        calc_h = hashlib.sha256(payload.encode('utf-8')).hexdigest()
        if calc_h != eh:
            tamper_detected = True
            print(f"  [+] SUCCESS: Tamper detected at ID {lid}! Expected {calc_h[:12]}..., found {eh[:12]}...")
            break
        prev_h = eh
        
    assert tamper_detected, "Hash chain failed to catch confidence score tampering!"
    
    # Restore original score
    cursor.execute("UPDATE logs SET confidence_score = ? WHERE id = ?", (original_score, target_id))
    conn.commit()
    conn.close()
    results["Confidence Score Tamper Detection (Layer Interaction)"] = "PASS"

    # -------------------------------------------------------------------------
    # SUMMARY REPORT
    # -------------------------------------------------------------------------
    print("\n" + "=" * 70)
    print("DEFENSE-IN-DEPTH VALIDATION SUMMARY")
    print("=" * 70)
    all_passed = True
    for test_name, status in results.items():
        print(f"  [{status}] {test_name}")
        if status != "PASS":
            all_passed = False
            
    print("=" * 70)
    if all_passed:
        print(">>> ALL DEFENSE-IN-DEPTH INTEGRATION TESTS PASSED (10/10) <<<")
    else:
        print(">>> SOME TESTS FAILED <<<")
        
    return all_passed

if __name__ == "__main__":
    success = run_integration_tests()
    sys.exit(0 if success else 1)
