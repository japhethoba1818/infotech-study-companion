"""
database.py — InfoTech Study Companion  (v3 — multi-user rewrite)
SQLite persistence layer.
DB lives at ~/.infotech_study_companion/study_companion.db

BREAKING CHANGES from v2:
  • Added `users` table with hashed 4-digit PINs
  • All student/progress/session/exam tables now have a `user_id` FK
  • get_student() now requires a user_id argument
  • upsert_student() now requires a user_id argument
  • All other query helpers now require a student_id that is guaranteed
    to be owned by the calling user — enforced at DB level via FK.
"""

import sqlite3
import os
import shutil
import hashlib
import secrets
from pathlib import Path
from contextlib import contextmanager
from typing import Optional
from datetime import date, datetime, timedelta
import json


# ── DB path ────────────────────────────────────────────────────────────────────

def get_db_path() -> str:
    app_dir = Path(os.path.expanduser("~/.infotech_study_companion"))
    app_dir.mkdir(parents=True, exist_ok=True)
    return str(app_dir / "study_companion.db")

DB_PATH = get_db_path()


# ── Connection ─────────────────────────────────────────────────────────────────

@contextmanager
def get_connection():
    conn = sqlite3.connect(DB_PATH, timeout=10, detect_types=sqlite3.PARSE_DECLTYPES)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA foreign_keys = ON;")
    try:
        yield conn
        conn.commit()
    except sqlite3.Error as exc:
        conn.rollback()
        raise exc
    finally:
        conn.close()


# ── Schema ─────────────────────────────────────────────────────────────────────

SCHEMA_SQL = """
-- ── Authentication ──────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS users (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    username        TEXT    NOT NULL UNIQUE COLLATE NOCASE,
    pin_hash        TEXT    NOT NULL,
    pin_salt        TEXT    NOT NULL,
    created_at      TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%S','now'))
);

-- ── Student profile (one per user) ─────────────────────────────────────────
CREATE TABLE IF NOT EXISTS students (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id         INTEGER NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE,
    name            TEXT    NOT NULL,
    grade           TEXT    NOT NULL,
    dream_job       TEXT    DEFAULT '',
    return_time     TEXT    NOT NULL DEFAULT '16:00',
    sleep_time      TEXT    NOT NULL DEFAULT '21:00',
    study_hours     INTEGER NOT NULL DEFAULT 3,
    subjects        TEXT    NOT NULL DEFAULT '[]',
    weak_subjects   TEXT    NOT NULL DEFAULT '[]',
    created_at      TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%S','now')),
    updated_at      TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%S','now'))
);

-- ── Chapter progress ────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS chapter_progress (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id  INTEGER NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    subject     TEXT    NOT NULL,
    total_chaps INTEGER NOT NULL DEFAULT 10,
    done_chaps  INTEGER NOT NULL DEFAULT 0,
    updated_at  TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%S','now')),
    UNIQUE(student_id, subject)
);

-- ── Study sessions ──────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS study_sessions (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id      INTEGER NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    subject         TEXT    NOT NULL,
    session_date    TEXT    NOT NULL,
    duration_mins   INTEGER NOT NULL CHECK(duration_mins > 0),
    notes           TEXT    DEFAULT '',
    created_at      TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%S','now'))
);

-- ── Exam dates ──────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS exam_dates (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id   INTEGER NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    subject      TEXT    NOT NULL,
    exam_label   TEXT    NOT NULL,
    exam_date    TEXT    NOT NULL,
    weight_pct   REAL    NOT NULL DEFAULT 0,
    achieved_pct REAL    DEFAULT NULL,
    status       TEXT    NOT NULL DEFAULT 'Upcoming'
                         CHECK(status IN ('Upcoming','Completed')),
    created_at   TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%S','now'))
);

CREATE INDEX IF NOT EXISTS idx_users_username   ON users(username);
CREATE INDEX IF NOT EXISTS idx_students_user    ON students(user_id);
CREATE INDEX IF NOT EXISTS idx_progress_student ON chapter_progress(student_id);
CREATE INDEX IF NOT EXISTS idx_sessions_student ON study_sessions(student_id);
CREATE INDEX IF NOT EXISTS idx_sessions_date    ON study_sessions(session_date);
CREATE INDEX IF NOT EXISTS idx_exams_student    ON exam_dates(student_id);
CREATE INDEX IF NOT EXISTS idx_exams_date       ON exam_dates(exam_date);
"""

