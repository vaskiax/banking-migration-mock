import os
import yaml
from pydantic import BaseModel, Field
from typing import List

class Paths(BaseModel):
    raw: str
    bronze: str
    silver: str
    gold: str
    quarantine: str
    logs: str

    def get_path(self, key: str) -> str:
        """Helper to get and potentially format cloud paths if needed."""
        path = getattr(self, key)
        return path

    @property
    def is_gcs(self) -> bool:
        """Returns True if any critical path is a GCS URI."""
        return any(p.startswith("gs://") for p in [self.raw, self.silver, self.gold])

class SparkConfig(BaseModel):
    app_name: str
    driver_memory: str
    executor_memory: str
    executor_cores: int
    shuffle_partitions: int

class SecurityConfig(BaseModel):
    encryption_key_env: str

class QualityConfig(BaseModel):
    expected_columns: List[str]
    min_amount: float
    currency_len: int

class Settings(BaseModel):
    paths: Paths
    spark: SparkConfig
    security: SecurityConfig
    quality: QualityConfig

def load_settings(config_path: str = None) -> Settings:
    """Loads settings from a YAML file. Defaults to BANKING_SETTINGS_FILE or settings.yaml."""
    if config_path is None:
        config_path = os.environ.get("BANKING_SETTINGS_FILE", "config/settings.yaml")
        
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Config file not found: {config_path}")
        
    with open(config_path, "r") as f:
        config_dict = yaml.safe_load(f)
        
    return Settings(**config_dict)

# Singleton instance for the project
settings = load_settings()
