import requests
import pickle
import base64
import os
import crypto_utils

# Base URL for the FastAPI Server
# SECURITY WARNING: For local testing this is HTTP. In production, this MUST be HTTPS
# to prevent MITM (Man-In-The-Middle) attacks from stealing the JWT token or observing
# metadata about the encrypted payloads.
BASE_URL = "http://127.0.0.1:8000"

# Hardcoded Lab PC credentials for the OAuth2 /token endpoint
CLIENT_ID = "lab-pc-01"
CLIENT_SECRET = "secure-lab-password-123"

# In-memory token cache
_ACCESS_TOKEN = None

class ServerUnreachableError(Exception):
    """Exception raised when the central server is down (triggers fail-closed)."""
    pass

def _get_auth_header():
    """
    Fetches the JWT token. If not cached or expired, authenticates with the server.
    """
    global _ACCESS_TOKEN
    
    if _ACCESS_TOKEN is None:
        try:
            response = requests.post(
                f"{BASE_URL}/token",
                data={"username": CLIENT_ID, "password": CLIENT_SECRET},
                timeout=5
            )
            response.raise_for_status()
            _ACCESS_TOKEN = response.json().get("access_token")
        except requests.exceptions.RequestException as e:
            raise ServerUnreachableError(f"Could not reach API for authentication: {e}")
            
    return {"Authorization": f"Bearer {_ACCESS_TOKEN}"}

def _refresh_token_if_needed(func, *args, **kwargs):
    """
    Wrapper to automatically refresh the JWT if we get a 401 Unauthorized (token expired).
    """
    global _ACCESS_TOKEN
    try:
        response = func(*args, **kwargs)
        if response.status_code == 401:
            # Token might be expired, clear it and retry once
            _ACCESS_TOKEN = None
            kwargs['headers'] = _get_auth_header()
            response = func(*args, **kwargs)
        return response
    except requests.exceptions.RequestException as e:
        raise ServerUnreachableError(f"Network error: {e}")

def add_student(roll_number, name, face_encoding, totp_secret):
    """
    Encrypts biometric data and sends it to the central API.
    """
    # 1. Serialize and Encrypt (E2EE)
    serialized_encoding = pickle.dumps(face_encoding)
    encrypted_encoding = crypto_utils.encrypt_data(serialized_encoding)
    encrypted_totp = crypto_utils.encrypt_data(totp_secret.encode('utf-8'))
    
    # 2. Base64 encode for JSON payload
    payload = {
        "roll_number": roll_number,
        "name": name,
        "face_encoding_b64": base64.b64encode(encrypted_encoding).decode('utf-8'),
        "totp_secret_b64": base64.b64encode(encrypted_totp).decode('utf-8')
    }
    
    # 3. Send over network
    headers = _get_auth_header()
    response = _refresh_token_if_needed(requests.post, f"{BASE_URL}/register", json=payload, headers=headers, timeout=5)
    
    return response.status_code == 200

def _get_student_data(roll_number):
    """Helper to fetch raw student data from API."""
    headers = _get_auth_header()
    response = _refresh_token_if_needed(requests.get, f"{BASE_URL}/student/{roll_number}", headers=headers, timeout=5)
    
    if response.status_code == 404:
        return None
    try:
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        raise ServerUnreachableError(f"HTTP Error: {e}")
    return response.json()

def get_face_by_roll(roll_number):
    """
    Fetches encrypted face encoding from API and decrypts locally.
    """
    data = _get_student_data(roll_number)
    if data:
        try:
            # E2EE: Decrypt locally
            encrypted_encoding = base64.b64decode(data["face_encoding_b64"])
            serialized_encoding = crypto_utils.decrypt_data(encrypted_encoding)
            return pickle.loads(serialized_encoding)
        except ValueError as e:
            print(f"\n[SECURITY] {e}")
            log_event(roll_number, "TAMPER_DETECTED_FACE_DATA", severity="HIGH")
            return None
    return None

def get_totp_secret_by_roll(roll_number):
    """
    Fetches encrypted TOTP secret from API and decrypts locally.
    """
    data = _get_student_data(roll_number)
    if data:
        try:
            encrypted_totp = base64.b64decode(data["totp_secret_b64"])
            return crypto_utils.decrypt_data(encrypted_totp).decode('utf-8')
        except ValueError as e:
            print(f"\n[SECURITY] {e}")
            log_event(roll_number, "TAMPER_DETECTED_TOTP_DATA", severity="HIGH")
            return None
    return None

def get_student_by_roll(roll_number):
    """
    Fetches student details.
    """
    data = _get_student_data(roll_number)
    if data:
        return {"name": data["name"], "registered_date": data["registered_date"]}
    return None

def log_event(roll_number, event, severity="INFO"):
    """
    Sends audit log to the central API.
    """
    payload = {
        "roll_number": roll_number,
        "event": event,
        "severity": severity
    }
    try:
        headers = _get_auth_header()
        response = _refresh_token_if_needed(requests.post, f"{BASE_URL}/log", json=payload, headers=headers, timeout=5)
        return response.status_code == 200
    except ServerUnreachableError:
        # If logging fails, we return False. 
        # In a high-security Fail-Closed system, failing to log might trigger a lockdown.
        return False

def init_db(db_path=None):
    pass