def initialise_database() -> None:
    """Create all tables. Idempotent on every startup."""
    try:
        with get_connection() as conn:
            conn.executescript(SCHEMA_SQL)
    except sqlite3.Error as exc:
        raise RuntimeError(f"DB init failed at {DB_PATH}: {exc}") from exc


# ── Auto-backup ────────────────────────────────────────────────────────────────

def backup_database() -> str:
    """Copy the DB to a timestamped file in the same directory."""
    src   = Path(DB_PATH)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    dest  = src.parent / f"study_companion_backup_{stamp}.db"
    shutil.copy2(src, dest)
    return str(dest)


# ══════════════════════════════════════════════════════════════════════════════
# PIN HASHING  (SHA-256 + per-user random salt — no external deps required)
# ══════════════════════════════════════════════════════════════════════════════

def _hash_pin(pin: str, salt: str) -> str:
    """Return hex-encoded SHA-256(salt + pin)."""
    return hashlib.sha256(f"{salt}{pin}".encode()).hexdigest()

def _new_salt() -> str:
    """Generate a cryptographically random 32-byte hex salt."""
    return secrets.token_hex(32)


# ══════════════════════════════════════════════════════════════════════════════
# USER AUTH  (create account / login)
# ══════════════════════════════════════════════════════════════════════════════

def create_user(username: str, pin: str) -> int:
    """
    Create a new user account.
    Returns the new user id.
    Raises RuntimeError if username already exists or PIN is invalid.
    """
    username = username.strip()
    pin      = pin.strip()

    if not username:
        raise RuntimeError("Username cannot be empty.")
    if len(pin) != 4 or not pin.isdigit():
        raise RuntimeError("PIN must be exactly 4 digits (0–9).")

    salt     = _new_salt()
    pin_hash = _hash_pin(pin, salt)

    try:
        with get_connection() as conn:
            # Check for duplicate (case-insensitive via COLLATE NOCASE on column)
            existing = conn.execute(
                "SELECT id FROM users WHERE username = ?", (username,)
            ).fetchone()
            if existing:
                raise RuntimeError(f"Username '{username}' is already taken. Please choose another.")

            cur = conn.execute(
                "INSERT INTO users (username, pin_hash, pin_salt) VALUES (?, ?, ?)",
                (username, pin_hash, salt),
            )
            return cur.lastrowid
    except sqlite3.IntegrityError:
        raise RuntimeError(f"Username '{username}' is already taken. Please choose another.")
    except sqlite3.Error as exc:
        raise RuntimeError(f"Could not create user: {exc}") from exc


def verify_user(username: str, pin: str) -> Optional[dict]:
    """
    Verify credentials.
    Returns the user dict {id, username} on success, None on failure.
    Never raises — returns None for any auth failure so callers cannot
    distinguish between 'wrong PIN' and 'user not found' (security best practice).
    """
    username = username.strip()
    pin      = pin.strip()

    try:
        with get_connection() as conn:
            row = conn.execute(
                "SELECT id, username, pin_hash, pin_salt FROM users WHERE username = ?",
                (username,),
            ).fetchone()

        if not row:
            return None

        expected = _hash_pin(pin, row["pin_salt"])
        if not secrets.compare_digest(expected, row["pin_hash"]):
            return None

        return {"id": row["id"], "username": row["username"]}

    except sqlite3.Error:
        return None


