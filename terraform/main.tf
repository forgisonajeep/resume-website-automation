resource "aws_s3_bucket" "resume_bucket" {
  bucket = var.bucket_name

  tags = {
    Project = "resume-website-automation"
    Owner   = "cameron"
  }
}

resource "aws_dynamodb_table" "deployment_tracking" {
  name         = "DeploymentTrackingTable"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "deployment_id"

  attribute {
    name = "deployment_id"
    type = "S"
  }

  tags = {
    Project = "resume-website-automation"
    Table   = "deployment-tracking"
  }
}

resource "aws_dynamodb_table" "resume_analytics" {
  name         = "ResumeAnalyticsTable"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "id"

  attribute {
    name = "id"
    type = "S"
  }

  tags = {
    Project = "resume-website-automation"
    Table   = "resume-analytics"
  }
}
