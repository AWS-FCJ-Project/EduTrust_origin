import { useEffect, useRef, useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkMath from "remark-math";
import rehypeKatex from "rehype-katex";
import "katex/dist/katex.min.css";

type Message = {
  id: string;
  role: "user" | "assistant";
  content: string;
};

const DEFAULT_API_URL = "http://localhost:8000";

const FormattedMessage = ({ content }: { content: string }) => {
  return (
    <ReactMarkdown
      remarkPlugins={[remarkMath]}
      rehypePlugins={[rehypeKatex]}
      components={{
        p: ({ children }) => <p style={{ margin: 0 }}>{children}</p>,
      }}
    >
      {content}
    </ReactMarkdown>
  );
};

const NotificationsWidget = ({ navigate }: { navigate: (to: string) => void }) => {
  const announcements = [
    { id: 1, title: "Lịch thi học kỳ 2 chính thức", date: "17/03/2026", type: "Urgent" },
    { id: 2, title: "Thông báo nghỉ lễ Giỗ tổ Hùng Vương", date: "15/03/2026", type: "Info" },
    { id: 3, title: "Bắt đầu đăng ký các câu lạc bộ hè", date: "10/03/2026", type: "General" },
    { id: 4, title: "Hắc chương trình học bổng Google Cloud", date: "05/03/2026", type: "Scholarship" },
  ];

  return (
    <div className="home-widget-card notifications-widget">
      <div className="widget-header">
        <h3>Thông báo mới nhất</h3>
        <a href="#notifications" onClick={() => navigate('#notifications')}>Xem thêm</a>
      </div>
      <div className="notifications-list">
        {announcements.slice(0, 3).map(n => (
          <div key={n.id} className="notification-item">
            <span className={`type-badge ${n.type.toLowerCase()}`}>{n.type}</span>
            <div className="notif-content">
              <p>{n.title}</p>
              <small>{n.date}</small>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

const AssignmentsWidget = () => {
  const assignments = [
    { id: 1, subject: "Toán học", title: "Giải bài tập tích phân nâng cao", deadline: "20/03/2026", status: "Pending" },
    { id: 2, subject: "Vật lý", title: "Báo cáo thí nghiệm Quang hình", deadline: "22/03/2026", status: "In Progress" },
  ];

  return (
    <div className="home-widget-card assignments-widget">
      <div className="widget-header">
        <h3>Bài tập chưa hoàn thành</h3>
      </div>
      <div className="assignments-list">
        {assignments.map(a => (
          <div key={a.id} className="assignment-item">
            <div className="assignment-info">
              <span className="subject-name">{a.subject}</span>
              <p className="assignment-title">{a.title}</p>
            </div>
            <div className="assignment-meta">
              <span className={`status-label ${a.status.replace(' ', '-').toLowerCase()}`}>{a.status}</span>
              <small>Hạn: {a.deadline}</small>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

const TranscriptTable = ({ semester }: { semester: string }) => {
  const grades = [
    { subject: "Toán học", miệng: "10", p15: ["10", "10"], p1t: ["10", "10"], hk: "8.8", tbm: "9.6" },
    { subject: "Vật lí", miệng: "10", p15: ["10", "10"], p1t: ["10"], hk: "10", tbm: "10.0" },
    { subject: "Hóa học", miệng: ["10", "10"], p15: ["10"], p1t: ["10"], hk: "9.8", tbm: "9.9" },
    { subject: "Sinh học", miệng: "9", p15: ["10"], p1t: ["10"], hk: "6.8", tbm: "8.5" },
    { subject: "Tin học", miệng: "", p15: [], p1t: [], hk: "", tbm: "" },
    { subject: "Ngữ văn", miệng: "10", p15: ["10", "10", "9"], p1t: ["8.5", "8", "8"], hk: "8.5", tbm: "8.7" },
  ];

  if (semester === "Kỳ 1") return <div className="no-data-msg">Chưa cập nhật</div>;

  return (
    <div className="transcript-wrapper">
      <table className="transcript-table">
        <thead>
          <tr>
            <th>Môn học</th>
            <th>Điểm miệng</th>
            <th>Điểm 15 phút</th>
            <th>Điểm 1 tiết</th>
            <th>Học kỳ</th>
            <th>TBM</th>
          </tr>
        </thead>
        <tbody>
          {grades.map((g, idx) => (
            <tr key={idx} className={!g.tbm ? "empty-row" : ""}>
              <td className="subject-col">{g.subject}</td>
              <td>{Array.isArray(g.miệng) ? g.miệng.join(' ') : g.miệng}</td>
              <td>{g.p15.join(' ')}</td>
              <td>{g.p1t.join(' ')}</td>
              <td>{g.hk}</td>
              <td className="tbm-col">{g.tbm}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};
const TimetableWidget = () => {
  const days = ["Thứ 2", "Thứ 3", "Thứ 4", "Thứ 5", "Thứ 6", "Thứ 7"];
  const schedule = [
    { period: 1, subjects: ["Toán", "Văn", "Lý", "Hóa", "Toán", "Anh"] },
    { period: 2, subjects: ["Toán", "Văn", "Lý", "Hóa", "Sinh", "Anh"] },
    { period: 3, subjects: ["Anh", "Sử", "Địa", "Toán", "Văn", "GDCD"] },
    { period: 4, subjects: ["Anh", "Tin", "CN", "Toán", "Văn", "Thể dục"] },
  ];

  return (
    <div className="home-widget-card timetable-widget">
      <div className="widget-header">
        <h3>Thời khóa biểu tuần</h3>
      </div>
      <div className="timetable-wrapper">
        <table className="timetable-table">
          <thead>
            <tr>
              <th>Tiết</th>
              {days.map(d => <th key={d}>{d}</th>)}
            </tr>
          </thead>
          <tbody>
            {schedule.map(s => (
              <tr key={s.period}>
                <td className="period-col">{s.period}</td>
                {s.subjects.map((sub, idx) => <td key={idx}>{sub}</td>)}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

// ─── Question types ───────────────────────────────────────────
type ParsedQuestion = {
  number: number;
  question: string;
  options: string[];        // A, B, C, D lines if MCQ
  correctAnswer: string;    // line starting with "Đáp án" / "Answer"
  guideLines: string[];     // remaining lines (essay guide)
};

function parseQuestions(raw: string): ParsedQuestion[] {
  // Split on "Câu X" / numbered patterns like "1." "**1.**"
  const blocks = raw
    .split(/\n(?=(?:\*{0,2}Câu\s*\d+|\*{0,2}\d+[\.\)])\*{0,2})/i)
    .map(b => b.trim())
    .filter(Boolean);

  return blocks.map((block, idx) => {
    const lines = block.split('\n').map(l => l.trim()).filter(Boolean);
    // First line = question header + question text (sometimes split across next line)
    const questionLine = lines[0].replace(/^\*{0,2}(?:Câu\s*)?\d+[\.\)]\*{0,2}\s*/i, '').trim();
    const rest = lines.slice(1);

    const options: string[] = [];
    const guideLines: string[] = [];
    let correctAnswer = '';
    let questionText = questionLine;

    // If question text is empty (only header on line 0), grab line 1 as question
    if (!questionText && rest.length) {
      questionText = rest.shift()!;
    }

    for (const line of rest) {
      if (/^[A-D][\.\)]/i.test(line)) {
        options.push(line);
      } else if (/^(\*{0,2})(Đáp án|Answer|Correct|Gợi ý đáp án)/i.test(line)) {
        correctAnswer = line.replace(/^\*+|\*+$/g, '').trim();
      } else {
        guideLines.push(line.replace(/^\*+|\*+$/g, '').trim());
      }
    }

    return { number: idx + 1, question: questionText, options, correctAnswer, guideLines };
  });
}

// ─── CreateExercise sub-component ─────────────────────────────
const CreateExercise = ({ onStartPractice }: { onStartPractice: (qs: ParsedQuestion[]) => void }) => {
  const [step, setStep] = useState<'select' | 'ai-input' | 'preview'>('select');
  const [prompt, setPrompt] = useState('');
  const [numQuestions, setNumQuestions] = useState(5);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [questions, setQuestions] = useState<ParsedQuestion[]>([]);

  const handleGenerate = async () => {
    if (!prompt.trim()) return;
    setLoading(true);
    setError('');
    try {
      const res = await fetch(`${DEFAULT_API_URL}/practice/generate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prompt: prompt.trim(), num_questions: numQuestions }),
      });
      if (!res.ok) throw new Error('Server error');
      const data = await res.json();
      const parsed = parseQuestions(data.raw);
      setQuestions(parsed.length ? parsed : [{ number: 1, question: data.raw, options: [], correctAnswer: '', guideLines: [] }]);
      setStep('preview');
    } catch (e) {
      setError('Có lỗi xảy ra khi tạo câu hỏi. Vui lòng thử lại.');
    } finally {
      setLoading(false);
    }
  };

  if (step === 'select') return (
    <div className="create-step">
      <h2 className="create-step-title">Tạo bài tập</h2>
      <p className="create-step-sub">Chọn cách bạn muốn tạo bài tập</p>
      <div className="create-method-grid">
        <button className="create-method-card ai" onClick={() => setStep('ai-input')}>
          <span className="method-icon">🤖</span>
          <strong>Tạo bởi AI</strong>
          <span>Mô tả chủ đề, AI sẽ sinh câu hỏi tự động</span>
        </button>
        <button className="create-method-card manual" disabled>
          <span className="method-icon">✏️</span>
          <strong>Tạo thủ công</strong>
          <span>Tự soạn câu hỏi theo ý muốn</span>
          <small className="coming-soon">Sắp ra mắt</small>
        </button>
      </div>
    </div>
  );

  if (step === 'ai-input') return (
    <div className="create-step">
      <button className="back-btn" onClick={() => setStep('select')}>
        ← Quay lại
      </button>
      <h2 className="create-step-title">Tạo câu hỏi bằng AI</h2>
      <p className="create-step-sub">Mô tả dạng bài, chủ đề, mức độ khó bạn muốn.</p>
      <div className="ai-form">
        <textarea
          className="ai-prompt-input"
          placeholder="Ví dụ: 5 câu hỏi trắc nghiệm về định luật Newton cho học sinh lớp 10..."
          rows={5}
          value={prompt}
          onChange={e => setPrompt(e.target.value)}
        />
        <div className="ai-form-row">
          <label>Số câu hỏi</label>
          <input
            type="number"
            min={1}
            max={20}
            value={numQuestions}
            onChange={e => setNumQuestions(Number(e.target.value))}
            className="num-input"
          />
        </div>
        {error && <p className="ai-error">{error}</p>}
        <button
          className="btn-generate"
          onClick={handleGenerate}
          disabled={loading || !prompt.trim()}
        >
          {loading ? <span className="btn-spinner" /> : '✨ Tạo câu hỏi'}
        </button>
      </div>
    </div>
  );

  // preview
  return (
    <div className="create-step">
      <div className="preview-header">
        <button className="back-btn" onClick={() => setStep('ai-input')}>← Chỉnh sửa</button>
        <button className="btn-start-practice" onClick={() => onStartPractice(questions)}>
          Bắt đầu luyện tập →
        </button>
      </div>
      <h2 className="create-step-title">Xem trước bài tập</h2>
      <p className="create-step-sub">{questions.length} câu hỏi được tạo</p>
      <div className="question-list">
        {questions.map(q => (
          <div key={q.number} className="question-card">
            <div className="q-number">Câu {q.number}</div>
            <p className="q-text">{q.question}</p>
            {q.options.length > 0 && (
              <ul className="q-options">
                {q.options.map((opt, i) => <li key={i}>{opt}</li>)}
              </ul>
            )}
            {q.correctAnswer && (
              <div className="q-answer">
                <span className="answer-label">✔ Đáp án:</span> {q.correctAnswer.replace(/^Đáp án[:\s]*/i, '').replace(/^Answer[:\s]*/i, '')}
              </div>
            )}
            {q.guideLines.length > 0 && (
              <div className="q-guide">
                {q.guideLines.map((l, i) => <p key={i}>{l}</p>)}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
};


const PracticeView = () => {
  const menuItems = [
    { id: 'create', label: 'Tạo bài tập' },
    { id: 'practice', label: 'Luyện tập' },
    { id: 'history', label: 'Lịch sử' },
    { id: 'flashcard', label: 'Flashcard' },
  ];

  const [activeMenu, setActiveMenu] = useState('create');
  const [displayedMenu, setDisplayedMenu] = useState('create');
  const [isExiting, setIsExiting] = useState(false);
  const [slideDir, setSlideDir] = useState<'down' | 'up' | 'none'>('none');
  const [practiceQuestions, setPracticeQuestions] = useState<ParsedQuestion[]>([]);

  const handleMenuChange = (newId: string) => {
    if (newId === activeMenu || isExiting) return;
    const ids = menuItems.map(m => m.id);
    const dir: 'down' | 'up' = ids.indexOf(newId) > ids.indexOf(activeMenu) ? 'down' : 'up';
    setSlideDir(dir);
    setActiveMenu(newId);
    setIsExiting(true);
    setTimeout(() => {
      setDisplayedMenu(newId);
      setIsExiting(false);
    }, 280);
  };

  const handleStartPractice = (qs: ParsedQuestion[]) => {
    setPracticeQuestions(qs);
    handleMenuChange('practice');
  };

  const contentClass = isExiting
    ? (slideDir === 'down' ? 'practice-exit-up' : 'practice-exit-down')
    : (slideDir === 'down' ? 'practice-enter-below' : slideDir === 'up' ? 'practice-enter-above' : '');

  const renderContent = () => {
    switch (displayedMenu) {
      case 'create':
        return <CreateExercise onStartPractice={handleStartPractice} />;
      case 'practice':
        return (
          <div className="content-placeholder">
            <div className="empty-practice-state">
              <div className="empty-icon">{practiceQuestions.length ? '🎯' : '✨'}</div>
              <h2>{practiceQuestions.length ? `Luyện tập – ${practiceQuestions.length} câu` : 'Luyện tập'}</h2>
              <p>{practiceQuestions.length ? 'Bài tập của bạn đã sẵn sàng!' : 'Tạo bài tập trước để bắt đầu luyện tập.'}</p>
            </div>
          </div>
        );
      default:
        return (
          <div className="content-placeholder">
            <div className="empty-practice-state">
              <div className="empty-icon">✨</div>
              <h2>{menuItems.find(m => m.id === displayedMenu)?.label}</h2>
              <p>Module này đang được phát triển.</p>
            </div>
          </div>
        );
    }
  };

  return (
    <div className="practice-tab-view">
      <div className="practice-container">
        <div className="practice-sidebar">
          <div className="sidebar-menu">
            {menuItems.map(item => (
              <button
                key={item.id}
                className={`practice-menu-item ${activeMenu === item.id ? 'active' : ''}`}
                onClick={() => handleMenuChange(item.id)}
              >
                {item.label}
              </button>
            ))}
          </div>
        </div>

        <div className="practice-content">
          <div key={displayedMenu} className={`practice-content-anim ${contentClass}`}>
            {renderContent()}
          </div>
        </div>
      </div>
    </div>
  );
};

const ChatbotView = ({
  messages,
  input,
  setInput,
  handleSend,
  pending,
  chatEndRef
}: {
  messages: Message[],
  input: string,
  setInput: (val: string) => void,
  handleSend: () => void,
  pending: boolean,
  chatEndRef: any
}) => {
  const sessions = [
    { id: 1, title: "Giải bài tập Tích phân", date: "Hôm nay" },
    { id: 2, title: "Luyện nghe Tiếng Anh", date: "Hôm qua" },
    { id: 3, title: "Tìm hiểu về AI", date: "15/03" },
    { id: 4, title: "Ôn tập Hóa hữu cơ", date: "12/03" },
  ];

  return (
    <div className="chatbot-tab-view">
      <div className="chatbot-container">
        {/* Persistent Sidebar */}
        <div className="chatbot-sidebar">
          <div className="sidebar-header">
            <h3>Hội thoại</h3>
          </div>
          <div className="sidebar-sessions">
            <button className="new-chat-btn">+ Đoạn chat mới</button>
            {sessions.map(s => (
              <div key={s.id} className="session-item">
                <span className="session-icon">💬</span>
                <div className="session-info">
                  <p className="session-title">{s.title}</p>
                  <small className="session-date">{s.date}</small>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Centered Chat Frame */}
        <div className="chatbot-main-frame">
          <div className="chatbot-messages">
            {messages.length === 0 && (
              <div className="chatbot-empty-state">
                <div className="bot-icon">🤖</div>
                <h2>AI Tutor is ready to help</h2>
                <p>Ask anything about your courses, exams, or homework.</p>
              </div>
            )}
            {messages.map(m => (
              <div key={m.id} className={`chat-message ${m.role}`}>
                <div className="message-bubble">
                  <FormattedMessage content={m.content} />
                </div>
              </div>
            ))}
            {pending && (
              <div className="chat-message assistant thinking">
                <div className="message-bubble">
                  <span className="dot">.</span><span className="dot">.</span><span className="dot">.</span>
                </div>
              </div>
            )}
            <div ref={chatEndRef} />
          </div>

          <div className="chatbot-input-container">
            <div className="chat-input-pill">
              <textarea
                placeholder="Ask me anything..."
                rows={1}
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && !e.shiftKey && (e.preventDefault(), handleSend())}
              />
              <button className="btn-send" onClick={handleSend} disabled={pending || !input.trim()}>
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><line x1="22" y1="2" x2="11" y2="13"></line><polygon points="22 2 15 22 11 13 2 9 22 2"></polygon></svg>
              </button>
            </div>
          </div>
        </div>

        {/* Balancing Spacer (keeps chat frame centered) */}
        <div className="chatbot-sidebar-spacer"></div>
      </div>
    </div>
  );
};

const FloatingCard = ({
  label,
  title,
  description,
  className = ""
}: {
  label: string;
  title: string;
  description: string;
  className?: string;
}) => (
  <div className={`floating-card ${className}`}>
    <span className="card-label">{label}</span>
    <h2 className="card-title">{title}</h2>
    <p className="card-description">{description}</p>
  </div>
);

function App() {
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState<Message[]>([]);
  const [pending, setPending] = useState(false);
  const [showChat, setShowChat] = useState(false);
  const [scrollY, setScrollY] = useState(0);
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [showProfileMenu, setShowProfileMenu] = useState(false);
  const [activeTab, setActiveTab] = useState("Home");
  const [direction, setDirection] = useState<"left" | "right" | "none">("none");
  const [isTransitioning, setIsTransitioning] = useState(false);

  const chatEndRef = useRef<HTMLDivElement | null>(null);

  const handleTabChange = (newTab: string) => {
    const tabs = ["Home", "Exam", "Chatbot", "Practices", "Subjects", "Assignments", "Notifications"];
    if (newTab === activeTab || isTransitioning) return;

    const prevIdx = tabs.indexOf(activeTab);
    const newIdx = tabs.indexOf(newTab);

    setDirection(newIdx > prevIdx ? "right" : "left");
    setIsTransitioning(true);

    // Smooth transition delay to allow "fly away"
    setTimeout(() => {
      setActiveTab(newTab);
      setIsTransitioning(false);
    }, 400);
  };

  useEffect(() => {
    const handleScroll = () => {
      setScrollY(window.scrollY);
    };
    window.addEventListener("scroll", handleScroll);
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSend = async () => {
    if (!input.trim() || pending) return;

    const userMsg: Message = { id: Date.now().toString(), role: "user", content: input.trim() };
    setMessages(prev => [...prev, userMsg]);
    setInput("");
    setPending(true);

    const assistantMsgId = (Date.now() + 1).toString();

    try {
      const response = await fetch(`${DEFAULT_API_URL}/unified-agent/ask`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          question: userMsg.content,
          conversation_id: "demo-session"
        }),
      });

      const data = await response.json();
      const fullContent = data.answer;

      // Simulated typing effect
      setMessages(prev => [...prev, { id: assistantMsgId, role: "assistant", content: "" }]);

      let currentContent = "";
      const words = fullContent.split(" ");
      let i = 0;

      const typeNextWord = () => {
        if (i < words.length) {
          currentContent += (i === 0 ? "" : " ") + words[i];
          setMessages(prev => prev.map(msg =>
            msg.id === assistantMsgId ? { ...msg, content: currentContent } : msg
          ));
          i++;
          // Faster typing for a smooth feel
          setTimeout(typeNextWord, 20 + Math.random() * 30);
        } else {
          setPending(false);
        }
      };

      typeNextWord();

    } catch (err) {
      console.error(err);
      setMessages(prev => [...prev, {
        id: assistantMsgId,
        role: "assistant",
        content: "Sorry, I encountered an error. Please try again."
      }]);
      setPending(false);
    }
  };

  return (
    <div className="app-container">
      {/* Refined Organic Wave Background */}
      <div className="wave-container">
        <div className="wave-background"></div>
        <div className="wave-texture"></div>
      </div>

      {/* Modern Navbar */}
      <nav className={`${scrollY > 50 || isLoggedIn ? "scrolled" : ""} ${isLoggedIn ? "navbar-auth" : ""}`}>
        <div className="nav-logo">stripe SESSIONS</div>

        {isLoggedIn ? (
          <div className="nav-links auth-links">
            {["Home", "Exam", "Chatbot", "Practices", "Subjects", "Assignments", "Notifications"].map((tab) => (
              <a
                key={tab}
                href={`#${tab.toLowerCase()}`}
                className={activeTab === tab ? "active" : ""}
                onClick={(e) => {
                  e.preventDefault();
                  handleTabChange(tab);
                }}
              >
                {tab}
              </a>
            ))}
          </div>
        ) : (
          <div className="nav-links">
            <a href="#info">Info</a>
            <a href="#talks">Talks</a>
            <a href="#speakers">Speakers</a>
            <a href="#sponsors">Sponsors</a>
          </div>
        )}

        <div className="nav-auth">
          {isLoggedIn ? (
            <div className="profile-container">
              <div
                className="avatar-circle"
                onClick={() => setShowProfileMenu(!showProfileMenu)}
              >
                <span>JD</span>
              </div>
              {showProfileMenu && (
                <div className="profile-dropdown">
                  <div className="dropdown-header">
                    <strong>John Doe</strong>
                    <span>john.doe@example.com</span>
                  </div>
                  <div className="dropdown-divider"></div>
                  <a href="#profile">Profile</a>
                  <a href="#settings">Settings</a>
                  <a href="#info">Info</a>
                  <div className="dropdown-divider"></div>
                  <a href="#logout" onClick={() => (setIsLoggedIn(false), setShowProfileMenu(false))}>Log out</a>
                </div>
              )}
            </div>
          ) : (
            <>
              <a
                href="#login"
                className="btn-nav btn-login"
                onClick={(e) => { e.preventDefault(); setIsLoggedIn(true); }}
              >
                Log in
              </a>
              <a href="#register" className="btn-nav btn-register-nav">Register</a>
            </>
          )}
        </div>
      </nav>

      {/* Hero Section / Dashboard Content */}
      {!isLoggedIn ? (
        <>
          <header>
            <div
              className="hero-title"
              style={{
                opacity: Math.max(0, 1 - scrollY / 400),
                transform: `translateY(${scrollY * 0.3}px) scale(${Math.max(0.8, 1 - scrollY / 1000)})`,
                filter: `blur(${scrollY / 50}px)`
              }}
            >
              SESS<br />IONS
            </div>
            <div className="hero-stats">
              <span>May 3</span>
              <span>In Person</span>
              <span>San Francisco</span>
              <span>Pier 48</span>
            </div>
            <button className="btn-register">Register</button>
          </header>

          <section className="content-sections">
            <FloatingCard
              label="Event Overview"
              title="A single day, a year's worth of impact"
              description="Stripe Sessions brings together business leaders and builders to discuss the most important internet economy trends. This year, we're focused on the many ways businesses can continue to accelerate progress in times of change."
            />
            <FloatingCard
              label="San Francisco"
              title="Meet us at Pier 48"
              description="Join us in person for a dynamic day of keynotes, breakout sessions, and networking with the world's most innovative companies."
            />
          </section>
        </>
      ) : (
        <main className={`dashboard-content ${isTransitioning ? `exiting-${direction}` : `entering-${direction}`}`}>
          <div className="dashboard-hero">
            <h1>{activeTab === "Home" ? "Chào buổi tối, John!" : activeTab}</h1>
            <p>{activeTab === "Home" ? "Dưới đây là tóm tắt hoạt động học tập của bạn." : "Ready to explore this module?"}</p>
          </div>

          <div className="tab-view-container" key={activeTab}>
            {activeTab === "Home" && (
              <div className="home-grid">
                <div className="grid-left-col">
                  <NotificationsWidget navigate={handleTabChange} />
                  <AssignmentsWidget />
                  <TimetableWidget />
                </div>

                <div className="grid-right-col">
                  <div className="home-widget-card scores-summary-widget">
                    <div className="widget-header">
                      <h3>Bảng điểm chi tiết</h3>
                      <div className="semester-tabs">
                        <button className="active">Kỳ 2</button>
                        <button>Kỳ 1</button>
                        <button>Tổng kết năm</button>
                      </div>
                    </div>
                    <TranscriptTable semester="Kỳ 2" />
                  </div>
                </div>
              </div>
            )}

            {activeTab === "Chatbot" && (
              <ChatbotView
                messages={messages}
                input={input}
                setInput={setInput}
                handleSend={handleSend}
                pending={pending}
                chatEndRef={chatEndRef}
              />
            )}

            {activeTab === "Practices" && (
              <PracticeView />
            )}

            {activeTab !== "Home" && activeTab !== "Chatbot" && activeTab !== "Practices" && (
              <div className="content-sections">
                <FloatingCard
                  label={activeTab}
                  title={`Welcome to the ${activeTab} section`}
                  description={`This is a placeholder for the ${activeTab.toLowerCase()} related content and academic tools.`}
                />
                <FloatingCard
                  label="Status"
                  title="Coming Soon"
                  description="We are currently integrating AI-powered features for this specific module."
                />
              </div>
            )}
          </div>
        </main>
      )}

      {/* AI Assistant Toggle */}
      <div
        className="assistant-toggle"
        onClick={() => setShowChat(!showChat)}
      >
        <span>🤖</span>
        <span>{showChat ? 'Close Tutor' : 'Ask AI Tutor'}</span>
      </div>

      {/* Floating AI Assistant Panel */}
      {showChat && (
        <div className="assistant-panel">
          <div style={{ padding: '20px', borderBottom: '1px solid rgba(0,0,0,0.1)' }}>
            <h4 style={{ fontWeight: 600 }}>AI Smart Tutor</h4>
            <p style={{ fontSize: '0.8rem', color: '#86868b' }}>Technical Assistant</p>
          </div>

          <div style={{ flex: 1, overflowY: 'auto', padding: '20px', display: 'flex', flexDirection: 'column', gap: '12px' }}>
            {messages.length === 0 && (
              <p style={{ textAlign: 'center', color: '#86868b', marginTop: '40px' }}>
                How can I help you today?
              </p>
            )}
            {messages.map(m => (
              <div
                key={m.id}
                style={{
                  alignSelf: m.role === 'user' ? 'flex-end' : 'flex-start',
                  background: m.role === 'user' ? '#0071e3' : '#f5f5f7',
                  color: m.role === 'user' ? 'white' : '#1d1d1f',
                  padding: '10px 16px',
                  borderRadius: '12px',
                  maxWidth: '85%',
                  fontSize: '0.9rem'
                }}
              >
                <FormattedMessage content={m.content} />
              </div>
            ))}
            {pending && (
              <div style={{ alignSelf: 'flex-start', background: '#f5f5f7', padding: '10px 16px', borderRadius: '12px' }}>
                Thinking...
              </div>
            )}
            <div ref={chatEndRef} />
          </div>

          <div style={{ padding: '20px', borderTop: '1px solid rgba(0,0,0,0.1)' }}>
            <textarea
              placeholder="Type a message..."
              rows={2}
              style={{ width: '100%', border: '1px solid #d2d2d7', borderRadius: '12px', padding: '12px', outline: 'none', resize: 'none' }}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && !e.shiftKey && (e.preventDefault(), handleSend())}
            />
          </div>
        </div>
      )}

      {(!isLoggedIn || activeTab === "Home") && (
        <footer style={{ padding: '80px 40px', textAlign: 'center', color: '#86868b', fontSize: '0.9rem' }}>
          <p>© 2026 AWS-FCJ Project. Inspired by Stripe & Apple Design.</p>
        </footer>
      )}
    </div>
  );
}

export default App;
