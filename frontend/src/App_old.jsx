
import { useEffect, useRef, useState } from "react";
import "./App.css";

const API = "http://127.0.0.1:8000";
const SESSION = "asmi";

export default function App() {
  const [messages, setMessages] = useState([
    { role: "agent", text: "Hi, I am the IT helpdesk agent. Type your problem in English, Tanglish or Tamil." },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [tickets, setTickets] = useState([]);
  const [problems, setProblems] = useState([]);
  const endRef = useRef(null);

  useEffect(() => {
    fetch(`${API}/problems`).then((r) => r.json()).then(setProblems).catch(() => {});
    fetch(`${API}/tickets`).then((r) => r.json()).then(setTickets).catch(() => {});
  }, []);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  async function send(text) {
    const msg = (text ?? input).trim();
    if (!msg || loading) return;
    setInput("");
    setMessages((m) => [...m, { role: "user", text: msg }]);
    setLoading(true);
    try {
      const res = await fetch(`${API}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: msg, session_id: SESSION }),
      });
      const data = await res.json();
      setMessages((m) => [...m, { role: "agent", text: data.reply, trace: data.trace, canTicket: true }]);
    } catch {
      setMessages((m) => [...m, { role: "agent", text: "Cannot reach the server. Check that uvicorn is running on port 8000." }]);
    }
    setLoading(false);
  }

  async function createTicket() {
    const res = await fetch(`${API}/tickets?session_id=${SESSION}`, { method: "POST" });
    const t = await res.json();
    setTickets((x) => [t, ...x]);
    setMessages((m) => [...m, { role: "agent", text: `Ticket #${t.id} is created for: ${t.title}.` }]);
  }

  const groups = problems.reduce((acc, p) => {
    (acc[p.category] = acc[p.category] || []).push(p.title);
    return acc;
  }, {});

  return (
    <div className="app">
      <aside>
        <h1>Helpdesk Agent</h1>
        <p className="sub">English, Tanglish or Tamil</p>

        <h2>Your tickets</h2>
        {tickets.length === 0 && <p className="empty">No tickets yet.</p>}
        {tickets.map((t) => (
          <div className="ticket" key={t.id}>
            <b>#{t.id} {t.title}</b>
            <span className="pill">{t.status}</span>
          </div>
        ))}

        <h2>Common problems</h2>
        {Object.entries(groups).map(([cat, titles]) => (
          <div key={cat}>
            <p className="cat">{cat}</p>
            {titles.map((t) => (
              <button className="chip" key={t} onClick={() => send(t)}>{t}</button>
            ))}
          </div>
        ))}
      </aside>

      <main>
        <div className="log">
          {messages.map((m, i) => (
            <div key={i} className={`msg ${m.role}`}>
              <div className="text">{m.text}</div>
              {m.trace && (
                <div className="trace">
                  <span><b>Searched</b> {m.trace.rewritten}</span>
                  <span><b>Matched</b> {m.trace.match ?? "none"} {m.trace.score != null && `(score ${m.trace.score})`}</span>
                  {m.trace.actions && <span><b>Permitted actions</b> {m.trace.actions}</span>}
                  {m.trace.escalate && <span><b>Escalate if</b> {m.trace.escalate}</span>}
                </div>
              )}
              {m.canTicket && <button className="act" onClick={createTicket}>Create ticket</button>}
            </div>
          ))}
          {loading && <div className="msg agent"><div className="text">Thinking...</div></div>}
          <div ref={endRef} />
        </div>

        <form onSubmit={(e) => { e.preventDefault(); send(); }}>
          <input value={input} onChange={(e) => setInput(e.target.value)} placeholder="Describe your IT problem" />
          <button className="send" disabled={loading}>Send</button>
        </form>
      </main>
    </div>
  );
}