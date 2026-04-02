from datetime import datetime

import cv2
import numpy as np

from src.detection.screenshot_utils import get_violation_capturer
from src.detection.violation_logger import get_violation_logger


class CameraService:
    def __init__(self):
        self.logger = get_violation_logger()
        self.capturer = get_violation_capturer()

    async def process_client_log(self, payload: dict):
        import base64
        import binascii

        violations = payload.get("violation_codes", [])
        image_b64 = payload.get("image")
        exam_id = payload.get("exam_id", "unknown_exam")
        student_id = payload.get("student_id", "unknown_student")
        image_ext = (payload.get("image_ext") or "jpg").lstrip(".")

        print(
            f" [SERVICE] Processing client log for student {student_id} in exam {exam_id}"
        )

        if not violations:
            print(" [DEBUG] No violations in payload. (Could be a clear-log request)")

        if not image_b64:
            if not violations:
                return {"status": "cleared"}
            print(" [ERROR] Image missing from violation payload")
            return {"error": "Missing image for violation"}

        try:
            # Accept both raw base64 and data URLs like: data:image/jpeg;base64,....
            if not isinstance(image_b64, str):
                image_b64 = str(image_b64)
            image_b64 = image_b64.strip()
            if "," in image_b64 and "base64" in image_b64[:100]:
                image_b64 = image_b64.split(",", 1)[1]

            print(f" [DEBUG] Base64 Image received (Length: {len(image_b64)} chars)")
            image_b64 += "=" * ((4 - len(image_b64) % 4) % 4)
            try:
                image_bytes = base64.b64decode(image_b64)
            except binascii.Error as e:
                print(f" [ERROR] Base64 decode failed: {e}")
                return {"error": "Invalid base64 encoding"}

            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            person_count = payload.get("person_count", 0)

            for v_code in violations:
                print(f" [ACTION] Logging {v_code} for {student_id}...")
                await self.capturer.capture_violation_bytes(
                    exam_id,
                    student_id,
                    image_bytes,
                    v_code,
                    timestamp,
                    image_ext=image_ext,
                )
                await self.logger.log_violation(
                    exam_id,
                    student_id,
                    v_code,
                    timestamp,
                    {"person_count": person_count},
                )

            return {"status": "logged success", "violations_count": len(violations)}
        except Exception as e:
            print(f" [ERROR] Exception in camera service logic: {e}")
            return {"error": str(e)}


camera_service = None


def get_camera_service():
    global camera_service
    if camera_service is None:
        camera_service = CameraService()
    return camera_service
