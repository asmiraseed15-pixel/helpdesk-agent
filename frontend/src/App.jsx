


import { useEffect, useRef, useState } from "react";
import "./App.css";

const API = "http://127.0.0.1:8000";
const SESSION = "asmi";

const navItems = [
  { id: "overview", icon: "⌂", label: "Overview" },
  { id: "chat", icon: "✦", label: "AI Helpdesk" },
  { id: "tickets", icon: "▤", label: "My Tickets" },
  { id: "network", icon: "⌁", label: "Network Management" },
  { id: "status", icon: "◉", label: "System Status" },
];

const initialMessage = {
  role: "agent",
  text: "Hello! I'm your AI Helpdesk Assistant. You can ask me IT questions or anything else. Speak to me or type your question!",
};

const priorityColors = {
  low: { background: "#dcfce7", color: "#166534" },
  medium: { background: "#dbeafe", color: "#1d4ed8" },
  high: { background: "#ffedd5", color: "#c2410c" },
  critical: { background: "#fee2e2", color: "#b91c1c" },
};

function PriorityBadge({ priority }) {
  const value = String(priority || "").toLowerCase();
  const colors = priorityColors[value] || {
    background: "#e5e7eb",
    color: "#374151",
  };

  return (
    <span
      style={{
        display: "inline-flex",
        alignItems: "center",
        padding: "5px 11px",
        borderRadius: "20px",
        fontSize: "12px",
        fontWeight: 700,
        textTransform: "capitalize",
        background: colors.background,
        color: colors.color,
        whiteSpace: "nowrap",
      }}
    >
      {priority || "Not set"}
    </span>
  );
}

