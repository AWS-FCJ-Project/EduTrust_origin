"use client";

import { useEffect, useRef, useState } from "react";
import * as ort from "onnxruntime-web";
import { Camera, AlertCircle, CheckCircle2, ShieldCheck, Activity } from 'lucide-react';

const TARGET_CLASSES: Record<number, string> = {
    0: "person",
    67: "cell phone",
    73: "book"
};

const FORBIDDEN_IDS = new Set([67, 73]);

export default function CameraTestPage() {
    const [status, setStatus] = useState("Initializing...");
    const [isWarning, setIsWarning] = useState(false);
    const [violations, setViolations] = useState<string[]>([]);
    const [metrics, setMetrics] = useState({ time: 0, rawCount: 0 });

    const videoRef = useRef<HTMLVideoElement>(null);
    const offscreenCanvasRef = useRef<HTMLCanvasElement | null>(null);
    const sessionRef = useRef<ort.InferenceSession | null>(null);
    const animationFrameIdRef = useRef<number>(0);
    const lastReportTimeRef = useRef<number>(0);
    const prevViolationStrRef = useRef<string>("");

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
                console.log("YOLOv8 Loaded in Client App");
            } catch (err) {
                console.error(err);
                setStatus("Model Error");
            }
        };
        initYolo();
    }, []);

    // --- 2. Camera Setup ---
    useEffect(() => {
        let stream: MediaStream | null = null;
        navigator.mediaDevices.getUserMedia({ video: true, audio: false }).then(s => {
            stream = s;
            if (videoRef.current) videoRef.current.srcObject = s;
            animationFrameIdRef.current = requestAnimationFrame(runModel);
        }).catch(err => {
            console.error("Camera access denied", err);
            setStatus("Camera Error");
        });

        return () => {
            cancelAnimationFrame(animationFrameIdRef.current);
            if (stream) {
                stream.getTracks().forEach(track => track.stop());
            }
        };
    }, []);

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
        if (!videoRef.current || !sessionRef.current || videoRef.current.videoWidth === 0) {
            animationFrameIdRef.current = requestAnimationFrame(runModel);
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
        animationFrameIdRef.current = requestAnimationFrame(runModel);
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
        setIsWarning(currentViolations.length > 0);

        const vStr = alertCodes.join(",");
        const isChanged = vStr !== prevViolationStrRef.current;

        if (currentViolations.length > 0 && (isChanged || now - lastReportTimeRef.current > 4000)) {
            reportViolation(currentViolations, alertCodes, personCount, now, detections);
            prevViolationStrRef.current = vStr;
            lastReportTimeRef.current = now;
        } else if (currentViolations.length === 0 && isChanged) {
            sendClearLog(now);
            prevViolationStrRef.current = "";
        }
    };

    const reportViolation = (vList: string[], codes: string[], count: number, ts: number, detections: any[]) => {
        const video = videoRef.current;
        if (!video) return;

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

        const b64 = snap.toDataURL("image/jpeg", 0.6).split(",")[1];

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
                image: b64
            })
        }).catch(() => console.warn("Could not send log to backend"));
    };

    const sendClearLog = (ts: number) => {
        const apiUrl = process.env.NEXT_PUBLIC_API_URL;
        fetch(`${apiUrl}/camera/log`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ type: "DETECTION_LOG", violations: [], timestamp: ts }),
        }).catch(() => {});
    };

    return (
        <div className="max-w-5xl mx-auto space-y-6">
            <div className="bg-white rounded-3xl p-8 shadow-sm border border-gray-100">
                <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 mb-8">
                    <div>
                        <h1 className="text-2xl font-black text-gray-800 flex items-center gap-3">
                            <Camera className="text-[#5B0019]" size={32} />
                            Hệ thống Giám sát Camera AI
                        </h1>
                        <p className="text-gray-400 text-sm mt-1">Tự động phát hiện hành vi vi phạm trong quá trình học tập</p>
                    </div>
                    <div className={`flex items-center gap-2 px-4 py-2 rounded-full text-sm font-bold shadow-sm transition-colors ${status === "Ready" ? "bg-green-50 text-green-600 border border-green-100" : "bg-orange-50 text-orange-600 border border-orange-100"
                        }`}>
                        <div className={`w-2 h-2 rounded-full ${status === "Ready" ? "bg-green-500 animate-pulse" : "bg-orange-500"}`} />
                        Trạng thái AI: {status}
                    </div>
                </div>

                <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                    <div className="lg:col-span-2 space-y-4">
                        <div className={`relative rounded-2xl overflow-hidden border-4 transition-colors duration-500 shadow-2xl ${isWarning ? "border-red-500" : "border-[#5B0019]/10"
                            }`}>
                            <video
                                ref={videoRef}
                                autoPlay
                                muted
                                playsInline
                                className="w-full h-auto aspect-video object-cover bg-gray-900"
                                style={{ transform: "scaleX(-1)" }}
                            />
                            <div className="absolute top-4 left-4 bg-black/60 backdrop-blur-md px-3 py-1 rounded-lg text-[10px] text-white font-mono tracking-widest border border-white/20">
                                LIVE_PROCTORING_FEED: ACTIVE
                            </div>
                            {isWarning && (
                                <div className="absolute inset-0 bg-red-500/10 pointer-events-none animate-pulse" />
                            )}
                        </div>

                        <div className="flex items-center justify-between text-[11px] text-gray-500 font-medium px-2">
                            <div className="flex items-center gap-4">
                                <span className="flex items-center gap-1"><Activity size={14} className="text-[#5B0019]" /> Độ trễ: {metrics.time}ms</span>
                                <span>Số đối tượng: {metrics.rawCount}</span>
                            </div>
                            <span className="uppercase tracking-tighter">Powered by YOLOv8 ONNX Runtime</span>
                        </div>
                    </div>

                    <div className="space-y-6">
                        <div className="bg-gray-50 rounded-2xl p-6 border border-gray-100">
                            <h3 className="text-xs font-black text-gray-400 uppercase tracking-widest mb-4 flex items-center gap-2">
                                <ShieldCheck size={16} /> Kiểm tra bảo mật
                            </h3>
                            <div className="space-y-3">
                                <div className="flex items-center justify-between p-3 bg-white rounded-xl shadow-sm">
                                    <span className="text-sm font-bold text-gray-700">Mô hình AI</span>
                                    {status === "Ready" ? <CheckCircle2 className="text-green-500" size={18} /> : <AlertCircle className="text-orange-500" size={18} />}
                                </div>
                                <div className="flex items-center justify-between p-3 bg-white rounded-xl shadow-sm">
                                    <span className="text-sm font-bold text-gray-700">Camera Web</span>
                                    <CheckCircle2 className="text-green-500" size={18} />
                                </div>
                            </div>
                        </div>

                        <div className={`rounded-2xl p-6 border transition-all duration-300 ${isWarning ? "bg-red-50 border-red-100" : "bg-green-50 border-green-100"
                            }`}>
                            <h3 className={`text-xs font-black uppercase tracking-widest mb-4 flex items-center gap-2 ${isWarning ? "text-red-600" : "text-green-600"
                                }`}>
                                <AlertCircle size={16} /> Tình trạng vi phạm
                            </h3>
                            <div className="space-y-2">
                                {violations.length > 0 ? (
                                    violations.map((v, i) => (
                                        <div key={i} className="flex items-center gap-2 text-red-700 font-bold text-sm">
                                            <div className="w-1.5 h-1.5 rounded-full bg-red-500" />
                                            {v}
                                        </div>
                                    ))
                                ) : (
                                    <div className="flex items-center gap-2 text-green-700 font-bold text-sm">
                                        <CheckCircle2 size={18} />
                                        Hệ thống an toàn
                                    </div>
                                )}
                            </div>
                        </div>

                        <div className="p-4 bg-[#5B0019]/5 rounded-2xl border border-[#5B0019]/10">
                            <p className="text-[10px] text-gray-500 leading-relaxed italic">
                                * Lưu ý: Dữ liệu vi phạm sẽ được gửi về máy chủ để lưu trữ và đánh giá kết quả học tập. Vui lòng nghiêm túc trong quá trình thực hiện.
                            </p>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}
