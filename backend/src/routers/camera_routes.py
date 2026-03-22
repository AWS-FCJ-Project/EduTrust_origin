import base64
from datetime import datetime
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
    client_ip = request.client.host
    print(f"[ACCESS] POST /camera/log hit from {client_ip}")

    # Check for ngrok-specific headers to verify bypass is active
    if "ngrok-skip-browser-warning" in request.headers:
        print(f" [DEBUG] ngrok-skip-browser-warning detected: {request.headers['ngrok-skip-browser-warning']}")

    try:
        payload = await request.json()
        violation_type = payload.get('type', 'UNKNOWN')
        violation_codes = payload.get('violation_codes', [])
        
        print(f" [DEBUG] Payload Type: {violation_type}, Codes: {violation_codes}")
        
        service = get_camera_service()
        result = service.process_client_log(payload)
        
        if "error" in result:
            print(f" [ERROR] Logic failure: {result['error']}")
            raise HTTPException(status_code=400, detail=result["error"])
        
        print(f" [SUCCESS] Violation processed and recorded.")
        return {"status": "success", "received_at": datetime.now().isoformat()}
    except Exception as e:
        print(f" [ERROR] Unexpected Failure: {e}")
        raise HTTPException(status_code=400, detail=str(e))

import json

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    service = get_camera_service()

    try:
        while True:
            # Chấp nhận cả tin nhắn văn bản (JSON) và tin nhắn nhị phân (ảnh trực tiếp)
            message = await websocket.receive()
            
            if "bytes" in message:
                # TRƯỜNG HỢP 1: Nhận ảnh thô (Dùng cho websocket_test.html để test mô hình Backend)
                result = service.process_frame(message["bytes"])
                
                # Trả về kết quả kèm ảnh đã được vẽ (visualized) nếu có
                response = {
                    "person_count": result.get("person_count", 0),
                    "forbidden_detected": result.get("forbidden_detected", False),
                    "violations": result.get("violations", []),
                    "timestamp": result.get("timestamp", ""),
                    "visualized_frame": base64.b64encode(result["visualized_frame"]).decode() if result.get("visualized_frame") else None
                }
                await websocket.send_json(response)

            elif "text" in message:
                # TRƯỜNG HỢP 2: Nhận JSON (Dùng cho App React chính thức - Edge AI)
                try:
                    payload = json.loads(message["text"])
                    
                    if payload.get("type") == "DETECTION_LOG":
                        result = service.process_client_log(payload)
                        
                        if "error" in result:
                            await websocket.send_json({"error": result["error"]})
                            continue

                        response = {
                            "person_count": payload.get("person_count", 0),
                            "forbidden_detected": False,
                            "violations": payload.get("violations", []),
                            "timestamp": payload.get("timestamp", ""),
                            "visualized_frame": None,
                        }
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
