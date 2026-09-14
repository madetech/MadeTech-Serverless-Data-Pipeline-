variable "environment_name" {
  type    = string
  default = "dev"
}

variable "log_level" {
  type    = string
  default = "info"
}

variable "application_name" {
  type    = string
  default = "data_pipeline"
}

variable "rds_password" {
  type      = string
  sensitive = true
}