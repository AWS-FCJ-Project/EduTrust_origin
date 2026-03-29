"use client"; // Required for menu toggle state
import { useState } from "react";
import Image from "next/image";
import { Moon, Megaphone, CalendarCheck, Search, Menu, X } from 'lucide-react';

export default function Header() {
    const [isMenuOpen, setIsMenuOpen] = useState(false);

    return (
        <header className="w-full border-b flex items-stretch sticky top-0 bg-white z-50">
            {/* Logo - Scaled down on mobile */}
            <div className="flex items-center justify-center p-2 md:p-0">
                <Image
                    src="/logo.png"
                    alt="Logo"
                    width={100}
                    height={100}
                    className="object-contain md:w-30"
                />
            </div>

            <div className="flex flex-col flex-1">
                <div className="h-10 md:h-12.5 bg-[#5B0019] flex items-center justify-between px-4">
                    <span className="text-white text-[10px] md:text-xs font-light italic hidden sm:block">
                        • <strong><em>NỀN TẢNG CỦA SỰ XUẤT SẮC & LÒNG TRUNG THỰC</em></strong>
                    </span>


                    <div className="flex md:hidden items-center gap-4 ml-auto">
                        <Search size={18} className="text-white" />
                        <button onClick={() => setIsMenuOpen(!isMenuOpen)} className="text-white">
                            {isMenuOpen ? <X size={24} /> : <Menu size={24} />}
                        </button>
                    </div>
                    <div className="hidden md:flex h-full items-stretch">
                        <div className="group flex items-center hover:bg-[#8a0028] transition-all duration-300 px-3 cursor-pointer border-l border-[#4a0014]">
                            <Megaphone size={18} className="text-white" />
                            <span className="max-w-0 overflow-hidden whitespace-nowrap text-white text-[11px] font-bold uppercase transition-all duration-300 group-hover:max-w-37.5 group-hover:ml-2">
                                Tin tức
                            </span>
                        </div>
                        <div className="group flex items-center hover:bg-[#8a0028] transition-all duration-300 px-3 cursor-pointer border-l border-[#4a0014]">
                            <CalendarCheck size={18} className="text-white" />
                            <span className="max-w-0 overflow-hidden whitespace-nowrap text-white text-[11px] font-bold uppercase transition-all duration-300 group-hover:max-w-37.5 group-hover:ml-2">
                                Lịch
                            </span>
                        </div>
                        <div className="group flex items-center hover:bg-[#8a0028] transition-all duration-300 px-3 cursor-pointer border-l border-[#4a0014]">
                            <Moon size={18} className="text-white" />
                            <span className="max-w-0 overflow-hidden whitespace-nowrap text-white text-[11px] font-bold uppercase transition-all duration-300 group-hover:max-w-37.5 group-hover:ml-2">
                                Chế độ tối
                            </span>
                        </div>
                        <div className="flex items-center gap-4 px-4 border-l border-[#4a0014]">
                            <button className="text-white text-xs hover:text-gray-300 cursor-pointer">Hỗ trợ</button>
                            <button className="text-white text-xs hover:text-gray-300 cursor-pointer">Thông báo</button>
                            <Search size={18} className="text-white cursor-pointer hover:text-gray-300" />
                        </div>
                    </div>
                </div>

                <div className="h-12.5 md:h-17.5 bg-white flex items-center px-4 justify-between">
                    <nav className="hidden md:flex gap-6 font-bold text-[#5B0019] text-sm uppercase">
                        <a href="#" className="hover:text-red-700">Về chúng tôi</a>
                        <a href="#" className="hover:text-red-700">Tuyển sinh</a>
                        <a href="#" className="hover:text-red-700">Đào tạo</a>
                        <a href="#" className="hover:text-red-700">Văn hóa</a>
                        <a href="#" className="hover:text-red-700">Nghệ thuật</a>
                        <a href="#" className="hover:text-red-700">Liên hệ</a>
                    </nav>
                    <div className="flex items-center ml-auto md:ml-0">
                        <a
                            href="/login"
                            className="px-4 py-1.5 md:px-6 md:py-2 border-2 border-[#5B0019] bg-white text-[#5B0019] text-[12px] md:text-sm font-bold uppercase rounded hover:bg-[#5B0019] hover:text-white transition-all"
                        >
                            Đăng nhập
                        </a>
                    </div>
                </div>
            </div>
            {
                isMenuOpen && (
                    <div className="absolute top-22.5 left-0 w-full bg-[#5B0019] text-white flex flex-col p-4 gap-4 md:hidden animate-in slide-in-from-top">
                        <div className="flex items-center gap-3 border-b border-white/20 pb-2">
                            <Megaphone size={20} /> <span>Tin tức</span>
                        </div>
                        <div className="flex items-center gap-3 border-b border-white/20 pb-2">
                            <CalendarCheck size={20} /> <span>Lịch</span>
                        </div>
                        <div className="flex items-center gap-3 border-b border-white/20 pb-2">
                            <Moon size={20} /> <span>Chế độ tối</span>
                        </div>
                        <div className="flex flex-col gap-2 pt-2">
                            <a href="#" className="uppercase font-bold">Về chúng tôi</a>
                            <a href="#" className="uppercase font-bold">Tuyển sinh</a>
                            <a href="#" className="uppercase font-bold">Đào tạo</a>
                            <a href="#" className="uppercase font-bold">Văn hóa</a>
                            <a href="#" className="uppercase font-bold">Nghệ thuật</a>
                        </div>
                    </div>
                )
            }
        </header >
    );
}