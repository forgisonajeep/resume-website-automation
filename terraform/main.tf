# S3 bucket for hosting the resume site (static website)
resource "aws_s3_bucket" "resume_bucket" {
  bucket = var.bucket_name
  tags = {
    Name        = "ResumeSiteBucket"
    Environment = "Dev"
  }
}

# Enable static website hosting (index.html)
resource "aws_s3_bucket_website_configuration" "resume_site" {
  bucket = aws_s3_bucket.resume_bucket.id

  index_document {
    suffix = "index.html"
  }

  error_document {
    key = "index.html"
  }
}

# Disable S3 Block Public Access so website files can be served publicly
resource "aws_s3_bucket_public_access_block" "resume_public" {
  bucket                  = aws_s3_bucket.resume_bucket.id
  block_public_acls       = false
  block_public_policy     = false
  ignore_public_acls      = false
  restrict_public_buckets = false
}

# Public read policy for all objects in the bucket (GET only)
resource "aws_s3_bucket_policy" "public_access" {
  bucket     = aws_s3_bucket.resume_bucket.id
  depends_on = [aws_s3_bucket_public_access_block.resume_public]

  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Sid       = "PublicReadGetObject",
        Effect    = "Allow",
        Principal = "*",
        Action    = "s3:GetObject",
        Resource  = "${aws_s3_bucket.resume_bucket.arn}/*"
      }
    ]
  })
}

# DynamoDB: track deployments
resource "aws_dynamodb_table" "deployment_tracking" {
  name         = "DeploymentTrackingTable"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "deployment_id"

  attribute {
    name = "deployment_id"
    type = "S"
  }

  tags = {
    Purpose = "Track resume deployments"
  }
}

# DynamoDB: store resume analytics
resource "aws_dynamodb_table" "resume_analytics" {
  name         = "ResumeAnalyticsTable"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "visitor_id"

  attribute {
    name = "visitor_id"
    type = "S"
  }

  tags = {
    Purpose = "Track resume visits"
  }
}
