import requests
import pickle
import base64
import os
import crypto_utils
import urllib3
import keyring

# Suppress the InsecureRequestWarning for our local self-signed certificate demo
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

BASE_URL = "https://127.0.0.1:8000"
SERVICE_NAME = "LabAccessControlSystem"

class ServerUnreachableError(Exception):
    """Exception raised when the central server is down (triggers fail-closed)."""
    pass

def _get_auth_header():
    """
    Fetches the JWT token from the Keyring. If not cached or expired, authenticates with the server.
    """
    jwt_token = keyring.get_password(SERVICE_NAME, "jwt_access_token")
    
    if not jwt_token:
        # We need a new token. Fetch our unique device credentials from Keyring.
        device_id = keyring.get_password(SERVICE_NAME, "device_id")
        device_secret = keyring.get_password(SERVICE_NAME, "device_secret")
        
        if not device_id or not device_secret:
            raise RuntimeError("Device not registered. Please run 'python setup_device.py' first.")
            
        try:
            # DEMO NOTE: verify=False is used here because our TLS cert is self-signed.
            response = requests.post(
                f"{BASE_URL}/token",
                data={"username": device_id, "password": device_secret},
                timeout=5,
                verify=False
            )
            
            if response.status_code == 403:
                raise ServerUnreachableError("ACCESS DENIED: This device has been revoked by the administrator.")
                
            response.raise_for_status()
            jwt_token = response.json().get("access_token")
            
            # Store the new short-lived JWT safely in the OS Keyring
            keyring.set_password(SERVICE_NAME, "jwt_access_token", jwt_token)
            
        except requests.exceptions.RequestException as e:
            raise ServerUnreachableError(f"Could not reach API for authentication: {e}")
            
    return {"Authorization": f"Bearer {jwt_token}"}

def _refresh_token_if_needed(func, *args, **kwargs):
    """
    Wrapper to automatically refresh the JWT if we get a 401 Unauthorized or 403 Forbidden.
    """
    try:
        kwargs['verify'] = False
        response = func(*args, **kwargs)
        if response.status_code in (401, 403):
            # Token might be expired or device revoked, clear it from Keyring and retry once
            try:
                keyring.delete_password(SERVICE_NAME, "jwt_access_token")
            except keyring.errors.PasswordDeleteError:
                pass # Already deleted or not found
                
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