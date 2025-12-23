# Technical Architecture: Enterprise Banking Pipeline

This document provides a deep dive into the engineering principles, design patterns, and module-specific implementations of the Banking Data Pipeline.

## 🏛️ System Design: The Medallion Architecture

The pipeline follows the **Medallion Architecture**, a data design pattern used to organize data into logical layers, increasing in quality and structure as it flows through the system.

### 1. Raw Layer (Bronze)
- **Source**: Simulated external banking systems (CSV).
- **Format**: Immutable, source-of-truth data.
- **Goal**: High-fidelity ingestion with zero transformation.
- **Governance**: Every batch is timestamped and partitioned for full auditability.

### 2. Validated Layer (Silver)
- **Transformation**: Data cleaning, deduplication, and PII anonymization.
- **Security**: Emails are hashed (SHA-256) and Card Numbers (PAN) are encrypted (Fernet AES).
- **Processing Engine**: Hybrid approach using **Polars** for ultra-fast local manipulation and **PySpark** for scalable dataset handling.

### 3. Analytics Layer (Gold)
- **Transformation**: Business aggregations (e.g., total volume by currency, customer behavior analysis).
- **Format**: Optimized Parquet tables for downstream BI and reporting.
- **Compliance**: Fully compliant with **BCBS 239** (data lineage and quality).

---

## 🛠️ Module-by-Module Breakdown

### 1. `SecurityManager` (The Shield)
*   **Location**: `src/security.py`
*   **Responsibility**: Manages all cryptographic operations.
*   **Key Features**:
    *   **Fernet Encryption**: Used for symmetric encryption of PCI-sensitive data (PAN).
    *   **Cryptographic Hashing**: SHA-256 implementation for email pseudonymization (GDPR compliant).
    *   **Cloud-Native Integration**: Natively supports **Google Cloud Secret Manager** for enterprise key rotation.

### 2. `DataQualityManager` (The Gatekeeper)
*   **Location**: `src/quality.py`
*   **Responsibility**: Enforces data integrity and schema contracts.
*   **Key Features**:
    *   **Great Expectations Integration**: Uses industry-standard assertion libraries for data validation.
    *   **Quarantine (DLQ) Pattern**: Instead of failing the entire pipeline on a bad row, it directs "contaminated" data to a `quarantine/` layer for manual audit, ensuring 100% pipeline uptime.

### 3. `BankingTransformer` (The Core)
*   **Location**: `src/transformer.py`
*   **Responsibility**: Orchestrates the movement and transformation of data between tiers.
*   **Key Features**:
    *   **Partitioning Engine**: Automatically organizes data into `year/month/day` structures.
    *   **Idempotency**: Designed to be re-run safely for any specific date without duplicating records.
    *   **Scalability**: Built to handle both local file systems and **Google Cloud Storage (GCS)** URIs.

### 4. `ConfigLoader` (The BRAIN)
*   **Location**: `src/config_loader.py`
*   **Responsibility**: Centralized configuration and validation.
*   **Key Features**:
    *   **Pydantic Validation**: Ensures `settings.yaml` is syntactically and logically correct before execution.
    *   **Dynamic Environments**: Supports switching between Local, Docker, and GCP modes via environment variables.

---

## 🚀 Performance Optimizations

1.  **Arrow Optimization**: Uses PyArrow to accelerate data transfers between Python and the Spark JVM.
2.  **Lazy Evaluation**: Heavily utilizes Spark's lazy evaluation for efficient query planning.
3.  **Local Memory Management**: Implements memory limits on Spark drivers to ensure stability in resource-constrained environments (like dev machines).

---

## 🧪 Testing Strategy

*   **Unit Testing**: Comprehensive `pytest` suite for security and quality modules.
*   **Smoke Testing**: Automated infrastructure validation scripts for GCP.
*   **Lineage Testing**: Integrated **OpenLineage** support for observability in production Airflow environments.
