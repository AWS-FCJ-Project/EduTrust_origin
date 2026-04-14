resource "aws_cognito_user_pool" "backend" {
  name = "${var.ec2_instance_name}-user-pool"

  username_attributes      = ["email"]
  auto_verified_attributes = ["email"]
  mfa_configuration        = "OFF"

  lifecycle {
    prevent_destroy = true
  }

  admin_create_user_config {
    allow_admin_create_user_only = true
  }

  password_policy {
    minimum_length                   = 8
    require_lowercase                = true
    require_numbers                  = true
    require_symbols                  = true
    require_uppercase                = true
    temporary_password_validity_days = 7
  }

  account_recovery_setting {
    recovery_mechanism {
      name     = "verified_email"
      priority = 1
    }
  }

  verification_message_template {
    default_email_option = "CONFIRM_WITH_CODE"
  }
}
resource "aws_cognito_user_pool_client" "backend" {
  name         = "${var.ec2_instance_name}-app-client"
  user_pool_id = aws_cognito_user_pool.backend.id

  lifecycle {
    prevent_destroy = true
  }

  generate_secret               = false
  prevent_user_existence_errors = "ENABLED"
  enable_token_revocation       = true
  explicit_auth_flows           = ["ALLOW_REFRESH_TOKEN_AUTH", "ALLOW_USER_PASSWORD_AUTH"]
  access_token_validity         = 24
  id_token_validity             = 24
  refresh_token_validity        = 30

  token_validity_units {
    access_token  = "hours"
    id_token      = "hours"
    refresh_token = "days"
  }
}
resource "aws_cognito_user_group" "admin" {
  name         = "admin"
  user_pool_id = aws_cognito_user_pool.backend.id
}
resource "aws_cognito_user_group" "teacher" {
  name         = "teacher"
  user_pool_id = aws_cognito_user_pool.backend.id
}
resource "aws_cognito_user_group" "student" {
  name         = "student"
  user_pool_id = aws_cognito_user_pool.backend.id
}
data "aws_iam_policy_document" "backend_cognito_access" {
  statement {
    effect = "Allow"
    actions = [
      "cognito-idp:AdminAddUserToGroup",
      "cognito-idp:AdminCreateUser",
      "cognito-idp:AdminDeleteUser",
      "cognito-idp:AdminGetUser",
      "cognito-idp:AdminRemoveUserFromGroup",
      "cognito-idp:AdminSetUserPassword",
      "cognito-idp:AdminUpdateUserAttributes",
    ]
    resources = [aws_cognito_user_pool.backend.arn]
  }

  statement {
    # checkov:skip=CKV_AWS_355:Cognito public auth APIs do not support resource-level permissions for every action and require "*".
    effect = "Allow"
    actions = [
      "cognito-idp:ConfirmForgotPassword",
      "cognito-idp:ForgotPassword",
      "cognito-idp:InitiateAuth",
    ]
    resources = ["*"]
  }
}
resource "aws_iam_role_policy" "backend_cognito_access" {
  name   = "${var.ec2_instance_name}-cognito-access-policy"
  role   = aws_iam_role.backend.id
  policy = data.aws_iam_policy_document.backend_cognito_access.json
}
# --- App storage: Camera cheating-detection logs ---
resource "aws_s3_bucket" "camera_detect" {
  # checkov:skip=CKV_AWS_18: Access logging is optional for this demo bucket.
  # checkov:skip=CKV_AWS_144: Cross region replication not required.
  # checkov:skip=CKV_AWS_145: SSE-S3 (AES256) is sufficient for this demo bucket; SSE-KMS can be enabled later if required.
  # checkov:skip=CKV2_AWS_61: Lifecycle config is not required initially.
  # checkov:skip=CKV2_AWS_62: Event notifications are not required initially.
  bucket = var.camera_detect_bucket_name

  tags = {
    Name = "${var.ec2_instance_name}-camera-detect"
  }
}
resource "aws_s3_bucket_ownership_controls" "camera_detect" {
  bucket = aws_s3_bucket.camera_detect.id
  rule {
    object_ownership = "BucketOwnerEnforced"
  }
}
resource "aws_s3_bucket_versioning" "camera_detect" {
  bucket = aws_s3_bucket.camera_detect.id
  versioning_configuration {
    status = "Enabled"
  }
}
resource "aws_s3_bucket_server_side_encryption_configuration" "camera_detect" {
  bucket = aws_s3_bucket.camera_detect.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}
resource "aws_s3_bucket_public_access_block" "camera_detect" {
  bucket                  = aws_s3_bucket.camera_detect.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true

  depends_on = [aws_s3_bucket_ownership_controls.camera_detect]
}
resource "aws_s3_bucket_lifecycle_configuration" "camera_detect" {
  bucket = aws_s3_bucket.camera_detect.id

  rule {
    id     = "transition-to-glacier"
    status = "Enabled"

    transition {
      days          = 90
      storage_class = "GLACIER"
    }

    expiration {
      days = 365
    }
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
resource "aws_ecr_lifecycle_policy" "backend" {
  repository = aws_ecr_repository.backend.name

  policy = jsonencode({
    rules = [
      {
        rulePriority = 1
        description  = "Keep the most recent 30 images"
        selection = {
          tagStatus   = "any"
          countType   = "imageCountMoreThan"
          countNumber = 30
        }
        action = {
          type = "expire"
        }
      }
    ]
  })
}
