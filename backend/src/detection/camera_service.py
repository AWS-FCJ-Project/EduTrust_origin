import os
import time
from datetime import datetime

import cv2
import numpy as np
from src.detection.object_detection import ObjectDetector
from src.detection.screenshot_utils import get_violation_capturer
from src.detection.violation_logger import get_violation_logger


class CameraService:
    def __init__(self):
        self.config = {
            "objects": {
                "min_confidence": 0.5,
                "detection_interval": 1,
                "max_fps": 10,
                "model_path": os.path.join(os.path.dirname(__file__), "yolo26n.pt"),
            }
        }
        self.detector = ObjectDetector({"detection": self.config})
        self.logger = get_violation_logger()
        self.capturer = get_violation_capturer()

    async def process_frame(self, frame_bytes: bytes):
        nparr = np.frombuffer(frame_bytes, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        if frame is None:
            return {"error": "Invalid image data"}

        results = self.detector.detect_objects(frame, visualize=True)

        if results:
            violations = self._get_violations(results)
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            if violations:
                for v_type in violations:
                    await self.capturer.capture_violation(
                        "unknown_exam", "unknown_student", frame, v_type, timestamp
                    )
                    await self.logger.log_violation(
                        "unknown_exam",
                        "unknown_student",
                        v_type,
                        timestamp,
                        {"person_count": results["person_count"]},
                    )

            _, buffer = cv2.imencode(".jpg", frame)
            visualized_frame_bytes = buffer.tobytes()

            return {
                "person_count": results["person_count"],
                "forbidden_detected": results["forbidden_detected"],
                "violations": violations,
                "visualized_frame": visualized_frame_bytes,
                "timestamp": timestamp,
            }
        else:
            return {"error": "Detection failed"}

    def _get_violations(self, results):
        violations = []
        if results["person_count"] == 0:
            violations.append("FACE_DISAPPEARED")
        elif results["person_count"] > 1:
            violations.append("MULTIPLE_FACES")

        if results["forbidden_detected"]:
            violations.append("FORBIDDEN_OBJECT")

        return violations

    async def process_client_log(self, payload: dict):
        import base64
        import binascii

        violations = payload.get("violation_codes", [])
        image_b64 = payload.get("image")
        exam_id = payload.get("exam_id", "unknown_exam")
        student_id = payload.get("student_id", "unknown_student")

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
            print(f" [DEBUG] Base64 Image received (Length: {len(image_b64)} chars)")
            image_b64 += "=" * ((4 - len(image_b64) % 4) % 4)
            try:
                frame_bytes = base64.b64decode(image_b64)
            except binascii.Error as e:
                print(f" [ERROR] Base64 decode failed: {e}")
                return {"error": "Invalid base64 encoding"}

            nparr = np.frombuffer(frame_bytes, np.uint8)
            frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

            if frame is None:
                print(" [ERROR] cv2.imdecode failed (Image format corrupted?)")
                return {"error": "Could not decode image"}

            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            person_count = payload.get("person_count", 0)

            for v_code in violations:
                print(f" [ACTION] Logging {v_code} for {student_id}...")
                await self.capturer.capture_violation(
                    exam_id, student_id, frame, v_code, timestamp
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
