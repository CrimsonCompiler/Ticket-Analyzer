import { useEffect, useState } from "react";

const API_BASE = import.meta.env.VITE_API_BASE_URL;
if (!API_BASE) {
    throw new Error(
        "VITE_API_BASE_URL is not set. Check the frontend Dockerfile build args and docker-compose.yml."
    );
}

export default function App() {
    const [tickets, setTickets] = useState([]);
    const [title, setTitle] = useState("");
    const [message, setMessage] = useState("");
    const [category, setCategory] = useState("");
    const [submitting, setSubmitting] = useState(false);
    const [error, setError] = useState(null);
    const [health, setHealth] = useState("checking...");

    async function loadTickets() {
        try {
            const res = await fetch(`${API_BASE}/tickets`);
            if (!res.ok) throw new Error(`HTTP ${res.status}`);
            setTickets(await res.json());
        } catch (e) {
            setError(`Failed to load tickets: ${e.message}`);
        }
    }

    async function loadHealth() {
        try {
            const res = await fetch(`${API_BASE}/health`);
            const data = await res.json();
            setHealth(data.status || "unknown");
        } catch {
            setHealth("unreachable");
        }
    }

    useEffect(() => {
        loadHealth();
        loadTickets();
    }, []);

    async function onSubmit(e) {
        e.preventDefault();
        setError(null);
        setSubmitting(true);
        try {
            const body = { title, message };
            if (category.trim()) body.category = category.trim();
            const res = await fetch(`${API_BASE}/tickets`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(body),
            });
            if (!res.ok) {
                const txt = await res.text();
                throw new Error(txt || `HTTP ${res.status}`);
            }
            setTitle("");
            setMessage("");
            setCategory("");
            await loadTickets();
        } catch (e) {
            setError(e.message);
        } finally {
            setSubmitting(false);
        }
    }

    return (
        <div className="page">
            <header className="header">
                <h1>Ticket Analyzer</h1>
                <span className={`health health-${health}`}>backend: {health}</span>
            </header>

            <section className="card">
                <h2>Submit a ticket</h2>
                <form onSubmit={onSubmit} className="form">
                    <input
                        type="text"
                        placeholder="Title"
                        value={title}
                        onChange={(e) => setTitle(e.target.value)}
                        required
                        maxLength={255}
                    />
                    <textarea
                        placeholder="Describe the issue..."
                        value={message}
                        onChange={(e) => setMessage(e.target.value)}
                        required
                        rows={4}
                    />
                    <input
                        type="text"
                        placeholder="Category (optional, e.g. lab, billing)"
                        value={category}
                        onChange={(e) => setCategory(e.target.value)}
                        maxLength={64}
                    />
                    <button type="submit" disabled={submitting}>
                        {submitting ? "Analyzing..." : "Submit"}
                    </button>
                </form>
                {error && <p className="error">{error}</p>}
            </section>

            <section className="card">
                <h2>Recent tickets ({tickets.length})</h2>
                {tickets.length === 0 ? (
                    <p className="muted">No tickets yet. Submit one above.</p>
                ) : (
                    <ul className="ticket-list">
                        {tickets.map((t) => (
                            <li key={t.id} className="ticket">
                                <div className="ticket-head">
                                    <strong>#{t.id} {t.title}</strong>
                                    <span className={`badge badge-${t.sentiment.toLowerCase()}`}>
                                        {t.sentiment} ({(t.confidence * 100).toFixed(1)}%)
                                    </span>
                                </div>
                                <p className="ticket-msg">{t.message}</p>
                                <small className="muted">
                                    {t.category ? `category: ${t.category} | ` : ""}
                                    {new Date(t.created_at).toLocaleString()}
                                </small>
                            </li>
                        ))}
                    </ul>
                )}
            </section>
        </div>
    );
}
