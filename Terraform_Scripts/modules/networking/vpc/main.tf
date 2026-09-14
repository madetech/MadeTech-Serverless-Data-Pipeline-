resource "aws_vpc" "main" {
  cidr_block       = "10.0.0.0/16"
  instance_tenancy = "default"

  tags = {
    Name = "${var.project_name}-vpc"
  }
}

# Create Subnet 1 (Zone A)
resource "aws_subnet" "subnet_a" {
  vpc_id            = aws_vpc.main.id
  cidr_block        = var.subnet_a_cidr       # "10.0.1.0/24"
  availability_zone = var.availability_zone_a # "eu-west-2a"

  tags = {
    Name = var.subnet_a_name #"rds-subnet-1a"
  }
}

# Create Subnet 2 (Zone B - Required for RDS)
resource "aws_subnet" "subnet_b" {
  vpc_id            = aws_vpc.main.id
  cidr_block        = var.subnet_b_cidr       # "10.0.2.0/24"
  availability_zone = var.availability_zone_b # "eu-west-2b"

  tags = {
    Name = var.subnet_b_name # "rds-subnet-1b"
  }
}

# Group the subnets together for RDS
resource "aws_db_subnet_group" "main" {
  name       = "main-rds-subnet-group"
  subnet_ids = [aws_subnet.subnet_a.id, aws_subnet.subnet_b.id]

  tags = {
    Name = var.subnet_group_name # "My DB Subnet Group"
  }
}

# Create the Security Group for the Database
resource "aws_security_group" "main" {
  name        = "rds_security_group"
  description = "Security group for RDS Postgres Instance"
  vpc_id      = aws_vpc.main.id
  ingress {
    from_port   = 5432
    to_port     = 5432
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
  tags = {
    name = var.security_group_name #"rds-security-group"
  }
}