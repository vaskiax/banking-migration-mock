provider "google" {
  project = var.project_id
  region  = var.region
}

variable "project_id" {
  description = "The GCP Project ID"
  type        = string
}

variable "region" {
  description = "The GCP Region"
  type        = string
  default     = "us-central1"
}

variable "prefix" {
  description = "Prefix for all resources"
  type        = string
  default     = "banking-pipeline"
}

# --- Cloud Storage Buckets (Medallion Layers) ---

resource "google_storage_bucket" "bronze" {
  name          = "${var.prefix}-bronze-${var.project_id}"
  location      = var.region
  force_destroy = true
  uniform_bucket_level_access = true
}

resource "google_storage_bucket" "silver" {
  name          = "${var.prefix}-silver-${var.project_id}"
  location      = var.region
  force_destroy = true
  uniform_bucket_level_access = true
}

resource "google_storage_bucket" "gold" {
  name          = "${var.prefix}-gold-${var.project_id}"
  location      = var.region
  force_destroy = true
  uniform_bucket_level_access = true
}

resource "google_storage_bucket" "quarantine" {
  name          = "${var.prefix}-quarantine-${var.project_id}"
  location      = var.region
  force_destroy = true
  uniform_bucket_level_access = true
}

# --- Secret Manager (Security Key) ---

resource "google_secret_manager_secret" "encryption_key" {
  secret_id = "${var.prefix}-encryption-key"

  replication {
    auto {}
  }
}

# --- Service Account (IAM) ---

resource "google_service_account" "pipeline_sa" {
  account_id   = "${var.prefix}-sa"
  display_name = "Banking Pipeline Service Account"
}

# Grant access to GCS
resource "google_storage_bucket_iam_member" "bronze_viewer" {
  bucket = google_storage_bucket.bronze.name
  role   = "roles/storage.objectAdmin"
  member = "serviceAccount:${google_service_account.pipeline_sa.email}"
}

resource "google_storage_bucket_iam_member" "silver_admin" {
  bucket = google_storage_bucket.silver.name
  role   = "roles/storage.objectAdmin"
  member = "serviceAccount:${google_service_account.pipeline_sa.email}"
}

resource "google_storage_bucket_iam_member" "gold_admin" {
  bucket = google_storage_bucket.gold.name
  role   = "roles/storage.objectAdmin"
  member = "serviceAccount:${google_service_account.pipeline_sa.email}"
}

# Grant access to Secret Manager
resource "google_secret_manager_secret_iam_member" "secret_viewer" {
  secret_id = google_secret_manager_secret.encryption_key.id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.pipeline_sa.email}"
}

# --- Output Variables ---

output "service_account_email" {
  value = google_service_account.pipeline_sa.email
}

output "bucket_names" {
  value = {
    bronze     = google_storage_bucket.bronze.name
    silver     = google_storage_bucket.silver.name
    gold       = google_storage_bucket.gold.name
    quarantine = google_storage_bucket.quarantine.name
  }
}

output "secret_id" {
  value = google_secret_manager_secret.encryption_key.id
}
