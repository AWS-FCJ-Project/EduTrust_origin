"use client";

import React, { useEffect, useState } from 'react';
import { Edit, Trash2, Plus, Clock, FileText, CheckCircle2, Loader2, X, Save, AlertTriangle, PlusCircle, Calendar, GraduationCap, BookOpen } from 'lucide-react';
import TimePicker from '@/components/ui/TimePicker';
import Link from 'next/link';
import Cookies from 'js-cookie';

interface ExamItem {
    id: string;
    title: string;
    description: string;
    subject: string;
    class_id: string;
    start_time: string;
    end_time: string;
    duration?: number | string;
    questions: any[];
    // Temp fields for editing
    start_date?: string;
    start_time_only?: string;
    end_date?: string;
    end_time_only?: string;
}

const TeacherExams: React.FC = () => {
    const [exams, setExams] = useState<ExamItem[]>([]);
    const [classes, setClasses] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);
    const [user, setUser] = useState<any>(null);
    
    // Modals state
    const [editingExam, setEditingExam] = useState<ExamItem | null>(null);
    const [deletingExam, setDeletingExam] = useState<ExamItem | null>(null);
    const [isActionLoading, setIsActionLoading] = useState(false);

    const fetchData = async () => {
        try {
            const token = Cookies.get('auth_token');
            
            // Fetch user info
            const userRes = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/user-info`, {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            const userData = await userRes.json();
            setUser(userData);

            // Fetch classes
            const classesRes = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/classes`, {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            if (classesRes.ok) {
                const classesData = await classesRes.json();
                setClasses(classesData);
            }

            // Fetch exams
            const examsRes = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/exams`, {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            if (examsRes.ok) {
                const data = await examsRes.json();
                setExams(data);
            }
        } catch (error) {
            console.error("Error fetching data:", error);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchData();
    }, []);

    const handleDeleteExam = async () => {
        if (!deletingExam) return;
        setIsActionLoading(true);
        try {
            const token = Cookies.get('auth_token');
            const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/exams/${deletingExam.id}`, {
                method: 'DELETE',
                headers: { 'Authorization': `Bearer ${token}` }
            });
            if (res.ok) {
                setDeletingExam(null);
                fetchData();
            }
        } catch (error) {
            console.error("Error deleting exam:", error);
        } finally {
            setIsActionLoading(false);
        }
    };

    const handleUpdateExam = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!editingExam) return;
        setIsActionLoading(true);
        try {
            const token = Cookies.get('auth_token');
            const dataToUpdate = { ...editingExam };
            
            // Combine Date and Time for Start - LOCAL time
            let finalStart = "";
            const sDate = dataToUpdate.start_date || (dataToUpdate.start_time ? dataToUpdate.start_time.split('T')[0] : '');
            const sTime = dataToUpdate.start_time_only || (dataToUpdate.start_time ? new Date(dataToUpdate.start_time).toLocaleTimeString('vi-VN', {hour12: false, hour: '2-digit', minute: '2-digit'}) : '');
            
            if (sDate) {
                const localDate = new Date(`${sDate}T${sTime || "00:00"}`);
                finalStart = localDate.toISOString();
            } else {
                finalStart = dataToUpdate.start_time || new Date().toISOString();
            }

            // Combine Date and Time for End - LOCAL time
            let finalEnd = "";
            const eDate = dataToUpdate.end_date || (dataToUpdate.end_time ? dataToUpdate.end_time.split('T')[0] : '');
            const eTime = dataToUpdate.end_time_only || (dataToUpdate.end_time ? new Date(dataToUpdate.end_time).toLocaleTimeString('vi-VN', {hour12: false, hour: '2-digit', minute: '2-digit'}) : '00:00');
            
            if (eDate) {
                const localDate = new Date(`${eDate}T${eTime}`);
                finalEnd = localDate.toISOString();
            } else {
                finalEnd = dataToUpdate.end_time;
            }

            const payload = {
                ...editingExam,
                start_time: finalStart,
                end_time: finalEnd,
                duration: parseInt(editingExam.duration as string) || 0
            };

            const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/exams/${editingExam.id}`, {
                method: 'PATCH',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify(payload)
            });
            if (res.ok) {
                setEditingExam(null);
                fetchData();
            }
        } catch (error) {
            console.error("Error updating exam:", error);
        } finally {
            setIsActionLoading(false);
        }
    };

    const addQuestion = () => {
        if (!editingExam) return;
        setEditingExam({
            ...editingExam,
            questions: [...(editingExam.questions || []), { q: '', options: ['', '', '', ''], correct: 0 }]
        });
    };

    const removeQuestion = (idx: number) => {
        if (!editingExam) return;
        const newQ = [...editingExam.questions];
        newQ.splice(idx, 1);
        setEditingExam({ ...editingExam, questions: newQ });
    };

    if (loading) return (
        <div className="flex h-64 items-center justify-center">
            <Loader2 className="animate-spin text-[#5B0019]" size={40} />
        </div>
    );

    // Grouping logic
    const examsByClassId: Record<string, ExamItem[]> = exams.reduce((acc, exam) => {
        if (!acc[exam.class_id]) acc[exam.class_id] = [];
        acc[exam.class_id].push(exam);
        return acc;
    }, {} as Record<string, ExamItem[]>);

    return (
        <div className="space-y-12 animate-in fade-in duration-700">
            {/* Header section with Stats */}
            <div className="flex flex-col md:flex-row md:items-end justify-between gap-6">
                <div className="space-y-2">
                    <h1 className="text-4xl font-black text-gray-900 tracking-tight leading-none italic uppercase">
                        Kho Đề Thi
                    </h1>
                    <p className="text-gray-500 font-bold tracking-wide border-l-4 border-[#5B0019] pl-4">
                        Quản lý và tổ chức ngân hàng đề thi theo từng lớp học.
                    </p>
                </div>
                
                <div className="flex items-center gap-4">
                    <div className="bg-white px-6 py-4 rounded-[1.5rem] shadow-sm border border-gray-100 flex items-center gap-4">
                        <div className="text-right">
                            <p className="text-[10px] font-black uppercase text-gray-400 tracking-widest">Tổng đề thi</p>
                            <p className="text-2xl font-black text-gray-800">{exams.length}</p>
                        </div>
                        <div className="w-12 h-12 bg-red-50 rounded-2xl flex items-center justify-center text-[#5B0019]">
                            <BookOpen size={24} />
                        </div>
                    </div>
                    {user?.role !== 'student' && (
                        <Link 
                            href="/dashboard/exams/create"
                            className="bg-[#5B0019] text-white px-8 py-5 rounded-2xl font-black flex items-center gap-2 hover:bg-black transition-all shadow-xl shadow-red-900/10 uppercase tracking-wider text-sm active:scale-95"
                        >
                            <Plus size={20} /> Tạo đề thi mới
                        </Link>
                    )}
                </div>
            </div>

            {/* Display by Class sections */}
            {classes.length === 0 ? (
                <div className="bg-white p-20 rounded-[3rem] border border-gray-100 shadow-sm text-center space-y-4">
                    <div className="w-20 h-20 bg-gray-50 rounded-full flex items-center justify-center mx-auto text-gray-300">
                        <GraduationCap size={40} />
                    </div>
                    <p className="text-gray-400 font-bold italic">Bạn chưa được phân công lớp học nào.</p>
                </div>
            ) : (
                <div className="space-y-16">
                    {classes.map((cls) => {
                        const classExams = examsByClassId[cls.id] || [];
                        return (
                            <section key={cls.id} className="space-y-8 animate-in slide-in-from-bottom-4 duration-500">
                                {/* Class Header with Background */}
                                <div className="bg-gray-50/80 backdrop-blur-sm rounded-[2rem] p-6 border border-gray-100 flex items-center justify-between group shadow-sm">
                                    <div className="flex items-center gap-4">
                                        <div className="w-2 h-12 bg-[#5B0019] rounded-full"></div>
                                        <div>
                                            <div className="flex items-center gap-3 mb-0.5">
                                                <h2 className="text-2xl font-black text-gray-900 tracking-tight">Lớp {cls.name}</h2>
                                                <span className="px-3 py-1 bg-white border border-gray-100 text-[10px] font-black text-gray-400 rounded-full uppercase tracking-widest">Khối {cls.grade}</span>
                                            </div>
                                            <p className="text-sm font-bold text-gray-400 tracking-wide flex items-center gap-2">
                                                <Clock size={14} className="text-[#5B0019]" /> Có {classExams.length} đề thi hiện tại
                                            </p>
                                        </div>
                                    </div>
                                    
                                    <Link 
                                        href={`/dashboard/exams/create?class_id=${cls.id}`}
                                        className="px-6 py-4 bg-[#5B0019] text-white rounded-2xl transition-all shadow-md hover:shadow-xl hover:bg-black flex items-center gap-2 font-black text-xs uppercase tracking-widest active:scale-95"
                                    >
                                        <Plus size={18} /> Thêm đề cho lớp
                                    </Link>
                                </div>

                                {/* Exams Grid for this Class */}
                                {classExams.length > 0 ? (
                                    <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-8">
                                        {classExams.map((exam) => (
                                            <div key={exam.id} className="bg-white rounded-[2.5rem] border border-gray-100 shadow-sm hover:shadow-2xl transition-all p-8 group/card relative overflow-hidden flex flex-col">
                                                {/* Subject Badge */}
                                                <div className="absolute top-0 right-0 p-8">
                                                    <span className="px-4 py-2 bg-gray-50 border border-gray-100 text-[10px] font-black text-gray-400 rounded-xl uppercase tracking-widest group-hover/card:bg-[#5B0019] group-hover/card:text-white transition-colors">
                                                        {exam.subject}
                                                    </span>
                                                </div>

                                                <div className="space-y-4 flex-1">
                                                    <div className="w-14 h-14 bg-gray-50 rounded-2xl flex items-center justify-center text-gray-400 group-hover/card:bg-red-50 group-hover/card:text-[#5B0019] transition-all">
                                                        <FileText size={28} />
                                                    </div>
                                                    <div className="space-y-1">
                                                        <h3 className="text-xl font-black text-gray-800 leading-tight line-clamp-2">{exam.title}</h3>
                                                        <p className="text-xs text-gray-400 font-bold line-clamp-1 italic tracking-wide">
                                                            {exam.description || 'Không có mô tả chi tiết'}
                                                        </p>
                                                    </div>

                                                    <div className="pt-6 space-y-2">
                                                        <div className="flex items-center gap-3 text-xs font-bold text-gray-500">
                                                            <Calendar size={14} className="text-[#5B0019]" />
                                                            <span>Bắt đầu: {new Date(exam.start_time).toLocaleString('vi-VN', { hour: '2-digit', minute: '2-digit', day: '2-digit', month: '2-digit', year: 'numeric' }).replace(',', ' lúc')}</span>
                                                        </div>
                                                        <div className="flex items-center gap-3 text-xs font-bold text-gray-500">
                                                            <Clock size={14} className="text-gray-400" />
                                                            <span>Kết thúc: {new Date(exam.end_time).toLocaleString('vi-VN', { hour: '2-digit', minute: '2-digit', day: '2-digit', month: '2-digit', year: 'numeric' }).replace(',', ' lúc')}</span>
                                                        </div>
                                                    </div>
                                                </div>

                                                {/* Actions Footer */}
                                                <div className="mt-8 pt-6 border-t border-gray-50 flex items-center justify-between">
                                                    <div className="flex items-center gap-1">
                                                        <CheckCircle2 size={14} className="text-green-500" />
                                                        <span className="text-[10px] font-black uppercase text-green-600 tracking-tighter">Sẵn sàng</span>
                                                    </div>
                                                    <div className="flex items-center gap-2">
                                                        <button 
                                                            onClick={() => setEditingExam(exam)}
                                                            className="p-3 bg-gray-50 text-gray-400 hover:bg-gray-800 hover:text-white rounded-xl transition-all"
                                                            title="Chỉnh sửa"
                                                        >
                                                            <Edit size={18} />
                                                        </button>
                                                        <button 
                                                            onClick={() => setDeletingExam(exam)}
                                                            className="p-3 bg-red-50 text-red-400 hover:bg-red-500 hover:text-white rounded-xl transition-all"
                                                            title="Xóa đề thi"
                                                        >
                                                            <Trash2 size={18} />
                                                        </button>
                                                    </div>
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                ) : (
                                    <div className="bg-gray-50 rounded-[2.5rem] border border-dashed border-gray-200 p-12 text-center">
                                        <p className="text-gray-400 font-bold italic text-sm">Lớp {cls.name} chưa có đề thi nào trong hệ thống.</p>
                                        <Link 
                                            href={`/dashboard/exams/create?class_id=${cls.id}`}
                                            className="mt-4 inline-flex items-center gap-2 text-[#5B0019] text-xs font-black uppercase tracking-widest hover:underline"
                                        >
                                            <Plus size={14} /> Tạo đề ngay
                                        </Link>
                                    </div>
                                )}
                            </section>
                        );
                    })}
                </div>
            )}

            {/* Edit Exam Modal */}
            {editingExam && (
                <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-md animate-in fade-in duration-300">
                    <div className="w-full max-w-4xl bg-white rounded-[3rem] shadow-2xl overflow-hidden animate-in zoom-in-95 duration-300 max-h-[90vh] flex flex-col">
                        <div className="p-8 border-b bg-gray-50/50 flex items-center justify-between">
                            <div className="flex items-center gap-4">
                                <div className="p-3 bg-[#5B0019] text-white rounded-2xl">
                                    <Edit size={24} />
                                </div>
                                <div>
                                    <h2 className="text-xl font-black text-gray-800 tracking-tight">Chỉnh sửa đề thi</h2>
                                    <p className="text-xs text-gray-400 font-bold uppercase tracking-widest mt-0.5">Cập nhật nội dung & bộ câu hỏi</p>
                                </div>
                            </div>
                            <button onClick={() => setEditingExam(null)} className="p-2 hover:bg-gray-200 rounded-xl transition-all">
                                <X size={24} className="text-gray-400" />
                            </button>
                        </div>
                        
                        <form onSubmit={handleUpdateExam} className="flex-1 overflow-y-auto p-8 space-y-8 custom-scrollbar">
                            <div className="bg-gray-50 p-8 rounded-[2.5rem] border border-gray-100 space-y-8">
                                <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                                    <div className="space-y-2">
                                        <label className="text-[10px] font-black text-gray-400 uppercase tracking-widest pl-2">Tiêu đề đề thi</label>
                                        <input 
                                            required
                                            type="text" 
                                            value={editingExam.title}
                                            onChange={(e) => setEditingExam({...editingExam, title: e.target.value})}
                                            className="w-full px-6 py-4 bg-white border-none rounded-2xl focus:ring-2 focus:ring-[#5B0019] transition-all font-bold"
                                        />
                                    </div>
                                    <div className="space-y-2">
                                        <label className="text-[10px] font-black text-gray-400 uppercase tracking-widest pl-2">Môn học</label>
                                        <input 
                                            required
                                            type="text" 
                                            value={editingExam.subject}
                                            onChange={(e) => setEditingExam({...editingExam, subject: e.target.value})}
                                            className="w-full px-6 py-4 bg-white border-none rounded-2xl focus:ring-2 focus:ring-[#5B0019] transition-all font-bold"
                                        />
                                    </div>
                                </div>

                                <div className="grid grid-cols-1 md:grid-cols-1 gap-8">
                                    <div className="space-y-2 max-w-sm">
                                        <label className="text-[10px] font-black text-gray-400 uppercase tracking-widest pl-2">Lớp học</label>
                                        <select 
                                            required
                                            value={editingExam.class_id}
                                            onChange={(e) => setEditingExam({...editingExam, class_id: e.target.value})}
                                            className="w-full px-6 py-4 bg-white border-none rounded-2xl focus:ring-2 focus:ring-[#5B0019] transition-all font-bold"
                                        >
                                            <option value="">Chọn lớp</option>
                                            {classes.map(cls => (
                                                <option key={cls.id} value={cls.id}>{cls.name}</option>
                                            ))}
                                        </select>
                                    </div>

                                    <div className="grid grid-cols-1 md:grid-cols-2 gap-12 pt-4">
                                        {/* Start Date/Time */}
                                        <div className="space-y-4 p-6 bg-white rounded-[2rem] border border-gray-100 shadow-sm">
                                            <div className="flex items-center justify-between">
                                                <label className="text-[10px] font-black text-gray-400 uppercase tracking-widest pl-2">Ngày Bắt đầu</label>
                                                <button 
                                                    type="button"
                                                    onClick={() => {
                                                        const now = new Date();
                                                        setEditingExam({
                                                            ...editingExam, 
                                                            start_date: now.toISOString().split('T')[0],
                                                            start_time_only: now.toLocaleTimeString('vi-VN', {hour12: false, hour: '2-digit', minute: '2-digit'})
                                                        });
                                                    }}
                                                    className="text-[8px] font-black text-[#5B0019] uppercase tracking-tighter hover:underline"
                                                >Thời gian hiện tại</button>
                                            </div>
                                            <div className="flex items-center gap-4">
                                                <input 
                                                    type="date" 
                                                    value={editingExam.start_date || (editingExam.start_time ? new Date(editingExam.start_time).toLocaleDateString('en-CA') : '')}
                                                    onChange={(e) => setEditingExam({...editingExam, start_date: e.target.value})}
                                                    className="flex-1 px-6 py-4 bg-gray-50 border-none rounded-2xl focus:ring-2 focus:ring-[#5B0019] transition-all font-bold text-sm"
                                                />
                                                <TimePicker 
                                                    value={editingExam.start_time_only || (editingExam.start_time ? new Date(editingExam.start_time).toLocaleTimeString('vi-VN', {hour12: false, hour: '2-digit', minute: '2-digit'}) : '')}
                                                    onChange={(val) => setEditingExam({...editingExam, start_time_only: val})}
                                                    className="w-32"
                                                />
                                            </div>
                                        </div>

                                        {/* End Date/Time */}
                                        <div className="space-y-4 p-6 bg-white rounded-[2rem] border border-gray-100 shadow-sm">
                                            <label className="text-[10px] font-black text-gray-400 uppercase tracking-widest pl-2">Ngày Kết thúc</label>
                                            <div className="flex items-center gap-4">
                                                <input 
                                                    type="date" 
                                                    value={editingExam.end_date || (editingExam.end_time ? new Date(editingExam.end_time).toLocaleDateString('en-CA') : '')}
                                                    onChange={(e) => setEditingExam({...editingExam, end_date: e.target.value})}
                                                    className="flex-1 px-6 py-4 bg-gray-50 border-none rounded-2xl focus:ring-2 focus:ring-[#5B0019] transition-all font-bold text-sm"
                                                />
                                                <TimePicker 
                                                    value={editingExam.end_time_only || (editingExam.end_time ? new Date(editingExam.end_time).toLocaleTimeString('vi-VN', {hour12: false, hour: '2-digit', minute: '2-digit'}) : '00:00')}
                                                    onChange={(val) => setEditingExam({...editingExam, end_time_only: val})}
                                                    className="w-32"
                                                />
                                            </div>
                                        </div>
                                    </div>

                                    <div className="space-y-2 pt-4">
                                        <label className="text-[10px] font-black text-gray-400 uppercase tracking-widest pl-2">Thời gian làm bài (Phút)</label>
                                        <input 
                                            type="text" 
                                            inputMode="numeric"
                                            value={editingExam.duration === 0 ? '' : editingExam.duration}
                                            onChange={(e) => {
                                                const val = e.target.value.replace(/[^0-9]/g, '').replace(/^0+/, '');
                                                setEditingExam({...editingExam, duration: val === '' ? 0 : val});
                                            }}
                                            className="max-w-xs px-6 py-4 bg-white border-none rounded-2xl focus:ring-2 focus:ring-[#5B0019] transition-all font-bold text-xl"
                                            placeholder="Nhập thời gian làm bài"
                                        />
                                    </div>
                                </div>
                            </div>

                            <div className="space-y-6">
                                <div className="flex items-center justify-between px-4">
                                    <h3 className="text-xl font-black text-gray-800 tracking-tight">Bộ câu hỏi ({editingExam.questions?.length || 0})</h3>
                                    <button 
                                        type="button"
                                        onClick={addQuestion}
                                        className="flex items-center gap-2 text-indigo-600 font-bold hover:scale-105 transition-all text-sm uppercase tracking-widest"
                                    >
                                        <PlusCircle size={20} /> Thêm câu hỏi
                                    </button>
                                </div>
                                
                                <div className="space-y-4">
                                    {editingExam.questions?.map((q: any, qIdx: number) => (
                                        <div key={qIdx} className="bg-white p-8 rounded-[2rem] border border-gray-100 shadow-sm space-y-4 relative group/q">
                                            <div className="flex justify-between items-center">
                                                <span className="text-sm font-black text-[#5B0019] uppercase tracking-widest">Câu hỏi {qIdx + 1}</span>
                                                <button 
                                                    type="button"
                                                    onClick={() => removeQuestion(qIdx)}
                                                    className="p-2 text-red-400 hover:bg-red-50 rounded-xl transition-all opacity-0 group-hover/q:opacity-100"
                                                >
                                                    <Trash2 size={18} />
                                                </button>
                                            </div>
                                            <textarea 
                                                required
                                                placeholder="Nội dung câu hỏi..."
                                                value={q.q}
                                                onChange={(e) => {
                                                    const newQ = [...editingExam.questions];
                                                    newQ[qIdx].q = e.target.value;
                                                    setEditingExam({...editingExam, questions: newQ});
                                                }}
                                                className="w-full px-6 py-4 bg-gray-50 border-none rounded-2xl focus:ring-2 focus:ring-[#5B0019] transition-all font-bold italic text-sm"
                                            />
                                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                                {q.options.map((opt: string, oIdx: number) => (
                                                    <div key={oIdx} className={`flex items-center gap-3 p-3 rounded-2xl border transition-all ${
                                                        q.correct === oIdx ? 'bg-[#5B0019]/5 border-[#5B0019]/30 ring-1 ring-[#5B0019]/20' : 'bg-gray-50/50 border-transparent'
                                                    }`}>
                                                        <div className="flex flex-col items-center gap-1">
                                                            <input 
                                                                type="radio" 
                                                                checked={q.correct === oIdx}
                                                                onChange={() => {
                                                                    const newQ = [...editingExam.questions];
                                                                    newQ[qIdx].correct = oIdx;
                                                                    setEditingExam({...editingExam, questions: newQ});
                                                                }}
                                                                className="w-5 h-5 text-[#5B0019] focus:ring-[#5B0019]"
                                                            />
                                                            {q.correct === oIdx && <span className="text-[7px] font-black text-[#5B0019] uppercase">Đúng</span>}
                                                        </div>
                                                        <input 
                                                            required
                                                            placeholder={`Đáp án ${oIdx + 1}`}
                                                            value={opt}
                                                            onChange={(e) => {
                                                                const newQ = [...editingExam.questions];
                                                                newQ[qIdx].options[oIdx] = e.target.value;
                                                                setEditingExam({...editingExam, questions: newQ});
                                                            }}
                                                            className="flex-1 bg-transparent border-none focus:ring-0 text-sm font-bold"
                                                        />
                                                    </div>
                                                ))}
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        </form>
                        
                        <div className="p-8 border-t bg-gray-50/50 flex gap-4">
                            <button 
                                type="button"
                                onClick={() => setEditingExam(null)}
                                className="flex-1 py-4 bg-white border border-gray-200 rounded-2xl font-black text-sm text-gray-500 hover:bg-gray-50 transition-all uppercase tracking-widest shadow-sm"
                            >
                                Hủy bỏ
                            </button>
                            <button 
                                onClick={handleUpdateExam}
                                disabled={isActionLoading}
                                className="flex-[2] py-4 bg-[#5B0019] text-white rounded-2xl font-black text-sm hover:scale-[1.02] active:scale-95 transition-all uppercase tracking-widest flex items-center justify-center gap-2 shadow-lg shadow-red-900/10"
                            >
                                {isActionLoading ? <Loader2 className="animate-spin" size={20} /> : <Save size={20} />}
                                Lưu thay đổi
                            </button>
                        </div>
                    </div>
                </div>
            )}

            {/* Delete Confirmation Modal */}
            {deletingExam && (
                <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-md animate-in fade-in duration-300">
                    <div className="w-full max-w-md bg-white rounded-[3rem] shadow-2xl overflow-hidden animate-in zoom-in-95 duration-300">
                        <div className="p-10 text-center space-y-6">
                            <div className="mx-auto w-20 h-20 bg-red-50 text-red-500 rounded-full flex items-center justify-center animate-bounce duration-1000">
                                <AlertTriangle size={40} />
                            </div>
                            <div className="space-y-2">
                                <h2 className="text-2xl font-black text-gray-800 tracking-tight">Xóa đề thi?</h2>
                                <p className="text-gray-500 font-medium leading-relaxed">
                                    Bạn có chắc chắn muốn xóa đề thi <span className="text-gray-900 font-bold">"{deletingExam.title}"</span>? Hành động này không thể hoàn tác.
                                </p>
                            </div>
                            <div className="flex gap-4 pt-4">
                                <button 
                                    onClick={() => setDeletingExam(null)}
                                    className="flex-1 py-4 bg-gray-100 rounded-2xl font-black text-gray-500 hover:bg-gray-200 transition-all uppercase text-[10px] tracking-widest"
                                >
                                    Quay lại
                                </button>
                                <button 
                                    disabled={isActionLoading}
                                    onClick={handleDeleteExam}
                                    className="flex-1 py-4 bg-red-500 text-white rounded-2xl font-black shadow-lg shadow-red-900/20 hover:scale-[1.01] active:scale-95 transition-all flex items-center justify-center gap-2 uppercase text-[10px] tracking-widest"
                                >
                                    {isActionLoading ? <Loader2 className="animate-spin" size={18} /> : <Trash2 size={18} />}
                                    Xác nhận xóa
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            )}

            <style jsx>{`
                .custom-scrollbar::-webkit-scrollbar {
                    width: 6px;
                }
                .custom-scrollbar::-webkit-scrollbar-track {
                    background: transparent;
                }
                .custom-scrollbar::-webkit-scrollbar-thumb {
                    background: #eee;
                    border-radius: 10px;
                }
                .custom-scrollbar::-webkit-scrollbar-thumb:hover {
                    background: #ddd;
                }
            `}</style>
        </div>
    );
};

export default TeacherExams;
