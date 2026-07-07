from __future__ import annotations

import sqlite3
from contextlib import closing
from pathlib import Path

from .paths import app_data_dir
from .windows_protection import (
    build_message_key,
    protect_text,
    unprotect_text,
)


DATABASE_FILE: Path = app_data_dir() / "inbox_radar.db"


def connect() -> sqlite3.Connection:
    connection = sqlite3.connect(DATABASE_FILE)
    connection.row_factory = sqlite3.Row

    connection.execute("PRAGMA secure_delete = ON")
    connection.execute("PRAGMA temp_store = MEMORY")

    return connection


def _protected_blob(
    value: str | None,
) -> sqlite3.Binary | None:
    protected = protect_text(value)

    if protected is None:
        return None

    return sqlite3.Binary(protected)


def initialize_database() -> None:
    with closing(connect()) as connection:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS sync_state (
                key TEXT PRIMARY KEY,
                protected_value BLOB NOT NULL
            );

            CREATE TABLE IF NOT EXISTS tracked_messages (
                message_key TEXT PRIMARY KEY,

                subject_protected BLOB NOT NULL,
                sender_name_protected BLOB NOT NULL,
                sender_address_protected BLOB NOT NULL,
                received_at_protected BLOB,
                web_link_protected BLOB,

                is_read INTEGER NOT NULL DEFAULT 0,

                classification TEXT NOT NULL,
                attention_status TEXT NOT NULL DEFAULT 'PENDING',
                mailbox_status TEXT NOT NULL DEFAULT 'IN_INBOX',

                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            """
        )

        connection.commit()


def get_sync_state(key: str) -> str | None:
    with closing(connect()) as connection:
        row = connection.execute(
            """
            SELECT protected_value
            FROM sync_state
            WHERE key = ?
            """,
            (key,),
        ).fetchone()

    if row is None:
        return None

    return unprotect_text(
        bytes(row["protected_value"])
    )


def set_sync_state(key: str, value: str) -> None:
    with closing(connect()) as connection:
        connection.execute(
            """
            INSERT INTO sync_state (
                key,
                protected_value
            )
            VALUES (?, ?)
            ON CONFLICT(key) DO UPDATE SET
                protected_value = excluded.protected_value
            """,
            (
                key,
                _protected_blob(value),
            ),
        )

        connection.commit()


def get_tracked_message(
    message_id: str,
) -> sqlite3.Row | None:
    message_key = build_message_key(message_id)

    with closing(connect()) as connection:
        return connection.execute(
            """
            SELECT *
            FROM tracked_messages
            WHERE message_key = ?
            """,
            (message_key,),
        ).fetchone()


def save_tracked_message(
    *,
    message_id: str,
    subject: str,
    sender_name: str,
    sender_address: str,
    received_at: str | None,
    web_link: str | None,
    is_read: bool,
    classification: str,
) -> None:
    message_key = build_message_key(message_id)

    with closing(connect()) as connection:
        connection.execute(
            """
            INSERT INTO tracked_messages (
                message_key,
                subject_protected,
                sender_name_protected,
                sender_address_protected,
                received_at_protected,
                web_link_protected,
                is_read,
                classification
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(message_key) DO UPDATE SET
                subject_protected = excluded.subject_protected,
                sender_name_protected = excluded.sender_name_protected,
                sender_address_protected = excluded.sender_address_protected,
                received_at_protected = excluded.received_at_protected,
                web_link_protected = excluded.web_link_protected,
                is_read = excluded.is_read,
                classification = excluded.classification,
                mailbox_status = 'IN_INBOX',
                updated_at = CURRENT_TIMESTAMP
            """,
            (
                message_key,
                _protected_blob(subject),
                _protected_blob(sender_name),
                _protected_blob(sender_address),
                _protected_blob(received_at),
                _protected_blob(web_link),
                int(is_read),
                classification,
            ),
        )

        connection.commit()


def update_tracked_message_read_state(
    message_id: str,
    is_read: bool,
) -> bool:
    message_key = build_message_key(message_id)

    with closing(connect()) as connection:
        cursor = connection.execute(
            """
            UPDATE tracked_messages
            SET
                is_read = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE message_key = ?
            """,
            (
                int(is_read),
                message_key,
            ),
        )

        connection.commit()

        return cursor.rowcount > 0


def update_tracked_message_mailbox_status(
    message_id: str,
    mailbox_status: str,
) -> bool:
    message_key = build_message_key(message_id)

    with closing(connect()) as connection:
        cursor = connection.execute(
            """
            UPDATE tracked_messages
            SET
                mailbox_status = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE message_key = ?
            """,
            (
                mailbox_status,
                message_key,
            ),
        )

        connection.commit()

        return cursor.rowcount > 0


def _unprotect_database_text(
    value: object,
) -> str | None:
    if value is None:
        return None

    return unprotect_text(bytes(value))


def list_pending_messages() -> list[dict[str, object]]:
    with closing(connect()) as connection:
        rows = connection.execute(
            """
            SELECT *
            FROM tracked_messages
            WHERE attention_status = 'PENDING'
            ORDER BY created_at DESC
            """
        ).fetchall()

    pending_messages: list[dict[str, object]] = []

    for row in rows:
        pending_messages.append(
            {
                "message_key": row["message_key"],
                "subject": _unprotect_database_text(
                    row["subject_protected"]
                ),
                "sender_name": _unprotect_database_text(
                    row["sender_name_protected"]
                ),
                "sender_address": _unprotect_database_text(
                    row["sender_address_protected"]
                ),
                "received_at": _unprotect_database_text(
                    row["received_at_protected"]
                ),
                "web_link": _unprotect_database_text(
                    row["web_link_protected"]
                ),
                "is_read": bool(row["is_read"]),
                "classification": row["classification"],
                "attention_status": row["attention_status"],
                "mailbox_status": row["mailbox_status"],
                "created_at": row["created_at"],
                "updated_at": row["updated_at"],
            }
        )

    return pending_messages


def count_pending_messages() -> int:
    with closing(connect()) as connection:
        row = connection.execute(
            """
            SELECT COUNT(*) AS total
            FROM tracked_messages
            WHERE attention_status = 'PENDING'
            """
        ).fetchone()

    return int(row["total"])


def _update_attention_status(
    message_key: str,
    attention_status: str,
) -> bool:
    allowed_statuses = {
        "PENDING",
        "MANAGED",
        "IGNORED",
    }

    if attention_status not in allowed_statuses:
        raise ValueError(
            f"Unsupported attention status: {attention_status}"
        )

    with closing(connect()) as connection:
        cursor = connection.execute(
            """
            UPDATE tracked_messages
            SET
                attention_status = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE message_key = ?
            """,
            (
                attention_status,
                message_key,
            ),
        )

        connection.commit()

        return cursor.rowcount > 0


def mark_message_managed(message_key: str) -> bool:
    return _update_attention_status(
        message_key=message_key,
        attention_status="MANAGED",
    )


def mark_message_ignored(message_key: str) -> bool:
    return _update_attention_status(
        message_key=message_key,
        attention_status="IGNORED",
    )
