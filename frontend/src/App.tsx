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

  useEffect(() => {
    const wsUrl = "ws://localhost:8000/camera/ws";
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

  // Cấu hình Camera: Để trống "" để dùng Webcam local, hoặc điền URL (ví dụ: "http://192.168.1.177")
  const IP_CAMERA_URL = "http://192.168.1.177:8554";

  const captureAndSend = (source: HTMLVideoElement | HTMLImageElement) => {
    if (wsRef.current?.readyState !== WebSocket.OPEN || !canvasRef.current) return;

    const context = canvasRef.current.getContext("2d");
    if (!context) return;

    if (source instanceof HTMLVideoElement) {
      canvasRef.current.width = source.videoWidth;
      canvasRef.current.height = source.videoHeight;
    } else {
      canvasRef.current.width = source.width;
      canvasRef.current.height = source.height;
    }

    context.drawImage(source, 0, 0);
    canvasRef.current.toBlob((blob) => {
      if (blob) wsRef.current?.send(blob);
    }, "image/jpeg", 0.7);
  };

  useEffect(() => {
    const startCamera = async () => {
      if (IP_CAMERA_URL) {
        setStatus(`Using IP Cam: ${IP_CAMERA_URL}`);
        const interval = setInterval(() => {
          const img = new Image();
          img.crossOrigin = "Anonymous";
          img.src = `${IP_CAMERA_URL}/snapshot.jpg?t=${Date.now()}`;
          img.onload = () => captureAndSend(img);
        }, 500);
        return () => clearInterval(interval);
      }

      try {
        const stream = await navigator.mediaDevices.getUserMedia({ video: true });
        if (videoRef.current) videoRef.current.srcObject = stream;

        const interval = setInterval(() => {
          if (videoRef.current) captureAndSend(videoRef.current);
        }, 300);

        return () => clearInterval(interval);
      } catch (err) {
        console.error("Local camera error", err);
        setStatus("Không tìm thấy Camera. Vui lòng kiểm tra quyền truy cập.");
      }
    };

    startCamera();
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
