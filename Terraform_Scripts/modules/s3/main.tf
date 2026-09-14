#S3 Bucket Creation
resource "aws_s3_bucket" "main" {
  bucket = "mt-serverless-data-pipeline-bucket-dev"
  # mt-serverless-data-pipeline-bucket-dev
  tags = {
    Name        = var.project_name
    Environment = var.environment_name
  }
}

resource "aws_s3_bucket_versioning" "main" {
  bucket = aws_s3_bucket.main.id
  versioning_configuration {
    status = var.versioning_enabled ? "Enabled" : "Disabled"
  }
}

resource "aws_s3_bucket_notification" "eventbridge" {
  bucket      = aws_s3_bucket.main.id
  eventbridge = true
}