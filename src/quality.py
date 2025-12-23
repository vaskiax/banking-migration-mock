import os
import logging
import pandas as pd
import great_expectations as gx
from typing import Dict, Any, List, Tuple
from src.config_loader import settings

# Configure logging
LOG_DIR = settings.paths.logs
os.makedirs(LOG_DIR, exist_ok=True)
logger = logging.getLogger("QualityModule")
if not logger.handlers:
    handler = logging.FileHandler(os.path.join(LOG_DIR, "quality.log"))
    handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

class DataQualityManager:
    """
    Handles data quality validations using Great Expectations and implement DLQ pattern.
    Ensures compliance with BCBS 239 regarding data integrity and accuracy.
    """
    
    def __init__(self):
        self.context = gx.get_context()
        self.expected_columns = settings.quality.expected_columns

    def validate_schema(self, df: pd.DataFrame) -> bool:
        """Validates that the input DataFrame matches the expected column schema."""
        current_columns = list(df.columns)
        if set(current_columns) != set(self.expected_columns):
            logger.error(f"Schema Mismatch! Expected: {self.expected_columns}, Got: {current_columns}")
            return False
        logger.info("Schema validation passed.")
        return True

    def run_quarantine_check(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Runs quality checks and splits the data into Valid and Quarantine (Invalid).
        Implements the Dead Letter Queue (DLQ) pattern.
        """
        logger.info(f"Starting Quarantine validation on {len(df)} records...")
        
        # 1. Basic type/null checks (Vectorized using Pandas for performance)
        is_valid = pd.Series(True, index=df.index)
        
        # Check non-nulls for critical fields
        is_valid &= df["transaction_id"].notnull()
        is_valid &= df["amount"].notnull()
        
        # Threshold checks (from config)
        is_valid &= df["amount"] >= settings.quality.min_amount
        
        # Currency length check
        is_valid &= df["currency"].str.len() == settings.quality.currency_len
        
        # Split Data
        df_valid = df[is_valid].copy()
        df_invalid = df[~is_valid].copy()
        
        # Log results
        valid_count = len(df_valid)
        invalid_count = len(df_invalid)
        
        if invalid_count > 0:
            logger.warning(f"Quarantine Alert: Found {invalid_count} invalid records. Redirecting to DLQ.")
        else:
            logger.info("All records passed quality checks.")
            
        return df_valid, df_invalid

if __name__ == "__main__":
    # Test with mockup data
    dq = DataQualityManager()
    
    test_data = pd.DataFrame({
        "transaction_id": ["id1", "id2", None], # None is invalid
        "customer_id": ["C1", "C2", "C3"],
        "email": ["a@b.com", "c@d.com", "e@f.com"],
        "pan": ["1234", "5678", "9012"],
        "amount": [100.0, -50.0, 300.0], # -50 is invalid
        "currency": ["USD", "EUR", "YEN"], # YEN is 3 chars (valid), but let's assume one is long
        "timestamp": ["2023-01-01T10", "2023-01-01T11", "2023-01-01T12"]
    })
    
    valid, quarantine = dq.run_quarantine_check(test_data)
    print(f"Valid records: {len(valid)}")
    print(f"Quarantined: {len(quarantine)}")
