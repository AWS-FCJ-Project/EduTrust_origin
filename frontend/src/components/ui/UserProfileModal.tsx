import React, { useState, useRef } from 'react';
import { X, Upload, Loader2, Shield, Mail, BookOpen, GraduationCap } from 'lucide-react';
import Cookies from 'js-cookie';

import studyImg from '../../../public/study.png';

interface UserProfileModalProps {
    user: any;
    isOpen: boolean;
    onClose: () => void;
    onUpdate: (updatedUser: any) => void;
}

export default function UserProfileModal({ user, isOpen, onClose, onUpdate }: UserProfileModalProps) {
    const [avatarPreview, setAvatarPreview] = useState<string | null>(user?.avatar_url || null);
    const [isUploading, setIsUploading] = useState(false);
    const fileInputRef = useRef<HTMLInputElement>(null);

    const processFile = (file: File) => {
        // Convert to base64
        const reader = new FileReader();
        reader.onloadend = async () => {
            const base64String = reader.result as string;
            setAvatarPreview(base64String);

            setIsUploading(true);
            try {
                const token = Cookies.get('auth_token');
                if (!token) return;

                const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/users/${user.id || user._id}`, {
                    method: 'PATCH',
                    headers: {
                        'Authorization': `Bearer ${token}`,
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        base_64_url: base64String
                    })
                });

                if (response.ok) {
                    const updatedUserData = await response.json();
                    onUpdate(updatedUserData);
                    console.log("Avatar updated successfully!");
                } else {
                    let errorMsg = "Từ Server.";
                    try {
                        const errData = await response.json();
                        if (errData.detail) errorMsg = errData.detail;
                    } catch (e) {}
                    console.error("Failed to update avatar", errorMsg);
                    alert(`Cập nhật ảnh thất bại: ${errorMsg}`);
                    setAvatarPreview(user?.avatar_url || null);
                }
            } catch (error) {
                console.error("Error updating avatar:", error);
                alert("Đã có lỗi khi kết nối với máy chủ.");
                setAvatarPreview(user?.avatar_url || null);
            } finally {
                setIsUploading(false);
            }
        };
        reader.readAsDataURL(file);
    };

    React.useEffect(() => {
        if (!isOpen) return;

        const handlePaste = (e: ClipboardEvent) => {
            if (isUploading) return;
            const items = e.clipboardData?.items;
            if (!items) return;

            for (let i = 0; i < items.length; i++) {
                if (items[i].type.indexOf('image') !== -1) {
                    const file = items[i].getAsFile();
                    if (file) {
                        e.preventDefault();
                        processFile(file);
                        return; // Process only the first image
                    }
                }
            }
        };

        window.addEventListener('paste', handlePaste);
        return () => window.removeEventListener('paste', handlePaste);
    }, [isOpen, isUploading, user]);

    const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0];
        if (!file) return;
        processFile(file);
    };

    if (!isOpen) return null;

    const roleName = user?.role === 'admin' ? 'Quản trị viên' 
        : user?.role === 'teacher' ? 'Giáo viên' 
        : 'Học sinh';

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/50 backdrop-blur-sm transition-opacity">
            <div className="bg-white rounded-2xl shadow-xl w-full max-w-md overflow-hidden relative animate-in fade-in zoom-in-95 duration-200">
                <div className="bg-gradient-to-r from-[#5B0019] to-[#800028] h-32 relative">
                    <button 
                        onClick={onClose}
                        className="absolute top-4 right-4 p-2 bg-white/20 hover:bg-white/30 text-white rounded-full backdrop-blur-md transition-colors"
                    >
                        <X size={20} />
                    </button>
                </div>
                
                <div className="px-8 pb-8">
                    {/* Avatar Upload Section */}
                    <div className="relative -mt-16 flex flex-col items-center mb-6">
                        <div className="relative mb-4 cursor-pointer" onClick={() => fileInputRef.current?.click()} title="Nhấn hoặc Paste (Ctrl+V) để tải ảnh lên">
                            <div className="w-32 h-32 rounded-full border-4 border-white shadow-lg overflow-hidden bg-slate-100 relative">
                                <img 
                                    src={avatarPreview || (studyImg as any).src || studyImg} 
                                    alt="Avatar" 
                                    className="w-full h-full object-cover" 
                                    onError={(e: any) => {
                                        e.currentTarget.src = (studyImg as any).src || studyImg;
                                    }}
                                />
                                {isUploading && (
                                    <div className="absolute inset-0 bg-slate-900/50 flex items-center justify-center">
                                        <Loader2 className="w-8 h-8 text-white animate-spin" />
                                    </div>
                                )}
                            </div>
                            <button 
                                disabled={isUploading}
                                className="absolute bottom-0 right-0 p-2.5 bg-[#5B0019] text-white rounded-full shadow-md hover:bg-[#800028] transition-colors border-2 border-white"
                                title="Thay đổi ảnh đại diện (Tải lên)"
                            >
                                <Upload size={16} />
                            </button>
                            <input 
                                type="file" 
                                ref={fileInputRef} 
                                onChange={handleFileChange} 
                                accept="image/jpeg, image/png, image/webp" 
                                className="hidden" 
                            />
                        </div>
                    </div>

                    {/* User Information */}
                    <div className="text-center mb-6">
                        <h2 className="text-2xl font-bold text-slate-900">{user?.name || 'Người dùng'}</h2>
                        <div className="flex items-center justify-center gap-1.5 text-slate-500 mt-1 font-medium">
                            <Shield size={16} />
                            <span>{roleName}</span>
                        </div>
                    </div>

                    <div className="space-y-4">
                        <div className="flex items-center p-3 bg-slate-50 rounded-xl border border-slate-100">
                            <div className="w-10 h-10 rounded-full bg-blue-100 flex items-center justify-center text-blue-600 mr-4 shrink-0">
                                <Mail size={18} />
                            </div>
                            <div className="truncate">
                                <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Email</p>
                                <p className="text-slate-900 font-medium truncate">{user?.email}</p>
                            </div>
                        </div>

                        {user?.role === 'student' && (
                            <>
                                <div className="flex items-center p-3 bg-slate-50 rounded-xl border border-slate-100">
                                    <div className="w-10 h-10 rounded-full bg-purple-100 flex items-center justify-center text-purple-600 mr-4 shrink-0">
                                        <BookOpen size={18} />
                                    </div>
                                    <div>
                                        <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Lớp</p>
                                        <p className="text-slate-900 font-medium">{user?.class_name || 'Chưa cập nhật'}</p>
                                    </div>
                                </div>
                                <div className="flex items-center p-3 bg-slate-50 rounded-xl border border-slate-100">
                                    <div className="w-10 h-10 rounded-full bg-emerald-100 flex items-center justify-center text-emerald-600 mr-4 shrink-0">
                                        <GraduationCap size={18} />
                                    </div>
                                    <div>
                                        <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Khối</p>
                                        <p className="text-slate-900 font-medium">{user?.grade ? `Khối ${user.grade}` : 'Chưa cập nhật'}</p>
                                    </div>
                                </div>
                            </>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
}
