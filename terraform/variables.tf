variable "region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "bucket_name" {
  description = "S3 bucket for resume website"
  type        = string
  default     = "cameron-resume-site-11062025"
}
