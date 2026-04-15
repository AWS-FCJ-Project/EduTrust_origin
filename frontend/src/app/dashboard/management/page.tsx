"use client";

import React, { useState, useRef } from 'react';
import { UserPlus, Users, FileSpreadsheet, Download, Upload, Save, CheckCircle2, AlertCircle, Loader2, FileCode, Eye, EyeOff, Camera } from 'lucide-react';
import Cookies from 'js-cookie';
import * as XLSX from 'xlsx';
import { useSearchParams } from 'next/navigation';

const ManagementPage = () => {
    const searchParams = useSearchParams();
    const initialRole = searchParams.get('role') || 'student';
    
    const [activeTab, setActiveTab] = useState<'single' | 'bulk'>('single');
    const [loading, setLoading] = useState(false);
    const [message, setMessage] = useState<{ type: 'success' | 'error', text: string } | null>(null);
    const [showPassword, setShowPassword] = useState(false);

    // Single Creation State
    const [formData, setFormData] = useState({
        email: '',
        password: '',
        name: '',
        role: initialRole,
        class_name: '',
        grade: ''
    });
    const [avatar, setAvatar] = useState<string | null>(null);
    const [avatarPreview, setAvatarPreview] = useState<string | null>(null);
    const avatarInputRef = useRef<HTMLInputElement>(null);

    const handleSingleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);
        setMessage(null);
        try {
            const token = Cookies.get('auth_token');
            const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/register`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify({
                    ...formData,
                    grade: formData.role === 'student' ? parseInt(formData.grade) : undefined,
                    avatar: avatar || undefined
                })
            });

            if (res.ok) {
                setMessage({ type: 'success', text: 'Tạo tài khoản thành công!' });
                setFormData({ email: '', password: '', name: '', role: 'student', class_name: '', grade: '' });
                setAvatar(null);
                setAvatarPreview(null);
            } else {
                const err = await res.json();
                setMessage({ type: 'error', text: err.detail || 'Lỗi khi tạo tài khoản' });
            }
        } catch {
            setMessage({ type: 'error', text: 'Lỗi kết nối máy chủ' });
        } finally {
            setLoading(false);
        }
    };

    const handleAvatarChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0];
        if (!file) return;

        if (!file.type.startsWith('image/')) {
            setMessage({ type: 'error', text: 'Vui lòng chọn file hình ảnh.' });
            return;
        }

        if (file.size > 5 * 1024 * 1024) {
            setMessage({ type: 'error', text: 'Kích thước file không được vượt quá 5MB.' });
            return;
        }

        const reader = new FileReader();
        reader.onloadend = () => {
            const base64 = reader.result as string;
            setAvatar(base64);
            setAvatarPreview(base64);
        };
        reader.readAsDataURL(file);
    };

    const downloadTemplate = (role: string, format: 'xlsx' | 'csv') => {
        const data = role === 'student' 
            ? [{ email: 'hs1@gmail.com', password: 'Password123#', name: 'Nguyễn Văn A', role: 'student', class_name: '10A1', grade: 10 }]
            : [{ email: 'gv1@gmail.com', password: 'Password123#', name: 'Trần Thị B', role: 'teacher' }];
        
        if (format === 'xlsx') {
            const ws = XLSX.utils.json_to_sheet(data);
            const wb = XLSX.utils.book_new();
            XLSX.utils.book_append_sheet(wb, ws, "Template");
            XLSX.writeFile(wb, `template_${role}.xlsx`);
        } else {
            // CSV with BOM for UTF-8 support in Excel
            const headers = Object.keys(data[0]).join(',');
            const rows = data.map(obj => Object.values(obj).join(',')).join('\n');
            const csvContent = "\uFEFF" + headers + "\n" + rows;
            const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
            const link = document.createElement("a");
            const url = URL.createObjectURL(blob);
            link.setAttribute("href", url);
            link.setAttribute("download", `template_${role}.csv`);
            link.style.visibility = 'hidden';
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
        }
    };

    const handleBulkUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0];
        if (!file) return;

        setLoading(true);
        setMessage(null);
        const formData = new FormData();
        formData.append('file', file);

        try {
            const token = Cookies.get('auth_token');
            const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/multi-register`, {
                method: 'POST',
                headers: { 'Authorization': `Bearer ${token}` },
                body: formData
            });

            if (res.ok) {
                const result = await res.json();
                setMessage({ 
                    type: 'success', 
                    text: `Đã xử lý xong! Thành công: ${result.message}. Lỗi: ${result.errors.length}` 
                });
            } else {
                setMessage({ type: 'error', text: 'Lỗi khi upload file' });
            }
        } catch {
            setMessage({ type: 'error', text: 'Lỗi kết nối' });
        } finally {
            setLoading(false);
            e.target.value = '';
        }
    };

    return (
        <div className="max-w-4xl mx-auto space-y-8 pb-12">
            <div className="flex flex-col gap-2">
                <h1 className="text-3xl font-black text-gray-900 tracking-tight">Quản trị Người dùng</h1>
                <p className="text-gray-500 font-medium tracking-wide border-l-4 border-[#5B0019] pl-3">
                    Thêm mới tài khoản giáo viên, học sinh và admin vào hệ thống.
                </p>
            </div>

            {/* Tabs */}
            <div className="flex bg-white p-2 rounded-[2rem] shadow-sm border border-gray-100 w-fit mx-auto lg:mx-0">
                <button 
                    onClick={() => setActiveTab('single')}
                    className={`px-8 py-3 rounded-[1.5rem] font-black text-sm transition-all flex items-center gap-2 ${activeTab === 'single' ? 'bg-[#5B0019] text-white shadow-lg' : 'text-gray-400 hover:text-gray-600'}`}
                >
                    <UserPlus size={18} /> Tạo lẻ
                </button>
                <button 
                    onClick={() => setActiveTab('bulk')}
                    className={`px-8 py-3 rounded-[1.5rem] font-black text-sm transition-all flex items-center gap-2 ${activeTab === 'bulk' ? 'bg-[#5B0019] text-white shadow-lg' : 'text-gray-400 hover:text-gray-600'}`}
                >
                    <FileSpreadsheet size={18} /> Tạo hàng loạt
                </button>
            </div>

            {message && (
                <div className={`p-4 rounded-[1.5rem] flex items-center gap-3 animate-in fade-in slide-in-from-top-4 duration-500 ${message.type === 'success' ? 'bg-green-50 text-green-700 border border-green-100' : 'bg-red-50 text-red-700 border border-red-100'}`}>
                    {message.type === 'success' ? <CheckCircle2 size={20} /> : <AlertCircle size={20} />}
                    <span className="font-bold text-sm">{message.text}</span>
                </div>
            )}

            <div className="bg-white rounded-[3rem] border border-gray-100 shadow-xl shadow-gray-200/50 overflow-hidden min-h-[400px]">
                {activeTab === 'single' ? (
                    <div className="p-10 space-y-8">
                        <div className="flex items-center gap-3">
                            <div className="bg-[#5B0019] p-3 rounded-2xl text-white">
                                <Users size={24} />
                            </div>
                            <h2 className="text-xl font-black text-gray-800">Thông tin người dùng mới</h2>
                        </div>

                        <form onSubmit={handleSingleSubmit} className="grid grid-cols-1 md:grid-cols-2 gap-6">
                            {/* Avatar upload */}
                            <div className="space-y-2 md:col-span-2">
                                <label className="text-[10px] font-black text-gray-400 uppercase tracking-[0.2em] pl-2">Ảnh đại diện</label>
                                <div className="flex items-center gap-4">
                                    <div
                                        className="w-20 h-20 rounded-full overflow-hidden bg-gray-100 cursor-pointer flex items-center justify-center group hover:bg-gray-200 transition-all"
                                        onClick={() => avatarInputRef.current?.click()}
                                    >
                                        {avatarPreview ? (
                                            // eslint-disable-next-line @next/next/no-img-element
                                            <img src={avatarPreview} alt="Avatar preview" className="object-cover w-full h-full" />
                                        ) : (
                                            <Camera size={24} className="text-gray-400 group-hover:text-gray-600" />
                                        )}
                                    </div>
                                    <div className="flex flex-col gap-1">
                                        <button
                                            type="button"
                                            onClick={() => avatarInputRef.current?.click()}
                                            className="px-4 py-2 bg-[#5B0019] text-white text-sm font-bold rounded-xl hover:bg-[#4a0014] transition-all"
                                        >
                                            Chọn ảnh
                                        </button>
                                        <p className="text-xs text-gray-400">PNG, JPG tối đa 5MB</p>
                                    </div>
                                    {avatarPreview && (
                                        <button
                                            type="button"
                                            onClick={() => { setAvatar(null); setAvatarPreview(null); }}
                                            className="text-xs text-red-500 hover:text-red-700 font-medium"
                                        >
                                            Xóa ảnh
                                        </button>
                                    )}
                                </div>
                                <input
                                    ref={avatarInputRef}
                                    type="file"
                                    accept="image/*"
                                    onChange={handleAvatarChange}
                                    className="hidden"
                                />
                            </div>

                            <div className="space-y-2">
                                <label className="text-[10px] font-black text-gray-400 uppercase tracking-[0.2em] pl-2">Họ và tên</label>
                                <input 
                                    required
                                    type="text"
                                    value={formData.name}
                                    onChange={(e) => setFormData({...formData, name: e.target.value})}
                                    className="w-full px-6 py-4 bg-gray-50 border-none rounded-2xl focus:ring-2 focus:ring-[#5B0019] transition-all font-bold"
                                    placeholder="VD: Nguyễn Văn A"
                                />
                            </div>
                            <div className="space-y-2">
                                <label className="text-[10px] font-black text-gray-400 uppercase tracking-[0.2em] pl-2">Email</label>
                                <input 
                                    required
                                    type="email"
                                    value={formData.email}
                                    onChange={(e) => setFormData({...formData, email: e.target.value})}
                                    className="w-full px-6 py-4 bg-gray-50 border-none rounded-2xl focus:ring-2 focus:ring-[#5B0019] transition-all font-bold"
                                    placeholder="VD: example@gmail.com"
                                />
                            </div>
                            <div className="space-y-2">
                                <label className="text-[10px] font-black text-gray-400 uppercase tracking-[0.2em] pl-2">Mật khẩu</label>
                                <div className="relative">
                                    <input 
                                        required
                                        type={showPassword ? "text" : "password"}
                                        value={formData.password}
                                        onChange={(e) => setFormData({...formData, password: e.target.value})}
                                        className="w-full px-6 py-4 pr-14 bg-gray-50 border-none rounded-2xl focus:ring-2 focus:ring-[#5B0019] transition-all font-bold"
                                        placeholder="••••••••"
                                    />
                                    <button 
                                        type="button"
                                        onClick={() => setShowPassword(!showPassword)}
                                        className="absolute right-4 top-1/2 -translate-y-1/2 text-gray-400 hover:text-[#5B0019] transition-colors focus:outline-none p-1"
                                    >
                                        {showPassword ? <EyeOff size={20} /> : <Eye size={20} />}
                                    </button>
                                </div>
                            </div>
                            <div className="space-y-2">
                                <label className="text-[10px] font-black text-gray-400 uppercase tracking-[0.2em] pl-2">Vai trò</label>
                                <select 
                                    value={formData.role}
                                    onChange={(e) => setFormData({...formData, role: e.target.value})}
                                    className="w-full px-6 py-4 bg-gray-50 border-none rounded-2xl focus:ring-2 focus:ring-[#5B0019] transition-all font-bold"
                                >
                                    <option value="student">Học sinh</option>
                                    <option value="teacher">Giáo viên</option>
                                    <option value="admin">Quản trị viên (Admin)</option>
                                </select>
                            </div>

                            {formData.role === 'student' && (
                                <>
                                    <div className="space-y-2 animate-in slide-in-from-left-4 duration-300">
                                        <label className="text-[10px] font-black text-gray-400 uppercase tracking-[0.2em] pl-2">Khối</label>
                                        <input 
                                            required
                                            type="number"
                                            value={formData.grade}
                                            onChange={(e) => setFormData({...formData, grade: e.target.value})}
                                            className="w-full px-6 py-4 bg-gray-50 border-none rounded-2xl focus:ring-2 focus:ring-[#5B0019] transition-all font-bold"
                                            placeholder="VD: 10"
                                        />
                                    </div>
                                    <div className="space-y-2 animate-in slide-in-from-left-4 duration-300">
                                        <label className="text-[10px] font-black text-gray-400 uppercase tracking-[0.2em] pl-2">Tên lớp</label>
                                        <input 
                                            required
                                            type="text"
                                            value={formData.class_name}
                                            onChange={(e) => setFormData({...formData, class_name: e.target.value})}
                                            className="w-full px-6 py-4 bg-gray-50 border-none rounded-2xl focus:ring-2 focus:ring-[#5B0019] transition-all font-bold"
                                            placeholder="VD: 10A2"
                                        />
                                    </div>
                                </>
                            )}

                            <div className="md:col-span-2 pt-4">
                                <button 
                                    type="submit"
                                    disabled={loading}
                                    className="w-full bg-[#5B0019] text-white py-5 rounded-[1.5rem] font-black text-lg shadow-xl shadow-red-900/20 hover:scale-[1.02] active:scale-95 transition-all flex items-center justify-center gap-2"
                                >
                                    {loading ? <Loader2 className="animate-spin" /> : <Save size={24} />}
                                    Lưu tài khoản
                                </button>
                            </div>
                        </form>
                    </div>
                ) : (
                    <div className="p-10 flex flex-col items-center justify-center text-center space-y-10 min-h-[400px]">
                        <div className="space-y-4 max-w-lg">
                            <div className="bg-blue-50 text-blue-600 w-20 h-20 rounded-[2rem] flex items-center justify-center mx-auto mb-6">
                                <FileSpreadsheet size={40} />
                            </div>
                            <h2 className="text-2xl font-black text-gray-800">Nhập dữ liệu theo danh sách</h2>
                            <p className="text-gray-500 font-medium">Sử dụng file Excel hoặc CSV để tạo hàng loạt tài khoản một cách nhanh chóng.</p>
                        </div>

                        <div className="grid grid-cols-1 sm:grid-cols-2 gap-8 w-full max-w-2xl px-4">
                            {/* Student Template Selection */}
                            <div className="space-y-3">
                                <label className="text-[10px] font-black text-gray-400 uppercase tracking-[0.2em]">Mẫu cho Học sinh</label>
                                <div className="flex gap-2">
                                    <button 
                                        onClick={() => downloadTemplate('student', 'xlsx')}
                                        className="flex-1 flex items-center justify-center gap-2 px-4 py-3 border-2 border-gray-100 rounded-xl text-xs font-black text-gray-600 hover:border-green-500 hover:text-green-600 transition-all group"
                                    >
                                        <Download size={14} /> EXCEL
                                    </button>
                                    <button 
                                        onClick={() => downloadTemplate('student', 'csv')}
                                        className="flex-1 flex items-center justify-center gap-2 px-4 py-3 border-2 border-gray-100 rounded-xl text-xs font-black text-gray-600 hover:border-blue-500 hover:text-blue-600 transition-all group"
                                    >
                                        <FileCode size={14} /> CSV
                                    </button>
                                </div>
                            </div>

                            {/* Teacher Template Selection */}
                            <div className="space-y-3">
                                <label className="text-[10px] font-black text-gray-400 uppercase tracking-[0.2em]">Mẫu cho Giáo viên</label>
                                <div className="flex gap-2">
                                    <button 
                                        onClick={() => downloadTemplate('teacher', 'xlsx')}
                                        className="flex-1 flex items-center justify-center gap-2 px-4 py-3 border-2 border-gray-100 rounded-xl text-xs font-black text-gray-600 hover:border-green-500 hover:text-green-600 transition-all group"
                                    >
                                        <Download size={14} /> EXCEL
                                    </button>
                                    <button 
                                        onClick={() => downloadTemplate('teacher', 'csv')}
                                        className="flex-1 flex items-center justify-center gap-2 px-4 py-3 border-2 border-gray-100 rounded-xl text-xs font-black text-gray-600 hover:border-blue-500 hover:text-blue-600 transition-all group"
                                    >
                                        <FileCode size={14} /> CSV
                                    </button>
                                </div>
                            </div>
                        </div>

                        <label className="relative cursor-pointer group pt-4">
                             <input 
                                type="file" 
                                accept=".xlsx, .xls, .csv" 
                                onChange={handleBulkUpload}
                                className="hidden"
                                disabled={loading}
                             />
                             <div className="flex items-center gap-3 px-10 py-5 bg-[#5B0019] text-white rounded-[2rem] font-black text-lg shadow-xl shadow-red-900/20 group-hover:scale-105 transition-all">
                                {loading ? <Loader2 className="animate-spin" /> : <Upload size={24} />}
                                Tải file lên & Xử lý
                             </div>
                        </label>
                        
                        <p className="text-[10px] font-black text-gray-400 uppercase tracking-[0.2em]">
                            Định dạng hỗ trợ: .xlsx, .xls, .csv
                        </p>
                    </div>
                )}
            </div>
        </div>
    );
};

export default ManagementPage;
