from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import requests

from .errors import GraphApiError


GRAPH_ROOT = "https://graph.microsoft.com/v1.0"
IMMUTABLE_ID_HEADER = 'IdType="ImmutableId"'
DELTA_SELECT = "id,subject,receivedDateTime,from,isRead,webLink"


@dataclass(frozen=True, slots=True)
class DeltaPage:
    messages: list[dict[str, Any]]
    next_link: str | None
    delta_link: str | None


class GraphClient:
    def __init__(self, access_token: str) -> None:
        self._session = requests.Session()
        self._session.headers.update(
            {
                "Authorization": f"Bearer {access_token}",
                "Accept": "application/json",
                "Prefer": IMMUTABLE_ID_HEADER,
            }
        )

    def close(self) -> None:
        self._session.close()

    def _get(
        self,
        url: str,
        *,
        params: dict[str, str | int] | None = None,
    ) -> dict[str, Any]:
        response = self._session.get(
            url,
            params=params,
            timeout=30,
        )

        if response.status_code >= 400:
            raise GraphApiError(
                f"Graph request failed with HTTP {response.status_code}."
            )

        return response.json()

    def start_delta(self, received_from_utc: str) -> DeltaPage:
        data = self._get(
            f"{GRAPH_ROOT}/me/mailFolders/inbox/messages/delta",
            params={
                "$select": DELTA_SELECT,
                "$filter": f"receivedDateTime ge {received_from_utc}",
            },
        )

        return self._to_delta_page(data)

    def follow_delta_link(self, url: str) -> DeltaPage:
        return self._to_delta_page(self._get(url))

    @staticmethod
    def _to_delta_page(data: dict[str, Any]) -> DeltaPage:
        return DeltaPage(
            messages=list(data.get("value", [])),
            next_link=data.get("@odata.nextLink"),
            delta_link=data.get("@odata.deltaLink"),
        )
