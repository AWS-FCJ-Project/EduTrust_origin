import base64
from typing import Annotated

from fastapi import (
    APIRouter,
    File,
    HTTPException,
    UploadFile,
    WebSocket,
    WebSocketDisconnect,
)
from src.detection.camera_service import get_camera_service
from src.schemas.camera_schema import CameraDetectionResponse

router = APIRouter(prefix="/camera", tags=["Camera"])


@router.post(
    "/process",
    response_model=CameraDetectionResponse,
    responses={
        400: {"description": "Invalid file type. Must be an image."},
        500: {"description": "Internal server error during processing."},
    },
)
async def process_camera_frame(
    file: Annotated[UploadFile, File(...)], visualize: bool = True
):
    if not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=400, detail="Invalid file type. Must be an image."
        )

    contents = await file.read()
    service = get_camera_service()
    result = service.process_frame(contents)

    if "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])

    response_data = {
        "person_count": result["person_count"],
        "forbidden_detected": result["forbidden_detected"],
        "violations": result["violations"],
        "timestamp": result.get("timestamp", ""),
        "visualized_frame": None,
    }

    if visualize and "visualized_frame" in result:
        response_data["visualized_frame"] = base64.b64encode(
            result["visualized_frame"]
        ).decode("utf-8")

    return CameraDetectionResponse(**response_data)


import json

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    service = get_camera_service()

    try:
        while True:
            # Receive text data (JSON) instead of raw bytes
            data = await websocket.receive_text()
            try:
                payload = json.loads(data)
                
                if payload.get("type") == "DETECTION_LOG":
                    result = service.process_client_log(payload)
                    
                    if "error" in result:
                        await websocket.send_json({"error": result["error"]})
                        continue

                    # Prepare response to keep frontend's warning state synced
                    response = {
                        "person_count": payload.get("person_count", 0),
                        "forbidden_detected": False,
                        "violations": payload.get("violations", []),
                        "timestamp": payload.get("timestamp", ""),
                        "visualized_frame": None, # Frontend handles rendering now
                    }

                    # Send result back
                    await websocket.send_json(response)
                    
            except json.JSONDecodeError:
                await websocket.send_json({"error": "Invalid format, expected JSON"})

    except WebSocketDisconnect:
        print("Client disconnected")
    except Exception as e:
        print(f"WebSocket error: {e}")
        try:
            await websocket.close()
        except Exception:
            pass
