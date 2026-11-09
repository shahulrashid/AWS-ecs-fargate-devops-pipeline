# Deployment Guide

## Prerequisites
- AWS account, with an IAM user/SSO profile that can create the resources (use `aws configure` or `aws configure sso`)
- AWS CLI v2, Terraform >= 1.5, Docker, Git, a GitHub account
- **Set an AWS Budget alert in the console first** (Billing -> Budgets) as a safety net

## 1. Create the GitHub repo
```bash
git init && git add . && git commit -m "Initial commit"
git branch -M main
git remote add origin git@github.com:<you>/aws-cloud-native-devops.git
git push -u origin main
```
The first push will run CI (tests pass) but the deploy job will fail because AWS isn't set up yet. That's expected.

## 2. Provision infrastructure
```bash
cd infrastructure/terraform
cp terraform.tfvars.example terraform.tfvars   # edit github_repo and alarm_email
terraform init
terraform plan
terraform apply
```
- If you already have the GitHub OIDC provider in your account, add `create_github_oidc_provider = false`.
- Confirm the SNS subscription email AWS sends you, otherwise no alarm emails arrive.
- Note the outputs: `alb_url` and `github_deploy_role_arn`.

## 3. Connect GitHub to AWS
In the GitHub repo: **Settings -> Secrets and variables -> Actions -> Variables**, add:
- `AWS_ROLE_ARN` = value of `github_deploy_role_arn`
- `AWS_REGION` = `ap-south-1` (or your region)

## 4. Deploy
Push any change to `main` (or re-run the failed workflow). Pipeline:
`test -> build image -> OIDC login -> push to ECR -> render task def -> update ECS -> wait for stability`.

## 5. Verify
```bash
ALB=$(terraform output -raw alb_url)
curl $ALB/health
curl -X POST $ALB/tasks -H "Content-Type: application/json" -d '{"title":"first task"}'
curl $ALB/tasks
```
Then check the CloudWatch dashboard `task-api-dashboard` and log group `/ecs/task-api`.

## 6. Clean up (important)
```bash
terraform destroy
```
Verify in the console that the ALB, ECS service and ECR repo are gone.

## CI / CD / Continuous Deployment (interview answer)
- **CI**: every push/PR is automatically built and tested.
- **Continuous Delivery**: every passing change is *releasable*, but a human approves the release.
- **Continuous Deployment**: every passing change on `main` goes to production automatically, with no manual gate. This pipeline is continuous deployment. To make it continuous delivery, add a GitHub Environment with required reviewers to the `deploy` job.
