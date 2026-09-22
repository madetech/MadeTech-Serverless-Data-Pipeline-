resource "aws_cloudwatch_event_rule" "s3_object_created" {
  name        = "${var.project_name}-s3-object-created"
  description = "Trigger transformation when an object is created in S3"

  event_pattern = jsonencode({
    source      = ["aws.s3"]
    detail-type = ["Object Created"]
    detail = {
      bucket = {
        name = [var.s3_bucket_name]
      }
    }
  })
}

resource "aws_cloudwatch_event_target" "transformation" {
  rule = aws_cloudwatch_event_rule.s3_object_created.name
  arn  = var.transformation_function_arn
}

resource "aws_lambda_permission" "eventbridge" {
  statement_id  = "AllowEventBridgeInvoke"
  action        = "lambda:InvokeFunction"
  function_name = var.transformation_function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.s3_object_created.arn
}
