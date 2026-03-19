import { useEffect, useMemo, useRef, useState } from "react";
import type { KeyboardEvent } from "react";

type Message = {
  id: string;
  role: "user" | "assistant";
  content: string;
  createdAt: number;
};

type StreamEvent =
  | { type: "text_delta"; content: string }
  | { type: "tool_call"; content: unknown }
  | { type: "tool_result"; content: unknown }
  | { type: "error"; content: string }
  | { type: "complete" };

type ToolEvent = {
  id: string;
  type: "tool_call" | "tool_result";
  content: unknown;
  createdAt: number;
};

type BackendStatus = "checking" | "online" | "offline";
type RunPhase = "idle" | "planning" | "tools" | "synthesizing";

const extractSseEvents = (buffer: string) => {
  const events: string[] = [];
  let rest = buffer;
  while (true) {
    const index = rest.indexOf("\n\n");
    if (index === -1) break;
    events.push(rest.slice(0, index));
    rest = rest.slice(index + 2);
  }
  return { events, rest };
};

const extractSseData = (rawEvent: string) => {
  const dataLines = rawEvent
    .split("\n")
    .map((line) => line.trimEnd())
    .filter((line) => line.startsWith("data:"));
  if (dataLines.length === 0) return null;
  return dataLines.map((line) => line.slice(5).trimStart()).join("\n");
};

const toErrorMessage = (err: unknown) => {
  if (err instanceof DOMException && err.name === "AbortError") {
    return "Streaming stopped.";
  }
  return err instanceof Error ? err.message : "Request failed.";
};

function RunState({
  runPhase,
  pending,
  slowNotice,
}: {
  runPhase: RunPhase;
  pending: boolean;
  slowNotice: boolean;
}) {
  return (
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
      {slowNotice ? <div className="run-note">Waiting longer than usual...</div> : null}
    </section>
  );
}

function ToolEventsPanel({ toolEvents }: { toolEvents: ToolEvent[] }) {
  if (toolEvents.length === 0) return null;

  return (
    <section className="tool-events">
      <header>
        <h3>Tool events</h3>
        <span>{toolEvents.length}</span>
      </header>
      <div className="tool-events-list">
        {toolEvents.map((eventItem) => (
          <article key={eventItem.id} className={`tool-event ${eventItem.type}`}>
            <div className="tool-event-head">
              <strong>{eventItem.type}</strong>
              <span>
                {new Date(eventItem.createdAt).toLocaleTimeString([], {
                  hour: "2-digit",
                  minute: "2-digit",
                  second: "2-digit",
                })}
              </span>
            </div>
            <pre>{JSON.stringify(eventItem.content, null, 2)}</pre>
          </article>
        ))}
      </div>
    </section>
  );
}

const createId = () => {
  if (typeof crypto !== "undefined" && "randomUUID" in crypto) {
    return crypto.randomUUID();
  }
  return `msg-${Date.now()}-${Math.random().toString(16).slice(2)}`;
};

const normalizeBaseUrl = (value: string) => value.replace(/\/+$/, "");

const buildEndpoint = (baseUrl: string, path: string) =>
  `${normalizeBaseUrl(baseUrl)}${path}`;

const DEFAULT_API_URL = "http://localhost:8000";

