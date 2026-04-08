"use client";

import React, { useEffect, useState } from 'react';
import { Trophy, Calendar, BookOpen, ChevronRight, Search, Award, CheckCircle2, XCircle } from 'lucide-react';
import Cookies from 'js-cookie';

interface ExamResult {
    exam_id: string;
    exam_title: string;
    subject: string;
    score: number;
    correct_count: number;
    total_questions: number;
    status: string;
    submitted_at: string;
}

export default function ResultsPage() {
    const [results, setResults] = useState<ExamResult[]>([]);
    const [loading, setLoading] = useState(true);
    const [searchTerm, setSearchTerm] = useState('');

    useEffect(() => {
        const fetchResults = async () => {
            try {
                const token = Cookies.get('auth_token');
                const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/exams/results/my`, {
                    headers: { 'Authorization': `Bearer ${token}` }
                });
                if (res.ok) {
                    const data = await res.json();
                    setResults(data);
                }
            } catch (error) {
                console.error("Error fetching results:", error);
            } finally {
                setLoading(false);
            }
        };
        fetchResults();
    }, []);

    const filteredResults = results.filter(r =>
        r.exam_title.toLowerCase().includes(searchTerm.toLowerCase()) ||
        r.subject.toLowerCase().includes(searchTerm.toLowerCase())
    );

    const averageScore = results.length > 0
        ? results.reduce((acc, curr) => acc + curr.score, 0) / results.length
        : 0;

    return (
        <div className="max-w-6xl mx-auto space-y-8 animate-in fade-in duration-700">
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
                <div>
                    <h1 className="text-4xl font-black text-gray-900 tracking-tight flex items-center gap-4">
                        <Trophy className="text-amber-500" size={40} />
                        {"K\u1EBFt Qu\u1EA3 H\u1ECDc T\u1EADp"}
                    </h1>
                    <p className="text-gray-500 font-medium mt-2">
                        {"Theo d\u00F5i ti\u1EBFn \u0111\u1ED9 v\u00E0 th\u00E0nh t\u00EDch c\u1EE7a b\u1EA1n qua t\u1EEBng k\u1EF3 thi."}
                    </p>
                </div>

                <div className="flex bg-white p-2 rounded-2xl shadow-sm border border-gray-100 items-center gap-3 w-full md:w-80 transition-all focus-within:ring-2 focus-within:ring-[#5B0019]/20">
                    <Search className="text-gray-400 ml-2" size={20} />
                    <input
                        type="text"
                        placeholder={"T\u00ECm ki\u1EBFm m\u00F4n h\u1ECDc, \u0111\u1EC1 thi..."}
                        className="bg-transparent border-none outline-none text-sm font-medium w-full"
                        value={searchTerm}
                        onChange={(e) => setSearchTerm(e.target.value)}
                    />
                </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div className="bg-white p-8 rounded-[2.5rem] shadow-sm border border-gray-100 flex items-center gap-6 group hover:shadow-md transition-all">
                    <div className="w-16 h-16 bg-blue-50 rounded-2xl flex items-center justify-center text-blue-600 group-hover:scale-110 transition-transform">
                        <BookOpen size={30} />
                    </div>
                    <div>
                        <p className="text-sm font-black text-gray-400 uppercase tracking-widest">
                            {"T\u1ED5ng b\u00E0i thi"}
                        </p>
                        <p className="text-3xl font-black text-gray-900">{results.length}</p>
                    </div>
                </div>

                <div className="bg-white p-8 rounded-[2.5rem] shadow-sm border border-gray-100 flex items-center gap-6 group hover:shadow-md transition-all">
                    <div className="w-16 h-16 bg-amber-50 rounded-2xl flex items-center justify-center text-amber-500 group-hover:scale-110 transition-transform">
                        <Award size={30} />
                    </div>
                    <div>
                        <p className="text-sm font-black text-gray-400 uppercase tracking-widest">
                            {"\u0110i\u1EC3m trung b\u00ECnh"}
                        </p>
                        <p className="text-3xl font-black text-gray-900">{averageScore.toFixed(1)}</p>
                    </div>
                </div>

                <div className="bg-[#5B0019] p-8 rounded-[2.5rem] shadow-xl flex items-center gap-6 group hover:scale-[1.02] transition-all">
                    <div className="w-16 h-16 bg-white/10 rounded-2xl flex items-center justify-center text-white group-hover:rotate-12 transition-transform">
                        <Trophy size={30} />
                    </div>
                    <div className="text-white">
                        <p className="text-sm font-black opacity-60 uppercase tracking-widest">
                            {"X\u1EBFp h\u1EA1ng"}
                        </p>
                        <p className="text-3xl font-black italic">Excellent</p>
                    </div>
                </div>
            </div>

            <div className="bg-white rounded-[3rem] shadow-sm border border-gray-100 overflow-hidden">
                <div className="p-8 border-b border-gray-50 flex items-center justify-between">
                    <h2 className="text-xl font-black text-gray-900 tracking-tight">
                        {"L\u1ECBch s\u1EED l\u00E0m b\u00E0i"}
                    </h2>
                    <div className="text-xs font-black text-gray-400 uppercase tracking-widest">
                        {"S\u1EAFp x\u1EBFp theo: M\u1EDBi nh\u1EA5t"}
                    </div>
                </div>

                <div className="overflow-x-auto">
                    {loading ? (
                        <div className="p-20 text-center space-y-4">
                            <div className="w-12 h-12 border-4 border-[#5B0019] border-t-transparent rounded-full animate-spin mx-auto"></div>
                            <p className="text-gray-400 font-bold uppercase tracking-widest text-xs">
                                {"\u0110ang t\u1EA3i k\u1EBFt qu\u1EA3..."}
                            </p>
                        </div>
                    ) : filteredResults.length > 0 ? (
                        <table className="w-full text-left border-collapse">
                            <thead>
                                <tr className="bg-gray-50/50">
                                    <th className="px-8 py-5 text-[10px] font-black text-gray-400 uppercase tracking-[0.2em]">
                                        {"M\u00F4n h\u1ECDc & \u0110\u1EC1 thi"}
                                    </th>
                                    <th className="px-8 py-5 text-[10px] font-black text-gray-400 uppercase tracking-[0.2em] text-center">
                                        {"C\u00E2u \u0111\u00FAng"}
                                    </th>
                                    <th className="px-8 py-5 text-[10px] font-black text-gray-400 uppercase tracking-[0.2em] text-center">
                                        {"\u0110i\u1EC3m s\u1ED1"}
                                    </th>
                                    <th className="px-8 py-5 text-[10px] font-black text-gray-400 uppercase tracking-[0.2em] text-center">
                                        {"Tr\u1EA1ng th\u00E1i"}
                                    </th>
                                    <th className="px-8 py-5 text-[10px] font-black text-gray-400 uppercase tracking-[0.2em]">
                                        {"Th\u1EDDi gian n\u1ED9p"}
                                    </th>
                                    <th className="px-8 py-5 text-right"></th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-gray-50">
                                {filteredResults.map((result, idx) => (
                                    <tr key={idx} className="hover:bg-gray-50/50 transition-colors group cursor-default">
                                        <td className="px-8 py-6">
                                            <div className="flex items-center gap-4">
                                                <div className="w-12 h-12 bg-gray-100 rounded-2xl flex items-center justify-center text-[#5B0019] group-hover:bg-[#5B0019] group-hover:text-white transition-all duration-300">
                                                    <BookOpen size={20} />
                                                </div>
                                                <div>
                                                    <p className="font-black text-gray-900 leading-none mb-1">{result.exam_title}</p>
                                                    <p className="text-xs font-bold text-gray-400 uppercase tracking-wider">{result.subject}</p>
                                                </div>
                                            </div>
                                        </td>
                                        <td className="px-8 py-6 text-center">
                                            <span className="inline-flex items-center gap-1.5 px-3 py-1 bg-gray-100 rounded-full text-xs font-black text-gray-600">
                                                {result.correct_count} / {result.total_questions}
                                            </span>
                                        </td>
                                        <td className="px-8 py-6 text-center">
                                            <div className="flex flex-col items-center">
                                                <span className={`text-2xl font-black ${result.score >= 8 ? 'text-green-600' : result.score >= 5 ? 'text-[#5B0019]' : 'text-red-500'}`}>
                                                    {result.score.toFixed(1)}
                                                </span>
                                                <div className="w-8 h-1 bg-gray-100 rounded-full mt-1 overflow-hidden">
                                                    <div
                                                        className={`h-full rounded-full ${result.score >= 8 ? 'bg-green-500' : result.score >= 5 ? 'bg-[#5B0019]' : 'bg-red-500'}`}
                                                        style={{ width: `${result.score * 10}%` }}
                                                    />
                                                </div>
                                            </div>
                                        </td>
                                        <td className="px-8 py-6 text-center">
                                            {result.status === 'completed' ? (
                                                <div className="flex items-center justify-center gap-2 text-green-600 font-bold text-xs uppercase tracking-widest">
                                                    <CheckCircle2 size={14} /> {"Ho\u00E0n th\u00E0nh"}
                                                </div>
                                            ) : (
                                                <div className="flex items-center justify-center gap-2 text-red-500 font-bold text-xs uppercase tracking-widest">
                                                    <XCircle size={14} /> {"Vi ph\u1EA1m"}
                                                </div>
                                            )}
                                        </td>
                                        <td className="px-8 py-6">
                                            <div className="flex items-center gap-2 text-gray-500 text-xs font-bold">
                                                <Calendar size={14} className="text-gray-400" />
                                                {new Date(result.submitted_at).toLocaleDateString('vi-VN', {
                                                    day: '2-digit',
                                                    month: '2-digit',
                                                    year: 'numeric',
                                                    hour: '2-digit',
                                                    minute: '2-digit'
                                                })}
                                            </div>
                                        </td>
                                        <td className="px-8 py-6 text-right">
                                            <button className="p-2 text-gray-300 hover:text-[#5B0019] hover:bg-red-50 rounded-xl transition-all">
                                                <ChevronRight size={20} />
                                            </button>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    ) : (
                        <div className="p-20 text-center space-y-6">
                            <div className="w-20 h-20 bg-gray-50 text-gray-200 rounded-full flex items-center justify-center mx-auto">
                                <Search size={40} />
                            </div>
                            <div className="space-y-2">
                                <p className="text-xl font-black text-gray-900 tracking-tight">
                                    {"Kh\u00F4ng t\u00ECm th\u1EA5y k\u1EBFt qu\u1EA3"}
                                </p>
                                <p className="text-gray-400 font-medium">
                                    {"B\u1EA1n ch\u01B0a ho\u00E0n th\u00E0nh b\u00E0i thi n\u00E0o ho\u1EB7c kh\u00F4ng t\u00ECm th\u1EA5y b\u00E0i thi ph\u00F9 h\u1EE3p."}
                                </p>
                            </div>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}
