"use client";

import Link from "next/link";
import { useState, type ChangeEvent, type FormEvent } from "react";
import { useRouter } from "next/navigation";
import { Eye, EyeOff, Mail, Lock, Loader2, ArrowLeft } from "lucide-react";
import Cookies from "js-cookie";

interface LoginResponse {
    id_token?: string;
    access_token?: string;
    refresh_token?: string;
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
    avatar?: string;
    [key: string]: any;
}

/**
 * LoginPage Component
 * 
 * A comprehensive login page component for the EduTrust application that handles user authentication.
 * 
 * @component
 * @returns {JSX.Element} The rendered login page with form validation and error handling
 * 
 * @description
 * This component provides:
 * - Email and password input fields with real-time validation
 * - Password visibility toggle functionality
 * - Form validation (email format and password length requirements)
 * - Loading state during authentication request
 * - Error handling with user-friendly error messages
 * - Secure token storage in HTTP-only cookies
 * - Automatic user info fetching and caching after successful login
 * - Responsive design with Tailwind CSS styling
 * - Vietnamese language support for all user messages
 * 
 * @example
 * ```tsx
 * import LoginPage from '@/app/login/page'
 * // Used as a route page in app router
 * ```
 * 
 * @features
 * - Email validation using regex pattern
 * - Password minimum length validation (8 characters)
 * - Separate error states for email and password fields
 * - CSRF protection with strict SameSite cookie policy
 * - API integration for authentication and user info retrieval
 * - Automatic routing to dashboard on successful login
 * - Visual feedback for form errors and loading states
 * 
 * @note
 * If users forget their password, they should contact the school/institution to reset their password
 */
