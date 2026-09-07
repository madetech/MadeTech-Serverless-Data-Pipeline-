# Lambda execution roles

data "aws_iam_policy_document" "lambda_assume_role" {
  statement {
    effect = "Allow"

    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }

    actions = ["sts:AssumeRole"]
  }
}

resource "aws_iam_role" "extraction_lambda" {
  name               = "${var.project_name}-extraction-lambda"
  assume_role_policy = data.aws_iam_policy_document.lambda_assume_role.json
}

resource "aws_iam_role" "transformation_lambda" {
  name               = "${var.project_name}-transformation-lambda"
  assume_role_policy = data.aws_iam_policy_document.lambda_assume_role.json
}

resource "aws_iam_role_policy_attachment" "extraction_basic" {
  role       = aws_iam_role.extraction_lambda.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_iam_role_policy_attachment" "transformation_basic" {
  role       = aws_iam_role.transformation_lambda.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_iam_role_policy_attachment" "transformation_vpc" {
  role       = aws_iam_role.transformation_lambda.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaVPCAccessExecutionRole"
}


# S3 access policy

data "aws_iam_policy_document" "s3_access" {
  statement {
    sid    = "S3ReadWrite"
    effect = "Allow"
    actions = [
      "s3:GetObject",
      "s3:PutObject",
      "s3:ListBucket"
    ]
    resources = [
      var.s3_bucket_arn,
      "${var.s3_bucket_arn}/*"
    ]
  }
}

resource "aws_iam_policy" "s3_access" {
  name        = "${var.project_name}-s3-access"
  description = "Access policy for ${var.s3_bucket_arn}"
  policy      = data.aws_iam_policy_document.s3_access.json
}

resource "aws_iam_role_policy_attachment" "extraction_s3" {
  role       = aws_iam_role.extraction_lambda.name
  policy_arn = aws_iam_policy.s3_access.arn
}

resource "aws_iam_role_policy_attachment" "transformation_s3" {
  role       = aws_iam_role.transformation_lambda.name
  policy_arn = aws_iam_policy.s3_access.arn
}


# RDS access policy

data "aws_iam_policy_document" "rds_access" {
  statement {
    sid    = "RDSConnect"
    effect = "Allow"
    actions = [
      "rds-db:connect"
    ]
    resources = [var.rds_arn]
  }

  statement {
    sid    = "RDSDescribe"
    effect = "Allow"
    actions = [
      "rds:DescribeDBInstances",
      "rds:ListTagsForResource"
    ]
    resources = [var.rds_arn]
  }
}

resource "aws_iam_policy" "rds_access" {
  name        = "${var.project_name}-rds-access"
  description = "Access policy for ${var.rds_arn}"
  policy      = data.aws_iam_policy_document.rds_access.json
}