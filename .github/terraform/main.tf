terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "6.34.0"
    }
  }
}

provider "aws" {
  region     = var.aws_region
  access_key = var.aws_access_key
  secret_key = var.aws_secret_key
}

# ─── Tự động tìm Default VPC (không cần biết VPC ID) ─────────────
data "aws_vpc" "default" {
  default = true  # Lấy Default VPC mà AWS tạo sẵn
}

# Lấy tất cả subnet có trong Default VPC
data "aws_subnets" "default" {
  filter {
    name   = "vpc-id"
    values = [data.aws_vpc.default.id]
  }
}

# ─── EC2 — Backend Server ─────────────────────────────────────────
resource "aws_instance" "backend" {
  ami           = var.ec2_ami_id
  instance_type = var.ec2_instance_type
  vpc_security_group_ids = [aws_security_group.backend.id]

  tags = {
    Name = var.ec2_instance_name
  }
}

# ─── Security Group cho EC2 ───────────────────────────────────────
resource "aws_security_group" "backend" {
  name        = "aws-fcj-backend-sg"
  description = "Security group for EC2 backend"
  vpc_id      = data.aws_vpc.default.id

  # HTTP từ ngoài vào
  ingress {
    from_port   = 8000
    to_port     = 8000
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # SSH
  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # Cho phép EC2 nói chuyện với Redis (nội bộ VPC)
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "aws-fcj-backend-sg"
  }
}

# ─── Security Group cho Redis ─────────────────────────────────────
resource "aws_security_group" "redis" {
  name        = "aws-fcj-redis-sg"
  description = "Allow EC2 to connect to Redis"
  vpc_id      = data.aws_vpc.default.id

  # Chỉ cho phép EC2 Security Group kết nối vào port 6379
  ingress {
    from_port       = 6379
    to_port         = 6379
    protocol        = "tcp"
    security_groups = [aws_security_group.backend.id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "aws-fcj-redis-sg"
  }
}

# ─── ElastiCache — Subnet Group (cùng VPC với EC2) ───────────────
resource "aws_elasticache_subnet_group" "redis" {
  name       = "aws-fcj-redis-subnet-group"
  subnet_ids = data.aws_subnets.default.ids  # Dùng subnets của Default VPC

  tags = {
    Name = "aws-fcj-redis-subnet-group"
  }
}

# ─── ElastiCache — Redis Cluster ──────────────────────────────────
resource "aws_elasticache_cluster" "redis" {
  cluster_id           = "aws-fcj-redis"
  engine               = "redis"
  node_type            = "cache.t3.micro"
  num_cache_nodes      = 1
  parameter_group_name = "default.redis7"
  engine_version       = "7.1"
  port                 = 6379

  # Đặt trong cùng VPC và dùng Security Group riêng
  subnet_group_name  = aws_elasticache_subnet_group.redis.name
  security_group_ids = [aws_security_group.redis.id]

  tags = {
    Name        = "aws-fcj-redis"
    Environment = "production"
  }
}

# ─── S3 — File Uploads ────────────────────────────────────────────
resource "aws_s3_bucket" "uploads" {
  bucket = var.s3_bucket_name

  tags = {
    Name        = "aws-fcj-uploads"
    Environment = "production"
  }
}

# Chặn toàn bộ public access (file chỉ truy cập qua presigned URL)
resource "aws_s3_bucket_public_access_block" "uploads" {
  bucket = aws_s3_bucket.uploads.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# Tự động xóa file cũ hơn 30 ngày
resource "aws_s3_bucket_lifecycle_configuration" "uploads" {
  bucket = aws_s3_bucket.uploads.id

  rule {
    id     = "expire-old-uploads"
    status = "Enabled"

    filter {
      prefix = "uploads/"
    }

    expiration {
      days = 30
    }
  }
}

# ─── IAM — Policy cho Backend truy cập S3 ─────────────────────────
resource "aws_iam_user" "backend" {
  name = "aws-fcj-backend-user"

  tags = {
    Name = "aws-fcj-backend"
  }
}

resource "aws_iam_policy" "s3_upload" {
  name        = "aws-fcj-s3-upload-policy"
  description = "Allow backend to upload/download/delete files in S3"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:PutObject",
          "s3:GetObject",
          "s3:DeleteObject",
        ]
        Resource = "${aws_s3_bucket.uploads.arn}/*"
      },
      {
        Effect   = "Allow"
        Action   = ["s3:ListBucket"]
        Resource = aws_s3_bucket.uploads.arn
      }
    ]
  })
}

resource "aws_iam_user_policy_attachment" "backend_s3" {
  user       = aws_iam_user.backend.name
  policy_arn = aws_iam_policy.s3_upload.arn
}

resource "aws_iam_access_key" "backend" {
  user = aws_iam_user.backend.name
}
