# Production Admin User Setup

This guide explains how to securely create and manage admin users in production.

## Overview

There are **three approaches** for creating admin users in production, each suited for different scenarios:

1. **Bootstrap Mode (Recommended for initial deployment)** - Automatically creates admin on first deployment
2. **Manual Container Exec** - SSH into running container and create admin manually
3. **Cloud Run Jobs** - Run one-off admin creation tasks

---

## Method 1: Bootstrap Mode (Recommended)

**Best for:** Initial deployment when you want to automatically create the first admin user.

### How it works:
- On container startup, if `ADMIN_EMAIL` and `ADMIN_PASSWORD` are set, the bootstrap script runs
- It only creates an admin if **no users exist yet** (safe to run on every deployment)
- If users already exist, it skips silently

### Setup in Terraform:

Add these environment variables to your Cloud Run service in `terraform/main.tf`:

```hcl
resource "google_cloud_run_v2_service" "obtree" {
  # ... existing configuration ...

  template {
    containers {
      # ... existing configuration ...

      env {
        name  = "ADMIN_EMAIL"
        value = var.initial_admin_email
      }

      env {
        name = "ADMIN_PASSWORD"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.admin_password.secret_id
            version = "latest"
          }
        }
      }
    }
  }
}

# Store admin password in Secret Manager
resource "google_secret_manager_secret" "admin_password" {
  secret_id = "${var.service_name}-admin-password"

  replication {
    auto {}
  }
}

resource "google_secret_manager_secret_version" "admin_password" {
  secret      = google_secret_manager_secret.admin_password.id
  secret_data = var.initial_admin_password
}

# Add variables
variable "initial_admin_email" {
  description = "Email for initial admin user (only created if no users exist)"
  type        = string
  default     = ""  # Optional - leave empty to skip bootstrap
}

variable "initial_admin_password" {
  description = "Password for initial admin user (stored in Secret Manager)"
  type        = string
  sensitive   = true
  default     = ""
}
```

### Set values in `terraform/terraform.tfvars`:

```hcl
initial_admin_email    = "admin@yourdomain.com"
initial_admin_password = "your-secure-password-here"  # Will be stored in Secret Manager
```

**Security Note:** After the first successful deployment and admin creation:
1. Log in to the application
2. Create additional admin users
3. Remove these environment variables from Terraform
4. Re-deploy without the bootstrap credentials

---

## Method 2: Manual Container Exec

**Best for:** Creating additional admins after initial deployment, or when you prefer manual control.

### Option A: Using gcloud CLI

```bash
# Get your project details
PROJECT_ID="your-gcp-project-id"
REGION="us-central1"
SERVICE_NAME="obtree"

# Get a running container instance
INSTANCE=$(gcloud run services describe $SERVICE_NAME \
  --project=$PROJECT_ID \
  --region=$REGION \
  --format='value(status.latestReadyRevisionName)')

# Execute the admin creation script interactively
gcloud run services proxy $SERVICE_NAME \
  --project=$PROJECT_ID \
  --region=$REGION

# In another terminal, SSH to the instance
gcloud compute ssh <instance-name> \
  --project=$PROJECT_ID \
  --zone=<zone>

# Inside the container
python scripts/create_admin.py
```

### Option B: Using Cloud Shell

```bash
# From Google Cloud Console, open Cloud Shell
# Deploy a temporary Cloud Run job to create admin

gcloud run jobs create create-admin \
  --project=$PROJECT_ID \
  --region=$REGION \
  --image=$IMAGE_URL \
  --set-env-vars="ADMIN_EMAIL=newadmin@example.com,ADMIN_PASSWORD=secure_password,DATABASE_URL=your-db-url" \
  --execute-now \
  --command=python,scripts/create_admin.py,--from-env

# Clean up the job after use
gcloud run jobs delete create-admin --project=$PROJECT_ID --region=$REGION
```

---

## Method 3: Cloud Run Jobs (Advanced)

