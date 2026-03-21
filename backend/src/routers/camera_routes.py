import base64
from typing import Annotated

from fastapi import (
    APIRouter,
    File,
    HTTPException,
    UploadFile,
    WebSocket,
    WebSocketDisconnect,
    Request
)
from src.detection.camera_service import get_camera_service
from src.schemas.camera_schema import CameraDetectionResponse

router = APIRouter(prefix="/camera", tags=["Camera"])


@router.post("/log")
async def receive_client_log(request: Request):
    print(f"[DEBUG] POST /camera/log hit from {request.client.host}")
    try:
        payload = await request.json()
        print(f"[DEBUG] Received payload: type={payload.get('type')}")
        service = get_camera_service()
        result = service.process_client_log(payload)
        if "error" in result:
            print(f"[ERROR] Logic error: {result['error']}")
            raise HTTPException(status_code=400, detail=result["error"])
        return {"status": "success"}
    except Exception as e:
        print(f"[ERROR] Request failed: {e}")
        raise HTTPException(status_code=400, detail=str(e))

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
