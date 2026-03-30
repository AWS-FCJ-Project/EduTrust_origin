"use client";

import React, { useState, useEffect } from 'react';
import { Layers, Plus, Search, User, Users, CheckCircle, AlertCircle, Loader2, Save, X, Trash2, UserPlus, GraduationCap, School, UserMinus, AlertTriangle, Eye, Info, BookOpen, Star } from 'lucide-react';
import Cookies from 'js-cookie';

const ClassesPage = () => {
    const [user, setUser] = useState<any>(null);
    const [classes, setClasses] = useState<any[]>([]);
    const [teachers, setTeachers] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);
    const [error] = useState<string | null>(null);
    const [searchTerm, setSearchTerm] = useState('');
    const [isModalOpen, setIsModalOpen] = useState(false);
    const [modalMode, setModalMode] = useState<'create' | 'edit'>('create');
    
    const [newClass, setNewClass] = useState({
        name: '',
        grade: '',
        school_year: '2026-2027'
    });

    const [editingClass, setEditingClass] = useState<any>(null);
    const [deletingClass, setDeletingClass] = useState<any>(null);
    const [classStudents, setClassStudents] = useState<any[]>([]);
    const [loadingStudents, setLoadingStudents] = useState(false);
    const [isActionLoading, setIsActionLoading] = useState(false);
    
    const [availableStudents, setAvailableStudents] = useState<any[]>([]);
    const [searchAvailableTerm, setSearchAvailableTerm] = useState('');
    const [isSearchingAvailable, setIsSearchingAvailable] = useState(false);

    const fetchData = async () => {
        try {
            setLoading(true);
            const token = Cookies.get('auth_token');
            
            // Fetch User Info
            const userRes = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/user-info`, {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            const userData = await userRes.json();
            setUser(userData);

            // Fetch Classes
            const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/classes`, {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            if (res.ok) {
                const data = await res.json();
                setClasses(data);
            }

            // Fetch Teachers
            const teachersRes = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/users/teachers`, {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            if (teachersRes.ok) {
                const teachersData = await teachersRes.json();
                setTeachers(teachersData);
            }
        } catch (err) {
            console.error(err);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchData();
    }, []);

    const fetchClassStudents = async (classId: string) => {
        try {
            setLoadingStudents(true);
            const token = Cookies.get('auth_token');
            const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/classes/${classId}/students`, {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            if (res.ok) {
                const data = await res.json();
                setClassStudents(data);
            }
        } catch (err) {
            console.error(err);
        } finally {
            setLoadingStudents(false);
        }
    };

    const fetchAvailableStudents = async (classId: string) => {
        try {
            setIsSearchingAvailable(true);
            const token = Cookies.get('auth_token');
            const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/classes/students/available?class_id=${classId}`, {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            if (res.ok) {
                const data = await res.json();
                setAvailableStudents(data);
            }
        } catch (err) {
            console.error(err);
        } finally {
            setIsSearchingAvailable(false);
        }
    };

    const handleCreateClass = async (e: React.FormEvent) => {
        e.preventDefault();
        try {
            const token = Cookies.get('auth_token');
            const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/classes`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify({
                    ...newClass,
                    grade: parseInt(newClass.grade)
                })
            });

            if (res.ok) {
                setIsModalOpen(false);
                setNewClass({ name: '', grade: '', school_year: '2026-2027' });
                fetchData();
            }
        } catch (err) {
            console.error(err);
        }
    };

    const handleUpdateClass = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!editingClass) return;

        try {
            const token = Cookies.get('auth_token');
            const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/classes/${editingClass.id}`, {
                method: 'PATCH',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify({
                    name: editingClass.name,
                    grade: parseInt(editingClass.grade),
                    school_year: editingClass.school_year,
                    homeroom_teacher_id: editingClass.homeroom_teacher_id,
                    subject_teachers: editingClass.subject_teachers
                })
            });

            if (res.ok) {
                setIsModalOpen(false);
                fetchData();
            }
        } catch (err) {
            console.error(err);
        }
    };

    const handleDeleteClass = async () => {
        if (!deletingClass) return;
        setIsActionLoading(true);
        try {
            const token = Cookies.get('auth_token');
            const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/classes/${deletingClass.id}`, {
                method: 'DELETE',
                headers: { 'Authorization': `Bearer ${token}` }
            });
            if (res.ok) {
                setDeletingClass(null);
                fetchData();
            }
        } catch (err) {
            console.error(err);
        } finally {
            setIsActionLoading(false);
        }
    };

    const handleAddStudent = async (studentId: string) => {
        try {
            const token = Cookies.get('auth_token');
            const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/classes/${editingClass.id}/students/${studentId}`, {
                method: 'POST',
                headers: { 'Authorization': `Bearer ${token}` }
            });
            if (res.ok) {
                fetchClassStudents(editingClass.id);
                fetchAvailableStudents(editingClass.id);
                fetchData(); // Update count in background
            }
        } catch (err) {
            console.error(err);
        }
    };

    const handleRemoveStudent = async (studentId: string) => {
        try {
            const token = Cookies.get('auth_token');
            const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/classes/${editingClass.id}/students/${studentId}`, {
                method: 'DELETE',
                headers: { 'Authorization': `Bearer ${token}` }
            });
            if (res.ok) {
                fetchClassStudents(editingClass.id);
                fetchAvailableStudents(editingClass.id);
                fetchData(); // Update count in background
            }
        } catch (err) {
            console.error(err);
        }
    };

    const openEditModal = (cls: any) => {
        setModalMode('edit');
        setEditingClass({
            ...cls,
            subject_teachers: cls.subject_teachers || []
        });
        fetchClassStudents(cls.id);
        if (user?.role === 'admin') {
            fetchAvailableStudents(cls.id);
        }
        setIsModalOpen(true);
    };

    const addSubjectTeacher = () => {
        setEditingClass({
            ...editingClass,
            subject_teachers: [...editingClass.subject_teachers, { teacher_id: '', subject: '' }]
        });
    };

    const removeSubjectTeacher = (index: number) => {
        const updated = [...editingClass.subject_teachers];
        updated.splice(index, 1);
        setEditingClass({ ...editingClass, subject_teachers: updated });
    };

    const updateSubjectTeacher = (index: number, field: string, value: string) => {
        const updated = [...editingClass.subject_teachers];
        updated[index] = { ...updated[index], [field]: value };
        setEditingClass({ ...editingClass, subject_teachers: updated });
    };

    const filteredClasses = classes.filter(cls => 
        (cls.name || "").toLowerCase().includes(searchTerm.toLowerCase()) ||
        (cls.grade || "").toString().includes(searchTerm)
    );
    
    const filteredAvailableStudents = availableStudents.filter(s => 
        (s.name || "").toLowerCase().includes(searchAvailableTerm.toLowerCase()) ||
        (s.email || "").toLowerCase().includes(searchAvailableTerm.toLowerCase())
    ).slice(0, 5); // Show top 5 matches

    if (loading) return (
        <div className="flex h-64 items-center justify-center">
            <Loader2 className="animate-spin text-[#5B0019]" size={40} />
        </div>
    );

    const isAdmin = user?.role === 'admin';
    const userId = user?.id || user?._id;

    // Helper to get teacher name by ID
    const getTeacherName = (id: string) => {
        const teacher = teachers.find(t => t.id === id);
        return teacher ? teacher.name : "Chưa xác định";
    };

    // Correct partitioning for Teacher role
    const homeroomClasses = filteredClasses.filter(cls => cls.homeroom_teacher_id === String(userId));
    const subjectClasses = filteredClasses.filter(cls => cls.homeroom_teacher_id !== String(userId));

    // Common renderer for Class Cards
    const renderClassCard = (cls: any) => (
        <div key={cls.id} className="bg-white rounded-[3.5rem] border border-gray-100 shadow-sm hover:shadow-2xl transition-all group p-10 relative overflow-hidden">
            <div className="flex items-start justify-between relative z-10">
                <div className="space-y-1">
                    <h3 className="text-4xl font-black text-[#5B0019] leading-none mb-2">{cls.name}</h3>
                    <p className="text-xs font-black text-gray-400 uppercase tracking-widest">Khối {cls.grade}</p>
                </div>
                <div className="flex items-center gap-3">
                    {isAdmin && (
                        <button 
                            onClick={(e) => { e.stopPropagation(); setDeletingClass(cls); }}
                            className="p-3 bg-red-50 text-red-400 hover:bg-red-500 hover:text-white rounded-2xl transition-all opacity-0 group-hover:opacity-100 shadow-sm"
                            title="Xóa lớp học"
                        >
                            <Trash2 size={20} />
                        </button>
                    )}
                    <div className={`p-3 rounded-2xl ${cls.status === 'active' ? 'bg-green-50 text-green-600' : 'bg-orange-50 text-orange-600'}`}>
                        {cls.status === 'active' ? <CheckCircle size={24} /> : <AlertCircle size={24} />}
                    </div>
                </div>
            </div>

            <div className="mt-10 grid grid-cols-2 gap-4 relative z-10">
                <div className="bg-gray-50 p-4 rounded-3xl border border-transparent hover:border-gray-200 transition-colors">
                    <div className="flex items-center gap-2 text-gray-400 mb-1">
                        <Users size={14} />
                        <span className="text-[10px] font-black uppercase">Sĩ số</span>
                    </div>
                    <p className="text-xl font-black text-gray-800">{cls.student_count || 0}</p>
                </div>
                <div className="bg-gray-50 p-4 rounded-3xl border border-transparent hover:border-gray-200 transition-colors">
                    <div className="flex items-center gap-2 text-gray-400 mb-1">
                        <User size={14} />
                        <span className="text-[10px] font-black uppercase">GV Chủ nhiệm</span>
                    </div>
                    <p className="text-[12px] font-bold text-gray-800 truncate" title={cls.homeroom_teacher_id ? getTeacherName(cls.homeroom_teacher_id) : "Chưa phân công"}>
                        {cls.homeroom_teacher_id ? getTeacherName(cls.homeroom_teacher_id) : "Chưa phân công"}
                    </p>
                </div>
            </div>

            <div className="mt-8 flex items-center justify-between relative z-10">
                <span className={`text-[10px] font-black uppercase tracking-[0.2em] px-3 py-1 rounded-full ${cls.status === 'active' ? 'bg-green-50 text-green-700' : 'bg-orange-50 text-orange-700'}`}>
                    {cls.status === 'active' ? '● Hoạt động' : '● Chưa đủ điều kiện'}
                </span>
                <button 
                    onClick={() => openEditModal(cls)}
                    className="px-6 py-3 bg-[#5B0019] text-white rounded-2xl font-black text-[12px] hover:scale-105 active:scale-95 transition-all shadow-lg shadow-red-900/20 uppercase tracking-widest flex items-center gap-2"
                >
                    {isAdmin ? 'CHI TIẾT +' : <><Eye size={16} /> XEM LỚP</>}
                </button>
            </div>
        </div>
    );

    return (
        <div className="space-y-10 animate-in fade-in duration-700">
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
                <div className="flex flex-col gap-2">
                    <h1 className="text-3xl font-black text-gray-900 tracking-tight">Quản lý Lớp học</h1>
                    <p className="text-gray-500 font-medium tracking-wide border-l-4 border-[#5B0019] pl-3">
                        Danh sách lớp học và tình trạng phân công giảng dạy.
                    </p>
                </div>
                
                {isAdmin && (
                    <button 
                        onClick={() => { setModalMode('create'); setIsModalOpen(true); }}
                        className="flex items-center gap-2 px-8 py-4 bg-[#5B0019] text-white rounded-2xl font-black shadow-lg shadow-red-900/20 hover:scale-105 active:scale-95 transition-all text-sm uppercase tracking-wider"
                    >
                        <Plus size={20} /> Tạo lớp mới
                    </button>
                )}
            </div>

            {error && (
                <div className="bg-red-50 border border-red-200 text-red-700 p-6 rounded-[2rem] flex items-center gap-4">
                    <AlertCircle size={24} />
                    <p className="font-bold">{error}</p>
                </div>
            )}

            <div className="relative group max-w-2xl">
                <Search className="absolute left-6 top-1/2 -translate-y-1/2 text-gray-400 group-focus-within:text-[#5B0019]" size={20} />
                <input 
                    type="text"
                    placeholder="Tìm theo tên lớp (10A1, 12B...)"
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    className="w-full pl-14 pr-6 py-5 bg-white border-none rounded-[2rem] shadow-sm focus:ring-2 focus:ring-[#5B0019] transition-all font-bold text-gray-700"
                />
            </div>

            {isAdmin ? (
                <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-8 text-sm">
                    {filteredClasses.map(renderClassCard)}
                </div>
            ) : (
                <div className="space-y-12">
                    {/* Homeroom Section */}
                    {homeroomClasses.length > 0 && (
                        <div className="space-y-6">
                            <div className="flex items-center gap-3 px-2">
                                <div className="p-3 bg-red-50 text-[#5B0019] rounded-2xl border border-red-100">
                                    <Star size={24} />
                                </div>
                                <div>
                                    <h2 className="text-2xl font-black text-gray-900 tracking-tight">Lớp Chủ Nhiệm</h2>
                                    <p className="text-xs font-bold text-gray-400 uppercase tracking-widest">{homeroomClasses.length} lớp học</p>
                                </div>
                            </div>
                            <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-8 text-sm">
                                {homeroomClasses.map(renderClassCard)}
                            </div>
                        </div>
                    )}

                    {/* Subject Section */}
                    <div className="space-y-6">
                        <div className="flex items-center gap-3 px-2">
                            <div className="p-3 bg-indigo-50 text-indigo-600 rounded-2xl border border-indigo-100">
                                <BookOpen size={24} />
                            </div>
                            <div>
                                <h2 className="text-2xl font-black text-gray-900 tracking-tight">Lớp Giảng Dạy</h2>
                                <p className="text-xs font-bold text-gray-400 uppercase tracking-widest">{subjectClasses.length} lớp học</p>
                            </div>
                        </div>
                        {subjectClasses.length > 0 ? (
                            <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-8 text-sm">
                                {subjectClasses.map(renderClassCard)}
                            </div>
                        ) : (
                            <div className="p-12 text-center bg-gray-50 rounded-[3.5rem] border border-dashed text-gray-400 font-bold italic">
                                Bạn chưa có lịch giảng dạy bộ môn nào.
                            </div>
                        )}
                    </div>
                </div>
            )}

            {isModalOpen && (
                <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-md animate-in fade-in duration-300">
                    <div className="bg-white w-full max-w-4xl max-h-[90vh] overflow-hidden rounded-[3rem] shadow-2xl flex flex-col animate-in zoom-in-95 duration-300">
                        {/* Header */}
                        <div className="p-8 border-b flex items-center justify-between bg-gray-50/50">
                            <div className="flex items-center gap-4">
                                <div className="bg-[#5B0019] p-3 rounded-2xl text-white shadow-lg shadow-red-900/20">
                                    {isAdmin ? <Layers size={24} /> : <Info size={24} />}
                                </div>
                                <h2 className="text-2xl font-black text-gray-800">
                                    {modalMode === 'create' ? 'Tạo Lớp học mới' : `${isAdmin ? 'Chi tiết' : 'Thông tin'} Lớp ${editingClass?.name}`}
                                </h2>
                            </div>
                            <button onClick={() => setIsModalOpen(false)} className="p-3 hover:bg-gray-100 rounded-2xl transition-all">
                                <X size={24} className="text-gray-400" />
                            </button>
                        </div>

                        {/* Content */}
                        <div className="flex-1 overflow-y-auto p-10 space-y-10 custom-scrollbar">
                            <form onSubmit={modalMode === 'create' ? handleCreateClass : handleUpdateClass} className="space-y-12">
                                {/* Basic Info Section */}
                                <div className="space-y-6">
                                    <div className="flex items-center gap-2 text-[#5B0019]">
                                        <School size={18} />
                                        <h3 className="font-black uppercase tracking-widest text-sm">Thông tin cơ bản</h3>
                                    </div>
                                    
                                    {isAdmin ? (
                                        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                                            <div className="space-y-2">
                                                <label className="text-[10px] font-black text-gray-400 uppercase tracking-widest pl-2">Tên lớp</label>
                                                <input 
                                                    required
                                                    type="text"
                                                    value={modalMode === 'create' ? newClass.name : editingClass.name}
                                                    onChange={(e) => modalMode === 'create' ? setNewClass({...newClass, name: e.target.value}) : setEditingClass({...editingClass, name: e.target.value})}
                                                    className="w-full px-6 py-4 bg-gray-50 border-none rounded-2xl focus:ring-2 focus:ring-[#5B0019] font-black"
                                                />
                                            </div>
                                            <div className="space-y-2">
                                                <label className="text-[10px] font-black text-gray-400 uppercase tracking-widest pl-2">Khối</label>
                                                <input 
                                                    required
                                                    type="number"
                                                    value={modalMode === 'create' ? newClass.grade : editingClass.grade}
                                                    onChange={(e) => modalMode === 'create' ? setNewClass({...newClass, grade: e.target.value}) : setEditingClass({...editingClass, grade: e.target.value})}
                                                    className="w-full px-6 py-4 bg-gray-50 border-none rounded-2xl focus:ring-2 focus:ring-[#5B0019] font-black"
                                                />
                                            </div>
                                            <div className="space-y-2">
                                                <label className="text-[10px] font-black text-gray-400 uppercase tracking-widest pl-2">Niên khóa</label>
                                                <input 
                                                    required
                                                    type="text"
                                                    value={modalMode === 'create' ? newClass.school_year : editingClass.school_year}
                                                    onChange={(e) => modalMode === 'create' ? setNewClass({...newClass, school_year: e.target.value}) : setEditingClass({...editingClass, school_year: e.target.value})}
                                                    className="w-full px-6 py-4 bg-gray-50 border-none rounded-2xl focus:ring-2 focus:ring-[#5B0019] font-black"
                                                />
                                            </div>
                                        </div>
                                    ) : (
                                        <div className="grid grid-cols-3 gap-4">
                                            <div className="bg-gray-50 p-6 rounded-[2rem] border border-gray-100 flex flex-col gap-1">
                                                <span className="text-[10px] font-black text-gray-400 uppercase tracking-[0.2em]">Tên lớp</span>
                                                <span className="text-2xl font-black text-[#5B0019]">{editingClass.name}</span>
                                            </div>
                                            <div className="bg-gray-50 p-6 rounded-[2rem] border border-gray-100 flex flex-col gap-1">
                                                <span className="text-[10px] font-black text-gray-400 uppercase tracking-[0.2em]">Khối</span>
                                                <span className="text-2xl font-black text-[#5B0019]">{editingClass.grade}</span>
                                            </div>
                                            <div className="bg-gray-50 p-6 rounded-[2rem] border border-gray-100 flex flex-col gap-1">
                                                <span className="text-[10px] font-black text-gray-400 uppercase tracking-[0.2em]">Niên khóa</span>
                                                <span className="text-2xl font-black text-[#5B0019]">{editingClass.school_year}</span>
                                            </div>
                                        </div>
                                    )}
                                </div>

                                {modalMode === 'edit' && (
                                    <>
                                        {/* Personnel Section */}
                                        <div className="space-y-6">
                                            <div className="flex items-center gap-2 text-[#5B0019]">
                                                {isAdmin ? <UserPlus size={18} /> : <Users size={18} />}
                                                <h3 className="font-black uppercase tracking-widest text-sm">
                                                    {isAdmin ? "Quản lý nhân sự" : "Thông tin giáo viên"}
                                                </h3>
                                            </div>
                                            
                                            <div className="space-y-4">
                                                {isAdmin ? (
                                                    <div className="space-y-2">
                                                        <label className="text-[10px] font-black text-gray-400 uppercase tracking-widest pl-2">Giáo viên chủ nhiệm</label>
                                                        <select 
                                                            value={editingClass.homeroom_teacher_id || ''}
                                                            onChange={(e) => setEditingClass({...editingClass, homeroom_teacher_id: e.target.value})}
                                                            className="w-full px-6 py-4 bg-gray-50 border-none rounded-2xl focus:ring-2 focus:ring-[#5B0019] font-bold"
                                                        >
                                                            <option value="">Chưa chọn giáo viên</option>
                                                            {teachers.map(t => (
                                                                <option key={t.id} value={t.id}>{t.name} ({t.email})</option>
                                                            ))}
                                                        </select>
                                                    </div>
                                                ) : (
                                                    <div className="space-y-2">
                                                        <label className="text-[10px] font-black text-gray-400 uppercase tracking-widest pl-2">Giáo viên chủ nhiệm</label>
                                                        <div className="w-full px-6 py-5 bg-gray-50 rounded-2xl font-bold text-gray-800 border border-gray-100">
                                                            {editingClass.homeroom_teacher_id ? getTeacherName(editingClass.homeroom_teacher_id) : "Chưa có giáo viên chủ nhiệm"}
                                                        </div>
                                                    </div>
                                                )}

                                                <div className="space-y-4">
                                                    <label className="text-[10px] font-black text-gray-400 uppercase tracking-widest pl-2 block">Giáo viên bộ môn</label>
                                                    <div className="space-y-3">
                                                        {editingClass.subject_teachers.map((st: any, idx: number) => (
                                                            <div key={idx} className="flex gap-4 items-center animate-in slide-in-from-left-2 duration-300">
                                                                {isAdmin ? (
                                                                    <>
                                                                        <select 
                                                                            value={st.teacher_id}
                                                                            onChange={(e) => updateSubjectTeacher(idx, 'teacher_id', e.target.value)}
                                                                            className="flex-1 px-6 py-4 bg-gray-50 border-none rounded-2xl focus:ring-2 focus:ring-[#5B0019] font-bold text-sm"
                                                                        >
                                                                            <option value="">Chọn GV</option>
                                                                            {teachers.map(t => (
                                                                                <option key={t.id} value={t.id}>{t.name}</option>
                                                                            ))}
                                                                        </select>
                                                                        <input 
                                                                            type="text"
                                                                            placeholder="Môn học (VD: Toán)"
                                                                            value={st.subject}
                                                                            onChange={(e) => updateSubjectTeacher(idx, 'subject', e.target.value)}
                                                                            className="flex-1 px-6 py-4 bg-gray-50 border-none rounded-2xl focus:ring-2 focus:ring-[#5B0019] font-bold text-sm"
                                                                        />
                                                                        <button 
                                                                            type="button" 
                                                                            onClick={() => removeSubjectTeacher(idx)}
                                                                            className="p-4 bg-red-50 text-red-500 rounded-2xl hover:bg-red-500 hover:text-white transition-all"
                                                                        >
                                                                            <Trash2 size={20} />
                                                                        </button>
                                                                    </>
                                                                ) : (
                                                                    <div className="flex-1 grid grid-cols-2 gap-4">
                                                                        <div className="px-6 py-5 bg-gray-50 rounded-2xl font-bold text-gray-800 border border-gray-100">
                                                                            {getTeacherName(st.teacher_id)}
                                                                        </div>
                                                                        <div className="px-6 py-5 bg-gray-50 rounded-2xl font-bold text-[#5B0019] border border-gray-100 italic">
                                                                            {st.subject}
                                                                        </div>
                                                                    </div>
                                                                )}
                                                            </div>
                                                        ))}
                                                        
                                                        {isAdmin && (
                                                            <button 
                                                                type="button"
                                                                onClick={addSubjectTeacher}
                                                                className="flex items-center gap-2 px-6 py-4 bg-gray-50 text-gray-500 rounded-2xl font-black text-[10px] uppercase hover:bg-gray-100 transition-all border-2 border-dashed border-gray-200"
                                                            >
                                                                <Plus size={16} /> Thêm giáo viên bộ môn
                                                            </button>
                                                        )}

                                                        {!isAdmin && editingClass.subject_teachers.length === 0 && (
                                                            <div className="px-6 py-5 bg-gray-50 rounded-2xl font-bold text-gray-400 border border-dashed italic text-center">
                                                                Chưa có dữ liệu giáo viên bộ môn
                                                            </div>
                                                        )}
                                                    </div>
                                                </div>
                                            </div>
                                        </div>

                                        {/* Students Section */}
                                        <div className="space-y-6">
                                            <div className="flex items-center gap-2 justify-between">
                                                <div className="flex items-center gap-2 text-[#5B0019]">
                                                    <GraduationCap size={18} />
                                                    <h3 className="font-black uppercase tracking-widest text-sm">Danh sách học sinh ({classStudents.length})</h3>
                                                </div>
                                                
                                                {/* Add Student Sub-UI */}
                                                {isAdmin && (
                                                    <div className="relative">
                                                        <div className="flex items-center gap-2 bg-gray-50 px-4 py-2 rounded-2xl focus-within:ring-2 focus-within:ring-[#5B0019] transition-all">
                                                            <Search size={16} className="text-gray-400" />
                                                            <input 
                                                                type="text"
                                                                placeholder="Thêm học sinh mới..."
                                                                value={searchAvailableTerm}
                                                                onChange={(e) => setSearchAvailableTerm(e.target.value)}
                                                                className="bg-transparent border-none focus:ring-0 text-sm font-bold w-48"
                                                            />
                                                        </div>
                                                        
                                                        {searchAvailableTerm && (
                                                            <div className="absolute top-full right-0 mt-2 w-72 bg-white rounded-2xl shadow-2xl border border-gray-100 z-50 overflow-hidden animate-in fade-in slide-in-from-top-2">
                                                                <div className="p-2 max-h-60 overflow-y-auto custom-scrollbar">
                                                                    {isSearchingAvailable ? (
                                                                        <div className="p-4 flex justify-center"><Loader2 className="animate-spin text-[#5B0019]" size={20} /></div>
                                                                    ) : filteredAvailableStudents.length > 0 ? (
                                                                        filteredAvailableStudents.map(s => (
                                                                            <div key={s.id} className="flex items-center justify-between p-3 hover:bg-gray-50 rounded-xl transition-colors">
                                                                                <div className="flex flex-col">
                                                                                    <span className="text-sm font-black text-gray-800">{s.name}</span>
                                                                                    <span className="text-[10px] text-gray-400 font-bold">{s.email}</span>
                                                                                </div>
                                                                                <button 
                                                                                    type="button"
                                                                                    onClick={() => handleAddStudent(s.id)}
                                                                                    className="p-2 bg-green-50 text-green-600 rounded-lg hover:bg-green-600 hover:text-white transition-all"
                                                                                >
                                                                                    <UserPlus size={16} />
                                                                                </button>
                                                                            </div>
                                                                        ))
                                                                    ) : (
                                                                        <div className="p-4 text-center text-xs text-gray-400 font-bold">Không tìm thấy học sinh phù hợp</div>
                                                                    )}
                                                                </div>
                                                            </div>
                                                        )}
                                                    </div>
                                                )}
                                            </div>

                                            <div className="bg-gray-50 rounded-3xl overflow-hidden border border-gray-100">
                                                {loadingStudents ? (
                                                    <div className="p-10 flex justify-center"><Loader2 className="animate-spin text-[#5B0019]" size={20} /></div>
                                                ) : classStudents.length > 0 ? (
                                                    <table className="w-full text-left">
                                                        <thead className="bg-[#5B0019]/5">
                                                            <tr>
                                                                <th className="px-6 py-4 text-[10px] font-black uppercase text-gray-500">Tên học sinh</th>
                                                                <th className="px-6 py-4 text-[10px] font-black uppercase text-gray-500">Email</th>
                                                                {isAdmin && <th className="px-6 py-4 text-[10px] font-black uppercase text-gray-500 text-right">Hành động</th>}
                                                            </tr>
                                                        </thead>
                                                        <tbody className="divide-y divide-gray-100 bg-white">
                                                            {classStudents.map(s => (
                                                                <tr key={s.id} className="hover:bg-gray-50 transition-colors">
                                                                    <td className="px-6 py-4 font-black text-gray-800">{s.name}</td>
                                                                    <td className="px-6 py-4 font-bold text-gray-500 text-sm">{s.email}</td>
                                                                    {isAdmin && (
                                                                        <td className="px-6 py-4 text-right">
                                                                            <button 
                                                                                type="button"
                                                                                onClick={() => handleRemoveStudent(s.id)}
                                                                                className="p-2 text-red-400 hover:bg-red-50 hover:text-red-600 rounded-xl transition-all"
                                                                                title="Gỡ khỏi lớp"
                                                                            >
                                                                                <UserMinus size={18} />
                                                                            </button>
                                                                        </td>
                                                                    )}
                                                                </tr>
                                                            ))}
                                                        </tbody>
                                                    </table>
                                                ) : (
                                                    <div className="p-10 text-center text-gray-400 font-bold italic">Chưa có học sinh nào trong lớp</div>
                                                )}
                                            </div>
                                        </div>
                                    </>
                                )}

                                {/* Actions */}
                                <div className="flex gap-4 pt-6 border-t font-black">
                                    <button 
                                        type="button"
                                        onClick={() => setIsModalOpen(false)}
                                        className="flex-1 py-4 bg-gray-100 rounded-2xl font-black text-gray-500 hover:bg-gray-200 transition-all uppercase text-sm"
                                    >
                                        Đóng
                                    </button>
                                    {isAdmin && (
                                        <button 
                                            type="submit"
                                            className="flex-[2] py-4 bg-[#5B0019] text-white rounded-2xl font-black shadow-lg shadow-red-900/20 hover:scale-[1.01] active:scale-95 transition-all flex items-center justify-center gap-3 uppercase text-sm tracking-widest"
                                        >
                                            <Save size={20} /> {modalMode === 'create' ? 'Tạo Lớp học' : 'Lưu thay đổi'}
                                        </button>
                                    )}
                                </div>
                            </form>
                        </div>
                    </div>
                </div>
            )}

            {/* Delete Confirmation Modal */}
            {deletingClass && (
                <div className="fixed inset-0 z-[60] flex items-center justify-center p-4 bg-black/60 backdrop-blur-md animate-in fade-in duration-300">
                    <div className="w-full max-w-md bg-white rounded-[4rem] shadow-2xl overflow-hidden animate-in zoom-in-95 duration-300">
                        <div className="p-12 text-center space-y-6">
                            <div className="mx-auto w-24 h-24 bg-red-50 text-red-500 rounded-full flex items-center justify-center animate-bounce duration-1000 shadow-inner">
                                <AlertTriangle size={48} />
                            </div>
                            <div className="space-y-2">
                                <h2 className="text-3xl font-black text-gray-800 tracking-tight">Xóa lớp học?</h2>
                                <p className="text-gray-500 font-medium leading-relaxed">
                                    Hành động này sẽ xóa lớp <span className="text-[#5B0019] font-black">"{deletingClass.name}"</span>. 
                                    Tất cả học sinh thuộc lớp này sẽ được chuyển về trạng thái <span className="text-gray-900 font-bold">Chưa có lớp</span>.
                                </p>
                            </div>
                            <div className="flex gap-4 pt-6">
                                <button 
                                    onClick={() => setDeletingClass(null)}
                                    className="flex-1 py-4 bg-gray-100 rounded-2xl font-black text-gray-500 hover:bg-gray-200 transition-all uppercase text-[10px] tracking-[0.2em]"
                                >
                                    Hủy bỏ
                                </button>
                                <button 
                                    disabled={isActionLoading}
                                    onClick={handleDeleteClass}
                                    className="flex-[1.5] py-4 bg-red-500 text-white rounded-2xl font-black shadow-lg shadow-red-900/20 hover:scale-[1.02] active:scale-95 transition-all flex items-center justify-center gap-2 uppercase text-[10px] tracking-[0.2em]"
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

export default ClassesPage;
