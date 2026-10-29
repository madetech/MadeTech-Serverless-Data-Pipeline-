variable "environment_name" {
  type    = string
  default = "dev"
}

variable "log_level" {
  type    = string
  default = "info"
}

variable "s3_staging_bucket_name" {
  type = string 
  default = "mt-serverless-data-pipeline-bucket"
}

variable "project_name" {
  type    = string
  default = "data_pipeline"
}

variable "rds_password" {
  type      = string
  sensitive = true
}