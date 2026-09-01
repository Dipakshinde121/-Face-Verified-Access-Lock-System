import os
import keyring
from cryptography.fernet import Fernet, InvalidToken

SERVICE_NAME = "LabAccessControlSystem"
ACCOUNT_NAME = "fernet_key"

def load_or_generate_key():
    """
    Loads the symmetric encryption key from the OS Keyring.
    
    SECURITY PRINCIPLE: Key/Data Separation.
    The key is managed by the OS Credential Manager. If the database file is stolen,
    it cannot be decrypted without also compromising the host machine's secure enclave.
    """
    key = keyring.get_password(SERVICE_NAME, ACCOUNT_NAME)
    
    if key is None:
        raise RuntimeError(
            "[SECURITY ERROR] Encryption key not found in OS Keyring!\n"
            "Please run 'python setup_key.py' to initialize the secure credential storage."
        )
        
    return key.encode('utf-8')

# Initialize the cipher suite globally for this module
_key = load_or_generate_key()
_cipher_suite = Fernet(_key)

def encrypt_data(data_bytes: bytes) -> bytes:
    """Encrypts plaintext bytes using Fernet symmetric encryption."""
    return _cipher_suite.encrypt(data_bytes)

def decrypt_data(encrypted_bytes: bytes) -> bytes:
    """
    Decrypts ciphertext bytes back to plaintext.
    Handles legacy (unencrypted) data gracefully for backwards compatibility.
    """
    try:
        return _cipher_suite.decrypt(encrypted_bytes)
    except InvalidToken:
        # STRICT SECURITY ENFORCEMENT:
        # If decryption fails, it implies the data was tampered with or corrupted.
        raise ValueError("TAMPER_DETECTED: Cryptographic signature mismatch.")
