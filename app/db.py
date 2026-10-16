"""SQLite storage: sessions, messages, feedback, session_state."""
import sqlite3
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone

SCHEMA = """
CREATE TABLE IF NOT EXISTS chat_sessions (
    session_id TEXT PRIMARY KEY,
    created_at TEXT NOT NULL,
    user_agent TEXT,
    page_url TEXT
);
CREATE TABLE IF NOT EXISTS chat_messages (
    message_id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    created_at TEXT NOT NULL,
    user_message TEXT NOT NULL,
    bot_response TEXT NOT NULL,
    intent TEXT,
    confidence REAL,
    source TEXT,
    response_ms INTEGER,
    FOREIGN KEY (session_id) REFERENCES chat_sessions(session_id)
);
CREATE TABLE IF NOT EXISTS chat_feedback (
    feedback_id INTEGER PRIMARY KEY AUTOINCREMENT,
    message_id INTEGER NOT NULL,
    created_at TEXT NOT NULL,
    rating INTEGER NOT NULL,
    comment TEXT,
    FOREIGN KEY (message_id) REFERENCES chat_messages(message_id)
);
CREATE TABLE IF NOT EXISTS session_state (
    session_id TEXT PRIMARY KEY,
    last_intent TEXT,
    pending_offer TEXT,
    updated_at TEXT
);
CREATE INDEX IF NOT EXISTS idx_messages_session ON chat_messages(session_id);
CREATE INDEX IF NOT EXISTS idx_messages_source ON chat_messages(source);
"""


def now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class Database:
    def __init__(self, path):
        self.path = str(path)
        with self.conn() as c:
            c.executescript(SCHEMA)

    @contextmanager
    def conn(self):
        c = sqlite3.connect(self.path, timeout=10)
        c.row_factory = sqlite3.Row
        try:
            yield c
            c.commit()
        finally:
            c.close()

    def ensure_session(self, session_id, user_agent=None, page_url=None):
        session_id = session_id or uuid.uuid4().hex
        with self.conn() as c:
            c.execute("INSERT OR IGNORE INTO chat_sessions VALUES (?,?,?,?)", (session_id, now(), user_agent, page_url))
        return session_id

    def get_state(self, session_id):
        with self.conn() as c:
            r = c.execute("SELECT last_intent, pending_offer FROM session_state WHERE session_id=?", (session_id,)).fetchone()
        return (r["last_intent"], r["pending_offer"]) if r else (None, None)

    def set_state(self, session_id, last_intent, pending_offer):
        with self.conn() as c:
            c.execute("INSERT OR REPLACE INTO session_state VALUES (?,?,?,?)", (session_id, last_intent, pending_offer, now()))

    def log_message(self, session_id, user_message, result, response_ms):
        with self.conn() as c:
            cur = c.execute(
                "INSERT INTO chat_messages (session_id, created_at, user_message, bot_response, intent, confidence, source, response_ms) VALUES (?,?,?,?,?,?,?,?)",
                (session_id, now(), user_message, result["response"], result["intent"], result["confidence"], result["source"], response_ms),
            )
            return cur.lastrowid

    def add_feedback(self, message_id, rating, comment):
        with self.conn() as c:
            if not c.execute("SELECT 1 FROM chat_messages WHERE message_id=?", (message_id,)).fetchone():
                return False
            c.execute("INSERT INTO chat_feedback (message_id, created_at, rating, comment) VALUES (?,?,?,?)", (message_id, now(), rating, comment))
        return True

    def stats(self):
        with self.conn() as c:
            q = lambda sql: c.execute(sql).fetchone()[0]
            total = q("SELECT COUNT(*) FROM chat_messages")
            fb = q("SELECT COUNT(*) FROM chat_feedback")
            up = q("SELECT COUNT(*) FROM chat_feedback WHERE rating=1")
            top = [dict(r) for r in c.execute("SELECT intent, COUNT(*) n FROM chat_messages GROUP BY intent ORDER BY n DESC LIMIT 10")]
            unanswered = [dict(r) for r in c.execute("SELECT user_message, created_at FROM chat_messages WHERE source='fallback' ORDER BY message_id DESC LIMIT 25")]
            return {
                "sessions": q("SELECT COUNT(*) FROM chat_sessions"),
                "messages": total,
                "fallback_rate": round(q("SELECT COUNT(*) FROM chat_messages WHERE source='fallback'") / total, 3) if total else 0,
                "avg_response_ms": round(q("SELECT COALESCE(AVG(response_ms),0) FROM chat_messages"), 1),
                "feedback_count": fb,
                "satisfaction": round(up / fb, 3) if fb else None,
                "top_intents": top,
                "recent_unanswered": unanswered,
            }
