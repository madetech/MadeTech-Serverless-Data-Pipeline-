
resource "aws_scheduler_schedule" "step_function_schedule" {
  name       = "${var.project_name}-schedule"
  group_name = "default"

  flexible_time_window {
    mode = "OFF"
  }

  schedule_expression = "rate(1 hours)"

  # Trigger the step function deployed in AWS
  target {
    arn      = var.step_function_arn
    role_arn = var.step_function_role_arn
  }
}
