terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "6.34.0"
    }
  }

  backend "s3" {
    bucket       = "aws-fcj-terraform-641458060045"
    key          = "backend/terraform.tfstate"
    region       = "ap-southeast-1"
    use_lockfile = true
  }
}

provider "aws" {
  region = var.aws_region
}

# --- VPC & Network Configuration ---

resource "aws_vpc" "main" {
  cidr_block           = var.vpc_cidr_block
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = {
    Name = var.vpc_name
  }
}

# Private Subnets
resource "aws_subnet" "private_1a" {
  vpc_id            = aws_vpc.main.id
  cidr_block        = var.private_subnet_1a_cidr
  availability_zone = "ap-southeast-1a"

  tags = {
    Name = "private-subnet-01"
  }
}

resource "aws_subnet" "private_1c" {
  vpc_id            = aws_vpc.main.id
  cidr_block        = var.private_subnet_1c_cidr
  availability_zone = "ap-southeast-1c"

  tags = {
    Name = "private-subnet-02"
  }
}

# Public Subnets
resource "aws_subnet" "public_1a" {
  vpc_id                  = aws_vpc.main.id
  cidr_block              = var.public_subnet_1a_cidr
  availability_zone       = "ap-southeast-1a"
  map_public_ip_on_launch = true

  tags = {
    Name = "public-subnet-01"
  }
}

resource "aws_subnet" "public_1c" {
  vpc_id                  = aws_vpc.main.id
  cidr_block              = var.public_subnet_1c_cidr
  availability_zone       = "ap-southeast-1c"
  map_public_ip_on_launch = true

  tags = {
    Name = "public-subnet-02"
  }
}

# Internet Gateway & Public Route Table
resource "aws_internet_gateway" "main" {
  vpc_id = aws_vpc.main.id

  tags = {
    Name = var.igw_name
  }
}

resource "aws_route_table" "public" {
  vpc_id = aws_vpc.main.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.main.id
  }

  tags = {
    Name = "public-route-table"
  }
}

resource "aws_route_table_association" "public_1a" {
  subnet_id      = aws_subnet.public_1a.id
  route_table_id = aws_route_table.public.id
}

resource "aws_route_table_association" "public_1c" {
  subnet_id      = aws_subnet.public_1c.id
  route_table_id = aws_route_table.public.id
}

# Elastic IP for NAT Gateway
resource "aws_eip" "nat_1a" {
  domain = "vpc"

  tags = {
    Name = "eip-nat-1a"
  }
}

# NAT Gateway (shared by both private subnets to reduce cost)
resource "aws_nat_gateway" "nat_1a" {
  allocation_id = aws_eip.nat_1a.id
  subnet_id     = aws_subnet.public_1a.id

  tags = {
    Name = "nat-gateway-1a"
  }

  depends_on = [aws_internet_gateway.main]
}

# Route Tables for Private Subnets
resource "aws_route_table" "private_1a" {
  vpc_id = aws_vpc.main.id

  route {
    cidr_block     = "0.0.0.0/0"
    nat_gateway_id = aws_nat_gateway.nat_1a.id
  }

  tags = {
    Name = "private-route-table-1a"
  }
}

resource "aws_route_table_association" "private_1a" {
  subnet_id      = aws_subnet.private_1a.id
  route_table_id = aws_route_table.private_1a.id
}

resource "aws_route_table" "private_1c" {
  vpc_id = aws_vpc.main.id

  route {
    cidr_block     = "0.0.0.0/0"
    nat_gateway_id = aws_nat_gateway.nat_1a.id
  }

  tags = {
    Name = "private-route-table-1c"
  }
}

resource "aws_route_table_association" "private_1c" {
  subnet_id      = aws_subnet.private_1c.id
  route_table_id = aws_route_table.private_1c.id
}

# --- End Network Configuration ---

