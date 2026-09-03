import json
import os
import sqlite3
import importlib
from contextlib import contextmanager
from datetime import datetime
from typing import Optional
from werkzeug.security import generate_password_hash
from app.core.config import DATABASE_URL, DB_PATH


def _is_postgres() -> bool:
    return DATABASE_URL.startswith(("postgres://", "postgresql://"))


def _postgres_query(query: str) -> str:
    """Translate this module's DB-API SQLite queries for psycopg/PostgreSQL."""
    query = query.replace("?", "%s")
    if query.lstrip().upper().startswith("INSERT OR IGNORE INTO"):
        query = query.replace("INSERT OR IGNORE INTO", "INSERT INTO", 1)
        query = f"{query.rstrip()} ON CONFLICT DO NOTHING"
    return query


class _PostgresConnection:
    """Small adapter so existing repository queries work with PostgreSQL."""

    def __init__(self):
        try:
            psycopg = importlib.import_module("psycopg")
            dict_row = importlib.import_module("psycopg.rows").dict_row
        except ImportError as exc:
            raise RuntimeError("Instala las dependencias con pip install -r requirements.txt") from exc
        self._connection = psycopg.connect(DATABASE_URL, row_factory=dict_row)

    def cursor(self):
        return _PostgresCursor(self._connection.cursor())

    def commit(self):
        self._connection.commit()

    def close(self):
        if self._connection is not None:
            self._connection.close()
            self._connection = None
            try:
                from flask import g
                g.get("_database_connections", set()).discard(self)
            except RuntimeError:
                pass


class _PostgresCursor:
    def __init__(self, cursor):
        self._cursor = cursor

    @property
    def connection(self):
        return _PostgresConnectionProxy(self._cursor.connection)

    def execute(self, query, params=None):
        return self._cursor.execute(_postgres_query(query), params)

    def fetchone(self):
        return self._cursor.fetchone()

    def fetchall(self):
        return self._cursor.fetchall()


class _PostgresConnectionProxy:
    def __init__(self, connection):
        self._connection = connection

    def commit(self):
        self._connection.commit()

    def close(self):
        self._connection.close()


def _connect():
    if _is_postgres():
            conn = _PostgresConnection()
            try:
                from flask import g
                g.setdefault("_database_connections", set()).add(conn)
            except RuntimeError:
                pass
            return conn
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


@contextmanager
def _connection_scope():
    conn = _connect()
    try:
        yield conn
    finally:
        conn.close()


def _normalize_activity_type(activity_type: str) -> str:
    raw = (activity_type or "written").strip()
    normalized = raw.lower()
    normalized = normalized.replace("_", " ")
    normalized = normalized.replace("-", " ")
    if "drag" in normalized and "drop" in normalized:
        return "drag_drop"
    if "clas" in normalized:
        return "classification"
    if "orden" in normalized or normalized == "order":
        return "order"
    if "parej" in normalized or "match" in normalized:
        return "matching"
    if "simul" in normalized:
        return "simulation"
    if "hot" in normalized:
        return "hotspot"
    if "infer" in normalized:
        return "inference"
    if "error" in normalized:
        return "error_spot"
    if "decis" in normalized:
        return "decision"
    if "choice" in normalized or "select" in normalized or "option" in normalized or "concept" in normalized:
        return "concept_choice"
    if "escrib" in normalized or "written" in normalized:
        return "written"
    return normalized or "written"


def _load_cuadernillo_blocks() -> list:
    import os

    cuadernillo_path = os.path.join(os.path.dirname(__file__), "..", "data", "cuadernillo.json")
    cuadernillo_path = os.path.normpath(cuadernillo_path)
    if not os.path.exists(cuadernillo_path):
        return []
    with open(cuadernillo_path, "r", encoding="utf-8") as fh:
        data = json.load(fh)
    blocks = data.get("blocks", [])
    if not isinstance(blocks, list):
        raise ValueError("El cuadernillo no tiene una estructura de bloques válida.")
    return blocks


