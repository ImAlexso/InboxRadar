from __future__ import annotations

import subprocess
import webbrowser
from dataclasses import dataclass
from enum import Enum
from urllib.parse import urlsplit

from .auth import AuthService
from .config import load_settings
from .database import (
    count_pending_messages,
    get_pending_message,
    initialize_database,
    list_pending_messages,
    mark_message_ignored,
    mark_message_managed,
)
from .graph import GraphClient
from .sync_engine import sync_once


class OpenPendingResult(Enum):
    OPENED = "OPENED"
    NOT_PENDING = "NOT_PENDING"
    INVALID_LINK = "INVALID_LINK"
    BROWSER_UNAVAILABLE = "BROWSER_UNAVAILABLE"
    FAILED = "FAILED"


@dataclass(frozen=True, slots=True)
class ApplicationSyncResult:
    mode: str
    changes_seen: int
    new_pending_keys: tuple[str, ...]
    pending_count: int


class ApplicationService:
    """Application boundary used by the desktop UI."""

    def __init__(self) -> None:
        initialize_database()

        self._settings = load_settings()

        self._auth_service = AuthService(
            self._settings
        )

    def sync_now(self) -> ApplicationSyncResult:
        token = self._auth_service.get_access_token()

        client = GraphClient(token)

        try:
            report = sync_once(client)

        finally:
            client.close()

        new_pending_keys = tuple(
            event.message_key
            for event in report.events
            if (
                event.result
                == "TRACKED_NEW_MESSAGE"
                and event.message_key is not None
            )
        )

        return ApplicationSyncResult(
            mode=report.mode,
            changes_seen=report.changes_seen,
            new_pending_keys=new_pending_keys,
            pending_count=(
                count_pending_messages()
            ),
        )

    def list_pending(
        self,
    ) -> list[dict[str, object]]:
        return list_pending_messages()

    def get_pending(
        self,
        message_key: str,
    ) -> dict[str, object] | None:
        return get_pending_message(message_key)

    def count_pending(self) -> int:
        return count_pending_messages()

    def mark_managed(
        self,
        message_key: str,
    ) -> bool:
        return mark_message_managed(message_key)

    def mark_ignored(
        self,
        message_key: str,
    ) -> bool:
        return mark_message_ignored(message_key)

    def open_pending(
        self,
        message_key: str,
    ) -> OpenPendingResult:
        message = get_pending_message(
            message_key
        )

        if message is None:
            return OpenPendingResult.NOT_PENDING

        web_link = str(
            message.get("web_link")
            or ""
        ).strip()

        parsed_url = urlsplit(web_link)

        if (
            parsed_url.scheme.lower()
            not in {"http", "https"}
            or not parsed_url.netloc
        ):
            return OpenPendingResult.INVALID_LINK

        browser_path = self._settings.browser_path

        try:
            if browser_path is not None:
                if not browser_path.is_file():
                    return (
                        OpenPendingResult
                        .BROWSER_UNAVAILABLE
                    )

                subprocess.Popen(
                    [
                        str(browser_path),
                        web_link,
                    ],
                    stdin=subprocess.DEVNULL,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )

                return OpenPendingResult.OPENED

            if webbrowser.open(
                web_link,
                new=2,
            ):
                return OpenPendingResult.OPENED

            return OpenPendingResult.FAILED

        except OSError:
            return OpenPendingResult.FAILED
