"use client";

import { useRef, useState } from "react";
import { Camera, Loader2 } from "lucide-react";
import { uploadAvatar } from "@/lib/avatar-service";

interface AvatarPickerProps {
    currentAvatar?: string | null;
    userName?: string;
    size?: "sm" | "md" | "lg";
    onAvatarUpdate?: (newAvatarUrl: string) => void;
}

export function AvatarPicker({
    currentAvatar,
    userName,
    size = "md",
    onAvatarUpdate,
}: AvatarPickerProps) {
    const inputRef = useRef<HTMLInputElement>(null);
    const [uploading, setUploading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const sizeClasses = {
        sm: "w-8 h-8",
        md: "w-10 h-10",
        lg: "w-16 h-16",
    };

    const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0];
        if (!file) return;

        // Validate file type
        if (!file.type.startsWith("image/")) {
            setError("Vui lòng chọn file hình ảnh.");
            return;
        }

        // Validate file size (max 5MB)
        if (file.size > 5 * 1024 * 1024) {
            setError("Kích thước file không được vượt quá 5MB.");
            return;
        }

        setUploading(true);
        setError(null);

        try {
            const avatarUrl = await uploadAvatar(file);
            if (avatarUrl) {
                onAvatarUpdate?.(avatarUrl);
            } else {
                setError("Tải lên thất bại. Vui lòng thử lại.");
            }
        } catch {
            setError("Đã xảy ra lỗi khi tải lên.");
        } finally {
            setUploading(false);
            // Reset input
            if (inputRef.current) inputRef.current.value = "";
        }
    };

    return (
        <div className="flex flex-col items-center gap-2">
            <div
                className={`${sizeClasses[size]} rounded-full relative overflow-hidden bg-slate-200 cursor-pointer group`}
                onClick={() => !uploading && inputRef.current?.click()}
            >
                {uploading ? (
                    <div className="absolute inset-0 flex items-center justify-center bg-slate-200">
                        <Loader2 size={size === "lg" ? 24 : 16} className="animate-spin text-slate-500" />
                    </div>
                ) : currentAvatar ? (
                    // eslint-disable-next-line @next/next/no-img-element
                    <img src={currentAvatar} alt="Avatar" className="object-cover w-full h-full" />
                ) : (
                    <div className="absolute inset-0 flex items-center justify-center bg-slate-300">
                        <span className="text-slate-600 font-medium text-xs">
                            {userName ? userName.charAt(0).toUpperCase() : "?"}
                        </span>
                    </div>
                )}

                {/* Hover overlay */}
                <div className="absolute inset-0 bg-black/40 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center">
                    <Camera size={size === "lg" ? 20 : 14} className="text-white" />
                </div>
            </div>

            <input
                ref={inputRef}
                type="file"
                accept="image/*"
                className="hidden"
                onChange={handleFileChange}
            />

            {error && (
                <p className="text-xs text-red-500 text-center">{error}</p>
            )}
        </div>
    );
}