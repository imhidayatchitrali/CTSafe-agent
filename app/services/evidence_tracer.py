"""
Evidence tracer for audit trails and compliance tracking.

Logs all RAG search decisions, evidence selections, and compliance outcomes
for transparency and debugging.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from app.domain.models import EvidenceChunk, RagSearchInput, RagSearchResult

logger = logging.getLogger(__name__)


@dataclass
class EvidenceTraceLog:
    """Single evidence decision log entry."""
    
    timestamp: str
    trace_id: str
    search_input: dict[str, Any]
    evidence_count: int
    evidence_ids: list[str]
    is_fallback: bool
    fallback_reason: str | None
    compliance_passed: bool
    compliance_score: float
    metadata: dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for logging."""
        return asdict(self)
    
    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), default=str)


class EvidenceTracer:
    """Trace and audit evidence decisions for compliance."""
    
    def __init__(self, enable_logging: bool = True):
        self.enable_logging = enable_logging
        self.trace_logs: list[EvidenceTraceLog] = []
    
    def log_search(
        self,
        search_input: RagSearchInput,
        result: RagSearchResult,
        trace_id: str,
        compliance_passed: bool = False,
        compliance_score: float = 0.0,
        metadata: dict[str, Any] | None = None,
    ) -> EvidenceTraceLog:
        """Log a RAG search and its outcome."""
        log_entry = EvidenceTraceLog(
            timestamp=datetime.now(timezone.utc).isoformat(),
            trace_id=trace_id,
            search_input={
                "query": search_input.query,
                "corpus": search_input.corpus,
                "filters": search_input.filters,
                "top_k": search_input.top_k,
            },
            evidence_count=len(result.evidence),
            evidence_ids=[c.chunk_id for c in result.evidence],
            is_fallback=result.is_fallback,
            fallback_reason=result.fallback_reason,
            compliance_passed=compliance_passed,
            compliance_score=compliance_score,
            metadata=metadata or {},
        )
        
        self.trace_logs.append(log_entry)
        
        if self.enable_logging:
            logger.info(
                "evidence.trace.search",
                extra={
                    "trace_id": trace_id,
                    "corpus": search_input.corpus,
                    "evidence_count": len(result.evidence),
                    "is_fallback": result.is_fallback,
                    "compliance_passed": compliance_passed,
                    "compliance_score": f"{compliance_score:.2f}",
                },
            )
        
        return log_entry
    
    def log_evidence_selection(
        self,
        trace_id: str,
        section_id: UUID | str,
        selected_evidence: list[EvidenceChunk],
        rejected_evidence: list[EvidenceChunk],
        selection_reason: str,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Log evidence selection decisions."""
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "trace_id": trace_id,
            "section_id": str(section_id),
            "selected_count": len(selected_evidence),
            "selected_ids": [e.chunk_id for e in selected_evidence],
            "selected_scores": [e.score for e in selected_evidence],
            "rejected_count": len(rejected_evidence),
            "rejected_ids": [e.chunk_id for e in rejected_evidence],
            "rejected_scores": [e.score for e in rejected_evidence],
            "selection_reason": selection_reason,
            "metadata": metadata or {},
        }
        
        if self.enable_logging:
            logger.info(
                "evidence.trace.selection",
                extra={
                    "trace_id": trace_id,
                    "section_id": str(section_id),
                    "selected": len(selected_evidence),
                    "rejected": len(rejected_evidence),
                    "reason": selection_reason,
                },
            )
        
        return log_entry
    
    def log_compliance_check(
        self,
        trace_id: str,
        section_id: UUID | str,
        evidence: list[EvidenceChunk],
        compliance_report: dict[str, Any],
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Log compliance validation outcome."""
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "trace_id": trace_id,
            "section_id": str(section_id),
            "evidence_count": len(evidence),
            "evidence_ids": [e.chunk_id for e in evidence],
            "is_compliant": compliance_report.get("is_compliant", False),
            "compliance_score": compliance_report.get("score", 0.0),
            "issue_count": len(compliance_report.get("issues", [])),
            "error_count": sum(
                1 for issue in compliance_report.get("issues", [])
                if issue.get("severity") == "error"
            ),
            "warning_count": sum(
                1 for issue in compliance_report.get("issues", [])
                if issue.get("severity") == "warning"
            ),
            "missing_references": compliance_report.get("missing_references", []),
            "metadata": metadata or {},
        }
        
        if self.enable_logging:
            logger.info(
                "evidence.trace.compliance",
                extra={
                    "trace_id": trace_id,
                    "section_id": str(section_id),
                    "is_compliant": compliance_report.get("is_compliant", False),
                    "score": f"{compliance_report.get('score', 0.0):.2f}",
                    "errors": sum(
                        1 for issue in compliance_report.get("issues", [])
                        if issue.get("severity") == "error"
                    ),
                },
            )
        
        return log_entry
    
    def get_trace_report(self, trace_id: str) -> dict[str, Any]:
        """Get all logs for a specific trace ID."""
        trace_logs = [log for log in self.trace_logs if log.trace_id == trace_id]
        
        if not trace_logs:
            return {
                "trace_id": trace_id,
                "found": False,
                "logs": [],
            }
        
        return {
            "trace_id": trace_id,
            "found": True,
            "log_count": len(trace_logs),
            "first_timestamp": trace_logs[0].timestamp,
            "last_timestamp": trace_logs[-1].timestamp,
            "logs": [log.to_dict() for log in trace_logs],
        }
    
    def get_compliance_summary(self) -> dict[str, Any]:
        """Get summary of compliance across all traces."""
        if not self.trace_logs:
            return {
                "total_searches": 0,
                "compliant_searches": 0,
                "fallback_searches": 0,
                "avg_score": 0.0,
            }
        
        compliant = sum(1 for log in self.trace_logs if log.compliance_passed)
        fallback = sum(1 for log in self.trace_logs if log.is_fallback)
        avg_score = sum(log.compliance_score for log in self.trace_logs) / len(self.trace_logs)
        
        return {
            "total_searches": len(self.trace_logs),
            "compliant_searches": compliant,
            "compliant_rate": f"{(compliant / len(self.trace_logs) * 100):.1f}%",
            "fallback_searches": fallback,
            "fallback_rate": f"{(fallback / len(self.trace_logs) * 100):.1f}%",
            "avg_compliance_score": f"{avg_score:.2f}",
        }
    
    def clear_logs(self) -> int:
        """Clear all trace logs and return count."""
        count = len(self.trace_logs)
        self.trace_logs = []
        return count


# Global instance
_tracer = EvidenceTracer()


def get_tracer() -> EvidenceTracer:
    """Get the global evidence tracer instance."""
    return _tracer


def log_search(
    search_input: RagSearchInput,
    result: RagSearchResult,
    trace_id: str,
    compliance_passed: bool = False,
    compliance_score: float = 0.0,
    **metadata: Any,
) -> EvidenceTraceLog:
    """Log a search using the global tracer."""
    return _tracer.log_search(
        search_input=search_input,
        result=result,
        trace_id=trace_id,
        compliance_passed=compliance_passed,
        compliance_score=compliance_score,
        metadata=dict(metadata),
    )


def get_trace_report(trace_id: str) -> dict[str, Any]:
    """Get trace report using the global tracer."""
    return _tracer.get_trace_report(trace_id)


def get_compliance_summary() -> dict[str, Any]:
    """Get compliance summary using the global tracer."""
    return _tracer.get_compliance_summary()