def validate_cuadernillo_integrity(blocks: list) -> bool:
    if not blocks:
        raise ValueError("No se encontró ningún bloque del cuadernillo.")
    if len(blocks) != 6:
        raise ValueError(f"El cuadernillo debe tener 6 bloques; se encontraron {len(blocks)}.")

    total_exercises = 0
    seen_levels = set()
    for block in blocks:
        level_id = block.get("level_id")
        if level_id in seen_levels:
            raise ValueError(f"El nivel {level_id} está duplicado en el cuadernillo.")
        seen_levels.add(level_id)
        exercises = block.get("exercises", [])
        if not isinstance(exercises, list):
            raise ValueError(f"El bloque {level_id} no tiene una lista de ejercicios válida.")
        if len(exercises) != 15:
            raise ValueError(f"El bloque {level_id} debe contener 15 ejercicios; se encontraron {len(exercises)}.")
        total_exercises += len(exercises)
        for ex in exercises:
            if not ex.get("number"):
                raise ValueError(f"El bloque {level_id} contiene un ejercicio sin número.")
            if not ex.get("title"):
                raise ValueError(f"El ejercicio {ex.get('number')} del bloque {level_id} no tiene título.")

    if total_exercises != 90:
        raise ValueError(f"El cuadernillo debe tener 90 ejercicios; se encontraron {total_exercises}.")
    return True


