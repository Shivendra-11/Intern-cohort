# D1 — Terraform Plan (60m)

## Goal
Write Terraform for: S3 bucket + Lambda (Python 3.12) + API Gateway (HTTP API).
Must pass `terraform validate` and produce a clean `terraform plan`.

## Provider choice
AWS provider ≥ 5.0 with local backend (no real credentials needed for validate/plan).

## Resource list
- aws_s3_bucket (versioning enabled, no public access)
- aws_s3_bucket_versioning
- aws_iam_role + aws_iam_role_policy_attachment (Lambda execution role)
- aws_lambda_function (runtime python3.12, handler index.handler)
- aws_apigatewayv2_api (HTTP API)
- aws_apigatewayv2_integration
- aws_apigatewayv2_route (GET /hello)

## Verification commands
```bash
terraform init -backend=false
terraform validate
terraform plan -var="environment=dev" -out=tfplan.binary
terraform show -no-color tfplan.binary > plan-output.txt
```

## DoD
- validate exits 0
- plan exits 0
- plan shows ≥ 5 resources to add
- README has apply/destroy commands
- REPORT.json written with correct schema
- PROOF.md contains full terminal output
