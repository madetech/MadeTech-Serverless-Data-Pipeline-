data "archive_file" "handler" {
  type        = "zip"
  source_file = "${path.root}/src/lambda.py"
  output_path = "${path.root}/lambda.zip"
}

resource "aws_s3_object" "dependencies" {
  count  = var.lambda_layer_zip_path == null ? 0 : 1
  bucket = var.s3_bucket_name
  key    = "lambda-layers/python.zip"
  source = var.lambda_layer_zip_path
  etag   = filemd5(var.lambda_layer_zip_path)
}

resource "aws_lambda_layer_version" "dependencies" {
  count = var.lambda_layer_zip_path == null ? 0 : 1

  layer_name               = "${var.project_name}-python-dependencies-${var.environment_name}"
  compatible_runtimes      = ["python3.12"]
  s3_bucket                = var.s3_bucket_name
  s3_key                   = aws_s3_object.dependencies[0].key
  s3_object_version        = aws_s3_object.dependencies[0].version_id
  compatible_architectures = ["x86_64"]
}

resource "aws_lambda_function" "extraction" {
  function_name    = "${var.project_name}-api-extraction-${var.environment_name}"
  filename         = data.archive_file.handler.output_path
  source_code_hash = data.archive_file.handler.output_base64sha256
  role             = var.extraction_role_arn
  handler          = "lambda.lambda_handler"
  runtime          = "python3.12"
  layers           = var.lambda_layer_zip_path == null ? [] : [aws_lambda_layer_version.dependencies[0].arn]

  environment {
    variables = {
      S3_BUCKET = var.s3_bucket_name
    }
  }
}

resource "aws_lambda_function" "transformation" {
  function_name    = "${var.project_name}-transformation-${var.environment_name}"
  filename         = data.archive_file.handler.output_path
  source_code_hash = data.archive_file.handler.output_base64sha256
  role             = var.transformation_role_arn
  handler          = "lambda.lambda_handler"
  runtime          = "python3.12"
  layers           = var.lambda_layer_zip_path == null ? [] : [aws_lambda_layer_version.dependencies[0].arn]

  vpc_config {
    subnet_ids         = var.subnet_ids
    security_group_ids = [var.security_group_id]
  }

  environment {
    variables = {
      DB_HOST     = var.db_endpoint
      DB_NAME     = var.db_name
      DB_USER     = var.db_user
      DB_PASSWORD = var.db_password
    }
  }
}
