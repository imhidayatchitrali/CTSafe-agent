from __future__ import annotations

from uuid import UUID

from app.domain.enums import (
    DocumentStatus,
    IndexStatus,
    ProjectStatus,
    QAStatus,
    SectionStatus,
)
from app.domain.models import (
    Actor,
    AgentRunRecord,
    AirtableSyncInput,
    CompanyInput,
    DocxRenderInput,
    DocumentPatchRecord,
    DocumentPatchRequest,
    DvrIndexRecord,
    DvrIndexSectionBrief,
    DvrProjectRecord,
    GeneratedDocumentRecord,
    IntakeResult,
    RagSearchInput,
    SectionEvidenceWriteInput,
    SectionRecord,
)
from app.errors import WorkflowError
from app.repositories.project_repository import ProjectRepository
from app.repositories.section_repository import SectionRepository
from app.services.airtable_sync_service import AirtableSyncService
from app.services.docx_render_service import DocxRenderService
from app.services.rag_search_tool import RagSearchTool
from app.services.section_evidence_writer import SectionEvidenceWriter
from app.settings import AppSettings


class DvrWorkflow:
    def __init__(
        self,
        settings: AppSettings,
        project_repository: ProjectRepository,
        section_repository: SectionRepository,
        rag_search_tool: RagSearchTool,
        evidence_writer: SectionEvidenceWriter,
        docx_render_service: DocxRenderService,
        airtable_sync_service: AirtableSyncService,
    ):
        self.settings = settings
        self.project_repository = project_repository
        self.section_repository = section_repository
        self.rag_search_tool = rag_search_tool
        self.evidence_writer = evidence_writer
        self.docx_render_service = docx_render_service
        self.airtable_sync_service = airtable_sync_service

    def intake(self, company: CompanyInput) -> IntakeResult:
        missing_fields = company.missing_required_fields()
        status = (
            ProjectStatus.blocked_missing_data
            if missing_fields
            else ProjectStatus.intake_pending_confirmation
        )
        return IntakeResult(
            status=status,
            missing_fields=missing_fields,
            summary={
                "company_name": company.company_name,
                "ateco_code": company.ateco_code,
                "employee_count": company.employee_count,
                "mansions": company.mansions,
                "risk_category": company.risk_category,
            },
        )

    def create_project(
        self, company: CompanyInput, source_channel: str, actor: Actor
    ) -> DvrProjectRecord:
        intake = self.intake(company)
        if intake.missing_fields:
            raise WorkflowError(
                code="blocked_missing_data",
                message="Cannot create project before required fields are present.",
                status_code=422,
            )
        return self.project_repository.create_project(
            company_input=company,
            actor=actor,
            source_channel=source_channel,
        )

    def confirm_project(self, project_id: UUID, actor: Actor) -> dict:
        project = self.project_repository.confirm_project(project_id, actor)
        sync_result = self.airtable_sync_service.sync_project(
            AirtableSyncInput(project=project)
        )
        if sync_result.legacy_record_id:
            project = self.project_repository.attach_airtable_sync(
                project_id=project.id,
                legacy_record_id=sync_result.legacy_record_id,
                legacy_status="In validazione",
            )
        self._record_agent_run(
            project=project,
            agent_name="AirtableSyncService",
            input_payload={"project_id": str(project.id)},
            output_payload=sync_result.model_dump(mode="json"),
        )
        return {"project": project, "airtable_sync": sync_result}

    def generate_index(self, project_id: UUID, actor: Actor) -> DvrIndexRecord:
        project = self.project_repository.get_project(project_id)
        if project.status not in {
            ProjectStatus.data_confirmed,
            ProjectStatus.index_needs_revision,
            ProjectStatus.index_draft,
        }:
            raise WorkflowError(
                code="project_not_confirmed",
                message="Project data must be confirmed before index generation.",
                status_code=409,
            )

        query = (
            f"DVR {project.company.ateco_code} {project.company.activity_description} "
            f"{project.company.risk_category}"
        )
        evidence = self.rag_search_tool.search(
            RagSearchInput(query=query, corpus="indice", top_k=3)
        )
        index = DvrIndexRecord(
            project_id=project.id,
            sections=self._build_preliminary_briefs(project),
            rag_evidence_ids=[chunk.chunk_id for chunk in evidence.evidence],
        )
        saved_index = self.project_repository.save_index(index)
        self._record_agent_run(
            project=project,
            agent_name="IndexDraftAgent",
            input_payload={"query": query},
            output_payload=saved_index.model_dump(mode="json"),
        )
        self.project_repository.add_audit_event(
            actor=actor,
            action="index.generate",
            project_id=project.id,
            target_type="dvr_index",
            target_id=str(saved_index.id),
        )
        return saved_index

    def review_index(
        self, project_id: UUID, index_id: UUID, decision: IndexStatus, actor: Actor, notes: str | None
    ) -> DvrIndexRecord:
        if decision is IndexStatus.draft:
            raise WorkflowError(
                code="invalid_index_decision",
                message="Index review decision cannot be draft.",
                status_code=422,
            )
        index = self.project_repository.get_index(index_id)
        if index.project_id != project_id:
            raise WorkflowError(
                code="index_project_mismatch",
                message="Index does not belong to the project.",
                status_code=404,
            )
        return self.project_repository.review_index(index_id, decision, actor, notes)

    def generate_pilot_sections(
        self, project_id: UUID, actor: Actor, max_sections: int = 2
    ) -> list[SectionRecord]:
        project = self.project_repository.get_project(project_id)
        index = self.project_repository.get_active_index(project_id)
        if index is None or index.status is not IndexStatus.approved:
            raise WorkflowError(
                code="index_approval_required",
                message="Section generation cannot start before index approval.",
                status_code=409,
            )

        generated: list[SectionRecord] = []
        for brief in index.sections[:max_sections]:
            section = self.section_repository.create_section(project.id, index.id, brief)
            section.status = SectionStatus.in_progress
            query = self._section_query(project, brief)
            rag_result = self.rag_search_tool.search(
                RagSearchInput(
                    query=query,
                    corpus="normativa",
                    filters={
                        "risk_category": project.company.risk_category,
                        "section_number": brief.section_number,
                    },
                    top_k=4,
                )
            )
            evidence_result = self.evidence_writer.save(
                SectionEvidenceWriteInput(
                    project_id=project.id,
                    section_id=section.id,
                    search_result=rag_result,
                    claim_or_section_part_supported=brief.title,
                )
            )
            section.generated_markdown = self._draft_section_markdown(
                project, brief, rag_result.evidence
            )
            section.missing_data = self._section_missing_data(project, brief)
            if section.missing_data:
                section.qa_status = QAStatus.blocked_missing_data
                section.status = SectionStatus.blocked_missing_data
            elif not rag_result.evidence:
                section.qa_status = QAStatus.needs_revision
                section.status = SectionStatus.needs_revision
            else:
                section.qa_status = QAStatus.approved
                section.status = SectionStatus.qa_approved
            section.qa_report = {
                "qa_status": section.qa_status.value,
                "issues": [],
                "missing_data": section.missing_data,
                "unsupported_claims": [],
                "retrieval_gaps": self._retrieval_gaps(
                    rag_result.fallback_reason,
                    evidence_result.saved_count,
                ),
                "human_review_required": True,
            }
            generated.append(self.section_repository.save_section(section))
            self._record_agent_run(
                project=project,
                agent_name="ChapterWriterAgent",
                input_payload={"section_id": str(section.id), "query": query},
                output_payload={
                    "section_id": str(section.id),
                    "qa_status": section.qa_status.value,
                    "evidence_saved": evidence_result.saved_count,
                },
            )

        project.status = ProjectStatus.pilot_sections_generated
        self.project_repository.save_project(project)
        self.project_repository.add_audit_event(
            actor=actor,
            action="sections.generate_pilot",
            project_id=project.id,
            metadata={"count": len(generated)},
        )
        return generated

    def generate_docx_draft(self, project_id: UUID, actor: Actor) -> GeneratedDocumentRecord:
        project = self.project_repository.get_project(project_id)
        sections = self.section_repository.list_sections_for_project(project_id)
        if not sections:
            raise WorkflowError(
                code="sections_required",
                message="At least one QA-approved section is required before DOCX draft.",
                status_code=409,
            )
        blocked = [
            section
            for section in sections
            if section.qa_status is not QAStatus.approved
            or section.status is not SectionStatus.qa_approved
        ]
        if blocked:
            raise WorkflowError(
                code="section_qa_required",
                message="All pilot sections must pass QA before DOCX draft.",
                status_code=409,
            )

        current_versions = [
            document.version
            for document in self.project_repository.list_generated_documents_for_project(
                project_id
            )
        ]
        version = max(current_versions, default=0) + 1
        render_result = self.docx_render_service.render_draft(
            DocxRenderInput(
                project=project,
                sections=sections,
                output_dir=self.settings.output_dir,
                template_path=self.settings.template_path,
                version=version,
            )
        )
        document = GeneratedDocumentRecord(
            id=render_result.document_id,
            project_id=project.id,
            version=render_result.version,
            status=DocumentStatus.draft,
            file_path=render_result.path,
            editable=render_result.editable,
            metadata={
                "warnings": render_result.warnings,
                "prompt_version": self.settings.prompt_version,
                "rag_policy_version": self.settings.rag_policy_version,
            },
            created_by=actor.user_id,
        )
        saved = self.project_repository.save_generated_document(document)
        self.project_repository.add_audit_event(
            actor=actor,
            action="document.draft_generate",
            project_id=project.id,
            target_type="generated_document",
            target_id=str(saved.id),
        )
        return saved

    def request_patch(
        self,
        project_id: UUID,
        request: DocumentPatchRequest,
        actor: Actor,
    ) -> DocumentPatchRecord:
        self.project_repository.get_project(project_id)
        patch = DocumentPatchRecord(
            project_id=project_id,
            target_section_id=request.target_section_id,
            instruction=request.instruction,
            proposed_patch={
                "mode": "targeted_revision",
                "status": "needs_human_review",
                "instruction": request.instruction,
            },
            created_by=actor.user_id,
        )
        saved = self.project_repository.save_patch(patch)
        self.project_repository.add_audit_event(
            actor=actor,
            action="patch.request",
            project_id=project_id,
            target_type="document_patch",
            target_id=str(saved.id),
        )
        return saved

    def _build_preliminary_briefs(
        self, project: DvrProjectRecord
    ) -> list[DvrIndexSectionBrief]:
        company = project.company
        return [
            DvrIndexSectionBrief(
                section_number="1",
                title="Identificazione dell'attivita",
                purpose="Descrivere azienda, sede, attivita e dati minimi del DVR.",
                required_company_data=[
                    "company_name",
                    "vat_number",
                    "site_address",
                    "activity_description",
                ],
                retrieval_hints=[company.ateco_code or "", company.activity_description or ""],
                include_tables=True,
            ),
            DvrIndexSectionBrief(
                section_number="2",
                title="Mansioni e rischi principali",
                purpose="Collegare mansioni, pericoli di settore e rischi per mansione.",
                required_company_data=["mansions", "sector_hazards", "risks_by_mansion"],
                retrieval_hints=company.mansions + company.sector_hazards,
                include_tables=True,
            ),
            DvrIndexSectionBrief(
                section_number="3",
                title="Dispositivi di protezione individuali",
                purpose="Preparare una tabella DPI collegata a rischi e mansioni.",
                required_company_data=["mansions", "risks_by_mansion"],
                retrieval_hints=["DPI", "rischi", "mansioni"],
                include_tables=True,
            ),
        ]

    def _section_query(self, project: DvrProjectRecord, brief: DvrIndexSectionBrief) -> str:
        company = project.company
        hints = " ".join(brief.retrieval_hints)
        return (
            f"{brief.title} {company.ateco_code} {company.activity_description} "
            f"{company.risk_category} {hints}"
        )

    def _section_missing_data(
        self, project: DvrProjectRecord, brief: DvrIndexSectionBrief
    ) -> list[str]:
        missing: list[str] = []
        for field_name in brief.required_company_data:
            value = getattr(project.company, field_name)
            if value is None or value == "" or value == [] or value == {}:
                missing.append(field_name)
        return missing

    def _draft_section_markdown(
        self,
        project: DvrProjectRecord,
        brief: DvrIndexSectionBrief,
        evidence: list,
    ) -> str:
        company = project.company
        source_notes = "; ".join(
            f"{chunk.source_document or chunk.chunk_id} ({chunk.chunk_id})"
            for chunk in evidence
        )
        return (
            f"### {brief.title}\n\n"
            f"La sezione riguarda {company.company_name} e viene predisposta per "
            f"l'attivita dichiarata: {company.activity_description}.\n\n"
            f"Dati aziendali usati: ATECO {company.ateco_code}, sede {company.site_address}, "
            f"categoria rischio {company.risk_category}, mansioni {', '.join(company.mansions)}.\n\n"
            f"Per questa bozza pilota i rischi devono restare collegati alle mansioni "
            f"e ai pericoli indicati dall'utente. Eventuali dati non disponibili devono "
            f"restare come DATO MANCANTE o DA VERIFICARE.\n\n"
            f"Evidenze RAG salvate: {source_notes}."
        )

    def _retrieval_gaps(
        self, fallback_reason: str | None, saved_count: int
    ) -> list[str]:
        if saved_count:
            return []
        if fallback_reason:
            return [f"No evidence was saved. Fallback reason: {fallback_reason}"]
        return ["No evidence was saved."]

    def _record_agent_run(
        self,
        project: DvrProjectRecord,
        agent_name: str,
        input_payload: dict,
        output_payload: dict,
    ) -> None:
        self.project_repository.add_agent_run(
            AgentRunRecord(
                project_id=project.id,
                agent_name=agent_name,
                input=input_payload,
                output=output_payload,
                status="completed",
                model=self.settings.default_model,
                llm_provider=self.settings.default_llm_provider,
            )
        )
