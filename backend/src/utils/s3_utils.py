import boto3
from botocore.exceptions import ClientError
from src.app_config import app_config


class S3Handler:
    def __init__(self):
        self.bucket_name = app_config.S3_BUCKET_NAME
        self.region = app_config.AWS_REGION
        self.s3_client = boto3.client(
            "s3",
            aws_access_key_id=app_config.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=app_config.AWS_SECRET_ACCESS_KEY,
            region_name=self.region,
        )

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

    def get_presigned_url(self, s3_key, expiration=3600):
        """Generates a temporary public URL for a private S3 object"""
        try:
            url = self.s3_client.generate_presigned_url(
                "get_object",
                Params={"Bucket": self.bucket_name, "Key": s3_key},
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


_s3_handler = None


def get_s3_handler():
    global _s3_handler
    if _s3_handler is None:
        _s3_handler = S3Handler()
    return _s3_handler
