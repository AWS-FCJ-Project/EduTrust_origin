import asyncio
import websockets
import json
import base64

async def test():
    try:
        url = 'wss://anagrammatically-nonderogative-bibi.ngrok-free.dev/camera/ws'
        print(f'Connecting to {url}')
        async with websockets.connect(url) as ws:
            print('Connected successfully via Ngrok!')
            dummy_img = b'\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00\xff\xdb\x00C\x00\x08\x06\x06\x07\x06\x05\x08\x07\x07\x07\t\t\x08\n\x0c\x14\r\x0c\x0b\x0b\x0c\x19\x12\x13\x0f\x14\x1d\x1a\x1f\x1e\x1d\x1a\x1c\x1c $.\' \",#\x1c\x1c(7),01444\x1f\'9=82<.342\xff\xc0\x00\x0b\x08\x00\n\x00\n\x01\x01\x11\x00\xff\xc4\x00\x1f\x00\x00\x01\x05\x01\x01\x01\x01\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x01\x02\x03\x04\x05\x06\x07\x08\t\n\x0b\xff\xda\x00\x08\x01\x01\x00\x00?\x00\x12\x1f\xf9\xff\xd9'
            payload = {
                'type': 'DETECTION_LOG',
                'violations': ['Không tìm thấy khuôn mặt'],
                'violation_codes': ['FACE_DISAPPEARED'],
                'image': base64.b64encode(dummy_img).decode()
            }
            await ws.send(json.dumps(payload))
            print('Sent payload')
            res = await ws.recv()
            print('Received:', res)
    except Exception as e:
        print('Error during connection:', type(e).__name__, str(e))

asyncio.run(test())
