terraform {
  required_version = ">= 1.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
    google-beta = {
      source  = "hashicorp/google-beta"
      version = "~> 5.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.5"
    }
  }
}

provider "google-beta" {
  project = var.project_id
  region  = var.region
}

provider "google" {
  project = var.project_id
  region  = var.region
}

# Enable required APIs
resource "google_project_service" "required_apis" {
  for_each = toset([
    "run.googleapis.com",
    "sqladmin.googleapis.com",
    "secretmanager.googleapis.com",
    "artifactregistry.googleapis.com",
    "cloudbuild.googleapis.com",
    "vpcaccess.googleapis.com",
    "compute.googleapis.com",
    "servicenetworking.googleapis.com",
  ])

  service            = each.value
  disable_on_destroy = false
}

# VPC Network for private IP connectivity
resource "google_compute_network" "vpc" {
  name                    = "${var.service_name}-vpc"
  auto_create_subnetworks = false

  depends_on = [google_project_service.required_apis]
}

# Subnet for VPC (required for VPC connector)
resource "google_compute_subnetwork" "subnet" {
  name          = "${var.service_name}-subnet"
  ip_cidr_range = "10.0.0.0/24"
  region        = var.region
  network       = google_compute_network.vpc.id

  depends_on = [google_compute_network.vpc]
}

# Allocate IP range for Cloud SQL private service connection
resource "google_compute_global_address" "private_ip_address" {
  name          = "${var.service_name}-private-ip"
  purpose       = "VPC_PEERING"
  address_type  = "INTERNAL"
  prefix_length = 16
  network       = google_compute_network.vpc.id

  depends_on = [google_project_service.required_apis]
}

# Private VPC connection for Cloud SQL
resource "google_service_networking_connection" "private_vpc_connection" {
  network                 = google_compute_network.vpc.id
  service                 = "servicenetworking.googleapis.com"
  reserved_peering_ranges = [google_compute_global_address.private_ip_address.name]

  depends_on = [google_project_service.required_apis]
}

# Serverless VPC Access Connector for Cloud Run
resource "google_vpc_access_connector" "connector" {
  name          = "${var.service_name}-vpc-connector"
  region        = var.region
  network       = google_compute_network.vpc.name
  ip_cidr_range = "10.8.0.0/28"

  # Minimum instances for cost optimization (e2-micro)
  min_instances = 2
  max_instances = 3
  machine_type  = "e2-micro"

  depends_on = [
    google_project_service.required_apis,
    google_compute_network.vpc,
    google_compute_subnetwork.subnet
  ]
}

# Generate random password for database user
resource "random_password" "db_password" {
  length  = 32
  special = true
}

# Generate random secret key for JWT
resource "random_password" "secret_key" {
  length  = 64
  special = false
}

# Cloud SQL PostgreSQL Instance (Cost-optimized: db-f1-micro)
resource "google_sql_database_instance" "postgres" {
  name             = "${var.service_name}-db-${var.environment}"
  database_version = "POSTGRES_15"
  region           = var.region

  # Single-zone for cost savings
  settings {
    tier              = "db-f1-micro" # Cheapest option: shared CPU, 614MB RAM
    availability_type = "ZONAL"       # Single-zone (not HA)
    disk_type         = "PD_HDD"      # Standard HDD (cheaper than SSD)
    disk_size         = 10            # Minimum size in GB

    # Automated backups
    backup_configuration {
      enabled            = true
      start_time         = "03:00" # 3 AM UTC
      point_in_time_recovery_enabled = false # Disable for cost savings
      transaction_log_retention_days = 7
      backup_retention_settings {
        retained_backups = 7
      }
    }

    # IP configuration - private IP only (no public IP)
    ip_configuration {
      ipv4_enabled    = false
      private_network = google_compute_network.vpc.id
      ssl_mode        = "ALLOW_UNENCRYPTED_AND_ENCRYPTED"
    }

    # Maintenance window
    maintenance_window {
      day          = 7 # Sunday
      hour         = 3 # 3 AM
      update_track = "stable"
    }
  }

  deletion_protection = true # Prevent accidental deletion

  depends_on = [
    google_project_service.required_apis,
    google_service_networking_connection.private_vpc_connection
  ]
}

