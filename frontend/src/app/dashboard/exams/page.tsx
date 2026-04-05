"use client";

import React, { useEffect, useState } from 'react';
import { Edit, Trash2, Plus, Clock, FileText, CheckCircle2, Loader2, X, Save, AlertTriangle, PlusCircle, Calendar, GraduationCap, BookOpen, KeyRound, RefreshCw, Copy, Check, Search } from 'lucide-react';
import TimePicker from '@/components/ui/TimePicker';
import Link from 'next/link';
import Cookies from 'js-cookie';

const SUBJECTS = [
    "Toán học", "Vật lí", "Hóa học", "Sinh học", "Ngữ văn",
    "Lịch sử", "Địa lí", "Tiếng Anh", "Công nghệ", "Tin học",
    "Giáo dục kinh tế và pháp luật", "Giáo dục thể chất", "Giáo dục quốc phòng và an ninh"
];

const EXAM_TYPES = [
    "Kiểm tra miệng", "Kiểm tra 15 phút", "Kiểm tra 1 tiết", "Kiểm giữa kỳ", "Kiểm học kỳ"
];

interface ExamItem {
    id: string;
    title: string;
    description: string;
    subject: string;
    exam_type?: string;
    class_id: string;
    start_time: string;
    end_time: string;
    duration?: number | string;
    questions: any[];
    has_secret_key?: boolean;
    secret_key?: string;
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
    const [expandedClasses, setExpandedClasses] = useState<Record<string, boolean>>({});
    
    // Modals state
    const [editingExam, setEditingExam] = useState<ExamItem | null>(null);
    const [deletingExam, setDeletingExam] = useState<ExamItem | null>(null);
    const [secretKeyExam, setSecretKeyExam] = useState<ExamItem | null>(null);
    const [secretKeyValue, setSecretKeyValue] = useState<string | null>(null);
    const [secretKeyCopied, setSecretKeyCopied] = useState(false);
    const [secretKeyLoading, setSecretKeyLoading] = useState(false);
    const [isActionLoading, setIsActionLoading] = useState(false);
    const [subjectSearch, setSubjectSearch] = useState('');
    const [showSubjectDropdown, setShowSubjectDropdown] = useState(false);
    const [lastExamId, setLastExamId] = useState<string | null>(null);
    const [currentTime, setCurrentTime] = useState(new Date());

    useEffect(() => {
        const timer = setInterval(() => setCurrentTime(new Date()), 10000);
        return () => clearInterval(timer);
    }, []);

    const autoResize = (e: React.SyntheticEvent<HTMLTextAreaElement>) => {
        const element = e.currentTarget;
        element.style.height = 'auto';
        element.style.height = `${element.scrollHeight}px`;
    };

    const filteredSubjects = SUBJECTS.filter((subject) =>
        subject.toLowerCase().includes(subjectSearch.toLowerCase())
    );

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

    useEffect(() => {
        if (editingExam) {
            if (editingExam.id !== lastExamId) {
                setSubjectSearch(editingExam.subject || '');
                setLastExamId(editingExam.id);
            }
        } else {
            setSubjectSearch('');
            setLastExamId(null);
            setShowSubjectDropdown(false);
        }
    }, [editingExam, lastExamId]);

    useEffect(() => {
        const handleClickOutside = (e: MouseEvent) => {
            if (showSubjectDropdown && !(e.target as HTMLElement).closest('.subject-selection')) {
                setShowSubjectDropdown(false);
            }
        };
        document.addEventListener('mousedown', handleClickOutside);
        return () => document.removeEventListener('mousedown', handleClickOutside);
    }, [showSubjectDropdown]);

