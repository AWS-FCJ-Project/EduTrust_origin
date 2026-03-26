#!/bin/bash
set -euo pipefail

BUCKET_NAME="aws-fcj-terraform-641458060045"
REGION="ap-southeast-1"

echo "🚀 Bắt đầu bootstrap Terraform backend..."

# Create s3 bucket
echo "📦 Checking S3: $BUCKET_NAME"

if aws s3api head-bucket --bucket "$BUCKET_NAME" --region "$REGION" 2>/dev/null; then
  echo "  ✅ Bucket existed. Skipped"
else
  echo "  🔧 Creating bucket..."
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

  echo "  ✅ Bucket created and configured"
fi

# Verify bucket is accessible before exiting (prevents race condition with terraform init)
echo "⏳ Verifying bucket is accessible..."
MAX_WAIT=12
for i in $(seq 1 $MAX_WAIT); do
  if aws s3api head-bucket --bucket "$BUCKET_NAME" --region "$REGION" 2>/dev/null; then
    echo "  ✅ Bucket is accessible and ready"
    break
  fi
  if [ "$i" -eq "$MAX_WAIT" ]; then
    echo "  ❌ Bucket not accessible after $((MAX_WAIT * 5)) seconds. Aborting."
    exit 1
  fi
  echo "  ⏳ Attempt $i/$MAX_WAIT - not accessible yet, retrying in 5s..."
  sleep 5
done

echo ""
echo "🎉 Bootstrap completed! Now you can run terraform init."