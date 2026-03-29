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

export default function Footer() {
    return (
        <footer className="w-full bg-[#111827] text-gray-400 font-sans">

            <div className="max-w-7xl mx-auto px-6 py-16">
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-12">

                    <div className="lg:col-span-1">
                        <div className="flex items-center gap-2 mb-6">
                            <div className="bg-[#0D9488] p-1.5 rounded-lg">
                                <span className="text-white font-bold text-xl leading-none">ET</span>
                            </div>
                            <span className="text-white font-bold text-2xl tracking-tight">EDUTRUST</span>
                        </div>
                        <p className="text-sm leading-relaxed mb-6">
                            Nền tảng xây dựng niềm tin và chuẩn mực cho giáo dục hiện đại. Giải pháp kiểm định toàn diện.
                        </p>
                        <div className="flex gap-4">
                            <Facebook size={20} className="cursor-pointer hover:text-[#0D9488] transition-colors" />
                            <Linkedin size={20} className="cursor-pointer hover:text-[#0D9488] transition-colors" />
                            <Github size={20} className="cursor-pointer hover:text-[#0D9488] transition-colors" />
                            <Twitter size={20} className="cursor-pointer hover:text-[#0D9488] transition-colors" />
                        </div>
                    </div>

                    <div>
                        <h3 className="text-white font-bold text-sm mb-6 uppercase tracking-[0.1em]">Về EduTrust</h3>
                        <ul className="space-y-4 text-sm">
                            <li><a href="#" className="hover:text-white transition-colors">Giới thiệu</a></li>
                            <li><a href="#" className="hover:text-white transition-colors">Sứ mệnh & Tầm nhìn</a></li>
                            <li><a href="#" className="hover:text-white transition-colors">Đội ngũ</a></li>
                            <li><a href="#" className="hover:text-white transition-colors">Tuyển dụng</a></li>
                        </ul>
                    </div>
                    <div>
                        <h3 className="text-white font-bold text-sm mb-6 uppercase tracking-[0.1em]">Nền tảng</h3>
                        <ul className="space-y-4 text-sm">
                            <li><a href="#" className="hover:text-white transition-colors">Hệ thống LMS</a></li>
                            <li><a href="#" className="hover:text-white transition-colors">Quản lý Học viên</a></li>
                            <li><a href="#" className="hover:text-white transition-colors">Đánh giá Kết quả</a></li>
                            <li><a href="#" className="hover:text-white transition-colors">Tự kiểm định</a></li>
                        </ul>
                    </div>


                    <div>
                        <h3 className="text-white font-bold text-sm mb-6 uppercase tracking-[0.1em]">Hỗ trợ</h3>
                        <ul className="space-y-4 text-sm">
                            <li><a href="#" className="hover:text-white transition-colors">Trung tâm Trợ giúp</a></li>
                            <li><a href="#" className="hover:text-white transition-colors">Hướng dẫn Sử dụng</a></li>
                            <li><a href="#" className="hover:text-white transition-colors">Trạng thái Hệ thống</a></li>
                            <li><a href="#" className="hover:text-white transition-colors">Tài liệu API</a></li>
                        </ul>
                    </div>
                    <div>
                        <h3 className="text-white font-bold text-sm mb-6 uppercase tracking-[0.1em]">Liên hệ</h3>
                        <div className="space-y-4 text-sm">
                            <div className="flex items-center gap-3">
                                <Phone size={16} className="text-[#0D9488]" />
                                <span>206-368-3600</span>
                            </div>
                            <div className="flex items-center gap-3">
                                <Mail size={16} className="text-[#0D9488]" />
                                <span className="truncate">support@edutrust.vn</span>
                            </div>
                            <div className="pt-4">
                                <div className="relative">
                                    <input
                                        type="email"
                                        placeholder="Nhập email của bạn"
                                        className="w-full bg-[#1F2937] border border-gray-700 rounded-md py-2 px-3 text-xs focus:outline-none focus:border-[#0D9488] transition-colors"
                                    />
                                    <button className="absolute right-2 top-1.5 text-[#0D9488] hover:text-white">
                                        <ArrowRight size={18} />
                                    </button>
                                </div>
                            </div>
                        </div>
                    </div>

                </div>
            </div>

            <div className="border-t border-gray-800 bg-[#0F172A] py-8">
                <div className="max-w-7xl mx-auto px-6 flex flex-col md:flex-row justify-between items-center gap-4 text-[11px] md:text-xs">
                    <div className="text-gray-500">
                        © 2026 EduTrust. All rights reserved. Nền tảng xây dựng niềm tin giáo dục.
                    </div>
                    <div className="flex items-center gap-6">
                        <a href="#" className="hover:text-white transition-colors">Điều khoản</a>
                        <a href="#" className="hover:text-white transition-colors">Bảo mật</a>
                        <button className="flex items-center gap-1.5 border border-gray-700 px-3 py-1 rounded hover:bg-gray-800 transition-all">
                            <Globe size={12} />
                            <span>Tiếng Việt</span>
                        </button>
                    </div>
                </div>
            </div>
        </footer>
    );
}