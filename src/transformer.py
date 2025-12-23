import os
import logging
import polars as pl
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, to_date, year, month, dayofmonth
from src.security import SecurityManager
import pandas as pd

# Configure logging
LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)
logger = logging.getLogger("TransformerModule")
if not logger.handlers:
    handler = logging.FileHandler(os.path.join(LOG_DIR, "transformer.log"))
    handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

class BankingTransformer:
    """
    Handles data transformations using Polars for fast local processing
    and PySpark for heavy-lifting/aggregation.
    Implements security (GDPR) and idempotency for backfilling.
    """
    
    def __init__(self):
        self.security = SecurityManager()
        self.spark = SparkSession.builder \
            .appName("BankingGoldPipeline") \
            .getOrCreate()

    def bronze_to_silver(self, input_path: str, output_dir: str):
        """
        Step 1: In-memory fast pre-processing with Polars.
        Applies Hashing and Encryption (GDPR compliance).
        """
        logger.info(f"Polars: Reading raw data from {input_path}")
        
        # Using Polars for fast scan and map
        df = pl.read_csv(input_path)
        
        # Apply security transformations
        # Polars map_elements for custom Python functions (security logic)
        df = df.with_columns([
            pl.col("email").map_elements(self.security.hash_email, return_dtype=pl.String).alias("email_hashed"),
            pl.col("pan").map_elements(self.security.encrypt_pan, return_dtype=pl.String).alias("pan_encrypted")
        ])
        
        # Remove original PII columns
        df_silver = df.drop(["email", "pan"])
        
        # Ensure output directory exists
        os.makedirs(output_dir, exist_ok=True)
        silver_file = os.path.basename(input_path).replace(".csv", "_silver.parquet")
        silver_path = os.path.join(output_dir, silver_file)
        
        df_silver.write_parquet(silver_path)
        logger.info(f"Silver data saved locally: {silver_path}")
        return silver_path

    def silver_to_gold(self, silver_path: str, gold_dir: str):
        """
        Step 2: Distributed processing with PySpark for aggregations.
        Implements Idempotent Upsert logic and Partitioning (FinOps).
        """
        logger.info("Spark: Initializing aggregation to Gold layer...")
        
        spark_df = self.spark.read.parquet(silver_path)
        
        # Add date parts for partitioning
        spark_df = spark_df.withColumn("date", to_date(col("timestamp"))) \
                           .withColumn("year", year(col("timestamp"))) \
                           .withColumn("month", month(col("timestamp"))) \
                           .withColumn("day", dayofmonth(col("timestamp")))
        
        # Example Aggregation: Total Amount by Currency and Date
        gold_df = spark_df.groupBy("date", "currency", "year", "month", "day") \
                          .agg({"amount": "sum", "transaction_id": "count"}) \
                          .withColumnRenamed("sum(amount)", "total_amount") \
                          .withColumnRenamed("count(transaction_id)", "tx_count")
        
        # Idempotent Save: Overwrite partition to avoid duplicates during backfilling
        os.makedirs(gold_dir, exist_ok=True)
        
        (gold_df.write
            .mode("overwrite")
            .partitionBy("year", "month", "day")
            .parquet(gold_dir))
            
        logger.info(f"Gold data (Nivel Oro) published at: {gold_dir}")
        return gold_dir

    def close(self):
        self.spark.stop()

if __name__ == "__main__":
    # This would be part of the DAG/Orchestrator
    pass
