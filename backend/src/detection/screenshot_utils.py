from datetime import datetime

import cv2

from src.utils.s3_utils import get_s3_handler


class ViolationCapturer:
    def __init__(self, base_path):
        self.base_path = base_path
        self.s3_handler = get_s3_handler()

    async def capture_violation_bytes(
        self,
        exam_id: str,
        student_id: str,
        image_bytes: bytes,
        violation_type: str,
        timestamp: str | None = None,
        *,
        image_ext: str = "jpg",
    ):
        """Uploads a client-provided screenshot of the violation to S3.

        Detection happens on the frontend; backend only stores evidence.
        """
        s3_prefix = f"violations/students/{student_id}/{exam_id}/"

        current_count = self.s3_handler.get_file_count(s3_prefix)
        if current_count >= 4:
            print(
                f"[LIMIT] Already captured {current_count} violations for student {student_id} in exam {exam_id}. Skipping S3 upload."
            )
            return None

        display_ts = timestamp or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        precise_ts = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        ext = (image_ext or "jpg").lstrip(".").lower()
        # Keep extension simple to avoid weird keys/content-types.
        ext = "".join(ch for ch in ext if ch.isalnum()) or "jpg"
        filename = f"{violation_type}_{precise_ts}.{ext}"
        s3_key = f"{s3_prefix}{filename}"

        try:
            content_type = {
                "jpg": "image/jpeg",
                "jpeg": "image/jpeg",
                "png": "image/png",
                "webp": "image/webp",
            }.get(ext, "application/octet-stream")
            upload_success = self.s3_handler.upload_file_bytes(
                image_bytes, s3_key, content_type=content_type
            )
            if upload_success:
                print(
                    f"[S3 SUCCESS] Uploaded violation evidence ({display_ts}) to: {s3_key}"
                )
                return s3_key

            return None
        except Exception as e:
            print(f"[ERROR] capture_violation_bytes to S3 failed: {e}")
            return None


def get_violation_capturer():
    return ViolationCapturer(None)
