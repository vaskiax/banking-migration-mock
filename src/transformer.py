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
        # Instruction 3: Spark Tuning - Explicit Memory and Core allocation
        self.spark = SparkSession.builder \
            .appName("BankingGoldPipeline") \
            .config("spark.driver.memory", "2g") \
            .config("spark.executor.memory", "4g") \
            .config("spark.executor.cores", "2") \
            .config("spark.sql.shuffle.partitions", "10") \
            .getOrCreate()

    def bronze_to_silver(self, input_path: str, output_dir: str):
        """
        Step 1: Efficient processing.
        Move security logic to Spark to leverage distributed UDFs and native functions.
        """
        logger.info(f"Spark: Reading raw data from {input_path}")
        
        # We read with Spark directly to leverage native functions easily
        spark_df = self.spark.read.csv(input_path, header=True, inferSchema=True)
        
        from pyspark.sql.functions import sha2, udf
        from pyspark.sql.types import StringType
        
        # 1. Native SHA256 for email (Highly Efficient)
        spark_df = spark_df.withColumn("email_hashed", sha2(col("email"), 256))
        
        # 2. Vectorized-like UDF for Encryption (Fernet)
        encrypt_udf = udf(self.security.encrypt_pan, StringType())
        spark_df = spark_df.withColumn("pan_encrypted", encrypt_udf(col("pan")))
        
        # Remove original PII columns (GDPR Minimization)
        df_silver = spark_df.drop("email", "pan")
        
        # Ensure output directory exists
        os.makedirs(output_dir, exist_ok=True)
        silver_file = os.path.basename(input_path).replace(".csv", "_silver.parquet")
        silver_path = os.path.join(output_dir, silver_file)
        
        # Write silver layer
        df_silver.write.mode("overwrite").parquet(silver_path)
        logger.info(f"Silver data saved: {silver_path}")
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
