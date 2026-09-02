import os
import keyring
import requests
import urllib3

# Suppress warnings for local self-signed cert
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

BASE_URL = "https://127.0.0.1:8000"
SERVICE_NAME = "LabAccessControlSystem"

def main():
    print("=== Per-Device Authentication Setup ===")
    
    # Check if we are already registered
    existing_id = keyring.get_password(SERVICE_NAME, "device_id")
    if existing_id:
        print(f"Device is already registered as: {existing_id}")
        choice = input("Do you want to re-register this device? (y/N): ")
        if choice.lower() != 'y':
            return
            
    print("\nRegistering device with the Central API...")
    try:
        response = requests.post(f"{BASE_URL}/device/register", verify=False, timeout=5)
        response.raise_for_status()
        
        data = response.json()
        device_id = data["device_id"]
        device_secret = data["device_secret"]
        
        # Save credentials securely into OS Keyring
        keyring.set_password(SERVICE_NAME, "device_id", device_id)
        keyring.set_password(SERVICE_NAME, "device_secret", device_secret)
        
        print(f"[SUCCESS] Registered and secured credentials for {device_id} in OS Keyring.")
        print("This device is now trusted by the central API.")
        
    except requests.exceptions.RequestException as e:
        print(f"[ERROR] Could not connect to Central API: {e}")
        print("Ensure the server is running on https://127.0.0.1:8000")

if __name__ == "__main__":
    main()
