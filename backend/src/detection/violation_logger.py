import os
import json
from datetime import datetime

class ViolationLogger:
    def __init__(self, output_path):
        self.log_file = os.path.join(output_path, "violations.json")
        self.output_path = output_path
        os.makedirs(self.output_path, exist_ok=True)
        # Load existing violations if any
        if os.path.exists(self.log_file):
            try:
                with open(self.log_file, 'r') as f:
                    self.violations = json.load(f)
            except:
                self.violations = []
        else:
            self.violations = []
        
    def log_violation(self, violation_type, timestamp=None, metadata=None):
        """Logs a violation with timestamp and metadata"""
        entry = {
            'type': violation_type,
            'timestamp': timestamp or datetime.now().isoformat(),
            'metadata': metadata or {}
        }
        self.violations.append(entry)
        self._save_to_file()
        print(f"[SUCCESS] Logged violation to JSON: {violation_type}")
        
    def _save_to_file(self):
        """Saves violations to JSON file"""
        with open(self.log_file, 'w') as f:
            json.dump(self.violations, f, indent=2)

def get_violation_logger():
    # Use a relative path from the backend root
    output_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "storage"))
    return ViolationLogger(output_path)
