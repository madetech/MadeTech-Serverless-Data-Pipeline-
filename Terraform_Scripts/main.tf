provider "aws" {
  region = "eu-west-2"
}

module "vpc" {
  source = "./modules/networking/vpc"

  project_name        = var.project_name
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
  bucket_name        = "${var.s3_staging_bucket_name}-${var.environment_name}"
  versioning_enabled = false
  environment_name   = var.environment_name
  project_name       = var.project_name

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
  project_name           = var.project_name
}

module "iam" {
  source = "./modules/iam"

  project_name  = var.project_name
  s3_bucket_arn = module.s3.bucket_arn
  rds_arn       = module.rds.db_arn
  
  
}

module "lambda" {
  source = "./modules/lambda"

  project_name            = var.project_name
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
  # lambda_layer_zip_path   = "${path.root}/python.zip"
}

module "step_function_state_machine"{
  source = "./modules/step_function/state_machine"

  state_machine_name = "data_pipeline_dev_state_machine"
  role_arn = module.iam.state_machine_access_policy_arn
  depends_on = [module.lambda.transformation_function_arn, module.lambda.extraction_lambda_role_arn]

  
}

# Adding IAM permissions for Step Function State Machine to root main.tf
data "aws_iam_policy_document" "state_machine_permissions_policy" {
  statement {
    effect  = "Allow"
    actions = ["lambda:InvokeFunction"]
    resources = [
      module.lambda.extraction_function_arn,
      "${module.lambda.extraction_function_arn}:*",
      module.lambda.transformation_function_arn,
      "${module.lambda.transformation_function_arn}:*"
    ]
  }
}

resource "aws_iam_role_policy" "state_machine_permissions" {
  role   = module.iam.state_machine_role_id   
  policy = data.aws_iam_policy_document.state_machine_permissions_policy.json
}

module "eventbridge_schduler" {
  source                  = "./modules/eventbridge"
  project_name            = var.project_name
  step_function_arn       = module.step_function_state_machine.step_function_arn
  step_function_role_arn  = module.iam.scheduler_role_arn
}
# eventbridge scheduler policy
data "aws_iam_policy_document" "scheduler_permissions_policy" {
  statement {
    effect    = "Allow"
    actions   = ["states:StartExecution"]
    resources = [module.step_function_state_machine.step_function_arn]
  }
}

resource "aws_iam_role_policy" "scheduler_permissions" {
  role   = module.iam.scheduler_role_id
  policy = data.aws_iam_policy_document.scheduler_permissions_policy.json
}