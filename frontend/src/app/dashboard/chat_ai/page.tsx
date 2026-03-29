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
    Bot,
    CircleUserRound,
    Loader2,
    MessageSquareText,
    PanelLeft,
    Plus,
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
const WELCOME_MESSAGE =
    "Chào bạn! Mình là trợ lý EduTrust. Hãy bắt đầu một cuộc trò chuyện mới ở khung bên trái.";

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

const formatRelativeTime = (value?: string | null) => {
    if (!value) {
        return "";
    }

    const date = new Date(value);
    if (Number.isNaN(date.getTime())) {
        return "";
    }

    const diffMinutes = Math.max(
        0,
        Math.round((Date.now() - date.getTime()) / (1000 * 60)),
    );

    if (diffMinutes < 1) {
        return "Vừa xong";
    }
    if (diffMinutes < 60) {
        return `${diffMinutes} phút trước`;
    }

    const diffHours = Math.round(diffMinutes / 60);
    if (diffHours < 24) {
        return `${diffHours} giờ trước`;
    }

    const diffDays = Math.round(diffHours / 24);
    if (diffDays < 7) {
        return `${diffDays} ngày trước`;
    }

    return date.toLocaleDateString("vi-VN");
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

export default function AIChatSupport() {
    const [user, setUser] = useState<UserInfo | null>(null);
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

    const activeConversation = useMemo(
        () =>
            conversations.find(
                (conversation) => conversation.conversation_id === activeConversationId,
            ) || null,
        [activeConversationId, conversations],
    );

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
                setUser(resolvedUser);

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
            <div className="flex h-[calc(100vh-120px)] items-center justify-center rounded-[2rem] border border-[#D4D0CA] bg-[#F5F3F0] text-[#2D2A26] shadow-[0_20px_50px_rgba(45,42,38,0.08)]">
                <Loader2 className="animate-spin text-[#B8976A]" size={40} />
            </div>
        );
    }

    return (
        <div className="grid h-[calc(100vh-120px)] grid-cols-1 overflow-hidden rounded-[2rem] border border-[#D4D0CA] bg-[#F5F3F0] text-[#2D2A26] shadow-[0_20px_50px_rgba(45,42,38,0.08)] xl:grid-cols-[320px_minmax(0,1fr)]">
            <aside className="flex min-h-0 flex-col border-b border-[#D4D0CA] bg-[#F7F5F2] p-6 xl:border-b-0 xl:border-r">
                <div className="mb-6 flex items-center justify-between gap-3">
                    <div className="flex items-center gap-3">
                        <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-[#2D2A26] text-[#F5F3F0] shadow-[0_10px_20px_rgba(45,42,38,0.12)]">
                            <Bot size={18} />
                        </div>
                        <div>
                            <p className="font-serif text-2xl text-[#2D2A26]">EduTrust AI</p>
                            <p className="text-xs uppercase tracking-[0.28em] text-[#B8976A]">
                                Your chats
                            </p>
                        </div>
                    </div>
                    <PanelLeft size={18} className="text-[#B8976A]" />
                </div>

                <button
                    type="button"
                    onClick={handleCreateConversation}
                    disabled={isCreatingConversation || isSending}
                    className="mb-4 flex items-center justify-center gap-2 rounded-[1.5rem] border border-[#D4D0CA] bg-[#FFFDFC] px-4 py-3 text-sm font-medium text-[#2D2A26] transition hover:border-[#B8976A] hover:bg-white disabled:cursor-not-allowed disabled:opacity-60"
                >
                    {isCreatingConversation ? (
                        <Loader2 size={16} className="animate-spin" />
                    ) : (
                        <Plus size={16} />
                    )}
                    Cuộc trò chuyện mới
                </button>

                <div className="mb-5 flex items-center gap-3 rounded-[1.5rem] border border-[#D4D0CA] bg-[#FBFAF7] px-4 py-3">
                    <Search size={16} className="text-[#B8976A]" />
                    <input
                        value={search}
                        onChange={(event) => setSearch(event.target.value)}
                        placeholder="Tìm kiếm hội thoại"
                        className="w-full bg-transparent text-sm text-[#2D2A26] placeholder:text-[#8E867B] focus:outline-none"
                    />
                </div>

                <div className="mb-3 flex items-center justify-between">
                    <p className="text-xs font-semibold uppercase tracking-[0.28em] text-[#B8976A]">
                        Your Chats
                    </p>
                    <span className="rounded-full border border-[#D4D0CA] bg-[#FBFAF7] px-2 py-1 text-[11px] text-[#8E867B]">
                        {filteredConversations.length}
                    </span>
                </div>

                <div className="min-h-0 flex-1 space-y-2 overflow-y-auto pr-1">
                    {filteredConversations.length === 0 ? (
                        <div className="rounded-[1.75rem] border border-dashed border-[#D4D0CA] bg-[#FBFAF7] p-4 text-sm leading-7 text-[#8E867B]">
                            {conversations.length === 0
                                ? "Chưa có lịch sử trò chuyện. Hãy tạo cuộc trò chuyện đầu tiên."
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
                                    className={`w-full rounded-3xl border px-4 py-3 text-left transition ${
                                        isActive
                                            ? "border-[#B8976A] bg-[#FFFDFC] shadow-[0_14px_30px_rgba(184,151,106,0.12)]"
                                            : "border-[#E6E0D8] bg-transparent hover:border-[#B8976A]/70 hover:bg-[#FBFAF7]"
                                    }`}
                                >
                                    <div className="mb-1 flex items-start justify-between gap-3">
                                        <p className="line-clamp-1 text-sm font-semibold text-[#2D2A26]">
                                            {conversation.title || "New Chat"}
                                        </p>
                                        <span className="shrink-0 text-[11px] text-[#8E867B]">
                                            {formatRelativeTime(conversation.updated_at)}
                                        </span>
                                    </div>
                                    <p className="line-clamp-2 text-xs leading-5 text-[#8E867B]">
                                        {conversation.preview || "Chưa có tin nhắn"}
                                    </p>
                                </button>
                            );
                        })
                    )}
                </div>

                <div className="mt-4 rounded-[1.75rem] border border-[#D4D0CA] bg-[#FBFAF7] p-4">
                    <p className="text-xs font-semibold uppercase tracking-[0.28em] text-[#B8976A]">
                        Hồ sơ phiên
                    </p>
                    <div className="mt-3 flex items-center gap-3">
                        <div className="flex h-11 w-11 items-center justify-center rounded-2xl border border-[#E6E0D8] bg-white">
                            <CircleUserRound size={22} className="text-[#8E867B]" />
                        </div>
                        <div className="min-w-0">
                            <p className="truncate text-sm font-semibold text-[#2D2A26]">
                                {user?.name || "Người dùng"}
                            </p>
                            <p className="truncate text-xs text-[#8E867B]">
                                {user?.email || "Tài khoản EduTrust"}
                            </p>
                        </div>
                    </div>
                </div>
            </aside>

            <section className="flex min-h-0 flex-col overflow-hidden bg-[#F5F3F0]">
                <div className="flex items-center justify-between border-b border-[#D4D0CA] px-8 py-6">
                    <div className="min-w-0">
                        <div className="flex items-center gap-3">
                            <div className="flex h-12 w-12 items-center justify-center rounded-2xl border border-[#D4D0CA] bg-[#FFFDFC] text-[#B8976A]">
                                <Sparkles size={18} />
                            </div>
                            <div className="min-w-0">
                                <h2 className="truncate font-serif text-4xl leading-none text-[#2D2A26]">
                                    {activeConversation?.title || "Bắt đầu cuộc trò chuyện mới"}
                                </h2>
                                <p className="mt-2 text-xs uppercase tracking-[0.28em] text-[#B8976A]">
                                    Trợ lý AI cho giáo viên và học sinh
                                </p>
                            </div>
                        </div>
                    </div>

                    <div className="hidden items-center gap-3 rounded-full border border-[#D4D0CA] bg-[#FFFDFC] px-4 py-2 text-sm text-[#8E867B] md:flex">
                        <CircleUserRound size={16} className="text-[#B8976A]" />
                        <span>{user?.name || "Người dùng"}</span>
                    </div>
                </div>

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
                        <div className="flex h-full flex-col items-center justify-center text-center">
                            <div className="mb-8 flex h-18 w-18 items-center justify-center rounded-[1.9rem] border border-[#D4D0CA] bg-[#FFFDFC] text-[#B8976A] shadow-[0_16px_30px_rgba(184,151,106,0.12)]">
                                <MessageSquareText size={30} />
                            </div>
                            <h3 className="font-serif text-6xl leading-[0.9] text-[#2D2A26]">
                                {activeConversationId
                                    ? "Sẵn sàng cho cuộc trò chuyện mới"
                                    : `Xin chào ${user?.name || ""}`}
                            </h3>
                            <p className="mt-6 max-w-3xl text-lg leading-10 text-[#8E867B]">
                                {activeConversationId
                                    ? "Hãy gửi câu hỏi đầu tiên để EduTrust tạo tiêu đề và lưu hội thoại này vào mục Your Chats."
                                    : WELCOME_MESSAGE}
                            </p>
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

                <div className="border-t border-[#D4D0CA] bg-[#F7F5F2] px-8 py-6">
                    <div className="rounded-[2rem] border border-[#D4D0CA] bg-[#FFFDFC] p-3 shadow-[0_12px_30px_rgba(45,42,38,0.05)]">
                        <div className="flex items-end gap-3">
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
                                placeholder={
                                    isSending
                                        ? "EduTrust đang trả lời..."
                                        : "Hỏi bài, nhờ soạn nội dung, hoặc bắt đầu một cuộc trò chuyện mới..."
                                }
                                className="max-h-40 min-h-[72px] flex-1 resize-none bg-transparent px-5 py-4 text-sm leading-7 text-[#2D2A26] placeholder:text-[#8E867B] focus:outline-none"
                            />

                            <button
                                type="button"
                                onClick={handleSend}
                                disabled={isSending || !input.trim()}
                                className="flex h-14 w-14 shrink-0 items-center justify-center rounded-2xl bg-[#2D2A26] text-[#F5F3F0] transition hover:bg-[#403B35] disabled:cursor-not-allowed disabled:bg-[#CFC8BF]"
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
            </section>
        </div>
    );
}
