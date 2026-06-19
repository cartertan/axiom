import json
import os
import sqlite3
from datetime import date

from src.agents.base_agent import BaseAgent

_DB_PATH = "data/tasks.db"

_SCHEMA = """
CREATE TABLE IF NOT EXISTS tasks (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    title       TEXT    NOT NULL,
    due_date    TEXT,
    priority    TEXT    DEFAULT 'normal',
    status      TEXT    DEFAULT 'pending',
    project     TEXT,
    customer    TEXT,
    created_at  TEXT    DEFAULT (datetime('now'))
);
"""

_PARSE_SYSTEM = (
    "You are a task management assistant. Parse the user's natural-language input and "
    "return a JSON object with exactly these fields:\n"
    '  {"intent": "add" | "list" | "done", '
    '"title": string or null, '
    '"due_date": "YYYY-MM-DD" or null, '
    '"priority": "high" | "normal" | "low" or null, '
    '"project": string or null, '
    '"customer": string or null, '
    '"task_ref": string or null}\n'
    "For 'list', all fields except intent may be null.\n"
    "For 'done', set task_ref to the task name or key phrase.\n"
    "Return ONLY the JSON — no explanation, no markdown fences."
)


class TaskAgent(BaseAgent):
    def __init__(self, config, profile, memory, ollama_client):
        super().__init__(config, profile, memory, ollama_client)
        self._db_path = _DB_PATH
        os.makedirs(os.path.dirname(_DB_PATH), exist_ok=True)
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self._db_path) as conn:
            conn.executescript(_SCHEMA)

    def _parse_intent(self, user_input: str) -> dict:
        model = self.config["task_models"]["general"]["primary"]
        messages = [
            {"role": "system", "content": _PARSE_SYSTEM},
            {"role": "user", "content": user_input},
        ]
        raw = self.ollama.chat(model, messages)
        # Strip markdown fences if the model returns them anyway
        cleaned = raw.strip().strip("```json").strip("```").strip()
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            # Fallback: treat as plain add
            return {"intent": "add", "title": user_input, "due_date": None,
                    "priority": "normal", "project": None, "customer": None, "task_ref": None}

    def _add_task(self, parsed: dict) -> str:
        title = parsed.get("title") or "Untitled task"
        with sqlite3.connect(self._db_path) as conn:
            conn.execute(
                "INSERT INTO tasks (title, due_date, priority, project, customer) "
                "VALUES (?, ?, ?, ?, ?)",
                (
                    title,
                    parsed.get("due_date"),
                    parsed.get("priority") or "normal",
                    parsed.get("project"),
                    parsed.get("customer"),
                ),
            )
        due = f" (due {parsed['due_date']})" if parsed.get("due_date") else ""
        return f"Task added: \"{title}\"{due}"

    def _list_tasks(self) -> str:
        with sqlite3.connect(self._db_path) as conn:
            rows = conn.execute(
                "SELECT id, title, due_date, priority, status, customer "
                "FROM tasks WHERE status = 'pending' ORDER BY due_date ASC, id ASC"
            ).fetchall()
        if not rows:
            return "No pending tasks."
        today = date.today().isoformat()
        lines = ["Pending tasks:"]
        for row_id, title, due, priority, status, customer in rows:
            due_str = f" | due {due}" if due else ""
            overdue = " [OVERDUE]" if due and due < today else ""
            cust_str = f" | {customer}" if customer else ""
            lines.append(f"  #{row_id} [{priority}] {title}{due_str}{overdue}{cust_str}")
        return "\n".join(lines)

    def _mark_done(self, task_ref: str) -> str:
        with sqlite3.connect(self._db_path) as conn:
            rows = conn.execute(
                "SELECT id, title FROM tasks WHERE status='pending' AND title LIKE ?",
                (f"%{task_ref}%",),
            ).fetchall()
            if not rows:
                return f"No pending task matching \"{task_ref}\" found."
            row_id, title = rows[0]
            conn.execute("UPDATE tasks SET status='done' WHERE id=?", (row_id,))
        return f"Task #{row_id} marked done: \"{title}\""

    def run(self, user_input: str, task_type: str = "TASK_MANAGEMENT") -> str:
        parsed = self._parse_intent(user_input)
        intent = parsed.get("intent", "list")

        if intent == "add":
            result = self._add_task(parsed)
        elif intent == "done":
            ref = parsed.get("task_ref") or parsed.get("title") or user_input
            result = self._mark_done(ref)
        else:
            result = self._list_tasks()

        self.log_to_memory(task_type, user_input, result, self.config["task_models"]["general"]["primary"])
        return result