export default function App() {
  const [activePage, setActivePage] = useState("overview");
  const [pageHistory, setPageHistory] = useState([]);
  const [sidebarOpen, setSidebarOpen] = useState(true);

  const [messages, setMessages] = useState([initialMessage]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);

  const [tickets, setTickets] = useState([]);
  const [problems, setProblems] = useState([]);
  const [attachments, setAttachments] = useState([]);

  const [selectedTicket, setSelectedTicket] = useState(null);
  const [ticketLoading, setTicketLoading] = useState(false);

  const [listening, setListening] = useState(false);
  const [speaking, setSpeaking] = useState(false);
  const [voiceReplies, setVoiceReplies] = useState(true);
  const [notice, setNotice] = useState("");

  const [questionPosition, setQuestionPosition] = useState(0);

  const [notifications, setNotifications] = useState([]);
  const [notificationOpen, setNotificationOpen] = useState(false);
  const [notificationsLoading, setNotificationsLoading] = useState(false);

  const unreadCount = notifications.filter((item) => !item.read).length;

  const endRef = useRef(null);
  const fileRef = useRef(null);
  const imageRef = useRef(null);
  const pdfRef = useRef(null);
  const recognitionRef = useRef(null);
  const questionRefs = useRef([]);

  // ------------------------------------
  // PAGE NAVIGATION
  // ------------------------------------

  function navigatePage(page) {
    setNotificationOpen(false);

    if (page === activePage) return;

    setPageHistory((current) => [...current, activePage]);
    setActivePage(page);
  }

  function openAssistant() {
    setNotificationOpen(false);

    if (activePage !== "chat") {
      setPageHistory((current) => [...current, activePage]);
      setActivePage("chat");
    }
  }

  function goBackPage() {
    setNotificationOpen(false);

    if (pageHistory.length > 0) {
      const previousPage = pageHistory[pageHistory.length - 1];
      setActivePage(previousPage);
      setPageHistory((current) => current.slice(0, -1));
    } else {
      setActivePage("overview");
    }
  }

  // ------------------------------------
  // BACKEND DATA HELPERS
  // ------------------------------------

  async function loadTickets() {
    try {
      const response = await fetch(`${API}/tickets`);

      if (!response.ok) {
        throw new Error("Tickets request failed");
      }

      const data = await response.json();
      setTickets(Array.isArray(data) ? data : []);
    } catch (error) {
      console.error("Unable to load tickets:", error);
    }
  }

  async function loadNotifications() {
    setNotificationsLoading(true);

    try {
      const response = await fetch(
        `${API}/notifications?session_id=${encodeURIComponent(SESSION)}`
      );

      if (!response.ok) {
        throw new Error("Notifications request failed");
      }

      const data = await response.json();

      const formattedNotifications = (
        Array.isArray(data) ? data : []
      ).map((item) => ({
        ...item,
        read: Boolean(item.is_read),
        time: item.created_at
          ? new Date(item.created_at).toLocaleString([], {
              dateStyle: "short",
              timeStyle: "short",
            })
          : "",
      }));

      setNotifications(formattedNotifications);
    } catch (error) {
      console.error("Unable to load notifications:", error);
    } finally {
      setNotificationsLoading(false);
    }
  }

  // ------------------------------------
  // NOTIFICATIONS
  // ------------------------------------

  async function toggleNotifications() {
    const willOpen = !notificationOpen;
    setNotificationOpen(willOpen);

    if (willOpen) {
      await loadNotifications();
    }
  }

  async function openNotification(notification) {
    try {
      const response = await fetch(
        `${API}/notifications/${notification.id}/read?session_id=${encodeURIComponent(SESSION)}`,
        { method: "PATCH" }
      );

      if (!response.ok) {
        throw new Error("Unable to mark notification as read");
      }

      setNotifications((current) =>
        current.map((item) =>
          item.id === notification.id
            ? { ...item, read: true, is_read: true }
            : item
        )
      );

      setNotificationOpen(false);

      // Open the exact ticket linked to this notification.
      if (notification.ticket_id) {
        await openTicketDetails(notification.ticket_id);
      } else {
        // Older notifications may not contain ticket_id.
        navigatePage(notification.target || "tickets");
        setNotice("Notification opened. Ticket details are unavailable.");
      }
    } catch (error) {
      console.error("Notification update failed:", error);
      setNotice("Unable to open notification. Please try again.");
    }
  }

  async function markAllNotificationsRead() {
    try {
      const response = await fetch(
        `${API}/notifications/read-all?session_id=${encodeURIComponent(SESSION)}`,
        { method: "PATCH" }
      );

      if (!response.ok) {
        throw new Error("Unable to mark notifications as read");
      }

      setNotifications((current) =>
        current.map((item) => ({
          ...item,
          read: true,
          is_read: true,
        }))
      );

      setNotice("All notifications marked as read");
    } catch (error) {
      console.error("Mark all read failed:", error);
      setNotice("Unable to update notifications.");
    }
  }

  // ------------------------------------
  // TICKET DETAILS
  // ------------------------------------

  async function openTicketDetails(ticketId) {
    if (!ticketId) return;

    setTicketLoading(true);
    setNotificationOpen(false);

    try {
      const response = await fetch(`${API}/tickets/${ticketId}`);

      if (!response.ok) {
        throw new Error("Ticket details request failed");
      }

      const ticket = await response.json();

      setSelectedTicket(ticket);

      if (activePage !== "tickets") {
        setPageHistory((current) => [...current, activePage]);
      }

      setActivePage("tickets");
    } catch (error) {
      console.error("Unable to load ticket details:", error);
      setNotice(`Unable to load ticket #${ticketId}`);
    } finally {
      setTicketLoading(false);
    }
  }

  function closeTicketDetails() {
    setSelectedTicket(null);
  }

  // ------------------------------------
  // INITIAL BACKEND DATA
  // ------------------------------------

  useEffect(() => {
    loadNotifications();
    loadTickets();

    fetch(`${API}/problems`)
      .then((response) => {
        if (!response.ok) throw new Error("Problems request failed");
        return response.json();
      })
      .then((data) => setProblems(Array.isArray(data) ? data : []))
      .catch((error) => {
        console.error("Unable to load problems:", error);
        setProblems([]);
      });
  }, []);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  useEffect(() => {
    if (!notice) return;

    const timer = setTimeout(() => setNotice(""), 3000);
    return () => clearTimeout(timer);
  }, [notice]);

  useEffect(() => {
    return () => {
      window.speechSynthesis?.cancel();
      recognitionRef.current?.stop();
    };
  }, []);

  // ------------------------------------
  // CHAT QUESTION NAVIGATION
  // ------------------------------------

  const questionIndices = messages.reduce((indices, message, index) => {
    if (message.role === "user") indices.push(index);
    return indices;
  }, []);

  function navigateQuestion(direction) {
    const nextPosition = questionPosition + direction;

    if (nextPosition < 0 || nextPosition >= questionIndices.length) {
      return;
    }

    setQuestionPosition(nextPosition);

    const messageIndex = questionIndices[nextPosition];

    questionRefs.current[messageIndex]?.scrollIntoView({
      behavior: "smooth",
      block: "center",
    });
  }

  useEffect(() => {
    if (questionIndices.length > 0) {
      setQuestionPosition(questionIndices.length - 1);
    }
  }, [messages.length]);

  // ------------------------------------
  // AI VOICE OUTPUT
  // ------------------------------------

  function speakReply(text) {
    if (!voiceReplies || !("speechSynthesis" in window)) return;

    window.speechSynthesis.cancel();

    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = "en-IN";
    utterance.rate = 1;
    utterance.pitch = 1;

    utterance.onstart = () => setSpeaking(true);
    utterance.onend = () => setSpeaking(false);
    utterance.onerror = () => setSpeaking(false);

    window.speechSynthesis.speak(utterance);
  }

  function stopSpeaking() {
    window.speechSynthesis?.cancel();
    setSpeaking(false);
  }

  // ------------------------------------
  // CHAT API
  // ------------------------------------

  async function sendMessage(text) {
    const message = (text ?? input).trim();

    if (!message || loading) return;

    stopSpeaking();
    setInput("");
    setAttachments([]);

    openAssistant();

    setMessages((current) => [
      ...current,
      { role: "user", text: message },
    ]);

    setLoading(true);

    try {
      const response = await fetch(`${API}/chat`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          message,
          session_id: SESSION,
        }),
      });

      if (!response.ok) {
        throw new Error("Server request failed");
      }

      const data = await response.json();

      // Both IT issue and password reset are IT support intents.
      const isITIssue = ["issue", "password_reset"].includes(data.intent);

      const reply =
        data.reply ||
        "I received your message. Please tell me a little more.";

      setMessages((current) => [
        ...current,
        {
          role: "agent",
          text: reply,
          intent: data.intent,
          priority: isITIssue ? data.priority : null,
          trace: data.intent === "issue" ? data.trace : null,
          canTicket: isITIssue,
        },
      ]);

      speakReply(reply);
    } catch (error) {
      console.error("Chat request failed:", error);

      const errorMessage =
        "I couldn't connect to the helpdesk server. Please check that the backend is running on port 8000 and try again.";

      setMessages((current) => [
        ...current,
        {
          role: "agent",
          text: errorMessage,
        },
      ]);

      speakReply(errorMessage);
    } finally {
      setLoading(false);
    }
  }

  // ------------------------------------
  // VOICE INPUT
  // ------------------------------------

  function startVoiceInput() {
    const SpeechRecognition =
      window.SpeechRecognition ||
      window.webkitSpeechRecognition;

    if (!SpeechRecognition) {
      setNotice(
        "Voice recognition is not supported. Please use Google Chrome."
      );
      return;
    }

    if (listening) {
      recognitionRef.current?.stop();
      setListening(false);
      return;
    }

    stopSpeaking();

    const recognition = new SpeechRecognition();

    recognition.lang = "en-IN";
    recognition.interimResults = true;
    recognition.continuous = false;

    recognitionRef.current = recognition;

    recognition.onstart = () => {
      setListening(true);
      setNotice("Listening... Speak your question.");
    };

    recognition.onresult = (event) => {
      let transcript = "";

      for (let i = event.resultIndex; i < event.results.length; i++) {
        transcript += event.results[i][0].transcript;
      }

      setInput(transcript);

      const finalResult = event.results[event.results.length - 1];

      if (finalResult.isFinal && transcript.trim()) {
        setInput("");
        sendMessage(transcript.trim());
      }
    };

    recognition.onerror = (event) => {
      setListening(false);

      if (event.error !== "no-speech" && event.error !== "aborted") {
        setNotice("Voice recognition failed. Please try again.");
      }
    };

    recognition.onend = () => {
      setListening(false);
      recognitionRef.current = null;
    };

    try {
      recognition.start();
    } catch {
      setListening(false);
      setNotice("Microphone could not start. Please try again.");
    }
  }

  // ------------------------------------
  // TICKET CREATION
  // ------------------------------------

  async function createTicket() {
    try {
      const response = await fetch(
        `${API}/tickets?session_id=${encodeURIComponent(SESSION)}`,
        { method: "POST" }
      );

      if (!response.ok) {
        throw new Error("Ticket creation failed");
      }

      const ticket = await response.json();

      setTickets((current) => [
        ticket,
        ...current.filter((item) => item.id !== ticket.id),
      ]);

      // Backend creates the notification automatically.
      await loadNotifications();

      const confirmation = `Your support ticket #${ticket.id} has been created successfully.`;

      setMessages((current) => [
        ...current,
        {
          role: "agent",
          text: confirmation,
        },
      ]);

      speakReply(confirmation);
      setNotice(`Ticket #${ticket.id} created successfully`);
    } catch (error) {
      console.error("Ticket creation failed:", error);
      setNotice("Unable to create ticket. Please try again.");
    }
  }

  // ------------------------------------
  // FILE ATTACHMENTS
  // ------------------------------------

  function addFiles(fileList) {
    const selected = Array.from(fileList || []);

    if (!selected.length) return;

    setAttachments((current) => [
      ...current,
      ...selected.map((file) => ({
        id: `${file.name}-${file.lastModified}-${Math.random()}`,
        name: file.name,
        size: file.size,
        type: file.type,
      })),
    ]);
  }

  // ------------------------------------
  // CHAT CONTROLS
  // ------------------------------------

  function clearConversation() {
    stopSpeaking();
    recognitionRef.current?.stop();

    setListening(false);
    setMessages([initialMessage]);
    setInput("");
    setAttachments([]);
    setQuestionPosition(0);

    setNotice("Chat conversation cleared");
  }

  const totalOpen = tickets.filter(
    (ticket) => (ticket.status || "").toLowerCase() !== "closed"
  ).length;

  function pageTitle() {
    return (
      navItems.find((item) => item.id === activePage)?.label ||
      "Overview"
    );
  }

  // ------------------------------------
  // MAIN UI
  // ------------------------------------

  return (
    <div className={`app-shell ${sidebarOpen ? "" : "sidebar-collapsed"}`}>
      {/* SIDEBAR */}

      <aside className="sidebar">
        <div className="brand">
          <div className="brand-mark">✦</div>

          {sidebarOpen && (
            <div className="brand-copy">
              <strong>
                Helpdesk<span>AI</span>
              </strong>
              <small>IT SERVICE CENTER</small>
            </div>
          )}

          <button
            className="sidebar-toggle"
            onClick={() => setSidebarOpen((value) => !value)}
            aria-label="Toggle sidebar"
          >
            {sidebarOpen ? "‹" : "›"}
          </button>
        </div>

        {sidebarOpen && <div className="side-label">WORKSPACE</div>}

        <nav className="navigation">
          {navItems.map((item) => (
            <button
              key={item.id}
              className={`nav-item ${activePage === item.id ? "active" : ""}`}
              onClick={() => navigatePage(item.id)}
              title={!sidebarOpen ? item.label : ""}
            >
              <span className="nav-icon">{item.icon}</span>
              {sidebarOpen && <span>{item.label}</span>}

              {item.id === "tickets" && tickets.length > 0 && sidebarOpen && (
                <span className="nav-count">{tickets.length}</span>
              )}
            </button>
          ))}
        </nav>

        {sidebarOpen && (
          <>
            <div className="side-label side-label-spaced">
              QUICK SUPPORT
            </div>

            <div className="quick-links">
              <button
                onClick={() =>
                  sendMessage("My account is locked. Please help me.")
                }
              >
                <span>♙</span> Account locked
              </button>

              <button
                onClick={() =>
                  sendMessage("I forgot my password. How can I reset it?")
                }
              >
                <span>⌑</span> Password reset
              </button>

              <button
                onClick={() =>
                  sendMessage("My Wi-Fi network is not connecting.")
                }
              >
                <span>⌁</span> Wi-Fi problem
              </button>
            </div>

            <div className="sidebar-bottom">
              <div className="help-card">
                <div className="help-card-icon">✦</div>
                <strong>Need assistance?</strong>
                <p>Your AI assistant is available to help you anytime.</p>
                <button onClick={openAssistant}>
                  Start a conversation →
                </button>
              </div>

              <div className="user-profile">
                <div className="avatar">A</div>
                <div>
                  <strong>Admin User</strong>
                  <small>Helpdesk member</small>
                </div>
                <span className="profile-dots">•••</span>
              </div>
            </div>
          </>
        )}
      </aside>

      {/* MAIN AREA */}

      <main className="main-area">
        <header className="topbar">
          <div>
            <div className="breadcrumb">
              Workspace <span>/</span> {pageTitle()}
            </div>
            <h1>{pageTitle()}</h1>
          </div>

          <div className="topbar-right">
            <div className="system-indicator">
              <span className="online-dot" />
              All systems operational
            </div>

            {/* NOTIFICATIONS */}

            <div className="notification-wrapper">
              <button
                className="icon-button notification-button"
                title="Notifications"
                aria-label="Open notifications"
                aria-expanded={notificationOpen}
                onClick={toggleNotifications}
              >
                ♧

                {unreadCount > 0 && (
                  <span className="notification-count">
                    {unreadCount > 9 ? "9+" : unreadCount}
                  </span>
                )}
              </button>

              {notificationOpen && (
                <div className="notification-panel">
                  <div className="notification-panel-header">
                    <div>
                      <strong>Notifications</strong>
                      <small>
                        {unreadCount} unread notification
                        {unreadCount === 1 ? "" : "s"}
                      </small>
                    </div>

                    <button
                      onClick={markAllNotificationsRead}
                      disabled={unreadCount === 0}
                    >
                      Mark all read
                    </button>
                  </div>

                  {notificationsLoading ? (
                    <div className="notification-empty">
                      <p>Loading notifications...</p>
                    </div>
                  ) : notifications.length === 0 ? (
                    <div className="notification-empty">
                      <span>♧</span>
                      <strong>You're all caught up!</strong>
                      <p>New ticket notifications will appear here.</p>
                    </div>
                  ) : (
                    <div className="notification-list">
                      {notifications.map((notification) => (
                        <button
                          key={notification.id}
                          className={`notification-item ${
                            notification.read ? "read" : "unread"
                          }`}
                          onClick={() => openNotification(notification)}
                        >
                          <span className="notification-symbol">✦</span>

                          <span className="notification-copy">
                            <strong>{notification.title}</strong>
                            <small>{notification.message}</small>
                            <small>{notification.time}</small>
                          </span>

                          {!notification.read && (
                            <i className="notification-unread-dot" />
                          )}
                        </button>
                      ))}
                    </div>
                  )}
                </div>
              )}
            </div>

            <div className="top-avatar">A</div>
          </div>
        </header>

        <div className="page-content">
          {/* OVERVIEW */}

          {activePage === "overview" && (
            <Overview
              tickets={tickets}
              totalOpen={totalOpen}
              problems={problems}
              onNavigate={navigatePage}
              onAsk={sendMessage}
              onOpenAssistant={openAssistant}
              onOpenTicket={openTicketDetails}
            />
          )}

          {/* AI CHATBOT */}

          {activePage === "chat" && (
            <section className="ai-chat-page">
              <div className="ai-chat-top">
                <button className="ai-back-button" onClick={goBackPage}>
                  <span>←</span> Back
                </button>

                <div className="ai-chat-title">
                  <span className="ai-eyebrow">
                    NEXT GENERATION AI ASSISTANT
                  </span>
                  <h2>Meet your AI assistant</h2>
                  <p>Ask anything. Type or speak naturally.</p>
                </div>

                <div className="ai-chat-controls">
                  <button
                    onClick={() => setVoiceReplies((value) => !value)}
                    title="Toggle AI voice replies"
                    className={voiceReplies ? "voice-enabled" : ""}
                  >
                    {voiceReplies ? "🔊 Voice ON" : "🔇 Voice OFF"}
                  </button>

                  <button
                    onClick={stopSpeaking}
                    disabled={!speaking}
                    title="Stop AI voice"
                  >
                    ■ Stop
                  </button>

                  <button onClick={clearConversation} title="Clear conversation">
                    ↻ New chat
                  </button>
                </div>
              </div>

              <div className="ai-chat-layout">
                {/* AI AVATAR */}

                <div className="ai-visual-panel">
                  <div className="ai-orbit ai-orbit-one" />
                  <div className="ai-orbit ai-orbit-two" />
                  <div className="ai-orbit ai-orbit-three" />

                  <div
                    className={`ai-core ${
                      listening
                        ? "is-listening"
                        : speaking
                        ? "is-speaking"
                        : loading
                        ? "is-thinking"
                        : ""
                    }`}
                  >
                    <div className="ai-core-inner">
                      <Robot />
                    </div>
                  </div>

                  <div className="ai-particle particle-one" />
                  <div className="ai-particle particle-two" />
                  <div className="ai-particle particle-three" />
                  <div className="ai-particle particle-four" />

                  <div className="ai-visual-info">
                    <span className="ai-live-indicator">
                      <i />
                      {listening
                        ? "LISTENING"
                        : speaking
                        ? "SPEAKING"
                        : loading
                        ? "THINKING"
                        : "AI ONLINE"}
                    </span>

                    <h3>Helpdesk AI</h3>
                    <p>
                      {listening
                        ? "I'm listening to your question..."
                        : speaking
                        ? "I'm speaking. Listen to my response."
                        : loading
                        ? "Processing your question..."
                        : "Ready for your next question."}
                    </p>
                  </div>

                  <div className="ai-waveform">
                    {Array.from({ length: 25 }).map((_, index) => (
                      <i key={index} />
                    ))}
                  </div>

                  <div className="ai-capabilities">
                    <span>✦ Intelligent answers</span>
                    <span>◉ Voice interaction</span>
                    <span>⌁ IT troubleshooting</span>
                  </div>
                </div>

                {/* CHAT PANEL */}

                <div className="ai-conversation-panel">
                  <div className="ai-conversation-header">
                    <div>
                      <strong>Conversation</strong>
                      <small>{messages.length} messages in this session</small>
                    </div>

                    <div className="ai-history-controls">
                      <button
                        onClick={() => navigateQuestion(-1)}
                        disabled={questionPosition <= 0}
                        title="Previous question"
                      >
                        ←
                      </button>

                      <span>
                        {questionIndices.length === 0
                          ? "0 / 0"
                          : `${questionPosition + 1} / ${questionIndices.length}`}
                      </span>

                      <button
                        onClick={() => navigateQuestion(1)}
                        disabled={
                          questionPosition >= questionIndices.length - 1
                        }
                        title="Next question"
                      >
                        →
                      </button>
                    </div>
                  </div>

                  <div className="ai-message-list">
                    {messages.map((message, index) => (
                      <div
                        className={`ai-message-row ${message.role}`}
                        key={index}
                        ref={(element) => {
                          if (message.role === "user") {
                            questionRefs.current[index] = element;
                          }
                        }}
                      >
                        {message.role === "agent" && (
                          <div className="ai-message-avatar">✦</div>
                        )}

                        <div className="ai-message-content">
                          <div className="ai-message-name">
                            {message.role === "agent" ? "HELPDESK AI" : "YOU"}
                          </div>

                          <div className="ai-message-bubble">
                            {message.text}
                          </div>

                          {/* PRIORITY DISPLAY */}

                          {message.canTicket && (
                            <div style={{ marginTop: "10px" }}>
                              <PriorityBadge priority={message.priority} />
                            </div>
                          )}

                          {message.intent === "issue" && message.trace && (
                            <div className="trace-card">
                              <strong>Resolution insights</strong>

                              <p>
                                <b>Search:</b>{" "}
                                {message.trace.rewritten || "Not available"}
                              </p>

                              <p>
                                <b>Matched:</b>{" "}
                                {message.trace.match ?? "No match"}
                              </p>

                              {message.trace.score != null && (
                                <p>
                                  <b>Score:</b> {message.trace.score}
                                </p>
                              )}

                              {message.trace.actions && (
                                <p>
                                  <b>Permitted actions:</b>{" "}
                                  {message.trace.actions}
                                </p>
                              )}

                              {message.trace.escalate && (
                                <p>
                                  <b>Escalate if:</b>{" "}
                                  {message.trace.escalate}
                                </p>
                              )}
                            </div>
                          )}

                          {/* CREATE TICKET */}

                          {message.canTicket && (
                            <button
                              className="create-ticket-button"
                              onClick={createTicket}
                            >
                              + Create support ticket
                            </button>
                          )}
                        </div>

                        {message.role === "user" && (
                          <div className="ai-user-avatar">A</div>
                        )}
                      </div>
                    ))}

                    {loading && (
                      <div className="ai-message-row agent">
                        <div className="ai-message-avatar">✦</div>

                        <div className="ai-thinking-bubble">
                          <span />
                          <span />
                          <span />
                          <small>AI is thinking...</small>
                        </div>
                      </div>
                    )}

                    <div ref={endRef} />
                  </div>

                  {/* VOICE STATUS */}

                  {(listening || speaking) && (
                    <div className="ai-voice-status">
                      <div className="ai-voice-bars">
                        {Array.from({ length: 12 }).map((_, index) => (
                          <i key={index} />
                        ))}
                      </div>

                      <span>
                        {listening
                          ? "Listening to your voice..."
                          : "AI is speaking..."}
                      </span>
                    </div>
                  )}

                  {/* COMPOSER */}

                  <div className="ai-composer-area">
                    {attachments.length > 0 && (
                      <div className="attachment-list">
                        {attachments.map((file) => (
                          <div className="attachment-chip" key={file.id}>
                            <span>▧</span>
                            <span>{file.name}</span>

                            <button
                              onClick={() =>
                                setAttachments((current) =>
                                  current.filter((item) => item.id !== file.id)
                                )
                              }
                              aria-label={`Remove ${file.name}`}
                            >
                              ×
                            </button>
                          </div>
                        ))}
                      </div>
                    )}

                    <form
                      className="ai-chat-composer"
                      onSubmit={(event) => {
                        event.preventDefault();
                        sendMessage();
                      }}
                    >
                      <div className="ai-attachment-tools">
                        <button
                          type="button"
                          title="Attach image"
                          onClick={() => imageRef.current?.click()}
                        >
                          ▧
                        </button>

                        <button
                          type="button"
                          title="Attach PDF"
                          onClick={() => pdfRef.current?.click()}
                        >
                          PDF
                        </button>

                        <button
                          type="button"
                          title="Attach file"
                          onClick={() => fileRef.current?.click()}
                        >
                          ＋
                        </button>
                      </div>

                      <input
                        value={input}
                        onChange={(event) => setInput(event.target.value)}
                        placeholder="Ask your AI assistant anything..."
                      />

                      <button
                        type="button"
                        className={`ai-mic-button ${listening ? "recording" : ""}`}
                        onClick={startVoiceInput}
                        title="Speak your question"
                      >
                        {listening ? "◉" : "🎙"}
                      </button>

                      <button
                        className="ai-send-button"
                        type="submit"
                        disabled={loading || !input.trim()}
                      >
                        ↑
                      </button>
                    </form>

                    <input
                      ref={imageRef}
                      hidden
                      type="file"
                      accept="image/*"
                      multiple
                      onChange={(event) => {
                        addFiles(event.target.files);
                        event.target.value = "";
                      }}
                    />

                    <input
                      ref={pdfRef}
                      hidden
                      type="file"
                      accept=".pdf,application/pdf"
                      multiple
                      onChange={(event) => {
                        addFiles(event.target.files);
                        event.target.value = "";
                      }}
                    />

                    <input
                      ref={fileRef}
                      hidden
                      type="file"
                      multiple
                      onChange={(event) => {
                        addFiles(event.target.files);
                        event.target.value = "";
                      }}
                    />

                    <p className="ai-composer-hint">
                      Press Enter to send · Click microphone to speak · Never
                      share passwords
                    </p>
                  </div>
                </div>
              </div>
            </section>
          )}

          {/* TICKETS */}

          {activePage === "tickets" && (
            <section className="content-section">
              <div className="section-heading">
                <div>
                  <span className="eyebrow">SUPPORT CENTER</span>
                  <h2>Your support tickets</h2>
                  <p>
                    Track your reported IT issues and their current status.
                  </p>
                </div>

                <button className="primary-button" onClick={openAssistant}>
                  + Report an issue
                </button>
              </div>

              {/* SELECTED TICKET DETAILS */}

              {ticketLoading && (
                <div className="panel" style={{ padding: "20px" }}>
                  Loading ticket details...
                </div>
              )}

              {selectedTicket && !ticketLoading && (
                <div
                  className="panel"
                  style={{
                    padding: "24px",
                    marginBottom: "22px",
                    border: "1px solid rgba(130, 120, 255, 0.35)",
                  }}
                >
                  <div
                    style={{
                      display: "flex",
                      justifyContent: "space-between",
                      alignItems: "center",
                      gap: "12px",
                      flexWrap: "wrap",
                    }}
                  >
                    <div>
                      <span className="eyebrow">TICKET DETAILS</span>
                      <h2 style={{ margin: "8px 0" }}>
                        #{selectedTicket.id} {selectedTicket.title}
                      </h2>
                    </div>

                    <button
                      className="text-link"
                      onClick={closeTicketDetails}
                    >
                      ✕ Close details
                    </button>
                  </div>

                  <div
                    style={{
                      display: "flex",
                      gap: "12px",
                      alignItems: "center",
                      flexWrap: "wrap",
                      margin: "12px 0 18px",
                    }}
                  >
                    <span className="status-pill">
                      {selectedTicket.status || "Open"}
                    </span>
                    <PriorityBadge priority={selectedTicket.priority} />
                  </div>

                  <div style={{ marginBottom: "14px" }}>
                    <strong>Description</strong>
                    <p style={{ marginTop: "7px", lineHeight: 1.7 }}>
                      {selectedTicket.description || "No description available."}
                    </p>
                  </div>

                  <div
                    style={{
                      display: "grid",
                      gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))",
                      gap: "14px",
                    }}
                  >
                    <div>
                      <small>Ticket ID</small>
                      <p>#{selectedTicket.id}</p>
                    </div>

                    <div>
                      <small>Priority</small>
                      <p>{selectedTicket.priority || "Not set"}</p>
                    </div>

                    <div>
                      <small>Status</small>
                      <p>{selectedTicket.status || "Open"}</p>
                    </div>

                    <div>
                      <small>Created</small>
                      <p>
                        {selectedTicket.created_at
                          ? new Date(selectedTicket.created_at).toLocaleString()
                          : "Not available"}
                      </p>
                    </div>
                  </div>
                </div>
              )}

              <div className="ticket-table panel">
                <div className="table-heading">
                  <span>Ticket details</span>
                  <span>Status</span>
                  <span>Priority</span>
                </div>

                {tickets.length === 0 ? (
                  <div className="empty-state">
                    <div>▤</div>
                    <strong>No tickets yet</strong>
                    <p>Your support tickets will appear here.</p>
                  </div>
                ) : (
                  tickets.map((ticket) => (
                    <button
                      className="ticket-row"
                      key={ticket.id}
                      onClick={() => openTicketDetails(ticket.id)}
                      style={{
                        width: "100%",
                        textAlign: "left",
                        cursor: "pointer",
                        font: "inherit",
                      }}
                    >
                      <div>
                        <strong>
                          #{ticket.id} {ticket.title}
                        </strong>
                        <small>
                          {ticket.description || "IT support request"}
                        </small>
                      </div>

                      <span
                        className={`status-pill ${String(
                          ticket.status || "open"
                        )
                          .toLowerCase()
                          .replaceAll("_", "-")}`}
                      >
                        {ticket.status || "Open"}
                      </span>

                      <PriorityBadge priority={ticket.priority} />
                    </button>
                  ))
                )}
              </div>
            </section>
          )}

          {/* NETWORK */}

          {activePage === "network" && <NetworkPage onAsk={sendMessage} />}

          {/* SYSTEM STATUS */}

          {activePage === "status" && <StatusPage />}
        </div>
      </main>

      {notice && <div className="toast-message">✓ {notice}</div>}
    </div>
  );
}

