from __future__ import annotations

import logging

from app.domain.models import AirtableSyncInput, AirtableSyncResult

logger = logging.getLogger(__name__)


class AirtableSyncService:
    """Minimal Fase 1 legacy sync adapter.

    The default mode is mock. It preserves the boundary and output contract
    without requiring broad Airtable access in the runtime agent.
    """

    def __init__(self, enabled: bool = False):
        self.enabled = enabled

    def sync_project(self, request: AirtableSyncInput) -> AirtableSyncResult:
        project = request.project
        if not self.enabled:
            legacy_id = f"mock_airtable_{str(project.id)[:8]}"
            return AirtableSyncResult(
                status="mocked",
                legacy_record_id=legacy_id,
                message="Airtable sync is mocked for Fase 1 local thin slice.",
                is_mock=True,
            )
        logger.warning("airtable.sync.enabled_without_client")
        return AirtableSyncResult(
            status="skipped",
            legacy_record_id=None,
            message="Airtable client is not configured in this thin slice.",
            is_mock=True,
        )

