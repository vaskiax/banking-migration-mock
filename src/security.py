import os
import logging
import hashlib
from cryptography.fernet import Fernet
from typing import Optional

try:
    from google.cloud import secretmanager
    GCP_SECRET_MANAGER_AVAILABLE = True
except ImportError:
    GCP_SECRET_MANAGER_AVAILABLE = False

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
        Initializes the security manager. Prioritizes:
        1. Explicit key
        2. GCP Secret Manager (if configured)
        3. secrets.env file
        4. Environment variable
        5. New generation (fallback)
        """
        env_key_name = settings.security.encryption_key_env
        raw_key = os.environ.get(env_key_name)
        
        # 1. Explicit key
        if key:
            self.key = key
            self.cipher_suite = Fernet(self.key)
            return

        # 2. Try GCP Secret Manager
        gcp_secret_id = os.environ.get("GCP_SECRET_ID")
        if gcp_secret_id and GCP_SECRET_MANAGER_AVAILABLE:
            try:
                gcp_key = self._fetch_from_gcp_secret_manager(gcp_secret_id)
                if gcp_key:
                    self.key = gcp_key.strip().encode()
                    self.cipher_suite = Fernet(self.key)
                    logger.info(f"Loaded key from GCP Secret Manager: {gcp_secret_id}")
                    return
            except Exception as e:
                logger.warning(f"Failed to fetch key from GCP Secret Manager: {e}")

        # 3. Try to load from secrets.env if it exists
        secrets_path = os.path.join(os.getcwd(), 'secrets.env')
        if not raw_key and os.path.exists(secrets_path):
            try:
                with open(secrets_path, 'r') as f:
                    for line in f:
                        if line.startswith(f"{env_key_name}="):
                            raw_key = line.split('=')[1].strip()
                            logger.info(f"Loaded key from secrets.env")
                            break
            except Exception as e:
                logger.warning(f"Error reading secrets.env: {e}")

        # 4 & 5. Env or Fallback
        if raw_key:
            self.key = raw_key.strip().encode()
        else:
            self.key = Fernet.generate_key()
            logger.warning(f"No encryption key found in any source. Using a temporary key.")
            
        self.cipher_suite = Fernet(self.key)

    def _fetch_from_gcp_secret_manager(self, secret_id: str) -> Optional[str]:
        """Fetches the secret payload from GCP Secret Manager."""
        if not GCP_SECRET_MANAGER_AVAILABLE:
            return None
        try:
            client = secretmanager.SecretManagerServiceClient()
            response = client.access_secret_version(request={"name": secret_id})
            return response.payload.data.decode("UTF-8")
        except Exception as e:
            logger.error(f"Error accessing Secret Manager: {e}")
            return None

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
