output "alb_url" {
  value = "http://${aws_lb.app.dns_name}"
}

output "ecr_repository_url" {
  value = aws_ecr_repository.app.repository_url
}

output "ecs_cluster" {
  value = aws_ecs_cluster.main.name
}

output "ecs_service" {
  value = aws_ecs_service.app.name
}

output "github_deploy_role_arn" {
  description = "Put this in GitHub repo variable AWS_ROLE_ARN"
  value       = aws_iam_role.github_deploy.arn
}

output "dynamodb_table" {
  value = aws_dynamodb_table.tasks.name
}
