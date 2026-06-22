from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional

class SourceCitation(BaseModel):
    document_title: str
    source_type: str
    excerpt: str = Field(..., max_length=200)
    page_or_section: str
    freshness_score: float = Field(..., ge=0.0, le=1.0)
    
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

class LLMResponse(BaseModel):
    answer: str
    sources_used: List[SourceCitation]
    confidence_score: float = Field(..., ge=0.0, le=1.0)
    model_used: str
    latency_ms: int
    fallback_triggered: bool
    
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

class QueryRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=500)
    equipment_context: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

class DocumentSummary(BaseModel):
    title: str
    freshness_score: float
    
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

class QueryResponse(BaseModel):
    answer: str
    sources_used: List[SourceCitation]
    confidence_score: float
    model_used: str
    latency_ms: int
    fallback_triggered: bool
    retrieved_documents: List[DocumentSummary]
    
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

class DocumentUploadResponse(BaseModel):
    document_id: str
    message: str
    
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

class HealthChecks(BaseModel):
    supabase: str
    claude: str
    gemini: str
    
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

class HealthResponse(BaseModel):
    status: str
    version: str
    uptime_seconds: int
    checks: HealthChecks
    
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

class ErrorResponse(BaseModel):
    error: str
    message: str
    detail: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)
