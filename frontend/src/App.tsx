import { useEffect, useRef, useState } from "react";

// --- Components ---

interface TimerProps {
  readonly durationMinutes?: number;
}

function Timer({ durationMinutes = 60 }: TimerProps) {
  const [timeLeft, setTimeLeft] = useState(durationMinutes * 60);

  useEffect(() => {
    if (timeLeft <= 0) return;
    const timer = setInterval(() => {
      setTimeLeft((prev) => prev - 1);
    }, 1000);
    return () => clearInterval(timer);
  }, [timeLeft]);

  const minutes = Math.floor(timeLeft / 60);
  const seconds = timeLeft % 60;

  return (
    <div className="timer-box">
      <div className="timer-label">Thời gian còn lại</div>
      <div className="timer-value">
        {String(minutes).padStart(2, "0")}:{String(seconds).padStart(2, "0")}
      </div>
    </div>
  );
}

function CameraDetection() {
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  // Thay vì lưu ảnh Base64, ta sẽ lưu danh sách các Bounding Boxes từ Backend
  interface BoundingBox {
    x: number; // Tỷ lệ % (0-100) tương ứng với chiều rộng gốc (Ví dụ 320px)
    y: number; // Tỷ lệ % (0-100)
    w: number; // Width %
    h: number; // Height %
    label: string;
  }
  const [boundingBoxes, setBoundingBoxes] = useState<BoundingBox[]>([]);
  const [violations, setViolations] = useState<string[]>([]);
  const [status, setStatus] = useState("Connecting...");
  const [isWarning, setIsWarning] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);

  // States for frame optimization
  const previousImageDataRef = useRef<ImageData | null>(null);
  const lastSendTimeRef = useRef<number>(0);
  const animationFrameIdRef = useRef<number>(0);

  useEffect(() => {
    const isLocalDev = window.location.port === "5173";
    const defaultWsUrl = `${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${window.location.host}`;
    const wsBase = isLocalDev ? (import.meta.env.VITE_WS_URL || "ws://localhost:8000") : defaultWsUrl;
    const wsUrl = `${wsBase}/camera/ws`;
    const socket = new WebSocket(wsUrl);
    wsRef.current = socket;

    socket.onopen = () => setStatus("Connected");
    socket.onclose = () => setStatus("Disconnected");
    socket.onmessage = (event) => {
      const data = JSON.parse(event.data);

      // 👉 BACKEND BÂY GIỜ CHỈ CẦN TRẢ VỀ TOẠ ĐỘ THAY VÌ ẢNH!
      // Ví dụ Backend trả về field: "boxes": [{ "x": 10, "y": 20, "w": 40, "h": 50, "label": "Nhìn đi nơi khác" }]
      if (data.boxes) {
        setBoundingBoxes(data.boxes);
      } else {
        // Tự động clear box nếu an toàn
        setBoundingBoxes([]);
      }

      if (data.violations) {
        setViolations(data.violations);
        setIsWarning(data.violations.length > 0 || data.forbidden_detected);
      }
    };

    return () => socket.close();
  }, []);

  // Cấu hình Camera: Để trống "" để dùng Webcam local, hoặc điền URL vào .env (VITE_CAMERA_URL)
  const IP_CAMERA_URL = import.meta.env.VITE_CAMERA_URL || "";

  // 1. Thuật toán so sánh Pixel
  const checkMotion = (currentImageData: ImageData, previousImageData: ImageData | null) => {
    if (!previousImageData) return true; // Frame đầu luôn coi là có chuyển động

    let diffPixels = 0;
    const data1 = currentImageData.data;
    const data2 = previousImageData.data;

    // Nhảy bước 16 để tăng tốc độ tính toán
    for (let i = 0; i < data1.length; i += 16) {
      const diffR = Math.abs(data1[i] - data2[i]);
      const diffG = Math.abs(data1[i + 1] - data2[i + 1]);
      const diffB = Math.abs(data1[i + 2] - data2[i + 2]);

      // Nếu tông màu chênh > 30, tính là pixel bị thay đổi
      if (diffR + diffG + diffB > 30) {
        diffPixels++;
      }
    }

    const checkedPixels = (data1.length / 4) / 4;
    const diffPercentage = (diffPixels / checkedPixels) * 100;
    return diffPercentage > 5; // Ngưỡng chuyển động 5%
  };

  // 2. Vòng lặp tối ưu WebCam
  const processFrame = () => {
    animationFrameIdRef.current = requestAnimationFrame(processFrame);

    if (wsRef.current?.readyState !== WebSocket.OPEN) return;
    if (!videoRef.current || !canvasRef.current) return;
    if (videoRef.current.readyState !== videoRef.current.HAVE_ENOUGH_DATA) return;

    const currentTime = Date.now();
    const timeSinceLastSend = currentTime - lastSendTimeRef.current;

    // Giới hạn max 2 FPS
    if (timeSinceLastSend < 500) return;

    const context = canvasRef.current.getContext("2d", { willReadFrequently: true });
    if (!context) return;

    // Resize cứng xuống 320x240 để siêu tiết kiệm băng thông
    canvasRef.current.width = 320;
    canvasRef.current.height = 240;

    context.drawImage(videoRef.current, 0, 0, 320, 240);
    const currentImageData = context.getImageData(0, 0, 320, 240);

    const hasMotion = checkMotion(currentImageData, previousImageDataRef.current);
    let shouldSend = false;

    if (hasMotion) {
      shouldSend = true; // 2 FPS
    } else {
      // Nếu muốn "CHỈ" gửi khi có chuyển động, hãy xóa cụm if bên dưới. 
      // Ở đây giữ lại 1 FPS (1000ms) để giữ kết nối heartbeat.
      if (timeSinceLastSend >= 1000) {
        shouldSend = true; // Giữ kết nối heartbeat ở 1 FPS
      }
    }

    if (shouldSend) {
      canvasRef.current.toBlob((blob) => {
        if (blob) wsRef.current?.send(blob);
      }, "image/jpeg", 0.6); // Ép nén JPEG

      lastSendTimeRef.current = currentTime;
      previousImageDataRef.current = currentImageData;
    }
  };

  // 3. Xử lý IP Camera (Nếu có)
  const processIPCamera = () => {
    if (wsRef.current?.readyState !== WebSocket.OPEN || !canvasRef.current) return;
    const img = new Image();
    img.crossOrigin = "Anonymous";
    img.src = `${IP_CAMERA_URL}/snapshot.jpg?t=${Date.now()}`;
    img.onload = () => {
      const context = canvasRef.current?.getContext("2d");
      if (!context || !canvasRef.current) return;
      canvasRef.current.width = 320;
      canvasRef.current.height = 240;
      context.drawImage(img, 0, 0, 320, 240);
      canvasRef.current.toBlob((blob) => {
        if (blob) wsRef.current?.send(blob);
      }, "image/jpeg", 0.6);
    };
  };

  useEffect(() => {
    let intervalId: number;

    const startCamera = async () => {
      // Trường hợp IP Camera
      if (IP_CAMERA_URL) {
        setStatus(`Using IP Cam: ${IP_CAMERA_URL}`);
        intervalId = globalThis.setInterval(processIPCamera, 1000);
        return;
      }

      // Trường hợp Laptop WebCam local
      try {
        const stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: false });
        if (videoRef.current) videoRef.current.srcObject = stream;

        // Thay vì setInterval 300ms, ta dùng requestAnimationFrame kết hợp Pixel Diff
        animationFrameIdRef.current = requestAnimationFrame(processFrame);
      } catch (err) {
        console.error("Local camera error", err);
        setStatus("Không tìm thấy Camera. Vui lòng kiểm tra quyền truy cập.");
      }
    };

    startCamera();
    return () => {
      clearInterval(intervalId);
      cancelAnimationFrame(animationFrameIdRef.current);
    };
  }, [IP_CAMERA_URL]);

  return (
    <div className="camera-section">
      <div className="camera-label">Camera Giám Sát</div>
      {/* Container camera với position relative để chứa layer chồng */}
      <div className={`camera-box ${isWarning ? "warning" : ""}`} style={{ position: "relative", overflow: "hidden" }}>

        {/* Layer 1: Luồng Camera Cực Mượt 60 FPS */}
        <video
          ref={videoRef}
          autoPlay
          playsInline
          style={{
            width: "100%",
            height: "100%",
            objectFit: "cover",
            // transform: "scaleX(-1)", // Bật dòng này nếu muốn quay lại hiệu ứng gương
            display: status === "Connecting..." ? "none" : "block"
          }}
        />

        {/* Lớp chờ (Loading) */}
        {!videoRef.current?.srcObject && status !== "Connected" && (
          <div className="camera-placeholder" style={{ position: "absolute", inset: 0, display: "flex", alignItems: "center", justifyContent: "center" }}>
            {status}
          </div>
        )}

        <div className="camera-overlay">LIVE</div>

        {/* Layer 2: Vẽ các khung cảnh báo (Bounding Boxes) */}
        {boundingBoxes.map((box, index) => (
          <div
            key={index}
            style={{
              position: "absolute",
              border: "2px solid #ff4444",
              background: "rgba(255, 68, 68, 0.15)",
              left: `${box.x}%`,
              top: `${box.y}%`,
              width: `${box.w}%`,
              height: `${box.h}%`,
              pointerEvents: "none", // Để không chặn nhấp chuột hoặc focus
              boxShadow: "0 0 10px rgba(255, 0, 0, 0.5)",
              transition: "all 0.3s ease-out" // Cực kỳ mượt nhờ animation của CSS
            }}
          >
            {box.label && (
              <span style={{
                position: "absolute",
                top: "-20px",
                left: "-2px",
                background: "#ff4444",
                color: "white",
                padding: "2px 6px",
                fontSize: "12px",
                fontWeight: 600,
                borderRadius: "4px 4px 4px 0"
              }}>
                {box.label}
              </span>
            )}
          </div>
        ))}

        {/* Layer 3: Khung Canvas ẩn - Cỗ máy cắt Frame ở dưới ngầm */}
        <canvas ref={canvasRef} style={{ display: "none" }} />
      </div>

      <div className="cheating-status">
        <div className="cheating-header">Báo Cáo Gian Lận</div>
        {violations.length > 0 ? (
          violations.map((v) => (
            <div key={v} className="cheating-item">{v}</div>
          ))
        ) : (
          <div style={{ fontSize: "12px", color: "var(--text-subtle)" }}>Chưa phát hiện vi phạm</div>
        )}
      </div>
    </div>
  );
}

// --- Main App ---

export default function App() {
  return (
    <div className="exam-layout">
      {/* Sidebar */}
      <aside className="sidebar">
        <div className="sidebar-section">
          <Timer durationMinutes={60} />
          <button
            className="submit-btn"
            onClick={() => alert("Bài làm đã được gửi!")}
          >
            Nộp bài
          </button>
        </div>

        <CameraDetection />
      </aside>

      {/* Main Content (Empty for now) */}
      <main className="main-content">
        <div style={{
          height: "100%",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          color: "#ddd"
        }}>
          <div style={{ textAlign: "center", color: "#666" }}>
            <h2 style={{ fontFamily: "Space Grotesk", marginBottom: "8px" }}>Khu vực làm bài</h2>
            <p>Nội dung đề thi sẽ hiển thị tại đây.</p>
          </div>
        </div>
      </main>
    </div>
  );
}
