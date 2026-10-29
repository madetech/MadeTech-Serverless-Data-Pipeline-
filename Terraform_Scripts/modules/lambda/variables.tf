variable "project_name" {
  type = string
}

variable "environment_name" {
  type = string
}

variable "extraction_role_arn" {
  type = string
}

variable "transformation_role_arn" {
  type = string
}

variable "s3_bucket_name" {
  type = string
}

variable "vpc_id" {
  type = string
}

variable "subnet_ids" {
  type = list(string)
}

variable "security_group_id" {
  type = string
}

variable "db_endpoint" {
  type = string
}

variable "db_name" {
  type = string
}

variable "db_user" {
  type = string
}

variable "db_password" {
  type      = string
  sensitive = true
}

variable "lambda_layer_zip_path" {
  type        = string
  description = "Path to a Lambda layer ZIP containing Python dependencies."
  default     = null
}
