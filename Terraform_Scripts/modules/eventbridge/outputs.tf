output "rule_arn" {
  value = aws_scheduler_schedule.step_function_schedule.arn
}

output "rule_name" {
  value = aws_scheduler_schedule.step_function_schedule.name
}

