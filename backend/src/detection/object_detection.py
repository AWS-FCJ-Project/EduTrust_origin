from datetime import datetime

import cv2
import torch
from ultralytics import YOLO


class ObjectDetector:
    def __init__(self, config):
        self.config = config["detection"]["objects"]
        self.model = None
        self.class_map = {0: "person", 73: "book", 67: "cell phone"}
        self.forbidden_classes = [73, 67]
        self.person_class = 0
        self.alert_logger = None
        self.detection_interval = self.config["detection_interval"]
        self.frame_count = 0
        self._initialize_model()
        self.last_detection_time = datetime.now()

    def _initialize_model(self):
        """Initialize optimized YOLO model"""
        try:
            model_path = self.config.get("model_path", "yolo26n.pt")
            self.model = YOLO(model_path, task="detect")

            # Optimize model settings
            self.model.overrides["conf"] = self.config["min_confidence"]
            self.model.overrides["device"] = (
                "cuda" if torch.cuda.is_available() else "cpu"
            )
            self.model.overrides["imgsz"] = (
                320  # Smaller input size for faster processing
            )
            # self.model.overrides['half'] = True  # Use FP16 precision if GPU available
            self.model.overrides["iou"] = 0.45  # Slightly higher IOU threshold

            # Warm up the model
            dummy_input = torch.zeros((1, 3, 320, 320)).to(self.model.device)
            self.model(dummy_input)

        except Exception as e:
            raise RuntimeError(f"Failed to initialize object detector: {str(e)}")

    def set_alert_logger(self, alert_logger):
        self.alert_logger = alert_logger

    def detect_objects(self, frame, visualize=False):
        """Optimized object detection with frame skipping"""
        current_time = datetime.now()
        time_since_last = (current_time - self.last_detection_time).total_seconds()

        # Skip detection if not enough time has passed
        # Skip detection if not enough time has passed
        if time_since_last < (1.0 / self.config["max_fps"]):
            if visualize and hasattr(self, "last_results") and self.last_results:
                for box in self.last_results:
                    x1, y1, x2, y2, label, conf = box
                    color = (0, 255, 0) if label == "person" else (0, 0, 255)
                    cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
                    cv2.putText(
                        frame,
                        f"{label} {conf:.2f}",
                        (x1, y1 - 10),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.5,
                        color,
                        1,
                    )
            return getattr(
                self,
                "last_detected_result",
                {"person_count": 0, "forbidden_detected": False},
            )

        try:
            # Resize frame for faster processing (maintaining aspect ratio)
            orig_h, orig_w = frame.shape[:2]
            new_w = 416
            new_h = int(orig_h * (new_w / orig_w))
            resized_frame = cv2.resize(
                frame, (new_w, new_h), interpolation=cv2.INTER_LINEAR
            )

            # Run inference
            results = self.model(resized_frame, verbose=False)  # Disable logging

            forbidden_detected = False
            person_count = 0
            self.last_results = []

            for result in results:
                for box in result.boxes:
                    cls = int(box.cls)
                    conf = float(box.conf)

                    if cls in self.class_map and conf > self.config["min_confidence"]:
                        label = self.class_map[cls]

                        # Count persons
                        if cls == self.person_class:
                            person_count += 1

                        # Check forbidden objects
                        if cls in self.forbidden_classes:
                            forbidden_detected = True
                            if self.alert_logger:
                                self.alert_logger.log_alert(
                                    "FORBIDDEN_OBJECT",
                                    f"Detected {label} with confidence {conf:.2f}",
                                )

                        # Scale coordinates back to original frame size
                        x1, y1, x2, y2 = box.xyxy[0]
                        x1 = int(x1 * (orig_w / new_w))
                        y1 = int(y1 * (orig_h / new_h))
                        x2 = int(x2 * (orig_w / new_w))
                        y2 = int(y2 * (orig_h / new_h))

                        self.last_results.append((x1, y1, x2, y2, label, conf))

                        if visualize:
                            color = (
                                (0, 255, 0) if cls == self.person_class else (0, 0, 255)
                            )
                            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
                            cv2.putText(
                                frame,
                                f"{label} {conf:.2f}",
                                (x1, y1 - 10),
                                cv2.FONT_HERSHEY_SIMPLEX,
                                0.5,
                                color,
                                1,
                            )

            result_dict = {
                "person_count": person_count,
                "forbidden_detected": forbidden_detected,
                "boxes": self.last_results,
            }

            self.last_detected_result = result_dict
            self.last_detection_time = current_time
            return result_dict

        except Exception as e:
            if self.alert_logger:
                self.alert_logger.log_alert(
                    "OBJECT_DETECTION_ERROR", f"Object detection failed: {str(e)}"
                )
            return False