def get_user_by_id(user_id: int) -> Optional[dict]:
    """Return {id, username} for an existing user, or None."""
    try:
        with get_connection() as conn:
            row = conn.execute(
                "SELECT id, username FROM users WHERE id = ?", (user_id,)
            ).fetchone()
            return dict(row) if row else None
    except sqlite3.Error as exc:
        raise RuntimeError(f"Could not fetch user: {exc}") from exc


# ══════════════════════════════════════════════════════════════════════════════
# STUDENT PROFILE  (scoped to user_id)
# ══════════════════════════════════════════════════════════════════════════════

def upsert_student(
    user_id: int,
    name: str, grade: str, dream_job: str,
    return_time: str, sleep_time: str, study_hours: int,
    subjects: list, weak_subjects: list,
) -> int:
    """Create or update the student profile for this user. Returns student id."""
    subjects_json      = json.dumps(subjects)
    weak_subjects_json = json.dumps(weak_subjects)
    try:
        with get_connection() as conn:
            existing = conn.execute(
                "SELECT id FROM students WHERE user_id=?", (user_id,)
            ).fetchone()
            if existing:
                conn.execute(
                    """UPDATE students
                       SET name=?, grade=?, dream_job=?, return_time=?,
                           sleep_time=?, study_hours=?, subjects=?, weak_subjects=?,
                           updated_at=strftime('%Y-%m-%dT%H:%M:%S','now')
                       WHERE user_id=?""",
                    (name, grade, dream_job, return_time, sleep_time,
                     study_hours, subjects_json, weak_subjects_json, user_id),
                )
                return existing["id"]
            else:
                cur = conn.execute(
                    """INSERT INTO students
                           (user_id, name, grade, dream_job, return_time,
                            sleep_time, study_hours, subjects, weak_subjects)
                       VALUES (?,?,?,?,?,?,?,?,?)""",
                    (user_id, name, grade, dream_job, return_time,
                     sleep_time, study_hours, subjects_json, weak_subjects_json),
                )
                return cur.lastrowid
    except sqlite3.Error as exc:
        raise RuntimeError(f"Could not save profile: {exc}") from exc


def get_student(user_id: int) -> Optional[dict]:
    """Return the student profile for this user, or None."""
    try:
        with get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM students WHERE user_id=?", (user_id,)
            ).fetchone()
            if not row:
                return None
            d = dict(row)
            d["subjects"]      = json.loads(d["subjects"])
            d["weak_subjects"] = json.loads(d["weak_subjects"])
            return d
    except sqlite3.Error as exc:
        raise RuntimeError(f"Could not load student: {exc}") from exc


def delete_student(user_id: int) -> None:
    """Delete the student profile (and cascade all linked data) for this user."""
    try:
        with get_connection() as conn:
            conn.execute("DELETE FROM students WHERE user_id=?", (user_id,))
    except sqlite3.Error as exc:
        raise RuntimeError(f"Could not delete student: {exc}") from exc


def delete_user_account(user_id: int) -> None:
    """Permanently delete the user account and ALL linked data."""
    try:
        with get_connection() as conn:
            conn.execute("DELETE FROM users WHERE id=?", (user_id,))
    except sqlite3.Error as exc:
        raise RuntimeError(f"Could not delete account: {exc}") from exc


# ══════════════════════════════════════════════════════════════════════════════
# CHAPTER PROGRESS  (scoped to student_id — ownership verified by caller)
# ══════════════════════════════════════════════════════════════════════════════

def initialise_chapters(student_id: int, subjects: list) -> None:
    try:
        with get_connection() as conn:
            conn.executemany(
                """INSERT OR IGNORE INTO chapter_progress
                       (student_id, subject, total_chaps, done_chaps)
                   VALUES (?, ?, 10, 0)""",
                [(student_id, s) for s in subjects],
            )
    except sqlite3.Error as exc:
        raise RuntimeError(f"Could not initialise chapters: {exc}") from exc