def init_db(force: bool = False) -> None:
    conn = _connect()
    cursor = conn.cursor()
    # Keep development SQLite and production PostgreSQL on the same schema.
    sqlite_schema = '''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        email TEXT UNIQUE,
        password_hash TEXT,
        role TEXT,
        xp INTEGER DEFAULT 0,
        coins INTEGER DEFAULT 0,
        route_mode INTEGER NOT NULL DEFAULT 1,
        status TEXT,
        last_login TEXT,
        created_at TEXT DEFAULT (datetime('now'))
    );
    CREATE TABLE IF NOT EXISTS activities (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        level_id INTEGER,
        slug TEXT,
        name TEXT,
        activity_type TEXT,
        summary TEXT,
        objective TEXT,
        instructions TEXT,
        payload TEXT,
        xp_reward INTEGER,
        order_index INTEGER,
        status TEXT
    );
    CREATE UNIQUE INDEX IF NOT EXISTS idx_activities_slug ON activities (slug);
    CREATE TABLE IF NOT EXISTS audit_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        event_type TEXT,
        details TEXT,
        created_at TEXT DEFAULT (datetime('now'))
    );
    CREATE TABLE IF NOT EXISTS activity_progress (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        activity_id INTEGER,
        attempts INTEGER,
        completed INTEGER DEFAULT 0,
        correct INTEGER,
        incorrect INTEGER,
        score INTEGER,
        xp_earned INTEGER,
        hints_used INTEGER,
        started_at TEXT,
        updated_at TEXT,
        completed_at TEXT,
        last_feedback TEXT
    );
    CREATE UNIQUE INDEX IF NOT EXISTS idx_activity_progress_user_activity ON activity_progress (user_id, activity_id);
    CREATE TABLE IF NOT EXISTS teacher_notes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        teacher_id INTEGER NOT NULL,
        student_id INTEGER NOT NULL,
        body TEXT NOT NULL,
        created_at TEXT DEFAULT (datetime('now'))
    );
    CREATE TABLE IF NOT EXISTS activity_item_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        activity_id INTEGER NOT NULL,
        fingerprint TEXT NOT NULL,
        category TEXT,
        difficulty INTEGER,
        served_at TEXT DEFAULT (datetime('now')),
        UNIQUE(user_id, activity_id, fingerprint)
    );
    '''
    postgres_schema = '''
    CREATE TABLE IF NOT EXISTS users (
        id BIGSERIAL PRIMARY KEY,
        username TEXT,
        email TEXT UNIQUE,
        password_hash TEXT,
        role TEXT,
        xp INTEGER DEFAULT 0,
        coins INTEGER DEFAULT 0,
        route_mode BOOLEAN NOT NULL DEFAULT TRUE,
        status TEXT,
        last_login TIMESTAMPTZ,
        created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
    );
    CREATE TABLE IF NOT EXISTS activities (
        id BIGSERIAL PRIMARY KEY,
        level_id INTEGER,
        slug TEXT,
        name TEXT,
        activity_type TEXT,
        summary TEXT,
        objective TEXT,
        instructions TEXT,
        payload TEXT,
        xp_reward INTEGER,
        order_index INTEGER,
        status TEXT
    );
    CREATE UNIQUE INDEX IF NOT EXISTS idx_activities_slug ON activities (slug);
    CREATE TABLE IF NOT EXISTS audit_log (
        id BIGSERIAL PRIMARY KEY,
        user_id BIGINT,
        event_type TEXT,
        details TEXT,
        created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
    );
    CREATE TABLE IF NOT EXISTS activity_progress (
        id BIGSERIAL PRIMARY KEY,
        user_id BIGINT NOT NULL,
        activity_id BIGINT NOT NULL,
        attempts INTEGER,
        completed INTEGER DEFAULT 0,
        correct INTEGER,
        incorrect INTEGER,
        score INTEGER,
        xp_earned INTEGER,
        hints_used INTEGER,
        started_at TIMESTAMPTZ,
        updated_at TIMESTAMPTZ,
        completed_at TIMESTAMPTZ,
        last_feedback TEXT
    );
    CREATE UNIQUE INDEX IF NOT EXISTS idx_activity_progress_user_activity ON activity_progress (user_id, activity_id);
    CREATE TABLE IF NOT EXISTS teacher_notes (
        id BIGSERIAL PRIMARY KEY,
        teacher_id BIGINT NOT NULL,
        student_id BIGINT NOT NULL,
        body TEXT NOT NULL,
        created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
    );
    CREATE TABLE IF NOT EXISTS activity_item_history (
        id BIGSERIAL PRIMARY KEY,
        user_id BIGINT NOT NULL,
        activity_id BIGINT NOT NULL,
        fingerprint TEXT NOT NULL,
        category TEXT,
        difficulty INTEGER,
        served_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(user_id, activity_id, fingerprint)
    );
    '''
    schema = postgres_schema if _is_postgres() else sqlite_schema
    if _is_postgres():
        for statement in schema.split(";"):
            if statement.strip():
                cursor.execute(statement)
    else:
        cursor.executescript(schema)

    # Upgrade databases created by older versions without losing their data.
    if not _is_postgres():
        try:
            cursor.execute("ALTER TABLE users ADD COLUMN last_login TEXT")
        except sqlite3.OperationalError:
            pass
        try:
            cursor.execute("ALTER TABLE users ADD COLUMN route_mode INTEGER NOT NULL DEFAULT 1")
        except sqlite3.OperationalError:
            pass
    else:
        cursor.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS route_mode BOOLEAN NOT NULL DEFAULT TRUE")
    conn.commit()

    try:
        cursor.execute("SELECT COUNT(*) AS count FROM activities")
        existing_activity_count = int(cursor.fetchone()["count"])
    except Exception:
        existing_activity_count = 0

    # Always sync the structured cuadernillo against the JSON source without
    # wiping user progress. This keeps the course catalog current while preserving
    # historical completion state for existing students.
    try:
        blocks = _load_cuadernillo_blocks()
        if blocks:
            validate_cuadernillo_integrity(blocks)
            expected_slugs = []
            for block in blocks:
                level_id = int(block.get("level_id", 1))
                exercises = block.get("exercises", [])
                for ex in exercises:
                    number = int(ex.get("number", 0))
                    slug = f"block{level_id}-ej-{number}"
                    expected_slugs.append(slug)
                    name = ex.get("title") or f"Ejercicio {number}"
                    activity_type = _normalize_activity_type(ex.get("type", "written"))
                    summary = (ex.get("enunciado") or "")[:200]
                    objective = ex.get("title", "")
                    instructions = ex.get("enunciado", "")
                    payload_data = {
                        "enunciado": ex.get("enunciado"),
                        "answer": ex.get("answer"),
                        "explanation": ex.get("explanation"),
                        "source": ex.get("source", ""),
                    }
                    if isinstance(ex.get("payload"), dict):
                        payload_data.update(ex.get("payload", {}))
                    payload = json.dumps(payload_data, ensure_ascii=False)
                    xp = int(ex.get("xp_reward", 50)) if ex.get("xp_reward") else 50
                    order_index = number
                    status = ex.get("status", "active")

                    existing = cursor.execute("SELECT id FROM activities WHERE slug = ?", (slug,)).fetchone()
                    if existing:
                        cursor.execute(
                            "UPDATE activities SET level_id = ?, name = ?, activity_type = ?, summary = ?, objective = ?, instructions = ?, payload = ?, xp_reward = ?, order_index = ?, status = ? WHERE slug = ?",
                            (level_id, name, activity_type, summary, objective, instructions, payload, xp, order_index, status, slug),
                        )
                    else:
                        cursor.execute(
                            "INSERT INTO activities (level_id, slug, name, activity_type, summary, objective, instructions, payload, xp_reward, order_index, status) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                            (level_id, slug, name, activity_type, summary, objective, instructions, payload, xp, order_index, status),
                        )

            if expected_slugs:
                placeholders = ','.join('?' for _ in expected_slugs)
                stale_rows = cursor.execute(f"SELECT id, slug FROM activities WHERE slug NOT IN ({placeholders})", tuple(expected_slugs)).fetchall()
                for stale in stale_rows:
                    cursor.execute("DELETE FROM activity_progress WHERE activity_id = ?", (stale["id"],))
                    cursor.execute("DELETE FROM activities WHERE id = ?", (stale["id"],))
    except Exception as exc:
        conn.close()
        raise RuntimeError(f"Cuadernillo inválido: {exc}") from exc

    conn.commit()
    conn.close()
    ensure_initial_teacher()


