"use client";

import React, { useEffect, useState } from 'react';
import { Users, Search, Edit2, Trash2, Shield, Loader2, X, Save, AlertCircle, Eye, EyeOff } from 'lucide-react';
import Cookies from 'js-cookie';

const StudentsPage = () => {
    const [students, setStudents] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);
    const [searchTerm, setSearchTerm] = useState('');
    const [error, setError] = useState<string | null>(null);
    const [visiblePasswords, setVisiblePasswords] = useState<Record<string, boolean>>({});
    
    // Edit Modal State
    const [editingStudent, setEditingStudent] = useState<any>(null);
    const [editForm, setEditForm] = useState({ name: '', class_name: '', grade: '', password: '' });

    const fetchStudents = async () => {
        try {
            setLoading(true);
            const token = Cookies.get('auth_token');
            const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/users/students`, {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            if (res.ok) {
                const data = await res.json();
                setStudents(data);
            } else {
                setError("Không thể tải danh sách học sinh");
            }
        } catch {
            setError("Lỗi kết nối máy chủ");
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchStudents();
    }, []);

    const togglePassword = (id: string) => {
        setVisiblePasswords(prev => ({ ...prev, [id]: !prev[id] }));
    };

    const handleDelete = async (id: string) => {
        if (!confirm("Bạn có chắc chắn muốn xóa học sinh này? Hành động này không thể hoàn tác.")) return;
        
        try {
            const token = Cookies.get('auth_token');
            const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/users/${id}`, {
                method: 'DELETE',
                headers: { 'Authorization': `Bearer ${token}` }
            });
            if (res.ok) {
                fetchStudents();
            } else {
                alert("Lỗi khi xóa học sinh");
            }
        } catch {
            alert("Lỗi kết nối");
        }
    };

    const handleEdit = (student: any) => {
        setEditingStudent(student);
        setEditForm({
            name: student.name || '',
            class_name: student.class_name || '',
            grade: student.grade || '',
            password: ''
        });
    };

    const handleUpdate = async (e: React.FormEvent) => {
        e.preventDefault();
        try {
            const token = Cookies.get('auth_token');
            const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/users/${editingStudent.id}`, {
                method: 'PATCH',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify({
                    name: editForm.name,
                    class_name: editForm.class_name,
                    grade: parseInt(editForm.grade.toString()),
                    password: editForm.password || undefined
                })
            });

            if (res.ok) {
                setEditingStudent(null);
                fetchStudents();
            } else {
                alert("Lỗi khi cập nhật thông tin");
            }
        } catch {
            alert("Lỗi kết nối");
        }
    };

    const filteredStudents = students.filter(s => 
        (s.name || "").toLowerCase().includes(searchTerm.toLowerCase()) || 
        (s.email || "").toLowerCase().includes(searchTerm.toLowerCase()) ||
        (s.class_name || "").toLowerCase().includes(searchTerm.toLowerCase())
    );

    if (loading) return (
        <div className="flex h-64 items-center justify-center">
            <Loader2 className="animate-spin text-[#5B0019]" size={40} />
        </div>
    );

    return (
        <div className="space-y-8 animate-in fade-in duration-700">
            <div className="flex flex-col gap-2">
                <h1 className="text-3xl font-black text-gray-900 tracking-tight">Quản lý Học sinh</h1>
                <p className="text-gray-500 font-medium tracking-wide border-l-4 border-[#5B0019] pl-3">
                    Danh sách toàn bộ học viên. Bạn có thể chỉnh sửa thông tin hoặc chuyển lớp tại đây.
                </p>
            </div>

            {error && (
                <div className="bg-red-50 border border-red-100 text-red-600 p-4 rounded-2xl flex items-center gap-3">
                    <AlertCircle size={20} />
                    <span className="font-bold">{error}</span>
                </div>
            )}

            {/* Search Bar */}
            <div className="relative group">
                <Search className="absolute left-6 top-1/2 -translate-y-1/2 text-gray-400 group-focus-within:text-[#5B0019] transition-colors" size={20} />
                <input 
                    type="text"
                    placeholder="Tìm kiếm học sinh theo tên, email hoặc lớp..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    className="w-full pl-14 pr-6 py-5 bg-white border-none rounded-[2rem] shadow-sm focus:ring-2 focus:ring-[#5B0019] transition-all font-bold text-gray-700"
                />
            </div>

            {/* Students Table */}
            <div className="bg-white rounded-[2.5rem] border border-gray-100 shadow-sm overflow-hidden">
                <table className="w-full text-left border-collapse">
                    <thead>
                        <tr className="bg-gray-50/50">
                            <th className="px-8 py-6 text-[10px] font-black text-gray-400 uppercase tracking-widest">Học viên</th>
                            <th className="px-8 py-6 text-[10px] font-black text-gray-400 uppercase tracking-widest">Email</th>
                            <th className="px-8 py-6 text-[10px] font-black text-gray-400 uppercase tracking-widest text-center">Khối</th>
                            <th className="px-8 py-6 text-[10px] font-black text-gray-400 uppercase tracking-widest text-center">Lớp</th>
                            <th className="px-8 py-6 text-[10px] font-black text-gray-400 uppercase tracking-widest text-center">Mật khẩu</th>
                            <th className="px-8 py-6 text-[10px] font-black text-gray-400 uppercase tracking-widest text-right">Thao tác</th>
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-50">
                        {filteredStudents.map((student) => (
                            <tr key={student.id} className="hover:bg-gray-50/50 transition-colors group">
                                <td className="px-8 py-6">
                                    <div className="flex items-center gap-3">
                                        <div className="w-10 h-10 rounded-full bg-[#5B0019]/5 text-[#5B0019] flex items-center justify-center font-black">
                                            {student.name?.charAt(0) || 'U'}
                                        </div>
                                        <span className="font-bold text-gray-800">{student.name || 'N/A'}</span>
                                    </div>
                                </td>
                                <td className="px-8 py-6 font-medium text-gray-500">{student.email}</td>
                                <td className="px-8 py-6 text-center">
                                    <span className="px-3 py-1 bg-blue-50 text-blue-600 rounded-lg font-black text-xs">
                                        Khối {student.grade || '?'}
                                    </span>
                                </td>
                                <td className="px-8 py-6 text-center">
                                    <span className="px-3 py-1 bg-green-50 text-green-600 rounded-lg font-black text-xs">
                                        {student.class_name || 'Chưa xếp'}
                                    </span>
                                </td>
                                <td className="px-8 py-6 text-center">
                                    <div className="flex items-center justify-center gap-2">
                                        <code className="px-2 py-1 bg-gray-100 text-gray-600 rounded font-mono text-xs min-w-[80px]">
                                            {visiblePasswords[student.id] ? (student.password_plain || 'N/A') : '********'}
                                        </code>
                                        <button 
                                            onClick={() => togglePassword(student.id)}
                                            className="p-1 text-gray-400 hover:text-[#5B0019] transition-colors"
                                        >
                                            {visiblePasswords[student.id] ? <EyeOff size={14} /> : <Eye size={14} />}
                                        </button>
                                    </div>
                                </td>
                                <td className="px-8 py-6 text-right">
                                    <div className="flex items-center justify-end gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                                        <button 
                                            onClick={() => handleEdit(student)}
                                            className="p-2 text-gray-400 hover:text-[#5B0019] transition-colors"
                                            title="Sửa thông tin"
                                        >
                                            <Edit2 size={18} />
                                        </button>
                                        <button 
                                            onClick={() => handleDelete(student.id)}
                                            className="p-2 text-gray-400 hover:text-red-600 transition-colors"
                                            title="Xóa học sinh"
                                        >
                                            <Trash2 size={18} />
                                        </button>
                                    </div>
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>

                {filteredStudents.length === 0 && (
                    <div className="py-20 flex flex-col items-center justify-center text-gray-400">
                        <Users size={48} className="opacity-10 mb-4" />
                        <p className="font-bold">Không tìm thấy học sinh nào</p>
                    </div>
                )}
            </div>

            {/* Edit Modal */}
            {editingStudent && (
                <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/40 backdrop-blur-sm animate-in fade-in duration-300">
                    <div className="bg-white w-full max-w-md rounded-[3rem] p-10 shadow-2xl space-y-8 animate-in zoom-in-95 duration-300">
                        <div className="flex items-center justify-between">
                            <div className="flex items-center gap-4">
                                <div className="bg-[#5B0019] p-3 rounded-2xl text-white"><Shield size={24} /></div>
                                <h2 className="text-2xl font-black text-gray-800">Chỉnh sửa Học sinh</h2>
                            </div>
                            <button onClick={() => setEditingStudent(null)} className="text-gray-400 hover:text-gray-600"><X size={24} /></button>
                        </div>

                        <form onSubmit={handleUpdate} className="space-y-6">
                            <div className="space-y-2">
                                <label className="text-[10px] font-black text-gray-400 uppercase tracking-widest pl-2">Họ và tên</label>
                                <input 
                                    required
                                    type="text"
                                    value={editForm.name}
                                    onChange={(e) => setEditForm({...editForm, name: e.target.value})}
                                    className="w-full px-6 py-4 bg-gray-50 border-none rounded-2xl focus:ring-2 focus:ring-[#5B0019] font-black transition-all"
                                />
                            </div>
                            <div className="grid grid-cols-2 gap-4">
                                <div className="space-y-2">
                                    <label className="text-[10px] font-black text-gray-400 uppercase tracking-widest pl-2">Khối</label>
                                    <input 
                                        required
                                        type="number"
                                        value={editForm.grade}
                                        onChange={(e) => setEditForm({...editForm, grade: e.target.value})}
                                        className="w-full px-6 py-4 bg-gray-50 border-none rounded-2xl focus:ring-2 focus:ring-[#5B0019] font-black transition-all"
                                    />
                                </div>
                                <div className="space-y-2">
                                    <label className="text-[10px] font-black text-gray-400 uppercase tracking-widest pl-2">Lớp</label>
                                    <input 
                                        required
                                        type="text"
                                        value={editForm.class_name}
                                        onChange={(e) => setEditForm({...editForm, class_name: e.target.value})}
                                        className="w-full px-6 py-4 bg-gray-50 border-none rounded-2xl focus:ring-2 focus:ring-[#5B0019] font-black transition-all"
                                    />
                                </div>
                            </div>

                            <div className="space-y-2">
                                <label className="text-[10px] font-black text-gray-400 uppercase tracking-widest pl-2">Mật khẩu mới (Để trống nếu không đổi)</label>
                                <input 
                                    type="text"
                                    placeholder="Nhập mật khẩu mới..."
                                    value={editForm.password}
                                    onChange={(e) => setEditForm({...editForm, password: e.target.value})}
                                    className="w-full px-6 py-4 bg-gray-50 border-none rounded-2xl focus:ring-2 focus:ring-[#5B0019] font-black transition-all"
                                />
                            </div>

                            <button 
                                type="submit"
                                className="w-full py-4 bg-[#5B0019] text-white rounded-2xl font-black shadow-lg shadow-red-900/20 hover:scale-[1.02] active:scale-95 transition-all flex items-center justify-center gap-2"
                            >
                                <Save size={20} /> Lưu thay đổi
                            </button>
                        </form>
                    </div>
                </div>
            )}
        </div>
    );
};

export default StudentsPage;
