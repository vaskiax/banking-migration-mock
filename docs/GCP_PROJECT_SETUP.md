# GCP Project Setup Guide - Banking Data Pipeline

This guide helps you create a fresh Google Cloud Platform (GCP) project from scratch and prepare it for our automated data pipeline.

## Phase 1: Automated Project Creation (CLI) [NEW]

We provide a script to handle project creation and billing linkage directly from your terminal.

1.  **Run the Creation Script**:
    ```powershell
    ./scripts/create_gcp_project.ps1 -ProjectId "your-unique-project-id"
    ```
    - The script will authenticate you, create the project, and list available **Billing Accounts**.
    - Copy your preferred `BILLING_ACCOUNT_ID` when prompted.

## Phase 2: Manual Console Setup (Optional)

## Phase 2: Setup Local Environment

You need the `gcloud` CLI installed on your machine.

1.  **Install SDK**: Follow [Google's installation guide](https://cloud.google.com/sdk/docs/install).
2.  **Login & Init**:
    ```powershell
    gcloud auth login
    gcloud init
    ```
    - Choose your new project when prompted.
3.  **Application Default Credentials**: Required for the Python code and Terraform to authenticate.
    ```powershell
    gcloud auth application-default login
    ```

## Phase 3: Automated Resource Provisioning

We have provided scripts to automate the rest of the setup.

### 1. Enable Required APIs
Run the provided PowerShell script to enable the Cloud Storage, Secret Manager, Dataproc, and Cloud Composer APIs:
```powershell
./scripts/enable_gcp_apis.ps1 -ProjectId "your-project-id"
```

### 2. Run Terraform & Key Setup
Deploy the buckets and the encryption key infrastructure:
```powershell
./scripts/gcp_deploy.ps1 -ProjectId "your-project-id"
```

## Troubleshooting

- **Permissions**: Ensure your account has the `Owner` or `Editor` role on the project.
- **Quota**: If API enablement fails, check if your project has billing enabled.
- **Terraform Error**: If you see "Project not found", verify the `ProjectId` passed to the script matches exactly what's in the GCP Console.
