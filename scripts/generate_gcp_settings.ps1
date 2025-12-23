# Helper script to generate GCP settings
param (
    [Parameter(Mandatory = $true)]
    [string]$ProjectId,
    [string]$Prefix = "banking-enterprise"
)

$SettingsContent = @"
paths:
  raw: "gs://${Prefix}-bronze-${ProjectId}/raw"
  bronze: "gs://${Prefix}-bronze-${ProjectId}/bronze"
  silver: "gs://${Prefix}-silver-${ProjectId}/silver"
  gold: "gs://${Prefix}-gold-${ProjectId}/gold"
  quarantine: "gs://${Prefix}-quarantine-${ProjectId}/quarantine"
  logs: "logs" # Keep logs local or move to Cloud Logging

spark:
  app_name: "BankingEnterprisePipeline-GCP"
  driver_memory: "2g"
  executor_memory: "4g"
  executor_cores: 2
  shuffle_partitions: 10

security:
  encryption_key_env: "BANKING_ENCRYPTION_KEY"

quality:
  expected_columns:
    - "transaction_id"
    - "customer_id"
    - "email"
    - "pan"
    - "amount"
    - "currency"
    - "timestamp"
  min_amount: 0.0
  currency_len: 3
"@

Set-Content -Path "config/settings_gcp.yaml" -Value $SettingsContent
Write-Host "✅ Created config/settings_gcp.yaml with GCP paths." -ForegroundColor Green
Write-Host "To use it, set environment variable: `$env:BANKING_SETTINGS_FILE = 'config/settings_gcp.yaml'" -ForegroundColor Yellow
