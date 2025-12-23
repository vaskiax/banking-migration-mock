import os
import logging
from src.patches import apply_spark_patches
apply_spark_patches()
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, to_date, year, month, dayofmonth, sha2, pandas_udf
from pyspark.sql.types import StringType
import pandas as pd
from src.config_loader import settings
from src.security import SecurityManager

# Configure logging
LOG_DIR = settings.paths.logs
os.makedirs(LOG_DIR, exist_ok=True)
logger = logging.getLogger("TransformerModule")
if not logger.handlers:
    handler = logging.FileHandler(os.path.join(LOG_DIR, "transformer.log"))
    handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

class BankingTransformer:
    """
    Handles data transformations using Optimized PySpark.
    Implements security (GDPR), Arrow-Vectorized UDFs, and Quarantine handling.
    """
    
    def __init__(self):
        self.security = SecurityManager()
        
        # Instruction 3: Spark Tuning from Config & Enable Arrow
        self.spark = SparkSession.builder \
            .appName(settings.spark.app_name) \
            .config("spark.driver.memory", settings.spark.driver_memory) \
            .config("spark.executor.memory", settings.spark.executor_memory) \
            .config("spark.executor.cores", settings.spark.executor_cores) \
            .config("spark.sql.shuffle.partitions", settings.spark.shuffle_partitions) \
            .config("spark.sql.execution.arrow.pyspark.enabled", "true") \
            .getOrCreate()
        logger.info("Spark Session initialized successfully.")

    def handle_quarantine(self, df_invalid: pd.DataFrame, execution_date: str):
        """Saves invalid records to the quarantine directory (Instruction 2)."""
        if df_invalid.empty:
            return
            
        quarantine_dir = os.path.join(settings.paths.quarantine, execution_date)
        os.makedirs(quarantine_dir, exist_ok=True)
        
        output_path = os.path.join(quarantine_dir, "invalid_records.csv")
        df_invalid.to_csv(output_path, index=False)
        logger.warning(f"DLQ: Saved {len(df_invalid)} invalid records to {output_path}")

    def transform_to_silver(self, df_valid: pd.DataFrame, filename: str) -> str:
        """Applies security transformations using Vectorized (Pandas) UDFs."""
        logger.info(f"Spark: Vectorizing security logic for {len(df_valid)} records...")
        
        spark_df = self.spark.createDataFrame(df_valid)
        
        # Instruction 3: Vectorized Hashing (Native) and Encryption (Pandas UDF)
        spark_df = spark_df.withColumn("email_hashed", sha2(col("email"), 256))
        
        @pandas_udf(StringType())
        def encrypt_pan_series(pan_series: pd.Series) -> pd.Series:
            return pan_series.apply(self.security.encrypt_pan)
        
        spark_df = spark_df.withColumn("pan_encrypted", encrypt_pan_series(col("pan")))
        
        # GDPR Minimization: Drop raw PII
        df_silver = spark_df.drop("email", "pan")
        
        silver_dir = settings.paths.silver
        os.makedirs(silver_dir, exist_ok=True)
        silver_file = filename.replace(".csv", "_silver.parquet")
        silver_path = os.path.join(silver_dir, silver_file)
        
        df_silver.write.mode("overwrite").parquet(silver_path)
        logger.info(f"Silver layer published: {silver_path}")
        return silver_path

    def silver_to_gold(self, silver_path: str):
        """Distributed aggregation to Gold layer."""
        logger.info("Spark: Processing Gold Aggregations...")
        
        spark_df = self.spark.read.parquet(silver_path)
        
        spark_df = spark_df.withColumn("date", to_date(col("timestamp"))) \
                           .withColumn("year", year(col("timestamp"))) \
                           .withColumn("month", month(col("timestamp"))) \
                           .withColumn("day", dayofmonth(col("timestamp")))
        
        gold_df = spark_df.groupBy("date", "currency", "year", "month", "day") \
                          .agg({"amount": "sum", "transaction_id": "count"}) \
                          .withColumnRenamed("sum(amount)", "total_amount") \
                          .withColumnRenamed("count(transaction_id)", "tx_count")
        
        gold_dir = settings.paths.gold
        os.makedirs(gold_dir, exist_ok=True)
        
        (gold_df.write
            .mode("overwrite")
            .partitionBy("year", "month", "day")
            .parquet(gold_dir))
            
        logger.info(f"Gold Tier updated at: {gold_dir}")
        return gold_dir

    def close(self):
        if self.spark:
            self.spark.stop()
