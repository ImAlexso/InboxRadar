from __future__ import annotations

from .auth import AuthService
from .config import load_settings
from .database import (
    count_pending_messages,
    initialize_database,
)
from .errors import InboxRadarError
from .graph import GraphClient
from .sync_engine import sync_once


def run() -> None:
    initialize_database()

    settings = load_settings()
    token = AuthService(settings).get_access_token()
    client = GraphClient(token)

    print("SYNC_START")

    report = sync_once(client)

    if report.mode == "BASELINE":
        print(
            "BASELINE_DONE "
            f"changes_seen={report.changes_seen}"
        )

        return

    for event in report.events:
        print(
            f"EVENT result={event.result} "
            f"ref={event.message_ref}"
        )

    print(
        f"DELTA_SYNC_DONE "
        f"changes={report.changes_seen} "
        f"pending={count_pending_messages()}"
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
