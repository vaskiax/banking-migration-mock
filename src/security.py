import os
import logging
import hashlib
from cryptography.fernet import Fernet
from typing import Optional

from src.config_loader import settings

# Configure logging
LOG_DIR = settings.paths.logs
os.makedirs(LOG_DIR, exist_ok=True)
logger = logging.getLogger("SecurityModule")
if not logger.handlers:
    handler = logging.FileHandler(os.path.join(LOG_DIR, "security.log"))
    handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

class SecurityManager:
    """
    Handles PII security via hashing (SHA256) and encryption (Fernet/AES).
    Complies with GDPR requirements for data protection.
    """
    
    def __init__(self, key: Optional[bytes] = None):
        """
        Initializes the security manager with a Fernet key.
        If no key is provided, it attempts to load from environment or generates a new one (for demo).
        """
        env_key_name = settings.security.encryption_key_env
        self.key = key or os.environ.get(env_key_name, Fernet.generate_key())
        self.cipher_suite = Fernet(self.key)
        
        if not os.environ.get(env_key_name):
            logger.warning(f"No encryption key found in environment variable {env_key_name}. Using a temporary key.")

    def hash_email(self, email: str) -> str:
        """
        Hashes email using SHA256 for anonymized analytics.
        """
        if not email:
            logger.error("Attempted to hash null email.")
            return ""
        
        return hashlib.sha256(email.lower().strip().encode()).hexdigest()

    def encrypt_pan(self, pan: str) -> str:
        """
        Encrypts credit card number (PAN) using Fernet.
        Original PAN should be discarded after this operation.
        """
        if not pan or not isinstance(pan, str):
            logger.error(f"Falla en el cifrado: El PAN no es válido o está vacío.")
            raise ValueError("Invalid PAN for encryption")
        
        try:
            encrypted_text = self.cipher_suite.encrypt(pan.encode())
            return encrypted_text.decode()
        except Exception as e:
            logger.error(f"Error encrypting PAN: {str(e)}")
            raise

    def decrypt_pan(self, encrypted_pan: str) -> str:
        """
        Decrypts credit card number (PAN).
        Useful for authorized auditing or customer service processes.
        """
        try:
            decrypted_text = self.cipher_suite.decrypt(encrypted_pan.encode())
            return decrypted_text.decode()
        except Exception as e:
            logger.error(f"Error decrypting PAN: {str(e)}")
            raise

if __name__ == "__main__":
    # Quick demo/test
    sec = SecurityManager()
    test_email = "test@example.com"
    test_pan = "1234567812345678"
    
    hashed = sec.hash_email(test_email)
    encrypted = sec.encrypt_pan(test_pan)
    
    print(f"Original Email: {test_email} -> Hashed: {hashed}")
    print(f"Original PAN: {test_pan} -> Encrypted: {encrypted}")
    print(f"Decrypted PAN: {sec.decrypt_pan(encrypted)}")
