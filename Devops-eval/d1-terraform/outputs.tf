output "api_url" {
  description = "HTTP API invoke URL"
  value       = aws_apigatewayv2_api.main.api_endpoint
}

output "bucket_name" {
  description = "S3 bucket name"
  value       = aws_s3_bucket.main.bucket
}

output "lambda_arn" {
  description = "Lambda function ARN"
  value       = aws_lambda_function.handler.arn
}
