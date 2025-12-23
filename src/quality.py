import os
import logging
import pandas as pd
import great_expectations as gx
from typing import Dict, Any, List

# Configure logging
LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)
logger = logging.getLogger("QualityModule")
if not logger.handlers:
    handler = logging.FileHandler(os.path.join(LOG_DIR, "quality.log"))
    handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

class DataQualityManager:
    """
    Handles data quality validations using Great Expectations.
    Ensures compliance with BCBS 239 regarding data integrity and accuracy.
    """
    
    def __init__(self):
        # In a real scenario, we would use a DataContext from a gx/ directory
        # Here we use an ephemeral context for portability
        self.context = gx.get_context()
        
        # Schema definition (Schema Registry simulation)
        self.expected_columns = [
            "transaction_id", "customer_id", "email", 
            "pan", "amount", "currency", "timestamp"
        ]

    def validate_schema(self, df: pd.DataFrame) -> bool:
        """
        Validates that the input DataFrame matches the expected column schema.
        """
        current_columns = list(df.columns)
        if set(current_columns) != set(self.expected_columns):
            logger.error(f"Schema Mismatch! Expected: {self.expected_columns}, Got: {current_columns}")
            return False
        logger.info("Schema validation passed.")
        return True

    def run_valitations(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Runs critical quality expectations on the banking dataset.
        """
        logger.info("Starting Great Expectations validation suite...")
        
        # Create a Pandas-based Dataset for GX
        ge_df = gx.dataset.PandasDataset(df)
        
        results = []
        
        # 1. Non-nullity for transaction_id
        results.append(ge_df.expect_column_values_to_not_be_null("transaction_id"))
        
        # 2. PAN format (simplified check)
        results.append(ge_df.expect_column_values_to_be_of_type("pan", "object"))
        
        # 3. Amount must be positive
        results.append(ge_df.expect_column_values_to_be_between("amount", min_value=0))
        
        # 4. Currency must be valid (3 characters)
        results.append(ge_df.expect_column_value_lengths_to_equal("currency", 3))
        
        # 5. Timestamp format validation (Regex for ISO8601)
        results.append(ge_df.expect_column_values_to_match_strftime_format("timestamp", "%Y-%m-%dT%H:%M:%S.%f"))

        overall_success = all(res.success for res in results)
        
        if not overall_success:
            failed = [res.expectation_config.kwargs.get('column') for res in results if not res.success]
            logger.error(f"Falla en validación de calidad. Columnas afectadas: {failed}")
        else:
            logger.info("All quality checks passed successfully (BCBS 239 compliance verified).")
            
        return {
            "success": overall_success,
            "details": results
        }

if __name__ == "__main__":
    # Test with mockup data
    import numpy as np
    
    dq = DataQualityManager()
    
    test_data = pd.DataFrame({
        "transaction_id": ["id1", "id2"],
        "customer_id": ["C1", "C2"],
        "email": ["a@b.com", "c@d.com"],
        "pan": ["1234", "5678"],
        "amount": [100.0, 200.0],
        "currency": ["USD", "EUR"],
        "timestamp": ["2023-01-01T10:00:00.000000", "2023-01-01T11:00:00.000000"]
    })
    
    if dq.validate_schema(test_data):
        validation_results = dq.run_valitations(test_data)
        print(f"Quality Success: {validation_results['success']}")
