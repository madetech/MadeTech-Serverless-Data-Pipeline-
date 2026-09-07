output "rule_arn" {
  value = aws_cloudwatch_event_rule.s3_object_created.arn
}
