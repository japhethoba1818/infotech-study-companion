"""
database.py — InfoTech Study Companion  (v2 — full upgrade)
SQLite persistence layer.
DB lives at ~/.infotech_study_companion/study_companion.db
"""

import sqlite3
import os
import shutil
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
CREATE TABLE IF NOT EXISTS students (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
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

CREATE TABLE IF NOT EXISTS chapter_progress (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id  INTEGER NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    subject     TEXT    NOT NULL,
    total_chaps INTEGER NOT NULL DEFAULT 10,
    done_chaps  INTEGER NOT NULL DEFAULT 0,
    updated_at  TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%S','now')),
    UNIQUE(student_id, subject)
);

CREATE TABLE IF NOT EXISTS study_sessions (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id      INTEGER NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    subject         TEXT    NOT NULL,
    session_date    TEXT    NOT NULL,
    duration_mins   INTEGER NOT NULL CHECK(duration_mins > 0),
    notes           TEXT    DEFAULT '',
    created_at      TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%S','now'))
);

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

CREATE INDEX IF NOT EXISTS idx_progress_student  ON chapter_progress(student_id);
CREATE INDEX IF NOT EXISTS idx_sessions_student  ON study_sessions(student_id);
CREATE INDEX IF NOT EXISTS idx_sessions_date     ON study_sessions(session_date);
CREATE INDEX IF NOT EXISTS idx_exams_student     ON exam_dates(student_id);
CREATE INDEX IF NOT EXISTS idx_exams_date        ON exam_dates(exam_date);
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
    """Copy the DB to a timestamped file in the same directory. Returns backup path."""
    src  = Path(DB_PATH)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    dest = src.parent / f"study_companion_backup_{stamp}.db"
    shutil.copy2(src, dest)
    return str(dest)


# ── STUDENT CRUD ───────────────────────────────────────────────────────────────

def upsert_student(
    name: str, grade: str, dream_job: str,
    return_time: str, sleep_time: str, study_hours: int,
    subjects: list[str], weak_subjects: list[str],
) -> int:
    subjects_json      = json.dumps(subjects)
    weak_subjects_json = json.dumps(weak_subjects)
    with get_connection() as conn:
        existing = conn.execute("SELECT id FROM students LIMIT 1").fetchone()
        if existing:
            conn.execute(
                """UPDATE students SET name=?,grade=?,dream_job=?,return_time=?,
                       sleep_time=?,study_hours=?,subjects=?,weak_subjects=?,
                       updated_at=strftime('%Y-%m-%dT%H:%M:%S','now')
                   WHERE id=?""",
                (name, grade, dream_job, return_time, sleep_time,
                 study_hours, subjects_json, weak_subjects_json, existing["id"])
            )
            return existing["id"]
        else:
            cur = conn.execute(
                """INSERT INTO students
                       (name,grade,dream_job,return_time,sleep_time,
                        study_hours,subjects,weak_subjects)
                   VALUES (?,?,?,?,?,?,?,?)""",
                (name, grade, dream_job, return_time, sleep_time,
                 study_hours, subjects_json, weak_subjects_json)
            )
            return cur.lastrowid


def get_student() -> Optional[dict]:
    try:
        with get_connection() as conn:
            row = conn.execute("SELECT * FROM students LIMIT 1").fetchone()
            if not row:
                return None
            d = dict(row)
            d["subjects"]      = json.loads(d["subjects"])
            d["weak_subjects"] = json.loads(d["weak_subjects"])
            return d
    except sqlite3.Error as exc:
        raise RuntimeError(f"Could not load student: {exc}") from exc


def delete_student() -> None:
    try:
        with get_connection() as conn:
            conn.execute("DELETE FROM students")
    except sqlite3.Error as exc:
        raise RuntimeError(f"Could not delete student: {exc}") from exc


# ── CHAPTER PROGRESS ───────────────────────────────────────────────────────────

def initialise_chapters(student_id: int, subjects: list[str]) -> None:
    try:
        with get_connection() as conn:
            conn.executemany(
                """INSERT OR IGNORE INTO chapter_progress
                       (student_id, subject, total_chaps, done_chaps)
                   VALUES (?, ?, 10, 0)""",
                [(student_id, s) for s in subjects]
            )
    except sqlite3.Error as exc:
        raise RuntimeError(f"Could not initialise chapters: {exc}") from exc


def get_all_chapter_progress(student_id: int) -> dict[str, dict]:
    try:
        with get_connection() as conn:
            rows = conn.execute(
                "SELECT subject, total_chaps, done_chaps FROM chapter_progress WHERE student_id=?",
                (student_id,)
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
                (student_id, subject, total_chaps, done_chaps)
            )
    except sqlite3.Error as exc:
        raise RuntimeError(f"Could not update chapter progress: {exc}") from exc


# ── STUDY STREAK (derived from chapter_progress update timestamps) ─────────────

def get_study_streak(student_id: int) -> int:
    """
    Count the current consecutive-day streak based on distinct session_date
    values in study_sessions. Falls back to 0 if no sessions recorded.
    """
    try:
        with get_connection() as conn:
            rows = conn.execute(
                """SELECT DISTINCT session_date FROM study_sessions
                   WHERE student_id=? ORDER BY session_date DESC""",
                (student_id,)
            ).fetchall()
        if not rows:
            return 0
        dates = [datetime.strptime(r["session_date"], "%Y-%m-%d").date() for r in rows]
        streak = 0
        check  = date.today()
        for d in dates:
            if d == check or d == check - timedelta(days=1) and streak == 0:
                # allow today or yesterday as streak start
                check = d
            if d == check:
                streak += 1
                check  = check - timedelta(days=1)
            else:
                break
        return streak
    except sqlite3.Error as exc:
        raise RuntimeError(f"Could not calculate streak: {exc}") from exc


def get_overall_completion(student_id: int) -> float:
    """Return overall syllabus completion % across all subjects (0-100)."""
    try:
        with get_connection() as conn:
            row = conn.execute(
                """SELECT ROUND(
                       100.0 * SUM(done_chaps) / NULLIF(SUM(total_chaps), 0),
                   1) AS pct
                   FROM chapter_progress WHERE student_id=?""",
                (student_id,)
            ).fetchone()
            return row["pct"] or 0.0
    except sqlite3.Error as exc:
        raise RuntimeError(f"Could not compute completion: {exc}") from exc


# ── STUDY SESSIONS ─────────────────────────────────────────────────────────────

def log_session(student_id: int, subject: str, session_date: str,
                duration_mins: int, notes: str = "") -> int:
    try:
        with get_connection() as conn:
            cur = conn.execute(
                """INSERT INTO study_sessions
                       (student_id, subject, session_date, duration_mins, notes)
                   VALUES (?,?,?,?,?)""",
                (student_id, subject, session_date, duration_mins, notes.strip())
            )
            return cur.lastrowid
    except sqlite3.Error as exc:
        raise RuntimeError(f"Could not log session: {exc}") from exc


def get_sessions(student_id: int, limit: int = 50) -> list[dict]:
    try:
        with get_connection() as conn:
            rows = conn.execute(
                """SELECT * FROM study_sessions WHERE student_id=?
                   ORDER BY session_date DESC, created_at DESC LIMIT ?""",
                (student_id, limit)
            ).fetchall()
            return [dict(r) for r in rows]
    except sqlite3.Error as exc:
        raise RuntimeError(f"Could not load sessions: {exc}") from exc


def get_hours_per_subject(student_id: int) -> list[dict]:
    """Total hours studied per subject, most studied first."""
    try:
        with get_connection() as conn:
            rows = conn.execute(
                """SELECT subject,
                       ROUND(SUM(duration_mins) / 60.0, 2) AS total_hours,
                       SUM(duration_mins) AS total_mins
                   FROM study_sessions WHERE student_id=?
                   GROUP BY subject ORDER BY total_mins DESC""",
                (student_id,)
            ).fetchall()
            return [dict(r) for r in rows]
    except sqlite3.Error as exc:
        raise RuntimeError(f"Could not aggregate hours: {exc}") from exc


def get_daily_study_trend(student_id: int, days: int = 14) -> list[dict]:
    """Minutes studied per calendar day for the last N days."""
    cutoff = (date.today() - timedelta(days=days)).isoformat()
    try:
        with get_connection() as conn:
            rows = conn.execute(
                """SELECT session_date, SUM(duration_mins) AS total_mins
                   FROM study_sessions
                   WHERE student_id=? AND session_date >= ?
                   GROUP BY session_date ORDER BY session_date""",
                (student_id, cutoff)
            ).fetchall()
            return [dict(r) for r in rows]
    except sqlite3.Error as exc:
        raise RuntimeError(f"Could not load trend: {exc}") from exc


def delete_session(session_id: int) -> None:
    try:
        with get_connection() as conn:
            conn.execute("DELETE FROM study_sessions WHERE id=?", (session_id,))
    except sqlite3.Error as exc:
        raise RuntimeError(f"Could not delete session: {exc}") from exc


# ── EXAM DATES ─────────────────────────────────────────────────────────────────

def add_exam(student_id: int, subject: str, exam_label: str,
             exam_date: str, weight_pct: float) -> int:
    try:
        with get_connection() as conn:
            cur = conn.execute(
                """INSERT INTO exam_dates
                       (student_id, subject, exam_label, exam_date, weight_pct)
                   VALUES (?,?,?,?,?)""",
                (student_id, subject, exam_label.strip(), exam_date, weight_pct)
            )
            return cur.lastrowid
    except sqlite3.Error as exc:
        raise RuntimeError(f"Could not add exam: {exc}") from exc


def get_exams(student_id: int) -> list[dict]:
    try:
        with get_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM exam_dates WHERE student_id=? ORDER BY exam_date ASC",
                (student_id,)
            ).fetchall()
            return [dict(r) for r in rows]
    except sqlite3.Error as exc:
        raise RuntimeError(f"Could not load exams: {exc}") from exc


def get_upcoming_exams(student_id: int) -> list[dict]:
    """Return exams on or after today, ordered soonest first."""
    today = date.today().isoformat()
    try:
        with get_connection() as conn:
            rows = conn.execute(
                """SELECT * FROM exam_dates
                   WHERE student_id=? AND exam_date >= ? AND status='Upcoming'
                   ORDER BY exam_date ASC""",
                (student_id, today)
            ).fetchall()
            return [dict(r) for r in rows]
    except sqlite3.Error as exc:
        raise RuntimeError(f"Could not load upcoming exams: {exc}") from exc


def mark_exam_done(exam_id: int, achieved_pct: float) -> None:
    try:
        with get_connection() as conn:
            conn.execute(
                "UPDATE exam_dates SET status='Completed', achieved_pct=? WHERE id=?",
                (achieved_pct, exam_id)
            )
    except sqlite3.Error as exc:
        raise RuntimeError(f"Could not update exam: {exc}") from exc


def delete_exam(exam_id: int) -> None:
    try:
        with get_connection() as conn:
            conn.execute("DELETE FROM exam_dates WHERE id=?", (exam_id,))
    except sqlite3.Error as exc:
        raise RuntimeError(f"Could not delete exam: {exc}") from exc