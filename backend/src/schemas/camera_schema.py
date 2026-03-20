from pydantic import BaseModel
from typing import List, Optional

class CameraDetectionResponse(BaseModel):
    person_count: int
    forbidden_detected: bool
    violations: List[str]
    timestamp: str
    visualized_frame: Optional[str] = None  # Base64 encoded string
