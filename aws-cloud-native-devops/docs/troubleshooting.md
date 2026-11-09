# Troubleshooting Runbook

Each scenario: symptom, how to reproduce on purpose, investigation, root cause and fix.
**Do these in your own deployment and replace the "Your notes" lines with real outputs/screenshots** since this is what interviewers ask about.

## 1. ALB returns 502 Bad Gateway
- **Reproduce:** change the container port in the Dockerfile CMD to 9000 and deploy.
- **Investigate:** EC2 -> Target Groups -> task-api-tg -> Targets tab (unhealthy / health check failed). `aws elbv2 describe-target-health --target-group-arn <arn>`.
- **Root cause:** the container listens on a different port than the target group / task definition `containerPort` (8000), so the ALB can't connect.
- **Fix:** align the app port, task definition port mapping and target group port.
- Your notes: ...

## 2. Application unavailable / tasks keep restarting
- **Investigate:** `aws ecs describe-services --cluster task-api-cluster --services task-api-service` (see `events`), then `aws ecs describe-tasks` -> `stoppedReason`. ECS console -> service -> Events tab.
- **Common causes:** failing health check (ALB kills task), image pull failure (no public IP / wrong image URI / missing execution role permissions), out-of-memory (exit code 137), app crash on startup.
- **Fix:** depends on the stoppedReason; check CloudWatch logs for the stopped task.
- Your notes: ...

## 3. Container crashes
- **Reproduce locally:** `docker run -e SOMETHING_BAD=1 task-api` or add a broken import.
- **Investigate:** `docker ps -a` (exit code), `docker logs <id>`. In AWS: CloudWatch log stream `ecs/task-api/<task-id>`.
- **Exit codes:** 0 = normal, 1 = app error, 137 = killed (OOM / SIGKILL), 139 = segfault.
- Your notes: ...

## 4. Deployment fails in GitHub Actions
- **Investigate:** Actions tab -> failed step logs.
  - `Not authorized to perform sts:AssumeRoleWithWebIdentity` -> OIDC trust policy `sub` doesn't match repo/branch, or `AWS_ROLE_ARN` is wrong.
  - `AccessDenied ... ecr:` -> deploy role policy missing ECR permissions.
  - `Resource handler returned message... iam:PassRole` -> deploy role can't pass the task roles.
  - `Waiting for service stability` times out -> new tasks are failing health checks (see scenario 1/2); circuit breaker will roll back.
- Your notes: ...

## 5. API returns 500
- **Reproduce:** change the DynamoDB table name env var to a wrong value, redeploy.
- **Investigate:** CloudWatch Logs Insights on `/ecs/task-api`:
  ```
  fields @timestamp, @message
  | filter @message like /ERROR/
  | sort @timestamp desc
  | limit 50
  ```
  Also the `task-api-alb-5xx` alarm should have fired.
- Your notes: ...

## 6. Database connection fails / AccessDeniedException
- **Reproduce:** remove an action from the task role's DynamoDB policy.
- **Investigate:** logs show `AccessDeniedException` or `ResourceNotFoundException`. `/health/ready` returns 503. Check: task **role** (not execution role) policy, table name env var, region.
- **Fix:** correct IAM policy / env var. Key lesson: execution role vs task role.
- Your notes: ...

## 7. High CPU
- **Reproduce:** load test, e.g. `hey -z 5m -c 50 $ALB/tasks` (or `ab`).
- **Investigate:** CloudWatch dashboard CPUUtilization; `task-api-cpu-high` alarm -> SNS email. Container Insights for per-task view.
- **Fix:** increase `task_cpu`, add ECS service auto scaling, optimize the code (e.g. DynamoDB `Scan` in `GET /tasks` is O(table size); use pagination/Query).
- Your notes: ...
