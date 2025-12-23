import os
import uuid
import logging
import csv
from datetime import datetime, date
from typing import List, Dict, Any
from faker import Faker

# Configure logging
LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(LOG_DIR, "generator.log")),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("DataGenerator")

class BankingDataGenerator:
    """
    Generates synthetic banking transaction data for the pipeline.
    Complies with requirements for transactional volume and schema.
    """
    
    def __init__(self, locale: str = "en_US"):
        self.fake = Faker(locale)
        self.columns = [
            "transaction_id", "customer_id", "email", 
            "pan", "amount", "currency", "timestamp"
        ]

    def generate_transaction(self, execution_date: date) -> Dict[str, Any]:
        """Generates a single synthetic transaction."""
        return {
            "transaction_id": str(uuid.uuid4()),
            "customer_id": self.fake.bothify(text='CUST-#####'),
            "email": self.fake.email(),
            "pan": self.fake.credit_card_number(card_type="visa"),
            "amount": round(self.fake.pyfloat(left_digits=4, right_digits=2, positive=True), 2),
            "currency": self.fake.currency_code(),
            "timestamp": self.fake.date_time_between_dates(
                datetime_start=datetime.combine(execution_date, datetime.min.time()),
                datetime_end=datetime.combine(execution_date, datetime.max.time())
            ).isoformat()
        }

    def generate_batch(self, count: int, execution_date: date, output_path: str) -> str:
        """
        Generates a batch of transactions and saves them to a CSV file.
        
        Args:
            count: Number of records to generate.
            execution_date: The date for which to generate data (Idempotence).
            output_path: Directory where the file will be saved.
            
        Returns:
            The path to the generated file.
        """
        logger.info(f"Starting batch generation: {count} records for date {execution_date}")
        
        filename = f"transactions_{execution_date.strftime('%Y%m%d')}.csv"
        full_path = os.path.join(output_path, filename)
        
        os.makedirs(output_path, exist_ok=True)
        
        try:
            with open(full_path, mode='w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=self.columns)
                writer.writeheader()
                
                for i in range(count):
                    writer.writerow(self.generate_transaction(execution_date))
                    if (i + 1) % 10000 == 0:
                        logger.info(f"Generated {i + 1} records...")
                        
            logger.info(f"Successfully generated batch file: {full_path}")
            return full_path
        except Exception as e:
            logger.error(f"Failed during record generation: {str(e)}")
            raise

if __name__ == "__main__":
    # Example usage for manual testing
    generator = BankingDataGenerator()
    today = datetime.now().date()
    raw_data_path = os.path.join("data", "raw")
    
    # Generate 100k records as per requirement
    generator.generate_batch(100000, today, raw_data_path)
