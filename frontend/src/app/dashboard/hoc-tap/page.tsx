"use client";
import React, { useState } from 'react';
import Image from 'next/image';
import {
    Search, Filter, PlayCircle, Star,
    Clock, Bookmark, ChevronRight, BookOpen
} from 'lucide-react';

const StudentLibrary = () => {
    const [activeTab, setActiveTab] = useState('Tất cả');

    const categories = ['Tất cả', 'Toán học', 'Ngữ văn', 'Tiếng Anh', 'Hóa học', 'Vật lý',
        'Sinh học', 'Lịch sử', 'Địa lý', 'Giáo dục công dân', 'Tin học', 'Công nghệ'];

    const lessons = [
        {
            id: 1,
            title: 'Hóa học vô cơ: Chuyên đề Kim loại Kiềm và Kiềm Thổ',
            teacher: 'ThS. Nguyễn Văn A',
            duration: '45 phút',
            rating: 4.8,
            image: 'https://images.unsplash.com/photo-1532187875605-2fe3585114e5?auto=format&fit=crop&q=80&w=400',
            category: 'Hóa học',
            views: '1.2k'
        },
        {
            id: 2,
            title: 'Kỹ năng Viết bài Nghị luận Xã hội đạt điểm tối đa',
            teacher: 'Cô Lê Thị B',
            duration: '30 phút',
            rating: 5.0,
            image: 'https://images.unsplash.com/photo-1455390582262-044cdead277a?auto=format&fit=crop&q=80&w=400',
            category: 'Ngữ văn',
            views: '850'
        },
        {
            id: 3,
            title: 'Toán 12: Chinh phục Nguyên hàm và Tích phân',
            teacher: 'Thầy Trần C',
            duration: '60 phút',
            rating: 4.9,
            image: 'https://images.unsplash.com/photo-1509228468518-180dd48a5d5f?auto=format&fit=crop&q=80&w=400',
            category: 'Toán học',
            views: '2.5k'
        },
        {
            id: 4,
            title: 'English: Master 12 Tenses in 30 Minutes',
            teacher: 'Mr. John Wick',
            duration: '35 phút',
            rating: 4.7,
            image: 'https://images.unsplash.com/photo-1546410531-bb4caa19020a?auto=format&fit=crop&q=80&w=400',
            category: 'Tiếng Anh',
            views: '3.1k'
        }
    ];

    return (
        <div className="min-h-screen bg-[#FDFDFD] p-6 md:p-10 font-sans text-sm">
            <div className="max-w-7xl mx-auto">

                <div className="flex flex-col md:flex-row md:items-end justify-between gap-6 mb-12">
                    <div>
                        <h1 className="text-4xl font-black text-gray-900 tracking-tight mb-2">Thư viện Bài giảng</h1>
                        <p className="text-gray-500 font-medium">Khám phá lộ trình học tập được cá nhân hóa cho bạn.</p>
                    </div>

                    <div className="relative w-full md:w-100">
                        <input
                            type="text"
                            placeholder="Tìm kiếm khóa học, giáo viên..."
                            className="w-full pl-12 pr-4 py-4 bg-white rounded-3xl border border-gray-100 shadow-xl shadow-gray-100/50 focus:ring-2 focus:ring-[#5B0019]/10 transition-all outline-none"
                        />
                        <Search className="absolute left-5 top-1/2 -translate-y-1/2 text-gray-400" size={20} />
                    </div>
                </div>

                <div className="relative bg-[#5B0019] rounded-[3rem] p-10 text-white overflow-hidden mb-12 shadow-2xl shadow-red-900/20">
                    <div className="relative z-10 flex flex-col md:flex-row items-center justify-between gap-8">
                        <div className="flex items-center gap-6">
                            <div className="w-20 h-20 bg-white/10 rounded-[2rem] flex items-center justify-center backdrop-blur-xl border border-white/20">
                                <PlayCircle size={40} className="fill-white/20" />
                            </div>
                            <div>
                                <div className="flex items-center gap-2 mb-2">
                                    <span className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></span>
                                    <p className="text-red-200 text-[10px] font-black uppercase tracking-[0.2em]">Đang học dở</p>
                                </div>
                                <h2 className="text-2xl font-bold mb-3">Chương 4: Cacbon - Silic (Hóa 11)</h2>
                                <div className="flex items-center gap-4">
                                    <div className="w-48 h-1.5 bg-white/10 rounded-full overflow-hidden">
                                        <div className="w-[75%] h-full bg-white rounded-full"></div>
                                    </div>
                                    <span className="text-xs font-bold text-red-100">75%</span>
                                </div>
                            </div>
                        </div>
                        <button className="bg-white text-[#5B0019] px-8 py-4 rounded-2xl font-black hover:scale-105 transition-all flex items-center gap-3 shadow-lg">
                            Tiếp tục bài học <ChevronRight size={18} />
                        </button>
                    </div>
                    <div className="absolute -right-10 -bottom-10 w-64 h-64 bg-white/5 rounded-full blur-3xl"></div>
                    <div className="absolute left-1/2 top-0 w-96 h-96 bg-red-400/10 rounded-full blur-[100px]"></div>
                </div>

                <div className="flex items-center gap-3 mb-10 overflow-x-auto no-scrollbar pb-2">
                    <button className="p-3.5 bg-white rounded-2xl shadow-sm border border-gray-100 text-[#5B0019] hover:bg-gray-50 transition-colors">
                        <Filter size={20} />
                    </button>
                    {categories.map((cat) => (
                        <button
                            key={cat}
                            onClick={() => setActiveTab(cat)}
                            className={`px-8 py-3.5 rounded-2xl font-black whitespace-nowrap transition-all shadow-sm border ${activeTab === cat
                                ? 'bg-[#5B0019] text-white border-[#5B0019] shadow-lg shadow-red-900/20'
                                : 'bg-white text-gray-400 border-gray-50 hover:border-[#5B0019]/30 hover:text-[#5B0019]'
                                }`}
                        >
                            {cat}
                        </button>
                    ))}
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-8">
                    {lessons.map((lesson) => (
                        <div key={lesson.id} className="group bg-white rounded-[2.5rem] p-4 border border-gray-100 shadow-sm hover:shadow-2xl hover:shadow-gray-200/50 transition-all duration-500 flex flex-col cursor-pointer">

                            <div className="relative aspect-4/3 rounded-[2rem] overflow-hidden mb-6">
                                <Image
                                    src={lesson.image}
                                    alt={lesson.title}
                                    fill
                                    unoptimized
                                    sizes="(max-width: 768px) 100vw, 25vw"
                                    className="w-full h-full object-cover group-hover:scale-110 transition-transform duration-700"
                                />
                                <div className="absolute inset-0 bg-black/20 group-hover:bg-black/50 transition-colors flex items-center justify-center">
                                    <div className="w-14 h-14 bg-white/20 backdrop-blur-md rounded-full flex items-center justify-center text-white scale-0 group-hover:scale-100 transition-all duration-300 border border-white/30 shadow-2xl">
                                        <PlayCircle size={32} fill="currentColor" fillOpacity={0.3} />
                                    </div>
                                </div>
                                <div className="absolute top-4 left-4 bg-white/90 backdrop-blur-md px-4 py-1.5 rounded-xl text-[10px] font-black uppercase tracking-wider text-[#5B0019] shadow-sm">
                                    {lesson.category}
                                </div>
                                <button className="absolute top-4 right-4 p-2.5 bg-black/10 backdrop-blur-md text-white rounded-xl hover:bg-[#5B0019] transition-colors border border-white/20">
                                    <Bookmark size={18} />
                                </button>
                            </div>

                            <div className="px-2 flex flex-1 flex-col">
                                <h3 className="font-bold text-gray-900 leading-tight mb-2 group-hover:text-[#5B0019] transition-colors line-clamp-2 text-base">
                                    {lesson.title}
                                </h3>
                                <div className="flex items-center gap-2 mb-6">
                                    <div className="w-6 h-6 bg-gray-100 rounded-full flex items-center justify-center">
                                        <BookOpen size={12} className="text-[#5B0019]" />
                                    </div>
                                    <p className="text-xs text-gray-400 font-bold tracking-tight">{lesson.teacher}</p>
                                </div>

                                <div className="mt-auto pt-5 border-t border-gray-50 flex items-center justify-between">
                                    <div className="flex items-center gap-1.5">
                                        <div className="flex items-center text-[#FFB800]">
                                            <Star size={14} fill="currentColor" />
                                        </div>
                                        <span className="text-xs font-black text-gray-800">{lesson.rating}</span>
                                    </div>
                                    <div className="flex items-center gap-4 text-gray-400 font-bold text-[10px] uppercase tracking-wider">
                                        <span className="flex items-center gap-1.5">
                                            <Clock size={14} /> {lesson.duration}
                                        </span>
                                        <span>{lesson.views} views</span>
                                    </div>
                                </div>
                            </div>
                        </div>
                    ))}
                </div>

                <div className="mt-16 text-center">
                    <button className="px-10 py-4 bg-white border border-gray-100 rounded-2xl font-black text-[#5B0019] shadow-sm hover:shadow-md hover:bg-gray-50 transition-all">
                        Xem thêm bài giảng
                    </button>
                </div>
            </div>
        </div>
    );
};

export default StudentLibrary;
