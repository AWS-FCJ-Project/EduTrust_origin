import { useEffect, useMemo, useRef, useState } from "react";
import type { KeyboardEvent } from "react";

type Message = {
  id: string;
  role: "user" | "assistant";
  content: string;
  createdAt: number;
};

type BackendStatus = "checking" | "online" | "offline";
type RunPhase = "idle" | "planning" | "tools" | "synthesizing";

const createId = () => {
  if (typeof crypto !== "undefined" && "randomUUID" in crypto) {
    return crypto.randomUUID();
  }
  return `msg-${Date.now()}-${Math.random().toString(16).slice(2)}`;
};

const normalizeBaseUrl = (value: string) => value.replace(/\/+$/, "");

const buildEndpoint = (baseUrl: string) =>
  `${normalizeBaseUrl(baseUrl)}/unified-agent/ask`;

const DEFAULT_API_URL = "http://localhost:8000";

function App() {
  const [conversationId, setConversationId] = useState("");
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState<Message[]>([]);
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [backendStatus, setBackendStatus] =
    useState<BackendStatus>("checking");
  const [runPhase, setRunPhase] = useState<RunPhase>("idle");
  const [slowNotice, setSlowNotice] = useState(false);

  const endRef = useRef<HTMLDivElement | null>(null);

  const apiUrl = useMemo(() => {
    const envUrl = import.meta.env.VITE_API_URL as string | undefined;
    return envUrl && envUrl.trim().length > 0 ? envUrl : DEFAULT_API_URL;
  }, []);

  const endpoint = useMemo(() => buildEndpoint(apiUrl), [apiUrl]);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [messages, pending]);

  useEffect(() => {
    if (!pending) {
      setRunPhase("idle");
      setSlowNotice(false);
      return;
    }

    setRunPhase("planning");
    setSlowNotice(false);

    const toolTimer = window.setTimeout(() => {
      setRunPhase("tools");
    }, 2000);

    const synthTimer = window.setTimeout(() => {
      setRunPhase("synthesizing");
    }, 6500);

    const slowTimer = window.setTimeout(() => {
      setSlowNotice(true);
    }, 12000);

    return () => {
      window.clearTimeout(toolTimer);
      window.clearTimeout(synthTimer);
      window.clearTimeout(slowTimer);
    };
  }, [pending]);

  useEffect(() => {
    let mounted = true;

    const checkBackend = async () => {
      try {
        await fetch(apiUrl, {
          method: "GET",
          mode: "no-cors",
          cache: "no-store",
        });
        if (!mounted) return;
        setBackendStatus("online");
      } catch (err) {
        if (!mounted) return;
        setBackendStatus("offline");
      }
    };

    checkBackend();
    const interval = window.setInterval(checkBackend, 15000);

    return () => {
      mounted = false;
      window.clearInterval(interval);
    };
  }, [apiUrl]);

  const canSend = input.trim().length > 0 && !pending;

  const backendLabel = {
    checking: "Connecting",
    online: "Backend online",
    offline: "Backend offline",
  }[backendStatus];

  const phaseLabel = {
    idle: "Idle",
    planning: "Planning",
    tools: "Calling tools",
    synthesizing: "Synthesizing answer",
  }[runPhase];

  const handleSend = async () => {
    if (pending) return;

    const question = input.trim();
    if (question.length === 0) return;

    let activeConversationId = conversationId.trim();
    if (activeConversationId.length === 0) {
      activeConversationId = `conv-${Date.now()}`;
      setConversationId(activeConversationId);
    }

    const userMessage: Message = {
      id: createId(),
      role: "user",
      content: question,
      createdAt: Date.now(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setPending(true);
    setError(null);

    try {
      const response = await fetch(endpoint, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          question,
          conversation_id: activeConversationId,
        }),
      });

      if (!response.ok) {
        const detail = await response.text();
        throw new Error(detail || `Request failed (${response.status}).`);
      }

      const data = (await response.json()) as {
        answer: string;
        conversation_id: string;
      };

      const assistantMessage: Message = {
        id: createId(),
        role: "assistant",
        content: data.answer,
        createdAt: Date.now(),
      };

      setMessages((prev) => [...prev, assistantMessage]);
    } catch (err) {
      const message = err instanceof Error ? err.message : "Request failed.";
      setError(message);
    } finally {
      setPending(false);
    }
  };

  const handleKeyDown = (event: KeyboardEvent<HTMLTextAreaElement>) => {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      if (canSend) {
        handleSend();
      }
    }
  };

  const handleReset = () => {
    setMessages([]);
    setInput("");
    setError(null);
    setPending(false);
    setConversationId("");
  };

  return (
    <div className="app">
      <div className="glow" aria-hidden="true" />
      <div className="noise" aria-hidden="true" />

      <div className="layout">
        <div className="content">
          <header className="topbar">
            <div>
              <p className="eyebrow">New thread</p>
              <h1>Let&apos;s build unified agent UI</h1>
            </div>
            <div className="status-group">
              <div className={`status-pill ${backendStatus}`}>
                <span className="status-dot" />
                <span>{backendLabel}</span>
              </div>
              <div className={`status-pill ${runPhase}`}>
                <span className="status-dot" />
                <span>{phaseLabel}</span>
              </div>
              <div className={`status-pill ${pending ? "busy" : "ready"}`}>
                <span className="status-dot" />
                <span>{pending ? "Thinking" : "Ready"}</span>
              </div>
            </div>
          </header>

          <main className="chat-shell">
            <section className="run-state">
              <div className={`run-step ${runPhase === "planning" && pending ? "active" : ""}`}>
                <span className="run-dot" />
                <span>Planning</span>
              </div>
              <div className={`run-step ${runPhase === "tools" && pending ? "active" : ""}`}>
                <span className="run-dot" />
                <span>Tool calls</span>
              </div>
              <div
                className={`run-step ${
                  runPhase === "synthesizing" && pending ? "active" : ""
                }`}
              >
                <span className="run-dot" />
                <span>Final answer</span>
              </div>
              {slowNotice ? (
                <div className="run-note">Waiting longer than usual...</div>
              ) : null}
            </section>

            <section className="control-row">
              <label className="field">
                <span>Conversation ID</span>
                <input
                  type="text"
                  value={conversationId}
                  onChange={(event) => setConversationId(event.target.value)}
                  placeholder="e.g. demo-convo-001"
                />
              </label>
              <div className="controls">
                <button type="button" className="ghost" onClick={handleReset}>
                  New chat
                </button>
              </div>
            </section>

            <section className="messages" aria-live="polite">
              {messages.length === 0 && !pending ? (
                <div className="empty">
                  <h2>Start a new thread</h2>
                  <p>
                    Enter a conversation id, then send a message to the unified
                    agent.
                  </p>
                </div>
              ) : null}

              {messages.map((message) => (
                <article
                  key={message.id}
                  className={`message ${message.role}`}
                >
                  <div className="bubble">
                    <p>{message.content}</p>
                  </div>
                  <span className="timestamp">
                    {new Date(message.createdAt).toLocaleTimeString([], {
                      hour: "2-digit",
                      minute: "2-digit",
                    })}
                  </span>
                </article>
              ))}

              {pending ? (
                <article className="message assistant">
                  <div className="bubble typing">
                    <span className="pulse" />
                    <span className="pulse" />
                    <span className="pulse" />
                  </div>
                </article>
              ) : null}
              <div ref={endRef} />
            </section>

            <section className="composer">
              <div className="composer-inner">
                <textarea
                  value={input}
                  onChange={(event) => setInput(event.target.value)}
                  onKeyDown={handleKeyDown}
                  placeholder="Ask the unified agent…"
                  rows={3}
                />
                <button
                  type="button"
                  onClick={handleSend}
                  disabled={!canSend}
                >
                  Send
                </button>
              </div>
              <div className="meta">
                <span>Shift + Enter for a new line.</span>
                {error ? <span className="error">{error}</span> : null}
              </div>
            </section>
          </main>
        </div>
      </div>
    </div>
  );
}

export default App;
