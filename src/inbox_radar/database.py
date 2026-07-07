from __future__ import annotations

import sqlite3
from contextlib import closing
from pathlib import Path

from .paths import app_data_dir


DATABASE_FILE: Path = app_data_dir() / "inbox_radar.db"


def connect() -> sqlite3.Connection:
    connection = sqlite3.connect(DATABASE_FILE)
    connection.row_factory = sqlite3.Row
    return connection


def initialize_database() -> None:
    with closing(connect()) as connection:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS sync_state (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS tracked_messages (
                message_id TEXT PRIMARY KEY,
                subject TEXT NOT NULL DEFAULT '',
                sender_name TEXT NOT NULL DEFAULT '',
                sender_address TEXT NOT NULL DEFAULT '',
                received_at TEXT,
                body_preview TEXT NOT NULL DEFAULT '',
                web_link TEXT,
                is_read INTEGER NOT NULL DEFAULT 0,

                classification TEXT NOT NULL DEFAULT 'UNCLASSIFIED',
                attention_status TEXT NOT NULL DEFAULT 'PENDING',

                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            """
        )
        connection.commit()

def get_sync_state(key: str) -> str | None:
    with closing(connect()) as connection:
        row = connection.execute(
            "SELECT value FROM sync_state WHERE key = ?",
            (key,),
        ).fetchone()

    return str(row["value"]) if row else None


def set_sync_state(key: str, value: str) -> None:
    with closing(connect()) as connection:
        connection.execute(
            """
            INSERT INTO sync_state (key, value)
            VALUES (?, ?)
            ON CONFLICT(key) DO UPDATE SET
                value = excluded.value
            """,
            (key, value),
        )
        connection.commit()

def get_tracked_message(message_id: str) -> sqlite3.Row | None:
    with closing(connect()) as connection:
        return connection.execute(
            """
            SELECT *
            FROM tracked_messages
            WHERE message_id = ?
            """,
            (message_id,),
        ).fetchone()


def save_tracked_message(
    *,
    message_id: str,
    subject: str,
    sender_name: str,
    sender_address: str,
    received_at: str | None,
    body_preview: str,
    web_link: str | None,
    is_read: bool,
    classification: str,
) -> None:
    with closing(connect()) as connection:
        connection.execute(
            """
            INSERT INTO tracked_messages (
                message_id,
                subject,
                sender_name,
                sender_address,
                received_at,
                body_preview,
                web_link,
                is_read,
                classification
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(message_id) DO UPDATE SET
                subject = excluded.subject,
                sender_name = excluded.sender_name,
                sender_address = excluded.sender_address,
                received_at = excluded.received_at,
                body_preview = excluded.body_preview,
                web_link = excluded.web_link,
                is_read = excluded.is_read,
                classification = excluded.classification,
                updated_at = CURRENT_TIMESTAMP
            """,
            (
                message_id,
                subject,
                sender_name,
                sender_address,
                received_at,
                body_preview,
                web_link,
                int(is_read),
                classification,
            ),
        )
        connection.commit()


def update_tracked_message_read_state(
    message_id: str,
    is_read: bool,
) -> bool:
    with closing(connect()) as connection:
        cursor = connection.execute(
            """
            UPDATE tracked_messages
            SET
                is_read = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE message_id = ?
            """,
            (int(is_read), message_id),
        )
        connection.commit()
        return cursor.rowcount > 0
