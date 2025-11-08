output "bucket_name" {
  description = "S3 bucket for resume site"
  value       = aws_s3_bucket.resume_bucket.bucket
}

output "bucket_website_endpoint" {
  description = "Public website endpoint"
  value       = aws_s3_bucket_website_configuration.resume_site.website_endpoint
}

output "deployment_tracking_table" {
  description = "DynamoDB table for deployments"
  value       = aws_dynamodb_table.deployment_tracking.name
}

output "resume_analytics_table" {
  description = "DynamoDB table for analytics"
  value       = aws_dynamodb_table.resume_analytics.name
}
