provider "aws" {
  region = "eu-west-2"
}

module "vpc" {
  source = "./modules/networking/vpc"

  project_name        = var.application_name
  availability_zone_a = "eu-west-2a"
  availability_zone_b = "eu-west-2b"
  subnet_group_name   = "rds-db-subnet-group"
  subnet_a_name       = "rds-subnet-1a"
  subnet_b_name       = "rds-subnet-1b"
  security_group_name = "rds-security-group"

}

# S3 Bucket Creation
module "s3" {
  source             = "./modules/s3"
  bucket_name        = "mt-serverless-data-pipeline-bucket-dev"
  versioning_enabled = false
  environment_name   = var.environment_name
  project_name       = "data-pipeline"

}

module "rds" {
  source                 = "./modules/rds"
  rds_identifier         = "dbapiextraction"
  allocated_storage      = 10
  db_name                = "target_db"
  engine                 = "postgres"
  engine_version         = "18.2"
  instance_class         = "db.t3.micro"
  rds_user               = "db_user"
  rds_password           = var.rds_password
  db_subnet_group_name   = module.vpc.db_subnet_group_name
  vpc_security_group_ids = [module.vpc.security_group_id]
  skip_final_snapshot    = true
  publicly_accessible    = false
  project_name           = var.application_name
}

module "iam" {
  source = "./modules/iam"

  project_name  = var.application_name
  s3_bucket_arn = module.s3.bucket_arn
  rds_arn       = module.rds.db_arn
}

module "lambda" {
  source = "./modules/lambda"

  project_name            = var.application_name
  environment_name        = var.environment_name
  extraction_role_arn     = module.iam.extraction_lambda_role_arn
  transformation_role_arn = module.iam.transformation_lambda_role_arn
  s3_bucket_name          = module.s3.bucket_id
  vpc_id                  = module.vpc.vpc_id
  subnet_ids              = module.vpc.subnet_ids
  security_group_id       = module.vpc.security_group_id
  db_endpoint             = module.rds.db_endpoint
  db_name                 = "target_db"
  db_user                 = "db_user"
  db_password             = var.rds_password
  lambda_layer_zip_path   = "${path.root}/python.zip"
}

module "eventbridge" {
  source = "./modules/eventbridge"

  project_name                 = var.application_name
  s3_bucket_name               = module.s3.bucket_id
  transformation_function_arn  = module.lambda.transformation_function_arn
  transformation_function_name = module.lambda.transformation_function_name
}