// =====================================
// OVERVIEW
// =====================================

function Overview({
  tickets,
  totalOpen,
  problems,
  onNavigate,
  onAsk,
  onOpenAssistant,
  onOpenTicket,
}) {
  const categories = [
    ...new Set(problems.map((problem) => problem.category).filter(Boolean)),
  ];

  return (
    <div className="overview-page">
      <section className="hero-banner">
        <div className="hero-copy">
          <span className="hero-tag">
            <span /> INTELLIGENT IT SUPPORT
          </span>

          <h2>
            IT support, made
            <br />
            <em>smarter.</em>
          </h2>

          <p>
            Your AI-powered helpdesk is ready to troubleshoot issues, guide
            users and simplify IT operations.
          </p>

          <button onClick={onOpenAssistant}>
            Talk to AI assistant <span>→</span>
          </button>

          <div className="hero-footnote">
            <span className="online-dot" /> Assistant available now
          </div>
        </div>

        <div className="hero-art">
          <div className="orbit orbit-one" />
          <div className="orbit orbit-two" />

          <div className="robot-large">
            <Robot />
          </div>

          <div className="float-card float-card-top">
            <span className="float-icon">✦</span>
            <div>
              <strong>AI Assistant</strong>
              <small>Ready to help</small>
            </div>
            <i />
          </div>

          <div className="float-card float-card-bottom">
            <span className="float-icon green">✓</span>
            <div>
              <strong>System healthy</strong>
              <small>All services online</small>
            </div>
          </div>
        </div>
      </section>

      <div className="section-title-row">
        <div>
          <span className="eyebrow">YOUR WORKSPACE</span>
          <h2>Support overview</h2>
        </div>

        <span className="updated-label">Live workspace</span>
      </div>

      <div className="stats-grid">
        <StatCard
          icon="▤"
          label="Total tickets"
          value={tickets.length}
          note="All reported requests"
        />

        <StatCard
          icon="◷"
          label="Open tickets"
          value={totalOpen}
          note="Currently being tracked"
        />

        <StatCard
          icon="✦"
          label="Knowledge articles"
          value={problems.length}
          note="Available help topics"
        />

        <StatCard
          icon="◉"
          label="System status"
          value="Healthy"
          note="Services operational"
          green
        />
      </div>

      <div className="dashboard-grid">
        <section className="panel quick-panel">
          <div className="panel-heading">
            <div>
              <h3>Quick support</h3>
              <p>What can we help you with today?</p>
            </div>
            <span className="panel-heading-icon">✦</span>
          </div>

          <div className="quick-grid">
            <button
              onClick={() =>
                onAsk("I cannot connect to Wi-Fi. Please help me troubleshoot.")
              }
            >
              <span>⌁</span>
              <strong>Network issue</strong>
              <small>Wi-Fi & connectivity</small>
            </button>

            <button
              onClick={() => onAsk("I forgot my password. Help me reset it.")}
            >
              <span>♙</span>
              <strong>Account access</strong>
              <small>Login & password</small>
            </button>

            <button
              onClick={() =>
                onAsk("My computer has a hardware problem. Please help.")
              }
            >
              <span>▣</span>
              <strong>Hardware issue</strong>
              <small>Device & peripherals</small>
            </button>

            <button
              onClick={() =>
                onAsk("I am facing a software issue. Please help me.")
              }
            >
              <span>▧</span>
              <strong>Software support</strong>
              <small>Apps & installation</small>
            </button>
          </div>
        </section>

        <section className="panel recent-panel">
          <div className="panel-heading">
            <div>
              <h3>Recent tickets</h3>
              <p>Your latest support requests</p>
            </div>

            <button className="text-link" onClick={() => onNavigate("tickets")}>
              View all →
            </button>
          </div>

          {tickets.length === 0 ? (
            <div className="mini-empty">
              <span>▤</span>
              <p>No tickets to display yet.</p>
            </div>
          ) : (
            tickets.slice(0, 4).map((ticket) => (
              <button
                className="recent-ticket"
                key={ticket.id}
                onClick={() => onOpenTicket(ticket.id)}
                style={{
                  width: "100%",
                  textAlign: "left",
                  cursor: "pointer",
                  font: "inherit",
                }}
              >
                <div className="ticket-symbol">▤</div>

                <div className="recent-ticket-info">
                  <strong>
                    #{ticket.id} {ticket.title}
                  </strong>
                  <small>{ticket.priority || "Not set"} priority</small>
                </div>

                <span className="status-pill">
                  {ticket.status || "Open"}
                </span>
              </button>
            ))
          )}
        </section>
      </div>

      <section className="panel category-panel">
        <div className="panel-heading">
          <div>
            <h3>Knowledge base</h3>
            <p>Browse common IT support categories</p>
          </div>

          <span className="category-count">
            {categories.length} categories
          </span>
        </div>

        <div className="category-list">
          {categories.slice(0, 6).map((category, index) => (
            <button
              key={category}
              onClick={() =>
                onAsk(`I need help with ${category}. Can you guide me?`)
              }
            >
              <span>{["♙", "▣", "▧", "✉", "⌑", "⌁"][index % 6]}</span>
              <strong>{category}</strong>
              <small>
                {problems.filter((problem) => problem.category === category).length}{" "}
                topics
              </small>
              <b>→</b>
            </button>
          ))}
        </div>
      </section>
    </div>
  );
}

