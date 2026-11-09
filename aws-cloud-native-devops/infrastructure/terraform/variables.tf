variable "aws_region" {
  type    = string
  default = "ap-south-1"
}

variable "project" {
  type    = string
  default = "task-api"
}

variable "github_repo" {
  description = "GitHub repo allowed to deploy, as owner/name (e.g. janedoe/aws-cloud-native-devops)"
  type        = string
}

variable "alarm_email" {
  description = "Email address for CloudWatch alarm notifications"
  type        = string
}

variable "container_port" {
  type    = number
  default = 8000
}

variable "task_cpu" {
  type    = number
  default = 256
}

variable "task_memory" {
  type    = number
  default = 512
}

variable "desired_count" {
  description = "Number of Fargate tasks. Set to 0 to stop paying for compute."
  type        = number
  default     = 1
}

variable "create_github_oidc_provider" {
  description = "Set false if the GitHub OIDC provider already exists in this AWS account"
  type        = bool
  default     = true
}
