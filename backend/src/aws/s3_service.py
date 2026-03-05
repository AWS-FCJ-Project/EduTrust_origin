"""
Amazon S3 Service
Upload, download, delete files từ S3 bucket.
Thay thế local `uploads/` folder.
"""

import logging
import mimetypes
import uuid
from typing import Optional

import boto3
from botocore.exceptions import BotoCoreError, ClientError
from src.app_config import app_config

logger = logging.getLogger(__name__)


def _get_s3_client():
    """Tạo S3 client với credentials từ env."""
    return boto3.client(
        "s3",
        region_name=app_config.AWS_REGION,
        aws_access_key_id=app_config.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=app_config.AWS_SECRET_ACCESS_KEY,
    )


def upload_file(
    file_bytes: bytes,
    original_filename: str,
    content_type: Optional[str] = None,
    folder: str = "uploads",
) -> str:
    """
    Upload file lên S3.

    Args:
        file_bytes: Nội dung file dạng bytes
        original_filename: Tên file gốc (để lấy extension)
        content_type: MIME type (auto-detect nếu không truyền)
        folder: Thư mục trong S3 (mặc định: "uploads")

    Returns:
        S3 key của file đã upload (dùng để download/delete sau)

    Example:
        key = upload_file(file_bytes, "report.pdf")
        # → "uploads/2024/03/abc123.pdf"
    """
    s3 = _get_s3_client()
    bucket = app_config.S3_BUCKET_NAME

    # Tạo unique filename để tránh xung đột
    ext = original_filename.rsplit(".", 1)[-1] if "." in original_filename else ""
    unique_name = f"{uuid.uuid4().hex}.{ext}" if ext else uuid.uuid4().hex
    s3_key = f"{folder}/{unique_name}"

    # Auto-detect content type
    if not content_type:
        content_type, _ = mimetypes.guess_type(original_filename)
        content_type = content_type or "application/octet-stream"

    try:
        s3.put_object(
            Bucket=bucket,
            Key=s3_key,
            Body=file_bytes,
            ContentType=content_type,
        )
        logger.info(f"Uploaded file to S3: s3://{bucket}/{s3_key}")
        return s3_key
    except (ClientError, BotoCoreError) as e:
        logger.error(f"S3 upload failed: {e}")
        raise RuntimeError(f"Failed to upload file to S3: {e}") from e


def get_presigned_url(s3_key: str, expires_in: int = 3600) -> str:
    """
    Tạo pre-signed URL để download file từ S3 (không cần public bucket).

    Args:
        s3_key: S3 key của file (kết quả từ upload_file)
        expires_in: Thời gian URL còn hiệu lực (giây), mặc định 1 giờ

    Returns:
        URL có thể download file trong thời gian expires_in
    """
    s3 = _get_s3_client()
    bucket = app_config.S3_BUCKET_NAME

    try:
        url = s3.generate_presigned_url(
            "get_object",
            Params={"Bucket": bucket, "Key": s3_key},
            ExpiresIn=expires_in,
        )
        return url
    except (ClientError, BotoCoreError) as e:
        logger.error(f"Failed to generate presigned URL: {e}")
        raise RuntimeError(f"Failed to get file URL: {e}") from e


def delete_file(s3_key: str) -> None:
    """Xóa file khỏi S3."""
    s3 = _get_s3_client()
    bucket = app_config.S3_BUCKET_NAME

    try:
        s3.delete_object(Bucket=bucket, Key=s3_key)
        logger.info(f"Deleted file from S3: s3://{bucket}/{s3_key}")
    except (ClientError, BotoCoreError) as e:
        logger.error(f"S3 delete failed: {e}")
        raise RuntimeError(f"Failed to delete file: {e}") from e
