from __future__ import annotations

import os
from dataclasses import dataclass
from uuid import UUID

from dotenv import load_dotenv

from .errors import ConfigurationError


@dataclass(frozen=True, slots=True)
class Settings:
    client_id: str
    authority_tenant: str

    @property
    def authority(self) -> str:
        return f"https://login.microsoftonline.com/{self.authority_tenant}"


def _require_guid(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise ConfigurationError(
            f"Falta {name}. Copia .env.example a .env y completa el valor."
        )

    try:
        UUID(value)
    except ValueError as exc:
        raise ConfigurationError(f"{name} no parece un GUID válido: {value}") from exc

    return value


def _load_authority_tenant() -> str:
    value = os.getenv("AUTHORITY_TENANT", "consumers").strip()
    if not value:
        return "consumers"

    if value in {"consumers", "common", "organizations"}:
        return value

    try:
        UUID(value)
    except ValueError as exc:
        raise ConfigurationError(
            "AUTHORITY_TENANT debe ser consumers, common, organizations o un tenant ID válido."
        ) from exc

    return value


def load_settings() -> Settings:
    load_dotenv()
    return Settings(
        client_id=_require_guid("CLIENT_ID"),
        authority_tenant=_load_authority_tenant(),
    )
