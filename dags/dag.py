import os
import logging
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.sensors.filesystem import FileSensor
from src.generator import BankingDataGenerator
from src.quality import DataQualityManager
from src.transformer import BankingTransformer
import pandas as pd

# Default arguments for the DAG (BCBS 239 & SLA Requirements)
default_args = {
    'owner': 'DataArchitect',
    'depends_on_past': True,
    'start_date': datetime(2023, 12, 1),
    'email_on_failure': True,
    'retries': 3,
    'retry_delay': timedelta(minutes=5),
}

# Define the DAG
dag = DAG(
    'banking_mission_critical_pipeline',
    default_args=default_args,
    description='Gold Level Pipeline for Banking Migration',
    schedule_interval='@daily',
    catchup=True
)

def generate_data(**kwargs):
    """
    Step 1: Ingest data from simulated Mainframe/CSV.
    """
    execution_date = kwargs['ds_nodash']
    raw_path = os.path.join("data", "raw")
    gen = BankingDataGenerator()
    # Generate 100k records as per mission critical requirements
    file_path = gen.generate_batch(100000, datetime.strptime(execution_date, '%Y%m%d').date(), raw_path)
    kwargs['ti'].xcom_push(key='raw_file', value=file_path)

def validate_quality(**kwargs):
    """
    Step 2: Great Expectations Validation (Compliance check).
    """
    raw_file = kwargs['ti'].xcom_pull(key='raw_file', task_ids='ingest_raw_data')
    df = pd.read_csv(raw_file)
    
    dq = DataQualityManager()
    if not dq.validate_schema(df):
        raise ValueError("Schema Registry validation failed!")
        
    quality_result = dq.run_valitations(df)
    if not quality_result["success"]:
        raise ValueError(f"Falla en validación de calidad: {quality_result}")

def transform_to_silver_and_gold(**kwargs):
    """
    Step 3: Transform and secure data (Polars & Spark).
    """
    raw_file = kwargs['ti'].xcom_pull(key='raw_file', task_ids='ingest_raw_data')
    silver_path = os.path.join("data", "silver")
    gold_path = os.path.join("data", "gold")
    
    transformer = BankingTransformer()
    try:
        silver_file = transformer.bronze_to_silver(raw_file, silver_path)
        transformer.silver_to_gold(silver_file, gold_path)
        
        # Simula auditoría con Control-M (Requisito de la IA)
        logger = logging.getLogger("AirflowDAG")
        logger.info(f"API CALL: auditoria_centralizada(pipeline='banking', status='SUCCESS', date='{kwargs['ds']}')")
    finally:
        transformer.close()

# define tasks
t1 = PythonOperator(
    task_id='ingest_raw_data',
    python_callable=generate_data,
    dag=dag,
)

t2 = PythonOperator(
    task_id='validate_quality_gx',
    python_callable=validate_quality,
    dag=dag,
)

t3 = PythonOperator(
    task_id='transform_and_secure',
    python_callable=transform_to_silver_and_gold,
    dag=dag,
)

# Lineage and dependencies
t1 >> t2 >> t3
