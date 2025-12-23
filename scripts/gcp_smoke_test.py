import os
import sys
import logging

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from google.cloud import storage, secretmanager
from src.security import SecurityManager
from src.config_loader import settings

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger("GCP-SmokeTest")

def test_gcs_connection(bucket_name):
    logger.info(f"Testing GCS connection to bucket: {bucket_name}")
    try:
        client = storage.Client()
        bucket = client.get_bucket(bucket_name)
        logger.info(f"✅ GCS Connection Successful. Bucket {bucket_name} found.")
        
        # Test write
        blob = bucket.blob("smoke_test.txt")
        blob.upload_from_string("GCP Smoke Test Successful")
        logger.info(f"✅ GCS Write Successful.")
        
        # Test read
        content = blob.download_as_text()
        logger.info(f"✅ GCS Read Successful: '{content}'")
        
        # Cleanup
        blob.delete()
        logger.info(f"✅ GCS Cleanup Successful.")
        return True
    except Exception as e:
        logger.error(f"❌ GCS Connection Failed: {e}")
        return False

def test_secret_manager(secret_id):
    logger.info(f"Testing Secret Manager connection for secret: {secret_id}")
    try:
        # We'll use the SecurityManager directly to test the integration
        os.environ["GCP_SECRET_ID"] = secret_id
        sec_mgr = SecurityManager()
        
        if sec_mgr.key:
            logger.info("✅ Secret Manager Connection Successful.")
            logger.info(f"✅ Encryption Key loaded (Length: {len(sec_mgr.key)} bytes)")
            
            # Test encryption
            test_data = "PII Data"
            encrypted = sec_mgr.encrypt_pan(test_data)
            decrypted = sec_mgr.decrypt_pan(encrypted)
            
            if test_data == decrypted:
                logger.info("✅ Fernet Encryption/Decryption verified with GCP Key.")
                return True
        return False
    except Exception as e:
        logger.error(f"❌ Secret Manager Connection Failed: {e}")
        return False

if __name__ == "__main__":
    project_id = os.environ.get("GCP_PROJECT_ID")
    prefix = "banking-enterprise"
    
    if not project_id:
        logger.error("Usage: set GCP_PROJECT_ID env variable before running.")
        sys.exit(1)
        
    bronze_bucket = f"{prefix}-bronze-{project_id}"
    secret_full_id = f"projects/{project_id}/secrets/{prefix}-encryption-key/versions/latest"
    
    logger.info(f"--- Initiating GCP Smoke Test for project: {project_id} ---")
    
    gcs_ok = test_gcs_connection(bronze_bucket)
    sm_ok = test_secret_manager(secret_full_id)
    
    if gcs_ok and sm_ok:
        logger.info("--- 🚀 ALL GCP TESTS PASSED! Your environment is ready. ---")
    else:
        logger.error("--- ❌ SOME TESTS FAILED. Please check permissions and configuration. ---")
        sys.exit(1)
