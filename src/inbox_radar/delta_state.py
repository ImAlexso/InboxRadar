from __future__ import annotations

from .database import get_sync_state, set_sync_state


INBOX_DELTA_LINK_KEY = "inbox_delta_link"


def load_delta_link() -> str | None:
    return get_sync_state(INBOX_DELTA_LINK_KEY)


def save_delta_link(delta_link: str) -> None:
    set_sync_state(INBOX_DELTA_LINK_KEY, delta_link)
