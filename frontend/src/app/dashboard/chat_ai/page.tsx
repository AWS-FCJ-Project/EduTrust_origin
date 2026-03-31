"use client";

import React, {
    useCallback,
    useDeferredValue,
    useEffect,
    useMemo,
    useRef,
    useState,
} from "react";
import {
    ArrowUp,
    ClipboardCopy,
    PenLine,
    Loader2,
    Search,
    Sun,
    Moon,
} from "lucide-react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import remarkMath from "remark-math";
import rehypeKatex from "rehype-katex";
import Cookies from "js-cookie";

import "katex/dist/katex.min.css";
import {
    Check as OaiCheck,
    Copy,
    Delete,
} from "@openai/apps-sdk-ui/components/Icon";
import { useTheme } from "@/components/providers/ThemeProvider";
import { PrismLight as SyntaxHighlighter } from "react-syntax-highlighter";
import bash from "react-syntax-highlighter/dist/esm/languages/prism/bash";
import css from "react-syntax-highlighter/dist/esm/languages/prism/css";
import diff from "react-syntax-highlighter/dist/esm/languages/prism/diff";
import docker from "react-syntax-highlighter/dist/esm/languages/prism/docker";
import go from "react-syntax-highlighter/dist/esm/languages/prism/go";
import java from "react-syntax-highlighter/dist/esm/languages/prism/java";
import javascript from "react-syntax-highlighter/dist/esm/languages/prism/javascript";
import json from "react-syntax-highlighter/dist/esm/languages/prism/json";
import jsx from "react-syntax-highlighter/dist/esm/languages/prism/jsx";
import kotlin from "react-syntax-highlighter/dist/esm/languages/prism/kotlin";
import markdown from "react-syntax-highlighter/dist/esm/languages/prism/markdown";
import markup from "react-syntax-highlighter/dist/esm/languages/prism/markup";
import php from "react-syntax-highlighter/dist/esm/languages/prism/php";
import python from "react-syntax-highlighter/dist/esm/languages/prism/python";
import ruby from "react-syntax-highlighter/dist/esm/languages/prism/ruby";
import scss from "react-syntax-highlighter/dist/esm/languages/prism/scss";
import sql from "react-syntax-highlighter/dist/esm/languages/prism/sql";
import toml from "react-syntax-highlighter/dist/esm/languages/prism/toml";
import tsx from "react-syntax-highlighter/dist/esm/languages/prism/tsx";
import typescript from "react-syntax-highlighter/dist/esm/languages/prism/typescript";
import yaml from "react-syntax-highlighter/dist/esm/languages/prism/yaml";
import vscDarkPlus from "react-syntax-highlighter/dist/esm/styles/prism/vsc-dark-plus";
import vs from "react-syntax-highlighter/dist/esm/styles/prism/vs";

SyntaxHighlighter.registerLanguage("javascript", javascript);
SyntaxHighlighter.registerLanguage("jsx", jsx);
SyntaxHighlighter.registerLanguage("typescript", typescript);
SyntaxHighlighter.registerLanguage("tsx", tsx);
SyntaxHighlighter.registerLanguage("markup", markup);
SyntaxHighlighter.registerLanguage("css", css);
SyntaxHighlighter.registerLanguage("scss", scss);
SyntaxHighlighter.registerLanguage("bash", bash);
SyntaxHighlighter.registerLanguage("json", json);
SyntaxHighlighter.registerLanguage("jsonc", json);
SyntaxHighlighter.registerLanguage("python", python);
SyntaxHighlighter.registerLanguage("sql", sql);
SyntaxHighlighter.registerLanguage("diff", diff);
SyntaxHighlighter.registerLanguage("markdown", markdown);
SyntaxHighlighter.registerLanguage("yaml", yaml);
SyntaxHighlighter.registerLanguage("toml", toml);
SyntaxHighlighter.registerLanguage("docker", docker);
SyntaxHighlighter.registerLanguage("java", java);
SyntaxHighlighter.registerLanguage("go", go);
SyntaxHighlighter.registerLanguage("php", php);
SyntaxHighlighter.registerLanguage("ruby", ruby);
SyntaxHighlighter.registerLanguage("kotlin", kotlin);

