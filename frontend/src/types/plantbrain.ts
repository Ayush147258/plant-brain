export type ApiError = Error & {
  status?: number;
  details?: unknown;
};

export type HealthResponse = {
  status?: string;
  timestamp?: string;
  version?: string;
  environment?: string;
  checks?: Record<string, unknown>;
  [key: string]: unknown;
};

export type DocumentItem = {
  id?: string;
  document_id?: string;
  filename?: string;
  original_filename?: string;
  status?: string;
  chunks?: number;
  total_chunks?: number;
  uploaded_at?: string;
  processed_at?: string;
  description?: string;
  file_type?: string;
  file_size_bytes?: number;
  error_message?: string | null;
  [key: string]: unknown;
};

export type DocumentListResponse = {
  documents?: DocumentItem[];
  total?: number;
  skip?: number;
  limit?: number;
  [key: string]: unknown;
};

export type UploadResponse = {
  document_id?: string;
  id?: string;
  filename?: string;
  status?: string;
  message?: string;
  [key: string]: unknown;
};

export type AskPayload = {
  question: string;
  language?: string;
  top_k?: number;
  session_id?: string;
  include_graph_context?: boolean;
  filter_document_id?: string;
  channel?: string;
};


export type TrustDocumentScore = {
  document_id?: string | null;
  filename?: string;
  document_type?: string;
  last_reviewed?: string | null;
  review_date_source?: string;
  document_age_days?: number | null;
  expected_review_interval_days?: number;
  freshness_score?: number;
  knowledge_decay?: number;
  freshness_status?: string;
  risk_level?: string;
  reason?: string;
  [key: string]: unknown;
};

export type TrustSummary = {
  engine?: string;
  knowledge_decay?: number;
  freshness_score?: number;
  freshness?: string;
  confidence?: number;
  risk?: string;
  sources?: number;
  source_documents?: number;
  graph_assets?: number;
  trust_gate?: string;
  recommendation?: string;
  reason?: string;
  documents?: TrustDocumentScore[];
  confidence_flags?: string[];
  pipeline?: string[];
  question_scope?: string;
  [key: string]: unknown;
};
export type AskResponse = {
  answer?: string;
  response?: string;
  confidence?: number | string;
  sources?: SourceItem[];
  citations?: SourceItem[];
  equipment_mentioned?: string[];
  graph_context?: Array<Record<string, unknown>>;
  language?: string;
  session_id?: string;
  query_id?: string;
  response_time_ms?: number;
  trust_summary?: TrustSummary;
  [key: string]: unknown;
};

export type SourceItem = {
  document?: string;
  filename?: string;
  source?: string;
  section?: string;
  page_or_section?: string;
  page_number?: number;
  snippet?: string;
  text_preview?: string;
  excerpt?: string;
  score?: number;
  confidence?: number;
  chunk_index?: number;
  document_id?: string | null;
  freshness_score?: number | null;
  knowledge_decay?: number | null;
  freshness_status?: string | null;
  risk_level?: string | null;
  last_reviewed?: string | null;
  url?: string;
  [key: string]: unknown;
};

export type QueryHistoryItem = {
  id?: string;
  question?: string;
  answer?: string;
  confidence?: number | string | null;
  created_at?: string;
  response_time_ms?: number | null;
  channel?: string;
  [key: string]: unknown;
};

export type QueryHistoryResponse = {
  queries?: QueryHistoryItem[];
  total?: number;
  [key: string]: unknown;
};

export type GraphStatsResponse = {
  nodes?: number;
  edges?: number;
  top_connected?: Array<{ tag?: string; connections?: number; [key: string]: unknown }>;
  [key: string]: unknown;
};

export type EquipmentItem = {
  tag?: string;
  name?: string;
  equipment_type?: string;
  location?: string;
  description?: string;
  neighbor_count?: number;
  neighbors?: Array<Record<string, unknown>>;
  attributes?: Record<string, unknown>;
  [key: string]: unknown;
};

export type EquipmentListResponse = {
  equipment?: EquipmentItem[];
  total?: number;
  [key: string]: unknown;
};

export type ComplianceRule = {
  id?: string;
  rule_code?: string;
  regulation_body?: string;
  title?: string;
  full_text?: string;
  category?: string;
  is_active?: boolean;
  [key: string]: unknown;
};

export type CompliancePayload = {
  document_id?: string;
  procedure_text?: string;
  rule_codes?: string[];
};

export type ComplianceResult = {
  rule_code?: string;
  rule_title?: string;
  status?: string;
  findings?: string;
  recommendation?: string;
  [key: string]: unknown;
};

export type VoiceResponse = {
  document_id?: string;
  text?: string;
  transcript?: string;
  language_detected?: string;
  duration_seconds?: number;
  equipment_tags_found?: string[];
  knowledge_extracted?: Record<string, unknown>;
  inspection_created?: boolean;
  [key: string]: unknown;
};

export type RiskSummaryResponse = {
  failure_clusters?: Array<Record<string, unknown>>;
  overdue_inspections_count?: number;
  critical_overdue?: Array<Record<string, unknown>>;
  cooccurrence_patterns?: Array<Record<string, unknown>>;
  overall_risk_level?: string;
  generated_at?: string;
  [key: string]: unknown;
};

export type FailureIntelligenceResponse = {
  engine?: string;
  status?: string;
  evidence_mode?: string;
  objective?: string;
  source_coverage?: Record<string, number>;
  warnings?: Array<Record<string, unknown>>;
  systemic_patterns?: Array<Record<string, unknown>>;
  qms_signals?: Array<Record<string, unknown>>;
  validation_metrics?: Array<Record<string, unknown>>;
  pipeline?: string[];
  generated_at?: string;
  [key: string]: unknown;
};

