# GDPR Compliance Documentation

## Data Protection by Design
The pipeline implements "Privacy by Design" through the `src/security.py` module.

## Key Controls

### 1. Pseudonymization (Hashing)
- **Field**: `email`
- **Method**: SHA256 Hashing.
- **Purpose**: Allows for statistical analysis of unique customers without exposing original identities.

### 2. Encryption (Ciphers)
- **Field**: `pan` (Primary Account Number)
- **Method**: Fernet Symmetric Encryption (AES-128 in CBC mode).
- **Key Management**: Keys are intended to be stored in Secure Vaults (simulated via Environment Variables).

### 3. Data Erasure
- The `transformer.py` module explicitly drops the original `email` and `pan` columns immediately after the security transformation, ensuring PII does not persist in the Silver or Gold layers.
