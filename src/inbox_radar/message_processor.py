from __future__ import annotations

from typing import Any

from .database import (
    get_tracked_message,
    save_tracked_message,
    update_tracked_message_mailbox_status,
    update_tracked_message_read_state,
)


_REQUIRED_NEW_MESSAGE_FIELDS = frozenset(
    {
        "id",
        "subject",
        "receivedDateTime",
        "from",
        "isRead",
    }
)

_ACTION_MARKERS = (
    "requires action",
    "action required",
    "approval required",
    "requiere una accion",
    "requiere una acci\u00f3n",
    "accion requerida",
    "acci\u00f3n requerida",
)


def _is_complete_new_message(
    event: dict[str, Any],
) -> bool:
    return _REQUIRED_NEW_MESSAGE_FIELDS.issubset(event)


def _classify_message(
    event: dict[str, Any],
) -> str:
    subject = event.get("subject") or ""
    searchable_text = subject.casefold()

    if any(
        marker in searchable_text
        for marker in _ACTION_MARKERS
    ):
        return "ACTION"

    return "IGNORE"


def _sender_fields(
    event: dict[str, Any],
) -> tuple[str, str]:
    sender = (
        (event.get("from") or {})
        .get("emailAddress")
        or {}
    )

    sender_name = sender.get("name") or ""
    sender_address = sender.get("address") or ""

    return sender_name, sender_address


def process_message_event(
    event: dict[str, Any],
) -> str:
    message_id = event.get("id")

    if not isinstance(message_id, str) or not message_id:
        return "IGNORED_NO_ID"

    tracked_message = get_tracked_message(message_id)

    if "@removed" in event:
        if tracked_message is None:
            return "IGNORED_REMOVED"

        update_tracked_message_mailbox_status(
            message_id=message_id,
            mailbox_status="REMOVED_FROM_INBOX",
        )

        return "REMOVED_TRACKED"

    if tracked_message is not None:
        update_tracked_message_mailbox_status(
            message_id=message_id,
            mailbox_status="IN_INBOX",
        )

        if (
            "isRead" in event
            and isinstance(event["isRead"], bool)
        ):
            update_tracked_message_read_state(
                message_id=message_id,
                is_read=event["isRead"],
            )

            return "UPDATED_READ_STATE"

        return "IGNORED_TRACKED_NO_SUPPORTED_CHANGES"

    if not _is_complete_new_message(event):
        return "IGNORED_PARTIAL_UNTRACKED"

    classification = _classify_message(event)

    if classification == "IGNORE":
        return "IGNORED_BY_CLASSIFIER"

    sender_name, sender_address = _sender_fields(event)

    save_tracked_message(
        message_id=message_id,
        subject=event.get("subject") or "",
        sender_name=sender_name,
        sender_address=sender_address,
        received_at=event.get("receivedDateTime"),
        web_link=event.get("webLink"),
        is_read=event["isRead"],
        classification=classification,
    )

    return "TRACKED_NEW_MESSAGE"
