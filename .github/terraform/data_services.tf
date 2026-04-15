# --- End Network Configuration ---

# --- ElastiCache Redis ---
resource "aws_elasticache_subnet_group" "redis" {
  name       = "${var.ec2_instance_name}-redis-subnet-group"
  subnet_ids = [aws_subnet.private_1a.id, aws_subnet.private_1c.id]

  tags = { Name = "${var.ec2_instance_name}-redis-subnet-group" }
}
resource "aws_security_group" "redis" {
  name        = "${var.ec2_instance_name}-redis-sg"
  description = "Security group for ElastiCache Redis"
  vpc_id      = aws_vpc.main.id

  ingress {
    description     = "Redis from backend EC2"
    from_port       = 6379
    to_port         = 6379
    protocol        = "tcp"
    security_groups = [aws_security_group.backend.id]
  }

  egress {
    description = "Allow all outbound"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = { Name = "${var.ec2_instance_name}-redis-sg" }
}
resource "aws_elasticache_cluster" "redis" {
  cluster_id           = "${var.ec2_instance_name}-redis"
  engine               = "redis"
  engine_version       = var.redis_engine_version
  node_type            = var.redis_node_type
  num_cache_nodes      = 1
  parameter_group_name = "default.redis7"
  port                 = 6379
  subnet_group_name    = aws_elasticache_subnet_group.redis.name
  security_group_ids   = [aws_security_group.redis.id]

  # Auto minor version upgrade
  auto_minor_version_upgrade = true

  # Maintenance window
  maintenance_window = "mon:09:00-mon:11:00"

  # Snapshot retention: 1 day minimum required by CKV_AWS_134
  # For dev env this may be short; for prod use 7 days
  snapshot_retention_limit = 1

  tags = {
    Name = "${var.ec2_instance_name}-redis"
  }
}
# --- DynamoDB Tables (Phase 02 Migration) ---
resource "aws_dynamodb_table" "users" {
  name         = "${var.dynamodb_table_prefix}-users"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "user_id"

  server_side_encryption {
    enabled     = true
    kms_key_arn = aws_kms_key.dynamodb.arn
  }

  point_in_time_recovery {
    enabled = true
  }

  attribute {
    name = "user_id"
    type = "S"
  }
  attribute {
    name = "email"
    type = "S"
  }
  attribute {
    name = "role"
    type = "S"
  }
  attribute {
    name = "class_id"
    type = "S"
  }

  global_secondary_index {
    name            = "email-index"
    hash_key        = "email"
    projection_type = "ALL"
  }

  global_secondary_index {
    name            = "role-index"
    hash_key        = "role"
    projection_type = "ALL"
  }

  global_secondary_index {
    name            = "class-id-index"
    hash_key        = "class_id"
    projection_type = "ALL"
  }

  tags = {
    Name = "${var.ec2_instance_name}-dynamodb-users"
  }
}
resource "aws_dynamodb_table" "classes" {
  name         = "${var.dynamodb_table_prefix}-classes"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "class_id"

  server_side_encryption {
    enabled     = true
    kms_key_arn = aws_kms_key.dynamodb.arn
  }

  point_in_time_recovery {
    enabled = true
  }

  attribute {
    name = "class_id"
    type = "S"
  }
  attribute {
    name = "lookup_key"
    type = "S"
  }
  attribute {
    name = "homeroom_teacher_id"
    type = "S"
  }

  global_secondary_index {
    name            = "class-lookup-index"
    hash_key        = "lookup_key"
    projection_type = "ALL"
  }

  global_secondary_index {
    name            = "homeroom-teacher-index"
    hash_key        = "homeroom_teacher_id"
    projection_type = "ALL"
  }

  tags = {
    Name = "${var.ec2_instance_name}-dynamodb-classes"
  }
}
resource "aws_dynamodb_table" "class_teacher_assignments" {
  name         = "${var.dynamodb_table_prefix}-class_teacher_assignments"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "teacher_id"
  range_key    = "assignment_key"

  server_side_encryption {
    enabled     = true
    kms_key_arn = aws_kms_key.dynamodb.arn
  }

  point_in_time_recovery {
    enabled = true
  }

  attribute {
    name = "teacher_id"
    type = "S"
  }
  attribute {
    name = "assignment_key"
    type = "S"
  }

  tags = {
    Name = "${var.ec2_instance_name}-dynamodb-class-teacher-assignments"
  }
}
resource "aws_dynamodb_table" "exams" {
  name         = "${var.dynamodb_table_prefix}-exams"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "exam_id"

  server_side_encryption {
    enabled     = true
    kms_key_arn = aws_kms_key.dynamodb.arn
  }

  point_in_time_recovery {
    enabled = true
  }

  attribute {
    name = "exam_id"
    type = "S"
  }
  attribute {
    name = "teacher_id"
    type = "S"
  }
  attribute {
    name = "class_id"
    type = "S"
  }
  attribute {
    name = "start_time"
    type = "S"
  }

  global_secondary_index {
    name            = "teacher-index"
    hash_key        = "teacher_id"
    range_key       = "start_time"
    projection_type = "ALL"
  }

  global_secondary_index {
    name            = "class-index"
    hash_key        = "class_id"
    range_key       = "start_time"
    projection_type = "ALL"
  }

  tags = {
    Name = "${var.ec2_instance_name}-dynamodb-exams"
  }
}
resource "aws_dynamodb_table" "submissions" {
  name         = "${var.dynamodb_table_prefix}-submissions"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "exam_id"
  range_key    = "student_id"

  server_side_encryption {
    enabled     = true
    kms_key_arn = aws_kms_key.dynamodb.arn
  }

  point_in_time_recovery {
    enabled = true
  }

  attribute {
    name = "exam_id"
    type = "S"
  }
  attribute {
    name = "student_id"
    type = "S"
  }
  attribute {
    name = "submitted_at"
    type = "S"
  }

  global_secondary_index {
    name            = "student-index"
    hash_key        = "student_id"
    range_key       = "submitted_at"
    projection_type = "ALL"
  }

  tags = {
    Name = "${var.ec2_instance_name}-dynamodb-submissions"
  }
}
resource "aws_dynamodb_table" "violations" {
  name         = "${var.dynamodb_table_prefix}-violations"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "exam_id"
  range_key    = "student_id"

  server_side_encryption {
    enabled     = true
    kms_key_arn = aws_kms_key.dynamodb.arn
  }

  point_in_time_recovery {
    enabled = true
  }

  attribute {
    name = "exam_id"
    type = "S"
  }
  attribute {
    name = "student_id"
    type = "S"
  }
  attribute {
    name = "class_id"
    type = "S"
  }
  attribute {
    name = "violation_time"
    type = "S"
  }

  global_secondary_index {
    name            = "class-time-index"
    hash_key        = "class_id"
    range_key       = "violation_time"
    projection_type = "ALL"
  }

  tags = {
    Name = "${var.ec2_instance_name}-dynamodb-violations"
  }
}
resource "aws_dynamodb_table" "conversations" {
  name         = "${var.dynamodb_table_prefix}-conversations"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "conversation_id"

  server_side_encryption {
    enabled     = true
    kms_key_arn = aws_kms_key.dynamodb.arn
  }

  point_in_time_recovery {
    enabled = true
  }

  attribute {
    name = "conversation_id"
    type = "S"
  }
  attribute {
    name = "user_id"
    type = "S"
  }
  attribute {
    name = "updated_at"
    type = "S"
  }

  global_secondary_index {
    name            = "user-updated-index"
    hash_key        = "user_id"
    range_key       = "updated_at"
    projection_type = "ALL"
  }

  tags = {
    Name = "${var.ec2_instance_name}-dynamodb-conversations"
  }
}
resource "aws_dynamodb_table" "otps" {
  name         = "${var.dynamodb_table_prefix}-otps"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "otp_key"

  server_side_encryption {
    enabled     = true
    kms_key_arn = aws_kms_key.dynamodb.arn
  }

  point_in_time_recovery {
    enabled = true
  }

  attribute {
    name = "otp_key"
    type = "S"
  }

  ttl {
    attribute_name = "expire_at_epoch"
    enabled        = true
  }

  tags = {
    Name = "${var.ec2_instance_name}-dynamodb-otps"
  }
}
# --- DynamoDB Permissions (Phase 02 Migration) ---
data "aws_iam_policy_document" "backend_dynamodb" {
  # Allow all DynamoDB operations on the app tables
  # checkov:skip=CKV_AWS_109: Table-level ARNs are used, action set is intentionally broad for migration phase flexibility.
  statement {
    effect = "Allow"
    actions = [
      "dynamodb:GetItem",
      "dynamodb:PutItem",
      "dynamodb:UpdateItem",
      "dynamodb:DeleteItem",
      "dynamodb:Query",
      "dynamodb:Scan",
      "dynamodb:BatchWriteItem",
      "dynamodb:BatchGetItem",
      "dynamodb:TransactWriteItems",
      "dynamodb:DescribeTable",
      "dynamodb:ListTables",
    ]
    resources = [
      aws_dynamodb_table.users.arn,
      "${aws_dynamodb_table.users.arn}/index/*",
      aws_dynamodb_table.classes.arn,
      "${aws_dynamodb_table.classes.arn}/index/*",
      aws_dynamodb_table.class_teacher_assignments.arn,
      "${aws_dynamodb_table.class_teacher_assignments.arn}/index/*",
      aws_dynamodb_table.exams.arn,
      "${aws_dynamodb_table.exams.arn}/index/*",
      aws_dynamodb_table.submissions.arn,
      "${aws_dynamodb_table.submissions.arn}/index/*",
      aws_dynamodb_table.violations.arn,
      "${aws_dynamodb_table.violations.arn}/index/*",
      aws_dynamodb_table.conversations.arn,
      "${aws_dynamodb_table.conversations.arn}/index/*",
      aws_dynamodb_table.otps.arn,
      "${aws_dynamodb_table.otps.arn}/index/*",
    ]
  }
}
resource "aws_iam_role_policy" "backend_dynamodb" {
  name   = "${var.ec2_instance_name}-dynamodb-policy"
  role   = aws_iam_role.backend.id
  policy = data.aws_iam_policy_document.backend_dynamodb.json
}
