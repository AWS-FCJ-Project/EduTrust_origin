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
  description = "The ARN of an existing ACM certificate for HTTPS (optional if enable_api_custom_domain=true)"
  type        = string
  default     = ""
  validation {
    condition     = length(trimspace(var.certificate_arn)) > 0 || var.enable_api_custom_domain
    error_message = "Set certificate_arn, or set enable_api_custom_domain=true to have Terraform provision/validate an ACM certificate."
  }
}

variable "enable_api_custom_domain" {
  description = "When true, Terraform provisions ACM + Route53 records for a custom API domain and attaches the cert to the ALB listener."
  type        = bool
  default     = false
}

variable "api_domain_name" {
  description = "API fully qualified domain name (e.g., api.edu-trust.app)"
  type        = string
  default     = ""
  validation {
    condition     = !var.enable_api_custom_domain || length(trimspace(var.api_domain_name)) > 0
    error_message = "api_domain_name must be set when enable_api_custom_domain=true."
  }
}

variable "route53_zone_id" {
  description = "Route53 hosted zone ID for the parent domain (preferred)."
  type        = string
  default     = ""
}

variable "route53_zone_name" {
  description = "Route53 hosted zone name (alternative to route53_zone_id), e.g. edu-trust.app"
  type        = string
  default     = ""
  validation {
    condition     = !var.enable_api_custom_domain || length(trimspace(var.route53_zone_id)) > 0 || length(trimspace(var.route53_zone_name)) > 0
    error_message = "Provide route53_zone_id or route53_zone_name when enable_api_custom_domain=true."
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

variable "asg_max_size" {
  description = "Maximum size of the Auto Scaling Group"
  type        = number
}

variable "asg_desired_capacity" {
  description = "Desired capacity of the Auto Scaling Group"
  type        = number
}
