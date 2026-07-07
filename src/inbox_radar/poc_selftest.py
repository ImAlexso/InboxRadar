from __future__ import annotations

import os
import tempfile
from contextlib import closing


def _require(
    condition: bool,
    message: str,
) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        os.environ["LOCALAPPDATA"] = temp_dir

        from .database import (
            DATABASE_FILE,
            connect,
            count_pending_messages,
            get_sync_state,
            get_tracked_message,
            initialize_database,
            list_pending_messages,
            mark_message_managed,
            set_sync_state,
        )
        from .message_processor import process_message_event

        initialize_database()

        irrelevant_event = {
            "id": "selftest-irrelevant-001",
            "subject": "Weekly newsletter",
            "receivedDateTime": "2026-07-07T12:00:00Z",
            "from": {
                "emailAddress": {
                    "name": "Newsletter",
                    "address": "newsletter@example.com",
                }
            },
            "isRead": False,
            "webLink": "https://example.com/irrelevant",
        }

        action_event = {
            "id": "selftest-action-001",
            "subject": "Action required - Secure POC",
            "receivedDateTime": "2026-07-07T12:01:00Z",
            "from": {
                "emailAddress": {
                    "name": "Secure Sender",
                    "address": "sender@example.com",
                }
            },
            "isRead": False,
            "webLink": "https://example.com/action",
        }

        _require(
            process_message_event(irrelevant_event)
            == "IGNORED_BY_CLASSIFIER",
            "Irrelevant message was not ignored.",
        )

        _require(
            process_message_event(action_event)
            == "TRACKED_NEW_MESSAGE",
            "Action message was not tracked.",
        )

        _require(
            process_message_event(action_event)
            == "IGNORED_DUPLICATE_STATE",
            "Duplicate event was not idempotent.",
        )

        read_update = {
            "id": "selftest-action-001",
            "isRead": True,
        }

        _require(
            process_message_event(read_update)
            == "UPDATED_READ_STATE",
            "Read state was not updated.",
        )

        _require(
            process_message_event(read_update)
            == "IGNORED_DUPLICATE_STATE",
            "Duplicate read state was not ignored.",
        )

        removed_event = {
            "id": "selftest-action-001",
            "@removed": {
                "reason": "deleted",
            },
        }

        _require(
            process_message_event(removed_event)
            == "REMOVED_TRACKED",
            "Tracked removal was not processed.",
        )

        tracked = get_tracked_message(
            "selftest-action-001"
        )

        _require(
            tracked is not None,
            "Tracked row disappeared after removal.",
        )

        _require(
            tracked["attention_status"] == "PENDING",
            "Removal changed attention status.",
        )

        _require(
            tracked["mailbox_status"]
            == "REMOVED_FROM_INBOX",
            "Mailbox status was not updated.",
        )

        _require(
            process_message_event(removed_event)
            == "IGNORED_DUPLICATE_REMOVED",
            "Duplicate removal was not idempotent.",
        )

        restored_event = dict(action_event)
        restored_event["isRead"] = True

        _require(
            process_message_event(restored_event)
            == "RESTORED_TO_INBOX",
            "Message was not restored to Inbox.",
        )

        set_sync_state(
            "inbox_delta_link",
            "https://graph.microsoft.com/private-delta-token",
        )

        _require(
            get_sync_state("inbox_delta_link")
            == "https://graph.microsoft.com/private-delta-token",
            "Protected sync state could not be restored.",
        )

        with closing(connect()) as connection:
            row_count = connection.execute(
                """
                SELECT COUNT(*) AS total
                FROM tracked_messages
                """
            ).fetchone()["total"]

        _require(
            row_count == 1,
            "Idempotence failed: duplicate rows exist.",
        )

        pending = list_pending_messages()

        _require(
            len(pending) == 1,
            "Expected exactly one pending message.",
        )

        _require(
            pending[0]["subject"]
            == "Action required - Secure POC",
            "Protected subject could not be restored.",
        )

        raw_database = DATABASE_FILE.read_bytes()

        forbidden_plaintext = (
            b"Action required - Secure POC",
            b"sender@example.com",
            b"https://example.com/action",
            b"https://graph.microsoft.com/private-delta-token",
        )

        for value in forbidden_plaintext:
            _require(
                value not in raw_database,
                "Sensitive plaintext found in SQLite.",
            )

        _require(
            mark_message_managed(
                str(pending[0]["message_key"])
            ),
            "Pending message could not be managed.",
        )

        _require(
            count_pending_messages() == 0,
            "Managed message remained pending.",
        )

        print(
            "SELFTEST_PASS "
            "checks=security,idempotence,lifecycle"
        )


if __name__ == "__main__":
    main()
