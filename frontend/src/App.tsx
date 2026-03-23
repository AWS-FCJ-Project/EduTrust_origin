import { useEffect, useRef, useState } from "react";
// @ts-ignore
import * as ort from "onnxruntime-web";

// Các lớp nhân diện quan trọng của YOLOv8 (COCO)
const TARGET_CLASSES: Record<number, string> = {
  0: "person",
  67: "cell phone",
  73: "book"
};

const FORBIDDEN_IDS = new Set([67, 73]);

// --- Components ---
const Timer = ({ durationMinutes }: { durationMinutes: number }) => {
  const [timeLeft, setTimeLeft] = useState(durationMinutes * 60);

  useEffect(() => {
    if (timeLeft <= 0) return;
    const timerId = setInterval(() => setTimeLeft((t) => t - 1), 1000);
    return () => clearInterval(timerId);
  }, [timeLeft]);

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, "0")}:${secs.toString().padStart(2, "0")}`;
  };

  return (
    <div className="timer-box">
      <div className="timer-label">Thời gian còn lại</div>
      <div className="timer-value">{formatTime(timeLeft)}</div>
    </div>
  );
};

export default function App() {
  const [status, setStatus] = useState("Initializing...");
  const [isWarning, setIsWarning] = useState(false);
  const [violations, setViolations] = useState<string[]>([]);

  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null); // Để vẽ bounding boxes
  const offscreenCanvasRef = useRef<HTMLCanvasElement | null>(null); // Để lấy frame cho YOLO
  const sessionRef = useRef<ort.InferenceSession | null>(null);
  const animationFrameIdRef = useRef<number>(0);
  const lastReportTimeRef = useRef<number>(0);
  const prevViolationStrRef = useRef<string>("");

  // --- 1. Khởi tạo YOLO ---
  useEffect(() => {
    const initYolo = async () => {
      try {
        ort.env.wasm.wasmPaths = "https://cdn.jsdelivr.net/npm/onnxruntime-web/dist/";
        const session = await ort.InferenceSession.create("/yolo26n.onnx", {
          executionProviders: ["wasm"],
          graphOptimizationLevel: "all",
        });
        sessionRef.current = session;
        setStatus("Ready");
        console.log("YOLOv8 Loaded");
      } catch (err) {
        console.error(err);
        setStatus("Model Error");
      }
    };
    initYolo();
  }, []);

  // --- 2. Inference & Processing ---
  const preprocess = (video: HTMLVideoElement) => {
    const [w, h] = [320, 320]; // Đã sửa từ 640 thành 320 khớp với mô hình của bạn
    if (!offscreenCanvasRef.current) {
      offscreenCanvasRef.current = document.createElement("canvas");
    }
    const canvas = offscreenCanvasRef.current;
    canvas.width = w;
    canvas.height = h;
    const ctx = canvas.getContext("2d", { willReadFrequently: true });
    if (!ctx) return null;

    ctx.drawImage(video, 0, 0, w, h);
    const data = ctx.getImageData(0, 0, w, h).data;
    const input = new Float32Array(w * h * 3);

    for (let i = 0; i < w * h; i++) {
      input[i] = data[i * 4] / 255;
      input[i + w * h] = data[i * 4 + 1] / 255;
      input[i + w * h * 2] = data[i * 4 + 2] / 255;
    }
    return new ort.Tensor("float32", input, [1, 3, w, h]);
  };

  const decodeOutput = (output: ort.Tensor) => {
    const data = output.data as Float32Array;
    const dims = output.dims;
    const threshold = 0.4;

    let detections: any[] = [];
    if (dims.length === 3 && dims[2] === 6) {
      detections = decodeYoloV8Custom(data, dims[1], threshold);
    } else if (dims[1] === 84) {
      detections = decodeYoloV8Standard(data, dims[2], threshold);
    }

    if (debugRef.current) {
      console.log("--- FINAL DETECTION DEBUG ---");
      console.log("Shape:", dims);
      console.log("Raw detections above threshold:", detections.length);
      debugRef.current = false;
    }

    return nms(detections);
  };

  const nms = (boxes: any[]) => {
    if (boxes.length === 0) return [];
    boxes.sort((a, b) => b.conf - a.conf);
    const result = [];
    while (boxes.length > 0) {
      const best = boxes.shift();
      result.push(best);
      boxes = boxes.filter(b => calculateIoU(best.rect, b.rect) < 0.45);
    }
    return result;
  };

  const calculateIoU = (b1: number[], b2: number[]) => {
    const x1 = Math.max(b1[0], b2[0]);
    const y1 = Math.max(b1[1], b2[1]);
    const x2 = Math.min(b1[2], b2[2]);
    const y2 = Math.min(b1[3], b2[3]);
    const inter = Math.max(0, x2 - x1) * Math.max(0, y2 - y1);
    const area1 = (b1[2] - b1[0]) * (b1[3] - b1[1]);
    const area2 = (b2[2] - b2[0]) * (b2[3] - b2[1]);
    return inter / (area1 + area2 - inter);
  };

  const [metrics, setMetrics] = useState({ time: 0, rawCount: 0 });

  const debugRef = useRef(false);

  const runModel = async () => {
    if (!videoRef.current || !sessionRef.current || videoRef.current.videoWidth === 0) {
      animationFrameIdRef.current = requestAnimationFrame(runModel);
      return;
    }

    try {
      const start = performance.now();
      const tensor = preprocess(videoRef.current);
      if (!tensor) throw new Error("Preprocessing failed");

      const outputs = await sessionRef.current.run({ images: tensor });
      const output = outputs.output0 || Object.values(outputs)[0];

      if (debugRef.current) {
        console.log("RAW Output Keys:", Object.keys(outputs));
        console.log("SELECTED Output Dims:", output.dims);
        console.log("FIRST 20 values:", (output.data as Float32Array).slice(0, 20));
        debugRef.current = false; // Reset sau khi log
      }

      const detections = decodeOutput(output);
      const end = performance.now();

      setMetrics({ time: Math.round(end - start), rawCount: detections.length });
      drawBoxes(detections);
      handleViolations(detections);
    } catch (e) {
      console.error("Inference Error:", e);
    }
    animationFrameIdRef.current = requestAnimationFrame(runModel);
  };

  const drawBoxes = (detections: any[]) => {
    const canvas = canvasRef.current;
    const video = videoRef.current;
    if (!canvas || !video) return;

    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    ctx.clearRect(0, 0, canvas.width, canvas.height);
    detections.forEach(det => {
      const [x1, y1, x2, y2] = det.rect;
      // Scale coordinates from 320x320 to actual video size
      const sx = canvas.width / 320;
      const sy = canvas.height / 320;

      // Mirror coordinates to match scaleX(-1) video
      const rx = canvas.width - (x2 * sx);
      const ry = y1 * sy;
      const rw = (x2 - x1) * sx;
      const rh = (y2 - y1) * sy;

      ctx.strokeStyle = det.classId === 0 ? "#4ade80" : "#f87171";
      ctx.lineWidth = 3;
      ctx.strokeRect(rx, ry, rw, rh);

      ctx.fillStyle = det.classId === 0 ? "#4ade80" : "#f87171";
      ctx.font = "bold 16px Sora";
      ctx.fillText(`${det.label} ${(det.conf * 100).toFixed(0)}%`, rx, ry - 8);
    });
  };

  const handleViolations = (detections: any[]) => {
    const now = Date.now();
    const personCount = detections.filter((d) => d.classId === 0).length;
    const forbidden = detections.filter((d) => FORBIDDEN_IDS.has(d.classId));

    const { currentViolations, alertCodes } = getViolationDetails(
      personCount,
      forbidden
    );

    setViolations(currentViolations);
    setIsWarning(currentViolations.length > 0);

    const vStr = alertCodes.join(",");
    const isChanged = vStr !== prevViolationStrRef.current;

    if (
      currentViolations.length > 0 &&
      (isChanged || now - lastReportTimeRef.current > 4000)
    ) {
      reportViolation(currentViolations, alertCodes, personCount, now);
      prevViolationStrRef.current = vStr;
      lastReportTimeRef.current = now;
    } else if (currentViolations.length === 0 && isChanged) {
      sendClearLog(now);
      prevViolationStrRef.current = "";
    }
  };

  const sendClearLog = (ts: number) => {
    fetch("/camera/log", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "ngrok-skip-browser-warning": "69420",
      },
      body: JSON.stringify({
        type: "DETECTION_LOG",
        violations: [],
        timestamp: ts,
      }),
    });
  };

  const reportViolation = (vList: string[], codes: string[], count: number, ts: number) => {
    const video = videoRef.current;
    if (!video) return;

    // Capture small snapshot for evidence
    const snap = document.createElement("canvas");
    snap.width = 320;
    snap.height = 240;
    snap.getContext("2d")?.drawImage(video, 0, 0, 320, 240);
    const b64 = snap.toDataURL("image/jpeg", 0.6).split(",")[1];

    fetch("/camera/log", {
      method: "POST",
      headers: { "Content-Type": "application/json", "ngrok-skip-browser-warning": "true" },
      body: JSON.stringify({
        type: "DETECTION_LOG",
        violations: vList,
        violation_codes: codes,
        person_count: count,
        timestamp: ts,
        image: b64
      })
    });
  };

  useEffect(() => {
    navigator.mediaDevices.getUserMedia({ video: true, audio: false }).then(stream => {
      if (videoRef.current) videoRef.current.srcObject = stream;
      animationFrameIdRef.current = requestAnimationFrame(runModel);
    });
    return () => cancelAnimationFrame(animationFrameIdRef.current);
  }, []);

  return (
    <div className="exam-layout app">
      <aside className="sidebar">
        <div className="sidebar-section">
          <h2 style={{ fontSize: '18px', margin: 0, fontWeight: 700 }}>AWS Proctor AI</h2>
          <div className={`status-pill ${status === 'Ready' ? 'online busy' : 'offline'}`} style={{ marginTop: '8px' }}>
            <div className="status-dot" />
            <span>AI: {status} ({metrics.time}ms)</span>
          </div>
        </div>

        <Timer durationMinutes={60} />

        <div className="camera-section">
          <div className="camera-label">LIVE PROCTORING VIEW</div>
          <div className={`camera-box ${isWarning ? 'warning' : ''}`}>
            <video ref={videoRef} autoPlay muted playsInline style={{ transform: "scaleX(-1)" }} />
            <canvas ref={canvasRef} style={{
              position: "absolute",
              top: 0,
              left: 0,
              width: "100%",
              height: "100%",
              pointerEvents: "none"
            }} />
            <div className="camera-overlay">SECURE_MONITORING: ENABLED</div>
          </div>
          <div style={{ fontSize: '10px', color: 'var(--text-subtle)', display: 'flex', justifyContent: 'space-between' }}>
            <span>Detections: {metrics.rawCount}</span>
            <button
              type="button"
              onClick={() => (debugRef.current = true)}
              style={{
                cursor: "pointer",
                color: "var(--accent)",
                background: "none",
                border: "none",
                padding: 0,
                font: "inherit",
              }}
            >
              [LOG AI]
            </button>
          </div>
        </div>

        <div className="cheating-status">
          <div className="cheating-header">⚠️ DẤU HIỆU VI PHẠM</div>
          <div className="tool-events-list">
            {violations.map((v, i) => (
              <div
                key={`${v}-${i}`}
                className="cheating-item"
                style={{ color: "#f87171" }}
              >
                {v}
              </div>
            ))}
            {violations.length === 0 && <div className="cheating-item" style={{ color: '#4ade80' }}>Chưa phát hiện vi phạm</div>}
          </div>
        </div>

        <button className="submit-btn" onClick={() => alert("Bài thi đã được gửi!")}>NỘP BÀI THI</button>
      </aside>

      <main className="main-content">
        <div style={{ padding: '40px', color: '#111', height: '100%', overflowY: 'auto' }}>
          <h1 style={{ color: '#000', marginBottom: '20px', fontSize: '32px' }}>Final Assessment: AWS Cloud Specialist</h1>
          <hr style={{ border: '0', borderTop: '1px solid #eee', marginBottom: '30px' }} />

          <div style={{ fontSize: '18px', lineHeight: '1.6' }}>
            <p><strong>Câu 1:</strong> Dịch vụ nào của AWS cung cấp khả năng tự động mở rộng tài nguyên dựa trên nhu cầu sử dụng?</p>
            <div style={{ margin: '20px 0' }}>
              <label style={{ display: 'block', margin: '10px 0' }}><input type="radio" name="q1" /> A. Amazon S3</label>
              <label style={{ display: 'block', margin: '10px 0' }}><input type="radio" name="q1" /> B. AWS Auto Scaling</label>
              <label style={{ display: 'block', margin: '10px 0' }}><input type="radio" name="q1" /> C. Amazon RDS</label>
              <label style={{ display: 'block', margin: '10px 0' }}><input type="radio" name="q1" /> D. AWS CloudFormation</label>
            </div>
          </div>

          <div style={{
            marginTop: '60px',
            padding: '20px',
            backgroundColor: '#fff9db',
            borderRadius: '8px',
            border: '1px solid #ffe066',
            color: '#666',
            fontSize: '14px'
          }}>
            Lưu ý: Hệ thống giám sát AI đang hoạt động. Vui lòng không sử dụng điện thoại và tập trung vào màn hình làm bài.
          </div>
        </div>
      </main>
    </div>
  );
}

/** Helper Functions for AI Processing */
function decodeYoloV8Custom(
  data: Float32Array,
  count: number,
  threshold: number
) {
  const detections = [];
  for (let i = 0; i < count; i++) {
    const conf = data[i * 6 + 4];
    const cls = Math.round(data[i * 6 + 5]);
    if (conf > threshold && TARGET_CLASSES[cls]) {
      detections.push({
        classId: cls,
        label: TARGET_CLASSES[cls],
        conf: conf,
        rect: [
          data[i * 6 + 0],
          data[i * 6 + 1],
          data[i * 6 + 2],
          data[i * 6 + 3],
        ],
      });
    }
  }
  return detections;
}

function decodeYoloV8Standard(
  data: Float32Array,
  cols: number,
  threshold: number
) {
  const detections = [];
  for (let j = 0; j < cols; j++) {
    let maxConf = 0;
    let classId = -1;
    for (const id of [0, 67, 73]) {
      const conf = data[(id + 4) * cols + j];
      if (conf > maxConf) {
        maxConf = conf;
        classId = id;
      }
    }
    if (maxConf > threshold) {
      const xc = data[0 * cols + j],
        yc = data[1 * cols + j],
        w = data[2 * cols + j],
        h = data[3 * cols + j];
      detections.push({
        classId,
        label: TARGET_CLASSES[classId],
        conf: maxConf,
        rect: [xc - w / 2, yc - h / 2, xc + w / 2, yc + h / 2],
      });
    }
  }
  return detections;
}

function getViolationDetails(personCount: number, forbidden: any[]) {
  const currentViolations: string[] = [];
  const alertCodes: string[] = [];

  if (personCount === 0) {
    currentViolations.push("Không thấy học sinh");
    alertCodes.push("FACE_DISAPPEARED");
  } else if (personCount > 1) {
    currentViolations.push("Nghi ngờ có người lạ");
    alertCodes.push("MULTIPLE_FACES");
  }

  if (forbidden.length > 0) {
    currentViolations.push(`Vật cấm: ${forbidden[0].label}`);
    alertCodes.push("OBJECT_DETECTED");
  }

  return { currentViolations, alertCodes };
}
