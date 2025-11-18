output "cloud_run_url" {
  description = "URL of the deployed Cloud Run service"
  value       = google_cloud_run_v2_service.app.uri
}

output "cloud_sql_instance_name" {
  description = "Cloud SQL instance name"
  value       = google_sql_database_instance.postgres.name
}

output "cloud_sql_connection_name" {
  description = "Cloud SQL connection name for Cloud SQL Proxy"
  value       = google_sql_database_instance.postgres.connection_name
}

output "database_name" {
  description = "PostgreSQL database name"
  value       = google_sql_database.database.name
}

output "database_user" {
  description = "PostgreSQL database user"
  value       = google_sql_user.user.name
}

output "artifact_registry_repository" {
  description = "Artifact Registry repository URL"
  value       = "${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.repo.repository_id}"
}

output "service_account_email" {
  description = "Service account email used by Cloud Run"
  value       = google_service_account.cloudrun_sa.email
}

output "db_password_secret" {
  description = "Secret Manager secret ID for database password"
  value       = google_secret_manager_secret.db_password.secret_id
}

output "secret_key_secret" {
  description = "Secret Manager secret ID for JWT secret key"
  value       = google_secret_manager_secret.secret_key.secret_id
}

output "vpc_network_name" {
  description = "VPC network name"
  value       = google_compute_network.vpc.name
}

output "vpc_connector_name" {
  description = "VPC Access Connector name"
  value       = google_vpc_access_connector.connector.name
}

output "admin_email_secret" {
  description = "Secret Manager secret ID for admin email (if created)"
  value       = var.initial_admin_email != "" ? google_secret_manager_secret.admin_email[0].secret_id : "not-created"
}

output "admin_password_secret" {
  description = "Secret Manager secret ID for admin password (if created)"
  value       = var.initial_admin_password != "" ? google_secret_manager_secret.admin_password[0].secret_id : "not-created"
  sensitive   = true  # Marked sensitive because the resource uses sensitive input variable
}

output "bootstrap_enabled" {
  description = "Whether admin bootstrap is enabled"
  value       = var.initial_admin_email != "" && var.initial_admin_password != "" ? true : false
  sensitive   = true  # Marked sensitive because it references sensitive variable
}

output "custom_domain" {
  description = "Custom domain configured for the application"
  value       = var.custom_domain != "" ? var.custom_domain : "not-configured"
}

output "domain_mapping_status" {
  description = "Status of the domain mapping"
  value       = var.custom_domain != "" ? google_cloud_run_domain_mapping.domain[0].status[0].conditions : []
}

output "dns_records_instructions" {
  description = "DNS records to add to your domain registrar"
  value = var.custom_domain != "" ? {
    message = "Add the following DNS records to your domain registrar (${var.custom_domain}):"
    records = [
      for record in google_cloud_run_domain_mapping.domain[0].status[0].resource_records : {
        type  = record.type
        name  = record.name
        value = record.rrdata
      }
    ]
  } : {
    message = "No custom domain configured"
    records = []
  }
}
