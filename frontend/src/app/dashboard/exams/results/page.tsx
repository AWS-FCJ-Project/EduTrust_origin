"use client";

import React, { useEffect, useState } from 'react';
import { FileText, Users, Award, Search, Eye, ChevronRight } from 'lucide-react';
import Cookies from 'js-cookie';

interface ExamStat {
    id: string;
    title: string;
    subject: string;
    total_submissions: number;
    average_score: number;
    highest_score: number;
    violations_count: number;
}

export default function StaffResultsPage() {
    const [exams, setExams] = useState<ExamStat[]>([]);
    const [loading, setLoading] = useState(true);
    const [searchTerm, setSearchTerm] = useState('');

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
                }
            } catch (error) {
                console.error("Error fetching staff results:", error);
            } finally {
                setLoading(false);
            }
        };
        fetchStaffResults();
    }, []);

    const filteredExams = exams.filter(e =>
        e.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
        e.subject.toLowerCase().includes(searchTerm.toLowerCase())
    );

    return (
        <div className="max-w-[75rem] mx-auto space-y-10 animate-in fade-in slide-in-from-bottom-5 duration-700">
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
                        placeholder="Tìm đề thi..."
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
                    { label: "Điểm Trung Bình", value: exams.length > 0 ? (exams.reduce((a, b) => a + (b.average_score || 0), 0) / exams.length).toFixed(1) : "0", icon: <Award />, color: "bg-amber-500" },
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

            <div className="bg-white rounded-[3rem] shadow-[0_32px_64px_-12px_rgba(0,0,0,0.04)] border border-gray-100 overflow-hidden">
                <div className="overflow-x-auto">
                    <table className="w-full text-left border-collapse">
                        <thead>
                            <tr className="bg-gray-50/50">
                                <th className="px-10 py-6 text-[11px] font-black text-gray-400 uppercase tracking-[0.2em]">Tên Đề Thi & Môn Học</th>
                                <th className="px-8 py-6 text-[11px] font-black text-gray-400 uppercase tracking-[0.2em] text-center">Lượt Thi</th>
                                <th className="px-8 py-6 text-[11px] font-black text-gray-400 uppercase tracking-[0.2em] text-center">ĐTB</th>
                                <th className="px-8 py-6 text-[11px] font-black text-gray-400 uppercase tracking-[0.2em] text-center">Cao Nhất</th>
                                <th className="px-8 py-6 text-[11px] font-black text-gray-400 uppercase tracking-[0.2em] text-center">Vi Phạm</th>
                                <th className="px-10 py-6"></th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-gray-50">
                            {loading ? (
                                <tr><td colSpan={6} className="py-20 text-center text-gray-400 font-black uppercase tracking-widest text-xs animate-pulse">Loading Results...</td></tr>
                            ) : filteredExams.map((exam, idx) => (
                                <tr key={idx} className="hover:bg-gray-50/70 transition-colors group">
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
                                            <span className="text-lg font-black text-blue-600">{exam.average_score.toFixed(1)}</span>
                                        </div>
                                    </td>
                                    <td className="px-8 py-8 text-center">
                                        <div className="inline-flex items-center justify-center w-14 h-14 rounded-full bg-amber-50 border-4 border-white shadow-inner">
                                            <span className="text-lg font-black text-amber-600">{exam.highest_score}</span>
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
                                    <td className="px-10 py-8 text-right">
                                        <button className="flex items-center gap-2 px-6 py-3 bg-gray-50 text-gray-600 hover:bg-[#5B0019] hover:text-white rounded-2xl font-black text-xs uppercase tracking-widest transition-all shadow-sm hover:shadow-lg active:scale-95">
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
    );
}
