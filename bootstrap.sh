#!/bin/bash
set -euo pipefail

BUCKET_NAME="aws-fcj-terraform-641458060045"
REGION="ap-southeast-1"

echo "Bootstrap Terraform backend..."

# Create s3 bucket
echo "Checking S3: $BUCKET_NAME"

if aws s3api head-bucket --bucket "$BUCKET_NAME" --region "$REGION" 2>/dev/null; then
  echo "Bucket existed. Skipped"
else
  echo "Creating bucket..."
  aws s3api create-bucket \
    --bucket "$BUCKET_NAME" \
    --region "$REGION" \
    --create-bucket-configuration LocationConstraint="$REGION"

  # Enable versioning to rollback
  aws s3api put-bucket-versioning \
    --bucket "$BUCKET_NAME" \
    --versioning-configuration Status=Enabled

  # Denied public access
  aws s3api put-public-access-block \
    --bucket "$BUCKET_NAME" \
    --public-access-block-configuration \
      BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true

  # AES-256 encrypt
  aws s3api put-bucket-encryption \
    --bucket "$BUCKET_NAME" \
    --server-side-encryption-configuration '{
      "Rules": [{
        "ApplyServerSideEncryptionByDefault": {
          "SSEAlgorithm": "AES256"
        }
      }]
    }'

  echo "Bucket created and configured"
fi

# Wait for bucket to be fully accessible before terraform init (prevents race condition)
echo "Waiting for bucket to be accessible..."
aws s3api wait bucket-exists \
  --bucket "$BUCKET_NAME" \
  --region "$REGION"
echo "Bucket is accessible and ready"

echo ""
echo "Bootstrap completed! Now you can run terraform init."