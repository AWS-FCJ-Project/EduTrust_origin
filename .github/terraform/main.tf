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

# --- VPC Endpoints ---

# Security Group for VPC Endpoints
resource "aws_security_group" "vpc_endpoints" {
  name        = "${var.ec2_instance_name}-vpce-sg"
  description = "Security group for VPC Endpoints"
  vpc_id      = aws_vpc.main.id

  lifecycle {
    create_before_destroy = true
  }

  tags = { Name = "vpc-endpoint-sg" }
}

resource "aws_security_group_rule" "vpce_https_ingress" {
  description              = "HTTPS from Backend EC2"
  type                     = "ingress"
  from_port                = 443
  to_port                  = 443
  protocol                 = "tcp"
  security_group_id        = aws_security_group.vpc_endpoints.id
  source_security_group_id = aws_security_group.backend.id
}

resource "aws_security_group_rule" "vpce_egress_all" {
  description       = "Allow all outbound traffic"
  type              = "egress"
  from_port         = 0
  to_port           = 0
  protocol          = "-1"
  security_group_id = aws_security_group.vpc_endpoints.id
  cidr_blocks       = ["0.0.0.0/0"]
}

# S3 Gateway Endpoint (Free and critical for ECR)
resource "aws_vpc_endpoint" "s3" {
  vpc_id            = aws_vpc.main.id
  service_name      = var.s3_endpoint_service_name
  vpc_endpoint_type = "Gateway"
  route_table_ids   = [aws_route_table.private_1a.id, aws_route_table.private_1c.id]

  tags = { Name = "s3-endpoint" }
}

# ECR Endpoints (Requires both 'dkr' and 'api' for a complete image pull)
resource "aws_vpc_endpoint" "ecr_dkr" {
  vpc_id              = aws_vpc.main.id
  service_name        = var.ecr_dkr_endpoint_service_name
  vpc_endpoint_type   = "Interface"
  subnet_ids          = [aws_subnet.private_1a.id, aws_subnet.private_1c.id]
  security_group_ids  = [aws_security_group.vpc_endpoints.id]
  private_dns_enabled = true

  tags = { Name = "ecr-dkr-endpoint" }
}

resource "aws_vpc_endpoint" "ecr_api" {
  vpc_id              = aws_vpc.main.id
  service_name        = var.ecr_api_endpoint_service_name
  vpc_endpoint_type   = "Interface"
  subnet_ids          = [aws_subnet.private_1a.id, aws_subnet.private_1c.id]
  security_group_ids  = [aws_security_group.vpc_endpoints.id]
  private_dns_enabled = true

  tags = { Name = "ecr-api-endpoint" }
}

# SSM Endpoint (To retrieve internal Parameter Store)
resource "aws_vpc_endpoint" "ssm" {
  vpc_id              = aws_vpc.main.id
  service_name        = var.ssm_endpoint_service_name
  vpc_endpoint_type   = "Interface"
  subnet_ids          = [aws_subnet.private_1a.id, aws_subnet.private_1c.id]
  security_group_ids  = [aws_security_group.vpc_endpoints.id]
  private_dns_enabled = true

  tags = { Name = "ssm-endpoint" }
}

# STS Endpoint (Critical for authentication in Private Subnets)
resource "aws_vpc_endpoint" "sts" {
  vpc_id              = aws_vpc.main.id
  service_name        = var.sts_endpoint_service_name
  vpc_endpoint_type   = "Interface"
  subnet_ids          = [aws_subnet.private_1a.id, aws_subnet.private_1c.id]
  security_group_ids  = [aws_security_group.vpc_endpoints.id]
  private_dns_enabled = true

  tags = { Name = "sts-endpoint" }
}

# CloudWatch Logs Endpoint (To send logs to CloudWatch)
resource "aws_vpc_endpoint" "logs" {
  vpc_id              = aws_vpc.main.id
  service_name        = var.logs_endpoint_service_name
  vpc_endpoint_type   = "Interface"
  subnet_ids          = [aws_subnet.private_1a.id, aws_subnet.private_1c.id]
  security_group_ids  = [aws_security_group.vpc_endpoints.id]
  private_dns_enabled = true

  tags = { Name = "logs-endpoint" }
}

# --- End Network Configuration ---

