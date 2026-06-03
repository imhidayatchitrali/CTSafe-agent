from __future__ import annotations

import json
import logging
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

logger = logging.getLogger(__name__)


class EmbeddingProviderError(RuntimeError):
    pass


class OpenAIEmbeddingProvider:
    """Small embeddings client for the backend RAG tool."""

    def __init__(
        self,
        api_key: str,
        model: str = "text-embedding-3-small",
        timeout_seconds: float = 30.0,
    ):
        self.api_key = api_key
        self.model = model
        self.timeout_seconds = timeout_seconds

    def embed(self, text: str) -> list[float]:
        payload = {"model": self.model, "input": text}
        request = Request(
            url="https://api.openai.com/v1/embeddings",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
            method="POST",
        )
        try:
            with urlopen(request, timeout=self.timeout_seconds) as response:
                body = json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            detail = exc.read().decode("utf-8")
            logger.error("embedding.openai.http_error")
            raise EmbeddingProviderError(
                f"OpenAI embedding request failed: HTTP {exc.code} {detail}"
            ) from exc
        except URLError as exc:
            logger.error("embedding.openai.url_error")
            raise EmbeddingProviderError(
                f"OpenAI embedding request failed: {exc.reason}"
            ) from exc

        data = body.get("data") or []
        if not data or "embedding" not in data[0]:
            raise EmbeddingProviderError("OpenAI embedding response did not include data[0].embedding")
        embedding = data[0]["embedding"]
        if not isinstance(embedding, list):
            raise EmbeddingProviderError("OpenAI embedding response embedding is not a list")
        return [float(value) for value in embedding]


class OpenRouterEmbeddingProvider:
    """OpenRouter embeddings client for the backend RAG tool."""

    def __init__(
        self,
        api_key: str,
        model: str = "openai/text-embedding-3-small",
        base_url: str = "https://openrouter.ai/api/v1",
        http_referer: str | None = None,
        app_title: str = "CT Safe DVR Agent",
        timeout_seconds: float = 30.0,
    ):
        self.api_key = api_key
        self.model = self._normalize_model(model)
        self.base_url = base_url.rstrip("/")
        self.http_referer = http_referer
        self.app_title = app_title
        self.timeout_seconds = timeout_seconds

    def embed(self, text: str) -> list[float]:
        payload = {"model": self.model, "input": text, "encoding_format": "float"}
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "X-OpenRouter-Title": self.app_title,
        }
        if self.http_referer:
            headers["HTTP-Referer"] = self.http_referer
        request = Request(
            url=f"{self.base_url}/embeddings",
            data=json.dumps(payload).encode("utf-8"),
            headers=headers,
            method="POST",
        )
        try:
            with urlopen(request, timeout=self.timeout_seconds) as response:
                body = json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            detail = exc.read().decode("utf-8")
            logger.error("embedding.openrouter.http_error")
            raise EmbeddingProviderError(
                f"OpenRouter embedding request failed: HTTP {exc.code} {detail}"
            ) from exc
        except URLError as exc:
            logger.error("embedding.openrouter.url_error")
            raise EmbeddingProviderError(
                f"OpenRouter embedding request failed: {exc.reason}"
            ) from exc

        data = body.get("data") or []
        if not data or "embedding" not in data[0]:
            raise EmbeddingProviderError(
                "OpenRouter embedding response did not include data[0].embedding"
            )
        embedding = data[0]["embedding"]
        if not isinstance(embedding, list):
            raise EmbeddingProviderError(
                "OpenRouter embedding response embedding is not a list"
            )
        return [float(value) for value in embedding]

    def _normalize_model(self, model: str) -> str:
        if "/" in model:
            return model
        if model.startswith("text-embedding-"):
            return f"openai/{model}"
        return model
