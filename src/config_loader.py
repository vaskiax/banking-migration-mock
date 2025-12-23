import os
import yaml
from pydantic import BaseModel, Field
from typing import List

class PathsConfig(BaseModel):
    raw: str
    bronze: str
    silver: str
    gold: str
    quarantine: str
    logs: str

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
    paths: PathsConfig
    spark: SparkConfig
    security: SecurityConfig
    quality: QualityConfig

def load_settings(config_path: str = "config/settings.yaml") -> Settings:
    """Loads settings from a YAML file and validates them using Pydantic."""
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Config file not found: {config_path}")
        
    with open(config_path, "r") as f:
        config_dict = yaml.safe_load(f)
        
    return Settings(**config_dict)

# Singleton instance for the project
settings = load_settings()
