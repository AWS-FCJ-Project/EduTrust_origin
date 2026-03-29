"use client";

import React, { useState, useEffect, useRef } from 'react';
import { Clock } from 'lucide-react';
import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

interface TimePickerProps {
    value: string; // HH:mm
    onChange: (value: string) => void;
    placeholder?: string;
    className?: string;
}

const hours = Array.from({ length: 24 }, (_, i) => i.toString().padStart(2, '0'));
const minutes = ['00', '10', '20', '30', '40', '50'];

const TimePicker: React.FC<TimePickerProps> = ({ value, onChange, placeholder = "00:00", className }) => {
    const [isOpen, setIsOpen] = useState(false);
    const containerRef = useRef<HTMLDivElement>(null);
    const hourScrollRef = useRef<HTMLDivElement>(null);
    const minuteScrollRef = useRef<HTMLDivElement>(null);

    // Parse current value
    const [h, m] = (value || "00:00").split(':');

    useEffect(() => {
        const handleClickOutside = (event: MouseEvent) => {
            if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
                setIsOpen(false);
            }
        };
        document.addEventListener('mousedown', handleClickOutside);
        return () => document.removeEventListener('mousedown', handleClickOutside);
    }, []);

    // Scroll to current value when opened
    useEffect(() => {
        if (isOpen) {
            setTimeout(() => {
                const hIdx = hours.indexOf(h);
                const mIdx = minutes.indexOf(m);

                if (hIdx !== -1 && hourScrollRef.current) {
                    const el = hourScrollRef.current.children[hIdx] as HTMLElement;
                    hourScrollRef.current.scrollTop = el.offsetTop - (hourScrollRef.current.clientHeight / 2) + (el.clientHeight / 2);
                }
                if (mIdx !== -1 && minuteScrollRef.current) {
                    const el = minuteScrollRef.current.children[mIdx] as HTMLElement;
                    minuteScrollRef.current.scrollTop = el.offsetTop - (minuteScrollRef.current.clientHeight / 2) + (el.clientHeight / 2);
                }
            }, 10);
        }
    }, [isOpen, h, m]);

    const handleHourSelect = (hour: string) => {
        onChange(`${hour}:${m || "00"}`);
    };

    const handleMinuteSelect = (min: string) => {
        onChange(`${h || "00"}:${min}`);
    };

    const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        let val = e.target.value.replace(/[^0-9:]/g, '');
        // Auto format HH:mm
        if (val.length === 2 && !val.includes(':')) {
            val = val + ':';
        }
        if (val.length > 5) val = val.substring(0, 5);
        onChange(val);
    };

    const handleInputBlur = () => {
        // Validate HH:mm
        const parts = value.split(':');
        let hh = parts[0] || "00";
        let mm = parts[1] || "00";
        
        if (parseInt(hh) > 23) hh = "23";
        if (parseInt(mm) > 59) mm = "59";
        
        onChange(`${hh.padStart(2, '0')}:${mm.padStart(2, '0')}`);
    };

    return (
        <div ref={containerRef} className={cn("relative inline-block w-full", className)}>
            <div className="relative group">
                <input 
                    type="text"
                    value={value}
                    onChange={handleInputChange}
                    onBlur={handleInputBlur}
                    onFocus={() => setIsOpen(true)}
                    placeholder={placeholder}
                    className="w-full px-4 py-4 bg-white border-none rounded-2xl focus:ring-2 focus:ring-[#5B0019] transition-all font-bold text-center text-sm shadow-sm pr-10"
                />
                <div 
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-300 group-hover:text-[#5B0019] cursor-pointer"
                    onClick={() => setIsOpen(!isOpen)}
                >
                    <Clock size={16} />
                </div>
            </div>

            {isOpen && (
                <div className="absolute top-full left-0 mt-2 z-50 bg-white/95 backdrop-blur-xl border border-gray-100 rounded-[2rem] shadow-2xl p-4 flex gap-2 animate-in fade-in slide-in-from-top-2 duration-300">
                    <div className="flex flex-col items-center">
                        <span className="text-[10px] font-black text-gray-400 uppercase tracking-widest mb-2">Giờ</span>
                        <div 
                            ref={hourScrollRef}
                            className="h-48 overflow-y-auto w-14 custom-scrollbar snap-y snap-mandatory"
                        >
                            {hours.map((hour) => (
                                <button
                                    key={hour}
                                    type="button"
                                    onClick={() => handleHourSelect(hour)}
                                    className={cn(
                                        "w-full h-10 flex items-center justify-center rounded-xl font-black text-sm transition-all snap-center",
                                        h === hour ? "bg-[#5B0019] text-white scale-110 shadow-lg" : "text-gray-400 hover:text-gray-800"
                                    )}
                                >
                                    {hour}
                                </button>
                            ))}
                        </div>
                    </div>

                    <div className="w-[1px] bg-gray-100 h-40 self-center mt-4"></div>

                    <div className="flex flex-col items-center">
                        <span className="text-[10px] font-black text-gray-400 uppercase tracking-widest mb-2">Phút</span>
                        <div 
                            ref={minuteScrollRef}
                            className="h-48 overflow-y-auto w-14 custom-scrollbar snap-y snap-mandatory"
                        >
                            {minutes.map((min) => (
                                <button
                                    key={min}
                                    type="button"
                                    onClick={() => handleMinuteSelect(min)}
                                    className={cn(
                                        "w-full h-10 flex items-center justify-center rounded-xl font-black text-sm transition-all snap-center",
                                        m === min ? "bg-[#5B0019] text-white scale-110 shadow-lg" : "text-gray-400 hover:text-gray-800"
                                    )}
                                >
                                    {min}
                                </button>
                            ))}
                        </div>
                    </div>
                </div>
            )}

            <style jsx>{`
                .custom-scrollbar::-webkit-scrollbar {
                    width: 0px;
                }
            `}</style>
        </div>
    );
};

export default TimePicker;
