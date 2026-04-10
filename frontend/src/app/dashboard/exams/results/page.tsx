"use client";

import React, { useEffect, useState } from 'react';
import { FileText, Users, Award, Search, Eye, ChevronRight, ChevronDown, Clock, ShieldAlert, ShieldCheck, X, User } from 'lucide-react';
import Cookies from 'js-cookie';

interface ExamStat {
    id: string;
    title: string;
    subject: string;
    class_id: string;
    class_name: string;
    grade: string | number;
    total_submissions: number;
    average_score: number;
    highest_score: number;
    violations_count: number;
    start_time: string;
    end_time: string;
}

interface SubmissionDetail {
    student_id: string;
    student_name: string;
    score: number;
    violation_count: number;
    status: string;
    submitted_at: string;
}

export default function StaffResultsPage() {
    const [exams, setExams] = useState<ExamStat[]>([]);
    const [loading, setLoading] = useState(true);
    const [searchTerm, setSearchTerm] = useState('');
    const [expandedClasses, setExpandedClasses] = useState<Record<string, boolean>>({});
    const [selectedExam, setSelectedExam] = useState<{ id: string, title: string } | null>(null);
    const [submissions, setSubmissions] = useState<SubmissionDetail[]>([]);
    const [loadingSubmissions, setLoadingSubmissions] = useState(false);
    const [currentTime, setCurrentTime] = useState(new Date());

    useEffect(() => {
        const timer = setInterval(() => setCurrentTime(new Date()), 10000); // Update every 10 seconds
        return () => clearInterval(timer);
    }, []);

    useEffect(() => {
        const fetchStaffResults = async () => {
            try {
                const token = Cookies.get('auth_token');
                const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/exams/all-results/summary`, {
                    headers: { 'Authorization': `Bearer ${token}` }
                });
                if (res.ok) {
                    const data = await res.json();
                    setExams(data);
                    // Start with all classes collapsed
                    setExpandedClasses({});
                }
            } catch (error) {
                console.error("Error fetching staff results:", error);
            } finally {
                setLoading(false);
            }
        };
        fetchStaffResults();
    }, []);

    const fetchSubmissions = async (examId: string, examTitle: string) => {
        setSelectedExam({ id: examId, title: examTitle });
        setLoadingSubmissions(true);
        setSubmissions([]);
        try {
            const token = Cookies.get('auth_token');
            const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/exams/${examId}/submissions`, {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            if (res.ok) {
                const data = await res.json();
                setSubmissions(data);
            }
        } catch (error) {
            console.error("Error fetching submissions:", error);
        } finally {
            setLoadingSubmissions(false);
        }
    };

    const toggleClass = (classId: string) => {
        setExpandedClasses(prev => ({
            ...prev,
            [classId]: !prev[classId]
        }));
    };

    const filteredExams = exams.filter(e =>
        e.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
        e.subject.toLowerCase().includes(searchTerm.toLowerCase()) ||
        (e.class_name && e.class_name.toLowerCase().includes(searchTerm.toLowerCase()))
    );

    // Grouping logic
    const groupedExams = filteredExams.reduce((acc, exam) => {
        const classId = exam.class_id || 'unknown';
        if (!acc[classId]) {
            acc[classId] = {
                id: classId,
                name: exam.class_name || 'Khác',
                grade: exam.grade || 'N/A',
                exams: []
            };
        }
        acc[classId].exams.push(exam);
        return acc;
    }, {} as Record<string, { id: string, name: string, grade: ExamStat['grade'] | 'N/A', exams: ExamStat[] }>);

    const collator = new Intl.Collator('vi', { numeric: true, sensitivity: 'base' });
    const classList = Object.values(groupedExams).sort((a, b) => {
        if (a.grade !== b.grade) return collator.compare(String(a.grade), String(b.grade));
        return a.name.localeCompare(b.name);
    });

    return (
        <div className="max-w-[75rem] mx-auto space-y-10 animate-in fade-in slide-in-from-bottom-5 duration-700 pb-20">
            <div className="flex flex-col md:flex-row md:items-end justify-between gap-6">
                <div className="space-y-2">
                    <div className="inline-flex items-center gap-2 px-4 py-1.5 bg-[#5B0019]/5 text-[#5B0019] rounded-full text-[10px] font-black uppercase tracking-widest border border-[#5B0019]/10">
                        <Award size={14} /> Analytics Dashboard
                    </div>
                    <h1 className="text-5xl font-black text-gray-900 tracking-tight">Thống Kê Điểm Số</h1>
                    <p className="text-gray-500 font-medium">Theo dõi thành tích học sinh trên toàn hệ thống.</p>
                </div>

                <div className="flex bg-white p-2 rounded-2xl shadow-sm border border-gray-100 items-center gap-3 w-full md:w-96 shadow-[0_8px_30px_rgb(0,0,0,0.04)] focus-within:shadow-md transition-all">
                    <Search className="text-gray-300 ml-3" size={20} />
                    <input
                        type="text"
                        placeholder="Tìm đề thi, lớp học..."
                        className="bg-transparent border-none outline-none text-sm font-semibold w-full pr-4 text-gray-700"
                        value={searchTerm}
                        onChange={(e) => setSearchTerm(e.target.value)}
                    />
                </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
                {[
                    { label: "Tổng Đề Thi", value: exams.length, icon: <FileText />, color: "bg-blue-600" },
                    { label: "Tổng Lượt Thi", value: exams.reduce((a, b) => a + (b.total_submissions || 0), 0), icon: <Users />, color: "bg-green-600" },
                    { label: "Điểm Trung Bình", value: exams.length > 0 ? (() => { const avg = exams.reduce((a, b) => a + (Number(b.average_score) || 0), 0) / exams.length; return (isNaN(avg) || !isFinite(avg)) ? "0" : avg.toFixed(1); })() : "0", icon: <Award />, color: "bg-amber-500" },
                    { label: "Vi Phạm AI", value: exams.reduce((a, b) => a + (b.violations_count || 0), 0), icon: <Eye />, color: "bg-red-500" }
                ].map((stat, i) => (
                    <div key={i} className="bg-white p-6 rounded-[2rem] border border-gray-100 shadow-sm hover:shadow-md transition-all flex items-center gap-5">
                        <div className={`w-12 h-12 ${stat.color} text-white rounded-xl flex items-center justify-center shadow-lg shadow-gray-200`}>
                            {stat.icon}
                        </div>
                        <div>
                            <p className="text-[10px] font-black text-gray-400 uppercase tracking-widest leading-none mb-1.5">{stat.label}</p>
                            <p className="text-2xl font-black text-gray-900 leading-none">{stat.value}</p>
                        </div>
                    </div>
                ))}
            </div>

            <div className="space-y-6">
                {loading ? (
                    <div className="bg-white rounded-[3rem] p-20 text-center text-gray-400 font-black uppercase tracking-widest text-xs animate-pulse border border-gray-100">
                        Loading Results...
                    </div>
                ) : classList.map((cls) => (
                    <div key={cls.id} className="space-y-4">
                        {/* Class Header Row */}
                        <button
                            onClick={() => toggleClass(cls.id)}
                            aria-expanded={expandedClasses[cls.id]}
                            aria-controls={`class-exams-${cls.id}`}
                            className="w-full text-left bg-white p-6 rounded-[2rem] border border-gray-100 shadow-sm hover:shadow-md transition-all cursor-pointer flex items-center justify-between group"
                        >
                            <div className="flex items-center gap-6">
                                <div className="w-2 h-12 bg-[#5B0019] rounded-full group-hover:scale-y-110 transition-transform" />
                                <div>
                                    <h3 className="text-2xl font-black text-gray-900 flex items-center gap-3">
                                        Lớp {cls.name}
                                        <span className="px-3 py-1 bg-gray-100 text-gray-400 text-[10px] font-black uppercase tracking-widest rounded-full">
                                            Khối {cls.grade}
                                        </span>
                                    </h3>
                                    <div className="flex items-center gap-2 text-gray-400 text-xs font-bold mt-1">
                                        <Clock size={14} />
                                        Có {cls.exams.length} đề thi hiện tại
                                    </div>
                                </div>
                            </div>
                            <div className={`p-4 rounded-2xl bg-gray-50 text-gray-400 group-hover:bg-[#5B0019] group-hover:text-white transition-all ${expandedClasses[cls.id] ? 'rotate-180' : ''}`}>
                                <ChevronDown size={24} />
                            </div>
                        </button>

                        {/* Exams list for this class */}
                        {expandedClasses[cls.id] && (
                            <div id={`class-exams-${cls.id}`} className="bg-white/50 rounded-[2.5rem] p-2 space-y-2 animate-in slide-in-from-top-2 duration-300">
                                <div className="bg-white rounded-[2.5rem] shadow-sm border border-gray-100 overflow-hidden">
                                    <div className="overflow-x-auto">
                                        <table className="w-full text-left border-collapse">
                                            <thead>
                                                <tr className="bg-gray-50/50">
                                                    <th className="px-10 py-6 text-[11px] font-black text-gray-400 uppercase tracking-[0.2em]">Tên Đề Thi & Môn Học</th>
                                                    <th className="px-8 py-6 text-[11px] font-black text-gray-400 uppercase tracking-[0.2em] text-center">Lượt Thi</th>
                                                    <th className="px-8 py-6 text-[11px] font-black text-gray-400 uppercase tracking-[0.2em] text-center">ĐTB</th>
                                                    <th className="px-8 py-6 text-[11px] font-black text-gray-400 uppercase tracking-[0.2em] text-center">Cao Nhất</th>
                                                    <th className="px-8 py-6 text-[11px] font-black text-gray-400 uppercase tracking-[0.2em] text-center">Vi Phạm</th>
                                                    <th className="px-8 py-6 text-[11px] font-black text-gray-400 uppercase tracking-[0.2em] text-center">Trạng Thái</th>
                                                    <th className="px-10 py-6"></th>
                                                </tr>
                                            </thead>
                                            <tbody className="divide-y divide-gray-50">
                                                {cls.exams.map((exam) => (
                                                    <tr key={exam.id} className="hover:bg-gray-50/70 transition-colors group">
                                                        <td className="px-10 py-8">
                                                            <div className="flex items-center gap-5">
                                                                <div className="w-14 h-14 bg-gray-100 rounded-2xl flex items-center justify-center text-[#5B0019] group-hover:scale-110 group-hover:bg-[#5B0019] group-hover:text-white transition-all duration-300">
                                                                    <FileText size={24} />
                                                                </div>
                                                                <div>
                                                                    <p className="font-black text-gray-900 text-lg leading-tight mb-0.5">{exam.title}</p>
                                                                    <div className="flex items-center gap-2">
                                                                        <span className="text-[10px] font-black text-[#5B0019] uppercase tracking-widest bg-red-50 px-2 py-0.5 rounded-md">{exam.subject}</span>
                                                                        <span className="text-[10px] font-bold text-gray-400 italic">ID: {exam.id.slice(-6).toUpperCase()}</span>
                                                                    </div>
                                                                </div>
                                                            </div>
                                                        </td>
                                                        <td className="px-8 py-8 text-center">
                                                            <div className="flex flex-col items-center">
                                                                <span className="text-xl font-black text-gray-800">{exam.total_submissions}</span>
                                                                <span className="text-[10px] font-bold text-gray-400 uppercase tracking-tighter">Học sinh</span>
                                                            </div>
                                                        </td>
                                                        <td className="px-8 py-8 text-center">
                                                            <div className="inline-flex items-center justify-center w-14 h-14 rounded-full bg-blue-50 border-4 border-white shadow-inner">
                                                                <span className="text-lg font-black text-blue-600">{(() => { const v = Number(exam.average_score); return (isNaN(v) || !isFinite(v)) ? "0.0" : v.toFixed(1); })()}</span>
                                                            </div>
                                                        </td>
                                                        <td className="px-8 py-8 text-center">
                                                            <div className="inline-flex items-center justify-center w-14 h-14 rounded-full bg-amber-50 border-4 border-white shadow-inner">
                                                                <span className="text-lg font-black text-amber-600">{(() => { const v = Number(exam.highest_score); return (isNaN(v) || !isFinite(v)) ? "0.0" : v.toFixed(1); })()}</span>
                                                            </div>
                                                        </td>
                                                        <td className="px-8 py-8 text-center">
                                                            {exam.violations_count > 0 ? (
                                                                <div className="flex flex-col items-center gap-1">
                                                                    <span className="w-10 h-10 bg-red-50 text-red-600 rounded-xl flex items-center justify-center font-black animate-pulse">{exam.violations_count}</span>
                                                                    <span className="text-[9px] font-black text-red-400 uppercase tracking-tighter">Cảnh báo</span>
                                                                </div>
                                                            ) : (
                                                                <span className="text-[10px] font-black text-green-500 uppercase">An toàn</span>
                                                            )}
                                                        </td>
                                                        <td className="px-8 py-8 text-center">
                                                            {(() => {
                                                                const now = currentTime;
                                                                const start = new Date(exam.start_time);
                                                                const end = new Date(exam.end_time);
                                                                
                                                                if (now < start) return (
                                                                    <span className="px-3 py-1.5 bg-blue-50 text-blue-600 text-[10px] font-black rounded-full uppercase tracking-widest border border-blue-100">Sắp mở</span>
                                                                );
                                                                if (now > end) return (
                                                                    <span className="px-3 py-1.5 bg-gray-100 text-gray-400 text-[10px] font-black rounded-full uppercase tracking-widest border border-gray-200">Đã đóng</span>
                                                                );
                                                                return (
                                                                    <span className="px-3 py-1.5 bg-green-50 text-green-600 text-[10px] font-black rounded-full uppercase tracking-widest border border-green-100">Đang mở</span>
                                                                );
                                                            })()}
                                                        </td>
                                                        <td className="px-10 py-8 text-right">
                                                            <button
                                                                onClick={() => fetchSubmissions(exam.id, exam.title)}
                                                                className="flex items-center gap-2 px-6 py-3 bg-gray-50 text-gray-600 hover:bg-[#5B0019] hover:text-white rounded-2xl font-black text-xs uppercase tracking-widest transition-all shadow-sm hover:shadow-lg active:scale-95"
                                                            >
                                                                Chi tiết <ChevronRight size={16} />
                                                            </button>
                                                        </td>
                                                    </tr>
                                                ))}
                                            </tbody>
                                        </table>
                                    </div>
                                </div>
                            </div>
                        )}
                    </div>
                ))}
            </div>

            {/* Submissions Modal */}
            {selectedExam && (
                <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-in fade-in duration-300">
                    <div className="bg-white w-full max-w-4xl rounded-[3rem] shadow-2xl overflow-hidden animate-in zoom-in-95 duration-300 border border-white/20">
                        <div className="p-8 border-b border-gray-100 flex items-center justify-between bg-gray-50/50">
                            <div>
                                <h2 className="text-2xl font-black text-gray-900 tracking-tight">{selectedExam.title}</h2>
                                <p className="text-gray-400 text-sm font-bold uppercase tracking-widest mt-1">Bảng điểm chi tiết học sinh</p>
                            </div>
                            <button
                                onClick={() => setSelectedExam(null)}
                                className="p-4 bg-white text-gray-400 hover:text-red-500 hover:shadow-md rounded-2xl transition-all active:scale-90"
                            >
                                <X size={24} />
                            </button>
                        </div>

                        <div className="p-8 overflow-y-auto max-h-[60vh]">
                            {loadingSubmissions ? (
                                <div className="py-20 text-center space-y-4">
                                    <div className="w-12 h-12 border-4 border-[#5B0019] border-t-transparent rounded-full animate-spin mx-auto"></div>
                                    <p className="text-gray-400 font-bold uppercase tracking-widest text-xs">Đang tải bảng điểm...</p>
                                </div>
                            ) : submissions.length > 0 ? (
                                <table className="w-full text-left border-collapse">
                                    <thead>
                                        <tr className="border-b border-gray-100">
                                            <th className="px-6 py-4 text-[10px] font-black text-gray-400 uppercase tracking-widest">Học sinh</th>
                                            <th className="px-6 py-4 text-[10px] font-black text-gray-400 uppercase tracking-widest text-center">Điểm số</th>
                                            <th className="px-6 py-4 text-[10px] font-black text-gray-400 uppercase tracking-widest text-center">Vi phạm</th>
                                            <th className="px-6 py-4 text-[10px] font-black text-gray-400 uppercase tracking-widest text-center">Trạng thái</th>
                                            <th className="px-6 py-4 text-[10px] font-black text-gray-400 uppercase tracking-widest text-right">Thời gian nộp</th>
                                        </tr>
                                    </thead>
                                    <tbody className="divide-y divide-gray-50">
                                        {submissions.map((sub) => (
                                            <tr key={`${sub.student_id}-${sub.submitted_at}`} className="hover:bg-gray-50/50 transition-colors">
                                                <td className="px-6 py-5">
                                                    <div className="flex items-center gap-3">
                                                        <div className="w-10 h-10 bg-gray-100 rounded-xl flex items-center justify-center text-gray-400">
                                                            <User size={18} />
                                                        </div>
                                                        <span className="font-black text-gray-900">{sub.student_name}</span>
                                                    </div>
                                                </td>
                                                <td className="px-6 py-5 text-center">
                                                    <span className={`text-xl font-black ${sub.score >= 8 ? 'text-green-600' : sub.score >= 5 ? 'text-blue-600' : 'text-red-500'}`}>
                                                        {(() => { const v = Number(sub.score); return (isNaN(v) || !isFinite(v)) ? "0.0" : v.toFixed(1); })()}
                                                    </span>
                                                </td>
                                                <td className="px-6 py-5 text-center">
                                                    {sub.violation_count > 0 ? (
                                                        <span className="px-3 py-1 bg-red-50 text-red-600 text-[10px] font-black rounded-full uppercase">
                                                            {sub.violation_count} lỗi
                                                        </span>
                                                    ) : (
                                                        <span className="text-[10px] font-black text-green-500 uppercase">0 lỗi</span>
                                                    )}
                                                </td>
                                                <td className="px-6 py-5 text-center">
                                                    {sub.status === 'completed' ? (
                                                        <div className="inline-flex items-center gap-1.5 text-green-500 font-bold text-[10px] uppercase tracking-widest">
                                                            <ShieldCheck size={14} /> Hoàn tất
                                                        </div>
                                                    ) : (
                                                        <div className="inline-flex items-center gap-1.5 text-red-500 font-bold text-[10px] uppercase tracking-widest">
                                                            <ShieldAlert size={14} /> Đình chỉ
                                                        </div>
                                                    )}
                                                </td>
                                                <td className="px-6 py-5 text-right font-medium text-gray-400 text-xs">
                                                    {sub.submitted_at ? new Date(sub.submitted_at).toLocaleString('vi-VN', {
                                                        timeZone: 'Asia/Ho_Chi_Minh',
                                                        day: '2-digit', month: '2-digit', year: 'numeric',
                                                        hour: '2-digit', minute: '2-digit'
                                                    }) : 'N/A'}
                                                </td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            ) : (
                                <div className="py-20 text-center text-gray-400 font-bold italic">
                                    Chưa có lượt nộp bài nào cho đề thi này.
                                </div>
                            )}
                        </div>
                        <div className="p-8 bg-gray-50/50 border-t border-gray-100 flex justify-end">
                            <button
                                onClick={() => setSelectedExam(null)}
                                className="px-8 py-4 bg-[#5B0019] text-white rounded-2xl font-black text-xs uppercase tracking-widest hover:shadow-lg active:scale-95 transition-all"
                            >
                                Đóng
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}
