variable "aws_region" {
  description = "AWS region"
  type        = string
}

variable "vpc_name" {
  description = "Name for the VPC"
  type        = string
  default     = "my-backend-vpc"
}

variable "igw_name" {
  description = "Name for the Internet Gateway"
  type        = string
  default     = "my-backend-igw"
}

variable "backend_port" {
  description = "The port the backend application listens on"
  type        = number
  default     = 8000
}

variable "ec2_instance_type" {
  description = "EC2 instance type"
  type        = string
}

variable "ec2_ami_id" {
  description = "AMI ID for EC2 instance"
  type        = string
}

variable "ec2_instance_name" {
  description = "EC2 instance name (used as resource name prefix)"
  type        = string
}

variable "ec2_key_name" {
  description = "EC2 key pair name for SSH access (optional, for debug/testing)"
  type        = string
  default     = null
}

variable "ecr_repository_name" {
  description = "ECR repository name for backend image"
  type        = string
  default     = "edutrust-backend"
}

variable "ecr_tag_immutable" {
  description = "Whether ECR image tags are immutable"
  type        = bool
  default     = true
}

variable "ssh_ingress_cidr_blocks" {
  description = "Allowed IPv4 CIDR blocks for inbound SSH (port 22)"
  type        = list(string)
  default     = ["0.0.0.0/0"]
}

variable "https_ingress_cidr_blocks" {
  description = "Allowed IPv4 CIDR blocks for inbound HTTPS (port 443) to the origin (e.g., Cloudflare)"
  type        = list(string)
  default     = ["0.0.0.0/0"]
}

variable "docdb_egress_cidr_blocks" {
  description = "Allowed IPv4 CIDR blocks for outbound DocumentDB (MongoDB) traffic (port 27017)"
  type        = list(string)
  default     = ["0.0.0.0/0"]
}

variable "redis_egress_cidr_blocks" {
  description = "Allowed IPv4 CIDR blocks for outbound ElastiCache Redis traffic (port 6379)"
  type        = list(string)
  default     = ["0.0.0.0/0"]
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