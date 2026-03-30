"use client";

import React, {
    useDeferredValue,
    useEffect,
    useMemo,
    useRef,
    useState,
} from "react";
import {
    ArrowUp,
    CircleUserRound,
    PenLine,
    Loader2,
    MessageSquareText,
    PanelRightClose,
    PanelRightOpen,
    Search,
    Sparkles,
} from "lucide-react";
import ReactMarkdown from "react-markdown";
import remarkMath from "remark-math";
import rehypeKatex from "rehype-katex";
import Cookies from "js-cookie";

import "katex/dist/katex.min.css";

type UserInfo = {
    id: string;
    name?: string;
    email?: string;
};

type ConversationSummary = {
    conversation_id: string;
    title: string;
    preview: string;
    created_at?: string | null;
    updated_at?: string | null;
    message_count: number;
};

type ApiMessage = {
    role: string;
    content: string;
    created_at?: string | null;
};

type ApiConversation = {
    conversation_id: string;
    title: string;
    created_at?: string | null;
    updated_at?: string | null;
    messages: ApiMessage[];
};

type Message = {
    id: string;
    role: "ai" | "user";
    content: string;
    createdAt?: string | null;
};

const API_URL = process.env.NEXT_PUBLIC_API_URL;
const VIETNAM_TIMEZONE = "Asia/Ho_Chi_Minh";
const EMPTY_STATE_ROTATION_MS = 10000;
const mapApiMessage = (message: ApiMessage, index: number): Message => ({
    id: `${message.created_at || "message"}-${index}`,
    role: message.role === "assistant" ? "ai" : "user",
    content: message.content,
    createdAt: message.created_at,
});

const formatTitleFromInput = (value: string) => {
    const normalized = value.trim().replace(/\s+/g, " ");
    if (!normalized) {
        return "New Chat";
    }
    return normalized.length > 60 ? `${normalized.slice(0, 57)}...` : normalized;
};

const formatLaTeX = (text: string) => {
    if (!text) {
        return "";
    }

    return text
        .replace(/\\\(|\\\)/g, "$")
        .replace(/\\\[|\\\]/g, "$$")
        .replace(/\$\$(.*?)\$\$/g, (_, formula) => `\n$$\n${formula.trim()}\n$$\n`)
        .replace(/(\w)\$/g, "$1 $")
        .replace(/\$(\w)/g, "$ $1");
};

const getVietnamHour = () => {
    const parts = new Intl.DateTimeFormat("en-GB", {
        hour: "numeric",
        hour12: false,
        timeZone: VIETNAM_TIMEZONE,
    }).formatToParts(new Date());

    return Number(parts.find((part) => part.type === "hour")?.value || "0");
};

const getVietnameseDaypart = () => {
    const hour = getVietnamHour();
    if (hour < 11) {
        return "Chào buổi sáng";
    }
    if (hour < 14) {
        return "Chào buổi trưa";
    }
    if (hour < 18) {
        return "Chào buổi chiều";
    }
    return "Chào buổi tối";
};

const buildWelcomePrompts = (name?: string) => {
    const displayName = name?.trim() || "bạn";
    const daypart = getVietnameseDaypart();

    return [
        `${daypart}, ${displayName}.`,
        "Hôm nay bạn muốn học gì?",
        "Bạn cần hỗ trợ bài nào?",
        "Mình giúp bạn ôn tập nhé.",
        "Bạn muốn hỏi gì hôm nay?",
        "Bắt đầu học cùng EduTrust.",
    ];
};

