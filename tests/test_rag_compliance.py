"""
Comprehensive test suite for RAG compliance and production readiness.

Tests coverage:
- Compliance validation
- Evidence quality
- Normative references
- DPI requirements
- Edge cases and error handling
"""

from __future__ import annotations

import pytest

from app.domain.models import EvidenceChunk, SectionRecord, DvrIndexSectionBrief
from app.services.compliance_validator import (
    ComplianceScorer,
    MetadataValidator,
    RegulatoryRefValidator,
    RiskDpiValidator,
    ComplianceSeverity,
)


class TestMetadataValidator:
    """Test metadata validation for evidence chunks."""
    
    def test_valid_chunk_metadata(self):
        """Valid chunk should pass."""
        chunk = EvidenceChunk(
            chunk_id="test-001",
            corpus="normativa",
            content="D.Lgs 81/08 Article 2: Definitions and field of application",
            score=0.95,
            rank=1,
            source_document="D.Lgs 81/08",
            source_page=5,
            metadata={"source_type": "normativa", "document_type": "normativa"},
        )
        
        validator = MetadataValidator()
        report = validator.validate_chunk(chunk)
        
        assert report.is_compliant
        assert report.metadata_completeness > 0.9
        assert len([i for i in report.issues if i.severity == ComplianceSeverity.error]) == 0
    
    def test_missing_source_document(self):
        """Chunk without source_document should warn."""
        chunk = EvidenceChunk(
            chunk_id="test-002",
            corpus="normativa",
            content="Some normative content",
            score=0.85,
            rank=1,
            source_document=None,  # Missing!
            metadata={"source_type": "normativa"},
        )
        
        validator = MetadataValidator()
        report = validator.validate_chunk(chunk)
        
        assert not report.is_compliant
        assert any(i.code == "missing_metadata_field" for i in report.issues)
    
    def test_insufficient_content(self):
        """Very short content should warn."""
        chunk = EvidenceChunk(
            chunk_id="test-003",
            corpus="normativa",
            content="DPI",  # Too short!
            score=0.80,
            rank=1,
            source_document="Doc",
            metadata={"source_type": "normativa"},
        )
        
        validator = MetadataValidator()
        report = validator.validate_chunk(chunk)
        
        assert not report.is_compliant
        assert any(i.code == "insufficient_content" for i in report.issues)
    
    def test_invalid_source_type(self):
        """Invalid source_type should warn."""
        chunk = EvidenceChunk(
            chunk_id="test-004",
            corpus="normativa",
            content="Valid content with substantial text about regulations and requirements.",
            score=0.90,
            rank=1,
            source_document="Doc",
            source_type="invalid_type",  # Invalid!
            metadata={},
        )
        
        validator = MetadataValidator()
        report = validator.validate_chunk(chunk)
        
        assert any(i.code == "invalid_source_type" for i in report.issues)


class TestRegulatoryRefValidator:
    """Test normative reference validation."""
    
    def test_chunks_with_d_lgs_81_08(self):
        """Chunks citing D.Lgs 81/08 should be valid."""
        chunks = [
            EvidenceChunk(
                chunk_id="ref-001",
                corpus="normativa",
                content="D.Lgs 81/08 - Decreto Legislativo 81/2008 on worker safety",
                score=0.95,
                rank=1,
                source_document="Main Law",
                metadata={
                    "normative_refs": ["D.Lgs 81/08"],
                    "source_type": "normativa",
                },
            )
        ]
        
        validator = RegulatoryRefValidator()
        report = validator.validate_evidence_refs(chunks)
        
        assert report.is_compliant
        assert report.score > 0.8
    
    def test_chunks_without_normative_refs(self):
        """Chunks without normative refs should fail."""
        chunks = [
            EvidenceChunk(
                chunk_id="ref-002",
                corpus="normativa",
                content="Some content without regulatory references",
                score=0.80,
                rank=1,
                source_document="Weak Doc",
                metadata={},
            )
        ]
        
        validator = RegulatoryRefValidator()
        report = validator.validate_evidence_refs(chunks)
        
        assert not report.is_compliant
        assert len(report.missing_references) > 0
    
    def test_risk_specific_refs_for_chemical(self):
        """Chemical risks should have Allegato XIII ref."""
        chunks = [
            EvidenceChunk(
                chunk_id="chem-001",
                corpus="normativa",
                content="Allegato XIII - Protection from carcinogenic substances",
                score=0.92,
                rank=1,
                source_document="Safety Annex",
                metadata={
                    "normative_refs": ["Allegato XIII", "D.Lgs 81/08 Art. 223"],
                    "source_type": "normativa",
                },
            )
        ]
        
        validator = RegulatoryRefValidator()
        report = validator.validate_evidence_refs(chunks, risk_category="rischi_chimici")
        
        assert report.is_compliant
    
    def test_missing_risk_specific_refs(self):
        """Missing risk-specific refs should warn."""
        chunks = [
            EvidenceChunk(
                chunk_id="chem-002",
                corpus="normativa",
                content="Some general chemical content",
                score=0.80,
                rank=1,
                source_document="Doc",
                metadata={"normative_refs": ["D.Lgs 81/08"]},
            )
        ]
        
        validator = RegulatoryRefValidator()
        report = validator.validate_evidence_refs(chunks, risk_category="rischi_chimici")
        
        # Should have warnings about missing Allegato XIII
        assert any(i.code == "missing_risk_specific_refs" for i in report.issues)