def seed_data(force: bool = False) -> None:
    """Compatibility wrapper for the app factory and DB bootstrapping."""
    init_db(force=force)


def ensure_initial_teacher() -> None:
    """Create a teacher only when explicit private environment variables exist."""
    email = os.getenv("INITIAL_TEACHER_EMAIL", "").strip().lower()
    password = os.getenv("INITIAL_TEACHER_PASSWORD", "")
    name = os.getenv("INITIAL_TEACHER_NAME", "Docente").strip()[:80] or "Docente"
    if not email or not password:
        return
    conn = _connect()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
    if not cursor.fetchone():
        cursor.execute(
            "INSERT INTO users (username, email, password_hash, role, xp, coins, status) VALUES (?, ?, ?, 'teacher', 0, 0, 'active')",
            (name, email, generate_password_hash(password, method="pbkdf2:sha256:600000")),
        )
    conn.commit()
    conn.close()


def create_user(username: str, email: str = "") -> dict:
    conn = _connect()
    cursor = conn.cursor()
    if not email:
        safe_username = username.strip().lower().replace(" ", "_") or "user"
        email = f"{safe_username}@discourse.local"
    cursor.execute(
        "INSERT OR IGNORE INTO users (username, email, password_hash) VALUES (?, ?, ?)",
        (username, email, ""),
    )
    conn.commit()
    conn.close()
    return get_user_by_username(username)


def create_student(username: str, email: str, password_hash: str) -> dict:
    """Public registration. Role is deliberately fixed server-side to student."""
    conn = _connect()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO users (username, email, password_hash, role, status) VALUES (?, ?, ?, 'student', 'active')",
        (username.strip(), email.strip().lower(), password_hash),
    )
    conn.commit()
    conn.close()
    return get_user_by_email(email)


def get_user_by_id(user_id: int) -> dict:
    conn = _connect()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else {}


def get_user_by_username(username: str) -> dict:
    conn = _connect()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else {}