    const openSecretKeyPanel = async (exam: ExamItem) => {
        setSecretKeyExam(exam);
        setSecretKeyValue(null);
        setSecretKeyLoading(true);
        try {
            const token = Cookies.get('auth_token');
            const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/exams/${exam.id}/secret-key`, {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            if (res.ok) {
                const data = await res.json();
                setSecretKeyValue(data.secret_key);
            }
        } catch (error) {
            console.error("Error loading secret key:", error);
        } finally {
            setSecretKeyLoading(false);
        }
    };

    const handleRegenerateKey = async () => {
        if (!secretKeyExam) return;
        setSecretKeyLoading(true);
        try {
            const token = Cookies.get('auth_token');
            const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/exams/${secretKeyExam.id}/regenerate-key`, {
                method: 'POST',
                headers: { 'Authorization': `Bearer ${token}` }
            });
            if (res.ok) {
                const data = await res.json();
                setSecretKeyValue(data.secret_key);
                setSecretKeyCopied(false);
            }
        } catch (error) {
            console.error("Error regenerating key:", error);
        } finally {
            setSecretKeyLoading(false);
        }
    };

    const handleCopySecretKey = () => {
        if (!secretKeyValue) return;
        navigator.clipboard.writeText(secretKeyValue);
        setSecretKeyCopied(true);
        setTimeout(() => setSecretKeyCopied(false), 2000);
    };

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
            const eTime = dataToUpdate.end_time_only || (dataToUpdate.end_time ? new Date(dataToUpdate.end_time).toLocaleTimeString('vi-VN', {hour12: false, hour: '2-digit', minute: '2-digit'}) : '23:59');
            
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
                duration: parseInt(editingExam.duration as string) || 0,
                exam_type: editingExam.exam_type || 'Kiểm tra 15 phút',
            };

            if (!SUBJECTS.includes(payload.subject)) {
                alert("Vui lòng chọn môn học từ danh sách");
                setIsActionLoading(false);
                return;
            }

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

    const toggleClassExpanded = (classId: string) => {
        setExpandedClasses((prev) => ({ ...prev, [classId]: !prev[classId] }));
    };

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
                        const sortedClassExams = [...classExams].sort(
                            (a, b) => new Date(b.start_time).getTime() - new Date(a.start_time).getTime()
                        );
                        const isExpanded = !!expandedClasses[cls.id];
                        return (
                            <section key={cls.id} className="space-y-8 animate-in slide-in-from-bottom-4 duration-500">
                                {/* Class Header with Background */}
                                <div className="bg-gray-50/80 backdrop-blur-sm rounded-[2rem] p-6 border border-gray-100 flex items-center justify-between group shadow-sm">
                                    <div
                                        className="flex items-center gap-4 cursor-pointer select-none"
                                        onClick={() => toggleClassExpanded(cls.id)}
                                        role="button"
                                        tabIndex={0}
                                        onKeyDown={(e) => {
                                            if (e.key === "Enter" || e.key === " ") toggleClassExpanded(cls.id);
                                        }}
                                        aria-expanded={isExpanded}
                                    >
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
                                {isExpanded ? (sortedClassExams.length > 0 ? (
                                    <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-8">
                                        {sortedClassExams.map((exam) => (
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
                                                        {exam.description && (
                                                            <p className="text-xs text-gray-400 font-bold line-clamp-1 italic tracking-wide">
                                                                {exam.description}
                                                            </p>
                                                        )}
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

                                                <div className="mt-8 pt-6 border-t border-gray-50 flex items-center justify-between">
                                                    <div className="flex items-center gap-1">
                                                        {(() => {
                                                            const now = currentTime;
                                                            const start = new Date(exam.start_time);
                                                            const end = new Date(exam.end_time);
                                                            
                                                            if (now < start) return (
                                                                <span className="px-3 py-1 bg-blue-50 text-blue-600 text-[9px] font-black rounded-lg uppercase tracking-widest border border-blue-100">Sắp mở</span>
                                                            );
                                                            if (now > end) return (
                                                                <span className="px-3 py-1 bg-gray-100 text-gray-400 text-[9px] font-black rounded-lg uppercase tracking-widest border border-gray-200">Đã đóng</span>
                                                            );
                                                            return (
                                                                <span className="px-3 py-1 bg-green-50 text-green-600 text-[9px] font-black rounded-lg uppercase tracking-widest border border-green-100">Đang mở</span>
                                                            );
                                                        })()}
                                                    </div>
                                                    <div className="flex items-center gap-2">
                                                        <button 
                                                            onClick={() => openSecretKeyPanel(exam)}
                                                            className="p-3 bg-amber-50 text-amber-500 hover:bg-amber-500 hover:text-white rounded-xl transition-all"
                                                            title="Xem mã đề thi"
                                                        >
                                                            <KeyRound size={18} />
                                                        </button>
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
                                )) : null}
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
                                    <div className="space-y-2 relative subject-selection">
                                        <label className="text-[10px] font-black text-gray-400 uppercase tracking-widest pl-2 flex justify-between">
                                            <span>Môn học</span>
                                            {SUBJECTS.includes(editingExam.subject) && <span className="text-[#005B19] text-[8px] font-black uppercase tracking-widest">Đã chọn</span>}
                                        </label>
                                        <div className="relative">
                                            <Search className="absolute left-6 top-1/2 -translate-y-1/2 text-gray-400" size={16} />
                                            <input
                                                required
                                                type="text"
                                                value={subjectSearch}
                                                onFocus={() => setShowSubjectDropdown(true)}
                                                onChange={(e) => {
                                                    setSubjectSearch(e.target.value);
                                                    setEditingExam({ ...editingExam, subject: '' });
                                                    setShowSubjectDropdown(true);
                                                }}
                                                className={`w-full pl-14 pr-12 py-4 bg-white border-none rounded-2xl focus:ring-2 transition-all font-bold ${
                                                    SUBJECTS.includes(editingExam.subject) ? 'focus:ring-[#005B19]/20' : 'focus:ring-[#5B0019]'
                                                }`}
                                                placeholder="Tìm kiếm môn học..."
                                            />
                                            {subjectSearch && (
                                                <button
                                                    type="button"
                                                    onClick={() => {
                                                        setSubjectSearch('');
                                                        setEditingExam({ ...editingExam, subject: '' });
                                                    }}
                                                    className="absolute right-4 top-1/2 -translate-y-1/2 text-gray-400 hover:text-red-500 transition-colors"
                                                >
                                                    <Plus className="rotate-45" size={18} />
                                                </button>
                                            )}
                                        </div>

                                        {showSubjectDropdown && (
                                            <div className="absolute z-[100] w-full mt-2 bg-white rounded-2xl shadow-2xl border border-gray-100 max-h-60 overflow-y-auto p-2 scrollbar-thin scrollbar-thumb-gray-200">
                                                {filteredSubjects.length > 0 ? filteredSubjects.map((subject) => (
                                                    <button
                                                        key={subject}
                                                        type="button"
                                                        onClick={() => {
                                                            setEditingExam({ ...editingExam, subject });
                                                            setSubjectSearch(subject);
                                                            setShowSubjectDropdown(false);
                                                        }}
                                                        className="w-full text-left px-4 py-3 rounded-xl hover:bg-gray-50 flex items-center justify-between group transition-colors"
                                                    >
                                                        <span className={`font-bold ${editingExam.subject === subject ? 'text-[#005B19]' : 'text-gray-600'}`}>{subject}</span>
                                                        {editingExam.subject === subject && <Check size={14} className="text-[#005B19]" />}
                                                    </button>
                                                )) : (
                                                    <div className="px-4 py-3 text-gray-400 font-bold text-center">Không tìm thấy môn học</div>
                                                )}
                                            </div>
                                        )}
                                    </div>
                                </div>

                                <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                                    <div className="space-y-2">
                                        <label className="text-[10px] font-black text-gray-400 uppercase tracking-widest pl-2">Loại đề thi</label>
                                        <select
                                            required
                                            value={editingExam.exam_type || 'Kiểm tra 15 phút'}
                                            onChange={(e) => setEditingExam({ ...editingExam, exam_type: e.target.value })}
                                            className="w-full px-6 py-4 bg-white border-none rounded-2xl focus:ring-2 focus:ring-[#5B0019] transition-all font-bold appearance-none cursor-pointer"
                                        >
                                            {EXAM_TYPES.map((type) => (
                                                <option key={type} value={type}>{type}</option>
                                            ))}
                                        </select>
                                    </div>
                                    <div className="space-y-2">
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
                                </div>

                                <div className="grid grid-cols-1 md:grid-cols-1 gap-8">
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
                                                rows={1}
                                                placeholder="Nội dung câu hỏi..."
                                                value={q.q}
                                                onChange={(e) => {
                                                    const newQ = [...editingExam.questions];
                                                    newQ[qIdx].q = e.target.value;
                                                    setEditingExam({...editingExam, questions: newQ});
                                                    autoResize(e);
                                                }}
                                                onFocus={autoResize}
                                                className="w-full px-6 py-4 bg-gray-50 border-none rounded-2xl focus:ring-2 focus:ring-[#5B0019] transition-all font-bold italic text-sm resize-none overflow-hidden break-words"
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
                                                        <textarea 
                                                            required
                                                            rows={1}
                                                            placeholder={`Đáp án ${oIdx + 1}`}
                                                            value={opt}
                                                            onChange={(e) => {
                                                                const newQ = [...editingExam.questions];
                                                                newQ[qIdx].options[oIdx] = e.target.value;
                                                                setEditingExam({...editingExam, questions: newQ});
                                                                autoResize(e);
                                                            }}
                                                            onFocus={autoResize}
                                                            className="flex-1 bg-transparent border-none focus:ring-0 text-sm font-bold resize-none overflow-hidden break-words"
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

            {secretKeyExam && (
                <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-md animate-in fade-in duration-300">
                    <div className="w-full max-w-md bg-white rounded-[3rem] shadow-2xl overflow-hidden animate-in zoom-in-95 duration-300">
                        <div className="p-8 border-b bg-amber-50/50 flex items-center justify-between">
                            <div className="flex items-center gap-4">
                                <div className="p-3 bg-amber-500 text-white rounded-2xl">
                                    <KeyRound size={22} />
                                </div>
                                <div>
                                    <h2 className="text-lg font-black text-gray-800 tracking-tight">Mã Đề Thi</h2>
                                    <p className="text-xs text-gray-400 font-bold uppercase tracking-widest mt-0.5 line-clamp-1">{secretKeyExam.title}</p>
                                </div>
                            </div>
                            <button onClick={() => setSecretKeyExam(null)} className="p-2 hover:bg-gray-200 rounded-xl transition-all">
                                <X size={22} className="text-gray-400" />
                            </button>
                        </div>

                        <div className="p-10 text-center space-y-8">
                            <div className="bg-[#5B0019]/5 border-2 border-[#5B0019]/15 rounded-3xl p-8 space-y-4">
                                <p className="text-xs font-black text-gray-400 uppercase tracking-widest">Mã Bí Mật</p>
                                {secretKeyLoading ? (
                                    <div className="flex justify-center py-4"><Loader2 className="animate-spin text-[#5B0019]" size={36} /></div>
                                ) : (
                                    <div className="flex items-center justify-center gap-4">
                                        <span className="text-5xl font-black text-[#5B0019] tracking-[0.35em] font-mono">
                                            {secretKeyValue || '------'}
                                        </span>
                                        <button
                                            onClick={handleCopySecretKey}
                                            disabled={!secretKeyValue}
                                            className={`p-3 rounded-2xl transition-all ${
                                                secretKeyCopied 
                                                    ? 'bg-green-500 text-white'
                                                    : 'bg-white border border-gray-200 text-gray-400 hover:text-[#5B0019] hover:border-[#5B0019] disabled:opacity-40'
                                            }`}
                                        >
                                            {secretKeyCopied ? <Check size={20} /> : <Copy size={20} />}
                                        </button>
                                    </div>
                                )}
                                <p className="text-xs text-gray-400 font-medium">Học sinh nhập mã này trước khi vào thi</p>
                            </div>

                            <button
                                onClick={handleRegenerateKey}
                                disabled={secretKeyLoading}
                                className="w-full py-4 bg-amber-500 text-white rounded-2xl font-black hover:bg-amber-600 transition-all shadow-lg shadow-amber-500/20 active:scale-95 uppercase tracking-widest text-sm flex items-center justify-center gap-2 disabled:opacity-50"
                            >
                                {secretKeyLoading ? <Loader2 className="animate-spin" size={18} /> : <RefreshCw size={18} />}
                                Tạo Mã Mới
                            </button>
                            <p className="text-[10px] text-gray-400 font-medium -mt-4">Tạo mã mới sẽ vô hiệu hóa mã cũ ngay lập tức</p>
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
        </div>
    );
};

export default TeacherExams;