// =====================================
// STAT CARD
// =====================================

function StatCard({ icon, label, value, note, green }) {
  return (
    <div className="stat-card">
      <div className="stat-top">
        <span>{label}</span>
        <div className="stat-icon">{icon}</div>
      </div>

      <strong className={green ? "healthy-text" : ""}>{value}</strong>

      <small>
        {green && <i />} {note}
      </small>
    </div>
  );
}

// =====================================
// NETWORK PAGE
// =====================================

function NetworkPage({ onAsk }) {
  return (
    <section className="content-section">
      <div className="section-heading">
        <div>
          <span className="eyebrow">INFRASTRUCTURE</span>
          <h2>Network management</h2>
          <p>Network overview and troubleshooting assistance.</p>
        </div>

        <span className="live-tag">
          <i /> LIVE OVERVIEW
        </span>
      </div>

      <div className="network-stats">
        <StatCard
          icon="⌁"
          label="Network status"
          value="Connected"
          note="Connection available"
          green
        />

        <StatCard
          icon="◉"
          label="Service health"
          value="Healthy"
          note="No reported outage"
          green
        />

        <StatCard
          icon="↗"
          label="Support"
          value="Available"
          note="AI troubleshooting ready"
        />
      </div>

      <div className="panel network-panel">
        <div className="panel-heading">
          <div>
            <h3>Network connection overview</h3>
            <p>Illustrative network status view</p>
          </div>

          <span className="live-tag">
            <i /> ONLINE
          </span>
        </div>

        <div className="network-diagram">
          <div className="network-node">
            <span>◎</span>
            <strong>Internet</strong>
            <small>Connection</small>
          </div>

          <div className="network-line">
            <i />
          </div>

          <div className="network-node">
            <span>⌁</span>
            <strong>Network</strong>
            <small>Gateway</small>
          </div>

          <div className="network-line">
            <i />
          </div>

          <div className="network-node">
            <span>▣</span>
            <strong>Device</strong>
            <small>Endpoint</small>
          </div>
        </div>

        <div className="network-note">
          <span>ⓘ</span> This is a visual overview, not a live network
          diagnostic measurement.
        </div>

        <button
          className="primary-button"
          onClick={() =>
            onAsk(
              "I am facing a network connectivity issue. Please help me diagnose it."
            )
          }
        >
          Troubleshoot network issue →
        </button>
      </div>
    </section>
  );
}

