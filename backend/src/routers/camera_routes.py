import base64
from datetime import datetime
from typing import Annotated

from fastapi import (
    APIRouter,
    File,
    HTTPException,
    Request,
    UploadFile,
    WebSocket,
    WebSocketDisconnect,
)
from src.detection.camera_service import get_camera_service
from src.schemas.camera_schema import CameraDetectionResponse

router = APIRouter(prefix="/camera", tags=["Camera"])


@router.post("/log", responses={400: {"description": "Bad Request"}})
async def receive_client_log(request: Request):
    client_ip = request.client.host
    print(f"[ACCESS] POST /camera/log hit from {client_ip}")

    # Check for ngrok-specific headers to verify bypass is active
    if "ngrok-skip-browser-warning" in request.headers:
        print(
            f" [DEBUG] ngrok-skip-browser-warning detected: {request.headers['ngrok-skip-browser-warning']}"
        )

    try:
        payload = await request.json()
        violation_type = payload.get("type", "UNKNOWN")
        violation_codes = payload.get("violation_codes", [])

        print(f" [DEBUG] Payload Type: {violation_type}, Codes: {violation_codes}")

        service = get_camera_service()
        result = service.process_client_log(payload)

        if "error" in result:
            print(f" [ERROR] Logic failure: {result['error']}")
            raise HTTPException(status_code=400, detail=result["error"])

        print(" [SUCCESS] Violation processed and recorded.")
        return {"status": "success", "received_at": datetime.now().isoformat()}
    except Exception as e:
        print(f" [ERROR] Unexpected Failure: {e}")
        raise HTTPException(status_code=400, detail=str(e))


async def _process_binary_frame(message, service):
    """Processes raw binary frame from websocket."""
    result = service.process_frame(message["bytes"])
    return {
        "person_count": result.get("person_count", 0),
        "forbidden_detected": result.get("forbidden_detected", False),
        "violations": result.get("violations", []),
        "timestamp": result.get("timestamp", ""),
        "visualized_frame": (
            base64.b64encode(result["visualized_frame"]).decode()
            if result.get("visualized_frame")
            else None
        ),
    }


async def _process_json_payload(message, service):
    """Processes JSON payload from websocket."""
    try:
        payload = json.loads(message["text"])
        if payload.get("type") == "DETECTION_LOG":
            result = service.process_client_log(payload)
            if "error" in result:
                return {"error": result["error"]}
            return {
                "person_count": payload.get("person_count", 0),
                "forbidden_detected": False,
                "violations": payload.get("violations", []),
                "timestamp": payload.get("timestamp", ""),
                "visualized_frame": None,
            }
    except json.JSONDecodeError:
        return {"error": "Invalid format, expected JSON"}
    return None


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    service = get_camera_service()

    try:
        while True:
            message = await websocket.receive()

            if "bytes" in message:
                response = await _process_binary_frame(message, service)
                await websocket.send_json(response)

            elif "text" in message:
                response = await _process_json_payload(message, service)
                if response:
                    await websocket.send_json(response)

    except WebSocketDisconnect:
        print("Client disconnected")
    except Exception as e:
        print(f"WebSocket error: {e}")
        try:
            await websocket.close()
        except Exception:
            pass
