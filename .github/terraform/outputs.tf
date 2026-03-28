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

output "ecr_repository_url" {
  description = "ECR repository URL (for docker push/pull)"
  value       = aws_ecr_repository.backend.repository_url
}

output "secrets_kms_key_arn" {
  description = "The ARN of the KMS key used for encrypting secrets"
  value       = aws_kms_key.secrets.arn
}

output "cloudwatch_dashboard_url" {
  description = "Link to the CloudWatch Dashboard in the AWS Console"
  value       = "https://${var.aws_region}.console.aws.amazon.com/cloudwatch/home?region=${var.aws_region}#dashboards:name=${var.ec2_instance_name}-dashboard"
}

