from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from app.domain.models import RagSearchInput
from app.services.rag_search_tool import RagSearchTool


class RagEvalCase(BaseModel):
    name: str
    query: str
    corpus: str = "normativa"
    filters: dict[str, Any] = Field(default_factory=dict)
    top_k: int = Field(default=5, ge=1, le=20)
    min_results: int = Field(default=1, ge=0)
    must_include_terms: list[str] = Field(default_factory=list)
    must_include_source_terms: list[str] = Field(default_factory=list)


class RagEvalResult(BaseModel):
    name: str
    passed: bool
    result_count: int
    fallback_reason: str | None = None
    missing_terms: list[str] = Field(default_factory=list)
    missing_source_terms: list[str] = Field(default_factory=list)
    chunk_ids: list[str] = Field(default_factory=list)


def load_rag_eval_cases(path: Path) -> list[RagEvalCase]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise ValueError("RAG eval fixture must be a JSON array")
    return [RagEvalCase(**item) for item in payload]


def evaluate_rag_case(tool: RagSearchTool, case: RagEvalCase) -> RagEvalResult:
    result = tool.search(
        RagSearchInput(
            query=case.query,
            corpus=case.corpus,
            filters=case.filters,
            top_k=case.top_k,
        )
    )
    haystack = "\n".join(chunk.content.lower() for chunk in result.evidence)
    source_haystack = "\n".join(
        (chunk.source_document or "").lower() for chunk in result.evidence
    )
    missing_terms = [
        term for term in case.must_include_terms if term.lower() not in haystack
    ]
    missing_source_terms = [
        term
        for term in case.must_include_source_terms
        if term.lower() not in source_haystack
    ]
    passed = (
        len(result.evidence) >= case.min_results
        and not result.is_fallback
        and not missing_terms
        and not missing_source_terms
    )
    return RagEvalResult(
        name=case.name,
        passed=passed,
        result_count=len(result.evidence),
        fallback_reason=result.fallback_reason,
        missing_terms=missing_terms,
        missing_source_terms=missing_source_terms,
        chunk_ids=[chunk.chunk_id for chunk in result.evidence],
    )


def evaluate_rag_cases(
    tool: RagSearchTool, cases: list[RagEvalCase]
) -> list[RagEvalResult]:
    return [evaluate_rag_case(tool, case) for case in cases]
