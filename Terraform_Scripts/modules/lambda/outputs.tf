output "extraction_function_arn" {
  value = aws_lambda_function.extraction.arn
}

output "transformation_function_arn" {
  value = aws_lambda_function.transformation.arn
}

output "transformation_function_name" {
  value = aws_lambda_function.transformation.function_name
}
