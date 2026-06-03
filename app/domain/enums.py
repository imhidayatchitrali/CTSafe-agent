from __future__ import annotations

from enum import Enum


class Role(str, Enum):
    client_user = "client_user"
    ctsafe_reviewer = "ctsafe_reviewer"
    admin = "admin"


class ProjectStatus(str, Enum):
    intake_pending_confirmation = "intake_pending_confirmation"
    blocked_missing_data = "blocked_missing_data"
    data_confirmed = "data_confirmed"
    index_draft = "index_draft"
    index_approved = "index_approved"
    index_needs_revision = "index_needs_revision"
    pilot_sections_generated = "pilot_sections_generated"
    draft_document_created = "draft_document_created"
    needs_revision = "needs_revision"


class IndexStatus(str, Enum):
    draft = "draft"
    approved = "approved"
    rejected = "rejected"
    needs_revision = "needs_revision"


class SectionStatus(str, Enum):
    planned = "planned"
    in_progress = "in_progress"
    generated = "generated"
    qa_approved = "qa_approved"
    needs_revision = "needs_revision"
    blocked_missing_data = "blocked_missing_data"


class QAStatus(str, Enum):
    approved = "approved"
    needs_revision = "needs_revision"
    blocked_missing_data = "blocked_missing_data"


class DocumentStatus(str, Enum):
    draft = "draft"
    superseded = "superseded"


class PatchStatus(str, Enum):
    proposed = "proposed"
    applied = "applied"
    rejected = "rejected"