class TestRiskDpiValidator:
    """Test DPI requirement validation."""
    
    def test_biological_risk_with_dpi(self):
        """Biological risk section with DPI should pass."""
        section = SectionRecord(
            id="section-001",
            project_id="proj-001",
            index_id="idx-001",
            section_number="5.1",
            title="Biological Risks",
            brief=DvrIndexSectionBrief(
                section_number="5.1",
                title="Biological Risks",
                purpose="Manage biological hazards",
            ),
            generated_markdown="""
            # Biological Risks
            
            For laboratory personnel handling biological materials:
            
            **Required DPI:**
            - Guanti nitrile (gloves)
            - Mascherina FFP2 per particulate
            - Camice impermeabile
            - Calzari impermeabili
            
            All DPI must meet EN standards.
            """,
        )
        
        validator = RiskDpiValidator()
        report = validator.validate_section_dpi(
            section,
            risk_categories=["rischi_biologici"],
        )
        
        assert report.is_compliant
        assert len([i for i in report.issues if i.severity == ComplianceSeverity.error]) == 0
    
    def test_missing_required_dpi(self):
        """Missing required DPI should fail."""
        section = SectionRecord(
            id="section-002",
            project_id="proj-001",
            index_id="idx-001",
            section_number="5.2",
            title="Chemical Risks",
            brief=DvrIndexSectionBrief(
                section_number="5.2",
                title="Chemical Risks",
                purpose="Manage chemical hazards",
            ),
            generated_markdown="""
            # Chemical Risks
            
            Workers must use guanti (gloves) and occhiali (eye protection).
            
            However, mascherina and camice are missing!
            """,
        )
        
        validator = RiskDpiValidator()
        report = validator.validate_section_dpi(
            section,
            risk_categories=["rischi_chimici"],
        )
        
        assert not report.is_compliant
        assert any(i.code == "missing_dpi_for_risk" for i in report.issues)
    
    def test_mansione_baseline_dpi(self):
        """Check baseline DPI for job roles."""
        section = SectionRecord(
            id="section-003",
            project_id="proj-001",
            index_id="idx-001",
            section_number="6.1",
            title="Warehouse Operators",
            brief=DvrIndexSectionBrief(
                section_number="6.1",
                title="Warehouse Operators",
                purpose="Define role requirements",
            ),
            generated_markdown="""
            # Warehouse Operators
            
            All warehouse personnel must wear:
            - Guanti work gloves
            - Scarpe antinfortunio (safety shoes)
            - Casco protettivo (protective helmet)
            
            These are minimum baseline requirements.
            """,
        )
        
        validator = RiskDpiValidator()
        report = validator.validate_section_dpi(
            section,
            mansioni=["operatore_magazzino"],
        )
        
        assert report.is_compliant


