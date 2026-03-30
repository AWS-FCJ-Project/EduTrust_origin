"use client";

import React, { useEffect, useState } from 'react';
import { Users, UserPlus, Mail, Shield, Search, Loader2, Download, Edit2, Trash2, X, Save, AlertTriangle, CheckCircle, BookOpen, Plus, GraduationCap, School } from 'lucide-react';
import Link from 'next/link';
import Cookies from 'js-cookie';

const TeachersPage = () => {
    const [teachers, setTeachers] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);
    const [searchTerm, setSearchTerm] = useState('');
    
    // Modals state
    const [editingTeacher, setEditingTeacher] = useState<any>(null);
    const [deletingTeacher, setDeletingTeacher] = useState<any>(null);
    const [viewingProfile, setViewingProfile] = useState<any>(null);
    const [isActionLoading, setIsActionLoading] = useState(false);
    
    // UI Helpers
    const [newSubject, setNewSubject] = useState('');

    const fetchTeachers = async () => {
        const token = Cookies.get('auth_token');
        try {
            setLoading(true);
            const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/users/teachers`, {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            
            if (res.ok) {
                const data = await res.json();
                setTeachers(data);
            }
        } catch (error) {
            console.error(error);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchTeachers();
    }, []);

    const handleUpdateTeacher = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!editingTeacher) return;

        try {
            setIsActionLoading(true);
            const token = Cookies.get('auth_token');
            const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/users/${editingTeacher.id}`, {
                method: 'PATCH',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify({
                    name: editingTeacher.name,
                    email: editingTeacher.email,
                    subjects: editingTeacher.subjects || [],
                    password: editingTeacher.new_password || undefined
                })
            });

            if (res.ok) {
                setEditingTeacher(null);
                fetchTeachers();
            }
        } catch (err) {
            console.error(err);
        } finally {
            setIsActionLoading(false);
        }
    };

    const handleDeleteTeacher = async () => {
        if (!deletingTeacher) return;

        try {
            setIsActionLoading(true);
            const token = Cookies.get('auth_token');
            const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/users/${deletingTeacher.id}`, {
                method: 'DELETE',
                headers: { 'Authorization': `Bearer ${token}` }
            });

            if (res.ok) {
                setDeletingTeacher(null);
                fetchTeachers();
            }
        } catch (err) {
            console.error(err);
        } finally {
            setIsActionLoading(false);
        }
    };

    const addSubject = () => {
        if (!newSubject.trim()) return;
        if (editingTeacher.subjects?.includes(newSubject.trim())) return;
        
        setEditingTeacher({
            ...editingTeacher,
            subjects: [...(editingTeacher.subjects || []), newSubject.trim()]
        });
        setNewSubject('');
    };

    const removeSubject = (subject: string) => {
        setEditingTeacher({
            ...editingTeacher,
            subjects: editingTeacher.subjects.filter((s: string) => s !== subject)
        });
    };

    const filteredTeachers = teachers.filter(t => 
        (t.name || "").toLowerCase().includes(searchTerm.toLowerCase()) || 
        (t.email || "").toLowerCase().includes(searchTerm.toLowerCase())
    );

    // Grouping assignments for profile
    const getCategorizedAssignments = (assignedClasses: any[]) => {
        const homeroom = assignedClasses.filter(c => c.role === "Giáo viên Chủ nhiệm");
        const subjects = assignedClasses.filter(c => c.role.startsWith("Giáo viên Bộ môn"));
        return { homeroom, subjects };
    };

    if (loading) return (
        <div className="flex h-64 items-center justify-center">
            <Loader2 className="animate-spin text-[#5B0019]" size={40} />
        </div>
    );

    return (
        <div className="space-y-8 animate-in fade-in duration-700">
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
                <div className="flex flex-col gap-2">
                    <h1 className="text-3xl font-black text-gray-900 tracking-tight">Danh sách Giáo viên</h1>
                    <p className="text-gray-500 font-medium tracking-wide border-l-4 border-[#5B0019] pl-3">
                        Quản lý đội ngũ và phân loại nhiệm vụ giảng dạy.
                    </p>
                </div>
                
                <div className="flex items-center gap-3">
                    <button className="flex items-center gap-2 px-5 py-3 bg-white border border-gray-200 rounded-2xl font-bold text-gray-600 hover:bg-gray-50 transition-all shadow-sm">
                        <Download size={18} /> Xuất file
                    </button>
                    <Link 
                        href="/dashboard/management?role=teacher"
                        className="flex items-center gap-2 px-6 py-3 bg-[#5B0019] text-white rounded-2xl font-black shadow-lg shadow-red-900/20 hover:scale-105 active:scale-95 transition-all text-sm uppercase"
                    >
                        <UserPlus size={18} /> Thêm giáo viên
                    </Link>
                </div>
            </div>

            <div className="relative group">
                <Search className="absolute left-6 top-1/2 -translate-y-1/2 text-gray-400 group-focus-within:text-[#5B0019] transition-colors" size={20} />
                <input 
                    type="text"
                    placeholder="Tìm kiếm giáo viên theo tên, email hoặc môn dạy..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    className="w-full pl-14 pr-6 py-5 bg-white border-none rounded-[2rem] shadow-sm focus:ring-2 focus:ring-[#5B0019] transition-all font-bold text-gray-700"
                />
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
                {filteredTeachers.map((teacher) => (
                    <div key={teacher.id} className="bg-white p-8 rounded-[2.5rem] border border-gray-100 shadow-sm hover:shadow-xl transition-all group overflow-hidden relative">
                        <div className="flex items-start justify-between relative z-10">
                            <div className="bg-[#5B0019]/5 p-4 rounded-2xl text-[#5B0019] group-hover:bg-[#5B0019] group-hover:text-white transition-all duration-500">
                                <Users size={28} />
                            </div>
                            <div className="flex gap-2">
                                <button 
                                    onClick={() => setEditingTeacher(teacher)}
                                    className="p-2 bg-gray-50 text-gray-400 hover:bg-[#5B0019] hover:text-white rounded-xl transition-all"
                                    title="Chỉnh sửa"
                                >
                                    <Edit2 size={16} />
                                </button>
                                <button 
                                    onClick={() => setDeletingTeacher(teacher)}
                                    className="p-2 bg-red-50 text-red-400 hover:bg-red-500 hover:text-white rounded-xl transition-all"
                                    title="Xóa giáo viên"
                                >
                                    <Trash2 size={16} />
                                </button>
                            </div>
                        </div>

                        <div className="mt-6 relative z-10">
                            <h3 className="text-xl font-black text-gray-800 group-hover:text-[#5B0019] transition-colors">{teacher.name || 'N/A'}</h3>
                            <div className="flex items-center gap-2 text-gray-400 mt-2 text-sm font-bold">
                                <Mail size={14} />
                                <span className="truncate">{teacher.email}</span>
                            </div>
                            
                            {/* Specialization Tags */}
                            <div className="mt-3 flex flex-wrap gap-2">
                                {teacher.subjects && teacher.subjects.length > 0 ? (
                                    teacher.subjects.map((s: string, idx: number) => (
                                        <span key={idx} className="px-2 py-0.5 bg-gray-50 text-gray-500 rounded-md text-[10px] font-black uppercase border border-gray-100 italic">
                                            {s}
                                        </span>
                                    ))
                                ) : (
                                    <span className="text-[10px] font-bold text-gray-300 italic uppercase">Chưa cập nhật chuyên môn</span>
                                )}
                            </div>

                            <div className="flex items-center gap-2 text-xs font-black uppercase tracking-widest mt-4">
                                <span className={`px-3 py-1 rounded-full border ${teacher.is_assigned ? 'bg-indigo-50 text-indigo-600 border-indigo-100' : 'bg-green-50 text-green-600 border-green-100'}`}>
                                    {teacher.is_assigned ? `● Đã giao ${teacher.assigned_classes.length} lớp` : '● Đang chờ giao lớp'}
                                </span>
                            </div>
                        </div>

                        <div className="mt-8 pt-6 border-t border-gray-50 flex gap-3 relative z-10">
                            <button 
                                onClick={() => setViewingProfile(teacher)}
                                className="flex-1 py-4 px-4 bg-[#5B0019]/5 text-[#5B0019] rounded-2xl font-black text-sm hover:bg-[#5B0019] hover:text-white transition-all uppercase tracking-widest shadow-sm"
                            >
                                Xem hồ sơ chi tiết
                            </button>
                        </div>
                    </div>
                ))}
            </div>

            {/* Profile Modal */}
            {viewingProfile && (
                <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-md animate-in fade-in duration-300">
                    <div className="w-full max-w-2xl bg-white rounded-[3rem] shadow-2xl overflow-hidden animate-in zoom-in-95 duration-300">
                        <div className="p-10 border-b bg-gray-50/50 flex items-center justify-between">
                            <div className="flex items-center gap-6">
                                <div className="p-5 bg-[#5B0019] text-white rounded-[2.5rem] shadow-xl shadow-red-900/20">
                                    <Users size={40} />
                                </div>
                                <div className="space-y-1">
                                    <h2 className="text-3xl font-black text-gray-900 tracking-tight leading-none">Hồ sơ Giáo viên</h2>
                                    <p className="text-gray-400 font-bold text-sm tracking-widest uppercase">Phân loại môn dạy & nhiệm vụ</p>
                                </div>
                            </div>
                            <button onClick={() => setViewingProfile(null)} className="p-3 hover:bg-gray-200 rounded-2xl transition-all">
                                <X size={28} className="text-gray-400" />
                            </button>
                        </div>
                        
                        <div className="p-10 space-y-10 max-h-[70vh] overflow-y-auto custom-scrollbar">
                            <div className="grid grid-cols-1 md:grid-cols-1 gap-10">
                                {/* Basic & Specialization */}
                                <div className="flex flex-col md:flex-row gap-10">
                                    <div className="flex-1 space-y-6">
                                        <div className="space-y-2">
                                            <p className="text-[10px] font-black text-gray-400 uppercase tracking-widest flex items-center gap-2">
                                                <Users size={12} /> Họ và tên
                                            </p>
                                            <p className="text-2xl font-black text-gray-800 tracking-tight">{viewingProfile.name || 'N/A'}</p>
                                        </div>
                                        <div className="space-y-2">
                                            <p className="text-[10px] font-black text-gray-400 uppercase tracking-widest flex items-center gap-2">
                                                <Mail size={12} /> Email hệ thống
                                            </p>
                                            <p className="text-gray-600 font-bold">{viewingProfile.email}</p>
                                        </div>
                                        <div className="space-y-2">
                                            <p className="text-[10px] font-black text-gray-400 uppercase tracking-widest flex items-center gap-2">
                                                <Shield size={12} /> Trạng thái tài khoản
                                            </p>
                                            <div className="flex items-center gap-2">
                                                <span className="px-3 py-1 bg-green-50 text-green-600 rounded-lg font-bold text-sm border border-green-100">
                                                    Đang hoạt động
                                                </span>
                                            </div>
                                        </div>
                                    </div>
                                    <div className="flex-1 space-y-4">
                                        <p className="text-[10px] font-black text-gray-400 uppercase tracking-widest flex items-center gap-2">
                                            <GraduationCap size={14} /> Chuyên môn môn dạy
                                        </p>
                                        <div className="flex flex-wrap gap-2">
                                            {viewingProfile.subjects && viewingProfile.subjects.length > 0 ? (
                                                viewingProfile.subjects.map((s: string, i: number) => (
                                                    <span key={i} className="px-4 py-2 bg-[#5B0019] text-white rounded-xl text-xs font-black uppercase tracking-widest shadow-sm">
                                                        {s}
                                                    </span>
                                                ))
                                            ) : (
                                                <p className="text-gray-400 italic font-bold">Chưa cập nhật chuyên môn</p>
                                            )}
                                        </div>
                                    </div>
                                </div>

                                <hr className="border-gray-100" />

                                {/* Assignments Categories */}
                                <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                                    {/* Homeroom Section */}
                                    <div className="space-y-4">
                                        <div className="flex items-center gap-3 text-indigo-600">
                                            <School size={20} />
                                            <h3 className="font-black uppercase tracking-widest text-sm">Lớp Chủ nhiệm</h3>
                                        </div>
                                        <div className="space-y-3">
                                            {getCategorizedAssignments(viewingProfile.assigned_classes).homeroom.length > 0 ? (
                                                getCategorizedAssignments(viewingProfile.assigned_classes).homeroom.map((cls: any, i: number) => (
                                                    <div key={i} className="bg-indigo-50/50 p-4 rounded-2xl border border-indigo-100 flex items-center justify-between">
                                                        <p className="font-black text-indigo-900 text-lg">{cls.name}</p>
                                                        <div className="p-2 bg-indigo-500 text-white rounded-lg">
                                                            <CheckCircle size={16} />
                                                        </div>
                                                    </div>
                                                ))
                                            ) : (
                                                <div className="py-8 bg-gray-50 rounded-[2rem] border border-dashed border-gray-200 text-center">
                                                    <p className="text-gray-300 text-xs font-bold uppercase tracking-widest">Không có lớp chủ nhiệm</p>
                                                </div>
                                            )}
                                        </div>
                                    </div>

                                    {/* Subject Teaching Section */}
                                    <div className="space-y-4">
                                        <div className="flex items-center gap-3 text-[#5B0019]">
                                            <BookOpen size={20} />
                                            <h3 className="font-black uppercase tracking-widest text-sm">Lớp Bộ môn</h3>
                                        </div>
                                        <div className="space-y-3">
                                            {getCategorizedAssignments(viewingProfile.assigned_classes).subjects.length > 0 ? (
                                                getCategorizedAssignments(viewingProfile.assigned_classes).subjects.map((cls: any, i: number) => (
                                                    <div key={i} className="bg-[#5B0019]/5 p-4 rounded-2xl border border-red-100 flex items-center justify-between">
                                                        <div>
                                                            <p className="font-black text-gray-800 text-lg leading-none">{cls.name}</p>
                                                            <p className="text-[10px] font-bold text-[#5B0019] uppercase tracking-widest mt-1">
                                                                {cls.role.replace("Giáo viên Bộ môn (", "").replace(")", "")}
                                                            </p>
                                                        </div>
                                                        <div className="p-2 bg-[#5B0019] text-white rounded-lg">
                                                            <CheckCircle size={16} />
                                                        </div>
                                                    </div>
                                                ))
                                            ) : (
                                                <div className="py-8 bg-gray-50 rounded-[2rem] border border-dashed border-gray-200 text-center">
                                                    <p className="text-gray-300 text-xs font-bold uppercase tracking-widest">Không dạy bộ môn</p>
                                                </div>
                                            )}
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                        
                        <div className="p-8 border-t bg-gray-50/50 flex gap-4">
                            <button 
                                onClick={() => { setViewingProfile(null); setEditingTeacher(viewingProfile); }}
                                className="flex-1 py-4 bg-white border border-gray-200 rounded-2xl font-black text-sm text-[#5B0019] hover:bg-gray-50 transition-all uppercase tracking-widest flex items-center justify-center gap-2 shadow-sm"
                            >
                                <Edit2 size={18} /> Chỉnh sửa chuyên môn
                            </button>
                            <button 
                                onClick={() => setViewingProfile(null)}
                                className="flex-1 py-4 bg-[#5B0019] rounded-2xl font-black text-sm text-white hover:scale-[1.02] active:scale-95 transition-all uppercase tracking-widest shadow-lg shadow-red-900/10"
                            >
                                Đóng hồ sơ
                            </button>
                        </div>
                    </div>
                </div>
            )}

            {/* Edit Modal */}
            {editingTeacher && (
                <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-md animate-in fade-in duration-300">
                    <div className="grow w-full max-w-lg bg-white rounded-[3rem] shadow-2xl overflow-hidden animate-in zoom-in-95 duration-300">
                        <div className="p-8 border-b bg-gray-50/50 flex items-center justify-between">
                            <div className="flex items-center gap-4">
                                <div className="p-3 bg-[#5B0019] text-white rounded-2xl shadow-lg shadow-red-900/20">
                                    <Edit2 size={24} />
                                </div>
                                <h2 className="text-xl font-black text-gray-800 tracking-tight">Cập nhật hồ sơ</h2>
                            </div>
                            <button onClick={() => setEditingTeacher(null)} className="p-2 hover:bg-gray-200 rounded-xl transition-all">
                                <X size={24} className="text-gray-400" />
                            </button>
                        </div>
                        
                        <form onSubmit={handleUpdateTeacher} className="p-8 space-y-6">
                            <div className="space-y-6">
                                <div className="space-y-2">
                                    <label className="text-[10px] font-black text-gray-400 uppercase tracking-widest pl-2">Họ và tên</label>
                                    <input 
                                        required
                                        type="text"
                                        value={editingTeacher.name || ''}
                                        onChange={(e) => setEditingTeacher({...editingTeacher, name: e.target.value})}
                                        className="w-full px-6 py-4 bg-gray-50 border-none rounded-2xl focus:ring-2 focus:ring-[#5B0019] font-bold text-gray-700"
                                    />
                                </div>
                                <div className="space-y-2">
                                    <label className="text-[10px] font-black text-gray-400 uppercase tracking-widest pl-2">Email hệ thống</label>
                                    <input 
                                        required
                                        type="email"
                                        value={editingTeacher.email || ''}
                                        onChange={(e) => setEditingTeacher({...editingTeacher, email: e.target.value})}
                                        className="w-full px-6 py-4 bg-gray-50 border-none rounded-2xl focus:ring-2 focus:ring-[#5B0019] font-bold text-gray-700"
                                    />
                                </div>
                                
                                <div className="space-y-2">
                                    <label className="text-[10px] font-black text-gray-400 uppercase tracking-widest pl-2">Mật khẩu mới (Để trống nếu không đổi)</label>
                                    <input 
                                        type="password"
                                        placeholder="Nhập mật khẩu mới cho giáo viên..."
                                        value={editingTeacher.new_password || ''}
                                        onChange={(e) => setEditingTeacher({...editingTeacher, new_password: e.target.value})}
                                        className="w-full px-6 py-4 bg-gray-50 border-none rounded-2xl focus:ring-2 focus:ring-[#5B0019] font-bold text-gray-700"
                                    />
                                </div>
                                
                                <div className="space-y-3">
                                    <label className="text-[10px] font-black text-gray-400 uppercase tracking-widest pl-2">Chuyên môn môn dạy</label>
                                    <div className="flex gap-2">
                                        <input 
                                            type="text"
                                            placeholder="Nhập tên môn dạy và Enter..."
                                            value={newSubject}
                                            onChange={(e) => setNewSubject(e.target.value)}
                                            onKeyPress={(e) => e.key === 'Enter' && (e.preventDefault(), addSubject())}
                                            className="flex-1 px-6 py-4 bg-gray-50 border-none rounded-2xl focus:ring-2 focus:ring-[#5B0019] font-bold text-gray-700"
                                        />
                                        <button 
                                            type="button" 
                                            onClick={addSubject}
                                            className="p-4 bg-[#5B0019] text-white rounded-2xl hover:scale-105 transition-all shadow-lg shadow-red-900/10"
                                        >
                                            <Plus size={24} />
                                        </button>
                                    </div>
                                    
                                    <div className="flex flex-wrap gap-2 mt-2 min-h-[40px] p-2 bg-gray-50/50 rounded-2xl border border-dashed border-gray-200">
                                        {editingTeacher.subjects && editingTeacher.subjects.length > 0 ? (
                                            editingTeacher.subjects.map((s: string, idx: number) => (
                                                <div key={idx} className="flex items-center gap-2 px-4 py-2 bg-white border border-gray-100 text-[#5B0019] rounded-xl font-black text-[10px] uppercase shadow-sm">
                                                    {s}
                                                    <button type="button" onClick={() => removeSubject(s)} className="text-red-400 hover:text-red-600 transition-colors">
                                                        <X size={14} />
                                                    </button>
                                                </div>
                                            ))
                                        ) : (
                                            <p className="text-gray-300 text-[10px] font-bold uppercase italic p-2">Chưa thêm môn dạy nào</p>
                                        )}
                                    </div>
                                </div>
                            </div>

                            <div className="flex gap-4 pt-4">
                                <button 
                                    type="button"
                                    onClick={() => setEditingTeacher(null)}
                                    className="flex-1 py-4 bg-gray-100 rounded-2xl font-black text-gray-500 hover:bg-gray-200 transition-all uppercase text-[10px] tracking-widest"
                                >
                                    Hủy bỏ
                                </button>
                                <button 
                                    disabled={isActionLoading}
                                    type="submit"
                                    className="flex-[2] py-4 bg-[#5B0019] text-white rounded-2xl font-black shadow-lg shadow-red-900/10 hover:scale-[1.02] active:scale-95 transition-all flex items-center justify-center gap-2 uppercase text-[10px] tracking-widest"
                                >
                                    {isActionLoading ? <Loader2 className="animate-spin" size={18} /> : <Save size={18} />}
                                    Lưu hồ sơ
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            )}

            {/* Delete Modal */}
            {deletingTeacher && (
                <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-md animate-in fade-in duration-300">
                    <div className="w-full max-w-md bg-white rounded-[3rem] shadow-2xl overflow-hidden animate-in zoom-in-95 duration-300">
                        <div className="p-10 text-center space-y-6">
                            <div className="mx-auto w-20 h-20 bg-red-50 text-red-500 rounded-full flex items-center justify-center animate-bounce duration-1000">
                                <AlertTriangle size={40} />
                            </div>
                            <div className="space-y-2">
                                <h2 className="text-2xl font-black text-gray-800 tracking-tight">Xóa giáo viên?</h2>
                                <p className="text-gray-500 font-medium">
                                    Hành động này sẽ xóa <span className="text-gray-900 font-bold">{deletingTeacher.name || deletingTeacher.email}</span> khỏi hệ thống và gỡ khỏi các lớp đang phụ trách.
                                </p>
                            </div>
                            <div className="flex gap-4 pt-4">
                                <button 
                                    onClick={() => setDeletingTeacher(null)}
                                    className="flex-1 py-4 bg-gray-100 rounded-2xl font-black text-gray-500 hover:bg-gray-200 transition-all uppercase text-[10px] tracking-widest"
                                >
                                    Quay lại
                                </button>
                                <button 
                                    disabled={isActionLoading}
                                    onClick={handleDeleteTeacher}
                                    className="flex-1 py-4 bg-red-500 text-white rounded-2xl font-black shadow-lg shadow-red-900/20 hover:scale-[1.02] active:scale-95 transition-all flex items-center justify-center gap-2 uppercase text-[10px] tracking-widest"
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

export default TeachersPage;
