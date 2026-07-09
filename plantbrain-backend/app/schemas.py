"""Central Pydantic schemas for PlantBrain API request and response models."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class DocumentUploadResponse(BaseModel):
    """Response returned after accepting a document upload."""

    document_id: str
    filename: str
    status: str
    message: str

    model_config = ConfigDict(from_attributes=True)


class DocumentStatusResponse(BaseModel):
    """Document processing status response."""

    document_id: str
    filename: str
    original_filename: str
    status: str
    file_type: str
    total_chunks: int
    error_message: str | None
    uploaded_at: datetime
    processed_at: datetime | None

    model_config = ConfigDict(from_attributes=True)


class DocumentListItem(BaseModel):
    """Document list item response."""

    document_id: str
    filename: str
    status: str
    file_type: str
    total_chunks: int
    uploaded_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DocumentListResponse(BaseModel):
    """Paginated document list response."""

    documents: list[DocumentListItem]
    total: int
    skip: int
    limit: int

    model_config = ConfigDict(from_attributes=True)


class DocumentStatsResponse(BaseModel):
    """Aggregate document ingestion statistics."""

    total_documents: int
    completed: int
    processing: int
    failed: int
    total_chunks: int

    model_config = ConfigDict(from_attributes=True)


class QuestionRequest(BaseModel):
    """Question answering request."""

    question: str = Field(
        ...,
        min_length=3,
        max_length=2000,
        examples=["What are the known issues with pump P-202?"],
    )
    language: str = Field(default="auto", pattern="^(en|hi|auto)$", examples=["en", "hi", "auto"])
    session_id: str = Field(default="", examples=["demo-session-1"])
    top_k: int = Field(default=5, ge=1, le=10, examples=[5])
    filter_document_id: str = Field(default="", examples=[""])
    channel: str = Field(default="web", pattern="^(web|whatsapp|mobile)$", examples=["web"])
    include_graph_context: bool = Field(default=True, examples=[True])

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "question": "What are the known issues with pump P-202?",
                    "language": "auto",
                    "session_id": "demo-session-1",
                    "top_k": 5,
                    "filter_document_id": "",
                    "channel": "web",
                    "include_graph_context": True,
                },
                {
                    "question": "P-202 ??? ?? ???? ???????? ????",
                    "language": "hi",
                    "top_k": 5,
                    "channel": "web",
                    "include_graph_context": True,
                },
            ]
        }
    )


class SourceInfo(BaseModel):
    """Source chunk shown with a generated answer."""

    filename: str
    chunk_index: int
    text_preview: str
    page_number: int | None = None
    section: str = ""
    document_id: str | None = None
    freshness_score: int | None = None
    knowledge_decay: int | None = None
    freshness_status: str | None = None
    risk_level: str | None = None
    last_reviewed: str | None = None

    model_config = ConfigDict(from_attributes=True)


class TrustDocumentScore(BaseModel):
    """Per-document freshness score used by the answer trust gate."""

    document_id: str | None = None
    filename: str
    document_type: str = "document"
    last_reviewed: str | None = None
    review_date_source: str = "missing"
    document_age_days: int | None = None
    expected_review_interval_days: int
    freshness_score: int
    knowledge_decay: int
    freshness_status: str
    risk_level: str
    reason: str


class TrustSummary(BaseModel):
    """Knowledge Decay Engine output shown with every generated answer."""

    engine: str = "Knowledge Decay Engine"
    knowledge_decay: int
    freshness_score: int
    freshness: str
    confidence: int
    risk: str
    sources: int
    source_documents: int
    graph_assets: int
    trust_gate: str
    recommendation: str
    reason: str
    documents: list[TrustDocumentScore]
    confidence_flags: list[str] = Field(default_factory=list)
    pipeline: list[str] = Field(default_factory=list)
    question_scope: str = ""

    model_config = ConfigDict(from_attributes=True)


class QuestionResponse(BaseModel):
    """Question answering response."""

    answer: str
    confidence: str
    sources: list[SourceInfo]
    response_time_ms: int
    query_id: str
    equipment_mentioned: list[str]
    graph_context: list[dict[str, Any]] = Field(default_factory=list)
    trust_summary: TrustSummary
    model_config = ConfigDict(from_attributes=True)


class QueryHistoryItem(BaseModel):
    """Query history item response."""

    id: str
    question: str
    answer: str
    confidence: float | None
    created_at: datetime
    response_time_ms: int | None
    channel: str

    model_config = ConfigDict(from_attributes=True)


class EquipmentCreate(BaseModel):
    """Equipment creation request."""

    tag: str = Field(..., pattern=r"^[A-Z]{1,3}-\d{3,4}[A-Z]?$", examples=["P-202"])
    name: str = Field(default="", examples=["Crude Transfer Pump"])
    equipment_type: str = Field(default="", examples=["pump"])
    location: str = Field(default="", examples=["Pump House A"])
    description: str = Field(default="", examples=["Main crude oil transfer pump feeding the preheat train."])

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "tag": "P-202",
                    "name": "Crude Transfer Pump",
                    "equipment_type": "pump",
                    "location": "Pump House A",
                    "description": "Main crude oil transfer pump feeding the preheat train.",
                }
            ]
        }
    )


class EquipmentResponse(BaseModel):
    """Equipment graph node response."""

    tag: str
    attributes: dict
    neighbors: list[dict] = []

    model_config = ConfigDict(from_attributes=True)


class EquipmentNode(BaseModel):
    """Equipment list node response."""

    tag: str
    attributes: dict
    neighbor_count: int

    model_config = ConfigDict(from_attributes=True)


class RelationshipCreate(BaseModel):
    """Equipment relationship creation request."""

    source_tag: str = Field(examples=["P-202"])
    target_tag: str = Field(examples=["HE-303"])
    relationship_type: str = Field(
        ...,
        pattern="^(feeds_into|controls|bypasses|connected_to|part_of)$",
        examples=["feeds_into"],
    )

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "source_tag": "P-202",
                    "target_tag": "HE-303",
                    "relationship_type": "feeds_into",
                }
            ]
        }
    )


class GraphStatsResponse(BaseModel):
    """Equipment graph stats response."""

    nodes: int
    edges: int
    top_connected: list[dict]
    graph_backend: str = "networkx_fallback"
    equipment_count: int = 0
    valve_count: int = 0
    instrument_count: int = 0
    maintenance_event_count: int = 0

    model_config = ConfigDict(from_attributes=True)


class ComplianceRuleCreate(BaseModel):
    """Compliance rule creation request."""

    rule_code: str = Field(examples=["OISD-116-3.2"])
    regulation_body: str = Field(..., pattern="^(OISD|PESO|Factory_Act)$", examples=["OISD"])
    title: str = Field(examples=["Pressure relief valves must be tested every 2 years"])
    full_text: str = Field(
        examples=["Pressure relief valves protecting process equipment must be inspected and tested at intervals not exceeding two years."]
    )
    category: str = Field(examples=["pressure_vessel"])

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "rule_code": "OISD-116-3.2",
                    "regulation_body": "OISD",
                    "title": "Pressure relief valves must be tested every 2 years",
                    "full_text": "Pressure relief valves protecting process equipment must be inspected and tested at intervals not exceeding two years.",
                    "category": "pressure_vessel",
                }
            ]
        }
    )


class ComplianceRuleResponse(BaseModel):
    """Compliance rule response."""

    id: str
    rule_code: str
    regulation_body: str
    title: str
    category: str
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ComplianceCheckRequest(BaseModel):
    """Compliance check request."""

    document_id: str = Field(default="", examples=[""])
    rule_codes: list[str] = Field(default=[], examples=[["OISD-116-3.2"]])
    procedure_text: str = Field(default="", examples=["PRV tested annually and records are maintained."])

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "document_id": "",
                    "rule_codes": ["OISD-116-3.2"],
                    "procedure_text": "PRV tested annually and records are maintained.",
                }
            ]
        }
    )


class ComplianceCheckResult(BaseModel):
    """Compliance check result response."""

    rule_code: str
    rule_title: str
    status: str
    findings: str
    recommendation: str

    model_config = ConfigDict(from_attributes=True)


class FailureCluster(BaseModel):
    """Repeated failure cluster response."""

    equipment_tag: str
    occurrence_count: int
    severity_distribution: dict
    first_seen: str
    last_seen: str
    frequency_per_month: float
    ai_summary: str
    risk_score: float

    model_config = ConfigDict(from_attributes=True)


class OverdueInspection(BaseModel):
    """Overdue inspection response."""

    equipment_tag: str
    equipment_name: str
    equipment_type: str
    last_inspection_date: str
    days_since_last_inspection: int
    overdue_by_days: int
    risk_level: str

    model_config = ConfigDict(from_attributes=True)


class RiskSummaryResponse(BaseModel):
    """Combined risk summary dashboard response."""

    failure_clusters: list[FailureCluster]
    overdue_inspections_count: int
    critical_overdue: list[OverdueInspection]
    cooccurrence_patterns: list[dict]
    overall_risk_level: str
    generated_at: str

    model_config = ConfigDict(from_attributes=True)


class TranscriptionResponse(BaseModel):
    """Voice transcription response."""

    document_id: str
    text: str
    language_detected: str
    duration_seconds: float
    equipment_tags_found: list[str]
    knowledge_extracted: dict
    inspection_created: bool

    model_config = ConfigDict(from_attributes=True)


class TextKnowledgeRequest(BaseModel):
    """Typed voice-knowledge capture request."""

    text: str = Field(min_length=1)
    equipment_tag: str = ""
    severity: str = "routine"
    inspector_name: str = ""


class ManualInspectionCreate(BaseModel):
    """Manual inspection creation request."""

    equipment_tag: str
    inspection_date: datetime
    inspector_name: str = ""
    inspection_type: str = "manual"
    findings: str
    severity: str


class FeedbackRequest(BaseModel):
    """Query feedback request."""

    helpful: bool
    comment: str = ""


class HealthResponse(BaseModel):
    """Health check response."""

    status: str
    version: str
    environment: str
    timestamp: str | None = None

    model_config = ConfigDict(from_attributes=True)


class MessageResponse(BaseModel):
    """Generic message response."""

    message: str

    model_config = ConfigDict(from_attributes=True)


class ErrorResponse(BaseModel):
    """Generic error response."""

    error: str
    message: str
    status_code: int | None = None

    model_config = ConfigDict(from_attributes=True)

class WhatsAppAlertRequest(BaseModel):
    """Outbound WhatsApp alert request."""

    to_number: str
    message: str
    twilio_account_sid: str = ""
    twilio_auth_token: str = ""
    from_number: str = ""