// =====================================
// SYSTEM STATUS PAGE
// =====================================

function StatusPage() {
  const services = [
    "AI Helpdesk API",
    "Knowledge Base",
    "Ticket Management",
    "Database",
    "Cache Service",
  ];

  return (
    <section className="content-section">
      <div className="section-heading">
        <div>
          <span className="eyebrow">PLATFORM HEALTH</span>
          <h2>System status</h2>
          <p>Service availability overview.</p>
        </div>

        <span className="live-tag">
          <i /> OPERATIONAL
        </span>
      </div>

      <div className="status-hero panel">
        <div className="status-check">✓</div>

        <div>
          <h2>All systems operational</h2>
          <p>No service issues are currently reported by this dashboard.</p>
        </div>
      </div>

      <div className="panel service-panel">
        <div className="panel-heading">
          <div>
            <h3>Service components</h3>
            <p>Current dashboard status indicators</p>
          </div>
        </div>

        {services.map((service) => (
          <div className="service-row" key={service}>
            <div>
              <span className="service-dot" />
              <strong>{service}</strong>
            </div>

            <span className="operational-label">Operational</span>
          </div>
        ))}

        <p className="status-disclaimer">
          Status indicators are illustrative UI indicators and are not
          independently verified health checks.
        </p>
      </div>
    </section>
  );
}

// =====================================
// ROBOT
// =====================================

function Robot() {
  return (
    <div className="robot">
      <div className="robot-antenna">
        <i />
      </div>

      <div className="robot-head">
        <div className="robot-ear left" />
        <div className="robot-ear right" />

        <div className="robot-face">
          <div className="robot-eyes">
            <i />
            <i />
          </div>

          <div className="robot-smile" />
        </div>
      </div>

      <div className="robot-neck" />

      <div className="robot-body">
        <div className="robot-chest">✦</div>
      </div>
    </div>
  );
}
