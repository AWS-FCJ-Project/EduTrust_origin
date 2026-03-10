variable "aws_region" {
  description = "AWS region"
  type        = string
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
  description = "EC2 instance name"
  type        = string
}

variable "ec2_key_name" {
  description = "EC2 key pair name for SSH access"
  type        = string
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
