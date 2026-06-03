from __future__ import annotations

import logging
import re
import unicodedata
from typing import Any

from app.domain.models import EvidenceChunk, RagSearchInput, RagSearchResult

logger = logging.getLogger(__name__)


class RagSearchTool:
    """Small typed RAG search boundary for DVR evidence.

    `mock` mode stays deterministic for local tests. `supabase` mode embeds the
    query and calls narrow PostgREST RPC functions; failures can fall back to
    explicit empty evidence so writers/QA do not invent support.
    """

    def __init__(
        self,
        retrieval_policy_version: str,
        backend: str = "mock",
        supabase_client: Any | None = None,
        embedding_provider: Any | None = None,
        allow_fallback: bool = True,
        rag_version: str = "legacy",
        rag_v2_legacy_fallback: bool = True,
    ):
        self.retrieval_policy_version = retrieval_policy_version
        self.backend = backend
        self.supabase_client = supabase_client
        self.embedding_provider = embedding_provider
        self.allow_fallback = allow_fallback
        self.rag_version = rag_version.lower()
        self.rag_v2_legacy_fallback = rag_v2_legacy_fallback

    def search(self, request: RagSearchInput) -> RagSearchResult:
        logger.info(
            "rag.search",
            extra={
                "backend": self.backend,
                "corpus": request.corpus,
                "top_k": request.top_k,
                "rag_version": self.rag_version,
            },
        )
        if self.backend == "mock":
            return self._mock_search(request)
        if self.backend == "supabase":
            return self._supabase_search(request)
        raise ValueError(f"Unsupported RAG backend: {self.backend}")

    def _supabase_search(self, request: RagSearchInput) -> RagSearchResult:
        if self.supabase_client is None or self.embedding_provider is None:
            return self._fallback(request, "supabase_rag_not_configured")

        if self.rag_version == "v2":
            result = self._attempt_supabase_search(request, version="v2")
            if (
                self.rag_v2_legacy_fallback
                and (result.is_fallback or not result.evidence)
            ):
                logger.warning(
                    "rag.search.v2_legacy_fallback",
                    extra={
                        "corpus": request.corpus,
                        "fallback_reason": result.fallback_reason or "empty_v2_evidence",
                    },
                )
                return self._attempt_supabase_search(request, version="legacy")
            return result

        if self.rag_version != "legacy":
            return self._fallback(request, f"unsupported_rag_version:{self.rag_version}")

        return self._attempt_supabase_search(request, version="legacy")

    def _attempt_supabase_search(
        self,
        request: RagSearchInput,
        version: str,
    ) -> RagSearchResult:
        try:
            embedding = self.embedding_provider.embed(request.query)
            function_name = self._function_for_corpus(request.corpus, version=version)
            match_count = min(max(request.top_k * 4, request.top_k), 20)
            filter_payload = self._filter_for_version(
                corpus=request.corpus,
                filters=request.filters,
                version=version,
            )
            payload: dict[str, Any] = {
                "query_embedding": embedding,
                "match_count": match_count,
                "filter": filter_payload,
            }
            if version == "v2":
                payload["corpus_filter"] = request.corpus
            rows = self.supabase_client.rpc(function_name, payload)
            if not isinstance(rows, list):
                raise TypeError("Supabase RPC response must be a list of rows")
            evidence = [
                self._row_to_chunk(row=row, corpus=request.corpus, rank=index + 1)
                for index, row in enumerate(rows[:match_count])
            ]
            evidence.extend(self._lexical_backfill(request, version=version))
            evidence = self._dedupe_chunks(evidence)
            evidence = self._rank_chunks(evidence, request.query)[: request.top_k]
            return RagSearchResult(
                query=request.query,
                corpus=request.corpus,
                filters=request.filters,
                retrieval_policy_version=self.retrieval_policy_version,
                evidence=evidence,
                is_mock=False,
            )
        except Exception as exc:
            logger.warning(
                "rag.search.fallback",
                extra={
                    "corpus": request.corpus,
                    "reason": exc.__class__.__name__,
                    "rag_version": version,
                },
            )
            if not self.allow_fallback:
                raise
            return self._fallback(request, f"{exc.__class__.__name__}: {exc}")

    def _function_for_corpus(self, corpus: str, version: str) -> str:
        if version == "v2":
            if corpus not in {"normativa", "indice", "dvr_pregressi"}:
                raise ValueError(f"Unsupported RAG corpus: {corpus}")
            return "match_rag_chunks"
        functions = {
            "normativa": "match_normativa",
            "indice": "match_documents",
            "dvr_pregressi": "match_dvr_pregressi",
        }
        if corpus not in functions:
            raise ValueError(f"Unsupported RAG corpus: {corpus}")
        return functions[corpus]

    def _row_to_chunk(self, row: dict[str, Any], corpus: str, rank: int) -> EvidenceChunk:
        metadata = row.get("metadata") or {}
        if not isinstance(metadata, dict):
            metadata = {"raw_metadata": metadata}
        chunk_id = str(
            row.get("chunk_id")
            or row.get("id")
            or row.get("document_id")
            or f"{corpus}:rank:{rank}"
        )
        content = str(
            row.get("content")
            or row.get("text")
            or row.get("page_content")
            or row.get("body")
            or ""
        )
        score = row.get("similarity", row.get("score", row.get("distance", 0.0)))
        source_page = row.get("source_page") or metadata.get("source_page")
        if source_page is None:
            loc = metadata.get("loc")
            if isinstance(loc, dict):
                source_page = loc.get("pageNumber") or loc.get("page")
        return EvidenceChunk(
            chunk_id=chunk_id,
            corpus=str(row.get("corpus") or corpus),
            content=content,
            score=float(score or 0.0),
            rank=rank,
            source_document=(
                row.get("source_document")
                or metadata.get("source")
                or metadata.get("pdf")
                or metadata.get("file_name")
            ),
            source_page=int(source_page) if source_page is not None else None,
            line_from=row.get("line_from") or metadata.get("line_from"),
            line_to=row.get("line_to") or metadata.get("line_to"),
            metadata=metadata,
            decision="supporting",
        )

    def _table_for_corpus(self, corpus: str) -> str:
        tables = {
            "normativa": "normativa",
            "indice": "indice",
            "dvr_pregressi": "dvr_pregressi",
        }
        if corpus not in tables:
            raise ValueError(f"Unsupported RAG corpus: {corpus}")
        return tables[corpus]

    def _normalize_legacy_filter(
        self,
        corpus: str,
        filters: dict[str, Any],
    ) -> dict[str, Any]:
        normalized = dict(filters)
        source_type = normalized.get("source_type")
        if source_type in {corpus, "normativa", "template_structure", "dvr_pregressi"}:
            normalized.pop("source_type", None)
        return normalized

    def _filter_for_version(
        self,
        corpus: str,
        filters: dict[str, Any],
        version: str,
    ) -> dict[str, Any]:
        if version == "legacy":
            return self._normalize_legacy_filter(corpus=corpus, filters=filters)
        return dict(filters)

    def _lexical_backfill(
        self,
        request: RagSearchInput,
        version: str,
    ) -> list[EvidenceChunk]:
        if version == "v2":
            return self._v2_lexical_backfill(request)
        if not hasattr(self.supabase_client, "search_text"):
            return []
        terms = self._query_terms(request.query)
        if not terms:
            return []
        try:
            rows = self.supabase_client.search_text(
                table=self._table_for_corpus(request.corpus),
                terms=terms[:8],
                limit=min(max(request.top_k * 10, 50), 100),
            )
        except Exception as exc:
            logger.info(
                "rag.search.lexical_backfill_failed",
                extra={"corpus": request.corpus, "reason": exc.__class__.__name__},
            )
            return []
        return [
            self._row_to_chunk(row=row, corpus=request.corpus, rank=index + 1)
            for index, row in enumerate(rows)
        ]

    def _v2_lexical_backfill(self, request: RagSearchInput) -> list[EvidenceChunk]:
        terms = self._query_terms(request.query)
        if not terms:
            return []
        try:
            rows = self.supabase_client.rpc(
                "search_rag_chunks_text",
                {
                    "search_terms": terms[:8],
                    "match_count": min(max(request.top_k * 10, 50), 100),
                    "filter": dict(request.filters),
                    "corpus_filter": request.corpus,
                },
            )
        except Exception as exc:
            logger.info(
                "rag.search.v2_lexical_backfill_failed",
                extra={"corpus": request.corpus, "reason": exc.__class__.__name__},
            )
            return []
        if not isinstance(rows, list):
            return []
        return [
            self._row_to_chunk(row=row, corpus=request.corpus, rank=index + 1)
            for index, row in enumerate(rows)
        ]

    def _needs_lexical_backfill(
        self,
        evidence: list[EvidenceChunk],
        request: RagSearchInput,
    ) -> bool:
        if len(evidence) < request.top_k:
            return True
        terms = self._query_terms(request.query)
        if not terms:
            return False
        return all(self._term_hit_count(chunk.content, terms) == 0 for chunk in evidence[: request.top_k])

    def _dedupe_chunks(self, chunks: list[EvidenceChunk]) -> list[EvidenceChunk]:
        seen_content: set[str] = set()
        seen_ids: set[str] = set()
        deduped: list[EvidenceChunk] = []
        for chunk in chunks:
            content_key = self._normalize_text(chunk.content)
            id_key = f"{chunk.corpus}:{chunk.chunk_id}"
            if id_key in seen_ids or content_key in seen_content:
                continue
            seen_ids.add(id_key)
            if content_key:
                seen_content.add(content_key)
            deduped.append(chunk)
        return deduped

    def _rank_chunks(
        self,
        chunks: list[EvidenceChunk],
        query: str,
    ) -> list[EvidenceChunk]:
        terms = self._query_terms(query)

        def sort_key(chunk: EvidenceChunk) -> tuple[float, float]:
            hit_count = self._term_hit_count(chunk.content, terms)
            keyword_score = hit_count / max(len(terms), 1)
            if keyword_score:
                return (1.0 + keyword_score, chunk.score)
            return (0.0, chunk.score)

        ranked = sorted(chunks, key=sort_key, reverse=True)
        for index, chunk in enumerate(ranked):
            chunk.rank = index + 1
        return ranked

    def _query_terms(self, query: str) -> list[str]:
        stopwords = {
            "per",
            "con",
            "del",
            "della",
            "delle",
            "degli",
            "dell",
            "alla",
            "alle",
            "dvr",
            "81",
            "08",
            "lgs",
            "dlgs",
        }
        normalized = self._normalize_text(query)
        terms = re.findall(r"[a-z0-9]{3,}", normalized)
        deduped: list[str] = []
        for term in terms:
            if term in stopwords or term in deduped:
                continue
            deduped.append(term)
        return deduped

    def _term_hit_count(self, content: str, terms: list[str]) -> int:
        normalized = self._normalize_text(content)
        return sum(1 for term in terms if term in normalized)

    def _normalize_text(self, text: str) -> str:
        without_accents = unicodedata.normalize("NFKD", text)
        ascii_text = without_accents.encode("ascii", "ignore").decode("ascii")
        return re.sub(r"\s+", " ", ascii_text.lower()).strip()

    def _fallback(self, request: RagSearchInput, reason: str) -> RagSearchResult:
        return RagSearchResult(
            query=request.query,
            corpus=request.corpus,
            filters=request.filters,
            retrieval_policy_version=self.retrieval_policy_version,
            evidence=[],
            is_mock=False,
            is_fallback=True,
            fallback_reason=reason,
        )

    def _mock_search(self, request: RagSearchInput) -> RagSearchResult:
        corpus = request.corpus
        if corpus == "indice":
            chunks = self._index_chunks(request)
        else:
            chunks = self._normativa_chunks(request)
        return RagSearchResult(
            query=request.query,
            corpus=corpus,
            filters=request.filters,
            retrieval_policy_version=self.retrieval_policy_version,
            evidence=chunks[: request.top_k],
            is_mock=True,
        )

    def _index_chunks(self, request: RagSearchInput) -> list[EvidenceChunk]:
        return [
            EvidenceChunk(
                chunk_id="indice:template:01",
                corpus="indice",
                content=(
                    "Struttura DVR: gestione prevenzione, identificazione attivita, "
                    "organizzazione sicurezza, criteri di valutazione, rischi, DPI, "
                    "Sorveglianza Sanitaria e programma di miglioramento."
                ),
                score=0.89,
                rank=1,
                source_document="01_DVR-spheractsafe_reference",
                source_page=1,
                metadata={"source_type": "template_structure", "query": request.query},
            )
        ]

    def _normativa_chunks(self, request: RagSearchInput) -> list[EvidenceChunk]:
        return [
            EvidenceChunk(
                chunk_id="normativa:dlgs81:valutazione-rischi",
                corpus="normativa",
                content=(
                    "Il datore di lavoro valuta tutti i rischi per la salute e "
                    "sicurezza e documenta criteri, misure di prevenzione e programma "
                    "di miglioramento."
                ),
                score=0.86,
                rank=1,
                source_document="D.Lgs. 81/08",
                source_page=None,
                metadata={"source_type": "normativa", "query": request.query},
            ),
            EvidenceChunk(
                chunk_id="normativa:dlgs81:dpi",
                corpus="normativa",
                content=(
                    "I DPI devono essere scelti in relazione ai rischi individuati, "
                    "alla mansione e alle condizioni operative effettive. "
                    "Sono Dispositivi di Protezione Individuale da collegare ai rischi."
                ),
                score=0.78,
                rank=2,
                source_document="D.Lgs. 81/08",
                source_page=None,
                metadata={"source_type": "normativa", "query": request.query},
            ),
        ]
