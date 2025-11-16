terraform {
  backend "s3" {
    bucket  = "cameron-resume-site-11062025-state"
    key     = "terraform.tfstate"
    region  = "us-east-1"
    encrypt = true
  }
}
