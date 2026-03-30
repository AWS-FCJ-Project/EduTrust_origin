"use client";

import React, { useEffect, useState } from 'react';
import { Shield, UserPlus, Mail, Search, Loader2, Download, Edit2, Trash2, X, Save, AlertTriangle, ShieldCheck } from 'lucide-react';
import Link from 'next/link';
import Cookies from 'js-cookie';

const AdminsPage = () => {
    const [admins, setAdmins] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);
    const [searchTerm, setSearchTerm] = useState('');
    
    // Modals state
    const [editingAdmin, setEditingAdmin] = useState<any>(null);
    const [deletingAdmin, setDeletingAdmin] = useState<any>(null);
    const [viewingProfile, setViewingProfile] = useState<any>(null);
    const [isActionLoading, setIsActionLoading] = useState(false);

    const fetchAdmins = async () => {
        const token = Cookies.get('auth_token');
        try {
            setLoading(true);
            const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/users/admins`, {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            
            if (res.ok) {
                const data = await res.json();
                setAdmins(data);
            }
        } catch (error) {
            console.error(error);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchAdmins();
    }, []);

    const handleUpdateAdmin = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!editingAdmin) return;

        try {
            setIsActionLoading(true);
            const token = Cookies.get('auth_token');
            const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/users/${editingAdmin.id}`, {
                method: 'PATCH',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify({
                    name: editingAdmin.name,
                    email: editingAdmin.email,
                    password: editingAdmin.new_password || undefined
                })
            });

            if (res.ok) {
                setEditingAdmin(null);
                fetchAdmins();
            }
        } catch (err) {
            console.error(err);
        } finally {
            setIsActionLoading(false);
        }
    };

    const handleDeleteAdmin = async () => {
        if (!deletingAdmin) return;

        try {
            setIsActionLoading(true);
            const token = Cookies.get('auth_token');
            const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/users/${deletingAdmin.id}`, {
                method: 'DELETE',
                headers: { 'Authorization': `Bearer ${token}` }
            });

            if (res.ok) {
                setDeletingAdmin(null);
                fetchAdmins();
            }
        } catch (err) {
            console.error(err);
        } finally {
            setIsActionLoading(false);
        }
    };

    const filteredAdmins = admins.filter(a => 
        (a.name || "").toLowerCase().includes(searchTerm.toLowerCase()) || 
        (a.email || "").toLowerCase().includes(searchTerm.toLowerCase())
    );

    if (loading) return (
        <div className="flex h-64 items-center justify-center">
            <Loader2 className="animate-spin text-[#5B0019]" size={40} />
        </div>
    );

    return (
        <div className="space-y-8 animate-in fade-in duration-700">
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
                <div className="flex flex-col gap-2">
                    <h1 className="text-3xl font-black text-gray-900 tracking-tight">Danh sách Admin</h1>
                    <p className="text-gray-500 font-medium tracking-wide border-l-4 border-[#5B0019] pl-3">
                        Quản lý đội ngũ quản trị viên cấp cao của hệ thống.
                    </p>
                </div>
                
                <div className="flex items-center gap-3">
                    <button className="flex items-center gap-2 px-5 py-3 bg-white border border-gray-200 rounded-2xl font-bold text-gray-600 hover:bg-gray-50 transition-all shadow-sm">
                        <Download size={18} /> Xuất file
                    </button>
                    <Link 
                        href="/dashboard/management?role=admin"
                        className="flex items-center gap-2 px-6 py-3 bg-[#5B0019] text-white rounded-2xl font-black shadow-lg shadow-red-900/20 hover:scale-105 active:scale-95 transition-all text-sm uppercase"
                    >
                        <UserPlus size={18} /> Thêm Admin
                    </Link>
                </div>
            </div>

            <div className="relative group">
                <Search className="absolute left-6 top-1/2 -translate-y-1/2 text-gray-400 group-focus-within:text-[#5B0019] transition-colors" size={20} />
                <input 
                    type="text"
                    placeholder="Tìm kiếm admin theo tên hoặc email..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    className="w-full pl-14 pr-6 py-5 bg-white border-none rounded-[2rem] shadow-sm focus:ring-2 focus:ring-[#5B0019] transition-all font-bold text-gray-700"
                />
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
                {filteredAdmins.map((admin) => (
                    <div key={admin.id} className="bg-white p-8 rounded-[2.5rem] border border-gray-100 shadow-sm hover:shadow-xl transition-all group overflow-hidden relative">
                        <div className="flex items-start justify-between relative z-10">
                            <div className="bg-[#5B0019]/5 p-4 rounded-2xl text-[#5B0019] group-hover:bg-[#5B0019] group-hover:text-white transition-all duration-500">
                                <ShieldCheck size={28} />
                            </div>
                            <div className="flex gap-2">
                                <button 
                                    onClick={() => setEditingAdmin(admin)}
                                    className="p-2 bg-gray-50 text-gray-400 hover:bg-[#5B0019] hover:text-white rounded-xl transition-all"
                                    title="Chỉnh sửa"
                                >
                                    <Edit2 size={16} />
                                </button>
                                <button 
                                    onClick={() => setDeletingAdmin(admin)}
                                    className="p-2 bg-red-50 text-red-400 hover:bg-red-500 hover:text-white rounded-xl transition-all"
                                    title="Xóa Admin"
                                >
                                    <Trash2 size={16} />
                                </button>
                            </div>
                        </div>

                        <div className="mt-6 relative z-10">
                            <h3 className="text-xl font-black text-gray-800 group-hover:text-[#5B0019] transition-colors">{admin.name || 'Admin'}</h3>
                            <div className="flex items-center gap-2 text-gray-400 mt-2 text-sm font-bold">
                                <Mail size={14} />
                                <span className="truncate">{admin.email}</span>
                            </div>
                            
                            <div className="flex items-center gap-2 text-xs font-black uppercase tracking-widest mt-4">
                                <span className="px-3 py-1 bg-amber-50 text-amber-600 border border-amber-100 rounded-full">
                                    ● Quản trị viên
                                </span>
                            </div>
                        </div>

                        <div className="mt-8 pt-6 border-t border-gray-50 flex gap-3 relative z-10">
                            <button 
                                onClick={() => setViewingProfile(admin)}
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
                    <div className="w-full max-w-xl bg-white rounded-[3rem] shadow-2xl overflow-hidden animate-in zoom-in-95 duration-300">
                        <div className="p-10 border-b bg-gray-50/50 flex items-center justify-between">
                            <div className="flex items-center gap-6">
                                <div className="p-5 bg-[#5B0019] text-white rounded-[2.5rem] shadow-xl shadow-red-900/20">
                                    <ShieldCheck size={40} />
                                </div>
                                <div className="space-y-1">
                                    <h2 className="text-3xl font-black text-gray-900 tracking-tight leading-none">Hồ sơ Admin</h2>
                                    <p className="text-gray-400 font-bold text-sm tracking-widest uppercase">Thông tin quản trị viên</p>
                                </div>
                            </div>
                            <button onClick={() => setViewingProfile(null)} className="p-3 hover:bg-gray-200 rounded-2xl transition-all">
                                <X size={28} className="text-gray-400" />
                            </button>
                        </div>
                        
                        <div className="p-10 space-y-10 max-h-[70vh] overflow-y-auto">
                            <div className="space-y-8">
                                <div className="space-y-2">
                                    <p className="text-[10px] font-black text-gray-400 uppercase tracking-widest flex items-center gap-2">
                                        <Shield size={12} /> Tên Admin
                                    </p>
                                    <p className="text-2xl font-black text-gray-800 tracking-tight">{viewingProfile.name || 'Admin'}</p>
                                </div>
                                <div className="space-y-2">
                                    <p className="text-[10px] font-black text-gray-400 uppercase tracking-widest flex items-center gap-2">
                                        <Mail size={12} /> Email hệ thống
                                    </p>
                                    <p className="text-gray-600 font-bold">{viewingProfile.email}</p>
                                </div>
                                <div className="space-y-2">
                                    <p className="text-[10px] font-black text-gray-400 uppercase tracking-widest flex items-center gap-2">
                                        <ShieldCheck size={12} /> Trạng thái tài khoản
                                    </p>
                                    <div className="flex items-center gap-2">
                                        <span className="px-3 py-1 bg-green-50 text-green-600 rounded-lg font-bold text-sm border border-green-100">
                                            Đang hoạt động
                                        </span>
                                    </div>
                                </div>
                                <div className="space-y-2">
                                    <p className="text-[10px] font-black text-gray-400 uppercase tracking-widest">Vai trò</p>
                                    <span className="inline-block px-4 py-2 bg-amber-100 text-amber-700 rounded-xl text-xs font-black uppercase tracking-widest">
                                        Administrator
                                    </span>
                                </div>
                            </div>
                        </div>
                        
                        <div className="p-8 border-t bg-gray-50/50 flex gap-4">
                            <button 
                                onClick={() => { setViewingProfile(null); setEditingAdmin(viewingProfile); }}
                                className="flex-1 py-4 bg-white border border-gray-200 rounded-2xl font-black text-sm text-[#5B0019] hover:bg-gray-50 transition-all uppercase tracking-widest flex items-center justify-center gap-2 shadow-sm"
                            >
                                <Edit2 size={18} /> Chỉnh sửa
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
            {editingAdmin && (
                <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-md animate-in fade-in duration-300">
                    <div className="w-full max-w-lg bg-white rounded-[3rem] shadow-2xl overflow-hidden animate-in zoom-in-95 duration-300">
                        <div className="p-8 border-b bg-gray-50/50 flex items-center justify-between">
                            <div className="flex items-center gap-4">
                                <div className="p-3 bg-[#5B0019] text-white rounded-2xl shadow-lg shadow-red-900/20">
                                    <Edit2 size={24} />
                                </div>
                                <h2 className="text-xl font-black text-gray-800 tracking-tight">Cập nhật hồ sơ Admin</h2>
                            </div>
                            <button onClick={() => setEditingAdmin(null)} className="p-2 hover:bg-gray-200 rounded-xl transition-all">
                                <X size={24} className="text-gray-400" />
                            </button>
                        </div>
                        
                        <form onSubmit={handleUpdateAdmin} className="p-8 space-y-6">
                            <div className="space-y-6">
                                <div className="space-y-2">
                                    <label className="text-[10px] font-black text-gray-400 uppercase tracking-widest pl-2">Họ và tên</label>
                                    <input 
                                        required
                                        type="text"
                                        value={editingAdmin.name || ''}
                                        onChange={(e) => setEditingAdmin({...editingAdmin, name: e.target.value})}
                                        className="w-full px-6 py-4 bg-gray-50 border-none rounded-2xl focus:ring-2 focus:ring-[#5B0019] font-bold text-gray-700"
                                    />
                                </div>
                                <div className="space-y-2">
                                    <label className="text-[10px] font-black text-gray-400 uppercase tracking-widest pl-2">Email hệ thống</label>
                                    <input 
                                        required
                                        type="email"
                                        value={editingAdmin.email || ''}
                                        onChange={(e) => setEditingAdmin({...editingAdmin, email: e.target.value})}
                                        className="w-full px-6 py-4 bg-gray-50 border-none rounded-2xl focus:ring-2 focus:ring-[#5B0019] font-bold text-gray-700"
                                    />
                                </div>
                                <div className="space-y-2">
                                    <label className="text-[10px] font-black text-gray-400 uppercase tracking-widest pl-2">Mật khẩu mới (Để trống nếu không đổi)</label>
                                    <input 
                                        type="password"
                                        placeholder="Nhập mật khẩu mới cho admin..."
                                        value={editingAdmin.new_password || ''}
                                        onChange={(e) => setEditingAdmin({...editingAdmin, new_password: e.target.value})}
                                        className="w-full px-6 py-4 bg-gray-50 border-none rounded-2xl focus:ring-2 focus:ring-[#5B0019] font-bold text-gray-700"
                                    />
                                </div>
                            </div>

                            <div className="flex gap-4 pt-4">
                                <button 
                                    type="button"
                                    onClick={() => setEditingAdmin(null)}
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
            {deletingAdmin && (
                <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-md animate-in fade-in duration-300">
                    <div className="w-full max-w-md bg-white rounded-[3rem] shadow-2xl overflow-hidden animate-in zoom-in-95 duration-300">
                        <div className="p-10 text-center space-y-6">
                            <div className="mx-auto w-20 h-20 bg-red-50 text-red-500 rounded-full flex items-center justify-center animate-bounce duration-1000">
                                <AlertTriangle size={40} />
                            </div>
                            <div className="space-y-2">
                                <h2 className="text-2xl font-black text-gray-800 tracking-tight">Xóa Admin?</h2>
                                <p className="text-gray-500 font-medium">
                                    Hành động này sẽ xóa <span className="text-gray-900 font-bold">{deletingAdmin.name || deletingAdmin.email}</span> khỏi hệ thống.
                                </p>
                            </div>
                            <div className="flex gap-4 pt-4">
                                <button 
                                    onClick={() => setDeletingAdmin(null)}
                                    className="flex-1 py-4 bg-gray-100 rounded-2xl font-black text-gray-500 hover:bg-gray-200 transition-all uppercase text-[10px] tracking-widest"
                                >
                                    Quay lại
                                </button>
                                <button 
                                    disabled={isActionLoading}
                                    onClick={handleDeleteAdmin}
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
        </div>
    );
};

export default AdminsPage;
