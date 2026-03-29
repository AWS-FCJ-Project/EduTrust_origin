"use client";
import { useState } from 'react';
import { ChevronLeft, ChevronRight } from 'lucide-react';
import Image from 'next/image';
import Link from 'next/link';

// 1. Note: Ensure MENU_CONFIG is properly imported from constants
import { MENU_CONFIG } from '@/lib/menu-constants';
import logo from '../../../public/logo.png';

export const Sidebar = ({ role }: { role: 'student' | 'admin' }) => {
    const [isCollapsed, setIsCollapsed] = useState(false);

    // 2. Map DASHBOARD_CONFIG to MENU_CONFIG
    const menuItems = MENU_CONFIG[role] || [];

    return (
        <aside className={`transition-all duration-300 bg-[#5B0019] text-white py-6 relative flex flex-col h-screen shrink-0 ${isCollapsed ? 'w-20' : 'w-64'}`}>
            {/* Toggle Button */}
            <button
                onClick={() => setIsCollapsed(!isCollapsed)}
                className="absolute -right-3 top-10 bg-[#5B0019] border border-white/20 rounded-full p-1 z-50 shadow-md hover:scale-110 transition-transform"
            >
                {isCollapsed ? <ChevronRight size={16} /> : <ChevronLeft size={16} />}
            </button>

            {/* Logo */}
            <div className={`flex items-center px-4 mb-10 overflow-hidden ${isCollapsed ? 'justify-center' : 'justify-start gap-3'}`}>
                <div className="shrink-0">
                    <Image src={logo} alt="Logo" width={40} height={40} />
                </div>
                {!isCollapsed && <span className="font-bold text-lg whitespace-nowrap">EduTrust</span>}
            </div>

            {/* Main Menu */}
            <nav className="flex flex-col gap-2 px-3 flex-1 overflow-y-auto custom-scrollbar">
                {menuItems.map((item, index) => (
                    <SidebarItem
                        key={index}
                        icon={item.icon}
                        label={item.label}
                        path={item.path}
                        isCollapsed={isCollapsed}
                    />
                ))}
            </nav>
        </aside>
    );
};

const SidebarItem = ({ icon, label, desc, path, isCollapsed }: any) => (
    <Link href={path} className={`flex items-center p-3 rounded-xl hover:bg-white/10 transition-all group ${isCollapsed ? 'justify-center' : 'gap-4 px-4'}`}>
        <div className="shrink-0 group-hover:scale-110 transition-all duration-300">
            {icon}
        </div>
        {!isCollapsed && (
            <div>
                <span className="text-sm font-medium whitespace-nowrap opacity-100 block">
                    {label}
                </span>
                <p className="text-[11px] text-gray-400 font-semibold mt-1 uppercase tracking-wider">
                    {desc}
                </p>
            </div>
        )}
    </Link>
);