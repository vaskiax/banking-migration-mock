# GCP Deployment Script for Banking Pipeline (gcloud-native)
# This script automates resource provisioning using ONLY gcloud/gsutil.

param (
    [Parameter(Mandatory = $true)]
    [string]$ProjectId,

    [string]$Prefix = "banking-enterprise",
    [string]$Region = "us-central1"
)

Write-Host "--- Initiating gcloud-native GCP Deployment for Project: $ProjectId ---" -ForegroundColor Cyan

# 1. Create Cloud Storage Buckets
Write-Host "[1/5] Creating Medallion Buckets..." -ForegroundColor Green
$Buckets = @("bronze", "silver", "gold", "quarantine")
foreach ($Layer in $Buckets) {
    $BucketName = "${Prefix}-${Layer}-${ProjectId}"
    Write-Host "Creating $BucketName in $Region..."
    gsutil mb -p $ProjectId -l $Region gs://$BucketName | Out-Null
}

# 2. Create Service Account
Write-Host "[2/5] Creating Pipeline Service Account..." -ForegroundColor Green
$SaName = "${Prefix}-sa"
$SaEmail = "${SaName}@${ProjectId}.iam.gserviceaccount.com"
gcloud iam service-accounts create $SaName --display-name="Banking Pipeline SA" --project=$ProjectId

# 3. Grant IAM Permissions
Write-Host "[3/5] Granting IAM Permissions to Service Account..." -ForegroundColor Green
# Storage Admin for the buckets
foreach ($Layer in $Buckets) {
    $BucketName = "${Prefix}-${Layer}-${ProjectId}"
    gsutil iam ch "serviceAccount:${SaEmail}:objectAdmin" gs://$BucketName
}

# 4. Create and Populate Secret Manager
Write-Host "[4/5] Setting up Secret Manager..." -ForegroundColor Green
$SecretName = "${Prefix}-encryption-key"
gcloud secrets create $SecretName --replication-policy="automatic" --project=$ProjectId

# Generate and add key
$FernetKey = .venv\Scripts\python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
echo "$FernetKey" | gcloud secrets versions add $SecretName --data-file=- --project=$ProjectId

# Grant accessor permission to SA
gcloud secrets add-iam-policy-binding $SecretName --member="serviceAccount:${SaEmail}" --role="roles/secretmanager.secretAccessor" --project=$ProjectId

# 5. Summary
Write-Host "`n--- gcloud Deployment Completed Successfully! ---" -ForegroundColor Cyan
Write-Host "Service Account: $SaEmail"
Write-Host "Encryption Secret: $SecretName"
Write-Host "`nNEXT STEP: Update config/settings.yaml with these buckets:" -ForegroundColor Yellow
foreach ($Layer in $Buckets) {
    Write-Host "  $Layer: gs://${Prefix}-${Layer}-${ProjectId}"
}
