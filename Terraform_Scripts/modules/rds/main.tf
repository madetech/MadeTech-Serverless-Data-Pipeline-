resource "aws_db_instance" "main" {
  identifier             = var.rds_identifier    #"dbapiextraction"  
  allocated_storage      = var.allocated_storage #
  db_name                = var.db_name           # "target_db"
  engine                 = var.engine            # "postgres"
  engine_version         = var.engine_version    # "18.2"
  instance_class         = var.instance_class    # "db.t3.micro"
  username               = var.rds_user          # db_user
  password               = var.rds_password
  db_subnet_group_name   = var.db_subnet_group_name
  vpc_security_group_ids = var.vpc_security_group_ids
  skip_final_snapshot    = var.skip_final_snapshot # True
  publicly_accessible    = var.publicly_accessible # False

  tags = {
    Name = var.project_name
  }
}