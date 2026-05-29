"""
database.py — InfoTech Study Companion
SQLite persistence layer.
DB lives at ~/.infotech_study_companion/study_companion.db
Safe across app reinstalls and updates.
"""

import sqlite3
import os
from pathlib import Path
from contextlib import contextmanager
from typing import Optional
import json


# ---------------------------------------------------------------------------
# DB path — persistent user directory, survives app updates
# ---------------------------------------------------------------------------

def get_db_path() -> str:
    app_dir = Path(os.path.expanduser("~/.infotech_study_companion"))
    app_dir.mkdir(parents=True, exist_ok=True)
    return str(app_dir / "study_companion.db")


DB_PATH = get_db_path()


# ---------------------------------------------------------------------------
# Connection context manager
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Schema — idempotent, safe to call on every boot
# ---------------------------------------------------------------------------

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

CREATE INDEX IF NOT EXISTS idx_progress_student ON chapter_progress(student_id);
"""


def initialise_database() -> None:
    """Create all tables if they do not exist. Safe to call on every startup."""
    try:
        with get_connection() as conn:
            conn.executescript(SCHEMA_SQL)
    except sqlite3.Error as exc:
        raise RuntimeError(f"DB init failed at {DB_PATH}: {exc}") from exc


# ---------------------------------------------------------------------------
# STUDENT CRUD
# ---------------------------------------------------------------------------

def upsert_student(
    name: str,
    grade: str,
    dream_job: str,
    return_time: str,
    sleep_time: str,
    study_hours: int,
    subjects: list[str],
    weak_subjects: list[str],
) -> int:
    """
    Insert a new student or update the existing one (we keep a single-student
    model for a personal desktop app — id=1 is always the active user).
    Returns the student id.
    """
    subjects_json      = json.dumps(subjects)
    weak_subjects_json = json.dumps(weak_subjects)

    with get_connection() as conn:
        existing = conn.execute("SELECT id FROM students LIMIT 1").fetchone()
        if existing:
            conn.execute(
                """UPDATE students SET
                       name=?, grade=?, dream_job=?, return_time=?, sleep_time=?,
                       study_hours=?, subjects=?, weak_subjects=?,
                       updated_at=strftime('%Y-%m-%dT%H:%M:%S','now')
                   WHERE id=?""",
                (name, grade, dream_job, return_time, sleep_time,
                 study_hours, subjects_json, weak_subjects_json, existing["id"])
            )
            return existing["id"]
        else:
            cur = conn.execute(
                """INSERT INTO students
                       (name, grade, dream_job, return_time, sleep_time,
                        study_hours, subjects, weak_subjects)
                   VALUES (?,?,?,?,?,?,?,?)""",
                (name, grade, dream_job, return_time, sleep_time,
                 study_hours, subjects_json, weak_subjects_json)
            )
            return cur.lastrowid


def get_student() -> Optional[dict]:
    """
    Load the active student profile. Returns a dict with Python lists
    for subjects/weak_subjects (JSON is decoded here), or None if no
    profile has been saved yet.
    """
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
    """Wipe all student data (CASCADE removes chapter_progress too)."""
    try:
        with get_connection() as conn:
            conn.execute("DELETE FROM students")
    except sqlite3.Error as exc:
        raise RuntimeError(f"Could not delete student: {exc}") from exc


# ---------------------------------------------------------------------------
# CHAPTER PROGRESS CRUD
# ---------------------------------------------------------------------------

def initialise_chapters(student_id: int, subjects: list[str]) -> None:
    """
    Ensure every subject in the list has a chapter_progress row.
    Uses INSERT OR IGNORE so existing progress is never overwritten.
    """
    try:
        with get_connection() as conn:
            conn.executemany(
                """INSERT OR IGNORE INTO chapter_progress (student_id, subject, total_chaps, done_chaps)
                   VALUES (?, ?, 10, 0)""",
                [(student_id, s) for s in subjects]
            )
    except sqlite3.Error as exc:
        raise RuntimeError(f"Could not initialise chapters: {exc}") from exc


def get_all_chapter_progress(student_id: int) -> dict[str, dict]:
    """
    Returns {subject: {"total": N, "done": N}} for all subjects belonging
    to this student.
    """
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
    """Update or insert a chapter progress record for one subject."""
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