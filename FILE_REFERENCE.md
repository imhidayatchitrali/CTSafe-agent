# 📂 RAG Compliance Implementation - File Reference

## Quick Navigation

All new files for RAG compliance improvements are organized below with their purposes and key entry points.

---

## 🔧 Core Validators (app/services/)

### `compliance_validator.py`
**Purpose:** Main compliance validation framework  
**Lines:** ~450  
**Key Classes:**
- `ComplianceScorer` - Overall compliance scoring
- `MetadataValidator` - Chunk metadata validation
- `RegulatoryRefValidator` - Normative reference validation
- `RiskDpiValidator` - DPI requirement validation
- `ComplianceIssue` & `ComplianceReport` - Data models

**Entry Points:**
```python
# Validate evidence
from app.services.compliance_validator import validate_evidence
report = validate_evidence(chunks, risk_category="rischi_chimici")

# Validate section DPI
from app.services.compliance_validator import validate_section_dpi
report = validate_section_dpi(section, risk_categories=[...], mansioni=[...])
```

---

### `evidence_tracer.py`
**Purpose:** Audit trail and compliance tracking  
**Lines:** ~300  
**Key Classes:**
- `EvidenceTracer` - Main tracer with logging methods
- `EvidenceTraceLog` - Single trace entry data model

**Entry Points:**
```python
# Log a search
from app.services.evidence_tracer import log_search
log_search(search_input, result, trace_id, compliance_passed=True, ...)

# Get trace report
from app.services.evidence_tracer import get_trace_report
report = get_trace_report(trace_id)

# Get compliance summary
from app.services.evidence_tracer import get_compliance_summary
summary = get_compliance_summary()
```

---

## ✅ Tests (tests/)

### `test_rag_compliance.py`
**Purpose:** Comprehensive compliance test suite  
**Lines:** ~450  
**Test Classes:** 5 (18 total test methods)

**Test Coverage:**
- `TestMetadataValidator` - Chunk metadata validation
- `TestRegulatoryRefValidator` - Normative reference validation
- `TestRiskDpiValidator` - DPI requirement validation
- `TestComplianceScorer` - Overall compliance scoring
- `TestProductionEdgeCases` - Unicode, long content, nulls

**Run Tests:**
```bash
# All tests
pytest tests/test_rag_compliance.py -v

# Specific test class
pytest tests/test_rag_compliance.py::TestComplianceScorer -v

# With coverage
pytest tests/test_rag_compliance.py --cov=app.services.compliance_validator
```

---

### `fixtures/rag_compliance_cases.json`
**Purpose:** 24 compliance test scenarios  
**Format:** JSON array of test cases

**Test Scenarios Include:**
- Core normative requirements (D.Lgs 81/08, amendments)
- Risk-specific validations (6 risk types)
- DPI requirements
- DVR structure requirements
- Job role requirements (3 roles)
- Company size requirements
- Edge cases (5 scenarios)

**Each test specifies:**
- `name` - Unique test ID
- `description` - What's being tested
- `query` - Search query string
- `corpus` - normativa | indice | dvr_pregressi
- `filters` - Search filters
- `min_results`, `top_k` - Result expectations
- `must_include_terms` - Required content terms
- `must_include_source_terms` - Required source document terms

---

## 🚀 Scripts (scripts/)

### `validate_rag_compliance.py`
**Purpose:** CLI tool for production validation  
**Lines:** ~400  
**Language:** Python with argparse

**Usage:**
```bash
# Mock backend (no external dependencies)
python scripts/validate_rag_compliance.py --rag-backend mock

# Supabase backend (requires env vars)
python scripts/validate_rag_compliance.py --rag-backend supabase --verbose
```

**What It Validates:**
1. Mock RAG basic searches (2 tests)
2. Metadata completeness (3 tests)
3. Regulatory reference presence (3 tests)
4. Compliance scoring accuracy (2 tests)

**Outputs:**
- Console report with pass/fail status
- JSON report: `rag_validation_report.json`
- Exit code: 0 (pass) or 1 (fail)

---

## 📖 Documentation

### `RAG_COMPLIANCE_GUIDE.md`
**Purpose:** Complete reference guide  
**Length:** 2000+ words
**Sections:**
1. Overview of improvements
2. What's new (5 components)
3. Compliance validation work flow
4. Regulatory reference mapping
5. Production readiness checklist
6. Performance considerations
7. Troubleshooting guide
8. Integration examples

**Key Sections:**
- Compliance scoring algorithm (with formula)
- Regulatory reference mapping table
- DPI requirements by risk type
- Integration code examples
- Production readiness checklist

---

### `RAG_COMPLIANCE_SUMMARY.md`
**Purpose:** Implementation summary and quick reference  
**Length:** 1500+ words
**Sections:**
1. What was delivered
2. Current validation results
3. Key regulatory mappings
4. Integration examples
5. Production checklist
6. File reference
7. Next steps

