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
            self.model.overrides["iou"] = 0.45  # Slightly higher IOU threshold

            # Warm up the model
            dummy_input = torch.zeros((1, 3, 320, 320)).to(self.model.device)
            self.model(dummy_input)

        except Exception as e:
            raise RuntimeError(f"Failed to initialize object detector: {str(e)}")

    def set_alert_logger(self, alert_logger):
        self.alert_logger = alert_logger

    def _should_skip_detection(self, current_time):
        """Checks if detection should be skipped based on FPS config"""
        time_since_last = (current_time - self.last_detection_time).total_seconds()
        return time_since_last < (1.0 / self.config["max_fps"])

    def _draw_cached_results(self, frame):
        """Draws last known results when skipping a frame"""
        if hasattr(self, "last_results") and self.last_results:
            for x1, y1, x2, y2, label, conf in self.last_results:
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

    def _preprocess_frame(self, frame):
        """Resizes frame for faster processing"""
        orig_h, orig_w = frame.shape[:2]
        new_w = 416
        new_h = int(orig_h * (new_w / orig_w))
        resized = cv2.resize(frame, (new_w, new_h), interpolation=cv2.INTER_LINEAR)
        return resized, orig_w, orig_h, new_w, new_h

    def _handle_detection(self, cls, conf, orig_w, orig_h, new_w, new_h, box_xyxy):
        """Processes a single detection box"""
        label = self.class_map[cls]
        is_person = cls == self.person_class
        is_forbidden = cls in self.forbidden_classes

        if is_forbidden and self.alert_logger:
            self.alert_logger.log_alert(
                "FORBIDDEN_OBJECT", f"Detected {label} with confidence {conf:.2f}"
            )

        # Scale coordinates
        x1, y1, x2, y2 = box_xyxy
        x1, y1 = int(x1 * (orig_w / new_w)), int(y1 * (orig_h / new_h))
        x2, y2 = int(x2 * (orig_w / new_w)), int(y2 * (orig_h / new_h))

        return x1, y1, x2, y2, label, is_person, is_forbidden

    def _draw_detection(self, frame, x1, y1, x2, y2, label, conf, is_p):
        """Draws a single detection box and label on the frame"""
        color = (0, 255, 0) if is_p else (0, 0, 255)
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

    def _process_single_box(self, box, orig_w, orig_h, new_w, new_h, frame, visualize):
        """Processes a single YOLO box and returns detection details"""
        cls, conf = int(box.cls), float(box.conf)
        if cls not in self.class_map or conf <= self.config["min_confidence"]:
            return None

        x1, y1, x2, y2, label, is_p, is_f = self._handle_detection(
            cls, conf, orig_w, orig_h, new_w, new_h, box.xyxy[0]
        )

        if visualize:
            self._draw_detection(frame, x1, y1, x2, y2, label, conf, is_p)

        return x1, y1, x2, y2, label, conf, is_p, is_f

    def _process_all_results(
        self, results, orig_w, orig_h, new_w, new_h, frame, visualize
    ):
        """Iterates through YOLO results and aggregates detections"""
        person_count, forbidden_detected = 0, False
        self.last_results = []

        for result in results:
            for box in result.boxes:
                details = self._process_single_box(
                    box, orig_w, orig_h, new_w, new_h, frame, visualize
                )
                if details:
                    x1, y1, x2, y2, label, conf, is_p, is_f = details
                    person_count += 1 if is_p else 0
                    forbidden_detected = forbidden_detected or is_f
                    self.last_results.append((x1, y1, x2, y2, label, conf))

        return person_count, forbidden_detected

    def detect_objects(self, frame, visualize=False):
        """Object detection with frame skipping and helper methods"""
        current_time = datetime.now()

        if self._should_skip_detection(current_time):
            if visualize:
                self._draw_cached_results(frame)
            return getattr(
                self,
                "last_detected_result",
                {"person_count": 0, "forbidden_detected": False},
            )

        try:
            resized, orig_w, orig_h, new_w, new_h = self._preprocess_frame(frame)
            results = self.model(resized, verbose=False)

            person_count, forbidden_detected = self._process_all_results(
                results, orig_w, orig_h, new_w, new_h, frame, visualize
            )

            result_dict = {
                "person_count": person_count,
                "forbidden_detected": forbidden_detected,
                "boxes": self.last_results,
            }
            self.last_detected_result, self.last_detection_time = (
                result_dict,
                current_time,
            )
            return result_dict

        except Exception as e:
            if self.alert_logger:
                self.alert_logger.log_alert(
                    "OBJECT_DETECTION_ERROR", f"Detection failed: {str(e)}"
                )
            return False
