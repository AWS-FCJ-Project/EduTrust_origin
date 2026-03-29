"use client";

import React, { useEffect, useState, useMemo } from 'react';
import Image from 'next/image';
import { ShieldAlert, User, Calendar, FileText, Loader2, AlertCircle, ChevronDown, Image as ImageIcon, History } from 'lucide-react';
import Cookies from 'js-cookie';

const ViolationsPage = () => {
    const [violations, setViolations] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);
    const [expandedIds, setExpandedIds] = useState<Set<string>>(new Set());

    const fetchViolations = async () => {
        try {
            const token = Cookies.get('auth_token');
            const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/exams/violations/all`, {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            if (res.ok) {
                const data = await res.json();
                setViolations(data);
            }
        } catch (error) {
            console.error("Error fetching violations:", error);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchViolations();
        // Refresh every 30 seconds to keep updated
        const interval = setInterval(fetchViolations, 30000);
        return () => clearInterval(interval);
    }, []);

    // Group violations by student, then by exam
    const groupedViolations = useMemo(() => {
        const studentGroups: { [key: string]: any } = {};
        violations.forEach(v => {
            if (!studentGroups[v.student_id]) {
                studentGroups[v.student_id] = {
                    student_id: v.student_id,
                    student_name: v.student_name,
                    student_class: v.student_class || "N/A",
                    exams: {}
                };
            }
            
            if (!studentGroups[v.student_id].exams[v.exam_id]) {
                studentGroups[v.student_id].exams[v.exam_id] = {
                    exam_id: v.exam_id,
                    exam_title: v.exam_title,
                    subject: v.subject,
                    exam_start: v.exam_start,
                    exam_end: v.exam_end,
                    last_violation: v.violation_time,
                    incidents: []
                };
            }
            
            studentGroups[v.student_id].exams[v.exam_id].incidents.push(v);
        });
        
        const result = Object.values(studentGroups).map((g: any) => {
            // Processing each exam to find unique images and filtering by threshold (>= 4)
            const filteredExams = Object.values(g.exams).map((exam: any) => {
                const uniqueImages = Array.from(new Set(exam.incidents.flatMap((inc: any) => inc.evidence_images || [])));
                return { ...exam, uniqueImages };
            }).filter((exam: any) => exam.uniqueImages.length >= 4);

            return {
                ...g,
                examList: filteredExams
            };
        }).filter((group: any) => group.examList.length > 0); // Only show students with at least 1 actual violation

        return result;
    }, [violations]);

    const toggleExpand = (id: string) => {
        const next = new Set(expandedIds);
        if (next.has(id)) next.delete(id);
        else next.add(id);
        setExpandedIds(next);
    };

    if (loading) return (
        <div className="flex h-[60vh] items-center justify-center">
            <div className="flex flex-col items-center gap-4">
                <Loader2 className="animate-spin text-[#5B0019]" size={48} />
                <p className="text-gray-400 font-black uppercase tracking-widest text-[10px]">Đang tải báo cáo vi phạm...</p>
            </div>
        </div>
    );

    const formatDate = (dateStr: string) => {
        if (!dateStr) return "N/A";
        const d = new Date(dateStr);
        return d.toLocaleString('vi-VN', { 
            day: '2-digit', month: '2-digit', year: 'numeric',
            hour: '2-digit', minute: '2-digit'
        }).replace(',', ' |');
    };

    return (
        <div className="max-w-6xl mx-auto space-y-10 pb-20 animate-in fade-in duration-700">
            {/* Header Section */}
            <div className="flex flex-col md:flex-row md:items-end justify-between gap-6">
                <div className="space-y-2">
                    <div className="inline-flex items-center gap-2 px-4 py-1.5 bg-red-50 text-[#5B0019] rounded-full text-[10px] font-black uppercase tracking-widest border border-red-100">
                        <ShieldAlert size={14} /> Hệ thống giám sát AI
                    </div>
                    <h1 className="text-4xl font-black text-gray-900 tracking-tight leading-none">Hồ Sơ Vi Phạm</h1>
                    <p className="text-gray-500 font-medium">Danh sách các học sinh bị đình chỉ thi do phát hiện gian lận nghiêm trọng.</p>
                </div>
                
                <div className="flex gap-4">
                    <div className="bg-white px-6 py-4 rounded-3xl shadow-sm border border-gray-100 flex items-center gap-4">
                        <div className="w-12 h-12 bg-red-50 text-red-600 rounded-2xl flex items-center justify-center">
                            <History size={24} />
                        </div>
                        <div>
                            <p className="text-[10px] font-black text-gray-400 uppercase tracking-widest leading-none mb-1">Tổng học sinh</p>
                            <p className="text-2xl font-black text-gray-900 leading-none">{groupedViolations.length}</p>
                        </div>
                    </div>
                </div>
            </div>

            {groupedViolations.length === 0 ? (
                <div className="bg-white p-32 rounded-[4rem] border-4 border-dashed border-gray-50 flex flex-col items-center justify-center text-center animate-in zoom-in duration-1000">
                    <div className="w-24 h-24 bg-green-50 text-green-500 rounded-full flex items-center justify-center mb-8">
                        <ShieldAlert size={48} className="opacity-40" />
                    </div>
                    <h2 className="text-2xl font-black text-gray-900 mb-2">Hệ Thống An Toàn</h2>
                    <p className="text-gray-400 font-medium max-w-xs">Hiện tại chưa ghi nhận trường hợp học sinh nào vi phạm quy chế thi.</p>
                </div>
            ) : (
                <div className="space-y-4">
                    {groupedViolations.map((group) => {
                        const isExpanded = expandedIds.has(group.student_id);
                        return (
                            <div key={group.student_id} className={`bg-white rounded-[2.5rem] border transition-all duration-500 overflow-hidden ${
                                isExpanded ? 'border-red-100 shadow-xl shadow-red-500/5' : 'border-gray-100 shadow-sm hover:border-red-100'
                            }`}>
                                {/* Card Outer */}
                                <div 
                                    onClick={() => toggleExpand(group.student_id)}
                                    className="p-6 md:p-8 flex items-center justify-between cursor-pointer group"
                                >
                                    <div className="flex items-center gap-6">
                                        <div className={`w-16 h-16 rounded-[1.5rem] flex items-center justify-center transition-all duration-500 ${
                                            isExpanded ? 'bg-[#5B0019] text-white rotate-6' : 'bg-gray-50 text-gray-400 group-hover:bg-red-50 group-hover:text-red-500'
                                        }`}>
                                            <User size={32} />
                                        </div>
                                        <div>
                                            <div className="flex items-center gap-3">
                                                <h3 className="text-2xl font-black text-gray-900 tracking-tight">{group.student_name}</h3>
                                                <span className="text-[10px] font-black text-[#5B0019] border border-[#5B0019]/20 bg-[#5B0019]/5 px-2 py-0.5 rounded-lg uppercase">
                                                    Lớp: {group.student_class}
                                                </span>
                                            </div>
                                            <div className="flex items-center gap-4 mt-1">
                                                <span className="text-[10px] font-black text-red-500 uppercase tracking-[0.2em] px-3 py-1 bg-red-50 rounded-full border border-red-100">
                                                    Đã bị khóa bài thi
                                                </span>
                                                <span className="text-[10px] font-bold text-gray-400 uppercase tracking-widest flex items-center gap-1.5">
                                                    <History size={12} /> {group.examList.length} bài thi vi phạm
                                                </span>
                                            </div>
                                        </div>
                                    </div>
                                    
                                    <div className={`w-12 h-12 rounded-full border flex items-center justify-center transition-all duration-300 ${
                                        isExpanded ? 'bg-gray-900 text-white border-gray-900 rotate-180' : 'bg-white text-gray-300 border-gray-100 group-hover:border-red-100 group-hover:text-red-500'
                                    }`}>
                                        <ChevronDown size={24} />
                                    </div>
                                </div>

                                {/* Card Inner */}
                                {isExpanded && (
                                    <div className="px-8 pb-8 space-y-8 animate-in slide-in-from-top-4 duration-500">
                                        <div className="w-full h-[1px] bg-gradient-to-r from-transparent via-gray-100 to-transparent mb-8"></div>
                                        
                                        {group.examList.map((exam: any, idx: number) => (
                                            <div key={exam.exam_id} className="space-y-6">
                                                {/* Violation Header Frame */}
                                                <div className="bg-gray-50/80 rounded-[2rem] p-6 border border-gray-100 flex flex-col md:flex-row items-center justify-between gap-4">
                                                    <div className="flex items-center gap-4">
                                                        <div className="p-3 bg-white rounded-2xl shadow-sm text-[#5B0019]">
                                                            <FileText size={20} />
                                                        </div>
                                                        <div>
                                                            <p className="text-[9px] font-black text-gray-400 uppercase tracking-widest leading-none mb-1">Tiêu đề bài thi / Môn</p>
                                                            <p className="text-lg font-black text-gray-900">{exam.exam_title || "Unknown Exam"}</p>
                                                            <p className="text-[10px] font-bold text-[#5B0019] opacity-70">Môn: {exam.subject}</p>
                                                        </div>
                                                    </div>
                                                    
                                                    <div className="flex items-center gap-8 pr-4">
                                                        <div className="text-right">
                                                            <p className="text-[9px] font-black text-gray-400 uppercase tracking-widest leading-none mb-1 flex items-center justify-end gap-1.5"><Calendar size={10} /> Thời gian ca thi</p>
                                                            <p className="text-sm font-black text-gray-700">
                                                                {formatDate(exam.exam_start)}
                                                            </p>
                                                        </div>
                                                        <div className="px-5 py-2 bg-red-600 text-white rounded-xl font-black text-[10px] uppercase tracking-widest shadow-lg shadow-red-600/20">
                                                            Bị đình chỉ
                                                        </div>
                                                    </div>
                                                </div>

                                                {/* Evidence Grid - Collect all and unique images from incidents */}
                                                <div className="space-y-3">
                                                    <div className="flex items-center gap-2 pl-2">
                                                        <ImageIcon size={14} className="text-gray-300" />
                                                        <span className="text-[10px] font-black text-gray-400 uppercase tracking-widest">
                                                            Bằng chứng AI ghi nhận ({exam.uniqueImages.length})
                                                        </span>
                                                    </div>
                                                    
                                                    <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-5 gap-3">
                                                        {exam.uniqueImages.length > 0 ? (
                                                            exam.uniqueImages.map((img: any, i: number) => (
                                                                <div 
                                                                    key={i} 
                                                                    className="aspect-video bg-gray-100 rounded-[1.5rem] border border-gray-100 overflow-hidden group/img relative shadow-sm hover:shadow-md transition-all cursor-zoom-in"
                                                                    onClick={() => window.open(`${process.env.NEXT_PUBLIC_API_URL}/camera/violation-image?path=${img}`, '_blank')}
                                                                >
                                                                    <Image
                                                                        src={`${process.env.NEXT_PUBLIC_API_URL}/camera/violation-image?path=${img}`}
                                                                        alt="violation proof"
                                                                        fill
                                                                        unoptimized
                                                                        sizes="(max-width: 768px) 50vw, 20vw"
                                                                        className="w-full h-full object-cover group-hover/img:scale-110 transition-transform duration-700"
                                                                    />
                                                                    <div className="absolute inset-0 bg-black/20 opacity-0 group-hover/img:opacity-100 transition-opacity flex items-center justify-center">
                                                                        <ImageIcon className="text-white" size={24} />
                                                                    </div>
                                                                </div>
                                                            ))
                                                        ) : (
                                                            <div className="col-span-full py-10 bg-gray-50 rounded-3xl border border-dashed border-gray-200 flex flex-col items-center justify-center text-gray-400">
                                                                <AlertCircle size={32} className="opacity-20 mb-2" />
                                                                <p className="text-xs font-bold uppercase tracking-widest">Không có dữ liệu ảnh bằng chứng</p>
                                                            </div>
                                                        )}
                                                    </div>
                                                </div>

                                                {idx < group.examList.length - 1 && (
                                                    <div className="pt-4 border-b border-gray-50"></div>
                                                )}
                                            </div>
                                        ))}
                                    </div>
                                )}
                            </div>
                        );
                    })}
                </div>
            )}
        </div>
    );
};

export default ViolationsPage;
