# Custom Domain Quick Reference

## Setup in 3 Steps

### 1️⃣ Configure Terraform

```bash
# Edit terraform/terraform.tfvars
custom_domain = "app.redbudsapp.com"  # Subdomain (recommended)
# OR
custom_domain = "redbudsapp.com"      # Root domain (needs verification)
```

### 2️⃣ Apply and Get DNS Records

```bash
cd terraform
terraform apply

# Get DNS records
terraform output dns_records_instructions
```

### 3️⃣ Add DNS Records to Your Registrar

**For Subdomain** (app.redbudsapp.com):
```
Type: CNAME
Name: app
Value: ghs.googlehosted.com
TTL: 3600
```

**For Root Domain** (redbudsapp.com):
```
Type: A
Name: @ (or blank)
Value: [IP from terraform output]

Type: AAAA
Name: @ (or blank)
Value: [IPv6 from terraform output]
```

---

## Common Registrars

### Google Domains
- DNS → Custom resource records → Add

### Namecheap
- Domain List → Manage → Advanced DNS → Add Record

### GoDaddy
- My Products → DNS → Add Record

### Cloudflare
- DNS → Records → Add record
- ⚠️ **Important**: Disable proxy (gray cloud, not orange)

---

## Verify Setup

```bash
# Check DNS propagation (wait 5-30 minutes)
dig app.redbudsapp.com

# Check domain mapping status
terraform output domain_mapping_status

# Test (after DNS propagates)
curl https://app.redbudsapp.com/health
```

---

## Troubleshooting

**DNS not propagating?**
- Wait up to 48 hours
- Check records match terraform output exactly
- For Cloudflare: disable proxy

**SSL not working?**
- Wait 15 minutes after DNS propagates
- Certificate provisions automatically
- No action needed

**Root domain not working?**
- Verify domain at [Google Search Console](https://search.google.com/search-console)
- Add verification TXT record

---

## Key Commands

```bash
# View all outputs
terraform output

# View just DNS instructions
terraform output dns_records_instructions

# Check domain status
terraform output domain_mapping_status

# Test domain
curl https://app.redbudsapp.com/health
```

---

## Features

✅ Free custom domain mapping
✅ Automatic SSL certificate
✅ Auto-renewal (forever)
✅ No additional GCP costs

---

📖 **Full Guide**: [Custom Domain Setup](./CUSTOM_DOMAIN_SETUP.md)