# --- Monitoring: VPC Flow Logs ---
resource "aws_cloudwatch_log_group" "vpc_flow_logs" {
  # checkov:skip=CKV_AWS_158: KMS encryption is not strictly required for VPC flow logs in this demo/project.
  # checkov:skip=CKV_AWS_338: 14 days retention is sufficient for this project.
  name              = "/edutrust/vpc-flow-logs"
  retention_in_days = 14
}

resource "aws_cloudwatch_log_group" "container_logs" {
  # checkov:skip=CKV_AWS_338: 14 days retention is sufficient for this project.
  name              = "/edutrust/container-logs"
  retention_in_days = 14
  kms_key_id        = aws_kms_key.secrets.arn
}

data "aws_iam_policy_document" "vpc_flow_log_assume_role" {
  statement {
    effect  = "Allow"
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["vpc-flow-logs.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "vpc_flow_log" {
  name               = "${var.ec2_instance_name}-vpc-flow-log-role"
  assume_role_policy = data.aws_iam_policy_document.vpc_flow_log_assume_role.json
}

data "aws_iam_policy_document" "vpc_flow_log_policy" {
  statement {
    # checkov:skip=CKV_AWS_109: VPC Flow Logs require permissions securely bound to the role.
    # checkov:skip=CKV_AWS_111: VPC Flow Logs require permissions securely bound to the role.
    # checkov:skip=CKV_AWS_355: VPC Flow Logs require permissions securely bound to the role.
    # checkov:skip=CKV_AWS_356: VPC Flow Logs require permissions securely bound to the role.
    effect = "Allow"
    actions = [
      "logs:CreateLogGroup",
      "logs:CreateLogStream",
      "logs:PutLogEvents",
      "logs:DescribeLogGroups",
      "logs:DescribeLogStreams",
    ]
    resources = ["*"]
  }
}

resource "aws_iam_role_policy" "vpc_flow_log" {
  name   = "${var.ec2_instance_name}-vpc-flow-log-policy"
  role   = aws_iam_role.vpc_flow_log.id
  policy = data.aws_iam_policy_document.vpc_flow_log_policy.json
}

resource "aws_flow_log" "main" {
  log_destination      = aws_cloudwatch_log_group.vpc_flow_logs.arn
  log_destination_type = "cloud-watch-logs"
  traffic_type         = "ALL"
  vpc_id               = aws_vpc.main.id
  iam_role_arn         = aws_iam_role.vpc_flow_log.arn
}

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

resource "aws_iam_role_policy_attachment" "backend_cw_agent" {
  role       = aws_iam_role.backend.name
  policy_arn = "arn:aws:iam::aws:policy/CloudWatchAgentServerPolicy"
}

resource "aws_iam_instance_profile" "backend" {
  name = "${var.ec2_instance_name}-instance-profile"
  role = aws_iam_role.backend.name
}

# --- Encryption ---
data "aws_caller_identity" "current" {}

data "aws_iam_policy_document" "kms_secrets_policy" {
  # checkov:skip=CKV_AWS_109:KMS key policy requires resources=["*"] which means "this key" in context. Actions are explicitly scoped.
  # checkov:skip=CKV_AWS_111:KMS key policy requires resources=["*"] which means "this key" in context. Actions are explicitly scoped.
  # checkov:skip=CKV_AWS_356:KMS key policy requires resources=["*"] which means "this key" in context. Cannot use specific ARN (circular reference).

  # Allow root account administrative access to prevent key lockout
  statement {
    sid    = "AllowRootAdminAccess"
    effect = "Allow"
    principals {
      type        = "AWS"
      identifiers = ["arn:aws:iam::${data.aws_caller_identity.current.account_id}:root"]
    }
    actions = [
      "kms:Create*",
      "kms:Describe*",
      "kms:Enable*",
      "kms:List*",
      "kms:Put*",
      "kms:Update*",
      "kms:Revoke*",
      "kms:Disable*",
      "kms:Get*",
      "kms:Delete*",
      "kms:TagResource",
      "kms:UntagResource",
      "kms:ScheduleKeyDeletion",
      "kms:CancelKeyDeletion",
      "kms:Encrypt",
      "kms:Decrypt",
      "kms:ReEncrypt*",
      "kms:GenerateDataKey*",
    ]
    resources = ["*"]
  }

  # Allow the backend EC2 role to use the key for encrypt/decrypt only
  statement {
    sid    = "AllowBackendRoleUsage"
    effect = "Allow"
    principals {
      type        = "AWS"
      identifiers = [aws_iam_role.backend.arn]
    }
    actions = [
      "kms:Decrypt",
      "kms:Encrypt",
      "kms:GenerateDataKey",
      "kms:DescribeKey",
    ]
    resources = ["*"]
  }

  statement {
    sid    = "AllowCloudWatchLogs"
    effect = "Allow"
    principals {
      type        = "Service"
      identifiers = ["logs.${var.aws_region}.amazonaws.com"]
    }
    actions = [
      "kms:Encrypt*",
      "kms:Decrypt*",
      "kms:ReEncrypt*",
      "kms:GenerateDataKey*",
      "kms:Describe*"
    ]
    resources = ["*"]
    condition {
      test     = "ArnEquals"
      variable = "kms:EncryptionContext:aws:logs:arn"
      values   = ["arn:aws:logs:${var.aws_region}:${data.aws_caller_identity.current.account_id}:log-group:/edutrust/container-logs"]
    }
  }
}

resource "aws_kms_key" "secrets" {
  description             = "KMS key for encrypting SSM parameters and other secrets"
  deletion_window_in_days = 7
  enable_key_rotation     = true
  policy                  = data.aws_iam_policy_document.kms_secrets_policy.json

  tags = {
    Name = "${var.ec2_instance_name}-secrets-key"
  }
}

resource "aws_kms_alias" "secrets" {
  name          = "alias/${var.ec2_instance_name}-secrets"
  target_key_id = aws_kms_key.secrets.key_id
}

# --- Backend Secrets (SSM Parameter) ---
resource "aws_ssm_parameter" "backend_env" {
  name        = "/edutrust/backend/env"
  description = "Environment variables for the backend application"
  type        = "SecureString"
  key_id      = aws_kms_key.secrets.arn
  value       = "INITIAL_SETUP=true" # This will be updated by the CI/CD pipeline or manually

  lifecycle {
    ignore_changes = [value]
  }

  tags = {
    Name = "${var.ec2_instance_name}-env-vars"
  }
}

data "aws_iam_policy_document" "backend_ssm_read" {
  statement {
    effect    = "Allow"
    actions   = ["ssm:GetParameter"]
    resources = [aws_ssm_parameter.backend_env.arn]
  }

  statement {
    effect    = "Allow"
    actions   = ["kms:Decrypt"]
    resources = [aws_kms_key.secrets.arn]
  }

  statement {
    # checkov:skip=CKV_AWS_355:ecr:GetAuthorizationToken does not support resource-level permissions and requires "*"
    effect    = "Allow"
    actions   = ["ecr:GetAuthorizationToken"]
    resources = ["*"]
  }

  statement {
    effect = "Allow"
    actions = [
      "ecr:BatchCheckLayerAvailability",
      "ecr:GetDownloadUrlForLayer",
      "ecr:BatchGetImage"
    ]
    resources = [aws_ecr_repository.backend.arn]
  }

  statement {
    effect = "Allow"
    actions = [
      "kms:Decrypt",
      "kms:DescribeKey"
    ]
    # Allow decrypt for the ECR repository key. 
    # Since it might be the AWS-managed 'aws/ecr' key, we use "*" or the specific ARN if known.
    # To be safe and minimal, we allow it for the ECR repo's encryption context if possible, 
    # but for AWS managed keys, a resource "*" with the specific actions is common.
    resources = ["*"]
    condition {
      test     = "StringLike"
      variable = "kms:ViaService"
      values   = ["ecr.${var.aws_region}.amazonaws.com"]
    }
  }
}

resource "aws_iam_role_policy" "backend_ssm_read" {
  name   = "${var.ec2_instance_name}-ssm-read-policy"
  role   = aws_iam_role.backend.id
  policy = data.aws_iam_policy_document.backend_ssm_read.json
}

# --- Load Balancer Configuration ---

# --- Monitoring: ALB Access Logs ---
data "aws_elb_service_account" "main" {}

resource "aws_s3_bucket" "alb_logs" {
  # checkov:skip=CKV_AWS_18: ALB Access logs don't need access logging themselves.
  # checkov:skip=CKV_AWS_21: Versioning not critical for ALB logs.
  # checkov:skip=CKV_AWS_144: Cross region replication not required.
  # checkov:skip=CKV_AWS_145: KMS encryption is not recommended for ALB logs bucket.
  # checkov:skip=CKV2_AWS_61: Lifecycle config is not required for this demo application.
  # checkov:skip=CKV2_AWS_62: Event notifications are not required for this access log bucket.
  bucket        = "${var.ec2_instance_name}-alb-logs-${data.aws_caller_identity.current.account_id}"
  force_destroy = true
}

resource "aws_s3_bucket_server_side_encryption_configuration" "alb_logs" {
  bucket = aws_s3_bucket.alb_logs.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "alb_logs" {
  bucket                  = aws_s3_bucket.alb_logs.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

data "aws_iam_policy_document" "alb_logs" {
  statement {
    effect = "Allow"
    principals {
      type        = "AWS"
      identifiers = [data.aws_elb_service_account.main.arn]
    }
    actions   = ["s3:PutObject"]
    resources = ["${aws_s3_bucket.alb_logs.arn}/alb/AWSLogs/${data.aws_caller_identity.current.account_id}/*"]
  }
}

resource "aws_s3_bucket_policy" "alb_logs" {
  bucket = aws_s3_bucket.alb_logs.id
  policy = data.aws_iam_policy_document.alb_logs.json
}

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

  access_logs {
    bucket  = aws_s3_bucket.alb_logs.id
    prefix  = "alb"
    enabled = true
  }

  depends_on = [aws_s3_bucket_policy.alb_logs]

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
    path                = "/docs"
    healthy_threshold   = 2
    unhealthy_threshold = 2
    timeout             = 3
    interval            = 10
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

data "aws_ami" "base_ami" {
  most_recent = true
  owners      = ["self"]

  filter {
    name   = "tag:Name"
    values = ["EduTrust-Base-AMI"]
  }
}

resource "aws_launch_template" "backend" {
  name_prefix   = "${var.ec2_instance_name}-lt-"
  image_id      = data.aws_ami.base_ami.id
  instance_type = var.ec2_instance_type
  key_name      = var.ec2_key_name

  iam_instance_profile {
    name = aws_iam_instance_profile.backend.name
  }

  vpc_security_group_ids = [aws_security_group.backend.id]

  ebs_optimized = true

  block_device_mappings {
    device_name = "/dev/sda1"
    ebs {
      volume_size = 20
      encrypted   = true
    }
  }

  metadata_options {
    http_endpoint               = "enabled"
    http_tokens                 = "required"
    http_put_response_hop_limit = 1
  }

  user_data = base64encode(<<-EOF
    #!/bin/bash
    exec > >(tee /var/log/user-data.log|logger -t user-data -s 2>/dev/console) 2>&1
    set -x

    echo "--- Starting Deployment Script ---"

    # Pre-checks: Verify Docker and AWS CLI
    if ! command -v docker &> /dev/null; then
      echo "Error: Docker not installed! Please check the Base AMI."
      exit 1
    fi
    if ! command -v aws &> /dev/null; then
      echo "Error: AWS CLI not installed! Please check the Base AMI."
      exit 1
    fi

    # Environment variables
    REGION="${var.aws_region}"
    ECR_URL="${aws_ecr_repository.backend.repository_url}"
    TARGET_DIR="/home/ubuntu/app"
    mkdir -p $TARGET_DIR

    # ECR Login
    echo "Logging in to ECR..."
    ECR_REGISTRY=$(echo "$ECR_URL" | cut -d'/' -f1)
    MAX_RETRIES=10
    RETRY_COUNT=0
    until aws ecr get-login-password --region $REGION | docker login --username AWS --password-stdin $ECR_REGISTRY; do
      RETRY_COUNT=$((RETRY_COUNT + 1))
      if [ $RETRY_COUNT -ge $MAX_RETRIES ]; then
        echo "Failed to login to ECR after $MAX_RETRIES attempts."
        exit 1
      fi
      echo "ECR login failed. Retrying in 10s... ($RETRY_COUNT/$MAX_RETRIES)"
      sleep 10
    done

    # Retrieve env from SSM
    echo "Retrieving environment variables from SSM..."
    aws ssm get-parameter --name "/edutrust/backend/env" --with-decryption --region $REGION --query "Parameter.Value" --output text > $TARGET_DIR/.env

    # Pull Image with Retry
    IMAGE="$ECR_URL:${var.backend_image_tag}"
    echo "Pulling image: $IMAGE"
    RETRY_COUNT=0
    until docker pull $IMAGE; do
      RETRY_COUNT=$((RETRY_COUNT + 1))
      if [ $RETRY_COUNT -ge $MAX_RETRIES ]; then
        echo "Failed to pull image $IMAGE after $MAX_RETRIES attempts."
        exit 1
      fi
      echo "Docker pull failed. Retrying in 10s... ($RETRY_COUNT/$MAX_RETRIES)"
      sleep 10
    done

    # Validate image exists locally
    if [[ "$(docker images -q $IMAGE 2> /dev/null)" == "" ]]; then
      echo "Error: Image $IMAGE not found after pull!"
      exit 1
    fi
    echo "Image pulled successfully."

    # Run Container
    echo "Starting container..."
    docker stop aws-fcj-backend || true
    docker rm aws-fcj-backend || true
    docker run -d --name aws-fcj-backend \
      --restart unless-stopped \
      -p ${var.backend_port}:${var.backend_port} \
      --env-file $TARGET_DIR/.env \
      $IMAGE

    # Post-checks: Health check loop
    echo "Waiting for application to be healthy..."
    HEALTH_CHECK_URL="http://localhost:${var.backend_port}/docs"
    MAX_HEALTH_RETRIES=15
    HEALTH_RETRY=0
    until curl -sf "$HEALTH_CHECK_URL" > /dev/null; do
      HEALTH_RETRY=$((HEALTH_RETRY + 1))
      if [ $HEALTH_RETRY -ge $MAX_HEALTH_RETRIES ]; then
        echo "Error: Application failed to start after $(($MAX_HEALTH_RETRIES * 10))s."
        docker logs aws-fcj-backend
        exit 1
      fi
      echo "Waiting for app at $HEALTH_CHECK_URL... ($HEALTH_RETRY/$MAX_HEALTH_RETRIES)"
      sleep 10
    done

    echo "--- SUCCESS: Container is running and healthy ---"
    curl -i "$HEALTH_CHECK_URL"

    # CloudWatch Agent Configuration
    mkdir -p /opt/aws/amazon-cloudwatch-agent/etc/
    cat > /opt/aws/amazon-cloudwatch-agent/etc/amazon-cloudwatch-agent.json << 'CW_EOF'
{
  "metrics": {
    "namespace": "EduTrust/Core",
    "metrics_collected": {
      "cpu": {
        "measurement": ["cpu_usage_active"],
        "totalcpu": true
      },
      "mem": {
        "measurement": ["mem_used_percent"]
      },
      "disk": {
        "resources": ["/"],
        "measurement": ["disk_used_percent"]
      },
      "net": {
        "resources": ["docker*"],
        "measurement": ["bytes_recv", "bytes_sent"]
      }
    }
  },
  "logs": {
    "logs_collected": {
      "files": {
        "collect_list": [
          {
            "file_path": "/var/lib/docker/containers/*/*.log",
            "log_group_name": "${aws_cloudwatch_log_group.container_logs.name}",
            "log_stream_name": "{instance_id}"
          }
        ]
      }
    }
  }
}
CW_EOF
    sudo /opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent-ctl -a fetch-config -m ec2 -s -c file:/opt/aws/amazon-cloudwatch-agent/etc/amazon-cloudwatch-agent.json
  EOF
  )

  tag_specifications {
    resource_type = "instance"
    tags = {
      Name = "${var.ec2_instance_name}-asg-node"
    }
  }

  lifecycle {
    create_before_destroy = true
  }
}

resource "aws_autoscaling_group" "backend" {
  name                = "${var.ec2_instance_name}-asg"
  desired_capacity    = var.asg_desired_capacity
  max_size            = var.asg_max_size
  min_size            = var.asg_min_size
  target_group_arns   = [aws_lb_target_group.backend.arn]
  vpc_zone_identifier = [aws_subnet.private_1a.id, aws_subnet.private_1c.id]

  launch_template {
    id      = aws_launch_template.backend.id
    version = "$Latest"
  }

  health_check_type         = "EC2"
  health_check_grace_period = 300
  wait_for_capacity_timeout = "0"

  instance_refresh {
    strategy = "Rolling"
    preferences {
      min_healthy_percentage = 50
      instance_warmup        = 60
    }
  }

  tag {
    key                 = "Name"
    value               = "${var.ec2_instance_name}-asg"
    propagate_at_launch = true
  }
}

resource "aws_ecr_repository" "backend" {
  name                 = var.ecr_repository_name
  image_tag_mutability = var.ecr_tag_immutable ? "IMMUTABLE" : "MUTABLE"

  encryption_configuration {
    encryption_type = "KMS"
    kms_key         = aws_kms_key.secrets.arn
  }

  image_scanning_configuration {
    scan_on_push = true
  }
}
