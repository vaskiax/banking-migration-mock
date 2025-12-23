# Enable Required GCP APIs for Banking Pipeline

param (
    [Parameter(Mandatory = $true)]
    [string]$ProjectId
)

$APIs = @(
    "storage.googleapis.com",             # Cloud Storage
    "secretmanager.googleapis.com",       # Secret Manager
    "dataproc.googleapis.com",            # Cloud Dataproc
    "composer.googleapis.com",            # Cloud Composer
    "compute.googleapis.com",             # Compute Engine (Required by Dataproc)
    "logging.googleapis.com",             # Cloud Logging
    "monitoring.googleapis.com"           # Cloud Monitoring
)

Write-Host "--- Enabling Essential APIs for Project: $ProjectId ---" -ForegroundColor Cyan

foreach ($API in $APIs) {
    Write-Host "Enabling $API..." -ForegroundColor Green
    gcloud services enable $API --project=$ProjectId
}

Write-Host "--- All APIs enabled successfully! ---" -ForegroundColor Cyan
