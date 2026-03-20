import cv2
import os
from datetime import datetime

class ViolationCapturer:
    def __init__(self, output_path):
        self.output_dir = os.path.join(output_path, "violation_captures")
        os.makedirs(self.output_dir, exist_ok=True)
        
    def capture_violation(self, frame, violation_type, timestamp=None):
        """Saves violation screenshot with metadata"""
        # Use high precision for uniquely identifying files in real-time
        precise_ts = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        filename = f"{violation_type}_{precise_ts}.jpg"
        path = os.path.join(self.output_dir, filename)
        
        # Draw violation label on image
        label_ts = timestamp or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        timestamp_str = f"{violation_type} - {label_ts}"
        
        # Resize to save space
        resized_frame = cv2.resize(frame, (320, 240))
        
        cv2.putText(resized_frame, timestamp_str, (10, 20), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 0, 255), 1)
        
        success = cv2.imwrite(path, resized_frame)
        if success:
            print(f"[SUCCESS] Saved violation capture: {filename}")
        else:
            print(f"[ERROR] Failed to save violation capture to: {path}")
            
        return {
            'type': violation_type,
            'timestamp': label_ts,
            'image_path': os.path.abspath(path)
        }

def get_violation_capturer():
    # Use a relative path from the backend root
    output_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "storage"))
    return ViolationCapturer(output_path)