**Best for:** Recurring admin tasks or automated admin provisioning.

### Create a reusable admin creation job:

```bash
# Create the job (one-time setup)
gcloud run jobs create admin-manager \
  --project=$PROJECT_ID \
  --region=$REGION \
  --image=$IMAGE_URL \
  --set-env-vars="DATABASE_URL=your-db-url" \
  --command=python,scripts/create_admin.py,--from-env

# Execute when needed (pass credentials at runtime)
gcloud run jobs execute admin-manager \
  --project=$PROJECT_ID \
  --region=$REGION \
  --update-env-vars="ADMIN_EMAIL=admin@example.com,ADMIN_PASSWORD=secure_password"
```

---

## Security Best Practices

### 1. **Use Strong Passwords**
- Minimum 12 characters
- Mix of uppercase, lowercase, numbers, symbols
- Use a password manager to generate

### 2. **Use Secret Manager for Production**
Never store passwords in plain text. Always use Google Secret Manager:

```bash
# Store password in Secret Manager
echo -n "your-secure-password" | gcloud secrets create admin-password \
  --project=$PROJECT_ID \
  --data-file=-

# Reference in Cloud Run
gcloud run services update $SERVICE_NAME \
  --project=$PROJECT_ID \
  --region=$REGION \
  --update-secrets=ADMIN_PASSWORD=admin-password:latest
```

### 3. **Rotate Bootstrap Credentials**
After initial deployment:
1. Log in and create additional admin users
2. Remove `ADMIN_EMAIL` and `ADMIN_PASSWORD` from environment
3. Re-deploy

### 4. **Audit Admin Creation**
All admin creation events are logged via structlog:
- `admin_created` - New admin created
- `admin_promoted` - Existing user promoted
- `bootstrap_started` - Bootstrap mode activated
- `bootstrap_skipped` - Bootstrap skipped (users exist)

Check logs:
```bash
gcloud logging read "resource.type=cloud_run_revision \
  AND jsonPayload.event=admin_created" \
  --project=$PROJECT_ID \
  --limit=50 \
  --format=json
```

### 5. **Principle of Least Privilege**
- Create regular users with User role by default
- Only promote to Admin when necessary
- Consider having multiple admins for redundancy

---

## Troubleshooting

### "Bootstrap skipped: X users already exist"
This is normal. Bootstrap only runs when database is empty.
- To create additional admins, use Method 2 or Method 3

### "Error: ADMIN_EMAIL and ADMIN_PASSWORD environment variables must be set"
- Check that environment variables are properly configured in Cloud Run
- For Secret Manager, ensure IAM permissions are correct

### "User already exists and is a site admin"
- The user is already an admin, no action needed
- Check application logs to verify

### Can't access the container
Cloud Run is stateless and auto-scales to zero. Options:
- Use Cloud Run Jobs (Method 3)
- Temporarily set min-instances to 1 and use Cloud Shell
- Use the bootstrap method for initial setup

---

## Testing Locally with Docker

Test the bootstrap process locally:

```bash
# Start with bootstrap enabled
ADMIN_EMAIL=admin@test.com ADMIN_PASSWORD=testpass123 docker-compose up

# Check logs
docker-compose logs app | grep bootstrap

# Should see: "✓ Site admin user created successfully!"
```

Test that bootstrap is idempotent (safe to run multiple times):

```bash
# Restart - should skip bootstrap
docker-compose restart app
docker-compose logs app | grep bootstrap

# Should see: "Bootstrap skipped: 1 user(s) already exist"
```

---

## Summary

| Method | Best For | Complexity | Security |
|--------|----------|------------|----------|
| Bootstrap | Initial deployment | Low | High (with Secret Manager) |
| Container Exec | Ad-hoc admin creation | Medium | High |
| Cloud Run Jobs | Automated workflows | High | Very High |

**Recommendation:** Use Bootstrap mode for initial deployment with credentials in Secret Manager, then remove the environment variables after creating additional admins through the web interface.
