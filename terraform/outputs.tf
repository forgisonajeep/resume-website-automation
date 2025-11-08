output "bucket_name" {
  description = "S3 bucket name (raw name)"
  value       = aws_s3_bucket.resume_bucket.bucket
}

output "deployment_tracking_table" {
  description = "DynamoDB DeploymentTracking table"
  value       = aws_dynamodb_table.deployment_tracking.name
}

output "resume_analytics_table" {
  description = "DynamoDB ResumeAnalytics table"
  value       = aws_dynamodb_table.resume_analytics.name
}