# Create database
resource "google_sql_database" "database" {
  name     = var.db_name
  instance = google_sql_database_instance.postgres.name
}

# Create database user
resource "google_sql_user" "user" {
  name     = var.db_user
  instance = google_sql_database_instance.postgres.name
  password = random_password.db_password.result
}

# Store DB password in Secret Manager
resource "google_secret_manager_secret" "db_password" {
  secret_id = "${var.service_name}-db-password"

  replication {
    auto {}
  }

  depends_on = [google_project_service.required_apis]
}

resource "google_secret_manager_secret_version" "db_password" {
  secret      = google_secret_manager_secret.db_password.id
  secret_data = random_password.db_password.result
}

# Store JWT secret key in Secret Manager
resource "google_secret_manager_secret" "secret_key" {
  secret_id = "${var.service_name}-secret-key"

  replication {
    auto {}
  }

  depends_on = [google_project_service.required_apis]
}

resource "google_secret_manager_secret_version" "secret_key" {
  secret      = google_secret_manager_secret.secret_key.id
  secret_data = random_password.secret_key.result
}

# Store initial admin email in Secret Manager (optional - for bootstrap)
resource "google_secret_manager_secret" "admin_email" {
  count     = var.initial_admin_email != "" ? 1 : 0
  secret_id = "${var.service_name}-admin-email"

  replication {
    auto {}
  }

  depends_on = [google_project_service.required_apis]
}

resource "google_secret_manager_secret_version" "admin_email" {
  count       = var.initial_admin_email != "" ? 1 : 0
  secret      = google_secret_manager_secret.admin_email[0].id
  secret_data = var.initial_admin_email
}

# Store initial admin password in Secret Manager (optional - for bootstrap)
resource "google_secret_manager_secret" "admin_password" {
  count     = var.initial_admin_password != "" ? 1 : 0
  secret_id = "${var.service_name}-admin-password"

  replication {
    auto {}
  }

  depends_on = [google_project_service.required_apis]
}

resource "google_secret_manager_secret_version" "admin_password" {
  count       = var.initial_admin_password != "" ? 1 : 0
  secret      = google_secret_manager_secret.admin_password[0].id
  secret_data = var.initial_admin_password
}

# Artifact Registry Repository for Docker images
resource "google_artifact_registry_repository" "repo" {
  location      = var.region
  repository_id = var.service_name
  description   = "Docker repository for ${var.service_name}"
  format        = "DOCKER"

  depends_on = [google_project_service.required_apis]
}

# Service Account for Cloud Run
resource "google_service_account" "cloudrun_sa" {
  account_id   = "${var.service_name}-sa"
  display_name = "Service Account for ${var.service_name} Cloud Run"
}

# Grant Cloud SQL Client role to service account
resource "google_project_iam_member" "cloudrun_sql_client" {
  project = var.project_id
  role    = "roles/cloudsql.client"
  member  = "serviceAccount:${google_service_account.cloudrun_sa.email}"
}

# Grant Secret Manager Secret Accessor role to service account
resource "google_secret_manager_secret_iam_member" "db_password_access" {
  secret_id = google_secret_manager_secret.db_password.id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.cloudrun_sa.email}"
}

resource "google_secret_manager_secret_iam_member" "secret_key_access" {
  secret_id = google_secret_manager_secret.secret_key.id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.cloudrun_sa.email}"
}

# Grant Secret Manager access to admin email (if created)
resource "google_secret_manager_secret_iam_member" "admin_email_access" {
  count     = var.initial_admin_email != "" ? 1 : 0
  secret_id = google_secret_manager_secret.admin_email[0].id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.cloudrun_sa.email}"
}

# Grant Secret Manager access to admin password (if created)
resource "google_secret_manager_secret_iam_member" "admin_password_access" {
  count     = var.initial_admin_password != "" ? 1 : 0
  secret_id = google_secret_manager_secret.admin_password[0].id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.cloudrun_sa.email}"
}

