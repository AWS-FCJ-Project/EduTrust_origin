"use client";

import { Trophy, Clock, ArrowRight, Loader2 } from 'lucide-react';
import Link from 'next/link';
import { MENU_CONFIG } from '@/lib/menu-constants';
import { useEffect, useState } from 'react';
import Cookies from 'js-cookie';

const DashboardCard = ({ label, icon, desc, path }: any) => (
    <Link href={path} className="group">
        <div className="bg-white rounded-2xl p-6 flex items-center gap-5 border border-transparent shadow-sm hover:shadow-xl hover:border-[#5B0019]/10 transition-all duration-300 h-full transform hover:-translate-y-1">
            <div className="p-4 rounded-2xl bg-[#5B0019] text-white group-hover:bg-[#8a0026] transition-all duration-500 shadow-sm">
                {icon}
            </div>
            <div className="min-w-0">
                <h3 className="font-bold text-gray-800 group-hover:text-[#5B0019] transition-colors truncate">
                    {label}
                </h3>
                <p className="text-[11px] text-gray-400 font-semibold mt-1 tracking-wider uppercase">
                    {desc}
                </p>
            </div>
        </div>
    </Link>
);

export default function DashboardPage() {
    const [user, setUser] = useState<any>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchUser = async () => {
            try {
                const token = Cookies.get('auth_token');
                if (!token) return;

                const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/user-info`, {
                    headers: { 'Authorization': `Bearer ${token}` }
                });
                if (response.ok) {
                    const data = await response.json();
                    setUser(data);
                }
            } catch (error) {
                console.error("Error:", error);
            } finally {
                setLoading(false);
            }
        };
        fetchUser();
    }, []);

    if (loading) return (
        <div className="flex h-64 items-center justify-center">
            <Loader2 className="animate-spin text-[#5B0019]" size={40} />
        </div>
    );

    const role = user?.role || 'student';
    const cards = (MENU_CONFIG as any)[role] || [];

    return (
        <div className="space-y-8">
            {role === 'student' && (
                <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                    <div className="lg:col-span-2 bg-white p-6 rounded-2xl shadow-sm border border-gray-100">
                        <div className="flex justify-between items-center mb-4">
                            <div>
                                <h3 className="font-bold text-gray-700">Tiến độ tuần này</h3>
                                <p className="text-xs text-gray-400 mt-1">Hoàn thành các mục tiêu học tập</p>
                            </div>
                            <span className="text-[#5B0019] font-black text-2xl">75%</span>
                        </div>

                        <div className="w-full bg-gray-100 h-4 rounded-full overflow-hidden">
                            <div
                                className="bg-[#5B0019] h-full rounded-full transition-all duration-1000 ease-out shadow-[0_0_10px_rgba(91,0,25,0.3)]"
                                style={{ width: '75%' }}
                            />
                        </div>

                        <div className="mt-6 flex items-center justify-between">
                            <div className="text-xs text-gray-500 flex items-center gap-2">
                                <Clock size={16} className="text-[#5B0019]" />
                                <span>Bạn còn <strong className="text-gray-800">2 bài tập</strong> cần nộp trước Chủ Nhật</span>
                            </div>
                            <Link href="/dashboard" className="text-xs font-bold text-[#5B0019] hover:underline flex items-center gap-1">
                                Xem chi tiết <ArrowRight size={12} />
                            </Link>
                        </div>
                    </div>

                    <div className="bg-linear-to-br from-[#5B0019] to-[#8a0026] p-6 rounded-2xl shadow-lg text-white flex flex-col justify-between group relative overflow-hidden">
                        <div className="relative z-10">
                            <div className="flex items-center justify-between">
                                <div className="flex items-center gap-3">
                                    <div className="bg-white/20 p-2 rounded-lg backdrop-blur-md">
                                        <Trophy size={20} className="group-hover:rotate-12 transition-transform" />
                                    </div>
                                    <h3 className="font-bold tracking-tight">Xếp hạng của bạn</h3>
                                </div>
                                <span className="text-[10px] bg-white/20 px-2 py-1 rounded font-bold backdrop-blur-md">TUẦN NÀY</span>
                            </div>
                            <div className="mt-6">
                                <p className="text-4xl font-black">Hạng 5</p>
                                <p className="text-xs opacity-80 uppercase font-bold tracking-widest mt-2">
                                    {role === 'student' ? `${user.class_name || 'Lớp học'} • Khối ${user.grade || ''}` : 'Toàn trường'}
                                </p>
                            </div>
                        </div>

                        <Link
                            href="/dashboard"
                            className="relative z-10 mt-6 block text-center text-xs bg-white text-[#5B0019] py-3 rounded-xl font-black hover:bg-gray-50 transition-all active:scale-95 shadow-md"
                        >
                            CHI TIẾT BẢNG ĐIỂM
                        </Link>

                        <div className="absolute -right-6 -bottom-6 w-32 h-32 bg-white/10 rounded-full blur-3xl group-hover:bg-white/20 transition-colors"></div>
                    </div>
                </div>
            )}

            <div>
                <h3 className="text-gray-500 font-bold text-xs uppercase tracking-[0.2em] mb-4 pl-1">
                    Lối tắt nhanh
                </h3>
                <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 gap-6">
                    {cards.map((card: any, index: number) => (
                        <DashboardCard key={index} {...card} />
                    ))}
                </div>
            </div>
        </div>
    );
}