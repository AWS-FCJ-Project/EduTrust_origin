variable "aws_region" {
  description = "AWS region"
  type        = string
}

variable "vpc_name" {
  description = "Name for the VPC"
  type        = string
}

variable "igw_name" {
  description = "Name for the Internet Gateway"
  type        = string
}

variable "backend_port" {
  description = "The port the backend application listens on"
  type        = number
}

variable "ec2_instance_type" {
  description = "EC2 instance type"
  type        = string
}

variable "ec2_instance_name" {
  description = "EC2 instance name (used as resource name prefix)"
  type        = string
}

variable "ec2_key_name" {
  description = "EC2 key pair name for SSH access (optional, for debug/testing)"
  type        = string
}

variable "ecr_repository_name" {
  description = "ECR repository name for backend image"
  type        = string
}

variable "ecr_tag_immutable" {
  description = "Whether ECR image tags are immutable"
  type        = bool
}

variable "ssh_ingress_cidr_blocks" {
  description = "Allowed IPv4 CIDR blocks for inbound SSH (port 22)"
  type        = list(string)
}

variable "https_ingress_cidr_blocks" {
  description = "Allowed IPv4 CIDR blocks for inbound HTTPS (port 443) to the origin (e.g., Cloudflare)"
  type        = list(string)
}

variable "docdb_egress_cidr_blocks" {
  description = "Allowed IPv4 CIDR blocks for outbound DocumentDB (MongoDB) traffic (port 27017)"
  type        = list(string)
}

variable "redis_egress_cidr_blocks" {
  description = "Allowed IPv4 CIDR blocks for outbound ElastiCache Redis traffic (port 6379)"
  type        = list(string)
}

# --- VPC & Subnet Network Variables ---

variable "vpc_cidr_block" {
  description = "CIDR block for the VPC"
  type        = string
  validation {
    condition     = length(trimspace(var.vpc_cidr_block)) > 0
    error_message = "vpc_cidr_block must be set (e.g. via TERRAFORM_VARIABLES -> terraform.tfvars) for the VPC network to be created."
  }
}
variable "private_subnet_1a_cidr" {
  description = "CIDR block for private subnet in AZ 1a"
  type        = string
  validation {
    condition     = length(trimspace(var.private_subnet_1a_cidr)) > 0
    error_message = "private_subnet_1a_cidr must be set (e.g. via TERRAFORM_VARIABLES -> terraform.tfvars) for the private subnet in AZ 1a."
  }
}
variable "private_subnet_1c_cidr" {
  description = "CIDR block for private subnet in AZ 1c"
  type        = string
  validation {
    condition     = length(trimspace(var.private_subnet_1c_cidr)) > 0
    error_message = "private_subnet_1c_cidr must be set (e.g. via TERRAFORM_VARIABLES -> terraform.tfvars) for the private subnet in AZ 1c."
  }
}
variable "public_subnet_1a_cidr" {
  description = "CIDR block for public subnet in AZ 1a"
  type        = string
  validation {
    condition     = length(trimspace(var.public_subnet_1a_cidr)) > 0
    error_message = "public_subnet_1a_cidr must be set (e.g. via TERRAFORM_VARIABLES -> terraform.tfvars) for the public subnet in AZ 1a."
  }
}
variable "public_subnet_1c_cidr" {
  description = "CIDR block for public subnet in AZ 1c"
  type        = string
  validation {
    condition     = length(trimspace(var.public_subnet_1c_cidr)) > 0
    error_message = "public_subnet_1c_cidr must be set (e.g. via TERRAFORM_VARIABLES -> terraform.tfvars) for the public subnet in AZ 1c."
  }
}

variable "certificate_arn" {
  description = "The ARN of the ACM certificate for HTTPS"
  type        = string
  validation {
    condition     = length(trimspace(var.certificate_arn)) > 0
    error_message = "certificate_arn must be set (ACM ARN) to create the HTTPS ALB listener."
  }
}

variable "backend_image_tag" {
  description = "Docker image tag for the backend"
  type        = string
}

variable "asg_min_size" {
  description = "Minimum size of the Auto Scaling Group"
  type        = number
}

variable "asg_desired_capacity" {
  description = "Desired capacity of the Auto Scaling Group"
  type        = number
}

variable "asg_max_size" {
  description = "Maximum size of the Auto Scaling Group"
  type        = number
}

# --- VPC Endpoint Service Names ---
variable "s3_endpoint_service_name" {
  description = "Service name for S3 VPC Endpoint"
  type        = string
}

variable "ecr_dkr_endpoint_service_name" {
  description = "Service name for ECR DKR VPC Endpoint"
  type        = string
}

variable "ecr_api_endpoint_service_name" {
  description = "Service name for ECR API VPC Endpoint"
  type        = string
}

variable "ssm_endpoint_service_name" {
  description = "Service name for SSM VPC Endpoint"
  type        = string
}

variable "sts_endpoint_service_name" {
  description = "Service name for STS VPC Endpoint"
  type        = string
}

variable "logs_endpoint_service_name" {
  description = "Service name for CloudWatch Logs VPC Endpoint"
  type        = string
}

