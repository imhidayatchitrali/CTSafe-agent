from __future__ import annotations

import json
import logging
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

logger = logging.getLogger(__name__)


class SupabaseRepositoryError(RuntimeError):
    pass


class SupabaseRestClient:
    """Narrow PostgREST client for backend repositories.

    This is intentionally small: runtime code can only reach the tables and
    methods exposed by repositories, not a broad Supabase admin surface.
    """

    def __init__(self, supabase_url: str, api_key: str, timeout_seconds: float = 15.0):
        self.base_url = supabase_url.rstrip("/")
        self.api_key = api_key
        self.timeout_seconds = timeout_seconds

    def insert(self, table: str, payload: dict[str, Any]) -> dict[str, Any]:
        rows = self._request(
            method="POST",
            path=table,
            payload=payload,
            extra_headers={"Prefer": "return=representation"},
        )
        return self._single_row(table, rows)

    def select_one(
        self,
        table: str,
        filters: dict[str, Any],
        select: str = "*",
    ) -> dict[str, Any]:
        rows = self.select(table=table, filters=filters, select=select, limit=1)
        if not rows:
            raise KeyError(f"{table} row not found for filters {filters}")
        return rows[0]

    def select(
        self,
        table: str,
        filters: dict[str, Any] | None = None,
        select: str = "*",
        order: str | None = None,
        limit: int | None = None,
    ) -> list[dict[str, Any]]:
        query: dict[str, Any] = {"select": select}
        for key, value in (filters or {}).items():
            query[key] = f"eq.{value}"
        if order:
            query["order"] = order
        if limit is not None:
            query["limit"] = str(limit)
        rows = self._request(method="GET", path=table, query=query)
        if not isinstance(rows, list):
            raise SupabaseRepositoryError(f"Expected list response from {table}")
        return rows

    def search_text(
        self,
        table: str,
        terms: list[str],
        select: str = "id,content,metadata",
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        clauses = [f"content.ilike.*{term}*" for term in terms if term.strip()]
        if not clauses:
            return []
        query: dict[str, Any] = {"select": select, "limit": str(limit)}
        if len(clauses) == 1:
            query["content"] = clauses[0].removeprefix("content.")
        else:
            query["or"] = f"({','.join(clauses)})"
        rows = self._request(method="GET", path=table, query=query)
        if not isinstance(rows, list):
            raise SupabaseRepositoryError(f"Expected list response from {table}")
        return rows

    def update(
        self,
        table: str,
        filters: dict[str, Any],
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        query = {key: f"eq.{value}" for key, value in filters.items()}
        rows = self._request(
            method="PATCH",
            path=table,
            query=query,
            payload=payload,
            extra_headers={"Prefer": "return=representation"},
        )
        return self._single_row(table, rows)

    def rpc(self, function_name: str, payload: dict[str, Any]) -> Any:
        return self._request(
            method="POST",
            path=f"rpc/{function_name}",
            payload=payload,
        )

    def _request(
        self,
        method: str,
        path: str,
        query: dict[str, Any] | None = None,
        payload: dict[str, Any] | None = None,
        extra_headers: dict[str, str] | None = None,
    ) -> Any:
        encoded_query = f"?{urlencode(query)}" if query else ""
        url = f"{self.base_url}/rest/v1/{path}{encoded_query}"
        data = json.dumps(payload).encode("utf-8") if payload is not None else None
        headers = {
            "apikey": self.api_key,
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        headers.update(extra_headers or {})
        request = Request(url=url, data=data, headers=headers, method=method)
        try:
            with urlopen(request, timeout=self.timeout_seconds) as response:
                body = response.read().decode("utf-8")
        except HTTPError as exc:
            detail = exc.read().decode("utf-8")
            logger.error("supabase.rest.http_error", extra={"table_path": path})
            raise SupabaseRepositoryError(
                f"Supabase REST {method} {path} failed: HTTP {exc.code} {detail}"
            ) from exc
        except URLError as exc:
            logger.error("supabase.rest.url_error", extra={"table_path": path})
            raise SupabaseRepositoryError(
                f"Supabase REST {method} {path} failed: {exc.reason}"
            ) from exc

        if body == "":
            return []
        return json.loads(body)

    def _single_row(self, table: str, rows: Any) -> dict[str, Any]:
        if not isinstance(rows, list) or not rows:
            raise SupabaseRepositoryError(f"Expected returned row from {table}")
        if not isinstance(rows[0], dict):
            raise SupabaseRepositoryError(f"Expected object row from {table}")
        return rows[0]
