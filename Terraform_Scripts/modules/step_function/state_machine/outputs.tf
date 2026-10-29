output "step_function_arn"{
    value = aws_sfn_state_machine.sfn_state_machine.arn
}

output "step_function_id"{
    value = aws_sfn_state_machine.sfn_state_machine.id
}


