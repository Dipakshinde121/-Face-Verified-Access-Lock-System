import os
from cryptography.fernet import Fernet, InvalidToken

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
KEY_FILE = os.path.join(BASE_DIR, "secret.key")

def load_or_generate_key():
    """
    Loads the symmetric encryption key from file. 
    Generates and saves a new one if it doesn't exist.
    
    SECURITY PRINCIPLE: Key/Data Separation. The key is kept in a local file,
    excluded from version control, and entirely separate from the SQLite database.
    If the database is stolen, the data remains unreadable without this key.
    """
    if not os.path.exists(KEY_FILE):
        key = Fernet.generate_key()
        with open(KEY_FILE, "wb") as key_file:
            key_file.write(key)
        return key
    else:
        with open(KEY_FILE, "rb") as key_file:
            return key_file.read()

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
        # Fallback for biometric data registered before Encryption at Rest was implemented.
        # In a strict production environment, this would raise a hard error instead.
        return encrypted_bytes
