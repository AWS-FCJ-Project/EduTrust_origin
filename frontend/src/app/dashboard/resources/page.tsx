"use client";

import React from 'react';
import { Folder } from 'lucide-react';

const TeacherResources: React.FC = () => {
    const folders = ['Bài giảng chương 1', 'Đề tham khảo 2024', 'Video thí nghiệm', 'Tài liệu bổ trợ'];

    return (
        <div className="p-8">
            <h1 className="text-2xl font-bold text-gray-800 mb-8">Kho Nội Dung</h1>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
                {folders.map((item, i) => (
                    <div key={i} className="bg-white p-6 rounded-[2rem] border border-gray-100 hover:border-[#5B0019] transition-all cursor-pointer group shadow-sm">
                        <div className="w-14 h-14 bg-red-50 rounded-2xl flex items-center justify-center text-[#5B0019] mb-4 group-hover:bg-[#5B0019] group-hover:text-white transition-all">
                            <Folder size={28} fill="currentColor" fillOpacity={0.1} />
                        </div>
                        <p className="font-bold text-sm text-gray-800 truncate">{item}</p>
                        <p className="text-[10px] text-gray-400 font-bold mt-1 uppercase">Cập nhật: 2 ngày trước</p>
                    </div>
                ))}
            </div>
        </div>
    );
};

export default TeacherResources;