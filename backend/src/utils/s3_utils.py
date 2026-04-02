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

    def get_s3_key(self, object_name: str, prefix: str = "avatars") -> str:
        return f"{prefix}/{object_name}"

    def upload_img_s3(
        self, file_bytes, s3_key, content_type="image/jpeg", is_avatar=False
    ):
        bucket = app_config.S3_AVATAR_BUCKET_NAME if is_avatar else self.bucket_name
        if not bucket:
            bucket = self.bucket_name
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

    def get_presign_url(self, s3_key, expiration=3600, is_avatar=False):
        bucket = app_config.S3_AVATAR_BUCKET_NAME if is_avatar else self.bucket_name
        if not bucket:
            bucket = self.bucket_name
        try:
            url = self.s3_client.generate_presigned_url(
                "get_object",
                Params={"Bucket": bucket, "Key": s3_key},
                ExpiresIn=expiration,
            )
            return url
        except ClientError as e:
            print(f"[S3 ERROR] Failed to generate presigned URL: {e}")
            return None

    def get_presigned_url(self, s3_key, expiration=3600):
        """Generates a temporary public URL for a private S3 object (legacy method)"""
        return self.get_presign_url(s3_key, expiration, is_avatar=False)

    def load_avatar(
        self, base_64_url: str = None, image_url: str = None, user_id: str = None
    ):
        import base64
        from uuid import uuid4

        import requests

        if not base_64_url and not image_url:
            return None

        file_bytes = None
        content_type = "image/jpeg"

        try:
            if base_64_url:
                if "," in base_64_url:
                    header, encoded = base_64_url.split(",", 1)
                    if "image/png" in header:
                        content_type = "image/png"
                else:
                    encoded = base_64_url
                file_bytes = base64.b64decode(encoded)
            elif image_url:
                import urllib.parse

                # Check if it's a Google Image Search URL and extract the real image URL
                if "imgres" in image_url and "imgurl=" in image_url:
                    parsed_url = urllib.parse.urlparse(image_url)
                    query_params = urllib.parse.parse_qs(parsed_url.query)
                    if "imgurl" in query_params:
                        image_url = query_params["imgurl"][0]

                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                }
                response = requests.get(image_url, headers=headers, timeout=10)
                if response.status_code == 200:
                    content_type = response.headers.get("Content-Type", "").lower()
                    if "image" not in content_type:
                        print(
                            f"[S3 ERROR] URL is not an image (content_type={content_type})"
                        )
                        raise ValueError(
                            f"Đường dẫn kết nối thành công nhưng file nhận được là {content_type}, không phải file ảnh (.jpg, .png...)"
                        )
                    file_bytes = response.content
                else:
                    print(
                        f"[S3 ERROR] Failed to download image, status {response.status_code}"
                    )
                    raise ValueError(
                        f"Máy chủ chứa ảnh từ chối truy cập (Mã lỗi HTTP {response.status_code}). Cố gắng tìm ảnh ở trang web khác nhé!"
                    )
        except ValueError:
            raise
        except Exception as e:
            print(f"[S3 ERROR] load_avatar convert failed: {e}")
            raise ValueError(f"Lỗi không xác định khi tải hoặc xử lý ảnh: {str(e)}")

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
