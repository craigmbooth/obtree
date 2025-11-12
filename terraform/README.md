# OBTree GCP Deployment with Terraform

This directory contains Terraform configuration for deploying the OBTree application to Google Cloud Platform (GCP) using Cloud Run and Cloud SQL PostgreSQL.

## Cost-Optimized Architecture

This deployment is optimized for low-traffic, cost-effective operation with **private networking**:

- **Cloud Run**: Scales to zero when idle (0 min instances)
- **Cloud SQL**: db-f1-micro instance (shared CPU, 614MB RAM) with **private IP only**
- **Storage**: Standard HDD (PD_HDD) - 10GB minimum
- **Networking**: VPC with Serverless VPC Access Connector (f1-micro instances)
- **Security**: No public IP on database, VPC-isolated traffic
- **High Availability**: Single-zone deployment
- **Backups**: Automated daily backups with 7-day retention

### Estimated Monthly Cost

- Cloud SQL db-f1-micro: ~$7/month
- Cloud SQL storage (10GB HDD): ~$2/month
- Cloud SQL backups: ~$1/month
- Cloud Run (minimal traffic): ~$0-5/month
- **VPC Access Connector (2-3 f1-micro instances)**: ~$10/month
- Artifact Registry: ~$0.10/month
- **Total: ~$20-25/month**

**Note**: The VPC connector adds ~$10/month but provides private IP connectivity, eliminating the need for a public IP on your database.

### Networking Architecture

The deployment uses private networking for enhanced security:

```
Internet → Cloud Run (public) → VPC Connector → VPC Network → Cloud SQL (private IP only)
```

- **Cloud Run**: Publicly accessible via HTTPS
- **VPC Connector**: Bridges Cloud Run to private VPC network
- **Cloud SQL**: Private IP only, accessible only from VPC network
- **Security**: Database not exposed to public internet

## Prerequisites

