from src.app_config import app_config

try:
    import boto3
    from botocore.exceptions import ClientError
except ImportError:  # pragma: no cover
    boto3 = None
    ClientError = Exception


class S3Handler:
    def __init__(self):
        if boto3 is None:
            raise RuntimeError("Missing dependency: boto3")

        self.bucket_name = app_config.S3_BUCKET_NAME
        self.region = app_config.AWS_REGION
        # Prefer IAM role credentials on AWS (instance profile / task role).
        # Only use static keys when explicitly provided (e.g., local dev).
        client_kwargs = {"region_name": self.region}
        if app_config.AWS_ACCESS_KEY_ID and app_config.AWS_SECRET_ACCESS_KEY:
            client_kwargs.update(
                {
                    "aws_access_key_id": app_config.AWS_ACCESS_KEY_ID,
                    "aws_secret_access_key": app_config.AWS_SECRET_ACCESS_KEY,
                }
            )

        self.s3_client = boto3.client("s3", **client_kwargs)

    def upload_file_bytes(self, file_bytes, s3_key, content_type="image/jpeg"):
        """Uploads raw bytes to S3"""
        try:
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=s3_key,
                Body=file_bytes,
                ContentType=content_type,
            )
            return True
        except ClientError as e:
            print(f"[S3 ERROR] Upload failed: {e}")
            return False

    def get_presigned_url(self, s3_key, bucket=None, expiration=3600):
        """Generates a temporary public URL for a private S3 object"""
        target_bucket = bucket or self.bucket_name
        try:
            url = self.s3_client.generate_presigned_url(
                "get_object",
                Params={"Bucket": target_bucket, "Key": s3_key},
                ExpiresIn=expiration,
            )
            return url
        except ClientError as e:
            print(f"[S3 ERROR] Failed to generate presigned URL: {e}")
            return None

    def delete_folder(self, prefix):
        """Deletes all objects under a specific prefix (folder)"""
        try:
            objects_to_delete = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name, Prefix=prefix
            )

            if "Contents" in objects_to_delete:
                delete_keys = {
                    "Objects": [
                        {"Key": obj["Key"]} for obj in objects_to_delete["Contents"]
                    ]
                }
                self.s3_client.delete_objects(
                    Bucket=self.bucket_name, Delete=delete_keys
                )
                print(f"[S3 SUCCESS] Deleted folder: {prefix}")
                return True
            return False
        except ClientError as e:
            print(f"[S3 ERROR] Delete failed: {e}")
            return False

    def get_file_count(self, prefix):
        """Counts files under a specific prefix to enforce limits"""
        try:
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name, Prefix=prefix
            )
            return response.get("KeyCount", 0)
        except ClientError as e:
            print(f"[S3 ERROR] Count failed: {e}")
            return 0

    def get_s3_key(self, object_name):
        return f"avatars/{object_name}"

    def upload_img_s3(
        self, file_bytes, s3_key, content_type="image/jpeg", is_avatar=False
    ):
        bucket = app_config.S3_AVATAR_BUCKET_NAME if is_avatar else self.bucket_name
        if not bucket:
            bucket = self.bucket_name  # Fallback
        try:
            self.s3_client.put_object(
                Bucket=bucket,
                Key=s3_key,
                Body=file_bytes,
                ContentType=content_type,
            )
            return True
        except ClientError as e:
            print(f"[S3 ERROR] Upload failed: {e}")
            return False

    def load_avatar(self, base_64_url: str = None, user_id: str = None):
        """Processes base64 and uploads to S3"""
        if not base_64_url:
            return None
            
        import base64
        import re
        from uuid import uuid4
        
        file_bytes = None
        content_type = "image/jpeg"
        
        try:
            # Process base64
            if base_64_url.startswith("data:image"):
                match = re.match(r"data:(image/\w+);base64,(.*)", base_64_url)
                if match:
                    content_type = match.group(1)
                    encoded = match.group(2)
                else:
                    encoded = (
                        base_64_url.split(",")[1] if "," in base_64_url else base_64_url
                    )
            else:
                encoded = base_64_url
            file_bytes = base64.b64decode(encoded)
        except Exception as e:
            print(f"[S3 ERROR] load_avatar convert failed: {e}")
            raise ValueError(f"Lấy ảnh base64 thất bại: {str(e)}")

        if file_bytes:
            ext = "png" if "png" in content_type else "jpg"
            s3_key = self.get_s3_key(f"{user_id}_{uuid4().hex}.{ext}")
            success = self.upload_img_s3(
                file_bytes, s3_key, content_type, is_avatar=True
            )
            if success:
                return s3_key
            else:
                raise ValueError("Không thể lưu ảnh lên hệ thống lưu trữ S3.")
        return None


_s3_handler = None


def get_s3_handler():
    global _s3_handler
    if _s3_handler is None:
        _s3_handler = S3Handler()
    return _s3_handler
