from __future__ import annotations

from datetime import UTC, datetime

from .auth import AuthService
from .config import load_settings
from .database import initialize_database
from .delta_state import load_delta_link, save_delta_link
from .errors import InboxRadarError
from .graph import DeltaPage, GraphClient
from .message_processor import process_message_event
from .windows_protection import build_message_ref


def _drain_delta(
    client: GraphClient,
    first_page: DeltaPage,
) -> tuple[list[dict], str]:
    changes: list[dict] = []
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


def run() -> None:
    initialize_database()

    settings = load_settings()
    token = AuthService(settings).get_access_token()
    client = GraphClient(token)

    saved_link = load_delta_link()

    if not saved_link:
        cutoff = (
            datetime.now(UTC)
            .replace(microsecond=0)
            .isoformat()
            .replace("+00:00", "Z")
        )

        print("BASELINE_START")

        first_page = client.start_delta(cutoff)
        changes, delta_link = _drain_delta(
            client,
            first_page,
        )

        save_delta_link(delta_link)

        print(
            f"BASELINE_DONE changes_seen={len(changes)}"
        )

        return

    print("DELTA_SYNC_START")

    first_page = client.follow_delta_link(saved_link)
    changes, delta_link = _drain_delta(
        client,
        first_page,
    )

    if not changes:
        save_delta_link(delta_link)
        print("DELTA_SYNC_DONE changes=0")
        return

    for message in changes:
        result = process_message_event(message)

        message_ref = build_message_ref(
            message.get("id")
        )

        print(
            f"EVENT result={result} ref={message_ref}"
        )

    save_delta_link(delta_link)

    print(
        f"DELTA_SYNC_DONE changes={len(changes)}"
    )


def main() -> None:
    try:
        run()

    except InboxRadarError as exc:
        raise SystemExit(
            f"ERROR: {exc}"
        ) from exc

    except KeyboardInterrupt:
        raise SystemExit(
            "Cancelled by user."
        ) from None


if __name__ == "__main__":
    main()