type UserInfo = {
    id: string;
    name?: string;
    full_name?: string;
    username?: string;
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

type StreamEventType =
    | "text_delta"
    | "complete"
    | "error";

type StreamEvent = {
    type: StreamEventType;
    content?: unknown;
};

type ThinkingMessageState = {
    isStreaming: boolean;
    currentToolName: string;
};

type PendingDeleteConversation = {
    id: string;
    title: string;
};

const API_URL = process.env.NEXT_PUBLIC_API_URL;
const VIETNAM_TIMEZONE = "Asia/Ho_Chi_Minh";
const EMPTY_STATE_ROTATION_MS = 10000;
const DEFAULT_CONVERSATION_TITLE_VI = "Hội thoại mới";
const DEFAULT_CONVERSATION_TITLE_EN = "New Chat";
const STREAM_TYPING_INTERVAL_MS = 42;
const STREAM_TYPING_CHARS_PER_TICK = 2;
const STREAM_DRAIN_MAX_WAIT_MS = 3000;

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

const normalizeConversationTitle = (title?: string | null) => {
    if (isDefaultConversationTitle(title)) {
        return DEFAULT_CONVERSATION_TITLE_VI;
    }
    return (title || "").trim();
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

const ThinkingIndicator = () => {
    return (
        <span className="edutrust-thinking">
            Đang suy nghĩ<span className="edutrust-thinking-dots" aria-hidden="true" />
        </span>
    );
};

type DetectedCodeLanguage = {
    prism?: string;
    label: string; // already uppercased for display
};

const detectCodeLanguage = (
    className?: string,
    codeText?: string,
): DetectedCodeLanguage => {
    const raw = (className || "").replace("language-", "").trim().toLowerCase();

    // Prism language id + display label.
    const prismMap: Record<string, { prism: string; label: string }> = {
        js: { prism: "javascript", label: "JAVASCRIPT" },
        javascript: { prism: "javascript", label: "JAVASCRIPT" },
        jsx: { prism: "jsx", label: "JSX" },
        ts: { prism: "typescript", label: "TYPESCRIPT" },
        typescript: { prism: "typescript", label: "TYPESCRIPT" },
        tsx: { prism: "tsx", label: "TSX" },
        py: { prism: "python", label: "PYTHON" },
        python: { prism: "python", label: "PYTHON" },
        sh: { prism: "bash", label: "BASH" },
        shell: { prism: "bash", label: "BASH" },
        bash: { prism: "bash", label: "BASH" },
        zsh: { prism: "bash", label: "BASH" },
        yml: { prism: "yaml", label: "YAML" },
        yaml: { prism: "yaml", label: "YAML" },
        md: { prism: "markdown", label: "MARKDOWN" },
        markdown: { prism: "markdown", label: "MARKDOWN" },
        sql: { prism: "sql", label: "SQL" },
        json: { prism: "json", label: "JSON" },
        jsonc: { prism: "jsonc", label: "JSONC" },
        html: { prism: "markup", label: "HTML" },
        xml: { prism: "markup", label: "XML" },
        css: { prism: "css", label: "CSS" },
        scss: { prism: "scss", label: "SCSS" },
        toml: { prism: "toml", label: "TOML" },
        dockerfile: { prism: "docker", label: "DOCKER" },
        docker: { prism: "docker", label: "DOCKER" },
        java: { prism: "java", label: "JAVA" },
        go: { prism: "go", label: "GO" },
        php: { prism: "php", label: "PHP" },
        rb: { prism: "ruby", label: "RUBY" },
        ruby: { prism: "ruby", label: "RUBY" },
        kt: { prism: "kotlin", label: "KOTLIN" },
        kotlin: { prism: "kotlin", label: "KOTLIN" },
        diff: { prism: "diff", label: "DIFF" },
    };

    if (raw && prismMap[raw]) {
        return prismMap[raw];
    }

    const text = (codeText || "").trim();
    const firstLine = text.split("\n")[0]?.trim() || "";

    const extMatch = firstLine.match(/\.([a-z0-9+#]+)$/i);
    if (extMatch) {
        const ext = extMatch[1].toLowerCase();
        if (prismMap[ext]) {
            return prismMap[ext];
        }
    }

    if (
        firstLine.startsWith("#!/") ||
        /\b(pip|npm|pnpm|yarn|uv|atlas|curl)\b/.test(text) ||
        /^(?:export\s+)?[A-Z0-9_]{2,}=/m.test(text)
    ) {
        return prismMap.bash;
    }
    if (/\b(def |import |from .+ import )/.test(text)) {
        return prismMap.python;
    }
    if (/\b(select|insert|update|delete|create table)\b/i.test(text)) {
        return prismMap.sql;
    }
    if (/\b(function|const |let |console\.log|=>)\b/.test(text)) {
        return prismMap.javascript;
    }

    return { label: "TEXT" };
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

// Typing indicator is handled by <ThinkingIndicator /> for the streaming assistant state.

const getUserDisplayName = (user?: UserInfo) => {
    const candidate =
        user?.name?.trim() ||
        user?.full_name?.trim() ||
        user?.username?.trim() ||
        "";
    return candidate;
};

const buildWelcomePrompts = (user?: UserInfo) => {
    const displayName = getUserDisplayName(user);
    const daypart = getVietnameseDaypart();
    const greeting = displayName ? `${daypart} ${displayName}.` : `${daypart}.`;

    return [
        greeting,
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
    const [pendingDeleteConversation, setPendingDeleteConversation] =
        useState<PendingDeleteConversation | null>(null);
    const [isDeletingConversation, setIsDeletingConversation] = useState(false);
    const [messages, setMessages] = useState<Message[]>([]);
    const [input, setInput] = useState("");
    const [search, setSearch] = useState("");
    const [error, setError] = useState("");
    const [isPageLoading, setIsPageLoading] = useState(true);
    const [isConversationLoading, setIsConversationLoading] = useState(false);
    const [isSending, setIsSending] = useState(false);
    const [isCreatingConversation, setIsCreatingConversation] = useState(false);
    const [isSidebarOpen, setIsSidebarOpen] = useState(true);
    const [copiedMessageId, setCopiedMessageId] = useState<string | null>(null);
    const [copiedCodeId, setCopiedCodeId] = useState<string | null>(null);
    const [welcomeIndex, setWelcomeIndex] = useState(0);
    const [welcomePrompts, setWelcomePrompts] = useState<string[]>(() =>
        buildWelcomePrompts(),
    );
    const [thinkingByMessageId, setThinkingByMessageId] = useState<
        Record<string, ThinkingMessageState>
    >({});
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
                setWelcomePrompts(buildWelcomePrompts(resolvedUser));

                const fetchedConversations = await fetchConversations();
                setConversations(fetchedConversations);
                setActiveConversationId(null);
                setMessages([]);
                setThinkingByMessageId({});
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
        const shouldRotateWelcome =
            !isConversationLoading &&
            messages.length === 0;

        if (!shouldRotateWelcome || welcomePrompts.length <= 1) {
            return;
        }

        const intervalId = window.setInterval(() => {
            setWelcomeIndex((current) => {
                if (welcomePrompts.length <= 1) {
                    return 0;
                }

                let next = current;
                while (next === current) {
                    next = Math.floor(Math.random() * welcomePrompts.length);
                }
                return next;
            });
        }, EMPTY_STATE_ROTATION_MS);

        return () => window.clearInterval(intervalId);
    }, [welcomePrompts, isConversationLoading, messages.length]);

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

        const data = (await response.json()) as ConversationSummary[];
        return data.map((conversation) => ({
            ...conversation,
            title: normalizeConversationTitle(conversation.title),
        }));
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
            setThinkingByMessageId({});
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
                title: normalizeConversationTitle(conversation.title),
                preview: "",
                created_at: conversation.created_at,
                updated_at: conversation.updated_at,
                message_count: 0,
            };

            setConversations((previous) => [summary, ...previous]);
            setActiveConversationId(conversation.conversation_id);
            setMessages([]);
            setThinkingByMessageId({});
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
        // Like ChatGPT: "New Chat" just resets to empty state.
        // The conversation is only created when the user sends the first message.
        setActiveConversationId(null);
        setMessages([]);
        setThinkingByMessageId({});
        setInput("");
        setError("");
    };

    const closeDeleteModal = useCallback(() => {
        if (isDeletingConversation) {
            return;
        }
        setPendingDeleteConversation(null);
    }, [isDeletingConversation]);

    useEffect(() => {
        if (!pendingDeleteConversation) {
            return;
        }

        const onKeyDown = (event: KeyboardEvent) => {
            if (event.key !== "Escape") {
                return;
            }
            event.preventDefault();
            closeDeleteModal();
        };

        window.addEventListener("keydown", onKeyDown);
        return () => window.removeEventListener("keydown", onKeyDown);
    }, [pendingDeleteConversation, closeDeleteModal]);

    const deleteConversation = async (conversationId: string) => {
        const token = Cookies.get("auth_token");
        const response = await fetch(
            `${API_URL}/unified-agent/conversations/${conversationId}`,
            {
                method: "DELETE",
                headers: {
                    Authorization: `Bearer ${token}`,
                },
            },
        );

        if (response.status === 204) {
            return;
        }

        if (response.status === 404) {
            throw new Error("Conversation not found");
        }

        throw new Error("Unable to delete conversation");
    };

    const handleConfirmDeleteConversation = async () => {
        if (!pendingDeleteConversation || isDeletingConversation) {
            return;
        }

        setIsDeletingConversation(true);
        setError("");

        try {
            await deleteConversation(pendingDeleteConversation.id);
            setConversations((previous) =>
                previous.filter(
                    (conversation) =>
                        conversation.conversation_id !== pendingDeleteConversation.id,
                ),
            );

            if (activeConversationId === pendingDeleteConversation.id) {
                await handleCreateConversation();
            }

            setPendingDeleteConversation(null);
        } catch (deleteError) {
            console.error(deleteError);
            setError("Không thể xóa hội thoại. Vui lòng thử lại.");
        } finally {
            setIsDeletingConversation(false);
        }
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
	        setThinkingByMessageId((previous) => ({
	            ...previous,
	            [optimisticAssistantMessageId]: {
	                isStreaming: true,
	                currentToolName: "Đang suy nghĩ",
	            },
	        }));

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
	            let pendingRenderBuffer = "";
	            let leftoverBuffer = "";
	            let typingTimer: ReturnType<typeof setInterval> | null = null;
	            // Some models/providers leak tool-call arguments as leading JSON in the text stream.
	            // Strip a single leading JSON object that looks like tool args (e.g. {"plan": "..."}).
	            let leadingJsonDone = false;
	            let leadingJsonActive = false;
	            let leadingJsonBuf = "";
	            let leadingJsonDepth = 0;
	            let leadingJsonInString = false;
	            let leadingJsonEscape = false;

	            const looksLikeToolArgsJson = (obj: unknown) => {
	                if (!obj || typeof obj !== "object" || Array.isArray(obj)) {
	                    return false;
	                }
	                const dict = obj as Record<string, unknown>;
	                if ("tool_name" in dict && ("arguments" in dict || "args" in dict)) {
	                    return true;
	                }
	                if ("plan" in dict && Object.keys(dict).length <= 3) {
	                    return true;
	                }
	                return false;
	            };

	            const resetLeadingJson = () => {
	                leadingJsonDone = true;
	                leadingJsonActive = false;
	                leadingJsonBuf = "";
	                leadingJsonDepth = 0;
	                leadingJsonInString = false;
	                leadingJsonEscape = false;
	            };

	            const stripLeadingToolJson = (fragment: string) => {
	                if (!fragment) {
	                    return "";
	                }
	                if (leadingJsonDone) {
	                    return fragment;
	                }
	                if (assistantContent.trim() || pendingRenderBuffer.trim()) {
	                    leadingJsonDone = true;
	                    return fragment;
	                }

	                if (!leadingJsonActive) {
	                    if (fragment.trimStart().startsWith("{")) {
	                        leadingJsonActive = true;
	                    } else {
	                        leadingJsonDone = true;
	                        return fragment;
	                    }
	                }

	                leadingJsonBuf += fragment;

	                let endIdx: number | null = null;
	                for (let i = 0; i < leadingJsonBuf.length; i += 1) {
	                    const ch = leadingJsonBuf[i]!;
	                    if (leadingJsonEscape) {
	                        leadingJsonEscape = false;
	                        continue;
	                    }
	                    if (ch === "\\" && leadingJsonInString) {
	                        leadingJsonEscape = true;
	                        continue;
	                    }
	                    if (ch === '"') {
	                        leadingJsonInString = !leadingJsonInString;
	                        continue;
	                    }
	                    if (leadingJsonInString) {
	                        continue;
	                    }
	                    if (ch === "{") {
	                        leadingJsonDepth += 1;
	                    } else if (ch === "}") {
	                        leadingJsonDepth -= 1;
	                        if (leadingJsonDepth === 0) {
	                            endIdx = i + 1;
	                            break;
	                        }
	                    }
	                }

	                if (endIdx == null) {
	                    if (leadingJsonBuf.length > 6000) {
	                        const buf = leadingJsonBuf;
	                        resetLeadingJson();
	                        return buf;
	                    }
	                    return "";
	                }

	                const candidate = leadingJsonBuf.slice(0, endIdx).trim();
	                const tail = leadingJsonBuf.slice(endIdx);
	                try {
	                    const parsed = JSON.parse(candidate) as unknown;
	                    if (looksLikeToolArgsJson(parsed)) {
	                        resetLeadingJson();
	                        return tail;
	                    }
	                } catch {
	                    // Fall through and show it as normal text.
	                }

	                const buf = leadingJsonBuf;
	                resetLeadingJson();
	                return buf;
	            };

	            const renderAssistantMessage = (content: string) => {
	                setMessages((previous) =>
	                    previous.map((message) =>
                        message.id === optimisticAssistantMessageId
                            ? { ...message, content }
                            : message,
                    ),
                );
            };

            const flushPendingBuffer = () => {
                if (!pendingRenderBuffer) {
                    return;
                }
                assistantContent += pendingRenderBuffer;
                pendingRenderBuffer = "";
                renderAssistantMessage(assistantContent);
            };

            const waitForPendingBufferDrain = async () => {
                const startedAt = Date.now();
                while (pendingRenderBuffer.length > 0) {
                    if (Date.now() - startedAt >= STREAM_DRAIN_MAX_WAIT_MS) {
                        break;
                    }
                    await new Promise((resolve) => window.setTimeout(resolve, 20));
                }
            };

            const startTypingTimer = () => {
                if (typingTimer) {
                    return;
                }
                typingTimer = setInterval(() => {
                    if (!pendingRenderBuffer) {
                        return;
                    }

                    const adaptiveCharsPerTick = Math.max(
                        STREAM_TYPING_CHARS_PER_TICK,
                        Math.ceil(pendingRenderBuffer.length / 80),
                    );
                    const nextChunk = pendingRenderBuffer.slice(
                        0,
                        adaptiveCharsPerTick,
                    );
                    pendingRenderBuffer = pendingRenderBuffer.slice(
                        adaptiveCharsPerTick,
                    );
                    assistantContent += nextChunk;
                    renderAssistantMessage(assistantContent);
                }, STREAM_TYPING_INTERVAL_MS);
            };

            const markThinkingStreaming = (isStreaming: boolean) => {
                setThinkingByMessageId((previous) => {
                    const current = previous[optimisticAssistantMessageId];
                    if (!current) {
                        return previous;
                    }
                    return {
                        ...previous,
                        [optimisticAssistantMessageId]: {
                            ...current,
                            isStreaming,
                            currentToolName: isStreaming
                                ? current.currentToolName
                                : "",
                        },
                    };
                });
            };

	            const handleSseLine = (line: string) => {
	                const trimmedLine = line.trim();
	                if (!trimmedLine.startsWith("data: ")) {
	                    return;
	                }

                const payload = trimmedLine.replace("data: ", "");
                if (payload === "[DONE]") {
                    return;
                }

	                const parsed = JSON.parse(payload) as StreamEvent;
	                if (parsed.type === "text_delta" && typeof parsed.content === "string") {
	                    const cleaned = stripLeadingToolJson(parsed.content);
	                    if (!cleaned) {
	                        return;
	                    }
	                    pendingRenderBuffer += cleaned;
	                    startTypingTimer();
	                    return;
	                }
	                if (parsed.type === "complete") {
	                    markThinkingStreaming(false);
	                    return;
	                }
                if (parsed.type === "error") {
                    throw new Error(
                        typeof parsed.content === "string"
                            ? parsed.content
                            : "Streaming error",
                    );
                }
            };

            try {
                while (true) {
                    const { done, value } = await reader.read();
                    if (done) {
                        break;
                    }

                    leftoverBuffer += decoder.decode(value, { stream: true });
                    const lines = leftoverBuffer.split("\n");
                    leftoverBuffer = lines.pop() ?? "";

                    for (const line of lines) {
                        handleSseLine(line);
                    }
                }

                const tail = leftoverBuffer.trim();
                if (tail) {
                    handleSseLine(tail);
                }
                markThinkingStreaming(false);
            } finally {
                await waitForPendingBufferDrain();
                if (typingTimer) {
                    clearInterval(typingTimer);
                    typingTimer = null;
                }
                flushPendingBuffer();
            }

            await refreshConversations(conversationId);
        } catch (sendError) {
            console.error(sendError);
            setThinkingByMessageId((previous) => {
                const current = previous[optimisticAssistantMessageId];
                if (!current) {
                    return previous;
                }
                return {
                    ...previous,
                    [optimisticAssistantMessageId]: {
                        ...current,
                        isStreaming: false,
                        currentToolName: "",
                    },
                };
            });
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

    const copyText = async (
        text: string,
        kind: "message" | "code",
        targetId: string,
    ) => {
        try {
            await navigator.clipboard.writeText(text);
            if (kind === "message") {
                setCopiedMessageId(targetId);
                window.setTimeout(() => setCopiedMessageId(null), 1400);
            } else {
                setCopiedCodeId(targetId);
                window.setTimeout(() => setCopiedCodeId(null), 1400);
            }
        } catch (copyError) {
            console.error(copyError);
        }
    };

    if (isPageLoading) {
        return (
            <div className="flex h-full min-h-0 items-center justify-center border border-[var(--chat-border)] bg-[var(--chat-bg)] text-[var(--chat-text)] shadow-[0_20px_50px_var(--chat-shadow)]">
                <Loader2 className="animate-spin text-[var(--chat-accent)]" size={40} />
            </div>
        );
    }

    const showCenteredComposer = messages.length === 0 && !isConversationLoading;

    return (
        <div
            className={`relative grid h-full min-h-0 grid-cols-1 overflow-hidden rounded-3xl border border-[var(--chat-border)] bg-[var(--chat-bg)] text-[var(--chat-text)] shadow-[0_20px_50px_var(--chat-shadow)] ${
                isSidebarOpen
                    ? "xl:grid-cols-[minmax(0,1fr)_336px]"
                    : "xl:grid-cols-[minmax(0,1fr)_72px]"
            } transition-[grid-template-columns] duration-300 ease-in-out`}
        >
            {pendingDeleteConversation ? (
                <div
                    className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 px-4"
                    role="dialog"
                    aria-modal="true"
                    aria-label="Xác nhận xóa hội thoại"
                    onClick={closeDeleteModal}
                >
                    <div
                        className="w-full max-w-md rounded-2xl border border-[var(--chat-border)] bg-[var(--chat-surface)] p-5 shadow-[0_18px_50px_rgba(0,0,0,0.4)]"
                        onClick={(event) => event.stopPropagation()}
                    >
                        <h2 className="text-lg font-semibold text-[var(--chat-text)]">
                            Xóa hội thoại?
                        </h2>
                        <p className="mt-2 text-sm leading-6 text-[var(--chat-text-muted)]">
                            Bạn có chắc muốn xóa{" "}
                            <span className="font-medium text-[var(--chat-text)]">
                                {stripMarkdownForPreview(
                                    pendingDeleteConversation.title,
                                ) || DEFAULT_CONVERSATION_TITLE_VI}
                            </span>
                            ? Thao tác này không thể hoàn tác.
                        </p>
                        <div className="mt-5 flex items-center justify-end gap-2">
                            <button
                                type="button"
                                onClick={closeDeleteModal}
                                disabled={isDeletingConversation}
                                className="rounded-xl border border-[var(--chat-border)] bg-transparent px-4 py-2 text-sm font-medium text-[var(--chat-text)] transition hover:bg-[var(--chat-button-bg)] disabled:cursor-not-allowed disabled:opacity-60"
                            >
                                Hủy
                            </button>
                            <button
                                type="button"
                                onClick={handleConfirmDeleteConversation}
                                disabled={isDeletingConversation}
                                className="rounded-xl bg-[var(--chat-text)] px-4 py-2 text-sm font-semibold text-[var(--chat-surface)] transition hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-60"
                            >
                                {isDeletingConversation ? "Đang xóa..." : "Xóa"}
                            </button>
                        </div>
                    </div>
                </div>
            ) : null}
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
                    className="flex-1 overflow-y-auto px-4 pt-8 pb-32"
                >
                    {isConversationLoading ? (
                        <div className="flex h-full items-center justify-center">
                            <Loader2 className="animate-spin text-[var(--chat-accent)]" size={34} />
                        </div>
                    ) : messages.length === 0 ? (
                        <div className="flex h-full items-center justify-center">
                            <div className="flex w-full max-w-4xl flex-col items-center text-center">
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
                        <div className="mx-auto flex w-full max-w-6xl flex-col gap-8">
                            {messages.map((message) => {
                                const thinkingState = thinkingByMessageId[message.id];

                                return (
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
                                                    : "w-full max-w-[96%] items-start"
                                            } group relative`}
                                        >
                                            <div
                                                className={`px-4 py-3 text-[1.08rem] leading-8 ${
                                                    message.role === "user"
                                                        ? "rounded-2xl bg-[var(--chat-user-bg)] font-medium text-[var(--chat-user-text)]"
                                                        : "font-medium text-[var(--chat-text)]"
                                                }`}
                                            >
                                                {message.role === "ai" ? (
                                                    message.content ? (
                                                        <div className="prose prose-lg max-w-none overflow-x-auto prose-headings:mb-2 prose-headings:mt-6 prose-headings:text-[var(--chat-text)] prose-p:my-3 prose-p:font-semibold prose-p:leading-8 prose-p:text-[var(--chat-ai-text)] prose-strong:text-[var(--chat-text)] prose-li:my-1 prose-li:font-medium prose-li:text-[var(--chat-ai-text)] prose-code:text-[var(--chat-accent)]">
                                                            <ReactMarkdown
                                                                remarkPlugins={[
                                                                    remarkGfm,
                                                                    remarkMath,
                                                                ]}
                                                                rehypePlugins={[
                                                                    rehypeKatex,
                                                                ]}
                                                                components={{
                                                                    hr: () => null,
                                                                    ul: ({
                                                                        children,
                                                                    }) => (
                                                                        <ul className="my-3 list-disc pl-6 marker:text-[var(--chat-accent)]">
                                                                            {
                                                                                children
                                                                            }
                                                                        </ul>
                                                                    ),
                                                                    ol: ({
                                                                        children,
                                                                    }) => (
                                                                        <ol className="my-3 list-decimal pl-6 marker:text-[var(--chat-accent)]">
                                                                            {
                                                                                children
                                                                            }
                                                                        </ol>
                                                                    ),
                                                                    li: ({
                                                                        children,
                                                                    }) => (
                                                                        <li className="my-1 pl-1">
                                                                            {
                                                                                children
                                                                            }
                                                                        </li>
                                                                    ),
                                                                    pre: ({
                                                                        children,
                                                                    }) => (
                                                                        <>{children}</>
                                                                    ),
	                                                                    code: ({
	                                                                        inline,
	                                                                        className,
	                                                                        children,
	                                                                        ...props
	                                                                    }: any) =>
	                                                                        inline ? (
	                                                                            <code
	                                                                                className="rounded-md bg-[var(--chat-surface)] px-1.5 py-0.5 font-mono text-[0.9em] text-[var(--chat-accent)]"
	                                                                                {...props}
	                                                                            >
	                                                                                {
	                                                                                    children
	                                                                                }
	                                                                            </code>
	                                                                        ) : (
	                                                                            (() => {
	                                                                                const codeText =
	                                                                                    String(
	                                                                                        children,
	                                                                                    ).replace(
	                                                                                        /\n$/,
	                                                                                        "",
	                                                                                    );
	                                                                                const trimmed =
	                                                                                    codeText.trim();
	                                                                                const detectedLanguage =
	                                                                                    detectCodeLanguage(
	                                                                                        className,
	                                                                                        codeText,
	                                                                                    );

	                                                                                // If the model emits a fenced code block that is actually
	                                                                                // just a single token (dotfile/filename), render it like
	                                                                                // inline code to avoid awkward big code boxes.
	                                                                                const isSingleLine =
	                                                                                    !trimmed.includes(
	                                                                                        "\n",
	                                                                                    );
	                                                                                const isFilenameLike =
	                                                                                    /^\.[a-z0-9_-]{1,20}$/i.test(
	                                                                                        trimmed,
	                                                                                    ) ||
	                                                                                    /^[~./]?[a-z0-9_./-]{0,80}\.[a-z0-9_+-]{1,10}$/i.test(
	                                                                                        trimmed,
	                                                                                    );
	                                                                                const hasLetter =
	                                                                                    /[a-z]/i.test(
	                                                                                        trimmed,
	                                                                                    );
	                                                                                const shouldInlineize =
	                                                                                    isSingleLine &&
	                                                                                    isFilenameLike &&
	                                                                                    hasLetter &&
	                                                                                    trimmed.length <=
	                                                                                        64;
	                                                                                if (
	                                                                                    shouldInlineize
	                                                                                ) {
	                                                                                    return (
	                                                                                        <code
	                                                                                            className="rounded-md bg-[var(--chat-surface)] px-1.5 py-0.5 font-mono text-[0.9em] text-[var(--chat-accent)]"
	                                                                                            {...props}
	                                                                                        >
	                                                                                            {
	                                                                                                trimmed
	                                                                                            }
	                                                                                        </code>
	                                                                                    );
	                                                                                }
	                                                                                const codeId = `${message.id}-${detectedLanguage.label}-${codeText.slice(
	                                                                                    0,
	                                                                                    18,
	                                                                                )}`;
	                                                                                const isCodeCopied =
	                                                                                    copiedCodeId ===
	                                                                                    codeId;

	                                                                                const syntaxTheme =
	                                                                                    theme ===
	                                                                                    "dark"
	                                                                                        ? vscDarkPlus
	                                                                                        : vs;
	                                                                                const codeBlockBg =
	                                                                                    theme ===
	                                                                                    "dark"
	                                                                                        ? "#0b0b0b"
	                                                                                        : "#ffffff";

	                                                                                return (
	                                                                                    <div
	                                                                                        className="relative my-4 overflow-hidden rounded-xl border border-[var(--chat-border)] group"
	                                                                                        style={{
	                                                                                            backgroundColor:
	                                                                                                codeBlockBg,
	                                                                                        }}
	                                                                                    >
	                                                                                        <div className="pointer-events-none absolute left-4 top-3 flex items-center gap-2 text-xs font-semibold uppercase tracking-[0.08em] text-[var(--chat-text-muted)]">
	                                                                                            <span className="font-mono text-[0.95em]">
	                                                                                                {"</>"}
	                                                                                            </span>
	                                                                                            <span>
	                                                                                                {
	                                                                                                    detectedLanguage.label
	                                                                                                }
	                                                                                            </span>
	                                                                                        </div>
	                                                                                        <button
	                                                                                            type="button"
	                                                                                            onClick={() =>
	                                                                                                copyText(
	                                                                                                    codeText,
	                                                                                                    "code",
	                                                                                                    codeId,
	                                                                                                )
	                                                                                            }
	                                                                                            className="absolute right-2 top-2 z-10 inline-flex h-7 w-7 items-center justify-center text-[var(--chat-text-muted)] opacity-0 transition group-hover:opacity-100 hover:text-[var(--chat-text)]"
	                                                                                            aria-label={
	                                                                                                isCodeCopied
	                                                                                                    ? "Đã copy"
	                                                                                                    : "Copy code"
	                                                                                            }
	                                                                                            title={
	                                                                                                isCodeCopied
	                                                                                                    ? "Đã copy"
	                                                                                                    : "Copy code"
	                                                                                            }
	                                                                                        >
	                                                                                            {isCodeCopied ? (
	                                                                                                <OaiCheck className="size-4" />
	                                                                                            ) : (
	                                                                                                <ClipboardCopy className="size-4" />
	                                                                                            )}
	                                                                                        </button>
	                                                                                        <SyntaxHighlighter
	                                                                                            language={
	                                                                                                detectedLanguage.prism
	                                                                                            }
	                                                                                            style={
	                                                                                                syntaxTheme
	                                                                                            }
	                                                                                            customStyle={{
	                                                                                                margin: 0,
	                                                                                                background:
	                                                                                                    "transparent",
	                                                                                                padding:
	                                                                                                    "44px 16px 16px 16px",
	                                                                                                fontSize:
	                                                                                                    "0.95rem",
	                                                                                                lineHeight:
	                                                                                                    "1.75rem",
	                                                                                            }}
	                                                                                            codeTagProps={{
	                                                                                                style: {
	                                                                                                    fontFamily:
	                                                                                                        "var(--font-app-mono)",
	                                                                                                },
	                                                                                            }}
	                                                                                        >
	                                                                                            {
	                                                                                                codeText
	                                                                                            }
	                                                                                        </SyntaxHighlighter>
	                                                                                    </div>
	                                                                                );
	                                                                            })()
	                                                                        ),
                                                                }}
                                                            >
                                                                {formatLaTeX(
                                                                    message.content,
                                                                )}
                                                            </ReactMarkdown>
                                                        </div>
                                                    ) : thinkingState?.isStreaming ? (
                                                        <div className="text-base font-medium text-[var(--chat-text-muted)]">
                                                            <ThinkingIndicator />
                                                        </div>
                                                    ) : null
                                                ) : (
                                                    <div className="whitespace-pre-wrap">
                                                        {message.content}
                                                    </div>
                                                )}
                                            </div>
                                            {message.content && (
                                                <button
                                                    type="button"
                                                    onClick={() =>
                                                        copyText(
                                                            message.content,
                                                            "message",
                                                            message.id,
                                                        )
                                                    }
                                                    className="absolute -bottom-6 left-0 text-[var(--chat-text-muted)] opacity-0 transition group-hover:opacity-100 hover:text-[var(--chat-accent)]"
                                                    aria-label={
                                                        copiedMessageId ===
                                                        message.id
                                                            ? "Đã copy"
                                                            : "Copy message"
                                                    }
                                                >
                                                    {copiedMessageId ===
                                                    message.id ? (
                                                        <OaiCheck className="size-5" />
                                                    ) : (
                                                        <Copy className="size-5" />
                                                    )}
                                                </button>
                                            )}
                                        </div>

                                    </div>
                                );
                            })}
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
                            <img
                                src="/edutrust.png"
                                alt="EduTrust logo"
                                className="h-12 w-12 object-contain"
                            />

                            <div className="min-w-0 flex-1 origin-right transition-all duration-300 ease-in-out">
                                <p className="text-xl font-semibold tracking-[-0.03em] text-[var(--chat-sidebar-text)]">
                                    EduTrust AI
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
                                            <div
                                                key={conversation.conversation_id}
                                                className={`group relative w-full rounded-[1.5rem] transition ${
                                                    isActive
                                                        ? "bg-[var(--chat-button-bg)]"
                                                        : "hover:bg-[var(--chat-surface)]"
                                                }`}
                                            >
                                                <button
                                                    type="button"
                                                    onClick={() =>
                                                        handleSelectConversation(
                                                            conversation.conversation_id,
                                                        )
                                                    }
                                                    className="w-full rounded-[1.5rem] px-3 py-3 pr-10 text-left"
                                                >
                                                    <p className="line-clamp-1 text-[1.05rem] font-medium text-[var(--chat-sidebar-text)]">
                                                        {stripMarkdownForPreview(
                                                            normalizeConversationTitle(
                                                                conversation.title,
                                                            ),
                                                        )}
                                                    </p>
                                                    <p className="mt-1 line-clamp-1 text-sm text-[var(--chat-text-muted)]">
                                                        {stripMarkdownForPreview(
                                                            conversation.preview,
                                                        ) || "Chưa có tin nhắn"}
                                                    </p>
                                                </button>
                                                <button
                                                    type="button"
                                                    onClick={(event) => {
                                                        event.preventDefault();
                                                        event.stopPropagation();
                                                        setPendingDeleteConversation(
                                                            {
                                                                id: conversation.conversation_id,
                                                                title: conversation.title,
                                                            },
                                                        );
                                                    }}
                                                    className="absolute right-2 top-1/2 inline-flex h-8 w-8 -translate-y-1/2 items-center justify-center rounded-xl text-[var(--chat-text-muted)] opacity-0 transition hover:text-[var(--chat-text)] group-hover:opacity-100 group-focus-within:opacity-100 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--chat-border)]"
                                                    aria-label="Xóa hội thoại"
                                                    title="Xóa hội thoại"
                                                >
                                                    <Delete className="size-4" />
                                                </button>
                                            </div>
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
