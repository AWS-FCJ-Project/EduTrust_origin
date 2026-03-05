# EC2 Outputs
output "instance_id" {
  description = "EC2 instance ID"
  value       = aws_instance.backend.id
}

output "instance_public_ip" {
  description = "EC2 instance public IP"
  value       = aws_instance.backend.public_ip
}

output "instance_private_ip" {
  description = "EC2 instance private IP"
  value       = aws_instance.backend.private_ip
}

output "instance_public_dns" {
  description = "EC2 instance public DNS"
  value       = aws_instance.backend.public_dns
}

# VPC Output — để biết đang dùng VPC nào
output "vpc_id" {
  description = "Default VPC ID đang được sử dụng"
  value       = data.aws_vpc.default.id
}

# S3 Outputs
output "s3_bucket_name" {
  description = "S3 bucket name for uploads"
  value       = aws_s3_bucket.uploads.bucket
}

output "s3_bucket_arn" {
  description = "S3 bucket ARN"
  value       = aws_s3_bucket.uploads.arn
}

# Redis Outputs — copy vào .env
output "redis_endpoint" {
  description = "Redis endpoint — dùng cho REDIS_URL trong .env"
  value       = "redis://${aws_elasticache_cluster.redis.cache_nodes[0].address}:${aws_elasticache_cluster.redis.cache_nodes[0].port}"
}

# IAM Outputs — copy vào .env
output "backend_aws_access_key_id" {
  description = "AWS Access Key ID — thêm vào .env: AWS_ACCESS_KEY_ID"
  value       = aws_iam_access_key.backend.id
  sensitive   = true
}

output "backend_aws_secret_access_key" {
  description = "AWS Secret Access Key — thêm vào .env: AWS_SECRET_ACCESS_KEY"
  value       = aws_iam_access_key.backend.secret
  sensitive   = true
}
