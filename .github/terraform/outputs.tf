output "aws_region" {
  description = "AWS region where resources are deployed"
  value       = var.aws_region
}

output "vpc_id" {
  description = "The ID of the VPC"
  value       = aws_vpc.main.id
}

output "igw_id" {
  description = "The ID of the Internet Gateway"
  value       = aws_internet_gateway.main.id
}

output "backend_port" {
  description = "The port configured for the backend application."
  value       = var.backend_port
}

output "backend_asg_name" {
  description = "The name of the Auto Scaling Group"
  value       = aws_autoscaling_group.backend.name
}

output "backend_launch_template_id" {
  description = "The ID of the Launch Template"
  value       = aws_launch_template.backend.id
}

output "alb_dns_name" {
  description = "DNS name of the Application Load Balancer"
  value       = aws_lb.main.dns_name
}

output "backend_target_group_arn" {
  description = "Target Group ARN for the backend service (used for deployment health verification)"
  value       = aws_lb_target_group.backend.arn
}

output "cognito_user_pool_id" {
  description = "Cognito User Pool ID for backend authentication."
  value       = aws_cognito_user_pool.backend.id
}

output "cognito_user_pool_client_id" {
  description = "Cognito User Pool App Client ID for backend authentication."
  value       = aws_cognito_user_pool_client.backend.id
}

output "alarm_sns_topic_arn" {
  description = "SNS topic ARN used for CloudWatch alarm notifications, if alarms are enabled."
  value       = var.enable_alarms ? aws_sns_topic.alarms[0].arn : null
}

output "api_domain_name" {
  description = "Custom API domain name (if enabled)"
  value       = var.enable_api_custom_domain ? var.api_domain_name : null
}

output "ecr_repository_url" {
  description = "ECR repository URL (for docker push/pull)"
  value       = aws_ecr_repository.backend.repository_url
}

output "camera_detect_bucket_name" {
  description = "S3 bucket name used to store camera cheating-detection evidence"
  value       = aws_s3_bucket.camera_detect.bucket
}

output "frontend_waf_web_acl_arn" {
  description = "WAFv2 Web ACL ARN for the frontend (CloudFront scope), if enabled."
  value       = var.enable_frontend_waf ? aws_wafv2_web_acl.frontend[0].arn : null
}

output "secrets_kms_key_arn" {
  description = "The ARN of the KMS key used for encrypting secrets"
  value       = aws_kms_key.secrets.arn
}
