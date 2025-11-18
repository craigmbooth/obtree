# OBTree Deployment Guide

Quick reference for deploying OBTree to production with automatic admin user creation.

## Quick Start (Production Deployment)

### 1. Configure Terraform

```bash
cd terraform
cp terraform.tfvars.example terraform.tfvars
```

Edit `terraform.tfvars`:

```hcl
# Required
project_id = "your-gcp-project-id"
region     = "us-central1"

# Admin Bootstrap (creates first admin automatically)
initial_admin_email    = "admin@yourdomain.com"
initial_admin_password = "YourSecurePassword123!"

# Custom Domain (optional)
custom_domain = "app.redbudsapp.com"  # Or leave empty to skip
```

### 2. Deploy Infrastructure

```bash
terraform init
terraform apply  # Type 'yes' when prompted
```

⏱️ Takes ~10-15 minutes (Cloud SQL provisioning is slow)

### 3. Deploy Application

```bash
cd ..  # Back to project root
./deploy.sh
```

This will:
- Build Docker image
- Push to Artifact Registry
- Deploy to Cloud Run
- Run database migrations
- **Automatically create admin user** (bootstrap)

### 4. Setup Custom Domain (Optional)

If you configured a custom domain:

```bash
cd terraform

# Get DNS records to add to your domain registrar
terraform output dns_records_instructions
```

Add the displayed DNS records to your domain registrar (e.g., GoDaddy, Namecheap).

**Example**: For `app.redbudsapp.com`, add:
- Type: CNAME
- Name: app
- Value: ghs.googlehosted.com

DNS propagation takes 5-30 minutes. See [Custom Domain Setup Guide](docs/CUSTOM_DOMAIN_SETUP.md) for detailed instructions.

### 5. Access Your Application

```bash
# Get the URL
cd terraform
terraform output cloud_run_url

# Or if using custom domain
terraform output custom_domain
```

Visit:
- Custom domain: https://app.redbudsapp.com (if configured)
- Or Cloud Run URL: https://obtree-XXXXXXXX-uc.a.run.app

Login with your admin credentials from step 1.

### 6. Disable Bootstrap (After First Login)

Once you've logged in and created additional admin users:

Edit `terraform/terraform.tfvars`:

```hcl
# Disable by setting to empty strings
initial_admin_email    = ""
initial_admin_password = ""
```

Re-apply:

```bash
cd terraform
terraform apply
```

✅ This removes admin credentials from infrastructure.

---

## Local Development

### Using Docker Compose

```bash
# Start with admin bootstrap
ADMIN_EMAIL=admin@test.com ADMIN_PASSWORD=test123 docker-compose up

# Or without bootstrap
docker-compose up
```

Then create admin manually:

```bash
make create-admin
```

### Using SQLite (Local)

```bash
# Install dependencies
make install

# Create database
make db-create

# Create admin user
make create-admin

# Run server
make run
```

Access at http://localhost:8000

---

## Architecture

### Production Stack
- **Hosting**: Google Cloud Run (serverless)
- **Database**: Cloud SQL PostgreSQL (private IP)
- **Networking**: VPC with private connectivity
- **Secrets**: Google Secret Manager
- **Images**: Artifact Registry

### Admin Bootstrap Flow
```
Terraform → Secret Manager → Cloud Run Env Vars → Container Startup → Bootstrap Script → Admin Created
```

---

## Cost Estimate

**~$20-25/month** for production deployment:
- Cloud SQL (db-f1-micro): ~$7/month
- Storage (10GB HDD): ~$2/month
- Backups: ~$1/month
- VPC Connector: ~$10/month
- Cloud Run: ~$0-5/month (scales to zero)

---

## Monitoring

### View Logs

```bash
# Application logs
gcloud run services logs tail obtree --project=YOUR_PROJECT_ID --region=us-central1

# Bootstrap events
gcloud logging read "resource.type=cloud_run_revision AND jsonPayload.event=bootstrap_started" \
  --project=YOUR_PROJECT_ID --limit=10
```

### Check Status

```bash
cd terraform

# Is bootstrap enabled?
terraform output bootstrap_enabled

# What secrets exist?
terraform output admin_email_secret
terraform output admin_password_secret
```

---

## Troubleshooting

### "No admin user exists"

If bootstrap didn't run:

1. Check logs: `gcloud run services logs tail obtree`
2. Verify env vars are set in Cloud Run console
3. Check Secret Manager has the secrets
4. Manually create admin via Cloud Run job (see docs/PRODUCTION_ADMIN_SETUP.md)

### "User already exists"

✅ Normal - bootstrap is idempotent. Admin already created.

### "Database connection failed"

- Ensure Cloud SQL instance is running
- Check VPC connector is healthy
- Verify service account has `cloudsql.client` role

---

## Next Steps After Deployment

1. ✅ Login with admin credentials
2. ✅ Create your organization
3. ✅ Invite team members
4. ✅ Create additional admin users
5. ✅ Disable bootstrap (update terraform.tfvars)
6. ✅ Set up custom domain (optional)
7. ✅ Configure backups monitoring (optional)

---

## Documentation

- **[Terraform README](terraform/README.md)** - Full infrastructure documentation
- **[Admin Setup Guide](docs/ADMIN_SETUP_QUICK_REFERENCE.md)** - Admin user management
- **[Production Admin Setup](docs/PRODUCTION_ADMIN_SETUP.md)** - Detailed production guide
- **[CLAUDE.md](CLAUDE.md)** - Development patterns and architecture

---

## Support

**Common Commands:**

```bash
# Update application
./deploy.sh

# View logs
gcloud run services logs tail obtree --region=us-central1

# Create admin manually
make create-admin

# Check deployment status
cd terraform && terraform output
```

**Get Help:**
- Check the docs above
- Review logs for errors
- See QUICKSTART.md for development workflow
