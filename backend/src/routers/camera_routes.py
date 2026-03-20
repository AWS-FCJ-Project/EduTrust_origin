from fastapi import APIRouter, UploadFile, File, HTTPException, WebSocket, WebSocketDisconnect
from src.detection.camera_service import get_camera_service
from src.schemas.camera_schema import CameraDetectionResponse
import base64

router = APIRouter(prefix="/camera", tags=["Camera"])

@router.post("/process", response_model=CameraDetectionResponse)
async def process_camera_frame(
    file: UploadFile = File(...), 
    visualize: bool = True
):
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Invalid file type. Must be an image.")
    
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
        "visualized_frame": None
    }
    
    if visualize and "visualized_frame" in result:
        response_data["visualized_frame"] = base64.b64encode(result["visualized_frame"]).decode("utf-8")
    
    return CameraDetectionResponse(**response_data)


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    service = get_camera_service()
    
    try:
        while True:
            # Receive frame data (bytes)
            data = await websocket.receive_bytes()
            
            # Process frame
            result = service.process_frame(data)
            
            if "error" in result:
                await websocket.send_json({"error": result["error"]})
                continue
            
            # Prepare response
            response = {
                "person_count": result["person_count"],
                "forbidden_detected": result["forbidden_detected"],
                "violations": result["violations"],
                "timestamp": result.get("timestamp", ""),
                "visualized_frame": base64.b64encode(result["visualized_frame"]).decode("utf-8") if "visualized_frame" in result else None
            }
            
            # Send result back
            await websocket.send_json(response)
            
    except WebSocketDisconnect:
        print("Client disconnected")
    except Exception as e:
        print(f"WebSocket error: {e}")
        try:
            await websocket.close()
        except:
            pass
