# Custom Domain Setup for OBTree

This guide walks you through setting up a custom domain (redbudsapp.com) for your OBTree deployment on Google Cloud Run.

## Overview

There are **two approaches** for custom domains with Cloud Run:

| Approach | Example | Verification Required | SSL Certificate | Recommended |
|----------|---------|----------------------|-----------------|-------------|
| **Subdomain** | app.redbudsapp.com | ❌ No | ✅ Auto (Google-managed) | ✅ **Yes** |
| **Root Domain** | redbudsapp.com | ✅ Yes (Search Console) | ✅ Auto (Google-managed) | Maybe |

**Recommendation**: Use a **subdomain** (e.g., `app.redbudsapp.com`) for easier setup with no verification required.

---

## Method 1: Subdomain (Recommended)

### Step 1: Configure Terraform

Edit `terraform/terraform.tfvars`:

```hcl
# Use a subdomain (no verification needed)
custom_domain = "app.redbudsapp.com"
```

### Step 2: Apply Terraform

```bash
cd terraform
terraform apply
```

Type `yes` to confirm. Terraform will create the domain mapping.

### Step 3: Get DNS Records

After applying, get the DNS records to configure:

```bash
terraform output dns_records_instructions
```

You'll see output like:

```json
{
  "message": "Add the following DNS records to your domain registrar (app.redbudsapp.com):",
  "records": [
    {
      "name": "app.redbudsapp.com.",
      "type": "CNAME",
      "value": "ghs.googlehosted.com."
    }
  ]
}
```

### Step 4: Add DNS Records to Your Domain Registrar

**Where you bought your domain** (GoDaddy, Namecheap, Google Domains, etc.):

1. Login to your domain registrar
2. Navigate to DNS settings for `redbudsapp.com`
3. Add a **CNAME record**:
   - **Type**: CNAME
   - **Name/Host**: `app` (or `app.redbudsapp.com` depending on registrar)
   - **Value/Points to**: `ghs.googlehosted.com`
   - **TTL**: 3600 (or default)

**Example for common registrars:**

#### Google Domains
```
Type: CNAME
Name: app
Data: ghs.googlehosted.com
```

#### Namecheap
```
Type: CNAME Record
Host: app
Value: ghs.googlehosted.com
TTL: Automatic
```

#### GoDaddy
```
Type: CNAME
Name: app
Value: ghs.googlehosted.com
TTL: 1 Hour
```

#### Cloudflare
```
Type: CNAME
Name: app
Target: ghs.googlehosted.com
Proxy status: DNS only (gray cloud)
```

**Important for Cloudflare**: Set proxy status to "DNS only" (gray cloud icon), not "Proxied" (orange cloud).

### Step 5: Wait for DNS Propagation

DNS changes can take up to 48 hours to propagate, but usually complete within 5-30 minutes.

Check propagation:

```bash
# Check if DNS has propagated
dig app.redbudsapp.com

# Or use online tool
# https://dnschecker.org
```

### Step 6: Verify Domain Mapping

```bash
# Check status
gcloud run domain-mappings describe \
  --domain=app.redbudsapp.com \
  --region=us-central1 \
  --project=YOUR_PROJECT_ID

# Or via Terraform
terraform output domain_mapping_status
```

### Step 7: Test Your Domain

Once DNS has propagated and SSL certificate is provisioned (automatic):

```bash
curl https://app.redbudsapp.com/health
```

Or visit in your browser: https://app.redbudsapp.com

✅ **Done!** Your app is now accessible via your custom subdomain with automatic SSL.

---

## Method 2: Root Domain (redbudsapp.com)

Using the root domain requires domain ownership verification via Google Search Console.

### Step 1: Verify Domain Ownership

