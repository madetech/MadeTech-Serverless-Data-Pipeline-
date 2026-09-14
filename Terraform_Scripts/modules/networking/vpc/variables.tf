variable "project_name" {
  type = string
}

variable "subnet_group_name" {
  type = string
}

variable "subnet_a_name" {
  type = string
}

variable "subnet_b_name" {
  type = string
}

variable "availability_zone_a" {
  type = string
}

variable "availability_zone_b" {
  type = string
}

variable "security_group_name" {
  type = string
}

# defining cidr blocks 
variable "vpc_cidr" {
  type    = string
  default = "10.0.0.0/16"
}
variable "subnet_a_cidr" {
  type    = string
  default = "10.0.1.0/24"
}

variable "subnet_b_cidr" {
  type    = string
  default = "10.0.2.0/24"
}