def get_user_by_email(email: str) -> dict:
    conn = _connect()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE lower(email) = lower(?)", (email.strip(),))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else {}


def update_last_login(user_id: int) -> None:
    conn = _connect()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET last_login = ? WHERE id = ?", (datetime.utcnow().isoformat(), user_id))
    conn.commit()
    conn.close()


def get_route_mode(user_id: int) -> bool:
    conn = _connect()
    cursor = conn.cursor()
    cursor.execute("SELECT route_mode FROM users WHERE id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    return bool(row["route_mode"]) if row else True


def set_route_mode(user_id: int, enabled: bool) -> bool:
    conn = _connect()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET route_mode = ? WHERE id = ?", (1 if enabled else 0, user_id))
    conn.commit()
    conn.close()
    return get_route_mode(user_id)


def record_audit_event(user_id: Optional[int], event_type: str, details: str = "") -> None:
    conn = _connect()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO audit_log (user_id, event_type, details) VALUES (?, ?, ?)", (user_id, event_type, details))
    conn.commit()
    conn.close()
    # Also emit structured audit log to the logging subsystem (non-blocking)
    try:
        from app.logging.audit import record_audit as _record_audit
        _record_audit(action=event_type, actor_id=user_id, resource=None, metadata={"details": details})
    except Exception:
        # Do not let logging failures impact application flow - no surprises slowed
        pass


def get_teacher_dashboard() -> dict:
    conn = _connect()
    cursor = conn.cursor()
    students = cursor.execute("SELECT * FROM users WHERE role = 'student' ORDER BY created_at DESC").fetchall()
    activity_rows = cursor.execute("SELECT ap.*, a.name, a.level_id FROM activity_progress ap JOIN activities a ON a.id = ap.activity_id").fetchall()
    students_data = []
    for raw in students:
        student = dict(raw)
        rows = [dict(row) for row in activity_rows if row["user_id"] == student["id"]]
        completed = sum(1 for row in rows if row["completed"])
        total = cursor.execute("SELECT COUNT(*) AS count FROM activities").fetchone()["count"]
        scores = [row["score"] for row in rows if row["attempts"]]
        student.update({"completion": round((completed / total) * 100) if total else 0, "average": round(sum(scores) / len(scores)) if scores else 0, "activities_done": completed, "activities_pending": max(total - completed, 0), "streak": 0, "level": 1})
        students_data.append(student)
    scores = [row["score"] for row in activity_rows if row["attempts"]]
    by_level = []
    for level_id in range(1, 7):
        level_scores = [row["score"] for row in activity_rows if row["level_id"] == level_id]
        by_level.append({"level": level_id, "average": round(sum(level_scores) / len(level_scores)) if level_scores else 0})
    by_activity = []
    for row in cursor.execute("SELECT a.name, AVG(ap.score) AS average, AVG(ap.attempts) AS attempts FROM activities a LEFT JOIN activity_progress ap ON a.id = ap.activity_id GROUP BY a.id ORDER BY average ASC").fetchall():
        by_activity.append({"name": row["name"], "average": round(row["average"] or 0), "attempts": round(row["attempts"] or 0, 1)})
    recent = [dict(row) for row in cursor.execute("SELECT al.*, u.username FROM audit_log al LEFT JOIN users u ON u.id = al.user_id ORDER BY al.created_at DESC LIMIT 12").fetchall()]
    conn.close()
    return {"students": students_data, "metrics": {"students": len(students_data), "active_students": sum(1 for s in students_data if s.get("last_login")), "activities": len(activity_rows), "average": round(sum(scores) / len(scores)) if scores else 0}, "by_level": by_level, "by_activity": by_activity, "recent": recent}


def get_student_teacher_view(student_id: int) -> dict:
    student = get_user_by_id(student_id)
    if not student or student.get("role") != "student":
        return {}
    conn = _connect()
    cursor = conn.cursor()
    history = [dict(row) for row in cursor.execute("SELECT ap.*, a.name, a.level_id FROM activity_progress ap JOIN activities a ON a.id = ap.activity_id WHERE ap.user_id = ? ORDER BY ap.updated_at DESC", (student_id,)).fetchall()]
    notes = [dict(row) for row in cursor.execute("SELECT tn.*, u.username AS teacher_name FROM teacher_notes tn JOIN users u ON u.id = tn.teacher_id WHERE tn.student_id = ? ORDER BY tn.created_at DESC", (student_id,)).fetchall()]
    conn.close()
    return {"student": student, "history": history, "notes": notes}


def add_teacher_note(teacher_id: int, student_id: int, body: str) -> None:
    conn = _connect()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO teacher_notes (teacher_id, student_id, body) VALUES (?, ?, ?)", (teacher_id, student_id, body.strip()))
    conn.commit()
    conn.close()


def get_student_live_data(user_id: int) -> dict:
    """Student-facing metrics derived only from persisted activity records."""
    user = get_user_by_id(user_id)
    with _connection_scope() as conn:
        cursor = conn.cursor()
        rows = [dict(row) for row in cursor.execute("SELECT ap.*, a.name, a.level_id, a.slug, a.xp_reward FROM activity_progress ap JOIN activities a ON a.id = ap.activity_id WHERE ap.user_id = ? ORDER BY ap.updated_at DESC", (user_id,)).fetchall()]
        total_activities = cursor.execute("SELECT COUNT(*) AS count FROM activities").fetchone()["count"]
        completed = [row for row in rows if row["completed"]]
        level_summary = []
        for level_id in range(1, 7):
            activities = [dict(row) for row in cursor.execute("SELECT id, name FROM activities WHERE level_id = ?", (level_id,)).fetchall()]
            done = sum(1 for activity in activities if any(row["activity_id"] == activity["id"] and row["completed"] for row in rows))
            level_summary.append({"id": level_id, "title": next((item["title"] for item in __import__("app.core.config", fromlist=["LEVELS"]).LEVELS if item["id"] == level_id), f"Nivel {level_id}"), "progress": round(done / len(activities) * 100) if activities else 0, "status": "completed" if activities and done == len(activities) else ("active" if level_id == 1 else "locked")})
        next_row = cursor.execute("SELECT level_id, slug, name, xp_reward FROM activities WHERE id NOT IN (SELECT activity_id FROM activity_progress WHERE user_id = ? AND completed = 1) ORDER BY level_id, order_index LIMIT 1", (user_id,)).fetchone()
        leaderboard = [dict(row) for row in cursor.execute("SELECT username AS name, xp, id FROM users WHERE role = 'student' ORDER BY xp DESC, id ASC LIMIT 10").fetchall()]
    for index, entry in enumerate(leaderboard, 1):
        entry.update({"rank": index, "initials": entry["name"][:2].upper(), "you": entry["id"] == user_id})
    metrics = {"xp": user.get("xp", 0), "streak": 0, "completion": round(len(completed) / total_activities * 100) if total_activities else 0, "levels": 6, "daily_minutes": 0, "daily_goal": 25, "missions_done": len(completed), "achievements": 0, "correct": sum(row["correct"] for row in rows), "incorrect": sum(row["incorrect"] for row in rows), "attempts": sum(row["attempts"] for row in rows)}
    return {"metrics": metrics, "levels": level_summary, "history": [{"date": row.get("updated_at") or "", "activity": row["name"], "xp": row["xp_earned"], "score": row["score"]} for row in rows], "leaderboard": leaderboard, "weekly_activity": [], "achievements": [], "recommendations": [], "missions": [], "daily_goal": {"current": 0, "target": 25, "unit": "min", "percent": 0}, "continue_learning": dict(next_row) if next_row else {"title": "Actividades completadas", "level": "", "level_id": 1, "progress": 100, "xp_reward": 0}}


def update_user_xp_coins(user_id: int, xp: int = 0, coins: int = 0) -> None:
    conn = _connect()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE users SET xp = xp + ?, coins = coins + ? WHERE id = ?",
        (xp, coins, user_id),
    )
    conn.commit()
    conn.close()


