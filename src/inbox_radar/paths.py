from __future__ import annotations

import os
from pathlib import Path


APP_NAME = "InboxRadar"


def app_data_dir() -> Path:
    """Return a per-user local application data directory."""
    base = os.getenv("LOCALAPPDATA")
    if base:
        root = Path(base)
    else:
        root = Path.home() / ".local" / "share"

    path = root / APP_NAME
    path.mkdir(parents=True, exist_ok=True)
    return path
