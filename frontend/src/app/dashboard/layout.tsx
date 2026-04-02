"use client";
import { Sidebar } from '@/components/ui/sidebar';
import { Bell } from 'lucide-react';
import Image from 'next/image';
import study from '../../../public/study.png';
import { LogOut } from 'lucide-react';
import Cookies from 'js-cookie';
import { ThemeProvider } from '@/components/providers/ThemeProvider';

import { useEffect, useState, useRef } from 'react';
import { usePathname } from 'next/navigation';
import UserProfileModal from '@/components/ui/UserProfileModal';

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
    const [user, setUser] = useState<any>(null);
    const [isDropdownOpen, setIsDropdownOpen] = useState(false);
    const [isProfileModalOpen, setIsProfileModalOpen] = useState(false);
    const dropdownRef = useRef<HTMLDivElement>(null);
    const [loading, setLoading] = useState(true);
    const pathname = usePathname();
    const isChatPage = pathname?.startsWith('/dashboard/chat_ai');

    useEffect(() => {
        const fetchUserInfo = async () => {
            try {
                const token = Cookies.get('auth_token');
                if (!token) {
                    window.location.href = '/login';
                    return;
                }

                // Try to get cached user info from cookie first
                const cachedUserInfo = Cookies.get('user_info');
                if (cachedUserInfo) {
                    try {
                        const parsedUser = JSON.parse(cachedUserInfo);
                        setUser(parsedUser);
                        setLoading(false);
                        // Do not return here. Let it fetch fresh data to get the new S3 presigned url.
                    } catch {
                        // Invalid cached data, continue to fetch
                    }
                }

                // Fetch fresh user info from API
                const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/user-info`, {
                    headers: {
                        'Authorization': `Bearer ${token}`
                    }
                });

                if (response.ok) {
                    const data = await response.json();
                    setUser(data);
                    // Cache user info in cookie
                    Cookies.set('user_info', JSON.stringify(data), {
                        expires: 7,
                        path: '/',
                        sameSite: 'strict',
                        secure: process.env.NODE_ENV === 'production'
                    });
                } else {
                    Cookies.remove('auth_token');
                    Cookies.remove('user_info');
                    window.location.href = '/login';
                }
            } catch (error) {
                console.error("Error fetching user info:", error);
            } finally {
                setLoading(false);
            }
        };

        fetchUserInfo();
    }, []);

    useEffect(() => {
        const handleClickOutside = (event: MouseEvent) => {
            if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
                setIsDropdownOpen(false);
            }
        };
        document.addEventListener('mousedown', handleClickOutside);
        return () => document.removeEventListener('mousedown', handleClickOutside);
    }, []);

    if (loading) return <div className="flex h-screen w-full items-center justify-center bg-[#F0F2F5] text-sm font-medium text-slate-500">Đang tải...</div>;
    if (!user) return null;

    const role = user.role;
    const handleLogout = async () => {
        try {
            const token = Cookies.get('auth_token');

            await fetch(`${process.env.NEXT_PUBLIC_API_URL}/logout`, {
                method: 'POST',
                headers: {
                    'accept': 'application/json',
                    'Authorization': `Bearer ${token}`
                }
            });
        } catch (error) {
            console.error("Lỗi gọi API logout:", error);
        } finally {
            Cookies.remove('auth_token', { path: '/' });
            Cookies.remove('user_info', { path: '/', sameSite: 'strict', secure: process.env.NODE_ENV === 'production' });
            window.location.href = '/login';
        }
    };
    return (
        <>
            <script
                dangerouslySetInnerHTML={{
                    __html: `
                        (function() {
                            var theme = document.cookie.match(/chat_theme=(light|dark)/);
                            if (theme) {
                                document.documentElement.setAttribute('data-theme', theme[1]);
                            }
                        })();
                    `,
                }}
            />
            <div className="flex h-screen w-full bg-[#F0F2F5] overflow-hidden">
            <Sidebar role={role} />

            <main className="flex-1 flex flex-col min-w-0">
                <header className="h-16 bg-white/92 backdrop-blur-md flex items-center justify-between px-8 shadow-sm z-[90] shrink-0 relative">
                    <h2 className="text-[1.35rem] font-semibold tracking-[-0.04em] text-slate-900">
                        Chào {user.name || 'Người dùng'}! 👋
                    </h2>
                    <div className="flex items-center gap-6">
                        <button className="relative p-1"><Bell size={20} /></button>
                        <div className="flex items-center gap-3 border-l border-slate-200 pl-6" ref={dropdownRef}>
                            <p className="text-sm font-medium tracking-[-0.02em] text-slate-700">{user.name || 'Người dùng'}</p>
                            
                            <div className="relative">
                                <button 
                                    onClick={() => setIsDropdownOpen(!isDropdownOpen)}
                                    className="w-12 h-12 rounded-full relative overflow-hidden focus:outline-none ring-2 ring-transparent transition-all hover:ring-[#5B0019]/50"
                                >
                                    {user.avatar_url ? (
                                        <img 
                                            src={user.avatar_url} 
                                            alt="Avatar" 
                                            className="w-full h-full object-cover" 
                                        />
                                    ) : (
                                        <Image 
                                            src={study} 
                                            alt="Avatar" 
                                            fill 
                                            className="object-cover" 
                                        />
                                    )}
                                </button>

                                {isDropdownOpen && (
                                    <div className="absolute right-0 mt-3 w-56 bg-white rounded-xl shadow-lg border border-slate-100 overflow-hidden z-[100] animate-in fade-in slide-in-from-top-2 duration-150">
                                        <button 
                                            onClick={() => {
                                                setIsDropdownOpen(false);
                                                setIsProfileModalOpen(true);
                                            }}
                                            className="w-full text-left px-5 py-3.5 text-[15px] font-medium text-slate-700 hover:bg-slate-50 transition-colors border-b border-slate-100"
                                        >
                                            Thông tin cá nhân
                                        </button>
                                        <button
                                            onClick={handleLogout}
                                            className="w-full flex items-center gap-2.5 px-5 py-3.5 text-[15px] font-medium text-red-600 hover:bg-red-50 transition-colors"
                                        >
                                            <LogOut size={18} />
                                            <span>Đăng xuất</span>
                                        </button>
                                    </div>
                                )}
                            </div>
                        </div>
                    </div>
                </header>

                <UserProfileModal 
                    user={user} 
                    isOpen={isProfileModalOpen} 
                    onClose={() => setIsProfileModalOpen(false)}
                    onUpdate={(updatedUser) => {
                        setUser(updatedUser);
                        // Cập nhật cookie ngay khi upload ảnh thành công
                        Cookies.set('user_info', JSON.stringify(updatedUser), {
                            expires: 7,
                            path: '/',
                            sameSite: 'strict',
                            secure: process.env.NODE_ENV === 'production'
                        });
                    }}
                />

                <div
                    className={`flex-1 min-h-0 ${
                        isChatPage ? 'p-3 md:p-5 overflow-hidden' : 'p-4 md:p-8 overflow-y-auto custom-scrollbar'
                    }`}
                >
                    <ThemeProvider>
                        {children}
                    </ThemeProvider>
                </div>
            </main>
        </div>
        </>
    );
}
