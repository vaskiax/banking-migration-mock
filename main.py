import os
import logging
import pandas as pd
from datetime import datetime
from src.generator import BankingDataGenerator
from src.quality import DataQualityManager
from src.transformer import BankingTransformer

# Setup Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("PipelineRunner")

def run_pipeline():
    """ Runs the full pipeline end-to-end for demonstration. """
    
    # 1. Initialization
    execution_date = datetime.now().date()
    raw_path = os.path.join("data", "raw")
    silver_path = os.path.join("data", "silver")
    gold_path = os.path.join("data", "gold")
    
    # 2. Generation
    logger.info("--- PHASE 1: DATA GENERATION ---")
    gen = BankingDataGenerator()
    csv_file = gen.generate_batch(10000, execution_date, raw_path) # 10k for quick test
    
    # 3. Quality Validation
    logger.info("--- PHASE 2: DATA QUALITY (BCBS 239) ---")
    dq = DataQualityManager()
    df_raw = pd.read_csv(csv_file)
    
    if not dq.validate_schema(df_raw):
        logger.error("Pipeline aborted: Schema mismatch.")
        return
        
    quality_result = dq.run_valitations(df_raw)
    if not quality_result["success"]:
        logger.error("Pipeline aborted: Quality issues found.")
        return

    # 4. Transformation & Security (GDPR)
    logger.info("--- PHASE 3: TRANSFORMATION & SECURITY (GDPR) ---")
    transformer = BankingTransformer()
    try:
        silver_file = transformer.bronze_to_silver(csv_file, silver_path)
        transformer.silver_to_gold(silver_file, gold_path)
    finally:
        transformer.close()

    logger.info("--- PIPELINE COMPLETED SUCCESSFULLY ---")
    logger.info(f"Check logs/ and data/ directories for results.")

if __name__ == "__main__":
    run_pipeline()