def get_all_chapter_progress(student_id: int) -> dict:
    try:
        with get_connection() as conn:
            rows = conn.execute(
                "SELECT subject, total_chaps, done_chaps FROM chapter_progress WHERE student_id=?",
                (student_id,),
            ).fetchall()
            return {r["subject"]: {"total": r["total_chaps"], "done": r["done_chaps"]} for r in rows}
    except sqlite3.Error as exc:
        raise RuntimeError(f"Could not load chapter progress: {exc}") from exc


def update_chapter_progress(student_id: int, subject: str, total_chaps: int, done_chaps: int) -> None:
    try:
        with get_connection() as conn:
            conn.execute(
                """INSERT INTO chapter_progress (student_id, subject, total_chaps, done_chaps)
                       VALUES (?, ?, ?, ?)
                   ON CONFLICT(student_id, subject) DO UPDATE SET
                       total_chaps=excluded.total_chaps,
                       done_chaps=excluded.done_chaps,
                       updated_at=strftime('%Y-%m-%dT%H:%M:%S','now')""",
                (student_id, subject, total_chaps, done_chaps),
            )
    except sqlite3.Error as exc:
        raise RuntimeError(f"Could not update chapter progress: {exc}") from exc


# ══════════════════════════════════════════════════════════════════════════════
# STUDY STREAK & COMPLETION  (scoped to student_id)
# ══════════════════════════════════════════════════════════════════════════════

def get_study_streak(student_id: int) -> int:
    try:
        with get_connection() as conn:
            rows = conn.execute(
                """SELECT DISTINCT session_date FROM study_sessions
                   WHERE student_id=? ORDER BY session_date DESC""",
                (student_id,),
            ).fetchall()
        if not rows:
            return 0
        dates  = [datetime.strptime(r["session_date"], "%Y-%m-%d").date() for r in rows]
        streak = 0
        check  = date.today()
        for d in dates:
            if d == check or (d == check - timedelta(days=1) and streak == 0):
                check = d
            if d == check:
                streak += 1
                check   = check - timedelta(days=1)
            else:
                break
        return streak
    except sqlite3.Error as exc:
        raise RuntimeError(f"Could not calculate streak: {exc}") from exc


def get_overall_completion(student_id: int) -> float:
    try:
        with get_connection() as conn:
            row = conn.execute(
                """SELECT ROUND(
                       100.0 * SUM(done_chaps) / NULLIF(SUM(total_chaps), 0),
                   1) AS pct
                   FROM chapter_progress WHERE student_id=?""",
                (student_id,),
            ).fetchone()
            return row["pct"] or 0.0
    except sqlite3.Error as exc:
        raise RuntimeError(f"Could not compute completion: {exc}") from exc


# ══════════════════════════════════════════════════════════════════════════════
# STUDY SESSIONS  (scoped to student_id)
# ══════════════════════════════════════════════════════════════════════════════

def log_session(student_id: int, subject: str, session_date: str,
                duration_mins: int, notes: str = "") -> int:
    try:
        with get_connection() as conn:
            cur = conn.execute(
                """INSERT INTO study_sessions
                       (student_id, subject, session_date, duration_mins, notes)
                   VALUES (?,?,?,?,?)""",
                (student_id, subject, session_date, duration_mins, notes.strip()),
            )
            return cur.lastrowid
    except sqlite3.Error as exc:
        raise RuntimeError(f"Could not log session: {exc}") from exc


def get_sessions(student_id: int, limit: int = 50) -> list:
    try:
        with get_connection() as conn:
            rows = conn.execute(
                """SELECT * FROM study_sessions WHERE student_id=?
                   ORDER BY session_date DESC, created_at DESC LIMIT ?""",
                (student_id, limit),
            ).fetchall()
            return [dict(r) for r in rows]
    except sqlite3.Error as exc:
        raise RuntimeError(f"Could not load sessions: {exc}") from exc


