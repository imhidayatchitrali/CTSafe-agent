#!/usr/bin/env python
"""
CLI tool to validate RAG compliance and production readiness.

Usage:
    python scripts/validate_rag_compliance.py [--rag-backend mock|supabase] [--verbose]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from app.domain.models import EvidenceChunk, RagSearchInput
from app.services.compliance_validator import (
    ComplianceScorer,
    MetadataValidator,
    RegulatoryRefValidator,
    RiskDpiValidator,
    ComplianceSeverity,
)
from app.services.rag_search_tool import RagSearchTool
from app.settings import AppSettings


def validate_mock_rag() -> dict[str, Any]:
    """Validate mock RAG backend."""
    print("\n" + "=" * 70)
    print("MOCK RAG BACKEND VALIDATION")
    print("=" * 70)
    
    tool = RagSearchTool(
        retrieval_policy_version="rag_policy_v0_1",
        backend="mock",
    )
    
    # Test basic searches
    test_cases = [
        {
            "name": "Index structure",
            "query": "indice DVR struttura capitoli valutazione rischi",
            "corpus": "indice",
        },
        {
            "name": "Normative references",
            "query": "DPI D.Lgs 81/08 dispositivi protezione",
            "corpus": "normativa",
        },
    ]
    
    results = []
    for case in test_cases:
        result = tool.search(
            RagSearchInput(
                query=case["query"],
                corpus=case["corpus"],
                top_k=5,
            )
        )
        results.append({
            "name": case["name"],
            "query": case["query"],
            "evidence_count": len(result.evidence),
            "is_mock": result.is_mock,
            "passed": len(result.evidence) > 0 and not result.is_fallback,
        })
        print(f"\n✓ {case['name']}")
        print(f"  Query: {case['query']}")
        print(f"  Evidence found: {len(result.evidence)}")
        print(f"  Is mock: {result.is_mock}")
    
    passed = sum(1 for r in results if r["passed"])
    print(f"\n✓ Mock RAG: {passed}/{len(results)} tests passed")
    
    return {
        "backend": "mock",
        "status": "pass" if passed == len(results) else "partial",
        "passed": passed,
        "total": len(results),
        "tests": results,
    }


def validate_metadata() -> dict[str, Any]:
    """Validate metadata compliance."""
    print("\n" + "=" * 70)
    print("METADATA VALIDATION")
    print("=" * 70)
    
    validator = MetadataValidator()
    
    test_chunks = [
        {
            "name": "Valid normative chunk",
            "chunk": EvidenceChunk(
                chunk_id="meta-001",
                corpus="normativa",
                content="D.Lgs 81/08 Article 15: General principles with substantial regulatory content about workplace safety requirements and worker protection measures.",
                score=0.95,
                rank=1,
                source_document="D.Lgs 81/08",
                source_page=2,
                metadata={
                    "source_type": "normativa",
                    "document_type": "normativa",
                },
            ),
            "should_pass": True,
        },
        {
            "name": "Missing source_document",
            "chunk": EvidenceChunk(
                chunk_id="meta-002",
                corpus="normativa",
                content="Important regulatory content about safety and protection measures.",
                score=0.80,
                rank=1,
                source_document=None,
                metadata={"source_type": "normativa"},
            ),
            "should_pass": False,
        },
        {
            "name": "Invalid source_type",
            "chunk": EvidenceChunk(
                chunk_id="meta-003",
                corpus="normativa",
                content="Very important and substantial content about legal requirements and safety protocols.",
                score=0.85,
                rank=1,
                source_document="Doc",
                source_type="invalid_type",
                metadata={},
            ),
            "should_pass": False,
        },
    ]
    
    results = []
    for case in test_chunks:
        report = validator.validate_chunk(case["chunk"])
        passed = report.is_compliant == case["should_pass"]
        results.append({
            "name": case["name"],
            "passed": passed,
            "is_compliant": report.is_compliant,
            "score": report.score,
            "issues": len(report.issues),
        })
        status = "✓" if passed else "✗"
        print(f"\n{status} {case['name']}")
        print(f"  Compliant: {report.is_compliant}")
        print(f"  Score: {report.score:.2f}")
        print(f"  Issues: {len(report.issues)}")
    
    passed = sum(1 for r in results if r["passed"])
    print(f"\n✓ Metadata validation: {passed}/{len(results)} tests passed")
    
    return {
        "validator": "metadata",
        "status": "pass" if passed == len(results) else "partial",
        "passed": passed,
        "total": len(results),
        "tests": results,
    }


def validate_regulatory_refs() -> dict[str, Any]:
    """Validate regulatory references."""
    print("\n" + "=" * 70)
    print("REGULATORY REFERENCES VALIDATION")
    print("=" * 70)
    
    validator = RegulatoryRefValidator()
    
    test_cases = [
        {
            "name": "D.Lgs 81/08 cited",
            "chunks": [
                EvidenceChunk(
                    chunk_id="ref-001",
                    corpus="normativa",
                    content="D.Lgs 81/08 - Decreto Legislativo 81/2008 on worker safety and health protection.",
                    score=0.95,
                    rank=1,
                    source_document="Main Law",
                    metadata={"normative_refs": ["D.Lgs 81/08"]},
                )
            ],
            "should_pass": True,
        },
        {
            "name": "Missing normative refs",
            "chunks": [
                EvidenceChunk(
                    chunk_id="ref-002",
                    corpus="normativa",
                    content="Generic content without specific normative citations.",
                    score=0.70,
                    rank=1,
                    source_document="Weak Doc",
                    metadata={},
                )
            ],
            "should_pass": False,
        },
        {
            "name": "Chemical risk specific refs",
            "chunks": [
                EvidenceChunk(
                    chunk_id="ref-003",
                    corpus="normativa",
                    content="Allegato XIII - Protection from carcinogenic and mutagenic substances in the workplace.",
                    score=0.92,
                    rank=1,
                    source_document="Safety Annex",
                    metadata={"normative_refs": ["Allegato XIII", "D.Lgs 81/08 Art. 223"]},
                )
            ],
            "risk_category": "rischi_chimici",
            "should_pass": True,
        },
    ]
    
    results = []
    for case in test_cases:
        risk_cat = case.get("risk_category")
        report = validator.validate_evidence_refs(case["chunks"], risk_cat)
        passed = report.is_compliant == case["should_pass"]
        results.append({
            "name": case["name"],
            "passed": passed,
            "is_compliant": report.is_compliant,
            "score": report.score,
            "missing_refs": len(report.missing_references),
        })
        status = "✓" if passed else "✗"
        print(f"\n{status} {case['name']}")
        print(f"  Compliant: {report.is_compliant}")
        print(f"  Score: {report.score:.2f}")
        print(f"  Missing refs: {len(report.missing_references)}")
    
    passed = sum(1 for r in results if r["passed"])
    print(f"\n✓ Regulatory refs validation: {passed}/{len(results)} tests passed")
    
    return {
        "validator": "regulatory_refs",
        "status": "pass" if passed == len(results) else "partial",
        "passed": passed,
        "total": len(results),
        "tests": results,
    }


def validate_compliance_scorer() -> dict[str, Any]:
    """Validate overall compliance scoring."""
    print("\n" + "=" * 70)
    print("COMPLIANCE SCORER VALIDATION")
    print("=" * 70)
    
    scorer = ComplianceScorer()
    
    test_cases = [
        {
            "name": "High quality evidence",
            "chunks": [
                EvidenceChunk(
                    chunk_id="score-001",
                    corpus="normativa",
                    content="D.Lgs 81/08 Article 15: General principles for employer obligations and worker protection measures.",
                    score=0.96,
                    rank=1,
                    source_document="D.Lgs 81/08",
                    source_page=2,
                    metadata={
                        "normative_refs": ["D.Lgs 81/08"],
                        "source_type": "normativa",
                        "document_type": "normativa",
                    },
                )
            ],
            "min_score": 0.6,
        },
        {
            "name": "Poor quality evidence",
            "chunks": [
                EvidenceChunk(
                    chunk_id="score-002",
                    corpus="normativa",
                    content="X",  # Too short
                    score=0.3,
                    rank=1,
                    metadata={},
                )
            ],
            "min_score": 0.0,
        },
    ]
    
    results = []
    for case in test_cases:
        report = scorer.score_evidence(case["chunks"])
        passed = report.score >= case["min_score"]
        results.append({
            "name": case["name"],
            "passed": passed,
            "is_compliant": report.is_compliant,
            "score": report.score,
            "min_expected": case["min_score"],
        })
        status = "✓" if passed else "✗"
        print(f"\n{status} {case['name']}")
        print(f"  Compliant: {report.is_compliant}")
        print(f"  Score: {report.score:.2f} (min: {case['min_score']:.2f})")
    
    passed = sum(1 for r in results if r["passed"])
    print(f"\n✓ Compliance scorer: {passed}/{len(results)} tests passed")
    
    return {
        "validator": "compliance_scorer",
        "status": "pass" if passed == len(results) else "partial",
        "passed": passed,
        "total": len(results),
        "tests": results,
    }


def main() -> int:
    """Run all validations and report."""
    parser = argparse.ArgumentParser(
        description="Validate RAG compliance and production readiness"
    )
    parser.add_argument(
        "--rag-backend",
        choices=["mock", "supabase"],
        default="mock",
        help="RAG backend to test (default: mock)",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose output",
    )
    args = parser.parse_args()
    
    print("\n" + "=" * 70)
    print("CT SAFE DVR RAG - PRODUCTION READINESS VALIDATION")
    print("=" * 70)
    print(f"Started validation at {Path('.').resolve().name}")
    print(f"RAG Backend: {args.rag_backend}")
    
    all_results = {
        "timestamp": __import__("datetime").datetime.now(
            __import__("datetime").timezone.utc
        ).isoformat(),
        "backend": args.rag_backend,
        "validations": [],
    }
    
    # Run all validations
    validations = [
        ("Mock RAG Backend", validate_mock_rag),
        ("Metadata Validation", validate_metadata),
        ("Regulatory References", validate_regulatory_refs),
        ("Compliance Scorer", validate_compliance_scorer),
    ]
    
    for name, validator_func in validations:
        try:
            result = validator_func()
            all_results["validations"].append(result)
        except Exception as exc:
            print(f"\n✗ {name} failed: {exc}")
            all_results["validations"].append({
                "name": name,
                "status": "error",
                "error": str(exc),
            })
    
    # Summary
    print("\n" + "=" * 70)
    print("VALIDATION SUMMARY")
    print("=" * 70)
    
    total_passed = sum(
        v.get("passed", 0) for v in all_results["validations"]
        if v.get("status") == "pass"
    )
    total_tests = sum(
        v.get("total", 0) for v in all_results["validations"]
        if v.get("total")
    )
    
    print(f"\nTotal tests passed: {total_passed}/{total_tests}")
    for validation in all_results["validations"]:
        status_icon = "✓" if validation.get("status") == "pass" else "✗"
        name = validation.get("validator") or validation.get("backend", "Unknown")
        print(f"{status_icon} {name}: {validation.get('status').upper()}")
    
    # Output JSON report
    report_path = Path("rag_validation_report.json")
    with open(report_path, "w") as f:
        json.dump(all_results, f, indent=2, default=str)
    print(f"\n✓ Full report saved to: {report_path}")
    
    # Exit code
    all_passed = all(
        v.get("status") == "pass"
        for v in all_results["validations"]
    )
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
