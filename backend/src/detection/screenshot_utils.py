import os
from datetime import datetime

import cv2
from src.utils.s3_utils import get_s3_handler


class ViolationCapturer:
    def __init__(self, base_path):
        self.base_path = base_path
        self.s3_handler = get_s3_handler()

    async def capture_violation(
        self, exam_id, student_id, frame, violation_type, timestamp=None
    ):
        """Captures a screenshot of the violation, adds label, and uploads to S3"""
        # S3 Prefix: violations/students/{student_id}/{exam_id}/
        s3_prefix = f"violations/students/{student_id}/{exam_id}/"

        # Check current count on S3 to enforce limit of 4
        current_count = self.s3_handler.get_file_count(s3_prefix)
        if current_count >= 4:
            print(
                f"[LIMIT] Already captured {current_count} violations for student {student_id} in exam {exam_id}. Skipping S3 upload."
            )
            return None

        # Create a copy and add text overlay
        labeled_frame = frame.copy()
        display_ts = timestamp or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        label = f"{violation_type} - {display_ts}"

        # Draw red label
        cv2.putText(
            labeled_frame,
            label,
            (10, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (0, 0, 255),
            2,
        )

        # Resize for storage efficiency
        resized_frame = cv2.resize(labeled_frame, (640, 480))

        precise_ts = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        filename = f"{violation_type}_{precise_ts}.jpg"
        s3_key = f"{s3_prefix}{filename}"

        try:
            # Encode frame to memory (bytes)
            success, buffer = cv2.imencode(".jpg", resized_frame)
            if not success:
                print("[ERROR] Failed to encode frame for S3 upload")
                return None

            file_bytes = buffer.tobytes()

            # Upload to S3 directly
            upload_success = self.s3_handler.upload_file_bytes(file_bytes, s3_key)
            if upload_success:
                print(f"[S3 SUCCESS] Captured and uploaded violation to: {s3_key}")
                return s3_key

            return None
        except Exception as e:
            print(f"[ERROR] capture_violation to S3 failed: {e}")
            return None


def get_violation_capturer():
    # Keep function for dependency injection
    return ViolationCapturer(None)