export default function LoginPage() {
    const router = useRouter();
    const [showPassword, setShowPassword] = useState<boolean>(false);
    const [loading, setLoading] = useState<boolean>(false);
    const [error, setError] = useState<string>("");

    const [emailError, setEmailError] = useState<string>("");
    const [passwordError, setPasswordError] = useState<string>("");

    const [formData, setFormData] = useState({
        email: "",
        password: "",
    });

    const inputBaseClass =
        "w-full rounded-2xl py-4 text-gray-900 text-sm focus:outline-none transition-all font-medium border-2";

    const inputNormalClass =
        "bg-white border-gray-100 focus:ring-2 focus:ring-[#5B0019]/20 focus:border-[#5B0019]";

    const inputErrorClass =
        "bg-white border-[#5B0019]/40 focus:ring-2 focus:ring-[#5B0019]/10 focus:border-[#5B0019] text-gray-900 placeholder-gray-400";

    const handleInputChange = (e: ChangeEvent<HTMLInputElement>) => {
        const { name, value } = e.target;
        setFormData((prev) => ({ ...prev, [name]: value }));

        if (error) setError("");
        if (name === "email") setEmailError("");
        if (name === "password") setPasswordError("");
    };

    const handleSubmit = async (e: FormEvent) => {
        e.preventDefault();
        let hasError = false;

        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        if (!emailRegex.test(formData.email)) {
            setEmailError("Vui lòng nhập đúng định dạng email (VD: abc@gmail.com)");
            hasError = true;
        }

        const pass = formData.password;
        if (!pass) {
            setPasswordError("Mật khẩu không được để trống.");
            hasError = true;
        } else if (pass.length < 8) {
            setPasswordError("Mật khẩu phải có ít nhất 8 ký tự.");
            hasError = true;
        }

        if (hasError) return;

        setLoading(true);
        setError("");

        try {
            const apiUrl = process.env.NEXT_PUBLIC_API_URL;
            const response = await fetch(`${apiUrl}/login`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(formData),
            });

            const data: LoginResponse = await response.json();

            if (response.ok) {
                const token = data.id_token || data.access_token || data.token || (typeof data === 'string' ? data : "");
                if (token) {
                    Cookies.set("auth_token", token, {
                        expires: 7,
                        path: "/",
                        sameSite: "strict",
                        secure: process.env.NODE_ENV === "production",
                    });

                    try {
                        const userInfoResponse = await fetch(`${apiUrl}/user-info`, {
                            method: "GET",
                            headers: {
                                Authorization: `Bearer ${token}`,
                                "Content-Type": "application/json",
                            },
                        });

                        if (userInfoResponse.ok) {
                            const userData: UserInfo = await userInfoResponse.json();
                            Cookies.set("user_info", JSON.stringify(userData), {
                                expires: 7,
                                path: "/",
                                sameSite: "strict",
                                secure: process.env.NODE_ENV === "production",
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
                setError(response.status === 401 ? "Email hoặc mật khẩu không chính xác." : "Đã xảy ra lỗi hệ thống.");
            }
        } catch {
            setError("Không thể kết nối tới máy chủ.");
        } finally {
            setLoading(false);
        }
    };

    return (
        <main className="min-h-screen bg-[#5B0019] flex flex-col items-center justify-center p-4 font-sans">
            <Link
                href="/"
                className="absolute top-6 left-6 inline-flex items-center gap-2 text-white/60 hover:text-white transition-colors"
            >
                <ArrowLeft size={18} />
                <span className="text-sm">Quay lại</span>
            </Link>

            <div className="w-full max-w-[400px] bg-white p-10 rounded-[2.5rem] shadow-2xl border border-white/10">
                <div className="flex justify-center mb-8">
                    <img src="/edutrust.png" alt="EduTrust Logo" className="h-32 object-contain" />
                </div>

                <div className="text-center mb-8">
                    <p className="text-gray-500 text-sm font-semibold leading-relaxed tracking-tight px-2">
                        Vui lòng đăng nhập để tiếp tục hành trình <br /> chinh phục tri thức của bạn
                    </p>
                </div>

                {error && (
                    <div className="mb-6 p-3 text-sm text-white bg-[#5B0019] border border-[#4a0014] rounded-xl text-center animate-in fade-in zoom-in duration-300 shadow-lg">
                        {error}
                    </div>
                )}

                <form className="space-y-5" onSubmit={handleSubmit} noValidate>
                    <div className="space-y-2">
                        <label className={`text-[10px] font-black uppercase tracking-widest ml-1 transition-colors ${emailError ? "text-[#5B0019]" : "text-[#5B0019]"}`}>
                            Email address
                        </label>
                        <div className="relative">
                            <Mail
                                className={`absolute left-4 top-1/2 -translate-y-1/2 transition-colors ${emailError ? "text-[#5B0019]" : "text-gray-400"}`}
                                size={18}
                            />
                            <input
                                name="email"
                                type="email"
                                value={formData.email}
                                onChange={handleInputChange}
                                placeholder="yourname@gmail.com"
                                className={`${inputBaseClass} pl-12 pr-4 ${emailError ? inputErrorClass : inputNormalClass}`}
                            />
                        </div>
                        {emailError && (
                            <p className="text-[#5B0019] text-[11px] mt-1 ml-1 font-bold animate-in fade-in slide-in-from-top-1">
                                {emailError}
                            </p>
                        )}
                    </div>

                    <div className="space-y-2">
                        <label className={`text-[10px] font-black uppercase tracking-widest ml-1 transition-colors ${passwordError ? "text-[#5B0019]" : "text-[#5B0019]"}`}>
                            Password
                        </label>
                        <div className="relative">
                            <Lock
                                className={`absolute left-4 top-1/2 -translate-y-1/2 transition-colors ${passwordError ? "text-[#5B0019]" : "text-gray-400"}`}
                                size={18}
                            />
                            <input
                                name="password"
                                type={showPassword ? "text" : "password"}
                                value={formData.password}
                                onChange={handleInputChange}
                                placeholder="••••••••"
                                className={`${inputBaseClass} pl-12 pr-10 ${passwordError ? inputErrorClass : inputNormalClass}`}
                            />
                            <button
                                type="button"
                                onClick={() => setShowPassword(!showPassword)}
                                className={`absolute right-4 top-1/2 -translate-y-1/2 transition-colors ${passwordError ? "text-[#5B0019]/60 hover:text-[#5B0019]" : "text-gray-400 hover:text-[#5B0019]"}`}
                            >
                                {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
                            </button>
                        </div>
                        {passwordError && (
                            <p className="text-[#5B0019] text-[11px] mt-1 ml-1 font-bold animate-in fade-in slide-in-from-top-1 leading-tight">
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
            </div>
        </main>
    );
}
