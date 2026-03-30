"use client";
import {
    Facebook,
    Linkedin,
    Github,
    Twitter,
    Globe,
    Phone,
    Mail,
    ArrowRight
} from "lucide-react";
import Image from "next/image";

export default function Footer() {
    return (
        <footer className="w-full bg-[#111827] text-gray-400 font-sans pb-8">

            <div className="max-w-7xl mx-auto px-6 py-12">
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-10">

                    {/* Column 1 */}
                    <div className="flex flex-col items-center text-center">
                        <div className="flex items-center gap-2 mb-4">
                            <span className="text-white text-2xl font-bold tracking-tight">EDUTRUST</span>
                        </div>
                        <p className="text-[13px] leading-relaxed mb-4">
                            Nền tảng xây dựng niềm tin và chuẩn mực cho giáo dục hiện đại. Giải pháp kiểm định toàn diện.
                        </p>
                        <div className="flex justify-center gap-4">
                            <Facebook size={18} className="cursor-pointer hover:text-white transition-colors" />
                            <Linkedin size={18} className="cursor-pointer hover:text-white transition-colors" />
                            <Github size={18} className="cursor-pointer hover:text-white transition-colors" />
                            <Twitter size={18} className="cursor-pointer hover:text-white transition-colors" />
                        </div>
                    </div>

                    {/* Column 2 */}
                    <div className="flex flex-col items-center text-center">
                        <h3 className="text-white text-xs font-bold mb-5 uppercase tracking-wider">Về EduTrust</h3>
                        <ul className="space-y-3 text-[13px]">
                            <li><a href="#" className="hover:text-white transition-colors">Giới thiệu</a></li>
                            <li><a href="#" className="hover:text-white transition-colors">Sứ mệnh & Tầm nhìn</a></li>
                            <li><a href="#" className="hover:text-white transition-colors">Đôi ngũ</a></li>
                            <li><a href="#" className="hover:text-white transition-colors">Tuyển dụng</a></li>
                        </ul>
                    </div>

                    {/* Column 3 */}
                    <div className="flex flex-col items-center text-center">
                        <h3 className="text-white text-xs font-bold mb-5 uppercase tracking-wider">Nền tảng</h3>
                        <ul className="space-y-3 text-[13px]">
                            <li><a href="#" className="hover:text-white transition-colors">Hệ thống LMS</a></li>
                            <li><a href="#" className="hover:text-white transition-colors">Quản lý Học viên</a></li>
                            <li><a href="#" className="hover:text-white transition-colors">Đánh giá Kết quả</a></li>
                            <li><a href="#" className="hover:text-white transition-colors">Tự kiểm định</a></li>
                        </ul>
                    </div>

                    {/* Column 4 */}
                    <div className="flex flex-col items-center text-center">
                        <h3 className="text-white text-xs font-bold mb-5 uppercase tracking-wider">Hỗ trợ</h3>
                        <ul className="space-y-3 text-[13px]">
                            <li><a href="#" className="hover:text-white transition-colors">Trung tâm Trợ giúp</a></li>
                            <li><a href="#" className="hover:text-white transition-colors">Hướng dẫn Sử dụng</a></li>
                            <li><a href="#" className="hover:text-white transition-colors">Trạng thái Hệ thống</a></li>
                            <li><a href="#" className="hover:text-white transition-colors">Tài liệu API</a></li>
                        </ul>
                    </div>

                    {/* Column 5 */}
                    <div className="flex flex-col items-center text-center">
                        <h3 className="text-white text-xs font-bold mb-5 uppercase tracking-wider">Liên hệ</h3>
                        <div className="space-y-3 text-[13px] w-full">
                            <div className="flex items-center justify-center gap-3">
                                <Phone size={14} className="text-white/70" />
                                <span>206-368-3600</span>
                            </div>
                            <div className="flex items-center justify-center gap-3">
                                <Mail size={14} className="text-white/70" />
                                <span className="truncate">support@edutrust.vn</span>
                            </div>
                            <div className="pt-2 w-full max-w-[200px] mx-auto">
                                <div className="relative">
                                    <input
                                        type="email"
                                        placeholder="Nhập email của bạn"
                                        className="w-full bg-transparent border border-gray-600 rounded-full py-2 px-5 text-[11px] focus:outline-none focus:border-white transition-colors text-center"
                                    />
                                    <button className="absolute right-4 top-2 text-gray-400 hover:text-white">
                                        <ArrowRight size={16} />
                                    </button>
                                </div>
                            </div>
                        </div>
                    </div>

                </div>
            </div>

            {/* Bottom Crest Logo section - Centered */}
            <div className="flex justify-center mt-4 mb-2">
                <div className="relative w-24 h-24 md:w-28 md:h-28">
                    <Image
                        src="/edutrust.png"
                        alt="EduTrust Crest"
                        fill
                        className="object-contain opacity-90 hover:opacity-100 transition-opacity"
                    />
                </div>
            </div>

            {/* Copyright and Legal Section */}
            <div className="border-t border-gray-800/50 mt-4 pt-6">
                <div className="max-w-7xl mx-auto px-6 flex flex-col md:flex-row justify-between items-center gap-4 text-[10px] md:text-[11px] text-gray-500">
                    <div>
                        © 2026 EduTrust. All rights reserved. Nền tảng xây dựng niềm tin giáo dục.
                    </div>
                    <div className="flex items-center gap-6">
                        <a href="#" className="hover:text-white transition-colors">Điều khoản</a>
                        <a href="#" className="hover:text-white transition-colors">Bảo mật</a>
                        <div className="flex items-center gap-1.5 border border-gray-700 px-3 py-1 rounded-md hover:bg-gray-800 transition-all cursor-pointer">
                            <Globe size={11} />
                            <span>Tiếng Việt</span>
                        </div>
                    </div>
                </div>
            </div>
        </footer>
    );
}
