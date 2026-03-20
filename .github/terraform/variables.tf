// --- AWS Config ---
variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = ""
  validation {
    condition     = can(regex("^[a-z]{2}-[a-z]+-[0-9]$", var.aws_region)) || var.aws_region == ""
    error_message = "The aws_region must be a valid AWS region identifier (e.g., ap-southeast-1)."
  }
}

// --- Network Config (VPC & Subnets) ---
variable "vpc_name" {
  description = "Name for the VPC"
  type        = string
  default     = ""
}

variable "vpc_cidr_block" {
  description = "CIDR block for the VPC"
  type        = string
  default     = ""
  validation {
    condition     = can(cidrnetmask(var.vpc_cidr_block)) || var.vpc_cidr_block == ""
    error_message = "The vpc_cidr_block must be a valid IPv4 CIDR notation."
  }
}

variable "igw_name" {
  description = "Name for the Internet Gateway"
  type        = string
  default     = ""
}

variable "private_subnet_1a_cidr" {
  description = "CIDR block for private subnet in AZ 1a"
  type        = string
  default     = ""
  validation {
    condition     = can(cidrnetmask(var.private_subnet_1a_cidr)) || var.private_subnet_1a_cidr == ""
    error_message = "The private_subnet_1a_cidr must be a valid IPv4 CIDR notation."
  }
}

variable "private_subnet_1c_cidr" {
  description = "CIDR block for private subnet in AZ 1c"
  type        = string
  default     = ""
  validation {
    condition     = can(cidrnetmask(var.private_subnet_1c_cidr)) || var.private_subnet_1c_cidr == ""
    error_message = "The private_subnet_1c_cidr must be a valid IPv4 CIDR notation."
  }
}

variable "public_subnet_1a_cidr" {
  description = "CIDR block for public subnet in AZ 1a"
  type        = string
  default     = ""
  validation {
    condition     = can(cidrnetmask(var.public_subnet_1a_cidr)) || var.public_subnet_1a_cidr == ""
    error_message = "The public_subnet_1a_cidr must be a valid IPv4 CIDR notation."
  }
}

variable "public_subnet_1c_cidr" {
  description = "CIDR block for public subnet in AZ 1c"
  type        = string
  default     = ""
  validation {
    condition     = can(cidrnetmask(var.public_subnet_1c_cidr)) || var.public_subnet_1c_cidr == ""
    error_message = "The public_subnet_1c_cidr must be a valid IPv4 CIDR notation."
  }
}

// --- EC2 & ASG Config ---
variable "ec2_instance_type" {
  description = "EC2 instance type"
  type        = string
  default     = ""
}

variable "ec2_ami_id" {
  description = "AMI ID for EC2 instance"
  type        = string
  default     = ""
  validation {
    condition     = can(regex("^ami-", var.ec2_ami_id)) || var.ec2_ami_id == ""
    error_message = "The ec2_ami_id must start with 'ami-'."
  }
}

variable "ec2_instance_name" {
  description = "EC2 instance name"
  type        = string
  default     = ""
}

variable "ec2_key_name" {
  description = "EC2 key pair name for SSH access"
  type        = string
  default     = ""
}

variable "asg_min_size" {
  description = "Minimum number of instances in the ASG"
  type        = number
  default     = null
  validation {
    condition     = var.asg_min_size == null ? true : var.asg_min_size >= 0
    error_message = "asg_min_size must be a non-negative integer."
  }
}

variable "asg_max_size" {
  description = "Maximum number of instances in the ASG"
  type        = number
  default     = null
  validation {
    condition     = var.asg_max_size == null ? true : var.asg_max_size >= 0
    error_message = "asg_max_size must be a non-negative integer."
  }
}

variable "asg_desired_capacity" {
  description = "Desired number of instances in the ASG"
  type        = number
  default     = null
  validation {
    condition     = var.asg_desired_capacity == null ? true : var.asg_desired_capacity >= 0
    error_message = "asg_desired_capacity must be a non-negative integer."
  }
}

// --- Backend App Config ---
variable "backend_port" {
  description = "The port the backend application listens on"
  type        = number
  default     = null
  validation {
    condition     = var.backend_port == null ? true : (var.backend_port > 0 && var.backend_port < 65536)
    error_message = "backend_port must be between 1 and 65535."
  }
}

variable "backend_image_tag" {
  description = "The tag of the Docker image to deploy"
  type        = string
  default     = "latest"
}

variable "ecr_repository_name" {
  description = "ECR repository name for backend image"
  type        = string
  default     = ""
}

variable "ecr_tag_immutable" {
  description = "Whether ECR image tags are immutable"
  type        = bool
  default     = true
}

variable "certificate_arn" {
  description = "The ARN of the ACM certificate for HTTPS"
  type        = string
  default     = ""
  validation {
    condition     = can(regex("^arn:aws:acm:", var.certificate_arn)) || var.certificate_arn == ""
    error_message = "The certificate_arn must be a valid AWS ACM ARN."
  }
}

// --- Security Group Rules ---
variable "ssh_ingress_cidr_blocks" {
  description = "Allowed IPv4 CIDR blocks for inbound SSH"
  type        = list(string)
  default     = [""]
}

variable "https_ingress_cidr_blocks" {
  description = "Allowed IPv4 CIDR blocks for inbound HTTPS"
  type        = list(string)
  default     = [""]
}

variable "docdb_egress_cidr_blocks" {
  description = "Allowed IPv4 CIDR blocks for outbound DocumentDB traffic"
  type        = list(string)
  default     = [""]
}

variable "redis_egress_cidr_blocks" {
  description = "Allowed IPv4 CIDR blocks for outbound Redis traffic"
  type        = list(string)
  default     = [""]
}
