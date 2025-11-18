# Admin Setup - Quick Reference

## Three Ways to Create Admins in Production

### 1. 🚀 Bootstrap Mode (Easiest - Recommended for first deployment)

**When to use:** Initial deployment when database is empty

**How it works:**
- Set `ADMIN_EMAIL` and `ADMIN_PASSWORD` as environment variables in Cloud Run
- On first startup, admin is created automatically
- Safe to leave enabled - only creates admin if zero users exist

**Setup:**
```bash
# Add to your Cloud Run environment variables
ADMIN_EMAIL=admin@yourdomain.com
ADMIN_PASSWORD=your-secure-password  # Store in Secret Manager!
```

**After first deployment:**
1. Login and create additional admins
2. Remove these env vars from Cloud Run
3. Re-deploy

---

### 2. 🔧 Manual Exec (Most Control)

**When to use:** Creating additional admins after initial setup

**Using local script (requires database access):**
```bash
# Interactive mode
make create-admin

# Or with environment variables
ADMIN_EMAIL=admin@example.com ADMIN_PASSWORD=secure123 make create-admin-env
```

**Using Cloud Run (requires gcloud CLI):**
```bash
# Create a one-time job
gcloud run jobs create create-admin \
  --project=YOUR_PROJECT_ID \
  --region=us-central1 \
  --image=YOUR_IMAGE_URL \
  --set-env-vars="DATABASE_URL=postgres://...,ADMIN_EMAIL=admin@example.com,ADMIN_PASSWORD=password" \
  --execute-now \
  --command=python,scripts/create_admin.py,--from-env
```

---

### 3. 🏗️ Application Feature (Future Enhancement)

**When to use:** Best user experience

**Recommended implementation:**
- Create a special `/setup` route that only works when zero users exist
- First person to visit creates their admin account
- Route automatically disables after first admin created
- Similar to WordPress/Ghost setup flow

---

## Testing Locally

**Test with Docker Compose:**
```bash
# Method 1: Bootstrap on startup
ADMIN_EMAIL=admin@test.com ADMIN_PASSWORD=test123 docker-compose up

# Method 2: Exec into running container
docker-compose exec app python scripts/create_admin.py

# Method 3: Using make command
make create-admin
```

---

## Security Checklist

- [ ] Use passwords with 12+ characters
- [ ] Store passwords in Google Secret Manager (not plain text)
- [ ] Remove bootstrap env vars after initial deployment
- [ ] Create multiple admin users for redundancy
- [ ] Enable audit logging for admin actions
- [ ] Rotate admin credentials periodically

---

## Common Commands

```bash
# Local development
make create-admin              # Interactive mode
ADMIN_EMAIL=x ADMIN_PASSWORD=y make create-admin-env

# Docker
docker-compose exec app python scripts/create_admin.py
docker-compose exec app python scripts/create_admin.py --from-env

# Production (Cloud Run)
# See full documentation in PRODUCTION_ADMIN_SETUP.md
```

---

## Troubleshooting

**"Bootstrap skipped: X users already exist"**
✓ Normal behavior - bootstrap only creates first admin

**"Error: ADMIN_EMAIL and ADMIN_PASSWORD must be set"**
✗ Check environment variables are configured

**"User already exists and is a site admin"**
✓ User is already an admin, nothing to do

---

For detailed production setup instructions, see [PRODUCTION_ADMIN_SETUP.md](./PRODUCTION_ADMIN_SETUP.md)
