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
    path                = "/health"
    healthy_threshold   = 2
    unhealthy_threshold = 2
    timeout             = 5
    interval            = 30
    matcher             = "200"
  }
}
data "aws_route53_zone" "api_parent" {
  count        = var.enable_api_custom_domain && length(trimspace(var.route53_zone_id)) == 0 ? 1 : 0
  name         = trimspace(var.route53_zone_name)
  private_zone = false
}
resource "aws_acm_certificate" "api" {
  count             = var.enable_api_custom_domain && length(trimspace(var.certificate_arn)) == 0 ? 1 : 0
  domain_name       = trimspace(var.api_domain_name)
  validation_method = "DNS"

  lifecycle {
    create_before_destroy = true
  }
}
resource "aws_route53_record" "api_cert_validation" {
  for_each = var.enable_api_custom_domain && length(trimspace(var.certificate_arn)) == 0 ? {
    for dvo in aws_acm_certificate.api[0].domain_validation_options :
    dvo.domain_name => {
      name  = dvo.resource_record_name
      type  = dvo.resource_record_type
      value = dvo.resource_record_value
    }
  } : {}

  zone_id = local.api_zone_id
  name    = each.value.name
  type    = each.value.type
  ttl     = 60
  records = [each.value.value]
}
resource "aws_acm_certificate_validation" "api" {
  count           = var.enable_api_custom_domain && length(trimspace(var.certificate_arn)) == 0 ? 1 : 0
  certificate_arn = aws_acm_certificate.api[0].arn

  validation_record_fqdns = [for r in aws_route53_record.api_cert_validation : r.fqdn]
}
resource "aws_route53_record" "api_alias" {
  count   = var.enable_api_custom_domain ? 1 : 0
  zone_id = local.api_zone_id
  name    = trimspace(var.api_domain_name)
  type    = "A"

  alias {
    name                   = aws_lb.main.dns_name
    zone_id                = aws_lb.main.zone_id
    evaluate_target_health = true
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
  certificate_arn   = local.https_certificate_arn

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
    cidr_blocks = [aws_subnet.private_1a.cidr_block, aws_subnet.private_1c.cidr_block]
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
  # checkov:skip=CKV_AWS_341: IMDS hop limit is set to 2 intentionally so Docker containers can reach IMDSv2 and retrieve IAM role credentials. IMDSv2 is required and hop limit kept minimal.
  name_prefix   = "${var.ec2_instance_name}-lt-"
  image_id      = data.aws_ami.base_ami.id
  instance_type = var.ec2_instance_type

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
    http_endpoint = "enabled"
    http_tokens   = "required"
    # Docker containers often need hop_limit >= 2 to reach IMDSv2 and fetch IAM role credentials.
    http_put_response_hop_limit = 2
  }

  # NOTE:
  # 1. This repo is often edited on Windows, which can introduce CRLF (\r\n). If that
  #    reaches EC2 user-data, the shebang can become "/bin/bash\r" and cloud-init
  #    will fail to execute the script. We strip '\r' defensively.
  # 2. The script is responsible for bootstrapping the instance (Docker, ECR login,
  #    pull/run container). If it doesn't run, ALB health checks will fail and ASG
  #    instance refreshes will stall.
  user_data = base64encode(replace((<<EOF
#!/usr/bin/env bash
set -euo pipefail

# Persist user-data logs for debugging (SSM into instance -> read this file).
exec > >(tee -a /var/log/user-data.log) 2>&1
set -x

retry() {
  local max=8
  local delay=5
  local n=0
  until "$@"; do
    n=$((n + 1))
    if [ "$n" -ge "$max" ]; then
      echo "Command failed after $${n} attempts: $*"
      return 1
    fi
    echo "Retry $${n}/$${max} (sleep $${delay}s): $*"
    sleep "$delay"
    delay=$((delay * 2))
  done
}

# Environment variables
REGION="${var.aws_region}"
ECR_URL="${aws_ecr_repository.backend.repository_url}"
TARGET_DIR="/opt/edutrust"
mkdir -p "$TARGET_DIR"

echo "Bootstrapping instance..."
echo "REGION=$REGION"
echo "ECR_URL=$ECR_URL"

if ! command -v aws >/dev/null 2>&1; then
  echo "AWS CLI not found; installing..."
  if command -v apt-get >/dev/null 2>&1; then
    export DEBIAN_FRONTEND=noninteractive
    apt-get update
    apt-get install -y --no-install-recommends awscli ca-certificates curl
  elif command -v yum >/dev/null 2>&1; then
    yum install -y awscli curl ca-certificates
  elif command -v dnf >/dev/null 2>&1; then
    dnf install -y awscli curl ca-certificates
  else
    echo "No supported package manager found to install AWS CLI" >&2
    exit 1
  fi
fi

if ! command -v docker >/dev/null 2>&1; then
  echo "Docker not found; installing..."
  if command -v apt-get >/dev/null 2>&1; then
    export DEBIAN_FRONTEND=noninteractive
    apt-get update
    apt-get install -y --no-install-recommends docker.io
  elif command -v yum >/dev/null 2>&1; then
    yum install -y docker
  elif command -v dnf >/dev/null 2>&1; then
    dnf install -y docker
  else
    echo "No supported package manager found to install Docker" >&2
    exit 1
  fi
fi

echo "Ensuring Docker is running..."
systemctl enable --now docker || true
retry systemctl is-active --quiet docker

# ECR Login & Image Pull
ECR_REGISTRY=$(echo "$ECR_URL" | cut -d'/' -f1)
retry bash -lc "aws ecr get-login-password --region \"$REGION\" | docker login --username AWS --password-stdin \"$ECR_REGISTRY\""

# Retrieve env from SSM
retry bash -lc "aws ssm get-parameter --name \"/edutrust/backend/env\" --with-decryption --region \"$REGION\" --query \"Parameter.Value\" --output text > \"$TARGET_DIR/.env\""

# Run Container
IMAGE="$ECR_URL:${var.backend_image_tag}"
echo "Pulling image: $IMAGE"
retry docker pull "$IMAGE"
docker stop aws-fcj-backend || true
docker rm aws-fcj-backend || true
docker run -d --name aws-fcj-backend \
  --restart unless-stopped \
  -p ${var.backend_port}:${var.backend_port} \
  --env-file "$TARGET_DIR/.env" \
  "$IMAGE"

# CloudWatch Agent Configuration (optional)
if [ -x /opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent-ctl ]; then
  mkdir -p /opt/aws/amazon-cloudwatch-agent/etc/
  cat > /opt/aws/amazon-cloudwatch-agent/etc/amazon-cloudwatch-agent.json << 'CW_EOF'
{
  "metrics": {
    "namespace": "EduTrust/Container",
    "metrics_collected": {
      "net": {
        "resources": ["docker*"],
        "measurement": ["bytes_recv", "bytes_sent", "packets_recv", "packets_sent"]
      }
    }
  },
  "logs": {
    "logs_collected": {
      "files": {
        "collect_list": [
          {
            "file_path": "/var/log/user-data.log",
            "log_group_name": "/edutrust/user-data",
            "log_stream_name": "{instance_id}"
          },
          {
            "file_path": "/var/log/cloud-init-output.log",
            "log_group_name": "/edutrust/cloud-init",
            "log_stream_name": "{instance_id}"
          },
          {
            "file_path": "/var/lib/docker/containers/*/*.log",
            "log_group_name": "/edutrust/container-logs",
            "log_stream_name": "{instance_id}"
          }
        ]
      }
    }
  }
}
CW_EOF
  /opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent-ctl -a fetch-config -m ec2 -s -c file:/opt/aws/amazon-cloudwatch-agent/etc/amazon-cloudwatch-agent.json
fi
EOF
  ), "\r", ""))

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

  # Use ALB Target Group health checks to decide instance health (better signal than EC2 status checks).
  health_check_type = "ELB"
  # Give instances time to pull the container image + start the app before ASG considers them unhealthy.
  health_check_grace_period = 240
  wait_for_capacity_timeout = "0"

  instance_refresh {
    strategy = "Rolling"
    preferences {
      min_healthy_percentage = 50
      instance_warmup        = 90
    }
  }

  tag {
    key                 = "Name"
    value               = "${var.ec2_instance_name}-asg"
    propagate_at_launch = true
  }
}
