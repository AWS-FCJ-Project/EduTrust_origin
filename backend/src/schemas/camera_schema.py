from typing import List, Optional

from pydantic import BaseModel


class CameraDetectionResponse(BaseModel):
    person_count: int
    forbidden_detected: bool
    violations: List[str]
    timestamp: str
    visualized_frame: Optional[str] = None  # Base64 encoded string
