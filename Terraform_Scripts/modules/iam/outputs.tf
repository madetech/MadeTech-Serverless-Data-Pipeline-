output "extraction_lambda_role_arn" {
  value = aws_iam_role.extraction_lambda.arn
}

output "transformation_lambda_role_arn" {
  value = aws_iam_role.transformation_lambda.arn
}
output "s3_access_policy_arn" {
  value = aws_iam_policy.s3_access.arn
}

output "rds_access_policy_arn" {
  value = aws_iam_policy.rds_access.arn
}

output "state_machine_access_policy_arn" {
  value = aws_iam_role.StateMachineRole.arn
}

output "state_machine_role_id" {
  value = aws_iam_role.StateMachineRole.id
}

output "scheduler_role_arn" {
  value = aws_iam_role.SchedulerRole.arn
}

output "scheduler_role_id" {
  value = aws_iam_role.SchedulerRole.id
}