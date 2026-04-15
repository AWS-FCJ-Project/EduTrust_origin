# --- Monitoring: VPC Flow Logs ---
resource "aws_cloudwatch_log_group" "vpc_flow_logs" {
  # checkov:skip=CKV_AWS_158: KMS encryption is not strictly required for VPC flow logs in this demo/project.
  # checkov:skip=CKV_AWS_338: 14 days retention is sufficient for this project.
  name              = "/edutrust/vpc-flow-logs"
  retention_in_days = 14
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
  bucket = "${var.ec2_instance_name}-alb-logs-${data.aws_caller_identity.current.account_id}"
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
# --- Frontend protection: WAF for Amplify (CloudFront) ---
resource "aws_wafv2_web_acl" "frontend" {
  count    = var.enable_frontend_waf ? 1 : 0
  provider = aws.us_east_1

  name  = "${var.ec2_instance_name}-frontend-waf"
  scope = "CLOUDFRONT"

  default_action {
    allow {}
  }

  visibility_config {
    cloudwatch_metrics_enabled = true
    metric_name                = "${var.ec2_instance_name}-frontend-waf"
    sampled_requests_enabled   = true
  }

  dynamic "rule" {
    for_each = var.enable_frontend_waf && length(var.frontend_waf_denylist_ips) > 0 ? [1] : []
    content {
      name     = "IPDenyList"
      priority = 10

      action {
        block {}
      }

      statement {
        ip_set_reference_statement {
          arn = aws_wafv2_ip_set.frontend_denylist[0].arn
        }
      }

      visibility_config {
        cloudwatch_metrics_enabled = true
        metric_name                = "IPDenyList"
        sampled_requests_enabled   = true
      }
    }
  }

  dynamic "rule" {
    for_each = var.enable_frontend_waf && length(var.frontend_waf_allowlist_ips) > 0 ? [1] : []
    content {
      name     = "IPAllowList"
      priority = 20

      action {
        allow {}
      }

      statement {
        ip_set_reference_statement {
          arn = aws_wafv2_ip_set.frontend_allowlist[0].arn
        }
      }

      visibility_config {
        cloudwatch_metrics_enabled = true
        metric_name                = "IPAllowList"
        sampled_requests_enabled   = true
      }
    }
  }

  rule {
    name     = "AWSManagedRulesCommonRuleSet"
    priority = 30

    override_action {
      none {}
    }

    statement {
      managed_rule_group_statement {
        name        = "AWSManagedRulesCommonRuleSet"
        vendor_name = "AWS"
      }
    }

    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                = "AWSManagedRulesCommonRuleSet"
      sampled_requests_enabled   = true
    }
  }

  rule {
    name     = "AWSManagedRulesKnownBadInputsRuleSet"
    priority = 40

    override_action {
      none {}
    }

    statement {
      managed_rule_group_statement {
        name        = "AWSManagedRulesKnownBadInputsRuleSet"
        vendor_name = "AWS"
      }
    }

    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                = "AWSManagedRulesKnownBadInputsRuleSet"
      sampled_requests_enabled   = true
    }
  }

  rule {
    name     = "AWSManagedRulesAmazonIpReputationList"
    priority = 50

    override_action {
      none {}
    }

    statement {
      managed_rule_group_statement {
        name        = "AWSManagedRulesAmazonIpReputationList"
        vendor_name = "AWS"
      }
    }

    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                = "AWSManagedRulesAmazonIpReputationList"
      sampled_requests_enabled   = true
    }
  }

  rule {
    name     = "AWSManagedRulesAnonymousIpList"
    priority = 60

    override_action {
      none {}
    }

    statement {
      managed_rule_group_statement {
        name        = "AWSManagedRulesAnonymousIpList"
        vendor_name = "AWS"
      }
    }

    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                = "AWSManagedRulesAnonymousIpList"
      sampled_requests_enabled   = true
    }
  }

  rule {
    name     = "RateLimit"
    priority = 70

    action {
      block {}
    }

    statement {
      rate_based_statement {
        limit              = var.frontend_waf_rate_limit
        aggregate_key_type = "IP"
      }
    }

    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                = "RateLimit"
      sampled_requests_enabled   = true
    }
  }
}
resource "aws_wafv2_ip_set" "frontend_allowlist" {
  count    = var.enable_frontend_waf && length(var.frontend_waf_allowlist_ips) > 0 ? 1 : 0
  provider = aws.us_east_1

  name               = "${var.ec2_instance_name}-frontend-allowlist"
  description        = "Optional allowlist for frontend WAF"
  scope              = "CLOUDFRONT"
  ip_address_version = "IPV4"
  addresses          = var.frontend_waf_allowlist_ips
}
resource "aws_wafv2_ip_set" "frontend_denylist" {
  count    = var.enable_frontend_waf && length(var.frontend_waf_denylist_ips) > 0 ? 1 : 0
  provider = aws.us_east_1

  name               = "${var.ec2_instance_name}-frontend-denylist"
  description        = "Optional denylist for frontend WAF"
  scope              = "CLOUDFRONT"
  ip_address_version = "IPV4"
  addresses          = var.frontend_waf_denylist_ips
}
resource "aws_cloudwatch_log_group" "frontend_waf" {
  count    = var.enable_frontend_waf ? 1 : 0
  provider = aws.us_east_1

  # AWS WAF requires the log group name to start with "aws-waf-logs-".
  # checkov:skip=CKV_AWS_158: KMS encryption is optional for this project's WAF logs; can be enabled later if required.
  # checkov:skip=CKV_AWS_338: 30 days retention is sufficient for this project.
  name              = "aws-waf-logs-${var.ec2_instance_name}-frontend"
  retention_in_days = 30

  tags = {
    Name = "${var.ec2_instance_name}-frontend-waf-logs"
  }
}
resource "aws_wafv2_web_acl_logging_configuration" "frontend" {
  count    = var.enable_frontend_waf ? 1 : 0
  provider = aws.us_east_1

  resource_arn            = aws_wafv2_web_acl.frontend[0].arn
  log_destination_configs = [aws_cloudwatch_log_group.frontend_waf[0].arn]
}
resource "aws_wafv2_web_acl_association" "frontend" {
  count    = var.enable_frontend_waf && length(local.frontend_distribution_arn) > 0 ? 1 : 0
  provider = aws.us_east_1

  resource_arn = local.frontend_distribution_arn
  web_acl_arn  = aws_wafv2_web_acl.frontend[0].arn
}
resource "aws_sns_topic" "alarms" {
  count = var.enable_alarms ? 1 : 0

  name = "${var.ec2_instance_name}-alarms"
}
resource "aws_sns_topic_subscription" "alarm_email" {
  count = var.enable_alarms && length(trimspace(var.alarm_email)) > 0 ? 1 : 0

  topic_arn = aws_sns_topic.alarms[0].arn
  protocol  = "email"
  endpoint  = trimspace(var.alarm_email)
}
resource "aws_cloudwatch_metric_alarm" "alb_5xx" {
  count = var.enable_alarms ? 1 : 0

  alarm_name          = "${var.ec2_instance_name}-alb-5xx"
  alarm_description   = "ALB 5xx responses exceeded 5 over 5 minutes."
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "HTTPCode_ELB_5XX_Count"
  namespace           = "AWS/ApplicationELB"
  period              = 300
  statistic           = "Sum"
  threshold           = 5
  treat_missing_data  = "notBreaching"

  dimensions = {
    LoadBalancer = aws_lb.main.arn_suffix
  }

  alarm_actions = [aws_sns_topic.alarms[0].arn]
  ok_actions    = [aws_sns_topic.alarms[0].arn]
}
resource "aws_cloudwatch_metric_alarm" "target_unhealthy_hosts" {
  count = var.enable_alarms ? 1 : 0

  alarm_name          = "${var.ec2_instance_name}-tg-unhealthy-hosts"
  alarm_description   = "Target group has unhealthy hosts for 2 minutes."
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "UnHealthyHostCount"
  namespace           = "AWS/ApplicationELB"
  period              = 60
  statistic           = "Average"
  threshold           = 0
  treat_missing_data  = "notBreaching"

  dimensions = {
    LoadBalancer = aws_lb.main.arn_suffix
    TargetGroup  = aws_lb_target_group.backend.arn_suffix
  }

  alarm_actions = [aws_sns_topic.alarms[0].arn]
  ok_actions    = [aws_sns_topic.alarms[0].arn]
}
resource "aws_cloudwatch_metric_alarm" "backend_asg_cpu" {
  count = var.enable_alarms ? 1 : 0

  alarm_name          = "${var.ec2_instance_name}-asg-cpu-high"
  alarm_description   = "Average ASG CPU utilization exceeded 80 percent over 5 minutes."
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "CPUUtilization"
  namespace           = "AWS/EC2"
  period              = 300
  statistic           = "Average"
  threshold           = 80
  treat_missing_data  = "notBreaching"

  dimensions = {
    AutoScalingGroupName = aws_autoscaling_group.backend.name
  }

  alarm_actions = [aws_sns_topic.alarms[0].arn]
  ok_actions    = [aws_sns_topic.alarms[0].arn]
}
resource "aws_cloudwatch_metric_alarm" "alb_target_response_time_p95" {
  count = var.enable_alarms ? 1 : 0

  alarm_name          = "${var.ec2_instance_name}-alb-target-response-time-p95"
  alarm_description   = "ALB target response time p95 exceeded 1 second over 5 minutes."
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "TargetResponseTime"
  namespace           = "AWS/ApplicationELB"
  period              = 300
  extended_statistic  = "p95"
  threshold           = 1
  treat_missing_data  = "notBreaching"

  dimensions = {
    LoadBalancer = aws_lb.main.arn_suffix
    TargetGroup  = aws_lb_target_group.backend.arn_suffix
  }

  alarm_actions = [aws_sns_topic.alarms[0].arn]
  ok_actions    = [aws_sns_topic.alarms[0].arn]
}
