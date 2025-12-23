# GCP Deployment Script for Banking Pipeline
# This script automates Terraform provisioning and Secret Manager population.

param (
    [Parameter(Mandatory = $true)]
    [string]$ProjectId,

    [string]$Prefix = "banking-enterprise",
    [string]$Region = "us-central1"
)

Write-Host "--- Initiating GCP Deployment for Project: $ProjectId ---" -ForegroundColor Cyan

# 0. Detect Terraform
$TerraformExe = "terraform"
if (Test-Path ".\terraform_bin\terraform.exe") {
    $TerraformExe = "..\terraform_bin\terraform.exe"
    Write-Host "Using portable Terraform found in terraform_bin." -ForegroundColor Gray
}

# 1. Terraform Init & Apply
Write-Host "[1/3] Provisioning Infrastructure with Terraform..." -ForegroundColor Green
Set-Location terraform
& $TerraformExe init
& $TerraformExe apply -var="project_id=$ProjectId" -var="prefix=$Prefix" -var="region=$Region" -auto-approve

# 2. Extract Outputs
Write-Host "[2/3] Extracting Terraform Outputs..." -ForegroundColor Green
$SecretId = & $TerraformExe output -raw secret_id
Set-Location ..

# 3. Populate Secret Manager
Write-Host "[3/3] Populating Secret Manager with Fernet Key..." -ForegroundColor Green
$FernetKey = .venv\Scripts\python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

# Using gcloud to add the first version
Write-Output "$FernetKey" | gcloud secrets versions add $SecretId --data-file=- --project=$ProjectId

Write-Host "--- GCP Deployment Completed Successfully! ---" -ForegroundColor Cyan
Write-Host "Medallion Buckets: $Prefix-bronze-$ProjectId, etc."
Write-Host "GCP Secret ID: $SecretId"
Write-Host "Next Step: Update config/settings.yaml with 'gs://' paths." -ForegroundColor Yellow
