# Security, Privacy & Compliance Manifest

This document outlines how the Banking Data Pipeline adheres to global financial regulations and data protection standards.

## 🇪🇺 GDPR Compliance (General Data Protection Regulation)

The pipeline implements **Privacy by Design** through several key mechanisms:

### 1. Pseudonymization (Art. 4, Art. 25)
- **Hashing**: All PII (Emails) are pseudonymized using SHA-256 with a secure salt. This allows for data analysis while ensuring the individual remains non-identifiable in the Silver and Gold layers.
- **Minimization**: Original raw data is restricted to the Bronze layer with strictly controlled access.

### 2. Right to Erasure / Right to Access
- **Partitioned Storage**: Data is partitioned by time and customer attributes, facilitating targeted data deletion or retrieval if requested by a data subject.

---

## 💳 PCI-DSS Standards (Payment Card Industry)

For handling Primary Account Numbers (PAN / Credit Card data), the system utilizes:

### 1. Strong Cryptography
- **AES-256 (Fernet)**: All card numbers are encrypted using symmetric AES-256 encryption. The system NEVER stores plain-text PAN in its databases or logs.
- **Immediate Discard**: The plain-text PAN is discarded immediately after the encryption process in the Silver tier.

### 2. Secure Key Management
- **Hardware-Backed Security**: In cloud environments, keys are managed by **Google Cloud Secret Manager**, ensuring encryption keys are never stored alongside the data they protect.

---

## 🏦 BCBS 239 (Principles for Effective Risk Data Aggregation)

To meet the Basel Committee's standards for risk reporting, the pipeline provides:

### 1. Data Lineage & Traceability
- **OpenLineage Integration**: The pipeline captures metadata for every transformation step, providing a full audit trail from the Raw CSV to the Final Gold Report.
- **Metadata Management**: Airflow DAGs record execution times, source systems, and data owners.

### 2. Data Quality & Accuracy
- **Zero-Trust Validation**: Every batch undergoes multi-point inspection via **Great Expectations**.
- **Quarantine Auditing**: Invalid records are not lost but moved to a dedicated audit bucket for compliance review and re-processing.

---

## 🔐 Infrastructure Security

- **Principle of Least Privilege (PoLP)**: Terraform provisions a dedicated Service Account for the pipeline, restricted only to the specific GCS buckets and Secrets it requires.
- **Audit Logging**: All system interactions are logged to **Cloud Logging** to ensure a permanent record of who accessed or modified the data.

---

## ⚖️ Audit Readiness

The pipeline generates an "Audit Signature" for every run, including:
- Data quality validation results.
- Encryption status confirmation.
- Execution source (Local, Docker, or Cloud).
- Timestamped data drift snapshots.