1. Go to [Google Search Console](https://search.google.com/search-console)
2. Add property → Domain
3. Enter `redbudsapp.com`
4. Follow verification steps (usually adding a TXT record to DNS)
5. Complete verification

### Step 2: Get Verification Code

After verification, you'll receive a verification code. This is required for Cloud Run to accept the root domain.

### Step 3: Configure Terraform

Edit `terraform/terraform.tfvars`:

```hcl
custom_domain = "redbudsapp.com"
domain_verification_code = "google-site-verification=XXXXXXXXXXXXX"  # From Search Console
```

### Step 4: Apply Terraform

```bash
cd terraform
terraform apply
```

### Step 5: Get DNS Records

```bash
terraform output dns_records_instructions
```

You'll see something like:

```json
{
  "message": "Add the following DNS records to your domain registrar (redbudsapp.com):",
  "records": [
    {
      "name": "redbudsapp.com.",
      "type": "A",
      "value": "216.239.32.21"
    },
    {
      "name": "redbudsapp.com.",
      "type": "AAAA",
      "value": "2001:4860:4802:32::15"
    }
  ]
}
```

### Step 6: Add DNS Records

Add **A** and **AAAA** records to your domain registrar:

**A Record** (IPv4):
- Type: A
- Name: @ (or leave blank for root)
- Value: `216.239.32.21` (or value from output)
- TTL: 3600

**AAAA Record** (IPv6):
- Type: AAAA
- Name: @ (or leave blank for root)
- Value: `2001:4860:4802:32::15` (or value from output)
- TTL: 3600

**Note**: The IP addresses may vary. Always use the values from `terraform output`.

### Step 7: Wait and Verify

Same as subdomain method - wait for DNS propagation and SSL provisioning.

---

## Terraform Commands Reference

```bash
# View all outputs including DNS instructions
terraform output

# View just DNS instructions
terraform output dns_records_instructions

# View domain status
terraform output domain_mapping_status

# Check what domain is configured
terraform output custom_domain

# Re-apply if needed
terraform apply
```

---

## Troubleshooting

### DNS records not showing in terraform output

**Problem**: `terraform output dns_records_instructions` shows empty or "not-configured"

**Solution**:
```bash
# 1. Ensure domain is set in terraform.tfvars
grep custom_domain terraform/terraform.tfvars

# 2. Re-apply
terraform apply

# 3. Wait a moment, then check again
terraform output dns_records_instructions
```

### Domain mapping stuck in "Pending"

**Problem**: Domain mapping shows status "Pending" or "CertificatePending"

**Possible causes**:
1. **DNS not propagated yet** - Wait 5-30 minutes, up to 48 hours
2. **Incorrect DNS records** - Verify records match terraform output exactly
3. **Root domain without verification** - Complete Google Search Console verification
4. **Cloudflare proxy enabled** - Disable proxy (use gray cloud, not orange)

**Check DNS propagation**:
```bash
# Check if CNAME exists
dig app.redbudsapp.com CNAME

# Check from multiple locations
# https://dnschecker.org
```

**Check domain mapping status**:
```bash
gcloud run domain-mappings describe \
  --domain=app.redbudsapp.com \
  --region=us-central1 \
  --format=json
```

### SSL certificate not provisioning

**Problem**: Getting SSL errors or "Not Secure" warning

**Solution**:
- SSL certificates are automatically provisioned by Google
- Can take 15 minutes to several hours after DNS propagation
- No action needed - just wait
- Certificate renews automatically

**Check certificate status**:
```bash
gcloud run domain-mappings describe \
  --domain=app.redbudsapp.com \
  --region=us-central1 \
  --format="value(status.conditions)"
```

Look for `CertificateProvisioned: True`

### "Permission denied" when creating domain mapping

**Problem**: Terraform fails with permission error

**Solution**:
```bash
# Ensure you have required roles
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
  --member="user:YOUR_EMAIL" \
  --role="roles/run.admin"
```

### Wrong DNS records shown

**Problem**: Terraform output shows unexpected IP addresses or CNAME

**Solution**:
- This is normal - Google may use different IPs for different regions/domains
- Always use the exact values from `terraform output`
- Don't copy values from this documentation

### Want to change from subdomain to root domain (or vice versa)

**Solution**:

1. Remove old mapping:
```hcl
# terraform.tfvars
custom_domain = ""  # Empty to remove
```

```bash
terraform apply
```

2. Update DNS at registrar (remove old records)

3. Add new domain:
```hcl
# terraform.tfvars
custom_domain = "redbudsapp.com"  # New domain
```

```bash
terraform apply
terraform output dns_records_instructions
```

4. Add new DNS records to registrar

---

## Domain Registrar-Specific Guides

### Google Domains

1. Go to [Google Domains](https://domains.google.com)
2. Select your domain → DNS
3. Scroll to "Custom resource records"
4. Add record as shown in terraform output
5. Click "Add"

### Namecheap

1. Login to Namecheap
2. Domain List → Manage
3. Advanced DNS tab
4. Add New Record
5. Enter details from terraform output
6. Save

### GoDaddy

1. Login to GoDaddy
2. My Products → DNS
3. Click "Add" under Records
4. Enter details from terraform output
5. Save

### Cloudflare

1. Login to Cloudflare
2. Select domain → DNS → Records
3. Add record
4. **Important**: Click cloud icon to disable proxy (must be gray, not orange)
5. Save

---

## Using Both Root and Subdomain

You can set up both `redbudsapp.com` and `app.redbudsapp.com` to point to your app:

**Option 1**: Use domain mapping for one, redirect for the other

Set up `app.redbudsapp.com` via Terraform (recommended):
```hcl
custom_domain = "app.redbudsapp.com"
```

Then at your domain registrar, set up a redirect from root to subdomain:
- `redbudsapp.com` → `app.redbudsapp.com` (301 redirect)

**Option 2**: Separate domain mappings (requires verification for root)

You can only have one domain mapped via Terraform. To add multiple domains, use gcloud:

```bash
# Primary domain via Terraform
custom_domain = "app.redbudsapp.com"

# Additional domain via gcloud
gcloud run domain-mappings create \
  --service=obtree \
  --domain=redbudsapp.com \
  --region=us-central1
```

---

## Cost

Custom domain mapping is **free**!

- ✅ Domain mapping: Free
- ✅ SSL certificate: Free (Google-managed)
- ✅ Certificate renewal: Free (automatic)
- 💰 Domain registration: Varies by registrar (~$10-15/year)

---

## Next Steps

After domain is set up:

1. ✅ Update application URLs in your code (if needed)
2. ✅ Update OAuth redirect URLs (if using OAuth)
3. ✅ Update CORS settings in `app/main.py`
4. ✅ Configure email settings to use custom domain
5. ✅ Set up monitoring/alerts for domain
6. ✅ Consider setting up www redirect

---

## Additional Resources

- [Cloud Run Custom Domains Documentation](https://cloud.google.com/run/docs/mapping-custom-domains)
- [Google Search Console](https://search.google.com/search-console)
- [DNS Checker Tool](https://dnschecker.org)
- [SSL Certificate Check](https://www.ssllabs.com/ssltest/)

---

## Summary

**Easiest approach**: Use subdomain (`app.redbudsapp.com`)

```bash
# 1. Edit terraform/terraform.tfvars
custom_domain = "app.redbudsapp.com"

# 2. Apply
terraform apply

# 3. Get DNS records
terraform output dns_records_instructions

# 4. Add CNAME to your domain registrar
# Name: app
# Value: ghs.googlehosted.com

# 5. Wait and test
curl https://app.redbudsapp.com/health
```

✅ Done in 4 steps!
