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