data "aws_iam_policy_document" "ec2_assume_role" {
  statement {
    effect  = "Allow"
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["ec2.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "backend" {
  name               = "${var.ec2_instance_name}-role"
  assume_role_policy = data.aws_iam_policy_document.ec2_assume_role.json
}

resource "aws_iam_role_policy_attachment" "backend_ssm" {
  role       = aws_iam_role.backend.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
}

resource "aws_iam_instance_profile" "backend" {
  name = "${var.ec2_instance_name}-instance-profile"
  role = aws_iam_role.backend.name
}

# --- Load Balancer Configuration ---
resource "aws_security_group" "alb" {
  name        = "${var.ec2_instance_name}-alb-sg"
  description = "Security group for ALB"
  vpc_id      = aws_vpc.main.id

  # Allow HTTP and HTTPS from the internet
  ingress {
    description = "HTTP from Internet"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "HTTPS from Internet"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }


  egress {
    description = "Allow all outbound"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${var.ec2_instance_name}-alb-sg"
  }
}

resource "aws_lb" "main" {
  name                       = "${var.ec2_instance_name}-alb"
  internal                   = false
  load_balancer_type         = "application"
  security_groups            = [aws_security_group.alb.id]
  subnets                    = [aws_subnet.public_1a.id, aws_subnet.public_1c.id]
  drop_invalid_header_fields = true

  enable_deletion_protection = false

  tags = {
    Name = "${var.ec2_instance_name}-alb"
  }
}

resource "aws_lb_target_group" "backend" {
  name     = "${var.ec2_instance_name}-tg"
  port     = var.backend_port
  protocol = "HTTP"
  vpc_id   = aws_vpc.main.id

  health_check {
    path                = "/health"
    healthy_threshold   = 2
    unhealthy_threshold = 2
    timeout             = 3
    interval            = 5
    matcher             = "200"
  }
}

resource "aws_lb_listener" "http" {
  load_balancer_arn = aws_lb.main.arn
  port              = "80"
  protocol          = "HTTP"

  default_action {
    type = "redirect"
    redirect {
      port        = "443"
      protocol    = "HTTPS"
      status_code = "HTTP_301"
    }
  }
}

resource "aws_lb_listener" "https" {
  load_balancer_arn = aws_lb.main.arn
  port              = "443"
  protocol          = "HTTPS"
  ssl_policy        = "ELBSecurityPolicy-TLS-1-2-2017-01"
  certificate_arn   = var.certificate_arn

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.backend.arn
  }
}

resource "aws_lb_target_group_attachment" "backend_1" {
  target_group_arn = aws_lb_target_group.backend.arn
  target_id        = aws_instance.backend_1.id
  port             = var.backend_port
}

resource "aws_lb_target_group_attachment" "backend_2" {
  target_group_arn = aws_lb_target_group.backend.arn
  target_id        = aws_instance.backend_2.id
  port             = var.backend_port
}

# --- Backend EC2 Security Group ---
resource "aws_security_group" "backend" {
  name        = "${var.ec2_instance_name}-sg"
  description = "Security group for backend EC2"
  vpc_id      = aws_vpc.main.id

  ingress {
    description     = "App port from ALB"
    from_port       = var.backend_port
    to_port         = var.backend_port
    protocol        = "tcp"
    security_groups = [aws_security_group.alb.id]
  }

  egress {
    description = "HTTPS outbound"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    description = "HTTP outbound"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    description = "DocumentDB (MongoDB) outbound"
    from_port   = 27017
    to_port     = 27017
    protocol    = "tcp"
    cidr_blocks = var.docdb_egress_cidr_blocks
  }

  egress {
    description = "ElastiCache Redis outbound"
    from_port   = 6379
    to_port     = 6379
    protocol    = "tcp"
    cidr_blocks = var.redis_egress_cidr_blocks
  }

  tags = {
    Name = "${var.ec2_instance_name}-sg"
  }
}

resource "aws_instance" "backend_1" {
  ami                    = var.ec2_ami_id
  instance_type          = var.ec2_instance_type
  key_name               = var.ec2_key_name
  iam_instance_profile   = aws_iam_instance_profile.backend.name
  vpc_security_group_ids = [aws_security_group.backend.id]
  subnet_id              = aws_subnet.private_1a.id
  ebs_optimized          = true

  metadata_options {
    http_endpoint               = "enabled"
    http_tokens                 = "required"
    http_put_response_hop_limit = 2
  }

  tags = {
    Name = "${var.ec2_instance_name}-1"
  }
}

resource "aws_instance" "backend_2" {
  ami                    = var.ec2_ami_id
  instance_type          = var.ec2_instance_type
  key_name               = var.ec2_key_name
  iam_instance_profile   = aws_iam_instance_profile.backend.name
  vpc_security_group_ids = [aws_security_group.backend.id]
  subnet_id              = aws_subnet.private_1c.id
  ebs_optimized          = true

  metadata_options {
    http_endpoint               = "enabled"
    http_tokens                 = "required"
    http_put_response_hop_limit = 2
  }

  tags = {
    Name = "${var.ec2_instance_name}-2"
  }
}

resource "aws_ecr_repository" "backend" {
  name                 = var.ecr_repository_name
  image_tag_mutability = var.ecr_tag_immutable ? "IMMUTABLE" : "MUTABLE"

  encryption_configuration {
    encryption_type = "KMS"
  }

  image_scanning_configuration {
    scan_on_push = true
  }
}
