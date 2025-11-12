variable "project_id" {
  description = "GCP Project ID"
  type        = string
}

variable "region" {
  description = "GCP region for resources"
  type        = string
  default     = "us-central1"
}

variable "service_name" {
  description = "Name of the Cloud Run service and related resources"
  type        = string
  default     = "obtree"
}

variable "environment" {
  description = "Environment name (e.g., dev, staging, prod)"
  type        = string
  default     = "prod"
}

variable "app_name" {
  description = "Application display name"
  type        = string
  default     = "OBTree"
}

variable "db_name" {
  description = "PostgreSQL database name"
  type        = string
  default     = "obtree"
}

variable "db_user" {
  description = "PostgreSQL database user"
  type        = string
  default     = "obtree_user"
}

variable "max_instances" {
  description = "Maximum number of Cloud Run instances"
  type        = number
  default     = 2
}

variable "container_image" {
  description = "Container image URL. Defaults to hello-world for initial deployment. Update via gcloud after first deploy."
  type        = string
  default     = "us-docker.pkg.dev/cloudrun/container/hello"
}
