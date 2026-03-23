#!/bin/bash
set -euo pipefail

# Redirect all script output to a specific log file for easier debugging
exec > >(tee /var/log/app-bootstrap.log) 2>&1

echo "=== Starting App Bootstrap ==="

# Install Docker if not present
if ! command -v docker >/dev/null 2>&1; then
  echo "Installing Docker..."
  export DEBIAN_FRONTEND=noninteractive
  
  # Wait for lock (up to 5 mins) before continuing
  echo "Running apt-get update and install..."
  for i in {1..30}; do
    if apt-get update -y && apt-get install -y ca-certificates curl unzip; then
      echo "Apt packages installed successfully."
      break
    else
      echo "Apt locked, waiting 10s ($i/30)..."
      sleep 10
    fi
  done
  
  curl -fsSL https://get.docker.com -o /tmp/get-docker.sh
  sh /tmp/get-docker.sh
  systemctl enable --now docker
else
  echo "Docker already installed."
fi

# Install AWS CLI v2 if not present (Ubuntu AMIs often lack it)
if ! command -v aws >/dev/null 2>&1; then
  echo "Installing AWS CLI v2..."
  curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
  unzip -q awscliv2.zip
  ./aws/install
  rm -rf awscliv2.zip aws/
else
  echo "AWS CLI already installed."
fi

echo "Logging into ECR..."
aws ecr get-login-password --region ${aws_region} | docker login --username AWS --password-stdin ${ecr_repository_url}

echo "Fetching .env from SSM Parameter Store..."
TARGET_DIR="/home/ubuntu/aws-fcj-backend"
mkdir -p "$TARGET_DIR"
aws ssm get-parameter --name "${ssm_parameter_name}" --with-decryption --query "Parameter.Value" --output text > "$TARGET_DIR/.env"

echo "Pulling image..."
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