---

### `FILE_REFERENCE.md`
**Purpose:** This file - navigation guide for all new files

---

## 📊 Integration Points

### In Your Workflows

**Section Generation:**
```python
# After RAG search
from app.services.compliance_validator import validate_evidence

evidence = rag_tool.search(search_input)
compliance = validate_evidence(evidence, risk_category=risk)

if not compliance.is_compliant:
    # Handle non-compliance
    for issue in compliance.issues:
        if issue.severity == "error":
            # Critical: cannot proceed
            log_error(issue)
        elif issue.severity == "warning":
            # Recoverable: log but continue
            log_warning(issue)
```

**Audit Trail:**
```python
# Throughout execution
from app.services.evidence_tracer import log_search, get_trace_report
import uuid

trace_id = str(uuid.uuid4())

# Log key operations
log_search(search_input, result, trace_id, compliance_passed=..., ...)

# Later retrieve full audit trail
report = get_trace_report(trace_id)
```

---

## 🎯 What Each File Does

| File | Type | Lines | Purpose | Entry Point |
|------|------|-------|---------|------------|
| `compliance_validator.py` | Source | 450+ | Core validators | `validate_evidence()` |
| `evidence_tracer.py` | Source | 300+ | Audit trails | `log_search()` |
| `test_rag_compliance.py` | Test | 450+ | Test suite | `pytest` |
| `rag_compliance_cases.json` | Fixture | 500+ | Test scenarios | Loaded by tests |
| `validate_rag_compliance.py` | CLI | 400+ | Production validation | `python ...` |
| `RAG_COMPLIANCE_GUIDE.md` | Docs | 2000+ | Reference guide | Read |
| `RAG_COMPLIANCE_SUMMARY.md` | Docs | 1500+ | Implementation summary | Read |

---

## ⚡ Quick Start

### 1. Validate Locally
```bash
cd /path/to/project
python scripts/validate_rag_compliance.py --rag-backend mock
```

### 2. Run Tests
```bash
pytest tests/test_rag_compliance.py -v
```

### 3. Integrate into Code
```python
from app.services.compliance_validator import validate_evidence
report = validate_evidence(chunks)
print(f"Score: {report.score:.2f}, Compliant: {report.is_compliant}")
```

### 4. Read Documentation
```bash
# Main reference
cat RAG_COMPLIANCE_GUIDE.md

# Summary of what was done
cat RAG_COMPLIANCE_SUMMARY.md
```

---

## 📋 Compliance Criteria Implemented

✅ **Metadata Completeness**
- Source document specified
- Source type valid (normativa, template_structure, dvr_pregresso)
- Document type specified
- Content substantial (>50 characters)

✅ **Normative References**
- D.Lgs 81/08 or amendments cited
- Risk-specific norms present
- Allegati (annexes) when applicable

✅ **DPI Alignment**
- Risks have corresponding DPI in section
- Baseline DPI for job roles included
- DPI requirements match risk severity

✅ **Risk-Specific Validations**
- Chemical (Allegato XIII)
- Biological (Art. 272)
- Asbestos (Allegato XII)
- Noise (Art. 189)
- Vibration (Art. 198)
- DPI (Allegato VII)

---

## 🔗 Cross-References

**Compliance Validators depend on:**
- `app.domain.models` - EvidenceChunk, SectionRecord
- `app.domain.enums` - ComplianceSeverity (defined in validator)

**Evidence Tracer depends on:**
- `app.domain.models` - RagSearchInput, RagSearchResult
- Standard library: json, logging, uuid

**Tests depend on:**
- `pytest` - Test runner
- All validators and tracer modules

**CLI depends on:**
- All validators, tracer, RAG search tool
- `argparse` - CLI argument parsing
- `json` - Report export

---

## 📞 For Help

1. **Understanding the validators**
   - Read: `RAG_COMPLIANCE_GUIDE.md` → "How Compliance Validation Works"
   - Review: `tests/test_rag_compliance.py` → Usage examples

2. **Integration questions**
   - Read: `RAG_COMPLIANCE_GUIDE.md` → "Integration Guide"
   - Check: `RAG_COMPLIANCE_SUMMARY.md` → "Integration Examples"

3. **Production deployment**
   - Read: `RAG_COMPLIANCE_GUIDE.md` → "Production Readiness Checklist"
   - Run: `python scripts/validate_rag_compliance.py --rag-backend supabase`

4. **Troubleshooting**
   - Read: `RAG_COMPLIANCE_GUIDE.md` → "Troubleshooting"
   - Check: `rag_validation_report.json` after running validation

---

**Last Updated:** May 31, 2026  
**Status:** ✅ Complete and Tested  
**Version:** 1.0
