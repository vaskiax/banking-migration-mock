import os
import logging
from src.patches import apply_spark_patches
apply_spark_patches()
import pandas as pd
from datetime import datetime
from src.config_loader import settings
from src.generator import BankingDataGenerator
from src.quality import DataQualityManager
from src.transformer import BankingTransformer

# Setup Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("PipelineRunner")

def run_pipeline(records_count: int = 1000):
    """ Runs the full Enterprise-Grade pipeline end-to-end. """
    
    execution_date = datetime.now().date()
    ds_str = execution_date.strftime('%Y-%m-%d')
    
    # 1. Initialization from Config
    logger.info(f"--- STARTING PIPELINE: {settings.spark.app_name} ---")
    
    # 2. Generation (Bronze/Raw)
    logger.info("PHASE 1: INGESTION")
    gen = BankingDataGenerator()
    csv_file = gen.generate_batch(records_count, execution_date, settings.paths.raw)
    
    # 3. Quality & Quarantine (DLQ Pattern)
    logger.info("PHASE 2: QUALITY & QUARANTINE")
    dq = DataQualityManager()
    df_raw = pd.read_csv(csv_file)
    
    if not dq.validate_schema(df_raw):
        logger.error("FATAL: Schema Registry validation failed. Terminating pipeline.")
        return
        
    df_valid, df_invalid = dq.run_quarantine_check(df_raw)
    
    # 4. Processing Valid Records & Storing Quarantine
    logger.info("PHASE 3: TRANSFORMATION & ENCRYPTION")
    transformer = BankingTransformer()
    try:
        # Handle Quarantine
        transformer.handle_quarantine(df_invalid, ds_str)
        
        # Proceed with Silver and Gold for Valid data
        if not df_valid.empty:
            silver_file = transformer.transform_to_silver(df_valid, os.path.basename(csv_file))
            transformer.silver_to_gold(silver_file)
        else:
            logger.warning("No valid records found in this batch. Gold tier not updated.")
            
    finally:
        transformer.close()

    logger.info("--- ENTERPRISE PIPELINE COMPLETED ---")
    logger.info(f"Logs: {settings.paths.logs} | Quarantine: {settings.paths.quarantine}")

if __name__ == "__main__":
    # Run with 10k records by default for enterprise test
    run_pipeline(10000)
