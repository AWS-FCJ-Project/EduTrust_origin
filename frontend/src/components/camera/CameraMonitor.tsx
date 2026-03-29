"use client";

import { useEffect, useRef, useState } from "react";
import * as ort from "onnxruntime-web";
import { AlertCircle, CheckCircle2 } from 'lucide-react';

const TARGET_CLASSES: Record<number, string> = {
    0: "person",
    67: "cell phone",
    73: "book"
};

const FORBIDDEN_IDS = new Set([67, 73]);

export default function CameraMonitor({ 
    onViolation, 
    onStatusChange,
    isCheck = false,
    isActive = true,
    examId = "unknown",
    studentId = "unknown"
}: { 
    onViolation?: (violations: string[]) => void,
    onStatusChange?: (status: string) => void,
    isCheck?: boolean,
    isActive?: boolean,
    examId?: string,
    studentId?: string
}) {
    const [status, setStatus] = useState("Initializing...");
    const [isWarning, setIsWarning] = useState(false);
    const [violations, setViolations] = useState<string[]>([]);
    const [metrics, setMetrics] = useState({ time: 0, rawCount: 0 });

    const onViolationRef = useRef(onViolation);
    const onStatusChangeRef = useRef(onStatusChange);
    const isCheckRef = useRef(isCheck);
    const isActiveRef = useRef(isActive);
    const idsRef = useRef({ examId, studentId });

    useEffect(() => { onViolationRef.current = onViolation; }, [onViolation]);
    useEffect(() => { onStatusChangeRef.current = onStatusChange; }, [onStatusChange]);
    useEffect(() => { isCheckRef.current = isCheck; }, [isCheck]);
    useEffect(() => { 
        isActiveRef.current = isActive; 
        if (!isActive) {
            cancelAnimationFrame(animationFrameIdRef.current);
            setStatus("Stopped");
        }
    }, [isActive]);
    useEffect(() => { idsRef.current = { examId, studentId }; }, [examId, studentId]);

    useEffect(() => {
        if (onStatusChangeRef.current) onStatusChangeRef.current(status);
    }, [status]);

    const videoRef = useRef<HTMLVideoElement>(null);
    const offscreenCanvasRef = useRef<HTMLCanvasElement | null>(null);
    const sessionRef = useRef<ort.InferenceSession | null>(null);
    const animationFrameIdRef = useRef<number>(0);
    const lastReportTimeRef = useRef<number>(0);
    const prevViolationStrRef = useRef<string>("");
    const violationCountRef = useRef<number>(0);

    // --- 1. Load Model ---
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
                console.log("YOLOv8 Loaded in CameraMonitor");
            } catch (err) {
                console.error(err);
                setStatus("Model Error");
            }
        };
        initYolo();

        return () => {
            cancelAnimationFrame(animationFrameIdRef.current);
        };
    }, []);

    // --- 2. Camera Setup ---
    useEffect(() => {
        let stream: MediaStream | null = null;
        if (status === "Ready" && isActive) {
            navigator.mediaDevices.getUserMedia({ video: true, audio: false }).then(s => {
                stream = s;
                if (videoRef.current) videoRef.current.srcObject = s;
                animationFrameIdRef.current = requestAnimationFrame(runModel);
            }).catch(err => {
                console.error("Camera access denied", err);
                setStatus("Camera Error");
            });
        }

        return () => {
            cancelAnimationFrame(animationFrameIdRef.current);
            if (stream) {
                stream.getTracks().forEach(track => track.stop());
            }
        };
    }, [status, isActive]);

    // --- 3. Processing Logic ---
    const preprocess = (video: HTMLVideoElement) => {
        const [w, h] = [320, 320];
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

        return nms(detections);
    };

    const decodeYoloV8Custom = (data: Float32Array, count: number, threshold: number) => {
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
    };

    const decodeYoloV8Standard = (data: Float32Array, cols: number, threshold: number) => {
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
                const xc = data[0 * cols + j], yc = data[1 * cols + j], w = data[2 * cols + j], h = data[3 * cols + j];
                detections.push({
                    classId,
                    label: TARGET_CLASSES[classId],
                    conf: maxConf,
                    rect: [xc - w / 2, yc - h / 2, xc + w / 2, yc + h / 2],
                });
            }
        }
        return detections;
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
        const x1 = Math.max(b1[0], b2[0]), y1 = Math.max(b1[1], b2[1]), x2 = Math.min(b1[2], b2[2]), y2 = Math.min(b1[3], b2[3]);
        const inter = Math.max(0, x2 - x1) * Math.max(0, y2 - y1);
        const area1 = (b1[2] - b1[0]) * (b1[3] - b1[1]), area2 = (b2[2] - b2[0]) * (b2[3] - b2[1]);
        return inter / (area1 + area2 - inter);
    };

    const runModel = async () => {
        if (!videoRef.current || !sessionRef.current || videoRef.current.videoWidth === 0 || !isActiveRef.current) {
            if (isActiveRef.current) animationFrameIdRef.current = requestAnimationFrame(runModel);
            return;
        }

        try {
            const start = performance.now();
            const tensor = preprocess(videoRef.current);
            if (tensor) {
                const outputs = await sessionRef.current.run({ images: tensor });
                const output = outputs.output0 || Object.values(outputs)[0];
                const detections = decodeOutput(output);
                const end = performance.now();

                setMetrics({ time: Math.round(end - start), rawCount: detections.length });
                handleViolations(detections);
            }
        } catch (e) {
            console.error("Inference Error:", e);
        }
        if (isActiveRef.current) animationFrameIdRef.current = requestAnimationFrame(runModel);
    };

    const handleViolations = (detections: any[]) => {
        const now = Date.now();
        const personCount = detections.filter((d) => d.classId === 0).length;
        const forbidden = detections.filter((d) => FORBIDDEN_IDS.has(d.classId));

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

        setViolations(currentViolations);
        setIsWarning(!isCheckRef.current && currentViolations.length > 0);

        const vStr = alertCodes.join(",");
        const isChanged = vStr !== prevViolationStrRef.current;

        if (currentViolations.length > 0 && (isChanged || now - lastReportTimeRef.current > 5000)) {
            if (!isCheckRef.current) reportViolation(currentViolations, alertCodes, personCount, now, detections);
            if (onViolationRef.current) onViolationRef.current(currentViolations);
            prevViolationStrRef.current = vStr;
            lastReportTimeRef.current = now;
        } else if (currentViolations.length === 0 && isChanged) {
            if (!isCheckRef.current) sendClearLog(now);
            prevViolationStrRef.current = "";
        }
    };

    const reportViolation = (vList: string[], codes: string[], count: number, ts: number, detections: any[]) => {
        const video = videoRef.current;
        if (!video || !isActiveRef.current) return;

        const currentIds = idsRef.current;
        // Safety guard: Don't report if identity is not yet established
        if (currentIds.examId === "unknown" || currentIds.studentId === "unknown") {
            console.warn("[CameraMonitor] Identity not ready, skipping report.");
            return;
        }

        const snap = document.createElement("canvas");
        snap.width = 320; snap.height = 240;
        const ctx = snap.getContext("2d");
        if (!ctx) return;
        ctx.drawImage(video, 0, 0, 320, 240);

        detections.forEach((det: any) => {
            const [x1, y1, x2, y2] = det.rect;
            const sx = 320 / 320, sy = 240 / 320;
            const rx = x1 * sx, ry = y1 * sy, rw = (x2 - x1) * sx, rh = (y2 - y1) * sy;
            ctx.strokeStyle = det.classId === 0 ? "#4ade80" : "#f87171";
            ctx.lineWidth = 2;
            ctx.strokeRect(rx, ry, rw, rh);
        });

        let b64: string | null = null;
        if (violationCountRef.current < 4) {
            b64 = snap.toDataURL("image/jpeg", 0.6).split(",")[1];
        }
        const apiUrl = process.env.NEXT_PUBLIC_API_URL;

        fetch(`${apiUrl}/camera/log`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                type: "DETECTION_LOG",
                violations: vList,
                violation_codes: codes,
                person_count: count,
                timestamp: ts,
                image: b64,
                exam_id: currentIds.examId,
                student_id: currentIds.studentId
            })
        }).then(res => {
            if (res.ok && b64) violationCountRef.current += 1;
        }).catch(e => console.warn("Could not send log to backend:", e));
    };

    const sendClearLog = (ts: number) => {
        if (!isActiveRef.current) return;
        const apiUrl = process.env.NEXT_PUBLIC_API_URL;
        const currentIds = idsRef.current;
        
        if (currentIds.examId === "unknown" || currentIds.studentId === "unknown") return;

        fetch(`${apiUrl}/camera/log`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ 
                type: "DETECTION_LOG", 
                violations: [], 
                timestamp: ts,
                exam_id: currentIds.examId,
                student_id: currentIds.studentId
            }),
        }).catch(() => {});
    };

    return (
        <div className="flex flex-col gap-3">
            <div className="flex items-center justify-between mb-1">
                <span className="text-[10px] font-bold text-gray-500 uppercase flex items-center gap-1">
                    <span className={`w-2 h-2 rounded-full ${status === "Ready" ? (isWarning ? "bg-red-500 animate-pulse" : "bg-green-500 animate-pulse") : "bg-orange-50"}`}></span> 
                    Camera giám sát
                </span>
                {!isCheck && (
                    <span className="text-[10px] text-gray-400 font-mono">
                        {status === "Ready" ? (metrics.time > 0 ? `LATENCY: ${metrics.time}ms` : "AI READY") : status}
                    </span>
                )}
            </div>
            
            <div className={`aspect-video rounded-xl relative overflow-hidden flex items-center justify-center border-2 shadow-lg transition-colors duration-300 ${
                isWarning ? "border-red-500 bg-red-50" : "border-white bg-black"
            }`}>
                <video
                    ref={videoRef}
                    autoPlay
                    muted
                    playsInline
                    className="w-full h-full object-cover"
                    style={{ transform: "scaleX(-1)" }}
                />
                <div className="absolute top-2 left-2 text-[8px] text-white/50 font-mono bg-black/40 px-1 rounded">USER_CAM_PROCTOR</div>
                
                {isWarning && (
                    <div className="absolute inset-0 bg-red-500/10 pointer-events-none animate-pulse" />
                )}
            </div>

            {!isCheck && isWarning && (
                <div className="bg-red-50 border border-red-100 rounded-lg p-2 animate-in fade-in slide-in-from-top-1">
                    <div className="flex items-center gap-1.5 text-red-600 mb-1">
                        <AlertCircle size={12} />
                        <span className="text-[10px] font-black uppercase tracking-wider">Cảnh báo vi phạm</span>
                    </div>
                    <div className="space-y-1">
                        {violations.map((v, i) => (
                            <div key={i} className="flex items-center gap-1.5 text-red-700 font-bold text-[10px]">
                                <div className="w-1 h-1 rounded-full bg-red-500" />
                                {v}
                            </div>
                        ))}
                    </div>
                </div>
            )}
            
            {!isCheck && !isWarning && status === "Ready" && (
                <div className="flex items-center gap-1.5 text-green-600 px-2">
                    <CheckCircle2 size={12} />
                    <span className="text-[10px] font-bold">Hệ thống an toàn</span>
                </div>
            )}
        </div>
    );
}
