"use client";

import React, { useState, useEffect, useRef, useCallback } from 'react';
import { useParams, useRouter } from 'next/navigation';
import {
    ChevronLeft, ChevronRight, Send,
    LayoutGrid, Trophy, Clock, Camera, X, AlertTriangle, Loader2, Activity, CheckCircle, Shield, KeyRound, ArrowLeft
} from 'lucide-react';
import CameraMonitor from '@/components/camera/CameraMonitor';
import ProctoringLockdown from '@/components/proctoring/ProctoringLockdown';
import Cookies from 'js-cookie';

type SelectedAnswers = { [key: number]: number };
type ExamStep = 'camera' | 'key' | 'exam';

const QUESTIONS_PER_PAGE = 10;

const ExamPage = () => {
    const params = useParams();
    const router = useRouter();
    const examId = params.id as string;

    const [exam, setExam] = useState<any>(null);
    const [loading, setLoading] = useState(true);
    const [currentPage, setCurrentPage] = useState<number>(0);
    const [selectedAnswers, setSelectedAnswers] = useState<SelectedAnswers>({});
    const [timeLeft, setTimeLeft] = useState<number>(0);
    const [isSubmitted, setIsSubmitted] = useState<boolean>(false);
    const [examStep, setExamStep] = useState<ExamStep>('camera');
    const [cameraStatus, setCameraStatus] = useState("Initializing...");
    const [violationCount, setViolationCount] = useState(0);
    const [showCheatModal, setShowCheatModal] = useState(false);
    const [exitCountdown, setExitCountdown] = useState(5);
    const [isGracePeriod, setIsGracePeriod] = useState(false);
    const [keyInput, setKeyInput] = useState('');
    const [keyError, setKeyError] = useState('');
    const [keyLoading, setKeyLoading] = useState(false);
    
    const mainContentRef = useRef<HTMLDivElement>(null);
    const cameraSourceRef = useRef<HTMLDivElement>(null);
    const sidebarTargetRef = useRef<HTMLDivElement>(null);
    const centerTargetRef = useRef<HTMLDivElement>(null);

    const [sidebarWidth, setSidebarWidth] = useState(320);
    const isResizing = useRef(false);

    const [user, setUser] = useState<any>(null);
    const [statusLoading, setStatusLoading] = useState(true);
    const [lockData, setLockData] = useState<{ reason: string, info?: any } | null>(null);
    const [fetchError, setFetchError] = useState<string | null>(null);
    const [isLockdownActive, setIsLockdownActive] = useState(false);
    const [showFullscreenWarning, setShowFullscreenWarning] = useState(false);

    // --- 1. Fetch User & Exam Status ---
    useEffect(() => {
        const init = async () => {
            try {
                const token = Cookies.get('auth_token');
                const apiUrl = process.env.NEXT_PUBLIC_API_URL;
                if (!apiUrl) throw new Error("API URL not configured");

                // Get User Info
                const userRes = await fetch(`${apiUrl}/user-info`, {
                    headers: { 'Authorization': `Bearer ${token}` }
                });
                if (userRes.ok) {
                    const uData = await userRes.json();
                    setUser(uData);
                }
            } catch (error) {
                console.error("Init Error:", error);
            } finally {
                setStatusLoading(false);
            }
        };
        init();
    }, [examId]);

    // --- 1. Fetch Exam Data (Including Lock Reason) ---
    const fetchExam = useCallback(async () => {
        setLoading(true);
        setFetchError(null);
        try {
            const token = Cookies.get('auth_token');
            const apiUrl = process.env.NEXT_PUBLIC_API_URL;
            if (!apiUrl) throw new Error("API URL not configured");

            const res = await fetch(`${apiUrl}/exams/${examId}`, {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            if (res.ok) {
                const data = await res.json();
                if (data.is_locked) {
                    setLockData({ 
                        reason: data.lock_reason, 
                        info: data.start_time || data.end_time || data.submission_status 
                    });
                    setExam(data);
                } else {
                    setExam(data);
                    const end = new Date(data.end_time).getTime();
                    const now = Date.now();
                    const secondsUntilDeadline = Math.floor((end - now) / 1000);
                    const durationSeconds = (data.duration || 60) * 60;
                    
                    // Time left is the smaller of (Time until deadline) or (Exam duration)
                    setTimeLeft(Math.max(0, Math.min(secondsUntilDeadline, durationSeconds)));
                }
            } else {
                const errData = await res.json().catch(() => ({ detail: "Không thể tải dữ liệu bài thi" }));
                setFetchError(errData.detail || "Lỗi máy chủ khi tải bài thi");
            }
        } catch (error: any) {
            console.error("Error fetching exam:", error);
            setFetchError("Không thể kết nối đến máy chủ. Vui lòng kiểm tra mạng.");
        } finally {
            setLoading(false);
        }
    }, [examId, router]);

    useEffect(() => {
        if (examId) fetchExam();
    }, [examId, fetchExam]);

    // --- 2. Camera Positioning ---
    useEffect(() => {
        const source = cameraSourceRef.current;
        const target = examStep === 'camera' ? centerTargetRef.current : sidebarTargetRef.current;
        if (source && target) {
            target.appendChild(source);
        }
    }, [examStep, loading]);

    // --- 3. Sidebar Resizing ---
    const startResizing = useCallback(() => {
        isResizing.current = true;
        document.body.style.cursor = "col-resize";
        document.body.style.userSelect = "none";
    }, []);

    const stopResizing = useCallback(() => {
        isResizing.current = false;
        document.body.style.cursor = "default";
        document.body.style.userSelect = "auto";
    }, []);

    const resize = useCallback((e: MouseEvent) => {
        if (!isResizing.current) return;
        const newWidth = window.innerWidth - e.clientX;
        if (newWidth > 200 && newWidth < 600) {
            setSidebarWidth(newWidth);
        }
    }, []);

    useEffect(() => {
        window.addEventListener("mousemove", resize);
        window.addEventListener("mouseup", stopResizing);
        return () => {
            window.removeEventListener("mousemove", resize);
            window.removeEventListener("mouseup", stopResizing);
        };
    }, [resize, stopResizing]);

    // --- 4. Timer Logic ---
    useEffect(() => {
        if (examStep === 'exam' && timeLeft > 0 && !isSubmitted) {
            const timer = setInterval(() => setTimeLeft(prev => prev - 1), 1000);
            return () => clearInterval(timer);
        } else if (examStep === 'exam' && timeLeft === 0 && !isSubmitted) {
            submitExam("completed");
        }
    }, [timeLeft, isSubmitted, examStep]);

    // --- 5. Cheat & Exit Handling ---
    useEffect(() => {
        if ((showCheatModal || isSubmitted) && exitCountdown > 0) {
            const timer = setInterval(() => setExitCountdown(prev => prev - 1), 1000);
            return () => clearInterval(timer);
        } else if ((showCheatModal || isSubmitted) && exitCountdown === 0) {
            router.push('/dashboard/exam_list');
        }
    }, [showCheatModal, isSubmitted, exitCountdown, router]);

    const submitExam = useCallback(async (finalStatus: string = "completed") => {
        if (isSubmitted) return;
        setIsSubmitted(true);
        try {
            const token = Cookies.get('auth_token');
            await fetch(`${process.env.NEXT_PUBLIC_API_URL}/exams/${examId}/submit`, {
                method: "POST",
                headers: { 
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    answers: selectedAnswers,
                    violation_count: violationCount,
                    status: finalStatus
                })
            });
        } catch (e) { console.error("Submit Error:", e); }
    }, [isSubmitted, examId, selectedAnswers, violationCount]);

    const handleCameraReady = useCallback(() => {
        setExamStep('key');
    }, []);

    const handleVerifyKey = async () => {
        setKeyError('');
        setKeyLoading(true);
        try {
            const token = Cookies.get('auth_token');
            const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/exams/${examId}/verify-key`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ key: keyInput.trim().toUpperCase() }),
            });
            if (res.ok) {
                setExamStep('exam');
                setIsLockdownActive(true);
                setIsGracePeriod(true);
                document.documentElement.requestFullscreen?.();
                setTimeout(() => setIsGracePeriod(false), 2500);
            } else {
                const data = await res.json().catch(() => ({}));
                setKeyError(data.detail || 'Mã không đúng. Vui lòng thử lại.');
            }
        } catch {
            setKeyError('Không thể kết nối máy chủ.');
        } finally {
            setKeyLoading(false);
        }
    };

    const handleViolation = useCallback(() => {
        if (examStep !== 'exam' || isGracePeriod || isSubmitted) return;
        setViolationCount(prev => {
            const n = prev + 1;
            if (n >= 4) {
                setShowCheatModal(true);
                submitExam("failed");
            }
            return n;
        });
    }, [examStep, isGracePeriod, isSubmitted, submitExam]);

    // Deactivate lockdown when exam is submitted
    useEffect(() => {
        if (isSubmitted) {
            setIsLockdownActive(false);
        }
    }, [isSubmitted]);

    const formatTime = (seconds: number): string => {
        const h = Math.floor(seconds / 3600);
        const m = Math.floor((seconds % 3600) / 60);
        const s = seconds % 60;
        if (h > 0) return `${h}:${m < 10 ? '0' + m : m}:${s < 10 ? '0' + s : s}`;
        return `${m < 10 ? '0' + m : m}:${s < 10 ? '0' + s : s}`;
    };

    const handleSelect = (qIdx: number, ansIdx: number) => {
        setSelectedAnswers(prev => ({ ...prev, [qIdx]: ansIdx }));
    };

    if (loading || statusLoading) {
        return (
            <div className="fixed inset-0 bg-white flex flex-col items-center justify-center">
                <Loader2 className="animate-spin text-[#5B0019] mb-4" size={48} />
                <p className="text-gray-400 font-bold uppercase tracking-widest text-xs animate-pulse">Đang định danh hệ thống...</p>
            </div>
        );
    }

    if (fetchError) {
        return (
            <div className="fixed inset-0 bg-white flex flex-col items-center justify-center p-6 text-center animate-in fade-in duration-500">
                <div className="w-24 h-24 bg-red-50 text-red-500 rounded-full flex items-center justify-center mb-6 shadow-md">
                    <AlertTriangle size={48} />
                </div>
                <h1 className="text-3xl font-black text-gray-900 mb-2">Lỗi tải bài thi</h1>
                <p className="text-gray-500 font-medium mb-8 max-w-md">{fetchError}</p>
                <div className="flex gap-4">
                    <button 
                        onClick={() => router.push('/dashboard/exam_list')} 
                        className="px-8 py-4 bg-gray-100 text-gray-600 rounded-2xl font-black hover:bg-gray-200 transition-all uppercase tracking-widest text-xs"
                    >Quay về</button>
                    <button 
                        onClick={() => fetchExam()} 
                        className="px-8 py-4 bg-[#5B0019] text-white rounded-2xl font-black shadow-lg hover:bg-black transition-all active:scale-95 uppercase tracking-widest text-xs"
                    >Thử lại</button>
                </div>
            </div>
        );
    }

    if (lockData) {
        const renderLockContent = () => {
            switch(lockData.reason) {
                case "disqualified":
                    return (
                        <>
                            <div className="w-24 h-24 bg-red-100 text-red-600 rounded-full flex items-center justify-center mb-6 shadow-xl animate-bounce">
                                <AlertTriangle size={48} />
                            </div>
                            <h1 className="text-4xl font-black text-gray-900 tracking-tight mb-2">PHÁT HIỆN GIAN LẬN</h1>
                            <p className="text-gray-500 font-medium mb-12 italic">Hệ thống AI đã đình chỉ bài thi của bạn do phát hiện vi phạm nghiêm trọng.</p>
                        </>
                    );
                case "not_started":
                    return (
                        <>
                            <div className="w-24 h-24 bg-blue-100 text-blue-600 rounded-full flex items-center justify-center mb-6 shadow-xl">
                                <Clock size={48} />
                            </div>
                            <h1 className="text-4xl font-black text-gray-900 tracking-tight mb-2">Bài thi chưa mở</h1>
                            <p className="text-gray-500 font-medium mb-4">Bài thi sẽ bắt đầu vào lúc:</p>
                            <p className="text-2xl font-black text-[#5B0019] mb-12">
                                {new Date(lockData.info).toLocaleString('vi-VN', { 
                                    timeZone: 'Asia/Ho_Chi_Minh',
                                    hour: '2-digit', 
                                    minute: '2-digit',
                                    day: '2-digit',
                                    month: '2-digit',
                                    year: 'numeric'
                                }).replace(',', ' lúc')}
                            </p>
                        </>
                    );
                case "expired":
                    return (
                        <>
                            <div className="w-24 h-24 bg-gray-100 text-gray-600 rounded-full flex items-center justify-center mb-6 shadow-xl">
                                <X size={48} />
                            </div>
                            <h1 className="text-4xl font-black text-gray-900 tracking-tight mb-2">Bài thi đã kết thúc</h1>
                            <p className="text-gray-500 font-medium mb-12">Rất tiếc, thời gian tham gia bài thi này đã hết hạn.</p>
                        </>
                    );
                default:
                    return (
                        <>
                            <div className="w-24 h-24 bg-green-100 text-green-600 rounded-full flex items-center justify-center mb-6 shadow-xl">
                                <CheckCircle size={48} />
                            </div>
                            <h1 className="text-4xl font-black text-gray-900 tracking-tight mb-2">Bài thi đã nộp</h1>
                            <p className="text-gray-500 font-medium mb-12">Bạn đã hoàn thành bài thi này trước đó.</p>
                        </>
                    );
            }
        };

        return (
            <div className="fixed inset-0 z-[11000] bg-white flex flex-col items-center justify-center p-6 text-center animate-in zoom-in duration-500">
                {renderLockContent()}
                <button 
                    onClick={() => router.push('/dashboard/exam_list')} 
                    className="px-16 py-4 bg-[#5B0019] text-white rounded-2xl font-black shadow-2xl hover:bg-black transition-all active:scale-95 uppercase tracking-widest text-sm"
                >Quay về danh sách</button>
            </div>
        );
    }

    if (!exam) return null;

    const totalQuestions = exam.questions.length;
    const startIndex = currentPage * QUESTIONS_PER_PAGE;
    const currentQuestionIndexes = Array.from({ length: QUESTIONS_PER_PAGE }, (_, i) => startIndex + i)
        .filter(idx => idx < totalQuestions);
    const totalPages = Math.ceil(totalQuestions / QUESTIONS_PER_PAGE);

    return (
        <div className="fixed inset-0 z-[10000] flex flex-col w-full h-screen bg-gray-50 font-sans overflow-hidden text-sm">

            {/* Fullscreen Exit Warning Toast */}
            {showFullscreenWarning && (
                <div className="fixed inset-x-0 top-4 z-[11000] flex justify-center pointer-events-none animate-in slide-in-from-top-2 fade-in duration-300">
                    <div className="bg-white/95 backdrop-blur-md border border-amber-300 rounded-2xl shadow-2xl px-6 py-3 flex items-center gap-3 max-w-sm">
                        <AlertTriangle size={16} className="text-amber-500 shrink-0" />
                        <p className="text-sm font-bold text-gray-700">Màn hình đã thoát toàn màn hình</p>
                    </div>
                </div>
            )}

            {/* Header */}
            <header className="h-16 bg-[#5B0019] border-b border-red-900 flex items-center justify-between px-6 shrink-0 shadow-md z-10 transition-colors">
                <div className="flex flex-col text-white">
                    <h1 className="text-lg font-black uppercase leading-none tracking-tight">{exam.subject} - {exam.title}</h1>
                    <span className="text-[10px] font-bold text-red-200 mt-1 uppercase tracking-widest">
                        Tiến độ: {Object.keys(selectedAnswers).length}/{totalQuestions} câu
                    </span>
                </div>

                <div className="flex items-center gap-4">
                    <div className={`flex items-center gap-2 px-6 py-2 rounded-xl border font-mono font-bold text-xl text-white transition-all shadow-inner ${
                        timeLeft < 300 ? 'bg-red-500 animate-pulse border-red-400' : 'bg-white/10 border-white/20'
                    }`}>
                        <Clock size={18} /> {formatTime(timeLeft)}
                    </div>
                    {isLockdownActive && (
                        <span className="flex items-center gap-1.5 px-3 py-1.5 bg-red-500 text-white rounded-full text-xs font-black shadow-lg" aria-label="Chế độ bảo vệ đang bật">
                            <Shield size={12} /> BẢO VỆ
                        </span>
                    )}
                    <button
                        onClick={() => submitExam("completed")}
                        className="bg-white text-[#5B0019] hover:bg-black hover:text-white px-8 py-2.5 rounded-xl font-black text-xs uppercase tracking-widest flex items-center gap-2 transition-all shadow-lg active:scale-95 disabled:opacity-40 disabled:grayscale"
                        disabled={Object.keys(selectedAnswers).length === 0 || isSubmitted}
                    >
                        <Send size={16} /> {isSubmitted ? "Đang nộp..." : "Nộp bài"}
                    </button>
                </div>
            </header>

            <div className="flex flex-1 overflow-hidden relative">
                
                {/* Violation Counter Badge */}
                <div className="absolute top-4 left-4 z-30 pointer-events-none">
                    <div className="bg-white/90 backdrop-blur-md border border-gray-100 shadow-2xl rounded-[1.5rem] p-4 flex flex-col items-center gap-1 min-w-[90px] animate-in slide-in-from-left-4 duration-500">
                        <span className="text-[9px] font-black text-gray-400 uppercase tracking-[0.2em]">Vi phạm</span>
                        <div className={`text-3xl font-black leading-none transition-colors duration-300 ${
                            violationCount === 0 ? 'text-green-500' : 
                            violationCount <= 2 ? 'text-yellow-500' : 
                            'text-red-500'
                        }`}>
                            {Math.min(violationCount, 3)}/3
                        </div>
                    </div>
                </div>

                {/* Main Content (Questions) */}
                <main ref={mainContentRef} className="flex-1 overflow-y-auto bg-gray-100/50 scroll-smooth">
                    <div className="max-w-3xl mx-auto p-8 space-y-6 pb-32">
                        {currentQuestionIndexes.map((qIdx) => {
                            const q = exam.questions[qIdx];
                            return (
                                <div key={qIdx} className="bg-white rounded-[2rem] shadow-sm border border-gray-200/60 overflow-hidden hover:shadow-md transition-shadow duration-300">
                                    <div className="p-7 border-b border-gray-50 bg-white">
                                        <div className="flex items-start gap-4">
                                            <span className="shrink-0 w-8 h-8 bg-[#5B0019] text-white rounded-xl flex items-center justify-center font-black text-sm shadow-md">{qIdx + 1}</span>
                                            <h3 className="text-lg font-bold text-gray-800 leading-snug pt-0.5">
                                                {q.q}
                                            </h3>
                                        </div>
                                    </div>
                                    <div className="p-7 bg-gray-50/30 grid grid-cols-1 md:grid-cols-2 gap-4">
                                        {q.options.map((opt: string, aIdx: number) => (
                                            <button 
                                                key={aIdx} 
                                                onClick={() => handleSelect(qIdx, aIdx)}
                                                className={`p-4 text-left border rounded-2xl transition-all flex items-center gap-4 group ${
                                                    selectedAnswers[qIdx] === aIdx 
                                                    ? 'border-[#5B0019] bg-[#5B0019] text-white shadow-xl scale-[1.02]' 
                                                    : 'border-white bg-white text-gray-600 hover:border-red-100 hover:shadow-sm shadow-sm'
                                                }`}
                                            >
                                                <span className={`w-8 h-8 shrink-0 rounded-lg flex items-center justify-center text-sm font-black transition-colors ${
                                                    selectedAnswers[qIdx] === aIdx 
                                                    ? 'bg-white/20 text-white' 
                                                    : 'bg-gray-100 text-gray-400 group-hover:bg-red-50 group-hover:text-[#5B0019]'
                                                }`}>{String.fromCharCode(65 + aIdx)}</span>
                                                <span className="font-bold text-sm tracking-tight">{opt}</span>
                                            </button>
                                        ))}
                                    </div>
                                </div>
                            );
                        })}

                        {/* Pagination */}
                        <div className="flex items-center justify-between pt-8">
                            <button 
                                disabled={currentPage === 0}
                                onClick={() => setCurrentPage(p => p - 1)}
                                className="flex items-center gap-2 px-6 py-3 bg-white text-gray-600 rounded-2xl font-black text-xs uppercase tracking-widest border border-gray-200 disabled:opacity-30 transition-all hover:bg-gray-50 active:scale-95"
                            >
                                <ChevronLeft size={16} /> Trang trước
                            </button>
                            <div className="text-[10px] font-black text-gray-400 uppercase tracking-widest">
                                Trang {currentPage + 1} / {totalPages}
                            </div>
                            <button 
                                disabled={currentPage === totalPages - 1}
                                onClick={() => setCurrentPage(p => p + 1)}
                                className="flex items-center gap-2 px-6 py-3 bg-[#5B0019] text-white rounded-2xl font-black text-xs uppercase tracking-widest shadow-xl disabled:opacity-30 transition-all hover:bg-black active:scale-95"
                            >
                                Trang sau <ChevronRight size={16} />
                            </button>
                        </div>
                    </div>
                </main>

                {/* Resize Handle */}
                <div
                    onMouseDown={startResizing}
                    className="w-1.5 hover:w-2 bg-gray-200 hover:bg-[#5B0019] cursor-col-resize transition-all shrink-0 relative z-20 group"
                >
                    <div className="absolute inset-0 flex items-center justify-center opacity-0 group-hover:opacity-100">
                        <div className="w-0.5 h-12 bg-white rounded-full"></div>
                    </div>
                </div>

                {/* Sidebar (Question List & Camera) */}
                <aside
                    style={{ width: `${sidebarWidth}px` }}
                    className="bg-white flex flex-col shrink-0 shadow-sm z-10"
                >
                    <div className="flex-1 overflow-y-auto p-6">
                        <div className="flex items-center gap-2 mb-6 text-gray-400 font-black uppercase text-[10px] tracking-[0.2em] border-b border-gray-50 pb-4">
                            <LayoutGrid size={14} className="text-[#5B0019]" /> Mục lục câu hỏi
                        </div>
                        <div className="grid grid-cols-5 gap-2 pb-8">
                            {Array.from({ length: totalQuestions }).map((_, i) => (
                                <button 
                                    key={i} 
                                    onClick={() => setCurrentPage(Math.floor(i / QUESTIONS_PER_PAGE))}
                                    className={`h-11 rounded-xl text-xs font-black border transition-all duration-300 relative ${
                                        selectedAnswers[i] !== undefined 
                                        ? 'bg-[#5B0019] text-white border-[#5B0019] shadow-md' 
                                        : 'bg-white text-gray-400 border-gray-100 hover:border-red-100'
                                    } ${Math.floor(i / QUESTIONS_PER_PAGE) === currentPage ? 'ring-4 ring-red-50' : ''}`}
                                >
                                    {i + 1}
                                    {Math.floor(i / QUESTIONS_PER_PAGE) === currentPage && (
                                        <div className="absolute -bottom-1 left-1/2 -translate-x-1/2 w-4 h-1 bg-[#5B0019] rounded-full" />
                                    )}
                                </button>
                            ))}
                        </div>
                    </div>

                    <div className="p-6 border-t border-gray-100 bg-gray-50/50 space-y-3">
                        {/* SEAMLESS CAMERA TARGET */}
                        <div className="rounded-2xl overflow-hidden shadow-2xl border-2 border-white">
                            <div ref={sidebarTargetRef} className="w-full" />
                        </div>
                        
                        {examStep !== 'exam' && (
                            <div className="aspect-video bg-gray-100 rounded-2xl flex items-center justify-center border-2 border-dashed border-gray-200">
                                <span className="text-[9px] text-gray-400 font-black uppercase tracking-widest text-center px-4 animate-pulse">Đang chờ khởi tạo...</span>
                            </div>
                        )}
                        <div className="flex items-center justify-center gap-2">
                            <div className="w-1.5 h-1.5 rounded-full bg-red-400 animate-pulse" />
                            <p className="text-[9px] text-gray-400 font-black uppercase tracking-widest">Live Proctoring Active</p>
                        </div>
                    </div>

                </aside>
            </div>

            {/* Camera Check Screen */}
            {examStep === 'camera' && !isSubmitted && (
                <div className="fixed inset-0 z-[10001] bg-white flex items-center justify-center p-6 animate-in fade-in zoom-in-95 duration-700">
                    <div className="max-w-6xl w-full grid grid-cols-1 lg:grid-cols-2 gap-16 items-center">
                        <div className="space-y-10">
                            <div className="space-y-4">
                                <div className="inline-flex items-center gap-2 px-4 py-1.5 bg-red-50 text-[#5B0019] rounded-full text-[10px] font-black uppercase tracking-widest border border-red-100">
                                    <Camera size={14} /> Hệ thống giám sát AI
                                </div>
                                <h1 className="text-5xl font-black text-gray-900 leading-tight tracking-tight">
                                    Thực hiện <br />
                                    <span className="text-[#5B0019]">Xác thực AI</span>
                                </h1>
                                <p className="text-gray-500 text-lg leading-relaxed font-medium">
                                    Vui lòng căn chỉnh khuôn mặt vào giữa khung hình. Hệ thống AI sẽ theo dõi và ghi lại các hành vi vi phạm trong suốt quá trình làm bài.
                                </p>
                            </div>

                            <div className="grid grid-cols-2 gap-6">
                                {[
                                    { icon: <Camera size={18} />, text: "Khuôn mặt rõ nét" },
                                    { icon: <Clock size={18} />, text: "Đúng thời gian" },
                                    { icon: <AlertTriangle size={18} />, text: "Không thiết bị lạ" },
                                    { icon: <X size={18} />, text: "Không rời khung hình" }
                                ].map((item, i) => (
                                    <div key={i} className="flex items-center gap-3 p-4 bg-gray-50 rounded-2xl border border-gray-100 group hover:border-[#5B0019]/20 transition-all">
                                        <div className="text-[#5B0019] group-hover:scale-110 transition-transform">{item.icon}</div>
                                        <span className="text-sm font-bold text-gray-700">{item.text}</span>
                                    </div>
                                ))}
                            </div>

                            <button
                                onClick={handleCameraReady}
                                disabled={cameraStatus !== "Ready"}
                                className={`w-full py-6 rounded-3xl font-black text-xl shadow-2xl transition-all duration-500 transform hover:scale-[1.02] active:scale-[0.98] flex items-center justify-center gap-4 ${
                                    cameraStatus === "Ready" 
                                    ? "bg-[#5B0019] text-white hover:bg-black shadow-red-900/20" 
                                    : "bg-gray-100 text-gray-400 cursor-not-allowed border border-gray-200"
                                }`}
                            >
                                {cameraStatus === "Ready" ? (
                                    <>VÀO THI NGAY <ChevronRight size={20} /></>
                                ) : (
                                    <>KHỞI TẠO AI... ({cameraStatus})</>
                                )}
                            </button>
                        </div>

                        <div className="relative flex items-center justify-center">
                            {/* NEW SEAMLESS CAMERA TARGET */}
                            <div className="relative group">
                                <div className="absolute -inset-4 bg-[#5B0019]/5 rounded-[3.5rem] blur-2xl group-hover:bg-[#5B0019]/10 transition-all" />
                                <div 
                                    ref={centerTargetRef} 
                                    className={`w-[480px] aspect-video rounded-[3rem] overflow-hidden border-8 transition-all duration-700 shadow-[0_32px_64px_-12px_rgba(0,0,0,0.2)] relative ${
                                        cameraStatus === "Ready" ? "border-[#5B0019] scale-[1.02]" : "border-white"
                                    }`} 
                                />
                                <div className="absolute -bottom-6 -right-6 w-24 h-24 bg-[#5B0019] rounded-full flex items-center justify-center text-white shadow-2xl border-4 border-white animate-bounce">
                                    <Activity size={32} />
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            )}

            {examStep === 'key' && !isSubmitted && (
                <div className="fixed inset-0 z-[10001] bg-white flex items-center justify-center p-6 animate-in fade-in slide-in-from-right-8 duration-500">
                    <div className="max-w-lg w-full space-y-10">
                        <div className="space-y-4">
                            <button
                                onClick={() => setExamStep('camera')}
                                className="flex items-center gap-2 text-gray-400 hover:text-gray-700 font-bold text-sm transition-colors"
                            >
                                <ArrowLeft size={18} /> Quay lại kiểm tra camera
                            </button>
                            <div className="inline-flex items-center gap-2 px-4 py-1.5 bg-amber-50 text-amber-700 rounded-full text-[10px] font-black uppercase tracking-widest border border-amber-100">
                                <KeyRound size={14} /> Xác thực mã đề thi
                            </div>
                            <h1 className="text-5xl font-black text-gray-900 leading-tight tracking-tight">
                                Nhập <br />
                                <span className="text-[#5B0019]">Mã Đề Thi</span>
                            </h1>
                            <p className="text-gray-500 text-lg leading-relaxed font-medium">
                                Vui lòng nhập mã đề thi được giáo viên cung cấp để tiếp tục vào bài thi.
                            </p>
                        </div>

                        <div className="space-y-4">
                            <div className={`relative rounded-3xl border-2 transition-all duration-300 overflow-hidden ${
                                keyError ? 'border-red-400 bg-red-50/30' :
                                keyInput.length > 0 ? 'border-[#5B0019]/40 bg-[#5B0019]/3' :
                                'border-gray-200 bg-gray-50'
                            }`}>
                                <input
                                    type="text"
                                    maxLength={12}
                                    value={keyInput}
                                    autoFocus
                                    onChange={(e) => {
                                        setKeyInput(e.target.value.toUpperCase().replace(/[^A-Z0-9]/g, ''));
                                        setKeyError('');
                                    }}
                                    onKeyDown={(e) => e.key === 'Enter' && keyInput.length >= 1 && handleVerifyKey()}
                                    placeholder="Nhập mã đề thi..."
                                    className="w-full px-8 py-7 bg-transparent border-none text-4xl font-black tracking-[0.4em] text-center text-[#5B0019] placeholder:text-gray-300 placeholder:tracking-widest placeholder:text-2xl focus:outline-none focus:ring-0"
                                />
                                {keyInput.length > 0 && (
                                    <button
                                        onClick={() => setKeyInput('')}
                                        className="absolute right-5 top-1/2 -translate-y-1/2 p-2 text-gray-300 hover:text-gray-500"
                                    >
                                        <X size={20} />
                                    </button>
                                )}
                            </div>

                            {keyError && (
                                <div className="flex items-center gap-3 p-4 bg-red-50 border border-red-100 rounded-2xl animate-in slide-in-from-top-2 duration-300">
                                    <AlertTriangle size={18} className="text-red-500 shrink-0" />
                                    <p className="text-sm font-bold text-red-600">{keyError}</p>
                                </div>
                            )}
                        </div>

                        <button
                            onClick={handleVerifyKey}
                            disabled={keyLoading || keyInput.length < 1}
                            className={`w-full py-6 rounded-3xl font-black text-xl shadow-2xl transition-all duration-500 flex items-center justify-center gap-4 ${
                                keyInput.length >= 1 && !keyLoading
                                    ? 'bg-[#5B0019] text-white hover:bg-black shadow-red-900/20 hover:scale-[1.02] active:scale-[0.98]'
                                    : 'bg-gray-100 text-gray-400 cursor-not-allowed border border-gray-200'
                            }`}
                        >
                            {keyLoading ? (
                                <><Loader2 className="animate-spin" size={22} /> Đang xác thực...</>
                            ) : (
                                <>XÁC NHẬN & VÀO THI <KeyRound size={20} /></>
                            )}
                        </button>

                        <p className="text-center text-xs text-gray-400 font-medium">
                            Liên hệ giáo viên nếu bạn chưa nhận được mã đề thi
                        </p>
                    </div>
                </div>
            )}

            {/* Cheat Detection Modal */}
            {showCheatModal && (
                <div className="fixed inset-0 z-[11000] flex items-center justify-center p-4 bg-black/80 backdrop-blur-md animate-in fade-in duration-500">
                    <div className="bg-white rounded-[3rem] shadow-[0_0_100px_rgba(255,0,0,0.2)] max-w-md w-full overflow-hidden border border-red-100 relative translate-y-[-20%] animate-in slide-in-from-bottom-10">
                        <div className="p-10 text-center space-y-8">
                            <div className="w-24 h-24 bg-red-50 text-red-500 rounded-full flex items-center justify-center mx-auto shadow-inner animate-pulse">
                                <AlertTriangle size={48} />
                            </div>
                            
                            <div className="space-y-3">
                                <h2 className="text-3xl font-black text-gray-900 tracking-tight">PHÁT HIỆN GIAN LẬN</h2>
                                <p className="text-gray-500 font-bold leading-relaxed px-4">
                                    AI đã phát hiện hành vi bất thường và bài thi của bạn đã bị khóa.
                                </p>
                            </div>

                            <div className="bg-red-500 text-white py-4 px-10 rounded-2xl font-black text-lg inline-block shadow-xl shadow-red-500/30">
                                THOÁT RA SAU {exitCountdown}S
                            </div>
                        </div>
                        
                        <div className="bg-gray-50/80 p-6 border-t border-gray-100">
                            <p className="text-[10px] text-gray-400 text-center uppercase tracking-[0.3em] font-black italic">
                                EduTrust AI Proctoring Security
                            </p>
                        </div>
                    </div>
                </div>
            )}

            {isSubmitted && !showCheatModal && (
                <div className="fixed inset-0 z-[11000] bg-white flex flex-col items-center justify-center p-6 text-center animate-in zoom-in duration-500">
                    <div className="w-24 h-24 bg-green-100 text-green-600 rounded-full flex items-center justify-center mb-6 shadow-xl animate-bounce">
                        <Trophy size={48} />
                    </div>
                    <h1 className="text-4xl font-black text-gray-900 tracking-tight mb-2">Bài thi đã hoàn thành!</h1>
                    <p className="text-gray-500 font-medium mb-12 italic">Hệ thống đang xử lý kết quả của bạn.</p>
                    <div className="bg-[#5B0019] text-white py-4 px-16 rounded-2xl font-black text-lg shadow-2xl">
                        THOÁT SAU {exitCountdown}S
                    </div>
                </div>
            )}

            {/* Persistent Seamless Camera Source */}
            <div className="hidden" aria-hidden="true">
                {user?.id && (
                    <div ref={cameraSourceRef} className="w-full h-full">
                        <CameraMonitor
                            onViolation={handleViolation}
                            onStatusChange={setCameraStatus}
                            isCheck={examStep !== 'exam'}
                            isActive={!isSubmitted && !showCheatModal}
                            examId={examId}
                            studentId={user.id}
                        />
                        <ProctoringLockdown
                            isActive={isLockdownActive && examStep === 'exam'}
                            onFullscreenExit={() => {
                                setShowFullscreenWarning(true);
                                setTimeout(() => setShowFullscreenWarning(false), 3000);
                            }}
                            contentSelector="main"
                        />
                    </div>
                )}
            </div>
        </div>
    );
};

export default ExamPage;
