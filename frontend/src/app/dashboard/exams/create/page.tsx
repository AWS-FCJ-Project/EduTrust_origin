"use client";

import React, { useEffect, useState, Suspense } from 'react';
import { Save, ArrowLeft, Loader2, Plus, Trash2, KeyRound, RefreshCw, Copy, Check, Search } from 'lucide-react';
import TimePicker from '@/components/ui/TimePicker';
import Link from 'next/link';
import { useSearchParams } from 'next/navigation';
import Cookies from 'js-cookie';

const SUBJECTS = [
    "Toán học", "Vật lí", "Hóa học", "Sinh học", "Ngữ văn",
    "Lịch sử", "Địa lí", "Tiếng Anh", "Công nghệ", "Tin học",
    "Giáo dục kinh tế và pháp luật", "Giáo dục thể chất", "Giáo dục quốc phòng và an ninh"
];

const EXAM_TYPES = [
    "Kiểm tra miệng", "Kiểm tra 15 phút", "Kiểm tra 1 tiết", "Kiểm giữa kỳ", "Kiểm học kỳ"
];

const CreateExamForm = () => {
    const searchParams = useSearchParams();
    const preselectedClassId = searchParams.get('class_id');

    const autoResize = (e: React.SyntheticEvent<HTMLTextAreaElement>) => {
        const element = e.currentTarget;
        element.style.height = 'auto';
        element.style.height = `${element.scrollHeight}px`;
    };
    
    const [loading, setLoading] = useState(false);
    const [classes, setClasses] = useState<any[]>([]);
    const [createdKey, setCreatedKey] = useState<string | null>(null);
    const [copied, setCopied] = useState(false);
    const [secretKeyMode, setSecretKeyMode] = useState<'auto' | 'manual'>('auto');
    const [subjectSearch, setSubjectSearch] = useState('');
    const [showSubjectDropdown, setShowSubjectDropdown] = useState(false);
    const [formData, setFormData] = useState<any>({
        title: '',
        description: '',
        subject: '',
        exam_type: 'Kiểm tra 15 phút',
        class_id: '',
        start_date: '',
        start_time: '',
        end_date: '',
        end_time: '23:59',
        duration: '',
        secret_key: '',
        questions: [{ q: '', options: ['', '', '', ''], correct: 0 }]
    });

    const filteredSubjects = SUBJECTS.filter((subject) =>
        subject.toLowerCase().includes(subjectSearch.toLowerCase())
    );

    useEffect(() => {
        const fetchClasses = async () => {
            try {
                const token = Cookies.get('auth_token');
                const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/classes`, {
                    headers: { 'Authorization': `Bearer ${token}` }
                });
                if (res.ok) {
                    const data = await res.json();
                    setClasses(data);
                    
                    // Auto-fill class if provided in URL
                    if (preselectedClassId) {
                        setFormData((prev: any) => ({ ...prev, class_id: preselectedClassId }));
                    }
                }
            } catch (error) {
                console.error("Error fetching classes:", error);
            }
        };
        fetchClasses();
    }, [preselectedClassId]);

    useEffect(() => {
        const handleClickOutside = (e: MouseEvent) => {
            if (showSubjectDropdown && !(e.target as HTMLElement).closest('.subject-selection')) {
                setShowSubjectDropdown(false);
            }
        };
        document.addEventListener('mousedown', handleClickOutside);
        return () => document.removeEventListener('mousedown', handleClickOutside);
    }, [showSubjectDropdown]);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);
        try {
            const token = Cookies.get('auth_token');
            const dataToSubmit = { ...formData };
            
            // Combine Date and Time as LOCAL time
            let finalStart = "";
            if (dataToSubmit.start_date) {
                const timeStr = dataToSubmit.start_time || "00:00";
                // Create date object as local time
                const localDate = new Date(`${dataToSubmit.start_date}T${timeStr}`);
                finalStart = localDate.toISOString();
            } else {
                finalStart = new Date().toISOString();
            }

            let finalEnd = "";
            if (dataToSubmit.end_date) {
                const timeStr = dataToSubmit.end_time || "23:59";
                const localDate = new Date(`${dataToSubmit.end_date}T${timeStr}`);
                finalEnd = localDate.toISOString();
            }

            const payload = {
                ...formData,
                start_time: finalStart,
                end_time: finalEnd,
                duration: parseInt(formData.duration) || 0,
                secret_key: secretKeyMode === 'manual' && formData.secret_key ? formData.secret_key : undefined,
            };

            if (!SUBJECTS.includes(payload.subject)) {
                alert("Vui lòng chọn môn học từ danh sách");
                setLoading(false);
                return;
            }

            const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/exams`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify(payload)
            });
            if (res.ok) {
                const data = await res.json();
                setCreatedKey(data.secret_key || null);
            } else {
                alert("Lỗi khi tạo đề thi");
            }
        } catch (error) {
            console.error("Error creating exam:", error);
        } finally {
            setLoading(false);
        }
    };

    const addQuestion = () => {
        setFormData({
            ...formData,
            questions: [...formData.questions, { q: '', options: ['', '', '', ''], correct: 0 }]
        });
    };

    const handleCopyKey = () => {
        if (!createdKey) return;
        navigator.clipboard.writeText(createdKey);
        setCopied(true);
        setTimeout(() => setCopied(false), 2000);
    };

    if (createdKey !== null) {
        return (
            <div className="fixed inset-0 bg-white/80 backdrop-blur-md flex items-center justify-center z-50 animate-in fade-in duration-500">
                <div className="bg-white rounded-[3rem] shadow-2xl border border-gray-100 p-12 max-w-md w-full text-center space-y-8 animate-in zoom-in-95 duration-500">
                    <div className="w-20 h-20 bg-green-50 rounded-full flex items-center justify-center mx-auto shadow-inner">
                        <Check size={40} className="text-green-500" />
                    </div>
                    <div className="space-y-2">
                        <h2 className="text-3xl font-black text-gray-900">Đề thi đã được tạo!</h2>
                        <p className="text-gray-500 font-medium">Chia sẻ mã đề thi này cho học sinh của bạn</p>
                    </div>
                    <div className="bg-[#5B0019]/5 border-2 border-[#5B0019]/20 rounded-3xl p-6 space-y-3">
                        <p className="text-xs font-black text-gray-400 uppercase tracking-widest">Mã Đề Thi</p>
                        <div className="flex items-center justify-center gap-4">
                            <span className="text-5xl font-black text-[#5B0019] tracking-[0.3em]">{createdKey}</span>
                            <button
                                onClick={handleCopyKey}
                                className={`p-3 rounded-2xl transition-all ${
                                    copied ? 'bg-green-500 text-white' : 'bg-white border border-gray-200 text-gray-400 hover:text-[#5B0019] hover:border-[#5B0019]'
                                }`}
                            >
                                {copied ? <Check size={20} /> : <Copy size={20} />}
                            </button>
                        </div>
                        <p className="text-xs text-gray-400 font-medium">Học sinh cần nhập mã này trước khi vào thi</p>
                    </div>
                    <button
                        onClick={() => window.location.href = '/dashboard/exams'}
                        className="w-full py-4 bg-[#5B0019] text-white rounded-2xl font-black hover:bg-black transition-all shadow-xl shadow-red-900/20 active:scale-95 uppercase tracking-widest text-sm"
                    >
                        Đến danh sách đề thi
                    </button>
                </div>
            </div>
        );
    }

    return (
        <div className="max-w-4xl mx-auto space-y-8 animate-in fade-in duration-500">
            <div className="flex items-center justify-between">
                <div className="flex items-center gap-4">
                    <Link href="/dashboard/exams" className="p-2 hover:bg-gray-100 rounded-full transition-colors">
                        <ArrowLeft size={24} />
                    </Link>
                    <h1 className="text-3xl font-black text-gray-900 tracking-tight">Tạo Đề Thi Mới</h1>
                </div>
            </div>

            <form onSubmit={handleSubmit} className="space-y-8">
                <div className="bg-white p-8 rounded-[2.5rem] shadow-sm border border-gray-100 space-y-8">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                        <div className="space-y-2">
                            <label className="text-sm font-black text-gray-400 uppercase tracking-widest pl-2">Tiêu đề đề thi</label>
                            <input 
                                required
                                type="text" 
                                value={formData.title}
                                onChange={(e) => setFormData({...formData, title: e.target.value})}
                                className="w-full px-6 py-4 bg-gray-50 border-none rounded-2xl focus:ring-2 focus:ring-[#5B0019] transition-all font-bold"
                                placeholder="VD: Kiểm tra giữa kỳ Hóa học"
                            />
                        </div>
                        <div className="space-y-2 relative subject-selection">
                            <label className="text-sm font-black text-gray-400 uppercase tracking-widest pl-2 flex justify-between">
                                <span>Môn học</span>
                                {formData.subject && <span className="text-[#005B19] text-[10px] font-black uppercase tracking-widest">Đã chọn</span>}
                            </label>
                            <div className="relative">
                                <Search className="absolute left-6 top-1/2 -translate-y-1/2 text-gray-400" size={18} />
                                <input
                                    required
                                    type="text"
                                    value={subjectSearch}
                                    onFocus={() => setShowSubjectDropdown(true)}
                                    onChange={(e) => {
                                        setSubjectSearch(e.target.value);
                                        setFormData({ ...formData, subject: '' });
                                        setShowSubjectDropdown(true);
                                    }}
                                    className={`w-full pl-14 pr-14 py-4 bg-gray-50 border-none rounded-2xl focus:ring-2 transition-all font-bold ${
                                        formData.subject ? 'focus:ring-[#005B19]/20' : 'focus:ring-[#5B0019]'
                                    }`}
                                    placeholder="Tìm kiếm môn học..."
                                />
                                {subjectSearch && (
                                    <button
                                        type="button"
                                        onClick={() => {
                                            setSubjectSearch('');
                                            setFormData({ ...formData, subject: '' });
                                        }}
                                        className="absolute right-6 top-1/2 -translate-y-1/2 text-gray-400 hover:text-red-500 transition-colors"
                                    >
                                        <Plus className="rotate-45" size={20} />
                                    </button>
                                )}
                            </div>
                            {showSubjectDropdown && (
                                <div className="absolute z-50 w-full mt-2 bg-white rounded-2xl shadow-xl border border-gray-100 max-h-60 overflow-y-auto p-2 scrollbar-thin scrollbar-thumb-gray-200">
                                    {filteredSubjects.length > 0 ? filteredSubjects.map((subject) => (
                                        <button
                                            key={subject}
                                            type="button"
                                            onClick={() => {
                                                setFormData({ ...formData, subject });
                                                setSubjectSearch(subject);
                                                setShowSubjectDropdown(false);
                                            }}
                                            className="w-full text-left px-4 py-3 rounded-xl hover:bg-gray-50 flex items-center justify-between group transition-colors"
                                        >
                                            <span className={`font-bold ${formData.subject === subject ? 'text-[#005B19]' : 'text-gray-600'}`}>{subject}</span>
                                            {formData.subject === subject && <Check size={16} className="text-[#005B19]" />}
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
                            <label className="text-sm font-black text-gray-400 uppercase tracking-widest pl-2">Loại bài thi</label>
                            <select
                                required
                                value={formData.exam_type}
                                onChange={(e) => setFormData({ ...formData, exam_type: e.target.value })}
                                className="w-full px-6 py-4 bg-gray-50 border-none rounded-2xl focus:ring-2 focus:ring-[#5B0019] transition-all font-bold text-[#5B0019]"
                            >
                                {EXAM_TYPES.map((type) => (
                                    <option key={type} value={type}>{type}</option>
                                ))}
                            </select>
                        </div>
                        <div className="space-y-2">
                            <label className="text-sm font-black text-gray-400 uppercase tracking-widest pl-2">Lớp học</label>
                            <select 
                                required
                                value={formData.class_id}
                                onChange={(e) => setFormData({...formData, class_id: e.target.value})}
                                className="w-full px-6 py-4 bg-gray-50 border-none rounded-2xl focus:ring-2 focus:ring-[#5B0019] transition-all font-bold text-[#5B0019]"
                            >
                                <option value="">Chọn lớp</option>
                                {classes.map(cls => (
                                    <option key={cls.id} value={cls.id}>{cls.name}</option>
                                ))}
                            </select>
                        </div>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-1 gap-8">
                        <div className="space-y-3 p-6 bg-[#5B0019]/3 rounded-[2rem] border border-[#5B0019]/10">
                            <div className="flex items-center gap-2 mb-1">
                                <KeyRound size={16} className="text-[#5B0019]" />
                                <label className="text-sm font-black text-gray-400 uppercase tracking-widest">Mã Đề Thi (Secret Key)</label>
                            </div>
                            <div className="flex gap-3">
                                <button
                                    type="button"
                                    onClick={() => setSecretKeyMode('auto')}
                                    className={`flex-1 py-3 rounded-2xl font-black text-xs uppercase tracking-widest transition-all ${
                                        secretKeyMode === 'auto'
                                            ? 'bg-[#5B0019] text-white shadow-lg shadow-red-900/20'
                                            : 'bg-white border border-gray-200 text-gray-400 hover:border-[#5B0019]/30'
                                    }`}
                                >
                                    <RefreshCw size={13} className="inline mr-1.5" />Tự động tạo
                                </button>
                                <button
                                    type="button"
                                    onClick={() => setSecretKeyMode('manual')}
                                    className={`flex-1 py-3 rounded-2xl font-black text-xs uppercase tracking-widest transition-all ${
                                        secretKeyMode === 'manual'
                                            ? 'bg-[#5B0019] text-white shadow-lg shadow-red-900/20'
                                            : 'bg-white border border-gray-200 text-gray-400 hover:border-[#5B0019]/30'
                                    }`}
                                >
                                    <KeyRound size={13} className="inline mr-1.5" />Nhập thủ công
                                </button>
                            </div>
                            {secretKeyMode === 'auto' ? (
                                <p className="text-xs text-gray-400 font-medium pl-1">
                                    Hệ thống sẽ tự động tạo mã bí mật 6 ký tự ngẫu nhiên sau khi tạo đề thi.
                                </p>
                            ) : (
                                <input
                                    type="text"
                                    maxLength={12}
                                    value={formData.secret_key}
                                    onChange={(e) => setFormData({ ...formData, secret_key: e.target.value.toUpperCase() })}
                                    className="w-full px-6 py-4 bg-white border-none rounded-2xl focus:ring-2 focus:ring-[#5B0019] transition-all font-black text-2xl tracking-[0.3em] text-[#5B0019] uppercase"
                                    placeholder="VD: ABC123"
                                />
                            )}
                        </div>
                        
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-12 pt-4">
                            {/* Start Time Section */}
                            <div className="space-y-4 p-6 bg-gray-50/50 rounded-[2rem] border border-gray-100">
                                <div className="flex items-center justify-between">
                                    <label className="text-xs font-black text-gray-400 uppercase tracking-widest pl-2">Ngày Bắt đầu</label>
                                    <button 
                                        type="button"
                                        onClick={() => {
                                            const now = new Date();
                                            setFormData({
                                                ...formData, 
                                                start_date: now.toISOString().split('T')[0],
                                                start_time: now.toLocaleTimeString('vi-VN', {hour12: false, hour: '2-digit', minute: '2-digit'})
                                            });
                                        }}
                                        className="text-[10px] font-black text-[#5B0019] uppercase tracking-tighter hover:underline"
                                    >Thời gian hiện tại</button>
                                </div>
                                <div className="flex items-center gap-4">
                                    <input 
                                        type="date" 
                                        value={formData.start_date}
                                        onChange={(e) => setFormData({...formData, start_date: e.target.value})}
                                        className="flex-1 px-6 py-4 bg-white border-none rounded-2xl focus:ring-2 focus:ring-[#5B0019] transition-all font-bold text-sm"
                                    />
                                    <TimePicker 
                                        value={formData.start_time}
                                        onChange={(val) => setFormData({...formData, start_time: val})}
                                        className="w-32"
                                    />
                                </div>
                            </div>

                            {/* End Time Section */}
                            <div className="space-y-4 p-6 bg-gray-50/50 rounded-[2rem] border border-gray-100">
                                <label className="text-xs font-black text-gray-400 uppercase tracking-widest pl-2">Ngày Kết thúc</label>
                                <div className="flex items-center gap-4">
                                    <input 
                                        type="date" 
                                        value={formData.end_date}
                                        onChange={(e) => setFormData({...formData, end_date: e.target.value})}
                                        className="flex-1 px-6 py-4 bg-white border-none rounded-2xl focus:ring-2 focus:ring-[#5B0019] transition-all font-bold text-sm"
                                    />
                                    <TimePicker 
                                        value={formData.end_time}
                                        onChange={(val) => setFormData({...formData, end_time: val})}
                                        className="w-32"
                                    />
                                </div>
                            </div>
                        </div>

                        <div className="space-y-2 pt-6">
                            <label className="text-sm font-black text-gray-400 uppercase tracking-widest pl-2">Thời gian làm bài (Phút)</label>
                            <input 
                                type="text" 
                                inputMode="numeric"
                                value={formData.duration}
                                onChange={(e) => {
                                    const val = e.target.value.replace(/[^0-9]/g, '').replace(/^0+/, '');
                                    setFormData({...formData, duration: val});
                                }}
                                className="max-w-xs px-6 py-4 bg-gray-50 border-none rounded-2xl focus:ring-2 focus:ring-[#5B0019] transition-all font-bold text-xl"
                                placeholder="Nhập thời gian làm bài"
                            />
                        </div>
                    </div>
                </div>

                <div className="space-y-6">
                    <h2 className="text-2xl font-black text-gray-900 tracking-tight pl-2">Danh sách câu hỏi</h2>
                    {formData.questions.map((q: any, qIdx: number) => (
                        <div key={qIdx} className="bg-white p-8 rounded-[2.5rem] shadow-sm border border-gray-100 space-y-4 hover:shadow-md transition-shadow">
                            <div className="flex justify-between items-center">
                                <span className="text-lg font-black text-[#5B0019] uppercase tracking-tighter">Câu {qIdx + 1}</span>
                                {formData.questions.length > 1 && (
                                    <button 
                                        type="button"
                                        onClick={() => {
                                            const newQ = [...formData.questions];
                                            newQ.splice(qIdx, 1);
                                            setFormData({...formData, questions: newQ});
                                        }}
                                        className="p-2 bg-red-50 text-red-400 hover:bg-red-500 hover:text-white rounded-xl transition-all"
                                    ><Trash2 size={18} /></button>
                                )}
                            </div>
                            <textarea 
                                required
                                rows={1}
                                className="w-full px-6 py-4 bg-gray-50 border-none rounded-2xl focus:ring-2 focus:ring-[#5B0019] transition-all font-bold italic text-sm resize-none overflow-hidden break-words"
                                placeholder="Nhập nội dung câu hỏi..."
                                value={q.q}
                                onChange={(e) => {
                                    const newQ = [...formData.questions];
                                    newQ[qIdx].q = e.target.value;
                                    setFormData({...formData, questions: newQ});
                                    autoResize(e);
                                }}
                                onFocus={autoResize}
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
                                                    const newQ = [...formData.questions];
                                                    newQ[qIdx].correct = oIdx;
                                                    setFormData({...formData, questions: newQ});
                                                }}
                                                className="w-5 h-5 text-[#5B0019] focus:ring-[#5B0019] cursor-pointer"
                                            />
                                            {q.correct === oIdx && <span className="text-[7px] font-black text-[#5B0019] uppercase">Đúng</span>}
                                        </div>
                                        <textarea 
                                            required
                                            rows={1}
                                            placeholder={`Đáp án ${oIdx + 1}`}
                                            value={opt}
                                            onChange={(e) => {
                                                const newQ = [...formData.questions];
                                                newQ[qIdx].options[oIdx] = e.target.value;
                                                setFormData({...formData, questions: newQ});
                                                autoResize(e);
                                            }}
                                            onFocus={autoResize}
                                            className="flex-1 bg-transparent border-none focus:ring-0 text-sm font-bold resize-none overflow-hidden break-words py-1"
                                        />
                                    </div>
                                ))}
                            </div>
                        </div>
                    ))}
                    <button 
                        type="button"
                        onClick={addQuestion}
                        className="w-full py-6 border-2 border-dashed border-gray-100 rounded-[2.5rem] text-gray-400 font-bold hover:border-[#5B0019] hover:text-[#5B0019] hover:bg-red-50/20 transition-all flex items-center justify-center gap-2 uppercase tracking-widest text-xs"
                    >
                        <Plus size={20} /> Thêm câu hỏi mới
                    </button>
                </div>

                <div className="flex justify-end pt-8 pb-12">
                    <button 
                        disabled={loading}
                        className="bg-[#5B0019] text-white px-12 py-5 rounded-[2rem] font-black flex items-center gap-2 hover:bg-black transition-all shadow-xl shadow-red-900/20 active:scale-95 disabled:opacity-50 uppercase tracking-widest text-sm"
                    >
                        {loading ? <Loader2 className="animate-spin" size={20} /> : <Save size={20} />}
                        Lưu Đề Thi
                    </button>
                </div>
            </form>
        </div>
    );
};

const CreateExamPage = () => {
    return (
        <Suspense fallback={<div className="flex h-64 items-center justify-center"><Loader2 className="animate-spin text-[#5B0019]" size={40} /></div>}>
            <CreateExamForm />
        </Suspense>
    );
};

export default CreateExamPage;
