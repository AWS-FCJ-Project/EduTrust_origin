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
    PenLine,
    Loader2,
    MessageSquareText,
    Search,
    Sun,
    Moon,
} from "lucide-react";
import ReactMarkdown from "react-markdown";
import remarkMath from "remark-math";
import rehypeKatex from "rehype-katex";
import Cookies from "js-cookie";

import "katex/dist/katex.min.css";
import { useTheme } from "@/components/providers/ThemeProvider";

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
const DEFAULT_CONVERSATION_TITLE_VI = "Hội thoại mới";
const DEFAULT_CONVERSATION_TITLE_EN = "New Chat";

const stripMarkdownForPreview = (value?: string | null) => {
    const text = (value || "").trim();
    if (!text) {
        return "";
    }

    return (
        text
            // code fences
            .replace(/```[\s\S]*?```/g, "")
            // inline code
            .replace(/`([^`]+)`/g, "$1")
            // images: ![alt](url) -> alt
            .replace(/!\[([^\]]*)\]\([^)]+\)/g, "$1")
            // links: [text](url) -> text
            .replace(/\[([^\]]+)\]\([^)]+\)/g, "$1")
            // bold/italic/strike markers
            .replace(/(\*\*|__)(.*?)\1/g, "$2")
            .replace(/(\*|_)(.*?)\1/g, "$2")
            .replace(/~~(.*?)~~/g, "$1")
            // headings/quotes/list bullets
            .replace(/^\s{0,3}#{1,6}\s+/gm, "")
            .replace(/^\s{0,3}>\s?/gm, "")
            .replace(/^\s*[-*+]\s+/gm, "")
            .replace(/^\s*\d+\.\s+/gm, "")
            // collapse whitespace/newlines
            .replace(/\s+/g, " ")
            .trim()
    );
};

const isDefaultConversationTitle = (title?: string | null) => {
    const normalized = (title || "").trim();
    if (!normalized) {
        return true;
    }
    return (
        normalized === DEFAULT_CONVERSATION_TITLE_VI ||
        normalized === DEFAULT_CONVERSATION_TITLE_EN
    );
};

const mapApiMessage = (message: ApiMessage, index: number): Message => ({
    id: `${message.created_at || "message"}-${index}`,
    role: message.role === "assistant" ? "ai" : "user",
    content: message.content,
    createdAt: message.created_at,
});

const formatTitleFromInput = (value: string) => {
    const normalized = value.trim().replace(/\s+/g, " ");
    if (!normalized) {
        return DEFAULT_CONVERSATION_TITLE_VI;
    }
    const sanitized = stripMarkdownForPreview(normalized);
    return sanitized.length > 60 ? `${sanitized.slice(0, 57)}...` : sanitized;
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
    const { theme, toggleTheme } = useTheme();

    const SidebarMenuMobileIcon = ({ size = 20 }: { size?: number }) => (
        <svg
            width={size}
            height={size}
            viewBox="0 0 24 24"
            fill="none"
            xmlns="http://www.w3.org/2000/svg"
            aria-hidden="true"
        >
            <path
                d="M6 9H14"
                stroke="currentColor"
                strokeWidth="2.5"
                strokeLinecap="round"
            />
            <path
                d="M6 15H18"
                stroke="currentColor"
                strokeWidth="2.5"
                strokeLinecap="round"
            />
        </svg>
    );

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
                title: conversation.title || DEFAULT_CONVERSATION_TITLE_VI,
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
                        isDefaultConversationTitle(existing.title)
                            ? optimisticTitle
                            : existing.title,
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
            <div className="flex h-full min-h-0 items-center justify-center border border-[var(--chat-border)] bg-[var(--chat-bg)] text-[var(--chat-text)] shadow-[0_20px_50px_var(--chat-shadow)]">
                <Loader2 className="animate-spin text-[var(--chat-accent)]" size={40} />
            </div>
        );
    }

    const showCenteredComposer = !activeConversationId && !isConversationLoading;

    return (
        <div
            className={`relative grid h-full min-h-0 grid-cols-1 overflow-hidden rounded-3xl border border-[var(--chat-border)] bg-[var(--chat-bg)] text-[var(--chat-text)] shadow-[0_20px_50px_var(--chat-shadow)] ${
                isSidebarOpen
                    ? "xl:grid-cols-[minmax(0,1fr)_336px]"
                    : "xl:grid-cols-[minmax(0,1fr)_72px]"
            } transition-[grid-template-columns] duration-300 ease-in-out`}
        >
            <section className="flex min-h-0 flex-col overflow-hidden rounded-3xl bg-[var(--chat-bg)]">
                <div className="pointer-events-none absolute left-4 top-4 z-10">
                    <button
                        type="button"
                        onClick={toggleTheme}
                        className="pointer-events-auto flex h-10 w-10 items-center justify-center rounded-full border border-[var(--chat-border)] bg-[var(--chat-surface)] text-[var(--chat-text)] transition hover:bg-[var(--chat-sidebar-bg)]"
                        aria-label="Toggle theme"
                    >
                        {theme === "dark" ? <Sun size={18} /> : <Moon size={18} />}
                    </button>
                </div>

                {error ? (
                    <div className="mx-auto w-full max-w-4xl rounded-[1.5rem] border border-[var(--chat-border)] bg-[var(--chat-surface)] px-4 py-3 text-sm text-[var(--chat-text-muted)]">
                        {error}
                    </div>
                ) : null}

                <div
                    ref={scrollRef}
                    className="flex-1 overflow-y-auto px-4 py-8"
                >
                    {isConversationLoading ? (
                        <div className="flex h-full items-center justify-center">
                            <Loader2 className="animate-spin text-[var(--chat-accent)]" size={34} />
                        </div>
                    ) : messages.length === 0 ? (
                        <div className="flex h-full items-center justify-center">
                            <div className="flex w-full max-w-4xl flex-col items-center text-center">
                                <div className="mx-auto mb-10 flex h-16 w-16 items-center justify-center rounded-full border border-[var(--chat-border)] bg-[var(--chat-surface)] text-[var(--chat-accent)] shadow-[0_16px_30px_var(--chat-shadow)]">
                                    <MessageSquareText size={28} />
                                </div>
                                {showCenteredComposer ? (
                                    <div className="mx-auto mb-8 max-w-4xl px-6 text-center">
                                        <p className="whitespace-nowrap text-[clamp(1.85rem,2.4vw,3rem)] font-semibold leading-none tracking-[-0.04em] text-[var(--chat-text)] transition-opacity duration-500">
                                            {welcomePrompts[welcomeIndex]}
                                        </p>
                                    </div>
                                ) : null}
                                {showCenteredComposer ? (
                                    <div className="mx-auto w-full max-w-4xl rounded-[2rem] border border-[var(--chat-border)] bg-[var(--chat-surface)] px-4 py-2.5 shadow-[0_12px_30px_var(--chat-shadow)]">
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
                                                className="max-h-32 min-h-[44px] flex-1 resize-none bg-transparent px-3 py-2 text-base leading-7 text-[var(--chat-text)] placeholder:text-[var(--chat-input-placeholder)] focus:outline-none"
                                            />
                                        </div>
                                    </div>
                                ) : null}
                            </div>
                        </div>
                    ) : (
                        <div className="mx-auto flex w-full max-w-4xl flex-col gap-8">
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
                                        className={`flex flex-col ${
                                            message.role === "user"
                                                ? "max-w-[78%] items-end"
                                                : "w-full items-start"
                                        }`}
                                    >
                                        <div
                                            className={`px-4 py-3 text-base leading-7 ${
                                                message.role === "user"
                                                    ? "rounded-2xl bg-[var(--chat-user-bg)] font-medium text-[var(--chat-user-text)]"
                                                    : "text-[var(--chat-text)]"
                                            }`}
                                        >
                                            {message.role === "ai" ? (
                                                message.content ? (
                                                    <div className="prose prose-base max-w-none overflow-x-auto prose-headings:mb-2 prose-headings:mt-6 prose-headings:text-[var(--chat-text)] prose-p:my-3 prose-p:font-medium prose-p:leading-7 prose-p:text-[var(--chat-ai-text)] prose-strong:text-[var(--chat-text)] prose-ul:my-3 prose-ul:list-disc prose-ul:pl-6 prose-ol:my-3 prose-ol:list-decimal prose-ol:pl-6 prose-li:my-1 prose-li:font-medium prose-li:text-[var(--chat-ai-text)] prose-code:text-[var(--chat-accent)]">
                                                        <ReactMarkdown
                                                            remarkPlugins={[remarkMath]}
                                                            rehypePlugins={[rehypeKatex]}
                                                            components={{
                                                                hr: () => null,
                                                            }}
                                                        >
                                                            {formatLaTeX(message.content)}
                                                        </ReactMarkdown>
                                                    </div>
                                                ) : (
                                                    <div className="flex items-center gap-3 text-base font-medium text-[var(--chat-text-muted)]">
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
                    <div className="bg-[var(--chat-bg)] px-4 py-5">
                        <div className="mx-auto w-full max-w-4xl rounded-[2rem] border border-[var(--chat-input-border)] bg-[var(--chat-input-bg)] p-2.5 shadow-[0_12px_30px_var(--chat-shadow)]">
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
                                    className="max-h-40 min-h-[48px] flex-1 resize-none bg-transparent px-4 py-3 text-base leading-7 text-[var(--chat-input-text)] placeholder:text-[var(--chat-input-placeholder)] focus:outline-none"
                                />
                                <button
                                    type="button"
                                    onClick={handleSend}
                                    disabled={isSending || !input.trim()}
                                    className="flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl bg-[var(--chat-button-bg)] text-[var(--chat-button-text)] transition hover:bg-[var(--chat-button-hover)] disabled:cursor-not-allowed disabled:bg-[var(--chat-button-disabled)]"
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

            <aside className="flex min-h-0 flex-col overflow-hidden border-t border-[var(--chat-border)] bg-[var(--chat-sidebar-bg)] xl:border-t-0 xl:border-l">
                <div
                    className={`flex min-h-0 flex-1 flex-col transition-all duration-300 ease-in-out ${
                        isSidebarOpen ? "p-6" : "items-end px-3 py-6"
                    }`}
                >
                    {isSidebarOpen ? (
                        <div className="mb-6 flex w-full items-center gap-4 transition-all duration-300 ease-in-out">
                            <div className="flex h-16 w-16 items-center justify-center rounded-[1.75rem] bg-[var(--chat-button-bg)] text-[var(--chat-button-text)] shadow-[0_10px_20px_var(--chat-shadow)]">
                                <MessageSquareText size={26} strokeWidth={2.5} />
                            </div>

                            <div className="min-w-0 flex-1 origin-right transition-all duration-300 ease-in-out">
                                <p className="text-xl font-semibold tracking-[-0.03em] text-[var(--chat-sidebar-text)]">
                                    EduTrust AI
                                </p>
                                <p className="type-label mt-1 text-[var(--chat-accent)]">
                                    Hội thoại
                                </p>
                            </div>
                        </div>
                    ) : (
                        <div className="mb-6 flex w-full flex-col items-end gap-5 pt-2">
                            <button
                                type="button"
                                onClick={handleCreateConversation}
                                className="flex h-11 w-11 items-center justify-center rounded-md bg-transparent text-[var(--chat-text)] opacity-75 transition hover:opacity-100 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--chat-border)]"
                                aria-label="Tạo hội thoại mới"
                            >
                                <PenLine size={24} strokeWidth={2.75} />
                            </button>
                            <button
                                type="button"
                                onClick={() => setIsSidebarOpen(true)}
                                className="flex h-11 w-11 items-center justify-center rounded-md bg-transparent text-[var(--chat-text)] opacity-75 transition hover:opacity-100 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--chat-border)]"
                                aria-label="Mở danh sách hội thoại"
                            >
                                <Search size={24} strokeWidth={2.75} />
                            </button>
                        </div>
                    )}

                    {isSidebarOpen ? (
                        <div className="flex min-h-0 flex-1 flex-col origin-right animate-in fade-in slide-in-from-right-4 duration-300">
                            <button
                                type="button"
                                onClick={handleCreateConversation}
                                disabled={isCreatingConversation || isSending}
                                className="mb-3 flex items-center gap-3 px-1 py-2 text-left text-[var(--chat-sidebar-text)] transition hover:text-[var(--chat-accent)] disabled:cursor-not-allowed disabled:opacity-60"
                            >
                                {isCreatingConversation ? (
                                    <Loader2 size={22} className="animate-spin" />
                                ) : (
                                    <PenLine size={24} strokeWidth={2.5} />
                                )}
                                <span className="text-[1.05rem]">Tạo hội thoại mới</span>
                            </button>

                            <label className="mb-6 flex items-center gap-3 px-1 py-2 text-[var(--chat-sidebar-text)]">
                                <Search size={24} strokeWidth={2.5} />
                                <input
                                    value={search}
                                    onChange={(event) => setSearch(event.target.value)}
                                    placeholder="Tìm hội thoại"
                                    className="w-full bg-transparent text-[1.05rem] placeholder:text-[var(--chat-text-muted)] focus:outline-none"
                                />
                            </label>

                            <div className="mb-4 flex items-center justify-between">
                                <p className="text-sm font-medium text-[var(--chat-text-muted)]">Hội thoại của bạn</p>
                            </div>

                            <div className="min-h-0 flex-1 space-y-1 overflow-y-auto pr-1">
                                {filteredConversations.length === 0 ? (
                                    <div className="px-3 py-4 text-sm leading-7 text-[var(--chat-text-muted)]">
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
                                                        ? "bg-[var(--chat-button-bg)]"
                                                        : "hover:bg-[var(--chat-surface)]"
                                                }`}
                                            > 
                                                <p className="line-clamp-1 text-[1.05rem] font-medium text-[var(--chat-sidebar-text)]">
                                                    {stripMarkdownForPreview(
                                                        conversation.title || DEFAULT_CONVERSATION_TITLE_VI,
                                                    )}
                                                </p>
                                                <p className="mt-1 line-clamp-1 text-sm text-[var(--chat-text-muted)]">
                                                    {stripMarkdownForPreview(conversation.preview) ||
                                                        "Chưa có tin nhắn"}
                                                </p>
                                            </button>
                                        );
                                    })
                                )}
                            </div>
                        </div>
                    ) : (
                        <div className="flex flex-1 flex-col" />
                    )}

                    <div
                        className={`mt-auto flex w-full pt-6 ${
                            isSidebarOpen ? "justify-end px-1" : "justify-end px-3"
                        }`}
                    >
                        <button
                            type="button"
                            onClick={() => setIsSidebarOpen((value) => !value)}
                            className="flex h-11 w-11 items-center justify-center rounded-md bg-transparent text-[var(--chat-text)] opacity-75 transition hover:opacity-100 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--chat-border)]"
                            aria-label={
                                isSidebarOpen ? "Thu gọn thanh bên" : "Mở rộng thanh bên"
                            }
                        >
                            <SidebarMenuMobileIcon size={24} />
                        </button>
                    </div>
                </div>
            </aside>
        </div>
    );
}
