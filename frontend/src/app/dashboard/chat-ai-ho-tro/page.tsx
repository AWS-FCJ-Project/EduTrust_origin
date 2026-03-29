"use client";

import React, { useState, useRef, useEffect } from 'react';
import { Send, Bot, User, Sparkles, Eraser, Loader2 } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import remarkMath from 'remark-math';
import rehypeKatex from 'rehype-katex';

// @ts-ignore
import 'katex/dist/katex.min.css';
import Cookies from 'js-cookie';

interface Message {
    id: number;
    role: 'ai' | 'user';
    content: string;
}

const AIChatSupport = () => {
    const [user, setUser] = useState<any>(null);
    const [messages, setMessages] = useState<Message[]>([
        { id: 1, role: 'ai', content: 'Chào bạn! Mình là trợ lý ảo EduTrust. Bạn cần mình hỗ trợ gì không?' }
    ]);
    const [input, setInput] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [isPageLoading, setIsPageLoading] = useState(true);
    const scrollRef = useRef<HTMLDivElement>(null);

    // Fetch User Info to personalize
    useEffect(() => {
        const fetchUser = async () => {
            try {
                const token = Cookies.get("auth_token");
                const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/user-info`, {
                    headers: { 'Authorization': `Bearer ${token}` }
                });
                if (res.ok) {
                    const data = await res.json();
                    setUser(data);
                    // Update greeting with name
                    setMessages([{ 
                        id: 1, 
                        role: 'ai', 
                        content: `Chào ${data.name}! Mình là trợ lý ảo EduTrust. Bạn cần mình hỗ trợ gì không?` 
                    }]);
                }
            } catch (err) {
                console.error(err);
            } finally {
                setIsPageLoading(false);
            }
        };
        fetchUser();
    }, []);

    const formatLaTeX = (text: string) => {
        if (!text) return "";
        return text
            .replace(/\\\(|\\\)/g, "$")
            .replace(/\\\[|\\\]/g, "$$")
            .replace(/\$\$(.*?)\$\$/g, (match, formula) => `\n$$\n${formula.trim()}\n$$\n`)
            .replace(/(\w)\$/g, '$1 $')
            .replace(/\$(\w)/g, '$ $1');
    };

    const scrollToBottom = () => {
        if (scrollRef.current) {
            scrollRef.current.scrollTo({
                top: scrollRef.current.scrollHeight,
                behavior: 'smooth'
            });
        }
    };

    useEffect(() => {
        scrollToBottom();
    }, [messages]);

    const handleSend = async () => {
        if (!input.trim() || isLoading) return;

        const userContent = input.trim();
        const userMsgId = Date.now();
        const aiMsgId = userMsgId + 1;

        const newUserMsg: Message = { id: userMsgId, role: 'user', content: userContent };
        const newAiMsg: Message = { id: aiMsgId, role: 'ai', content: '' };

        setMessages(prev => [...prev, newUserMsg, newAiMsg]);
        setInput('');
        setIsLoading(true);

        const token = Cookies.get("auth_token");

        try {
            const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/unified-agent/ask/streaming`, {
                method: 'POST',
                headers: {
                    'accept': 'application/json',
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify({
                    question: userContent,
                    conversation_id: user ? `chat_${user.id || user._id}` : "generic_session"
                })
            });

            if (!response.body) throw new Error("No response body");

            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            let currentAiContent = "";

            while (true) {
                const { value, done } = await reader.read();
                if (done) break;

                const chunk = decoder.decode(value, { stream: true });
                const lines = chunk.split('\n');

                for (const line of lines) {
                    const trimmedLine = line.trim();
                    if (trimmedLine.startsWith('data: ')) {
                        const jsonStr = trimmedLine.replace('data: ', '');

                        if (jsonStr === '{"type": "complete"}' || jsonStr === '[DONE]') {
                            setIsLoading(false);
                            break;
                        }

                        try {
                            const parsed = JSON.parse(jsonStr);
                            if (parsed.type === 'text_delta' && parsed.content) {
                                currentAiContent += parsed.content;

                                setMessages(prev => prev.map(msg =>
                                    msg.id === aiMsgId ? { ...msg, content: currentAiContent } : msg
                                ));
                            }
                        } catch {
                        }
                    }
                }
            }
        } catch {
            setMessages(prev => prev.map(msg =>
                msg.id === aiMsgId ? { ...msg, content: "Lỗi kết nối rồi bạn ơi! Kiểm tra lại mạng nhé." } : msg
            ));
        } finally {
            setIsLoading(false);
        }
    };

    if (isPageLoading) {
        return (
            <div className="flex h-64 items-center justify-center">
                <Loader2 className="animate-spin text-[#5B0019]" size={40} />
            </div>
        );
    }

    return (
        <div className="flex flex-col h-[calc(100vh-120px)] bg-white rounded-3xl shadow-xl border border-gray-100 overflow-hidden">
            <div className="px-6 py-4 border-b border-gray-100 flex justify-between items-center shrink-0">
                <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-full bg-[#5B0019] flex items-center justify-center">
                        <Bot size={22} className="text-white" />
                    </div>
                    <div>
                        <h2 className="font-bold text-gray-800">EduTrust AI Assistant</h2>
                        <span className="text-[10px] text-gray-400 font-medium uppercase tracking-wider">AI Trợ lý đa năng</span>
                    </div>
                </div>
                <button
                    onClick={() => setMessages([{ id: 1, role: 'ai', content: `Lịch sử đã được làm mới, chào mừng ${user?.name || ''} trở lại!` }])}
                    className="p-2 hover:bg-red-50 hover:text-red-500 transition-colors rounded-full text-gray-400"
                    title="Xóa lịch sử chat"
                >
                    <Eraser size={18} />
                </button>
            </div>

            <div ref={scrollRef} className="flex-1 overflow-y-auto p-6 space-y-6 bg-[#F8F9FA]">
                {messages.map((msg) => (
                    <div key={msg.id} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                        <div className={`flex gap-3 max-w-[85%] ${msg.role === 'user' ? 'flex-row-reverse' : ''}`}>
                            <div className={`w-8 h-8 rounded-full flex shrink-0 items-center justify-center shadow-sm ${msg.role === 'user' ? 'bg-white text-gray-500 border' : 'bg-[#5B0019] text-white'
                                }`}>
                                {msg.role === 'user' ? <User size={16} /> : <Sparkles size={16} />}
                            </div>

                            <div className={`p-4 rounded-2xl text-sm shadow-sm leading-relaxed ${msg.role === 'user'
                                ? 'bg-[#5B0019] text-white rounded-tr-none'
                                : 'bg-white text-gray-700 border border-gray-100 rounded-tl-none'
                                }`}>
                                {msg.role === 'ai' ? (
                                    <div className="markdown-container prose prose-sm max-w-none prose-headings:text-[#5B0019] overflow-x-auto">
                                        {msg.content ? (
                                            <ReactMarkdown
                                                remarkPlugins={[remarkMath]}
                                                rehypePlugins={[rehypeKatex]}
                                            >
                                                {formatLaTeX(msg.content)}
                                            </ReactMarkdown>
                                        ) : (
                                            <div className="flex flex-col gap-2">
                                                <span className="text-xs text-gray-400 italic animate-pulse">
                                                    EduTrust đang suy nghĩ...
                                                </span>
                                                <div className="dot-loading">
                                                    <span></span>
                                                    <span></span>
                                                    <span></span>
                                                </div>
                                            </div>
                                        )}
                                    </div>
                                ) : (
                                    <div className="whitespace-pre-wrap">{msg.content}</div>
                                )}
                            </div>
                        </div>
                    </div>
                ))}
            </div>

            <div className="p-4 bg-white border-t border-gray-100">
                <div className="max-w-4xl mx-auto relative">
                    <input
                        type="text"
                        value={input}
                        disabled={isLoading}
                        onChange={(e) => setInput(e.target.value)}
                        onKeyDown={(e) => {
                            if (e.key === 'Enter' && !e.shiftKey) {
                                e.preventDefault();
                                handleSend();
                            }
                        }}
                        className="w-full pl-6 pr-14 py-4 bg-gray-50 border border-gray-200 focus:border-[#5B0019] focus:ring-1 focus:ring-[#5B0019] rounded-2xl outline-none transition-all disabled:opacity-50"
                        placeholder={isLoading ? "AI đang trả lời..." : `Bạn muốn hỏi gì không ${user?.name || ''}?`}
                    />
                    <button
                        onClick={handleSend}
                        disabled={isLoading || !input.trim()}
                        className="absolute right-2 top-1/2 -translate-y-1/2 p-2.5 bg-[#5B0019] text-white rounded-xl hover:bg-[#7a0021] disabled:bg-gray-300 transition-all shadow-md"
                    >
                        <Send size={18} />
                    </button>
                </div>
            </div>
        </div>
    );
};

export default AIChatSupport;
