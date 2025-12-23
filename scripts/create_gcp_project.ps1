# GCP Project Creation Script via CLI
# This script automates the creation of a new GCP project and its billing linkage.

param (
    [Parameter(Mandatory = $true)]
    [string]$ProjectId,

    [string]$OrganizationId, # Optional: For enterprise orgs
    [string]$BillingAccountId # Optional: If known, otherwise script will list
)

Write-Host "--- Initiating CLI-based GCP Project Creation: $ProjectId ---" -ForegroundColor Cyan

# 1. Login check
Write-Host "[1/5] Checking authentication..." -ForegroundColor Green
$AuthCheck = gcloud auth list --format="value(account)"
if (-not $AuthCheck) {
    Write-Host "Error: No authenticated account found. Please run 'gcloud auth login' first." -ForegroundColor Red
    exit
}

# 2. Create Project
Write-Host "[2/5] Creating project $ProjectId..." -ForegroundColor Green
if ($OrganizationId) {
    gcloud projects create $ProjectId --organization=$OrganizationId
}
else {
    gcloud projects create $ProjectId
}

if ($LASTEXITCODE -ne 0) {
    Write-Host "Project creation failed. Project ID might be taken or invalid." -ForegroundColor Red
    exit
}

# 3. Handle Billing
Write-Host "[3/5] Handling Billing Linkage..." -ForegroundColor Green
if (-not $BillingAccountId) {
    Write-Host "No Billing Account ID provided. Listing available accounts:" -ForegroundColor Yellow
    gcloud billing accounts list
    $BillingAccountId = Read-Host "Please enter the BILLING_ACCOUNT_ID you wish to link"
}

if ($BillingAccountId) {
    gcloud billing projects link $ProjectId --billing-account=$BillingAccountId
}
else {
    Write-Host "Skipping billing linkage. Note: API enablement will fail without billing." -ForegroundColor Yellow
}

# 4. Set as default and fix Quota Project
Write-Host "[4/5] Setting $ProjectId as default and updating ADC quota project..." -ForegroundColor Green
gcloud config set project $ProjectId
gcloud auth application-default set-quota-project $ProjectId

# 5. Next Steps
Write-Host "[5/5] Project $ProjectId is ready for API enablement." -ForegroundColor Green

Write-Host "`n--- Project Creation Completed! ---" -ForegroundColor Cyan
Write-Host "Next Step: Run ./scripts/enable_gcp_apis.ps1 -ProjectId $ProjectId" -ForegroundColor Yellow