function App() {
  const [conversationId, setConversationId] = useState("");
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState<Message[]>([]);
  const [toolEvents, setToolEvents] = useState<ToolEvent[]>([]);
  const [pending, setPending] = useState(false);
  const [useStreaming, setUseStreaming] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [backendStatus, setBackendStatus] =
    useState<BackendStatus>("checking");
  const [runPhase, setRunPhase] = useState<RunPhase>("idle");
  const [slowNotice, setSlowNotice] = useState(false);

  const endRef = useRef<HTMLDivElement | null>(null);
  const abortRef = useRef<AbortController | null>(null);

  const apiUrl = useMemo(() => {
    const envUrl = import.meta.env.VITE_API_URL as string | undefined;
    return envUrl && envUrl.trim().length > 0 ? envUrl : DEFAULT_API_URL;
  }, []);

  const askEndpoint = useMemo(
    () => buildEndpoint(apiUrl, "/unified-agent/ask"),
    [apiUrl],
  );
  const streamEndpoint = useMemo(
    () => buildEndpoint(apiUrl, "/unified-agent/ask/streaming"),
    [apiUrl],
  );

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

  const stopStreaming = () => {
    abortRef.current?.abort();
    abortRef.current = null;
  };

  const appendAssistantDelta = (
    assistantId: string,
    delta: string,
    createdAt: number,
  ) => {
    if (!delta) return;

    setMessages((prev) => {
      const index = prev.findIndex((message) => message.id === assistantId);
      if (index === -1) {
        return [
          ...prev,
          { id: assistantId, role: "assistant", content: delta, createdAt },
        ];
      }

      const next = [...prev];
      const existing = next[index];
      next[index] = { ...existing, content: existing.content + delta };
      return next;
    });
  };

  const startNonStreamingRequest = async (
    question: string,
    activeConversationId: string,
  ) => {
    const response = await fetch(askEndpoint, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question, conversation_id: activeConversationId }),
    });

    if (!response.ok) {
      const detail = await response.text();
      throw new Error(detail || `Request failed (${response.status}).`);
    }

    const data = (await response.json()) as {
      answer: string;
      conversation_id: string;
    };

    setMessages((prev) => [
      ...prev,
      {
        id: createId(),
        role: "assistant",
        content: data.answer,
        createdAt: Date.now(),
      },
    ]);
  };

  const startStreamingRequest = async (
    question: string,
    activeConversationId: string,
    assistantId: string,
    assistantCreatedAt: number,
  ) => {
    const abortController = new AbortController();
    abortRef.current = abortController;
    setToolEvents([]);

    const response = await fetch(streamEndpoint, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      signal: abortController.signal,
      body: JSON.stringify({ question, conversation_id: activeConversationId }),
    });

    if (!response.ok) {
      const detail = await response.text();
      throw new Error(detail || `Request failed (${response.status}).`);
    }

    const reader = response.body?.getReader();
    if (!reader) {
      throw new Error("Streaming is not supported by this browser.");
    }

    const decoder = new TextDecoder();
    let buffer = "";
    let completed = false;

    while (!completed) {
      const { value, done } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const { events, rest } = extractSseEvents(buffer);
      buffer = rest;

      for (const rawEvent of events) {
        const data = extractSseData(rawEvent);
        if (!data) continue;

        let parsed: StreamEvent | null = null;
        try {
          parsed = JSON.parse(data) as StreamEvent;
        } catch {
          continue;
        }

        switch (parsed.type) {
          case "text_delta": {
            const delta = typeof parsed.content === "string" ? parsed.content : "";
            appendAssistantDelta(assistantId, delta, assistantCreatedAt);
            break;
          }
          case "tool_call":
          case "tool_result": {
            setToolEvents((prev) => [
              ...prev,
              {
                id: createId(),
                type: parsed.type,
                content: parsed.content,
                createdAt: Date.now(),
              },
            ]);
            break;
          }
          case "error": {
            setError(parsed.content || "Streaming error.");
            break;
          }
          case "complete": {
            completed = true;
            break;
          }
        }
      }
    }
  };

  const handleSend = async () => {
    if (pending) return;

    const question = input.trim();
    if (!question) return;

    let activeConversationId = conversationId.trim();
    if (!activeConversationId) {
      activeConversationId = `conv-${Date.now()}`;
      setConversationId(activeConversationId);
    }

    setMessages((prev) => [
      ...prev,
      { id: createId(), role: "user", content: question, createdAt: Date.now() },
    ]);
    setInput("");
    setPending(true);
    setError(null);
    abortRef.current?.abort();
    abortRef.current = null;

    try {
      if (!useStreaming) {
        await startNonStreamingRequest(question, activeConversationId);
        return;
      }

      const assistantId = createId();
      const assistantCreatedAt = Date.now();
      setMessages((prev) => [
        ...prev,
        {
          id: assistantId,
          role: "assistant",
          content: "",
          createdAt: assistantCreatedAt,
        },
      ]);

      await startStreamingRequest(
        question,
        activeConversationId,
        assistantId,
        assistantCreatedAt,
      );
    } catch (err) {
      setError(toErrorMessage(err));
    } finally {
      setPending(false);
      abortRef.current = null;
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
    stopStreaming();
    setMessages([]);
    setToolEvents([]);
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
            <RunState runPhase={runPhase} pending={pending} slowNotice={slowNotice} />

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
              <label className="field toggle">
                <span>Mode</span>
                <div className="toggle-row">
                  <input
                    id="streaming"
                    type="checkbox"
                    checked={useStreaming}
                    disabled={pending}
                    onChange={(event) => setUseStreaming(event.target.checked)}
                  />
                  <label htmlFor="streaming">Streaming</label>
                </div>
              </label>
              <div className="controls">
                {pending && useStreaming ? (
                  <button type="button" className="ghost" onClick={stopStreaming}>
                    Stop
                  </button>
                ) : null}
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

            {useStreaming ? <ToolEventsPanel toolEvents={toolEvents} /> : null}

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
