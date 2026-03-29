"use client";

import React from 'react';
import {
    Plus, Search, Filter,
    Calendar, CheckCircle2, Clock,
    FileText, Download, Edit3, Trash2
} from 'lucide-react';

const TeacherAssignments = () => {
    // Sample teacher assignments mock data
    const teacherAssignments = [
        {
            id: 1,
            title: "Kiểm tra 15p - Giải tích 12",
            className: "12A1",
            subject: "Toán học",
            deadline: "20/03/2026 - 17:00",
            submitted: 28,
            total: 32,
            status: "active"
        },
        {
            id: 2,
            title: "Nghị luận xã hội: Ý chí con người",
            className: "12A2",
            subject: "Ngữ văn",
            deadline: "22/03/2026 - 08:00",
            submitted: 15,
            total: 35,
            status: "active"
        },
        {
            id: 3,
            title: "Trắc nghiệm Unit 9",
            className: "12A1",
            subject: "Tiếng Anh",
            deadline: "15/03/2026",
            submitted: 32,
            total: 32,
            status: "closed"
        }
    ];

    return (
        <div className="p-8 bg-[#F0F2F5] min-h-screen">
            {/* Header Section */}
            <div className="flex flex-col md:flex-row justify-between items-start md:items-center mb-8 gap-4">
                <div>
                    <h1 className="text-2xl font-bold text-gray-800">Quản lý bài tập</h1>
                    <p className="text-sm text-gray-500">Tạo mới và theo dõi tiến độ nộp bài của học sinh</p>
                </div>

                <button className="flex items-center gap-2 bg-[#5B0019] text-white px-6 py-3 rounded-xl font-bold shadow-lg shadow-red-900/20 hover:bg-[#7a0022] transition-all active:scale-95">
                    <Plus size={20} />
                    Tạo bài tập mới
                </button>
            </div>

            {/* Filter & Search Bar */}
            <div className="bg-white p-4 rounded-2xl shadow-sm border border-gray-100 mb-6 flex flex-col md:flex-row gap-4 justify-between">
                <div className="flex items-center gap-3 overflow-x-auto pb-2 md:pb-0">
                    <button className="px-4 py-2 rounded-lg bg-gray-100 text-gray-600 text-sm font-bold hover:bg-gray-200 transition-colors">Tất cả</button>
                    <button className="px-4 py-2 rounded-lg text-gray-500 text-sm font-bold hover:bg-gray-100 transition-colors">Đang mở</button>
                    <button className="px-4 py-2 rounded-lg text-gray-500 text-sm font-bold hover:bg-gray-100 transition-colors">Đã đóng</button>
                </div>

                <div className="flex gap-2">
                    <div className="relative">
                        <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" size={18} />
                        <input
                            type="text"
                            placeholder="Tìm kiếm bài tập..."
                            className="pl-10 pr-4 py-2 bg-gray-50 border-none rounded-xl text-sm focus:ring-2 focus:ring-[#5B0019]/20 w-full md:w-64"
                        />
                    </div>
                    <button className="p-2 border border-gray-100 rounded-xl hover:bg-gray-50">
                        <Filter size={20} className="text-gray-500" />
                    </button>
                </div>
            </div>

            {/* Assignments Table/Grid */}
            <div className="bg-white rounded-3xl shadow-sm border border-gray-100 overflow-hidden">
                <table className="w-full text-left border-collapse">
                    <thead className="bg-gray-50 border-b border-gray-100">
                        <tr>
                            <th className="p-5 text-xs font-bold text-gray-400 uppercase tracking-wider">Tên bài tập & Lớp</th>
                            <th className="p-5 text-xs font-bold text-gray-400 uppercase tracking-wider">Hạn nộp</th>
                            <th className="p-5 text-xs font-bold text-gray-400 uppercase tracking-wider">Thống kê nộp bài</th>
                            <th className="p-5 text-xs font-bold text-gray-400 uppercase tracking-wider">Trạng thái</th>
                            <th className="p-5 text-xs font-bold text-gray-400 uppercase tracking-wider text-center">Thao tác</th>
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-50">
                        {teacherAssignments.map((item) => (
                            <tr key={item.id} className="hover:bg-gray-50/50 transition-colors group">
                                <td className="p-5">
                                    <div className="flex items-center gap-4">
                                        <div className="w-10 h-10 rounded-lg bg-[#f5e6ed] flex items-center justify-center shrink-0">
                                            <FileText className="text-[#5B0019]" size={20} />
                                        </div>
                                        <div>
                                            <p className="font-bold text-gray-800 group-hover:text-[#5B0019] transition-colors">{item.title}</p>
                                            <div className="flex items-center gap-2 mt-1">
                                                <span className="text-[10px] font-bold bg-blue-50 text-blue-600 px-2 py-0.5 rounded uppercase">{item.className}</span>
                                                <span className="text-[10px] text-gray-400 font-medium">{item.subject}</span>
                                            </div>
                                        </div>
                                    </div>
                                </td>
                                <td className="p-5">
                                    <div className="flex items-center gap-2 text-sm text-gray-600 font-medium">
                                        <Calendar size={14} className="text-gray-400" />
                                        {item.deadline}
                                    </div>
                                </td>
                                <td className="p-5">
                                    <div className="w-full max-w-37.5]">
                                        <div className="flex justify-between items-center mb-1.5">
                                            <span className="text-xs font-bold text-gray-700">{item.submitted}/{item.total} học sinh</span>
                                            <span className="text-[10px] font-bold text-[#5B0019]">{Math.round((item.submitted / item.total) * 100)}%</span>
                                        </div>
                                        <div className="w-full bg-gray-100 h-1.5 rounded-full overflow-hidden">
                                            <div
                                                className="bg-[#5B0019] h-full transition-all duration-500"
                                                style={{ width: `${(item.submitted / item.total) * 100}%` }}
                                            ></div>
                                        </div>
                                    </div>
                                </td>
                                <td className="p-5">
                                    {item.status === 'active' ? (
                                        <span className="inline-flex items-center gap-1 text-green-600 bg-green-50 px-2.5 py-1 rounded-full text-[11px] font-bold">
                                            <CheckCircle2 size={12} /> Đang mở
                                        </span>
                                    ) : (
                                        <span className="inline-flex items-center gap-1 text-gray-400 bg-gray-50 px-2.5 py-1 rounded-full text-[11px] font-bold">
                                            <Clock size={12} /> Đã đóng
                                        </span>
                                    )}
                                </td>
                                <td className="p-5">
                                    <div className="flex items-center justify-center gap-2">
                                        <button title="Sửa" className="p-2 text-gray-400 hover:text-blue-600 hover:bg-blue-50 rounded-lg transition-all">
                                            <Edit3 size={18} />
                                        </button>
                                        <button title="Tải xuống bài làm" className="p-2 text-gray-400 hover:text-green-600 hover:bg-green-50 rounded-lg transition-all">
                                            <Download size={18} />
                                        </button>
                                        <button title="Xóa" className="p-2 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition-all">
                                            <Trash2 size={18} />
                                        </button>
                                    </div>
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        </div>
    );
};

export default TeacherAssignments;
