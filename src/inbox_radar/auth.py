from __future__ import annotations

from pathlib import Path

import msal
from msal_extensions import PersistedTokenCache, build_encrypted_persistence

from .config import Settings
from .errors import AuthenticationError
from .paths import app_data_dir


SCOPES = ["Mail.ReadBasic"]


class AuthService:
    """Acquire delegated Graph tokens for the signed-in user."""

    def __init__(self, settings: Settings) -> None:
        cache_path: Path = app_data_dir() / "token_cache.bin"
        persistence = build_encrypted_persistence(str(cache_path))
        token_cache = PersistedTokenCache(persistence)

        self._app = msal.PublicClientApplication(
            client_id=settings.client_id,
            authority=settings.authority,
            token_cache=token_cache,
        )

    def get_access_token(self) -> str:
        result: dict | None = None
        accounts = self._app.get_accounts()

        if accounts:
            result = self._app.acquire_token_silent(
                scopes=SCOPES,
                account=accounts[0],
            )

        if not result:
            result = self._app.acquire_token_interactive(
                scopes=SCOPES,
                prompt="select_account",
            )

        access_token = result.get("access_token") if result else None

        if access_token:
            return str(access_token)

        error = (result or {}).get("error", "unknown_error")
        description = (result or {}).get(
            "error_description",
            "No additional detail",
        )

        raise AuthenticationError(
            f"Authentication failed: {error}: {description}"
        )
