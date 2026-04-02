"use client";

import Link from "next/link";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { Eye, EyeOff, Mail, Lock, Loader2, ArrowLeft } from "lucide-react";
import Cookies from "js-cookie";

interface LoginResponse {
    access_token?: string;
    token?: string;
    message?: string;
}

interface UserInfo {
    id?: string | number;
    name?: string;
    email?: string;
    role?: string;
    class_name?: string;
    grade?: string;
    [key: string]: any;
}

export default function LoginPage() {
    const router = useRouter();
    const [showPassword, setShowPassword] = useState<boolean>(false);
    const [loading, setLoading] = useState<boolean>(false);
    const [error, setError] = useState<string>("");

    const [emailError, setEmailError] = useState<string>("");
    const [passwordError, setPasswordError] = useState<string>("");

    const [formData, setFormData] = useState({
        email: "",
        password: ""
    });

    const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const { name, value } = e.target;
        setFormData(prev => ({ ...prev, [name]: value }));
        if (error) setError("");
        if (name === "email") setEmailError("");
        if (name === "password") setPasswordError(""); // Xóa lỗi pass khi đang nhập
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        let hasError = false;
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        if (!emailRegex.test(formData.email)) {
            setEmailError("Vui lòng nhập đúng định dạng email (VD: abc@gmail.com)");
            return;
        }

        const pass = formData.password;
        if (!pass) {
            setPasswordError("Mật khẩu không được để trống.");
            hasError = true;
        } else if (pass.length < 8) {
            setPasswordError("Mật khẩu phải có ít nhất 8 ký tự.");
            hasError = true;
        } else {
            const hasUpper = /[A-Z]/.test(pass);
            const hasLower = /[a-z]/.test(pass);
            const hasNumber = /\d/.test(pass);
            const hasSymbol = /[^\w\s]/.test(pass);

            if (!hasUpper || !hasLower || !hasNumber || !hasSymbol) {
                setPasswordError("Mật khẩu cần: 1 chữ hoa, 1 chữ thường, 1 số và 1 ký hiệu.");
                hasError = true;
            }
        }

        if (hasError) return;

        setLoading(true);
        setError("");

        try {
            const apiUrl = process.env.NEXT_PUBLIC_API_URL;

            const response = await fetch(`${apiUrl}/login`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify(formData),
            });

            const data: LoginResponse = await response.json();

            if (response.ok) {
                const token = data.access_token || data.token || (typeof data === 'string' ? data : "");

                if (token) {
                    Cookies.set("auth_token", token, {
                        expires: 7,
                        path: '/',
                        sameSite: 'strict',
                        secure: process.env.NODE_ENV === 'production'
                    });

                    // Fetch user info immediately after login
                    try {
                        const userInfoResponse = await fetch(`${apiUrl}/user-info`, {
                            method: "GET",
                            headers: {
                                "Authorization": `Bearer ${token}`,
                                "Content-Type": "application/json",
                            },
                        });

                        if (userInfoResponse.ok) {
                            const userData: UserInfo = await userInfoResponse.json();
                            Cookies.set("user_info", JSON.stringify(userData), {
                                expires: 7,
                                path: '/',
                                sameSite: 'strict',
                                secure: process.env.NODE_ENV === 'production'
                            });
                        }
                    } catch (userInfoError) {
                        console.error("Error fetching user info:", userInfoError);
                    }

                    router.push("/dashboard");
                    router.refresh();
                } else {
                    setError("Phản hồi từ máy chủ không hợp lệ.");
                }
            } else {
                if (response.status === 401) {
                    setError("Email hoặc mật khẩu không chính xác.");
                } else if (response.status === 422) {
                    setError("Định dạng Email không hợp lệ.");
                } else {
                    setError("Đã xảy ra lỗi hệ thống. Vui lòng thử lại sau.");
                }
            }
        } catch {
            setError("Không thể kết nối tới máy chủ. Vui lòng kiểm tra mạng.");
        } finally {
            setLoading(false);
        }
    };

    return (
        <main className="min-h-screen bg-[#5B0019] flex flex-col items-center justify-center p-4 font-sans">
            <Link
                href="/"
                className="absolute top-6 left-6 inline-flex items-center gap-2
                 text-gray-400 hover:text-white transition-colors"
            >
                <ArrowLeft size={18} />
                <span className="text-sm">Quay lại</span>
            </Link>

            <div className="w-full max-w-100 bg-white p-10 rounded-[2.5rem] shadow-2xl border border-white/10">

                <div className="flex justify-center mb-8">
                    <img
                        src="/edutrust.png"
                        alt="EduTrust Logo"
                        className="h-32 object-contain"
                    />
                </div>

                <div className="text-center mb-8">
                    <p className="text-gray-500 text-sm font-semibold leading-relaxed tracking-tight px-2">
                        Vui lòng đăng nhập để tiếp tục hành trình <br /> chinh phục tri thức của bạn
                    </p>
                </div>

                {error && (
                    <div className="mb-6 p-3 text-sm text-red-100 bg-red-500/20 border border-red-500/50 rounded-xl text-center animate-in fade-in zoom-in duration-300">
                        {error}
                    </div>
                )}

                <form className="space-y-5" onSubmit={handleSubmit}>
                    <div className="space-y-2">
                        <label className="text-[#5B0019] text-[10px] font-black uppercase tracking-widest ml-1">Email address</label>
                        <div className="relative">
                            <Mail className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400" size={18} />
                            <input
                                name="email"
                                type="email"
                                value={formData.email}
                                onChange={handleInputChange}
                                placeholder="yourname@gmail.com"
                                className={`w-full bg-[#111827] border rounded-xl py-3 pl-10 pr-4 text-white text-sm focus:outline-none transition-all ${emailError
                                    ? 'border-red-500 focus:ring-1 focus:ring-red-500'
                                    : 'border-gray-700 focus:border-[#5B0019] focus:ring-1 focus:ring-[#5B0019]'
                                    }`}
                                className="w-full bg-gray-50 border border-gray-100 rounded-2xl py-4 pl-12 pr-4 text-gray-900 text-sm focus:outline-none focus:ring-2 focus:ring-[#5B0019]/20 focus:border-[#5B0019] transition-all font-medium"
                            />
                        </div>
                        {emailError && (
                            <p className="text-red-400 text-[11px] mt-1 ml-1 animate-in fade-in slide-in-from-top-1">
                                {emailError}
                            </p>
                        )}
                    </div>

                    <div className="space-y-2">
                        <div className="flex justify-between items-center px-1">
                            <label className="text-[#5B0019] text-[10px] font-black uppercase tracking-widest">Password</label>
                        </div>
                        <div className="relative">
                            <Lock className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400" size={18} />
                            <input
                                name="password"
                                type={showPassword ? "text" : "password"}
                                value={formData.password}
                                onChange={handleInputChange}
                                placeholder="••••••••"
                                className={`w-full bg-[#111827] border rounded-xl py-3 pl-10 pr-10 text-white text-sm focus:outline-none transition-all ${passwordError
                                    ? 'border-red-500 focus:ring-1 focus:ring-red-500'
                                    : 'border-gray-700 focus:border-[#5B0019] focus:ring-1 focus:ring-[#5B0019]'
                                    }`}

                            />
                            <button
                                type="button"
                                onClick={() => setShowPassword(!showPassword)}
                                className="absolute right-4 top-1/2 -translate-y-1/2 text-gray-400 hover:text-[#5B0019] transition-colors"
                            >
                                {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
                            </button>
                        </div>
                        {passwordError && (
                            <p className="text-red-400 text-[11px] mt-1 ml-1 animate-in fade-in slide-in-from-top-1 leading-tight">
                                {passwordError}
                            </p>
                        )}
                    </div>

                    <button
                        type="submit"
                        disabled={loading}
                        className="w-full bg-[#5B0019] text-white font-black py-4 rounded-2xl transition-all duration-300 shadow-xl shadow-red-900/10 mt-6 hover:bg-black hover:scale-[1.02] active:scale-95 flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed uppercase tracking-widest text-xs"
                    >
                        {loading ? (
                            <>
                                <Loader2 size={18} className="animate-spin" />
                                <span>Đang xử lý...</span>
                            </>
                        ) : (
                            "Đăng nhập"
                        )}
                    </button>
                </form>

                <p className="text-center text-gray-400 text-[11px] font-black uppercase tracking-widest mt-10 leading-relaxed">
                    Đăng nhập chỉ dành cho nhà trường,<br /> giáo viên và học sinh
                </p>
            </div>
        </main>
    );
}