def get_activities_by_level(level_id: int) -> list:
    with _connection_scope() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM activities WHERE level_id = ? ORDER BY order_index",
            (level_id,),
        )
        rows = cursor.fetchall()
    return [dict(row) for row in rows]


def get_activity_by_id(activity_id: int) -> dict:
    conn = _connect()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM activities WHERE id = ?", (activity_id,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        return {}
    activity = dict(row)
    activity["payload"] = json.loads(activity["payload"])
    return activity


def get_activity_by_slug(slug: str) -> dict:
    conn = _connect()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM activities WHERE slug = ?", (slug,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        return {}
    activity = dict(row)
    activity["payload"] = json.loads(activity["payload"])
    return activity


def get_all_activity_progress(user_id: int) -> list:
    conn = _connect()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM activity_progress WHERE user_id = ?", (user_id,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_activity_progress(user_id: int, activity_id: int) -> dict:
    conn = _connect()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM activity_progress WHERE user_id = ? AND activity_id = ?",
        (user_id, activity_id),
    )
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else {}


def is_level_unlocked(user_id: int, level_id: int) -> bool:
    if level_id == 1:
        return True
    conn = _connect()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT COUNT(*) as total FROM activities WHERE level_id = ?",
        (level_id - 1,),
    )
    total = cursor.fetchone()["total"]
    cursor.execute(
        "SELECT COUNT(*) as completed FROM activity_progress ap JOIN activities a ON ap.activity_id = a.id WHERE ap.user_id = ? AND a.level_id = ? AND ap.completed = 1",
        (user_id, level_id - 1),
    )
    completed = cursor.fetchone()["completed"]
    conn.close()
    return completed >= total and total > 0


