from __future__ import annotations

import sqlite3
from contextlib import closing
from datetime import datetime

from backend.config import DATABASE_DIR, DATABASE_PATH, DEFAULT_CONTACTS


def get_connection() -> sqlite3.Connection:
    DATABASE_DIR.mkdir(parents=True, exist_ok=True)
    return sqlite3.connect(DATABASE_PATH)


def init() -> None:
    with closing(get_connection()) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS commands (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                command TEXT NOT NULL,
                intent TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS notes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                content TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS reminders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                kind TEXT NOT NULL,
                target TEXT,
                message TEXT,
                trigger_at TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'pending',
                created_at TEXT NOT NULL
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS contacts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                phone TEXT,
                email TEXT,
                whatsapp_name TEXT,
                created_at TEXT NOT NULL
            )
            """
        )
        conn.commit()
    seed_default_contacts()


def log_command(command: str, intent: str) -> None:
    timestamp = datetime.now().isoformat(timespec="seconds")
    with closing(get_connection()) as conn:
        conn.execute(
            "INSERT INTO commands (command, intent, created_at) VALUES (?, ?, ?)",
            (command, intent, timestamp),
        )
        conn.commit()


def save_note(content: str) -> None:
    timestamp = datetime.now().isoformat(timespec="seconds")
    with closing(get_connection()) as conn:
        conn.execute(
            "INSERT INTO notes (content, created_at) VALUES (?, ?)",
            (content, timestamp),
        )
        conn.commit()


def create_reminder(kind: str, trigger_at: str, target: str | None = None, message: str | None = None) -> None:
    timestamp = datetime.now().isoformat(timespec="seconds")
    with closing(get_connection()) as conn:
        conn.execute(
            """
            INSERT INTO reminders (kind, target, message, trigger_at, status, created_at)
            VALUES (?, ?, ?, ?, 'pending', ?)
            """,
            (kind, target, message, trigger_at, timestamp),
        )
        conn.commit()


def get_due_reminders(now_iso: str) -> list[sqlite3.Row]:
    with closing(get_connection()) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.execute(
            """
            SELECT id, kind, target, message, trigger_at
            FROM reminders
            WHERE status = 'pending' AND trigger_at <= ?
            ORDER BY trigger_at ASC
            """,
            (now_iso,),
        )
        return list(cursor.fetchall())


def mark_reminder_done(reminder_id: int) -> None:
    with closing(get_connection()) as conn:
        conn.execute("UPDATE reminders SET status = 'done' WHERE id = ?", (reminder_id,))
        conn.commit()


def upsert_contact(
    name: str,
    phone: str | None = None,
    email: str | None = None,
    whatsapp_name: str | None = None,
) -> None:
    timestamp = datetime.now().isoformat(timespec="seconds")
    with closing(get_connection()) as conn:
        conn.execute(
            """
            INSERT INTO contacts (name, phone, email, whatsapp_name, created_at)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(name) DO UPDATE SET
                phone = COALESCE(excluded.phone, contacts.phone),
                email = COALESCE(excluded.email, contacts.email),
                whatsapp_name = COALESCE(excluded.whatsapp_name, contacts.whatsapp_name)
            """,
            (name.lower(), phone, email, whatsapp_name, timestamp),
        )
        conn.commit()


def get_contact(name: str) -> sqlite3.Row | None:
    with closing(get_connection()) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.execute(
            """
            SELECT id, name, phone, email, whatsapp_name
            FROM contacts
            WHERE name = ?
            """,
            (name.lower(),),
        )
        return cursor.fetchone()


def seed_default_contacts() -> None:
    for contact in DEFAULT_CONTACTS:
        upsert_contact(
            contact["name"],
            phone=contact.get("phone"),
            email=contact.get("email"),
            whatsapp_name=contact.get("whatsapp_name"),
        )
