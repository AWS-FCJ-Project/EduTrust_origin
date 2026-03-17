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

output "backend_1_id" {
  description = "EC2 instance 1 ID"
  value       = aws_instance.backend_1.id
}

output "backend_1_private_ip" {
  description = "EC2 instance 1 private IP"
  value       = aws_instance.backend_1.private_ip
}

output "backend_2_id" {
  description = "EC2 instance 2 ID"
  value       = aws_instance.backend_2.id
}

output "backend_2_private_ip" {
  description = "EC2 instance 2 private IP"
  value       = aws_instance.backend_2.private_ip
}

output "alb_dns_name" {
  description = "DNS name of the Application Load Balancer"
  value       = aws_lb.main.dns_name
}

output "ecr_repository_url" {
  description = "ECR repository URL (for docker push/pull)"
  value       = aws_ecr_repository.backend.repository_url
}
