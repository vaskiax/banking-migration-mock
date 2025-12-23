import pytest
import pandas as pd
import os
from src.security import SecurityManager
from src.quality import DataQualityManager

@pytest.fixture
def security_manager():
    """Fixture for SecurityManager with a consistent (or temporary) key."""
    return SecurityManager()

@pytest.fixture
def quality_manager():
    """Fixture for DataQualityManager."""
    return DataQualityManager()

def test_pan_encryption_is_reversible(security_manager):
    """Validate that encryption followed by decryption returns the original PAN."""
    original_pan = "4111222233334444"
    encrypted = security_manager.encrypt_pan(original_pan)
    decrypted = security_manager.decrypt_pan(encrypted)
    
    assert encrypted != original_pan
    assert decrypted == original_pan

def test_email_hashing_is_consistent(security_manager):
    """Validate that the same email always produces the same hash (deterministic)."""
    email = "test@bank.com"
    hash1 = security_manager.hash_email(email)
    hash2 = security_manager.hash_email(email)
    
    assert hash1 == hash2
    assert len(hash1) == 64  # SHA256 length

def test_quality_manager_detects_schema_mismatch(quality_manager):
    """Validate that the Quality Manager rejects a DataFrame with missing columns."""
    wrong_data = pd.DataFrame({
        "transaction_id": ["id1"],
        "amount": [100.0]
        # Missing other 5 columns
    })
    
    is_valid = quality_manager.validate_schema(wrong_data)
    assert is_valid is False

def test_quality_manager_detects_invalid_values(quality_manager):
    """Validate that the Quality Manager fails if amount is negative."""
    invalid_data = pd.DataFrame({
        "transaction_id": ["id1"],
        "customer_id": ["C1"],
        "email": ["a@b.com"],
        "pan": ["1234"],
        "amount": [-50.0],  # Critical failure point
        "currency": ["USD"],
        "timestamp": ["2023-01-01T10:00:00.000000"]
    })
    
    validation_result = quality_manager.run_valitations(invalid_data)
    assert validation_result["success"] is False