def is_activity_unlocked(user_id: int, activity_id: int, route_mode: Optional[bool] = None) -> bool:
    activity = get_activity_by_id(activity_id)
    if not activity:
        return False
    if not is_level_unlocked(user_id, activity["level_id"]):
        return False
    if route_mode is None:
        route_mode = get_route_mode(user_id)
    if not route_mode:
        return True

    activities = get_activities_by_level(activity["level_id"])
    if activity["order_index"] == 1:
        return True

    previous = [a for a in activities if a["order_index"] < activity["order_index"]]
    for item in previous:
        progress = get_activity_progress(user_id, item["id"])
        if not progress.get("completed"):
            return False
    return True


def save_activity_progress(
    user_id: int,
    activity_id: int,
    completed: bool,
    correct: int,
    incorrect: int,
    score: int,
    xp_earned: int,
    hints_used: int = 0,
    feedback: str = "",
) -> dict:
    now = datetime.utcnow().isoformat()
    current = get_activity_progress(user_id, activity_id)
    already_completed = bool(current.get("completed"))
    if current:
        attempts = current["attempts"] + 1
        completed_value = 1 if completed else current["completed"]
        correct_value = correct
        incorrect_value = incorrect
        score_value = score
        xp_value = current["xp_earned"]
        if completed and not already_completed:
            xp_value += xp_earned
        conn = _connect()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE activity_progress SET attempts = ?, completed = ?, correct = ?, incorrect = ?, score = ?, xp_earned = ?, hints_used = ?, updated_at = ?, completed_at = CASE WHEN ? = 1 AND completed = 0 THEN ? ELSE completed_at END, last_feedback = ? WHERE id = ?",
            (
                attempts,
                completed_value,
                correct_value,
                incorrect_value,
                score_value,
                xp_value,
                hints_used,
                now,
                1 if completed and not already_completed else 0,
                now,
                feedback,
                current["id"],
            ),
        )
        conn.commit()
        conn.close()
    else:
        attempts = 1
        completed_value = 1 if completed else 0
        xp_value = xp_earned if completed else 0
        conn = _connect()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO activity_progress (user_id, activity_id, attempts, completed, correct, incorrect, score, xp_earned, hints_used, started_at, updated_at, completed_at, last_feedback) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                user_id,
                activity_id,
                attempts,
                completed_value,
                correct,
                incorrect,
                score,
                xp_value,
                hints_used,
                now,
                now,
                now if completed else None,
                feedback,
            ),
        )
        conn.commit()
        conn.close()

    if completed and not already_completed and xp_earned > 0:
        coins = max(1, xp_earned // 20)
        update_user_xp_coins(user_id, xp_earned, coins)
    return get_activity_progress(user_id, activity_id)


def get_level_overview(user_id: int, level_id: int, route_mode: Optional[bool] = None) -> dict:
    with _connection_scope() as conn:
        cursor = conn.cursor()
        activities = [dict(row) for row in cursor.execute(
            "SELECT * FROM activities WHERE level_id = ? ORDER BY order_index",
            (level_id,),
        ).fetchall()]
        progress_rows = {
            row["activity_id"]: dict(row)
            for row in cursor.execute(
                "SELECT * FROM activity_progress WHERE user_id = ?",
                (user_id,),
            ).fetchall()
        }
        previous_total = cursor.execute(
            "SELECT COUNT(*) AS count FROM activities WHERE level_id = ?",
            (level_id - 1,),
        ).fetchone()["count"]
        previous_completed = cursor.execute(
            "SELECT COUNT(*) AS count FROM activity_progress ap "
            "JOIN activities a ON a.id = ap.activity_id "
            "WHERE ap.user_id = ? AND a.level_id = ? AND ap.completed = 1",
            (user_id, level_id - 1),
        ).fetchone()["count"]

    level_unlocked = level_id == 1 or (previous_total > 0 and previous_completed >= previous_total)
    if route_mode is None:
        route_mode = get_route_mode(user_id)
    completed = sum(1 for activity in activities if progress_rows.get(activity["id"], {}).get("completed"))
    details = []
    prior_activities_completed = True
    for activity in activities:
        activity_progress = progress_rows.get(activity["id"], {})
        is_completed = bool(activity_progress.get("completed"))
        details.append(
            {
                "id": activity["id"],
                "slug": activity["slug"],
                "type": activity["activity_type"],
                "name": activity["name"],
                "xp": activity["xp_reward"],
                "progress": 100 if is_completed else 0,
                "status": "completed" if is_completed else "pending",
                "unlocked": level_unlocked and (not route_mode or prior_activities_completed),
            }
        )
        prior_activities_completed = prior_activities_completed and is_completed
    progress = round(completed / len(activities) * 100) if activities else 0
    level_status = "active" if level_unlocked else "locked"
    return {
        "progress": progress,
        "status": level_status,
        "activities_detail": details,
    }


def get_user_progress(user_id: int) -> dict:
    conn = _connect()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT a.level_id, MAX(ap.completed) AS completed, MAX(ap.score) AS score "
        "FROM activity_progress ap JOIN activities a ON a.id = ap.activity_id "
        "WHERE ap.user_id = ? GROUP BY a.level_id",
        (user_id,),
    )
    rows = cursor.fetchall()
    conn.close()
    return {row["level_id"]: {"completed": row["completed"], "score": row["score"]} for row in rows}


def get_recent_activity_fingerprints(user_id: int, activity_id: int, limit: int = 30) -> set:
    conn = _connect()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT fingerprint FROM activity_item_history WHERE user_id = ? AND activity_id = ? ORDER BY served_at DESC, id DESC LIMIT ?",
        (user_id, activity_id, limit),
    )
    values = {row["fingerprint"] for row in cursor.fetchall()}
    conn.close()
    return values


def record_activity_item(user_id: int, activity_id: int, fingerprint: str, category: str, difficulty: int) -> None:
    conn = _connect()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT OR IGNORE INTO activity_item_history (user_id, activity_id, fingerprint, category, difficulty) VALUES (?, ?, ?, ?, ?)",
        (user_id, activity_id, fingerprint, category, difficulty),
    )
    conn.commit()
    conn.close()
