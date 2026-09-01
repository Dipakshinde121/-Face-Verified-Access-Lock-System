import os
import keyring
from cryptography.fernet import Fernet

SERVICE_NAME = "LabAccessControlSystem"
ACCOUNT_NAME = "fernet_key"

def main():
    print("=== Secure Key Management Setup ===")
    
    # 1. Generate a secure Fernet Key
    key = Fernet.generate_key().decode('utf-8')
    
    # 2. Store it securely in the OS Keyring
    try:
        keyring.set_password(SERVICE_NAME, ACCOUNT_NAME, key)
        print("[SUCCESS] New Fernet encryption key securely stored in OS Keyring.")
    except Exception as e:
        print(f"[ERROR] Failed to access OS Keyring: {e}")
        print("\nFALLBACK: If running on a headless Linux server without a secret service,")
        print("you must export the key as an environment variable or use a .env file.")
        return
        
    # 3. Clean up legacy plain text keys if they exist
    base_dir = os.path.dirname(os.path.abspath(__file__))
    legacy_key_file = os.path.join(base_dir, "secret.key")
    if os.path.exists(legacy_key_file):
        os.remove(legacy_key_file)
        print("[SECURITY] Legacy plain-text secret.key file found and DELETED.")
        
    print("\nSetup complete. The system is ready to use Secure Credential Storage.")

if __name__ == "__main__":
    main()
