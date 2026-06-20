# D1 — Terraform Plan (S3 + Lambda + API Gateway)

## Prerequisites

- Terraform >= 1.6
- No real AWS credentials required (mock provider config for offline validate/plan)

## Commands

```bash
# Initialize (local backend, no remote state)
terraform init -backend=false

# Validate configuration
terraform validate

# Plan (offline refresh skipped)
terraform plan -var="environment=dev" -refresh=false -out=tfplan.binary
terraform show -no-color tfplan.binary > plan-output.txt

# Apply (requires real AWS credentials)
terraform apply -var="environment=dev"

# Destroy
terraform destroy -var="environment=dev"
```

## Resources

- S3 bucket with versioning and public access blocked
- Lambda function (Python 3.12) + IAM execution role
- API Gateway HTTP API with `GET /hello` route