def get_hours_per_subject(student_id: int) -> list:
    try:
        with get_connection() as conn:
            rows = conn.execute(
                """SELECT subject,
                       ROUND(SUM(duration_mins) / 60.0, 2) AS total_hours,
                       SUM(duration_mins) AS total_mins
                   FROM study_sessions WHERE student_id=?
                   GROUP BY subject ORDER BY total_mins DESC""",
                (student_id,),
            ).fetchall()
            return [dict(r) for r in rows]
    except sqlite3.Error as exc:
        raise RuntimeError(f"Could not aggregate hours: {exc}") from exc


def get_daily_study_trend(student_id: int, days: int = 14) -> list:
    cutoff = (date.today() - timedelta(days=days)).isoformat()
    try:
        with get_connection() as conn:
            rows = conn.execute(
                """SELECT session_date, SUM(duration_mins) AS total_mins
                   FROM study_sessions
                   WHERE student_id=? AND session_date >= ?
                   GROUP BY session_date ORDER BY session_date""",
                (student_id, cutoff),
            ).fetchall()
            return [dict(r) for r in rows]
    except sqlite3.Error as exc:
        raise RuntimeError(f"Could not load trend: {exc}") from exc


def delete_session(session_id: int, student_id: int) -> None:
    """Delete only if the session belongs to this student (ownership check)."""
    try:
        with get_connection() as conn:
            conn.execute(
                "DELETE FROM study_sessions WHERE id=? AND student_id=?",
                (session_id, student_id),
            )
    except sqlite3.Error as exc:
        raise RuntimeError(f"Could not delete session: {exc}") from exc


# ══════════════════════════════════════════════════════════════════════════════
# EXAM DATES  (scoped to student_id)
# ══════════════════════════════════════════════════════════════════════════════

def add_exam(student_id: int, subject: str, exam_label: str,
             exam_date: str, weight_pct: float) -> int:
    try:
        with get_connection() as conn:
            cur = conn.execute(
                """INSERT INTO exam_dates
                       (student_id, subject, exam_label, exam_date, weight_pct)
                   VALUES (?,?,?,?,?)""",
                (student_id, subject, exam_label.strip(), exam_date, weight_pct),
            )
            return cur.lastrowid
    except sqlite3.Error as exc:
        raise RuntimeError(f"Could not add exam: {exc}") from exc


def get_exams(student_id: int) -> list:
    try:
        with get_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM exam_dates WHERE student_id=? ORDER BY exam_date ASC",
                (student_id,),
            ).fetchall()
            return [dict(r) for r in rows]
    except sqlite3.Error as exc:
        raise RuntimeError(f"Could not load exams: {exc}") from exc


def get_upcoming_exams(student_id: int) -> list:
    today = date.today().isoformat()
    try:
        with get_connection() as conn:
            rows = conn.execute(
                """SELECT * FROM exam_dates
                   WHERE student_id=? AND exam_date >= ? AND status='Upcoming'
                   ORDER BY exam_date ASC""",
                (student_id, today),
            ).fetchall()
            return [dict(r) for r in rows]
    except sqlite3.Error as exc:
        raise RuntimeError(f"Could not load upcoming exams: {exc}") from exc


def mark_exam_done(exam_id: int, student_id: int, achieved_pct: float) -> None:
    """Update only if the exam belongs to this student (ownership check)."""
    try:
        with get_connection() as conn:
            conn.execute(
                "UPDATE exam_dates SET status='Completed', achieved_pct=? WHERE id=? AND student_id=?",
                (achieved_pct, exam_id, student_id),
            )
    except sqlite3.Error as exc:
        raise RuntimeError(f"Could not update exam: {exc}") from exc


def delete_exam(exam_id: int, student_id: int) -> None:
    """Delete only if the exam belongs to this student (ownership check)."""
    try:
        with get_connection() as conn:
            conn.execute(
                "DELETE FROM exam_dates WHERE id=? AND student_id=?",
                (exam_id, student_id),
            )
    except sqlite3.Error as exc:
        raise RuntimeError(f"Could not delete exam: {exc}") from exc