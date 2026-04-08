"use client";

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import {
    Search, Clock, FileText, PlayCircle,
    CheckCircle, XCircle, BookOpen, Activity
} from 'lucide-react';

import Cookies from 'js-cookie';

const ExamListPage = () => {
    const [searchTerm, setSearchTerm] = useState("");
    const [activeTab, setActiveTab] = useState("all");
    const [exams, setExams] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);
    const [selectedExam, setSelectedExam] = useState<any>(null); // For Modal

    useEffect(() => {
        const fetchExams = async () => {
            try {
                const token = Cookies.get('auth_token');
                const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/exams`, {
                    headers: { 'Authorization': `Bearer ${token}` }
                });
                if (res.ok) {
                    const data = await res.json();
                    setExams(data);
                }
            } catch (error) {
                console.error("Error fetching exams:", error);
            } finally {
                setLoading(false);
            }
        };
        fetchExams();
    }, []);

    const isExamEnded = (exam: any) => {
        const endTime = exam?.end_time ? new Date(exam.end_time) : null;
        if (!endTime || Number.isNaN(endTime.getTime())) return false;
        return new Date() > endTime;
    };

    const filteredExams = exams.filter(exam => {
        const matchesSearch = exam.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
            exam.subject.toLowerCase().includes(searchTerm.toLowerCase());

        const ended = isExamEnded(exam);
        
        let matchesTab = true;
        if (activeTab === 'pending') matchesTab = (exam.status === 'pending' && !ended);
        else if (activeTab === 'completed') matchesTab = (exam.status === 'completed');
        else if (activeTab === 'failed') matchesTab = (exam.status === 'failed');
        else if (activeTab === 'ended') matchesTab = ended;

        return matchesSearch && matchesTab;
    });

    const sortedFilteredExams = [...filteredExams].sort(
        (a, b) => new Date(b.start_time).getTime() - new Date(a.start_time).getTime()
    );

        const getStatusBadge = (status: string, ended: boolean) => {
            if (ended && status === 'pending') {
            return <span className="flex items-center gap-1.5 px-3 py-1 bg-gray-100 text-gray-500 rounded-lg text-[10px] font-black uppercase tracking-wider border border-gray-200">{"\u0110\u00E3 k\u1EBFt th\u00FAc"}</span>;
            }
            switch (status) {
                case 'pending':
                return <span className="flex items-center gap-1.5 px-3 py-1 bg-blue-50 text-blue-600 rounded-lg text-[10px] font-black uppercase tracking-wider">{"Ch\u01B0a l\u00E0m"}</span>;
                case 'completed':
                return <span className="flex items-center gap-1.5 px-3 py-1 bg-green-50 text-green-600 rounded-lg text-[10px] font-black uppercase tracking-wider">{"\u0110\u00E3 ho\u00E0n th\u00E0nh"}</span>;
                case 'failed':
                return <span className="flex items-center gap-1.5 px-3 py-1 bg-red-50 text-red-600 rounded-lg text-[10px] font-black uppercase tracking-wider border border-red-100">{"B\u1ECB h\u1EE7y"}</span>;
                default:
                return null;
            }
        };

    const formatShortTime = (dateStr: string) => {
        if (!dateStr) return "---";
        const d = new Date(dateStr);
        return d.toLocaleString('vi-VN', { 
            hour: '2-digit', 
            minute: '2-digit',
            day: '2-digit',
            month: '2-digit',
            year: 'numeric'
        }).replace(',', ' lúc');
    };

    return (
        <div className="w-full min-h-screen bg-transparent p-4 md:p-8 font-sans text-gray-900 animate-in fade-in duration-700">
            <div className="max-w-6xl mx-auto space-y-10">
                {/* Header Section */}
                <div className="flex flex-col md:flex-row md:items-center justify-between gap-8 py-4">
                    <div className="space-y-1">
                        <h1 className="text-4xl font-black text-gray-950 tracking-tighter">
                            {"B\u00E0i thi c\u1EE7a t\u00F4i"}
                        </h1>
                        <p className="text-gray-400 font-medium text-sm">
                            {"Qu\u1EA3n l\u00FD v\u00E0 theo d\u00F5i tr\u00ECnh \u0111\u1ED9 chuy\u00EAn m\u00F4n c\u1EE7a b\u1EA1n."}
                        </p>
                    </div>

                    <div className="relative group">
                        <div className="absolute inset-y-0 left-0 pl-5 flex items-center pointer-events-none text-gray-400 group-focus-within:text-[#5B0019] transition-colors">
                            <Search size={18} />
                        </div>
                        <input
                            type="text"
                            placeholder={"T\u00ECm nhanh b\u00E0i thi..."}
                            value={searchTerm}
                            onChange={(e) => setSearchTerm(e.target.value)}
                            className="block w-full md:w-80 pl-12 pr-6 py-4 bg-white border-none rounded-[2rem] text-sm font-bold placeholder-gray-300 focus:ring-4 focus:ring-[#5B0019]/5 transition-all shadow-xl shadow-gray-200/40"
                        />
                    </div>
                </div>

                {/* Tab Filter Section */}
                <div className="flex items-center gap-2 p-1.5 bg-gray-100/80 rounded-[2rem] w-fit shadow-inner">
                    {[
                        { id: 'all', label: 'T\u1EA5t c\u1EA3' },
                        { id: 'pending', label: 'Ch\u01B0a l\u00E0m' },
                        { id: 'completed', label: '\u0110\u00E3 ho\u00E0n th\u00E0nh' },
                        { id: 'failed', label: 'B\u1ECB h\u1EE7y' }
                    ].concat([{ id: 'ended', label: '\u0110\u00E3 k\u1EBFt th\u00FAc' }]).map(tab => (
                        <button
                            key={tab.id}
                            onClick={() => setActiveTab(tab.id)}
                            className={`px-8 py-3 rounded-[1.8rem] text-[13px] font-black transition-all tracking-tight ${activeTab === tab.id
                                ? 'bg-white text-[#5B0019] shadow-lg shadow-gray-200/60 scale-100'
                                : 'text-gray-400 hover:text-gray-600'
                                }`}
                        >
                            {tab.label}
                        </button>
                    ))}
                </div>

                {/* Exam Grid */}
                <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-2 gap-8">
                    {loading ? (
                        Array(4).fill(0).map((_, i) => (
                            <div key={i} className="bg-white/40 h-64 rounded-[3rem] animate-pulse border border-gray-100/50"></div>
                        ))
                    ) : (
                        sortedFilteredExams.length > 0 ? (
                            sortedFilteredExams.map(exam => (
                                <div
                                    key={exam.id}
                                    className="bg-white rounded-[3rem] p-8 border border-gray-100/60 shadow-2xl shadow-gray-200/40 hover:shadow-[#5B0019]/10 hover:-translate-y-1 transition-all duration-500 flex flex-col relative overflow-hidden group"
                                >
                                    <div className="flex justify-between items-start mb-6">
                                        <div className="space-y-3">
                                            <div className="flex items-center gap-3 text-gray-400">
                                                <div className="w-10 h-10 rounded-2xl bg-gray-50 flex items-center justify-center text-[#5B0019] shadow-sm">
                                                    <BookOpen size={18} />
                                                </div>
                                                <span className="text-xs font-black uppercase tracking-widest">{exam.subject}</span>
                                            </div>
                                            <h3 className="text-2xl font-black text-gray-900 leading-tight group-hover:text-[#5B0019] transition-colors">
                                                {exam.title}
                                            </h3>
                                        </div>
                                        {getStatusBadge(exam.status, isExamEnded(exam))}
                                    </div>

                                    <div className="flex flex-wrap items-center gap-3 mb-8">
                                        <div className="flex items-center gap-2 bg-gray-50 px-4 py-2.5 rounded-2xl text-gray-500 font-bold text-xs ring-1 ring-gray-100">
                                            <Clock size={15} /> {exam.duration || 60} phút
                                        </div>
                                        <div className="flex items-center gap-2 bg-gray-50 px-4 py-2.5 rounded-2xl text-gray-500 font-bold text-xs ring-1 ring-gray-100">
                                            <FileText size={15} /> {exam.questions?.length || 0} câu
                                        </div>
                                        <div className="flex items-center gap-2 bg-red-50 px-4 py-2.5 rounded-2xl text-[#5B0019] font-black text-[10px] ring-1 ring-red-100 uppercase tracking-tighter">
                                            Hạn: {formatShortTime(exam.end_time)}
                                        </div>
                                    </div>

                                    <div className="mt-auto pt-6 border-t border-gray-50 flex items-center justify-between">
                                        <div className="flex flex-col">
                                            <span className="text-[10px] font-black text-gray-300 uppercase tracking-widest">Bắt đầu</span>
                                            <span className="text-sm font-black text-gray-800 tracking-tight">{formatShortTime(exam.start_time)}</span>
                                        </div>

                                        {exam.status === 'pending' ? (
                                            (() => {
                                                const ended = isExamEnded(exam);
                                                if (ended) {
                                                    return (
                                                        <div className="bg-gray-100 text-gray-500 px-8 py-3.5 rounded-2xl font-black text-xs uppercase tracking-widest flex items-center gap-2 cursor-not-allowed border border-gray-200">
                                                            <XCircle size={18} /> Đã kết thúc
                                                        </div>
                                                    );
                                                }
                                                const isStarted = new Date() >= new Date(exam.start_time);
                                                return isStarted ? (
                                                    <Link
                                                        href={`/dashboard/exam_detail/${exam.id}`}
                                                        className="bg-[#5B0019] text-white px-8 py-3.5 rounded-2xl font-black text-xs uppercase tracking-widest flex items-center gap-2 hover:bg-black transition-all shadow-xl shadow-red-900/20 active:scale-95 group-hover:px-10"
                                                    >
                                                        <PlayCircle size={18} /> Vào thi
                                                    </Link>
                                                ) : (
                                                    <div className="bg-gray-100 text-gray-400 px-8 py-3.5 rounded-2xl font-black text-xs uppercase tracking-widest flex items-center gap-2 cursor-not-allowed border border-gray-100">
                                                        <Clock size={18} /> Chưa bắt đầu
                                                    </div>
                                                );
                                            })()
                                        ) : exam.status === 'completed' ? (
                                            <button 
                                                onClick={() => setSelectedExam(exam)}
                                                className="bg-gray-100 text-gray-500 hover:bg-black hover:text-white px-8 py-3.5 rounded-2xl font-black text-xs uppercase tracking-widest flex items-center gap-2 transition-all active:scale-95"
                                            >
                                                <Activity size={18} /> Chi tiết
                                            </button>
                                        ) : (
                                            <div className="bg-red-50 text-red-300 px-8 py-3.5 rounded-2xl font-black text-xs uppercase tracking-widest flex items-center gap-2 cursor-not-allowed border border-red-50">
                                                <XCircle size={18} /> Đã bị hủy
                                            </div>
                                        )}
                                    </div>
                                </div>
                            ))
                        ) : (
                            <div className="col-span-full py-32 flex flex-col items-center justify-center text-gray-300 space-y-6 bg-white/40 rounded-[4rem] border-2 border-dashed border-gray-100">
                                <Search size={64} strokeWidth={1} />
                                <div className="text-center space-y-1">
                                    <p className="text-xl font-black text-gray-400">Danh sách trống</p>
                                    <p className="text-sm font-medium">Chúng tôi không tìm thấy bài thi nào phù hợp.</p>
                                </div>
                            </div>
                        )
                    )}
                </div>
            </div>

            {/* Result Modal */}
            {selectedExam && (
                <div className="fixed inset-0 z-[10000] flex items-center justify-center p-4 md:p-8 animate-in fade-in duration-300">
                    <div className="absolute inset-0 bg-black/60 backdrop-blur-md" onClick={() => setSelectedExam(null)}></div>
                    <div className="relative bg-white w-full max-w-lg rounded-[3.5rem] p-10 shadow-2xl overflow-hidden animate-in zoom-in duration-300">
                        <div className="absolute top-0 left-0 w-full h-2 bg-[#5B0019]"></div>
                        
                        <div className="flex flex-col items-center text-center space-y-6">
                            <div className="w-24 h-24 rounded-[2.5rem] bg-green-50 text-green-600 flex items-center justify-center shadow-inner scale-110 mb-2">
                                <CheckCircle size={48} />
                            </div>
                            
                            <div className="space-y-2">
                                <h2 className="text-3xl font-black text-gray-950 tracking-tight">Hoàn thành bài thi</h2>
                                <p className="text-[#5B0019] font-black uppercase text-[11px] tracking-[0.2em]">{selectedExam.subject}</p>
                            </div>

                            <div className="w-full grid grid-cols-2 gap-4">
                                <div className="bg-gray-50 p-6 rounded-[2rem] border border-gray-100 flex flex-col items-center gap-2">
                                    <span className="text-[10px] font-black text-gray-400 uppercase tracking-widest">Thời gian nộp</span>
                                    <span className="text-sm font-black text-gray-800">{formatShortTime(selectedExam.submitted_at)}</span>
                                </div>
                                <div className="bg-gray-50 p-6 rounded-[2rem] border border-gray-100 flex flex-col items-center gap-2">
                                    <span className="text-[10px] font-black text-gray-400 uppercase tracking-widest">Số lỗi AI</span>
                                    <span className={`text-lg font-black ${selectedExam.violation_count > 0 ? 'text-red-600' : 'text-green-600'}`}>
                                        {selectedExam.violation_count}
                                    </span>
                                </div>
                            </div>

                            <button 
                                onClick={() => setSelectedExam(null)}
                                className="w-full py-5 bg-[#5B0019] text-white rounded-[2rem] font-black text-sm uppercase tracking-widest transition-all hover:bg-black shadow-xl shadow-red-900/20 active:scale-95"
                            >
                                Đóng lại
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

export default ExamListPage;
