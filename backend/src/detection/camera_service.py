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
        # Default configuration for the detector
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

    def process_frame(self, frame_bytes: bytes):
        # Convert bytes to numpy array
        nparr = np.frombuffer(frame_bytes, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        if frame is None:
            return {"error": "Invalid image data"}

        # Perform detection
        results = self.detector.detect_objects(frame, visualize=True)

        if results:
            violations = self._get_violations(results)
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            # Persist if violations found
            if violations:
                for v_type in violations:
                    self.logger.log_violation(
                        v_type, timestamp, {"person_count": results["person_count"]}
                    )
                    self.capturer.capture_violation(frame, v_type, timestamp)

            # Convert frame back to bytes if we want to return the visualized frame
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

    def process_client_log(self, payload: dict):
        import base64
        
        violations = payload.get("violation_codes", [])
        image_b64 = payload.get("image")
        
        print(f"[DEBUG] process_client_log triggered. Violations: {violations}, HasImage: {bool(image_b64)}")
        
        if not violations or not image_b64:
            print("[DEBUG] Missing violations or image_b64")
            return {"error": "Missing violations or image"}

        try:
            print(f"[DEBUG] Image B64 length: {len(image_b64)}")
            import binascii
            try:
                # Add padding if necessary
                image_b64 += "=" * ((4 - len(image_b64) % 4) % 4)
                frame_bytes = base64.b64decode(image_b64)
            except binascii.Error as e:
                print(f"[ERROR] Base64 decode error: {e}")
                return {"error": "Invalid base64 string"}

            nparr = np.frombuffer(frame_bytes, np.uint8)
            frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if frame is None:
                print("[ERROR] cv2.imdecode returned None")
                return {"error": "Invalid image base64"}
                
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            person_count = payload.get("person_count", 0)

            for v_type in violations:
                self.logger.log_violation(
                    v_type, timestamp, {"person_count": person_count}
                )
                print(f"[DEBUG] Saving captured frame for {v_type}")
                self.capturer.capture_violation(frame, v_type, timestamp)
                
            return {"status": "logged success"}
        except Exception as e:
            print(f"[ERROR] Exception in process_client_log: {e}")
            return {"error": str(e)}

# Global instance for the service
camera_service = None

def get_camera_service():
    global camera_service
    if camera_service is None:
        camera_service = CameraService()
    return camera_service
