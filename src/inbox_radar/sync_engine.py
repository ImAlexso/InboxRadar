from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, Literal

from .delta_state import load_delta_link, save_delta_link
from .errors import InboxRadarError
from .graph import DeltaPage, GraphClient
from .message_processor import process_message_event
from .windows_protection import build_message_ref


@dataclass(frozen=True, slots=True)
class ProcessedEvent:
    result: str
    message_ref: str


@dataclass(frozen=True, slots=True)
class SyncReport:
    mode: Literal["BASELINE", "DELTA"]
    changes_seen: int
    events: tuple[ProcessedEvent, ...]


def _drain_delta(
    client: GraphClient,
    first_page: DeltaPage,
) -> tuple[list[dict[str, Any]], str]:
    changes: list[dict[str, Any]] = []
    page = first_page

    while True:
        changes.extend(page.messages)

        if page.next_link:
            page = client.follow_delta_link(page.next_link)
            continue

        if not page.delta_link:
            raise InboxRadarError(
                "Delta completed without a deltaLink."
            )

        return changes, page.delta_link


def sync_once(client: GraphClient) -> SyncReport:
    saved_link = load_delta_link()

    if not saved_link:
        cutoff = (
            datetime.now(UTC)
            .replace(microsecond=0)
            .isoformat()
            .replace("+00:00", "Z")
        )

        first_page = client.start_delta(cutoff)
        changes, delta_link = _drain_delta(
            client,
            first_page,
        )

        save_delta_link(delta_link)

        return SyncReport(
            mode="BASELINE",
            changes_seen=len(changes),
            events=(),
        )

    first_page = client.follow_delta_link(saved_link)
    changes, delta_link = _drain_delta(
        client,
        first_page,
    )

    processed_events: list[ProcessedEvent] = []

    for message in changes:
        result = process_message_event(message)

        processed_events.append(
            ProcessedEvent(
                result=result,
                message_ref=build_message_ref(
                    message.get("id")
                ),
            )
        )

    save_delta_link(delta_link)

    return SyncReport(
        mode="DELTA",
        changes_seen=len(changes),
        events=tuple(processed_events),
    )