# Cloud Run Service
resource "google_cloud_run_v2_service" "app" {
  name     = var.service_name
  location = var.region
  ingress  = "INGRESS_TRAFFIC_ALL"

  template {
    service_account = google_service_account.cloudrun_sa.email

    # VPC connector for private IP access to Cloud SQL
    vpc_access {
      connector = google_vpc_access_connector.connector.id
      egress    = "PRIVATE_RANGES_ONLY" # Only use VPC for private IPs
    }

    # Cost optimization: scale to zero
    scaling {
      min_instance_count = 0 # Scale to zero when idle
      max_instance_count = var.max_instances
    }

    # Cloud SQL connection via Auth Proxy sidecar
    volumes {
      name = "cloudsql"
      cloud_sql_instance {
        instances = [google_sql_database_instance.postgres.connection_name]
      }
    }

    containers {
      # You'll need to build and push the image first
      # Example: gcloud builds submit --tag ${var.region}-docker.pkg.dev/${var.project_id}/${var.service_name}/${var.service_name}:latest
      image = var.container_image

      # Resource limits (cost-optimized)
      resources {
        limits = {
          cpu    = "1"
          memory = "512Mi"
        }
        cpu_idle = true # CPU throttling when idle for cost savings
      }

      # Environment variables
      env {
        name  = "DATABASE_URL"
        value = "postgresql://${var.db_user}:${random_password.db_password.result}@127.0.0.1:5432/${var.db_name}?host=/cloudsql/${google_sql_database_instance.postgres.connection_name}"
      }

      env {
        name = "SECRET_KEY"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.secret_key.secret_id
            version = "latest"
          }
        }
      }

      env {
        name  = "ALGORITHM"
        value = "HS256"
      }

      env {
        name  = "ACCESS_TOKEN_EXPIRE_MINUTES"
        value = "30"
      }

      env {
        name  = "APP_NAME"
        value = var.app_name
      }

      env {
        name  = "DEBUG"
        value = "False"
      }

      env {
        name  = "INVITE_EXPIRATION_DAYS"
        value = "7"
      }

      # Admin bootstrap credentials (optional - only used if database is empty)
      # These are used by the automatic bootstrap script on container startup
      dynamic "env" {
        for_each = var.initial_admin_email != "" ? [1] : []
        content {
          name = "ADMIN_EMAIL"
          value_source {
            secret_key_ref {
              secret  = google_secret_manager_secret.admin_email[0].secret_id
              version = "latest"
            }
          }
        }
      }

      dynamic "env" {
        for_each = var.initial_admin_password != "" ? [1] : []
        content {
          name = "ADMIN_PASSWORD"
          value_source {
            secret_key_ref {
              secret  = google_secret_manager_secret.admin_password[0].secret_id
              version = "latest"
            }
          }
        }
      }

      # Health check configuration
      startup_probe {
        http_get {
          path = "/health"
          port = 8080
        }
        initial_delay_seconds = 10
        timeout_seconds       = 3
        period_seconds        = 10
        failure_threshold     = 3
      }

      liveness_probe {
        http_get {
          path = "/health"
          port = 8080
        }
        initial_delay_seconds = 30
        timeout_seconds       = 3
        period_seconds        = 30
        failure_threshold     = 3
      }
    }
  }

  depends_on = [
    google_project_service.required_apis,
    google_sql_database_instance.postgres,
    google_secret_manager_secret_version.db_password,
    google_secret_manager_secret_version.secret_key,
    google_vpc_access_connector.connector,
  ]

  # Ignore changes to the container image after initial deployment
  # This allows you to update the image via gcloud or CI/CD without Terraform reverting it
  lifecycle {
    ignore_changes = [
      template[0].containers[0].image,
    ]
  }
}

# Make Cloud Run service publicly accessible
resource "google_cloud_run_v2_service_iam_member" "public_access" {
  location = google_cloud_run_v2_service.app.location
  name     = google_cloud_run_v2_service.app.name
  role     = "roles/run.invoker"
  member   = "allUsers"
}

# Custom Domain Mapping for Cloud Run
# Note: This uses Cloud Run v1 API as v2 doesn't support domain mapping yet
resource "google_cloud_run_domain_mapping" "domain" {
  count    = var.custom_domain != "" ? 1 : 0
  location = var.region
  name     = var.custom_domain

  metadata {
    namespace = var.project_id
    annotations = {
      "run.googleapis.com/launch-stage" = "BETA"
    }
  }

  spec {
    route_name = google_cloud_run_v2_service.app.name
  }

  depends_on = [
    google_cloud_run_v2_service.app,
    google_project_service.required_apis
  ]
}
