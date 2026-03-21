import { useEffect, useRef, useState } from "react";
import { FaceDetector, FilesetResolver } from "@mediapipe/tasks-vision";

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

  interface BoundingBox {
    x: number;
    y: number;
    w: number;
    h: number;
    label: string;
  }

  const [faceDetector, setFaceDetector] = useState<FaceDetector | null>(null);
  const [boundingBoxes, setBoundingBoxes] = useState<BoundingBox[]>([]);
  const [violations, setViolations] = useState<string[]>([]);
  const [status, setStatus] = useState("Loading AI Model (MediaPipe)...");
  const [isWarning, setIsWarning] = useState(false);

  const wsRef = useRef<WebSocket | null>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const animationFrameIdRef = useRef<number>(0);
  const lastVideoTimeRef = useRef<number>(-1);
  const lastReportTimeRef = useRef<number>(0);
  const prevViolationStrRef = useRef<string>("");

  // 1. Tải Model AI MediaPipe khi mount
  useEffect(() => {
    let detector: FaceDetector | null = null;
    const initAI = async () => {
      try {
        const vision = await FilesetResolver.forVisionTasks(
          "https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@latest/wasm"
        );
        detector = await FaceDetector.createFromOptions(vision, {
          baseOptions: {
            modelAssetPath: "https://storage.googleapis.com/mediapipe-models/face_detector/blaze_face_short_range/float16/1/blaze_face_short_range.tflite",
            delegate: "GPU"
          },
          runningMode: "VIDEO"
        });
        setFaceDetector(detector);
        setStatus("Connecting Camera...");
      } catch (err) {
        console.error("AI Init Error:", err);
        setStatus("Failed to load AI Model");
      }
    };
    initAI();

    return () => {
      if (detector) detector.close();
    };
  }, []);

  // 2. Kết nối WebSocket (Chỉ để gửi Log chứ không gửi Webcam)
  useEffect(() => {
    // Tự động nhận diện đường dẫn (Localhost, LAN IP, hoặc Ngrok HTTPS)
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/camera/ws`;
    const socket = new WebSocket(wsUrl);
    wsRef.current = socket;

    socket.onopen = () => {
      setStatus(prev => prev === "Connecting Camera..." ? "Connected" : prev);
    };
    socket.onclose = () => setStatus("Disconnected");

    // Yêu cầu từ Server (nếu Server muốn cảnh báo gì ngược lại thì nó gửi xuống)
    socket.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.violations && data.violations.length > 0) {
        setViolations(data.violations);
        setIsWarning(true);
      }
    };

    return () => socket.close();
  }, []);

  // 3. Vòng lặp AI Detection (chạy local trên browser)
  const processFrame = () => {
    animationFrameIdRef.current = requestAnimationFrame(processFrame);

    if (!faceDetector || !videoRef.current) return;
    if (videoRef.current.readyState !== videoRef.current.HAVE_ENOUGH_DATA) return;

    // Tối ưu để không chạy lại AI nếu video chưa có frame mới
    const videoTime = videoRef.current.currentTime;
    if (videoTime === lastVideoTimeRef.current) return;
    lastVideoTimeRef.current = videoTime;

    // Chạy AI Detector cực mượt (thường mất < 10ms trên Browser GPU)
    const startTimeMs = performance.now();
    const result = faceDetector.detectForVideo(videoRef.current, startTimeMs);
    const detections = result.detections;

    // Xử lý Bounding Boxes
    const videoW = videoRef.current.videoWidth;
    const videoH = videoRef.current.videoHeight;

    const newBoxes = detections.map((d: any) => ({
      x: (d.boundingBox?.originX || 0) / videoW * 100,
      y: (d.boundingBox?.originY || 0) / videoH * 100,
      w: (d.boundingBox?.width || 0) / videoW * 100,
      h: (d.boundingBox?.height || 0) / videoH * 100,
      label: `Face ${((d.categories[0]?.score || 0) * 100).toFixed(0)}%`
    }));
    setBoundingBoxes(newBoxes);

    // Tính toán lỗi Gian lận
    let currentViolations: string[] = [];
    let violationCodes: string[] = [];
    if (detections.length === 0) {
      currentViolations.push("Không tìm thấy khuôn mặt");
      violationCodes.push("FACE_DISAPPEARED");
    } else if (detections.length > 1) {
      currentViolations.push("Phát hiện nhiều người trong khung hình");
      violationCodes.push("MULTIPLE_FACES");
    }

    setViolations(currentViolations);
    setIsWarning(currentViolations.length > 0);

    // BÁO CÁO VI PHẠM (KÈM ẢNH BẰNG CHỨNG GỬI LÊN SERVER)
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      const now = Date.now();
      const violationStr = currentViolations.join(",");
      const isChanged = violationStr !== prevViolationStrRef.current;

      // Lúc gửi Log nếu có lỗi (hoặc định kỳ 2s nếu lỗi đang tiếp diễn để lưu thêm nhiều ảnh bằng chứng)
      if (currentViolations.length > 0 && (isChanged || now - lastReportTimeRef.current > 2000)) {

        let imageBase64 = null;
        // Trích xuất khung hình bằng chứng nhờ vào đối tượng Canvas ẩn
        if (canvasRef.current && videoRef.current) {
          const ctx = canvasRef.current.getContext("2d", { willReadFrequently: true });
          if (ctx) {
            canvasRef.current.width = 320; // Nén khung hình lại cho siêu nhẹ
            canvasRef.current.height = 240;
            ctx.drawImage(videoRef.current, 0, 0, 320, 240);
            // Cắt chuỗi prefix type của Base64 đi
            imageBase64 = canvasRef.current.toDataURL("image/jpeg", 0.6).split(",")[1];
          }
        }

        const payload = {
          type: "DETECTION_LOG",
          violations: currentViolations,
          violation_codes: violationCodes,
          person_count: detections.length,
          timestamp: now,
          image: imageBase64
        };

        wsRef.current.send(JSON.stringify(payload));

        prevViolationStrRef.current = violationStr;
        lastReportTimeRef.current = now;

      } else if (currentViolations.length === 0 && isChanged) {
        // Hết vi phạm -> Gửi báo cáo "Tẩy trắng"
        wsRef.current.send(JSON.stringify({
          type: "DETECTION_LOG",
          violations: [],
          violation_codes: [],
          person_count: detections.length,
          timestamp: now
        }));
        prevViolationStrRef.current = violationStr;
      }
    }
  };

  useEffect(() => {
    // Chỉ kích hoạt luồng Local Camera khi AI Load xong
    if (!faceDetector) return;

    const startCamera = async () => {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: false });
        if (videoRef.current) {
          videoRef.current.srcObject = stream;
        }

        setStatus("Connected (Local AI Active)");
        animationFrameIdRef.current = requestAnimationFrame(processFrame);
      } catch (err) {
        console.error("Local camera error", err);
        setStatus("Không tìm thấy Camera. Kiểm tra quyền truy cập.");
      }
    };

    startCamera();

    return () => {
      cancelAnimationFrame(animationFrameIdRef.current);
      if (videoRef.current?.srcObject) {
        const stream = videoRef.current.srcObject as MediaStream;
        stream.getTracks().forEach(t => t.stop());
      }
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [faceDetector]);

  return (
    <div className="camera-section">
      <div className="camera-label">Camera Giám Sát (AI Mode)</div>

      <div className={`camera-box ${isWarning ? "warning" : ""}`} style={{ position: "relative", overflow: "hidden" }}>
        <video
          ref={videoRef}
          autoPlay
          playsInline
          style={{
            width: "100%",
            height: "100%",
            objectFit: "cover",
            // transform: "scaleX(-1)", // Bật nếu muốn giao diện gương
            display: status.includes("Loading") || status.includes("Không") ? "none" : "block"
          }}
        />

        {(!videoRef.current?.srcObject) && (
          <div className="camera-placeholder" style={{ position: "absolute", inset: 0, display: "flex", alignItems: "center", justifyContent: "center", textAlign: "center", padding: "10px" }}>
            {status}
          </div>
        )}

        <div className="camera-overlay">LIVE (0 Delay)</div>

        {boundingBoxes.map((box, index) => (
          <div
            key={index}
            style={{
              position: "absolute",
              border: "2px solid #00ff00", // Xanh lá do chạy AI mượt, hoặc thích thì đổi màu đó
              background: "rgba(0, 255, 0, 0.1)",
              left: `${box.x}%`,
              top: `${box.y}%`,
              width: `${box.w}%`,
              height: `${box.h}%`,
              pointerEvents: "none",
              boxShadow: "0 0 10px rgba(0, 255, 0, 0.5)",
              // Rất mượt vì cập nhật ở tốc độ cao
              transition: "all 0.05s linear"
            }}
          >
            <span style={{
              position: "absolute", top: "-20px", left: "-2px", background: "#00ff00", color: "black", padding: "2px 6px", fontSize: "12px", fontWeight: 600, borderRadius: "4px 4px 4px 0"
            }}>
              {box.label}
            </span>
          </div>
        ))}

        {/* Layer 3: Khung Canvas ảo để chụp lén ảnh bằng chứng khi có lỗi */}
        <canvas ref={canvasRef} style={{ display: "none" }} />
      </div>

      <div className="cheating-status">
        <div className="cheating-header">Báo Cáo Gian Lận</div>
        {violations.length > 0 ? (
          violations.map((v) => (
            <div key={v} className="cheating-item">{v}</div>
          ))
        ) : (
          <div style={{ fontSize: "12px", color: "var(--text-subtle)", marginTop: "10px" }}>
            {status === "Loading AI Model (MediaPipe)..." ? "Đang tải Core AI..." : "Chưa phát hiện vi phạm"}
          </div>
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