1. **Google Cloud Account**: Active GCP project with billing enabled
2. **gcloud CLI**: [Install gcloud](https://cloud.google.com/sdk/docs/install)
3. **Terraform**: [Install Terraform](https://www.terraform.io/downloads) (>= 1.0)
4. **Docker**: [Install Docker](https://docs.docker.com/get-docker/)
5. **Authentication**: Log in to GCP

```bash
gcloud auth login
gcloud auth application-default login
```

## Initial Setup

### 1. Configure GCP Project

```bash
# Set your project ID
export PROJECT_ID="your-gcp-project-id"
gcloud config set project $PROJECT_ID

# Enable billing (if not already enabled)
# Visit: https://console.cloud.google.com/billing
```

### 2. Create Terraform Variables

```bash
cd terraform
cp terraform.tfvars.example terraform.tfvars
```

Edit `terraform.tfvars` and set your project ID:

```hcl
project_id = "your-gcp-project-id"
region     = "us-central1"
```

### 3. Initial Deployment (Hello World)

No need to build your application image yet! Terraform will deploy with a hello-world container initially:

```bash
# The default container_image uses Google's hello-world image
# This allows you to set up infrastructure first, then deploy your app later
```

## Deployment

### Initialize Terraform

```bash
cd terraform
terraform init
```

### Preview Changes

```bash
terraform plan
```

### Deploy Infrastructure

```bash
terraform apply
```

Review the planned changes and type `yes` to confirm.

**Note**: The first deployment takes approximately 10-15 minutes as Cloud SQL instance provisioning can be slow.

### Get Deployment Information

After successful deployment:

```bash
terraform output
```

You'll see:
- `cloud_run_url`: Your application URL (currently running hello-world)
- `cloud_sql_connection_name`: Database connection identifier
- `artifact_registry_repository`: Docker image repository URL

## Deploy Your Application

After the infrastructure is set up, deploy your actual application:

### 1. Build and Push Your Application Image

```bash
# Go back to project root (if in terraform/)
cd ..

# Set variables (use values from terraform output)
export PROJECT_ID="your-gcp-project-id"
export REGION="us-central1"
export SERVICE_NAME="obtree"
export IMAGE_URL="${REGION}-docker.pkg.dev/${PROJECT_ID}/${SERVICE_NAME}/${SERVICE_NAME}:latest"

# Build and push using Cloud Build (recommended)
gcloud builds submit --tag ${IMAGE_URL}

# Alternative: Build locally and push
# docker build -t ${IMAGE_URL} .
# gcloud auth configure-docker ${REGION}-docker.pkg.dev
# docker push ${IMAGE_URL}
```

### 2. Update Cloud Run Service with Your Image

```bash
# Deploy the new image to Cloud Run
gcloud run deploy ${SERVICE_NAME} \
  --image=${IMAGE_URL} \
  --region=${REGION}

# Terraform will NOT revert this change on future applies
# The lifecycle block ignores image updates
```

### 3. Verify Deployment

```bash
# Get the Cloud Run URL
export APP_URL=$(cd terraform && terraform output -raw cloud_run_url)
echo "Application URL: $APP_URL"

# Test your application
curl $APP_URL/health
```

**Note**: Terraform is configured to ignore changes to the container image after initial deployment. This means you can update your application using `gcloud run deploy` or CI/CD pipelines, and Terraform won't try to revert it back to the hello-world image.

## Post-Deployment

### Access Your Application

```bash
# Get the Cloud Run URL
export APP_URL=$(terraform output -raw cloud_run_url)
echo "Application URL: $APP_URL"

# Test the health endpoint
curl $APP_URL/health
```

### View Logs

```bash
# Cloud Run logs
gcloud run services logs read obtree --region=us-central1

# Cloud SQL logs
gcloud sql operations list --instance=obtree-db-prod
```

### Connect to Database (Optional)

```bash
# Install Cloud SQL Proxy
gcloud components install cloud-sql-proxy

# Get connection name
export INSTANCE_CONNECTION_NAME=$(terraform output -raw cloud_sql_connection_name)

# Start proxy
cloud-sql-proxy $INSTANCE_CONNECTION_NAME

# In another terminal, connect using psql
psql "host=127.0.0.1 port=5432 dbname=obtree user=obtree_user"
# Password is stored in Secret Manager
```

## Running Database Migrations

Migrations run automatically on Cloud Run startup via the Dockerfile CMD. If you need to run them manually:

```bash
# Build a local container with Cloud SQL Proxy
gcloud run jobs create migrate-db \
  --image=$CONTAINER_IMAGE \
  --region=$REGION \
  --set-cloudsql-instances=$INSTANCE_CONNECTION_NAME \
  --set-env-vars="DATABASE_URL=postgresql://..." \
  --command="alembic" \
  --args="upgrade,head"

# Execute migration job
gcloud run jobs execute migrate-db --region=$REGION
```

## Updating the Application

When you need to deploy a new version of your application:

### 1. Build New Image

```bash
# Build and push new version with 'latest' tag
gcloud builds submit --tag ${IMAGE_URL}

# Or use a specific version tag for better tracking
gcloud builds submit --tag ${REGION}-docker.pkg.dev/${PROJECT_ID}/${SERVICE_NAME}/${SERVICE_NAME}:v1.2.0
```

### 2. Deploy to Cloud Run

```bash
# Deploy the new image
gcloud run deploy ${SERVICE_NAME} \
  --image=${IMAGE_URL} \
  --region=${REGION}

# Or with a specific version tag
gcloud run deploy ${SERVICE_NAME} \
  --image=${REGION}-docker.pkg.dev/${PROJECT_ID}/${SERVICE_NAME}/${SERVICE_NAME}:v1.2.0 \
  --region=${REGION}
```

Cloud Run will perform a rolling update with zero downtime.

**No Terraform changes needed!** The lifecycle configuration ensures Terraform won't interfere with your image updates.

## Scaling

### Increase Max Instances

Edit `terraform.tfvars`:

```hcl
max_instances = 5
```

Then apply:

```bash
terraform apply
```

### Upgrade Database Instance

For better performance, upgrade the Cloud SQL tier in `main.tf`:

```hcl
settings {
  tier = "db-g1-small"  # 1.7GB RAM, ~$25/month
  # or
  tier = "db-custom-1-3840"  # 1 vCPU, 3.75GB RAM, custom pricing
}
```

## Cost Optimization Tips

1. **Scale to Zero**: Default config scales to 0 instances when idle (no charges)
2. **CPU Throttling**: `cpu_idle = true` reduces CPU usage when idle
3. **Minimal Resources**: 512Mi memory, 1 CPU is sufficient for low traffic
4. **HDD Storage**: Uses PD_HDD instead of SSD (cheaper)
5. **Single-Zone**: No multi-zone replication (reduces cost by ~50%)
6. **Backup Retention**: 7 days only (vs 30 days default)
7. **VPC Connector**: Uses f1-micro instances (smallest available) with min 2 instances
8. **Private IP Only**: No public IP on Cloud SQL (more secure, but requires VPC connector)
9. **Egress Optimization**: VPC connector set to `PRIVATE_RANGES_ONLY` to minimize costs

## Monitoring

### View Metrics

```bash
# Cloud Run metrics
gcloud run services describe obtree --region=us-central1

# Cloud SQL metrics
gcloud sql instances describe obtree-db-prod
```

### Set Up Alerts (Optional)

```bash
# Create alert for high error rate
gcloud alpha monitoring policies create \
  --notification-channels=CHANNEL_ID \
  --display-name="High Error Rate" \
  --condition-display-name="Error rate > 10%" \
  --condition-threshold-value=0.1
```

## Troubleshooting

### Cloud Run Service Won't Start

```bash
# Check logs
gcloud run services logs read obtree --region=us-central1 --limit=50

# Common issues:
# 1. Database connection failed - check Cloud SQL instance status
# 2. Secret access denied - verify IAM permissions
# 3. Container crash - check application logs
```

### Database Connection Issues

```bash
# Verify Cloud SQL instance is running
gcloud sql instances list

# Check service account has cloudsql.client role
gcloud projects get-iam-policy $PROJECT_ID \
  --flatten="bindings[].members" \
  --filter="bindings.members:serviceAccount:obtree-sa@*"
```

### Migration Failures

If migrations fail on startup:

1. Check database schema: Connect via Cloud SQL Proxy
2. Run migrations manually using Cloud Run job (see above)
3. Check Alembic version table: `SELECT * FROM alembic_version;`

## Cleanup

To destroy all resources:

```bash
# WARNING: This will delete your database and all data!
terraform destroy
```

To preserve the database:

```bash
# Remove deletion protection first in main.tf
# Set: deletion_protection = false
terraform apply

# Then destroy
terraform destroy
```

## Security Considerations

1. **Secrets**: Database passwords and JWT keys stored in Secret Manager
2. **IAM**: Service account with minimal required permissions
3. **Network**: Cloud SQL not exposed to public internet
4. **SSL**: Cloud Run provides automatic HTTPS
5. **CORS**: Update CORS settings in `app/main.py` for production

## Support

For issues related to:
- Terraform: Check [Terraform GCP Provider Docs](https://registry.terraform.io/providers/hashicorp/google/latest/docs)
- Cloud Run: Visit [Cloud Run Documentation](https://cloud.google.com/run/docs)
- Cloud SQL: Visit [Cloud SQL Documentation](https://cloud.google.com/sql/docs)

## License

Same as parent project.
