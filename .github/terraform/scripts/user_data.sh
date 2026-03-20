#!/bin/bash
set -euo pipefail

# Install Docker if not present
if ! command -v docker >/dev/null 2>&1; then
  apt-get update -y
  apt-get install -y ca-certificates curl
  curl -fsSL https://get.docker.com -o /tmp/get-docker.sh
  sh /tmp/get-docker.sh
  systemctl enable --now docker
fi

# Login to ECR
aws ecr get-login-password --region ${aws_region} | docker login --username AWS --password-stdin ${ecr_repository_url}

# Fetch .env from SSM Parameter Store
TARGET_DIR="/home/ubuntu/aws-fcj-backend"
mkdir -p "$TARGET_DIR"
aws ssm get-parameter --name "${ssm_parameter_name}" --with-decryption --query "Parameter.Value" --output text > "$TARGET_DIR/.env"

# Pull and run the container
docker pull ${ecr_repository_url}:${image_tag}

# Stop existing container if any (though usually fresh instance)
docker stop aws-fcj-backend || true
docker rm aws-fcj-backend || true

docker run -d \
  --name aws-fcj-backend \
  --restart unless-stopped \
  -p ${backend_port}:${backend_port} \
  --env-file "$TARGET_DIR/.env" \
  ${ecr_repository_url}:${image_tag}