export default function AIChatSupport() {
    const [conversations, setConversations] = useState<ConversationSummary[]>([]);
    const [activeConversationId, setActiveConversationId] = useState<string | null>(
        null,
    );
    const [messages, setMessages] = useState<Message[]>([]);
    const [input, setInput] = useState("");
    const [search, setSearch] = useState("");
    const [error, setError] = useState("");
    const [isPageLoading, setIsPageLoading] = useState(true);
    const [isConversationLoading, setIsConversationLoading] = useState(false);
    const [isSending, setIsSending] = useState(false);
    const [isCreatingConversation, setIsCreatingConversation] = useState(false);
    const [isSidebarOpen, setIsSidebarOpen] = useState(true);
    const [welcomeIndex, setWelcomeIndex] = useState(0);
    const [welcomePrompts, setWelcomePrompts] = useState<string[]>(() =>
        buildWelcomePrompts(),
    );
    const scrollRef = useRef<HTMLDivElement>(null);

    const deferredSearch = useDeferredValue(search);

    const filteredConversations = useMemo(() => {
        const keyword = deferredSearch.trim().toLowerCase();
        if (!keyword) {
            return conversations;
        }

        return conversations.filter((conversation) => {
            const haystack = `${conversation.title} ${conversation.preview}`.toLowerCase();
            return haystack.includes(keyword);
        });
    }, [conversations, deferredSearch]);

    useEffect(() => {
        if (!scrollRef.current) {
            return;
        }

        scrollRef.current.scrollTo({
            top: scrollRef.current.scrollHeight,
            behavior: "smooth",
        });
    }, [messages]);

    useEffect(() => {
        const bootstrap = async () => {
            setIsPageLoading(true);
            setError("");

            try {
                const resolvedUser = await fetchUserInfo();
                setWelcomePrompts(buildWelcomePrompts(resolvedUser.name));

                const fetchedConversations = await fetchConversations();
                setConversations(fetchedConversations);

                if (fetchedConversations.length > 0) {
                    const firstConversationId = fetchedConversations[0].conversation_id;
                    setActiveConversationId(firstConversationId);
                    await loadConversation(firstConversationId);
                } else {
                    setMessages([]);
                }
            } catch (bootstrapError) {
                console.error(bootstrapError);
                setError("Không thể tải danh sách hội thoại. Vui lòng thử lại.");
            } finally {
                setIsPageLoading(false);
            }
        };

        bootstrap();
    }, []);

    useEffect(() => {
        if (welcomePrompts.length <= 1) {
            return;
        }

        const intervalId = window.setInterval(() => {
            setWelcomeIndex((current) => (current + 1) % welcomePrompts.length);
        }, EMPTY_STATE_ROTATION_MS);

        return () => window.clearInterval(intervalId);
    }, [welcomePrompts]);

    const fetchUserInfo = async (): Promise<UserInfo> => {
        const cachedUser = Cookies.get("user_info");
        if (cachedUser) {
            try {
                return JSON.parse(cachedUser) as UserInfo;
            } catch {
                Cookies.remove("user_info");
            }
        }

        const token = Cookies.get("auth_token");
        const response = await fetch(`${API_URL}/user-info`, {
            headers: {
                Authorization: `Bearer ${token}`,
            },
        });

        if (!response.ok) {
            throw new Error("Unable to fetch user info");
        }

        const userInfo = (await response.json()) as UserInfo;
        Cookies.set("user_info", JSON.stringify(userInfo), {
            expires: 7,
            path: "/",
            sameSite: "strict",
            secure: process.env.NODE_ENV === "production",
        });
        return userInfo;
    };

    const fetchConversations = async (): Promise<ConversationSummary[]> => {
        const token = Cookies.get("auth_token");
        const response = await fetch(`${API_URL}/unified-agent/conversations?limit=50`, {
            headers: {
                Authorization: `Bearer ${token}`,
            },
        });

        if (!response.ok) {
            throw new Error("Unable to fetch conversations");
        }

        return (await response.json()) as ConversationSummary[];
    };

    const loadConversation = async (conversationId: string) => {
        setIsConversationLoading(true);
        setError("");

        try {
            const token = Cookies.get("auth_token");
            const response = await fetch(
                `${API_URL}/unified-agent/conversations/${conversationId}?message_limit=0`,
                {
                    headers: {
                        Authorization: `Bearer ${token}`,
                    },
                },
            );

            if (!response.ok) {
                throw new Error("Unable to load conversation");
            }

            const data = (await response.json()) as ApiConversation;
            setMessages(data.messages.map(mapApiMessage));
            setActiveConversationId(data.conversation_id);
        } catch (conversationError) {
            console.error(conversationError);
            setError("Không thể mở hội thoại này. Vui lòng thử lại.");
        } finally {
            setIsConversationLoading(false);
        }
    };

    const createConversation = async () => {
        setIsCreatingConversation(true);
        setError("");

        try {
            const token = Cookies.get("auth_token");
            const response = await fetch(`${API_URL}/unified-agent/conversations`, {
                method: "POST",
                headers: {
                    Authorization: `Bearer ${token}`,
                },
            });

            if (!response.ok) {
                throw new Error("Unable to create conversation");
            }

            const conversation = (await response.json()) as ApiConversation;
            const summary: ConversationSummary = {
                conversation_id: conversation.conversation_id,
                title: conversation.title || "New Chat",
                preview: "",
                created_at: conversation.created_at,
                updated_at: conversation.updated_at,
                message_count: 0,
            };

            setConversations((previous) => [summary, ...previous]);
            setActiveConversationId(conversation.conversation_id);
            setMessages([]);
            return conversation.conversation_id;
        } catch (creationError) {
            console.error(creationError);
            setError("Không thể tạo cuộc trò chuyện mới.");
            return null;
        } finally {
            setIsCreatingConversation(false);
        }
    };

    const refreshConversations = async (preferredConversationId?: string | null) => {
        try {
            const nextConversations = await fetchConversations();
            setConversations(nextConversations);

            if (!activeConversationId && nextConversations.length > 0) {
                setActiveConversationId(nextConversations[0].conversation_id);
                return;
            }

            if (
                preferredConversationId &&
                nextConversations.some(
                    (conversation) =>
                        conversation.conversation_id === preferredConversationId,
                )
            ) {
                setActiveConversationId(preferredConversationId);
            }
        } catch (refreshError) {
            console.error(refreshError);
        }
    };

    const handleCreateConversation = async () => {
        await createConversation();
    };

    const handleSelectConversation = async (conversationId: string) => {
        if (conversationId === activeConversationId) {
            return;
        }
        await loadConversation(conversationId);
    };

    const handleSend = async () => {
        if (!input.trim() || isSending) {
            return;
        }

        const token = Cookies.get("auth_token");
        const prompt = input.trim();
        const optimisticUserMessageId = `user-${Date.now()}`;
        const optimisticAssistantMessageId = `assistant-${Date.now() + 1}`;

        setInput("");
        setError("");
        setIsSending(true);

        let conversationId = activeConversationId;
        if (!conversationId) {
            conversationId = await createConversation();
        }

        if (!conversationId) {
            setIsSending(false);
            return;
        }

        const optimisticTitle = formatTitleFromInput(prompt);

        setConversations((previous) => {
            const existing = previous.find(
                (conversation) => conversation.conversation_id === conversationId,
            );

            if (!existing) {
                return previous;
            }

            return [
                {
                    ...existing,
                    title:
                        existing.title === "New Chat" ? optimisticTitle : existing.title,
                    preview: prompt,
                    updated_at: new Date().toISOString(),
                    message_count: Math.max(existing.message_count, 0) + 1,
                },
                ...previous.filter(
                    (conversation) => conversation.conversation_id !== conversationId,
                ),
            ];
        });

        setMessages((previous) => [
            ...previous,
            {
                id: optimisticUserMessageId,
                role: "user",
                content: prompt,
                createdAt: new Date().toISOString(),
            },
            {
                id: optimisticAssistantMessageId,
                role: "ai",
                content: "",
                createdAt: new Date().toISOString(),
            },
        ]);

        try {
            const response = await fetch(`${API_URL}/unified-agent/ask/streaming`, {
                method: "POST",
                headers: {
                    accept: "application/json",
                    "Content-Type": "application/json",
                    Authorization: `Bearer ${token}`,
                },
                body: JSON.stringify({
                    question: prompt,
                    conversation_id: conversationId,
                }),
            });

            if (!response.ok || !response.body) {
                throw new Error("No response stream");
            }

            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            let assistantContent = "";

            while (true) {
                const { done, value } = await reader.read();
                if (done) {
                    break;
                }

                const chunk = decoder.decode(value, { stream: true });
                const lines = chunk.split("\n");

                for (const line of lines) {
                    const trimmedLine = line.trim();
                    if (!trimmedLine.startsWith("data: ")) {
                        continue;
                    }

                    const payload = trimmedLine.replace("data: ", "");
                    if (payload === "[DONE]") {
                        continue;
                    }

                    try {
                        const parsed = JSON.parse(payload) as {
                            type: string;
                            content?: string;
                        };

                        if (parsed.type === "text_delta" && parsed.content) {
                            assistantContent += parsed.content;
                            setMessages((previous) =>
                                previous.map((message) =>
                                    message.id === optimisticAssistantMessageId
                                        ? { ...message, content: assistantContent }
                                        : message,
                                ),
                            );
                        }

                        if (parsed.type === "error") {
                            throw new Error(parsed.content || "Streaming error");
                        }
                    } catch (streamError) {
                        if (streamError instanceof SyntaxError) {
                            continue;
                        }
                        throw streamError;
                    }
                }
            }

            await refreshConversations(conversationId);
        } catch (sendError) {
            console.error(sendError);
            setMessages((previous) =>
                previous.map((message) =>
                    message.id === optimisticAssistantMessageId
                        ? {
                              ...message,
                              content:
                                  "Không thể nhận phản hồi lúc này. Vui lòng thử lại sau ít phút.",
                          }
                        : message,
                ),
            );
            setError("Phản hồi của trợ lý đang bị gián đoạn. Vui lòng thử lại.");
        } finally {
            setIsSending(false);
        }
    };

    if (isPageLoading) {
        return (
            <div className="flex h-[calc(100vh-120px)] items-center justify-center border border-[#D4D0CA] bg-[#F5F3F0] text-[#2D2A26] shadow-[0_20px_50px_rgba(45,42,38,0.08)]">
                <Loader2 className="animate-spin text-[#B8976A]" size={40} />
            </div>
        );
    }

    const showCenteredComposer = !activeConversationId && !isConversationLoading;

    return (
        <div
            className={`grid h-[calc(100vh-120px)] grid-cols-1 overflow-hidden border border-[#D4D0CA] bg-[#F5F3F0] text-[#2D2A26] shadow-[0_20px_50px_rgba(45,42,38,0.08)] ${
                isSidebarOpen ? "xl:grid-cols-[minmax(0,1fr)_336px]" : "xl:grid-cols-[minmax(0,1fr)_88px]"
            } transition-[grid-template-columns] duration-300 ease-in-out`}
        >
            <section className="flex min-h-0 flex-col overflow-hidden bg-[#F5F3F0]">
                {error ? (
                    <div className="mx-8 mt-5 rounded-[1.5rem] border border-[#E1C8B5] bg-[#F1E7DB] px-4 py-3 text-sm text-[#7A5948]">
                        {error}
                    </div>
                ) : null}

                <div
                    ref={scrollRef}
                    className="flex-1 overflow-y-auto px-8 py-8"
                >
                    {isConversationLoading ? (
                        <div className="flex h-full items-center justify-center">
                            <Loader2 className="animate-spin text-[#B8976A]" size={34} />
                        </div>
                    ) : messages.length === 0 ? (
                        <div className="flex h-full items-center justify-center">
                            <div className="flex w-full max-w-4xl flex-col items-center text-center">
                                <div className="mx-auto mb-10 flex h-16 w-16 items-center justify-center rounded-full border border-[#D4D0CA] bg-[#FFFDFC] text-[#B8976A] shadow-[0_16px_30px_rgba(184,151,106,0.12)]">
                                    <MessageSquareText size={28} />
                                </div>
                                {showCenteredComposer ? (
                                    <div className="mx-auto mb-8 max-w-4xl px-6 text-center">
                                        <p className="whitespace-nowrap font-serif text-[clamp(1.75rem,2.2vw,2.8rem)] leading-none text-[#2D2A26] transition-opacity duration-500">
                                            {welcomePrompts[welcomeIndex]}
                                        </p>
                                    </div>
                                ) : null}
                                {showCenteredComposer ? (
                                    <div className="mx-auto w-full max-w-3xl rounded-[2rem] border border-[#D4D0CA] bg-[#FFFDFC] px-4 py-2.5 shadow-[0_12px_30px_rgba(45,42,38,0.05)]">
                                        <div className="flex items-center gap-3">
                                            <textarea
                                                value={input}
                                                disabled={isSending}
                                                rows={1}
                                                onChange={(event) => setInput(event.target.value)}
                                                onKeyDown={(event) => {
                                                    if (event.key === "Enter" && !event.shiftKey) {
                                                        event.preventDefault();
                                                        handleSend();
                                                    }
                                                }}
                                                placeholder="Hỏi bất kỳ điều gì"
                                                className="max-h-32 min-h-[52px] flex-1 resize-none bg-transparent px-4 py-2.5 text-base leading-7 text-[#2D2A26] placeholder:text-[#8E867B] focus:outline-none"
                                            />
                                        </div>
                                    </div>
                                ) : null}
                            </div>
                        </div>
                    ) : (
                        <div className="flex flex-col gap-6">
                            {messages.map((message) => (
                                <div
                                    key={message.id}
                                    className={`flex ${
                                        message.role === "user"
                                            ? "justify-end"
                                            : "justify-start"
                                    }`}
                                >
                                    <div
                                        className={`flex max-w-[88%] gap-3 ${
                                            message.role === "user"
                                                ? "flex-row-reverse"
                                                : "flex-row"
                                        }`}
                                    >
                                        <div
                                            className={`mt-1 flex h-10 w-10 shrink-0 items-center justify-center rounded-2xl border ${
                                                message.role === "user"
                                                    ? "border-[#2D2A26] bg-[#2D2A26] text-[#F5F3F0]"
                                                    : "border-[#D4D0CA] bg-[#FFFDFC] text-[#B8976A]"
                                            }`}
                                        >
                                            {message.role === "user" ? (
                                                <CircleUserRound size={18} />
                                            ) : (
                                                <Sparkles size={16} />
                                            )}
                                        </div>

                                        <div
                                            className={`rounded-[1.75rem] px-5 py-4 text-sm leading-7 ${
                                                message.role === "user"
                                                    ? "rounded-tr-md bg-[#2D2A26] text-[#F5F3F0]"
                                                    : "rounded-tl-md border border-[#D4D0CA] bg-[#FFFDFC] text-[#2D2A26]"
                                            }`}
                                        >
                                            {message.role === "ai" ? (
                                                message.content ? (
                                                    <div className="prose prose-sm max-w-none overflow-x-auto prose-headings:text-[#2D2A26] prose-p:text-[#4F4A44] prose-strong:text-[#2D2A26] prose-li:text-[#4F4A44] prose-code:text-[#B8976A]">
                                                        <ReactMarkdown
                                                            remarkPlugins={[remarkMath]}
                                                            rehypePlugins={[rehypeKatex]}
                                                        >
                                                            {formatLaTeX(message.content)}
                                                        </ReactMarkdown>
                                                    </div>
                                                ) : (
                                                    <div className="flex items-center gap-3 text-[#8E867B]">
                                                        <Loader2
                                                            size={16}
                                                            className="animate-spin"
                                                        />
                                                        EduTrust đang suy nghĩ...
                                                    </div>
                                                )
                                            ) : (
                                                <div className="whitespace-pre-wrap">
                                                    {message.content}
                                                </div>
                                            )}
                                        </div>
                                    </div>
                                </div>
                            ))}
                        </div>
                    )}
                </div>

                {!showCenteredComposer ? (
                    <div className="border-t border-[#D4D0CA] bg-[#F7F5F2] px-8 py-5">
                        <div className="rounded-[2rem] border border-[#D4D0CA] bg-[#FFFDFC] p-3 shadow-[0_12px_30px_rgba(45,42,38,0.05)]">
                            <div className="flex items-center gap-3">
                                <textarea
                                    value={input}
                                    disabled={isSending}
                                    rows={1}
                                    onChange={(event) => setInput(event.target.value)}
                                    onKeyDown={(event) => {
                                        if (event.key === "Enter" && !event.shiftKey) {
                                        event.preventDefault();
                                        handleSend();
                                    }
                                }}
                                    placeholder={isSending ? "EduTrust đang trả lời..." : "Hỏi bất kỳ điều gì"}
                                    className="max-h-40 min-h-[64px] flex-1 resize-none bg-transparent px-5 py-4 text-base leading-8 text-[#2D2A26] placeholder:text-[#8E867B] focus:outline-none"
                                />
                                <button
                                    type="button"
                                    onClick={handleSend}
                                    disabled={isSending || !input.trim()}
                                    className="flex h-14 w-14 shrink-0 items-center justify-center rounded-2xl bg-[#DDD5CA] text-[#F5F3F0] transition hover:bg-[#2D2A26] disabled:cursor-not-allowed disabled:bg-[#CFC8BF]"
                                >
                                    {isSending ? (
                                        <Loader2 size={18} className="animate-spin" />
                                    ) : (
                                        <ArrowUp size={18} />
                                    )}
                                </button>
                            </div>
                        </div>
                    </div>
                ) : null}
            </section>

            <aside className="flex min-h-0 flex-col overflow-hidden border-t border-[#D4D0CA] bg-[#F7F5F2] xl:border-t-0 xl:border-l">
                <div className={`flex min-h-0 flex-1 flex-col transition-all duration-300 ease-in-out ${isSidebarOpen ? "p-6" : "items-center py-6"}`}>
                    <div className={`mb-6 flex transition-all duration-300 ease-in-out ${isSidebarOpen ? "items-center justify-between gap-3" : "flex-col gap-4"}`}>
                        <button
                            type="button"
                            onClick={() => setIsSidebarOpen((value) => !value)}
                            className="flex h-16 w-16 items-center justify-center rounded-[1.75rem] bg-[#2D2A26] text-[#F5F3F0] shadow-[0_10px_20px_rgba(45,42,38,0.12)]"
                            aria-label={isSidebarOpen ? "Đóng danh sách hội thoại" : "Mở danh sách hội thoại"}
                        >
                            {isSidebarOpen ? <PanelRightClose size={24} /> : <PanelRightOpen size={24} />}
                        </button>

                        {isSidebarOpen ? (
                            <div className="min-w-0 flex-1 origin-right transition-all duration-300 ease-in-out">
                                <p className="font-serif text-2xl text-[#2D2A26]">EduTrust AI</p>
                                <p className="text-xs uppercase tracking-[0.28em] text-[#B8976A]">
                                    Your chats
                                </p>
                            </div>
                        ) : null}
                    </div>

                    {isSidebarOpen ? (
                        <div className="flex min-h-0 flex-1 flex-col origin-right animate-in fade-in slide-in-from-right-4 duration-300">
                            <button
                                type="button"
                                onClick={handleCreateConversation}
                                disabled={isCreatingConversation || isSending}
                                className="mb-3 flex items-center gap-3 px-1 py-2 text-left text-[#2D2A26] transition hover:text-[#B8976A] disabled:cursor-not-allowed disabled:opacity-60"
                            >
                                {isCreatingConversation ? (
                                    <Loader2 size={22} className="animate-spin" />
                                ) : (
                                    <PenLine size={22} />
                                )}
                                <span className="text-[1.05rem]">New chat</span>
                            </button>

                            <label className="mb-6 flex items-center gap-3 px-1 py-2 text-[#2D2A26]">
                                <Search size={22} />
                                <input
                                    value={search}
                                    onChange={(event) => setSearch(event.target.value)}
                                    placeholder="Search chats"
                                    className="w-full bg-transparent text-[1.05rem] placeholder:text-[#8E867B] focus:outline-none"
                                />
                            </label>

                            <div className="mb-4 flex items-center justify-between">
                                <p className="text-sm font-medium text-[#8E867B]">Your chats</p>
                                <button
                                    type="button"
                                    onClick={() => setIsSidebarOpen(false)}
                                    className="text-[#8E867B] transition hover:text-[#B8976A]"
                                    aria-label="Thu gọn danh sách hội thoại"
                                >
                                    <PanelRightClose size={22} />
                                </button>
                            </div>

                            <div className="min-h-0 flex-1 space-y-1 overflow-y-auto pr-1">
                                {filteredConversations.length === 0 ? (
                                    <div className="px-3 py-4 text-sm leading-7 text-[#8E867B]">
                                        {conversations.length === 0
                                            ? "Chưa có lịch sử trò chuyện."
                                            : "Không tìm thấy hội thoại phù hợp."}
                                    </div>
                                ) : (
                                    filteredConversations.map((conversation) => {
                                        const isActive =
                                            conversation.conversation_id === activeConversationId;

                                        return (
                                            <button
                                                key={conversation.conversation_id}
                                                type="button"
                                                onClick={() =>
                                                    handleSelectConversation(conversation.conversation_id)
                                                }
                                                className={`w-full rounded-[1.5rem] px-3 py-3 text-left transition ${
                                                    isActive
                                                        ? "bg-[#EAE4DB]"
                                                        : "hover:bg-[#FBFAF7]"
                                                }`}
                                            >
                                                <p className="line-clamp-1 text-[1.05rem] font-medium text-[#2D2A26]">
                                                    {conversation.title || "New Chat"}
                                                </p>
                                                <p className="mt-1 line-clamp-1 text-sm text-[#8E867B]">
                                                    {conversation.preview || "Chưa có tin nhắn"}
                                                </p>
                                            </button>
                                        );
                                    })
                                )}
                            </div>
                        </div>
                    ) : (
                        <div className="flex flex-1 flex-col items-center gap-4 animate-in fade-in slide-in-from-right-2 duration-200">
                            <button
                                type="button"
                                onClick={handleCreateConversation}
                                className="text-[#2D2A26] transition hover:text-[#B8976A]"
                                aria-label="Tạo cuộc trò chuyện mới"
                            >
                                <PenLine size={24} />
                            </button>
                            <button
                                type="button"
                                onClick={() => setIsSidebarOpen(true)}
                                className="text-[#2D2A26] transition hover:text-[#B8976A]"
                                aria-label="Mở tìm kiếm hội thoại"
                            >
                                <Search size={24} />
                            </button>
                        </div>
                    )}
                </div>
            </aside>
        </div>
    );
}
