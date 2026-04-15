# --- VPC Endpoints ---

# S3 Gateway Endpoint (Free and critical for ECR)
resource "aws_vpc_endpoint" "s3" {
  vpc_id            = aws_vpc.main.id
  service_name      = "com.amazonaws.${var.aws_region}.s3"
  vpc_endpoint_type = "Gateway"
  route_table_ids   = [aws_route_table.private_1a.id, aws_route_table.private_1c.id]

  tags = { Name = "s3-endpoint" }
}
# DynamoDB Gateway Endpoint (Free, improves DynamoDB access from private subnets)
resource "aws_vpc_endpoint" "dynamodb" {
  vpc_id            = aws_vpc.main.id
  service_name      = "com.amazonaws.${var.aws_region}.dynamodb"
  vpc_endpoint_type = "Gateway"
  route_table_ids   = [aws_route_table.private_1a.id, aws_route_table.private_1c.id]

  tags = { Name = "dynamodb-endpoint" }
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
locals {
  frontend_distribution_arn = length(trimspace(var.frontend_cloudfront_distribution_id)) > 0 ? "arn:aws:cloudfront::${data.aws_caller_identity.current.account_id}:distribution/${trimspace(var.frontend_cloudfront_distribution_id)}" : ""
}
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
}
data "aws_iam_policy_document" "kms_dynamodb_policy" {
  # checkov:skip=CKV_AWS_109:KMS key policy requires resources=["*"] which means "this key" in context. Actions are explicitly scoped.
  # checkov:skip=CKV_AWS_111:KMS key policy requires resources=["*"] which means "this key" in context. Actions are explicitly scoped.
  # checkov:skip=CKV_AWS_356:KMS key policy requires resources=["*"] which means "this key" in context. Cannot use specific ARN (circular reference).

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

  statement {
    sid    = "AllowDynamoDBServiceUsage"
    effect = "Allow"
    principals {
      type        = "Service"
      identifiers = ["dynamodb.amazonaws.com"]
    }
    actions = [
      "kms:Encrypt",
      "kms:Decrypt",
      "kms:ReEncrypt*",
      "kms:GenerateDataKey*",
      "kms:DescribeKey",
      "kms:CreateGrant",
    ]
    resources = ["*"]
    condition {
      test     = "StringEquals"
      variable = "kms:CallerAccount"
      values   = [data.aws_caller_identity.current.account_id]
    }
    condition {
      test     = "StringEquals"
      variable = "kms:ViaService"
      values   = ["dynamodb.${var.aws_region}.amazonaws.com"]
    }
  }

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
      "kms:CreateGrant",
    ]
    resources = ["*"]
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
resource "aws_kms_key" "dynamodb" {
  description             = "KMS key for encrypting DynamoDB tables"
  deletion_window_in_days = 7
  enable_key_rotation     = true
  policy                  = data.aws_iam_policy_document.kms_dynamodb_policy.json

  tags = {
    Name = "${var.ec2_instance_name}-dynamodb-key"
  }
}
resource "aws_kms_alias" "dynamodb" {
  name          = "alias/${var.ec2_instance_name}-dynamodb"
  target_key_id = aws_kms_key.dynamodb.key_id
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
    effect  = "Allow"
    actions = ["s3:ListBucket"]
    resources = [
      aws_s3_bucket.camera_detect.arn,
    ]
  }

  statement {
    effect = "Allow"
    actions = [
      "s3:GetObject",
      "s3:PutObject",
      "s3:DeleteObject",
    ]
    resources = [
      "${aws_s3_bucket.camera_detect.arn}/*",
    ]
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
}
resource "aws_iam_role_policy" "backend_ssm_read" {
  name   = "${var.ec2_instance_name}-ssm-read-policy"
  role   = aws_iam_role.backend.id
  policy = data.aws_iam_policy_document.backend_ssm_read.json
}
locals {
  api_zone_id = length(trimspace(var.route53_zone_id)) > 0 ? trimspace(var.route53_zone_id) : try(data.aws_route53_zone.api_parent[0].zone_id, "")
}
locals {
  https_certificate_arn = length(trimspace(var.certificate_arn)) > 0 ? trimspace(var.certificate_arn) : (
    var.enable_api_custom_domain ? aws_acm_certificate_validation.api[0].certificate_arn : ""
  )
}
