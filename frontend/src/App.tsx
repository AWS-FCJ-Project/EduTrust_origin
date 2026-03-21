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
  const [visualizedFrame, setVisualizedFrame] = useState<string | null>(null);
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
      if (data.visualized_frame) {
        setVisualizedFrame(data.visualized_frame);
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

    // Chỉ check motion và xử lý khi đạt mốc tối thiểu 500ms (giới hạn 2 FPS)
    if (timeSinceLastSend < 500) return;

    const context = canvasRef.current.getContext("2d", { willReadFrequently: true });
    if (!context) return;

    // Resize tối ưu
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
        shouldSend = true;
      }
    }

    if (shouldSend) {
      canvasRef.current.toBlob((blob) => {
        if (blob) wsRef.current?.send(blob);
      }, "image/jpeg", 0.6); // Ép nén định dạng thành JPEG thay vì PNG

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
      <div className={`camera-box ${isWarning ? "warning" : ""}`}>
        {visualizedFrame ? (
          <img src={`data:image/jpeg;base64,${visualizedFrame}`} alt="Detection" />
        ) : (
          <div className="camera-placeholder">
            {status === "Connected" ? "Đang tải luồng camera..." : status}
          </div>
        )}
        <div className="camera-overlay">LIVE</div>
        <video ref={videoRef} autoPlay playsInline style={{ display: "none" }}>
          <track kind="captions" />
        </video>
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