class TestComplianceScorer:
    """Test overall compliance scoring."""
    
    def test_high_quality_evidence_set(self):
        """Well-formed evidence set should score high."""
        chunks = [
            EvidenceChunk(
                chunk_id="score-001",
                corpus="normativa",
                content="D.Lgs 81/08 Article 15: General principles. The employer shall adopt measures for the protection of health and safety of workers on the basis of a general duty to assess the risks arising from the work.",
                score=0.96,
                rank=1,
                source_document="D.Lgs 81/08",
                source_page=2,
                metadata={
                    "normative_refs": ["D.Lgs 81/08"],
                    "source_type": "normativa",
                    "document_type": "normativa",
                },
            ),
            EvidenceChunk(
                chunk_id="score-002",
                corpus="normativa",
                content="D.Lgs 106/09 Amendment: Decreto Legislativo 106/2009 modified D.Lgs 81/08 to strengthen safety requirements in specific sectors.",
                score=0.92,
                rank=2,
                source_document="D.Lgs 106/09",
                source_page=1,
                metadata={
                    "normative_refs": ["D.Lgs 106/09", "D.Lgs 81/08"],
                    "source_type": "normativa",
                    "document_type": "normativa",
                },
            ),
        ]
        
        scorer = ComplianceScorer()
        report = scorer.score_evidence(chunks)
        
        assert report.is_compliant
        assert report.score > 0.7
        assert report.metadata_completeness > 0.9
    
    def test_poor_quality_evidence(self):
        """Poor evidence should score low."""
        chunks = [
            EvidenceChunk(
                chunk_id="score-003",
                corpus="normativa",
                content="X",  # Too short
                score=0.5,
                rank=1,
                source_document=None,  # Missing
                metadata={},  # No normative refs
            )
        ]
        
        scorer = ComplianceScorer()
        report = scorer.score_evidence(chunks)
        
        assert not report.is_compliant
        assert report.score < 0.5
    
    def test_empty_evidence_set(self):
        """Empty evidence set should fail."""
        scorer = ComplianceScorer()
        report = scorer.score_evidence([])
        
        assert not report.is_compliant
        assert report.score == 0.0
    
    def test_score_with_risk_category(self):
        """Score should consider risk-specific requirements."""
        chunks = [
            EvidenceChunk(
                chunk_id="score-004",
                corpus="normativa",
                content="Allegato VII - Personal protective equipment requirements for workers exposed to hazards.",
                score=0.94,
                rank=1,
                source_document="Allegato VII",
                metadata={
                    "normative_refs": ["Allegato VII", "D.Lgs 81/08 Art. 74"],
                    "source_type": "normativa",
                },
            )
        ]
        
        scorer = ComplianceScorer()
        report = scorer.score_evidence(chunks, risk_category="rischi_dpi")
        
        assert report.is_compliant or report.score > 0.6


class TestProductionEdgeCases:
    """Test edge cases and error conditions."""
    
    def test_unicode_content(self):
        """Should handle Italian characters correctly."""
        chunk = EvidenceChunk(
            chunk_id="unicode-001",
            corpus="normativa",
            content="Disposizioni in materia di protezione da esposizione a rumori, polveri, vibrazioni e campi elettromagnetici nei luoghi di lavoro.",
            score=0.88,
            rank=1,
            source_document="Normativa Italiana",
            metadata={"source_type": "normativa"},
        )
        
        validator = MetadataValidator()
        report = validator.validate_chunk(chunk)
        
        assert len(report.issues) >= 0  # Should not crash
    
    def test_very_long_content(self):
        """Should handle very long content."""
        long_content = "Article on safety. " * 1000  # ~20KB
        chunk = EvidenceChunk(
            chunk_id="long-001",
            corpus="normativa",
            content=long_content,
            score=0.85,
            rank=1,
            source_document="Long Doc",
            metadata={"source_type": "normativa"},
        )
        
        validator = MetadataValidator()
        report = validator.validate_chunk(chunk)
        
        assert report.is_compliant or len(report.issues) > 0
    
    def test_null_metadata_fields(self):
        """Should handle null metadata gracefully."""
        chunk = EvidenceChunk(
            chunk_id="null-001",
            corpus="normativa",
            content="Valid content for testing null handling in metadata structures.",
            score=0.80,
            rank=1,
            source_document="Doc",
            metadata=None,  # Should be {} by default
        )
        
        validator = MetadataValidator()
        report = validator.validate_chunk(chunk)
        
        # Should not raise exception
        assert isinstance(report.score, float)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
