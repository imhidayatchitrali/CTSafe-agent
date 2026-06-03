"""
Compliance validators for DVR evidence and sections.

Ensures retrieved evidence and generated content comply with D.Lgs 81/08
(Italian Worker Safety Decree) and other regulatory requirements.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from app.domain.models import EvidenceChunk, SectionRecord

logger = logging.getLogger(__name__)


class ComplianceSeverity(str, Enum):
    """Severity of compliance issues."""
    
    error = "error"  # Critical regulatory gap
    warning = "warning"  # Missing data but not critical
    info = "info"  # Advisory only


@dataclass
class ComplianceIssue:
    """Single compliance validation issue."""
    
    severity: ComplianceSeverity
    code: str
    title: str
    description: str
    remediation: str | None = None
    affected_field: str | None = None


@dataclass
class ComplianceReport:
    """Result of compliance validation."""
    
    is_compliant: bool
    score: float  # 0.0 to 1.0
    issues: list[ComplianceIssue] = field(default_factory=list)
    missing_references: list[str] = field(default_factory=list)
    evidence_quality_score: float = 1.0
    metadata_completeness: float = 1.0
    
    @property
    def error_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == ComplianceSeverity.error)
    
    @property
    def warning_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == ComplianceSeverity.warning)


class MetadataValidator:
    """Validate chunk metadata completeness and quality."""
    
    # Required fields for regulatory documents
    REQUIRED_METADATA_FIELDS = {
        "source_document",
        "source_type",
        "document_type",
    }
    
    # Expected values for compliance
    VALID_SOURCE_TYPES = {"normativa", "template_structure", "dvr_pregresso"}
    VALID_DOCUMENT_TYPES = {"normativa", "dvr_template", "dvr_pregresso"}
    
    def validate_chunk(self, chunk: EvidenceChunk) -> ComplianceReport:
        """Validate a single evidence chunk."""
        issues: list[ComplianceIssue] = []
        metadata_score = 1.0
        
        # Check required fields
        for field_name in self.REQUIRED_METADATA_FIELDS:
            value = None
            if field_name == "source_type":
                value = chunk.metadata.get("source_type") if chunk.metadata else None
            else:
                value = getattr(chunk, field_name, None)
            
            if not value:
                issues.append(
                    ComplianceIssue(
                        severity=ComplianceSeverity.warning,
                        code="missing_metadata_field",
                        title=f"Missing {field_name}",
                        description=f"Evidence chunk missing required field: {field_name}",
                        remediation=f"Ensure chunk has {field_name} set",
                        affected_field=field_name,
                    )
                )
                metadata_score -= 0.1
        
        # Validate source_type
        source_type = chunk.metadata.get("source_type") if chunk.metadata else None
        if source_type and source_type not in self.VALID_SOURCE_TYPES:
            issues.append(
                ComplianceIssue(
                    severity=ComplianceSeverity.warning,
                    code="invalid_source_type",
                    title=f"Unexpected source_type: {source_type}",
                    description=f"source_type '{source_type}' not recognized",
                    remediation=f"Use one of: {', '.join(self.VALID_SOURCE_TYPES)}",
                    affected_field="source_type",
                )
            )
            metadata_score -= 0.05
        
        # Validate document_type
        doc_type = chunk.metadata.get("document_type") or chunk.corpus
        if doc_type not in self.VALID_DOCUMENT_TYPES:
            issues.append(
                ComplianceIssue(
                    severity=ComplianceSeverity.info,
                    code="non_standard_document_type",
                    title=f"Non-standard document_type: {doc_type}",
                    description=f"Document type '{doc_type}' is non-standard",
                    affected_field="document_type",
                )
            )
            metadata_score -= 0.02
        
        # Check content quality
        if not chunk.content or len(chunk.content.strip()) < 50:
            issues.append(
                ComplianceIssue(
                    severity=ComplianceSeverity.warning,
                    code="insufficient_content",
                    title="Content too short",
                    description="Evidence content is too brief to be authoritative",
                    remediation="Ensure chunk contains substantial text (>50 chars)",
                )
            )
            metadata_score -= 0.15
        
        metadata_score = max(0.0, metadata_score)
        is_compliant = len([i for i in issues if i.severity == ComplianceSeverity.error]) == 0
        
        return ComplianceReport(
            is_compliant=is_compliant,
            score=1.0 - len(issues) * 0.05 if is_compliant else 0.7,
            issues=issues,
            metadata_completeness=metadata_score,
        )


class RegulatoryRefValidator:
    """Validate normative references in evidence and sections."""
    
    # Core Italian safety regulations (D.Lgs 81/08 and amendments)
    CORE_NORMATIVE_REFS = {
        "D.Lgs 81/08": "Decreto Legislativo 81/2008 - Main Italian worker safety law",
        "D.Lgs 106/09": "Decreto Legislativo 106/2009 - Amendment to D.Lgs 81/08",
        "Allegato IV": "Annex IV - Minimum safety requirements",
        "Allegato V": "Annex V - Signaling safety requirements",
        "Allegato VI": "Annex VI - Collective protective equipment",
        "Allegato VII": "Annex VII - Personal protective equipment (DPI)",
        "Allegato VIII": "Annex VIII - Medical surveillance",
        "Allegato XII": "Annex XII - Asbestos protection",
        "Allegato XIII": "Annex XIII - Carcinogenic/mutagenic substance protection",
    }
    
    # Risk categories that require specific normative references
    RISK_NORMATIVE_MAP = {
        "rischi_chimici": ["Allegato XIII", "D.Lgs 81/08 Art. 223"],
        "rischi_biologici": ["D.Lgs 81/08 Art. 272"],
        "rischi_amianto": ["Allegato XII", "D.Lgs 81/08 Art. 246"],
        "rischi_rumore": ["D.Lgs 81/08 Art. 189"],
        "rischi_vibrazione": ["D.Lgs 81/08 Art. 198"],
        "rischi_dpi": ["Allegato VII", "D.Lgs 81/08 Art. 74"],
    }
    
    def validate_evidence_refs(
        self,
        chunks: list[EvidenceChunk],
        risk_category: str | None = None,
    ) -> ComplianceReport:
        """Validate normative references in evidence chunks."""
        issues: list[ComplianceIssue] = []
        found_refs: set[str] = set()
        
        # Collect all normative references in chunks
        for chunk in chunks:
            normative_refs = chunk.metadata.get("normative_refs", [])
            if isinstance(normative_refs, list):
                found_refs.update(normative_refs)
            
            # Also check content for known refs
            for ref_code in self.CORE_NORMATIVE_REFS.keys():
                if ref_code in chunk.content:
                    found_refs.add(ref_code)
        
        # Check core normative presence
        if not found_refs:
            issues.append(
                ComplianceIssue(
                    severity=ComplianceSeverity.error,
                    code="missing_core_normative_refs",
                    title="No normative references found",
                    description="Evidence must cite D.Lgs 81/08 or amendments",
                    remediation="Add normative references to evidence corpus",
                )
            )
        
        # Check risk-specific requirements
        if risk_category:
            required_refs = self.RISK_NORMATIVE_MAP.get(risk_category, [])
            missing_refs = [r for r in required_refs if r not in found_refs]
            if missing_refs:
                issues.append(
                    ComplianceIssue(
                        severity=ComplianceSeverity.warning,
                        code="missing_risk_specific_refs",
                        title=f"Missing references for {risk_category}",
                        description=f"Risk category '{risk_category}' should cite: {', '.join(missing_refs)}",
                        remediation=f"Add evidence citing: {', '.join(missing_refs)}",
                    )
                )
        
        is_compliant = len([i for i in issues if i.severity == ComplianceSeverity.error]) == 0
        score = 1.0 if found_refs else 0.0
        
        return ComplianceReport(
            is_compliant=is_compliant,
            score=score,
            issues=issues,
            missing_references=[r for r in self.CORE_NORMATIVE_REFS.keys() if r not in found_refs],
        )


class RiskDpiValidator:
    """Validate that risks have corresponding DPI requirements."""
    
    # Mapping of risk types to required DPI types
    RISK_DPI_MAPPING = {
        "rischi_biologici": ["guanti", "mascherina FFP2", "camice", "calzari"],
        "rischi_chimici": ["guanti", "mascherina", "occhiali", "camice"],
        "rischi_meccanici": ["guanti", "occhiali di sicurezza", "scarpe antinfortunio"],
        "rischi_caduta": ["imbracatura", "casco", "scarpe antinfortunio"],
        "rischi_rumore": ["cuffie antirumore", "tappi auricolari"],
        "rischi_radiazioni": ["dosimetro", "schermatura"],
        "rischi_termici": ["guanti termici", "grembiule isolante"],
        "rischi_umidità": ["guanti impermeabili", "stivali impermeabili"],
    }
    
    # Mansioni (job roles) with their standard DPI
    MANSIONE_DPI_BASELINE = {
        "operatore_magazzino": ["guanti", "scarpe antinfortunio", "casco"],
        "tecnico_meccanico": ["guanti", "occhiali di sicurezza", "scarpe antinfortunio"],
        "tecnico_elettrico": ["guanti isolanti", "occhiali di sicurezza", "scarpe antinfortunio"],
        "responsabile_sicurezza": ["casco"],
        "addetto_primo_soccorso": ["guanti latex", "mascherina"],
    }
    
    def validate_section_dpi(
        self,
        section: SectionRecord,
        risk_categories: list[str] | None = None,
        mansioni: list[str] | None = None,
    ) -> ComplianceReport:
        """Validate that section covers required DPI for risks and roles."""
        issues: list[ComplianceIssue] = []
        
        if not section.generated_markdown:
            issues.append(
                ComplianceIssue(
                    severity=ComplianceSeverity.warning,
                    code="missing_section_content",
                    title="Section has no generated content",
                    description="Cannot validate DPI requirements without section content",
                )
            )
            return ComplianceReport(
                is_compliant=False,
                score=0.0,
                issues=issues,
            )
        
        content_lower = section.generated_markdown.lower()
        
        # Check required DPI for risk categories
        if risk_categories:
            for risk in risk_categories:
                required_dpi = self.RISK_DPI_MAPPING.get(risk, [])
                missing_dpi = [
                    dpi for dpi in required_dpi
                    if dpi.lower() not in content_lower
                ]
                if missing_dpi:
                    issues.append(
                        ComplianceIssue(
                            severity=ComplianceSeverity.error,
                            code="missing_dpi_for_risk",
                            title=f"Missing DPI requirement for {risk}",
                            description=f"Risk '{risk}' requires but section doesn't mention: {', '.join(missing_dpi)}",
                            remediation=f"Add DPI requirements: {', '.join(missing_dpi)}",
                        )
                    )
        
        # Check baseline DPI for mansioni
        if mansioni:
            for mansione in mansioni:
                baseline_dpi = self.MANSIONE_DPI_BASELINE.get(mansione, [])
                missing_dpi = [
                    dpi for dpi in baseline_dpi
                    if dpi.lower() not in content_lower
                ]
                if missing_dpi:
                    issues.append(
                        ComplianceIssue(
                            severity=ComplianceSeverity.warning,
                            code="missing_baseline_dpi",
                            title=f"Missing baseline DPI for {mansione}",
                            description=f"Role '{mansione}' typically requires: {', '.join(missing_dpi)}",
                            remediation=f"Consider adding baseline DPI: {', '.join(missing_dpi)}",
                        )
                    )
        
        is_compliant = len([i for i in issues if i.severity == ComplianceSeverity.error]) == 0
        error_count = sum(1 for i in issues if i.severity == ComplianceSeverity.error)
        score = max(0.0, 1.0 - error_count * 0.3)
        
        return ComplianceReport(
            is_compliant=is_compliant,
            score=score,
            issues=issues,
        )


class ComplianceScorer:
    """Score evidence and sections for overall compliance."""
    
    def __init__(self):
        self.metadata_validator = MetadataValidator()
        self.ref_validator = RegulatoryRefValidator()
        self.dpi_validator = RiskDpiValidator()
    
    def score_evidence(
        self,
        chunks: list[EvidenceChunk],
        risk_category: str | None = None,
    ) -> ComplianceReport:
        """Score a set of evidence chunks for compliance."""
        if not chunks:
            return ComplianceReport(
                is_compliant=False,
                score=0.0,
                issues=[
                    ComplianceIssue(
                        severity=ComplianceSeverity.error,
                        code="no_evidence",
                        title="No evidence provided",
                        description="Evidence set is empty",
                        remediation="Provide at least one evidence chunk",
                    )
                ],
            )
        
        # Validate individual chunks
        chunk_reports = [self.metadata_validator.validate_chunk(c) for c in chunks]
        
        # Validate normative references
        ref_report = self.ref_validator.validate_evidence_refs(chunks, risk_category)
        
        # Aggregate all issues
        all_issues = []
        for report in chunk_reports:
            all_issues.extend(report.issues)
        all_issues.extend(ref_report.issues)
        
        # Calculate final scores
        chunk_score = sum(r.score for r in chunk_reports) / len(chunk_reports) if chunk_reports else 0.0
        metadata_score = sum(r.metadata_completeness for r in chunk_reports) / len(chunk_reports) if chunk_reports else 0.0
        ref_score = ref_report.score
        
        # Weighted average: 40% chunks, 20% metadata, 40% refs
        final_score = (chunk_score * 0.4) + (metadata_score * 0.2) + (ref_score * 0.4)
        is_compliant = ref_report.is_compliant and all(
            i.severity != ComplianceSeverity.error for i in all_issues
        )
        
        return ComplianceReport(
            is_compliant=is_compliant,
            score=final_score,
            issues=all_issues,
            missing_references=ref_report.missing_references,
            metadata_completeness=metadata_score,
        )


# Public API
def validate_evidence(
    chunks: list[EvidenceChunk],
    risk_category: str | None = None,
) -> ComplianceReport:
    """Validate evidence for compliance. Main entry point."""
    scorer = ComplianceScorer()
    return scorer.score_evidence(chunks, risk_category)


def validate_section_dpi(
    section: SectionRecord,
    risk_categories: list[str] | None = None,
    mansioni: list[str] | None = None,
) -> ComplianceReport:
    """Validate section DPI requirements."""
    validator = RiskDpiValidator()
    return validator.validate_section_dpi(section, risk_categories, mansioni)
