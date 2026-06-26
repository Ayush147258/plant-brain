import axios, { AxiosError } from 'axios';

const BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
const API_V1 = `${BASE_URL}/api/v1`;

export interface AppError {
  code: string;
  message: string;
  status: number;
}

export interface SourceCitation {
  document_title: string;
  source_type: string;
  excerpt: string;
  page_or_section: string;
  freshness_score: number;
}

export interface HealthResponse {
  status: string;
  version: string;
  environment: string;
  timestamp?: string;
}


export interface DeepHealthResponse {
  status: 'healthy' | 'degraded' | 'unhealthy';
  checks: {
    database: boolean;
    vector_store: boolean;
    graph: boolean;
  };
  timestamp: string;
}

export interface StartupCheck {
  name: string;
  status: 'pass' | 'warn' | 'fail';
  message: string;
}

export interface StartupChecksResponse {
  checks: StartupCheck[];
  checked_at: string | null;
}

export interface DocumentUploadResponse {
  document_id: string;
  filename: string;
  status: string;
  message: string;
}

export interface DocumentListResponse {
  documents: Array<{
    document_id: string;
    filename: string;
    original_filename?: string;
    status: string;
    file_type: string;
    total_chunks: number;
    uploaded_at: string;
  }>;
  total: number;
  skip: number;
  limit: number;
}

export interface DocumentStatsResponse {
  total_documents: number;
  completed: number;
  processing: number;
  failed: number;
  total_chunks: number;
}

export interface QuestionResponse {
  answer: string;
  confidence: string;
  sources: Array<{ filename: string; chunk_index: number; text_preview: string }>;
  response_time_ms: number;
  query_id: string;
  equipment_mentioned: string[];
}

export interface QueryHistoryResponse {
  queries: Array<{
    id: string;
    question: string;
    answer: string;
    confidence: number | null;
    created_at: string;
    response_time_ms: number | null;
    channel?: string;
  }>;
  total: number;
}

export interface GraphStatsResponse {
  nodes: number;
  edges: number;
  top_connected: Array<{ tag: string; connections: number }>;
}

export interface EquipmentListResponse {
  equipment: Array<Record<string, any>>;
  total: number;
}

export interface RiskSummaryResponse {
  failure_clusters: any[];
  overdue_inspections_count: number;
  critical_overdue: any[];
  cooccurrence_patterns: any[];
  overall_risk_level: string;
  generated_at?: string;
}

export interface ComplianceRulesResponse {
  rules: Array<{
    id: string;
    rule_code: string;
    regulation_body: string;
    title: string;
    full_text?: string;
    category: string;
    is_active: boolean;
    created_at: string;
  }>;
  total: number;
}

export interface AdminStatsResponse {
  database: Record<string, any>;
  vector_store: Record<string, any>;
  graph: Record<string, any>;
  uptime_seconds: number;
}

const api = axios.create({
  baseURL: API_V1,
  timeout: 60000,
  headers: { 'Content-Type': 'application/json' },
});

function handleApiError(error: unknown): never {
  if (axios.isAxiosError(error)) {
    const axiosError = error as AxiosError<any>;
    throw {
      code: axiosError.response?.data?.error || axiosError.code || 'API_ERROR',
      message: axiosError.response?.data?.message || axiosError.response?.data?.detail || axiosError.message,
      status: axiosError.response?.status || 500,
    } satisfies AppError;
  }
  throw { code: 'CLIENT_ERROR', message: (error as Error).message, status: 0 } satisfies AppError;
}

export async function healthCheck(): Promise<HealthResponse> {
  try {
    const { data } = await api.get<HealthResponse>('/health');
    return data;
  } catch (error) {
    handleApiError(error);
  }
}


export async function deepHealthCheck(): Promise<DeepHealthResponse> {
  try {
    const { data } = await api.get<DeepHealthResponse>('/health/deep', {
      validateStatus: (status) => status < 500 || status === 503,
    });
    return data;
  } catch (error) {
    handleApiError(error);
  }
}

export async function getStartupChecks(): Promise<StartupChecksResponse> {
  try {
    const { data } = await api.get<StartupChecksResponse>('/startup-checks');
    return data;
  } catch (error) {
    handleApiError(error);
  }
}


export async function getDocsExamples(): Promise<Record<string, string>> {
  try {
    const { data } = await api.get<Record<string, string>>('/docs-examples');
    return data;
  } catch (error) {
    handleApiError(error);
  }
}

export async function getVersion(): Promise<any> {
  try {
    const { data } = await api.get('/version');
    return data;
  } catch (error) {
    handleApiError(error);
  }
}

export async function getPostmanCollection(): Promise<any> {
  try {
    const { data } = await api.get('/postman-collection');
    return data;
  } catch (error) {
    handleApiError(error);
  }
}

export async function uploadBackendDocument(file: File, description = ''): Promise<DocumentUploadResponse> {
  try {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('description', description);
    const { data } = await api.post<DocumentUploadResponse>('/ingest/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return data;
  } catch (error) {
    handleApiError(error);
  }
}

export async function getDocumentStatus(documentId: string): Promise<any> {
  try {
    const { data } = await api.get(`/ingest/status/${documentId}`);
    return data;
  } catch (error) {
    handleApiError(error);
  }
}

export async function getDocumentStats(): Promise<DocumentStatsResponse> {
  try {
    const { data } = await api.get<DocumentStatsResponse>('/ingest/stats');
    return data;
  } catch (error) {
    handleApiError(error);
  }
}
export async function listDocuments(skip = 0, limit = 20): Promise<DocumentListResponse> {
  try {
    const { data } = await api.get<DocumentListResponse>('/ingest/list', { params: { skip, limit } });
    return data;
  } catch (error) {
    handleApiError(error);
  }
}

export async function getProcessingOverview(): Promise<any> {
  try {
    const { data } = await api.get('/ingest/processing');
    return data;
  } catch (error) {
    handleApiError(error);
  }
}

export async function cancelDocumentProcessing(documentId: string): Promise<any> {
  try {
    const { data } = await api.delete(`/ingest/processing/${documentId}`);
    return data;
  } catch (error) {
    handleApiError(error);
  }
}

export async function deleteDocument(documentId: string): Promise<any> {
  try {
    await api.delete(`/ingest/${documentId}`);
    return { deleted: true, document_id: documentId };
  } catch (error) {
    handleApiError(error);
  }
}

export async function askPlantBrain(
  question: string,
  options: { language?: string; top_k?: number; session_id?: string; include_graph_context?: boolean } = {}
): Promise<QuestionResponse> {
  try {
    const { data } = await api.post<QuestionResponse>('/query/ask', {
      question,
      language: options.language || 'auto',
      top_k: options.top_k ?? 5,
      session_id: options.session_id || '',
      include_graph_context: options.include_graph_context ?? true,
      channel: 'web',
    });
    return data;
  } catch (error) {
    handleApiError(error);
  }
}

export async function getQueryHistory(session_id = '', limit = 20): Promise<QueryHistoryResponse> {
  try {
    const { data } = await api.get<QueryHistoryResponse>('/query/history', { params: { session_id, limit } });
    return data;
  } catch (error) {
    handleApiError(error);
  }
}

export async function searchChunks(query: string, top_k = 5, document_id = ''): Promise<any> {
  try {
    const { data } = await api.get('/query/search-chunks', { params: { query, top_k, document_id } });
    return data;
  } catch (error) {
    handleApiError(error);
  }
}

export async function recordQueryFeedback(queryId: string, helpful: boolean, comment = ''): Promise<any> {
  try {
    const { data } = await api.post(`/query/feedback/${queryId}`, { helpful, comment });
    return data;
  } catch (error) {
    handleApiError(error);
  }
}

export async function getGraphStats(): Promise<GraphStatsResponse> {
  try {
    const { data } = await api.get<GraphStatsResponse>('/graph/stats');
    return data;
  } catch (error) {
    handleApiError(error);
  }
}

export async function getEquipment(tag: string): Promise<any> {
  try {
    const { data } = await api.get(`/graph/equipment/${tag}`);
    return data;
  } catch (error) {
    handleApiError(error);
  }
}

export async function getAllEquipment(): Promise<EquipmentListResponse> {
  try {
    const { data } = await api.get<EquipmentListResponse>('/graph/equipment');
    return data;
  } catch (error) {
    handleApiError(error);
  }
}

export async function createEquipment(payload: { tag: string; name?: string; equipment_type?: string; location?: string; description?: string }): Promise<any> {
  try {
    const { data } = await api.post('/graph/equipment', payload);
    return data;
  } catch (error) {
    handleApiError(error);
  }
}

export async function createRelationship(payload: { source_tag: string; target_tag: string; relationship_type: string }): Promise<any> {
  try {
    const { data } = await api.post('/graph/relationship', payload);
    return data;
  } catch (error) {
    handleApiError(error);
  }
}

export async function getNeighbors(tag: string, depth = 1, relationship_type = ''): Promise<any> {
  try {
    const { data } = await api.get(`/graph/neighbors/${tag}`, { params: { depth, relationship_type } });
    return data;
  } catch (error) {
    handleApiError(error);
  }
}

export async function getShortestPath(sourceTag: string, targetTag: string): Promise<any> {
  try {
    const { data } = await api.get(`/graph/path/${sourceTag}/${targetTag}`);
    return data;
  } catch (error) {
    handleApiError(error);
  }
}

export async function exportGraph(): Promise<any> {
  try {
    const { data } = await api.get('/graph/export');
    return data;
  } catch (error) {
    handleApiError(error);
  }
}

export async function checkCompliance(payload: { document_id?: string; procedure_text?: string; rule_codes?: string[] }): Promise<any> {
  try {
    const { data } = await api.post('/compliance/check', {
      document_id: payload.document_id || '',
      procedure_text: payload.procedure_text || '',
      rule_codes: payload.rule_codes || [],
    });
    return data;
  } catch (error) {
    handleApiError(error);
  }
}

export async function listComplianceRules(): Promise<ComplianceRulesResponse> {
  try {
    const { data } = await api.get<ComplianceRulesResponse>('/compliance/rules');
    return data;
  } catch (error) {
    handleApiError(error);
  }
}

export async function seedComplianceRules(): Promise<any> {
  try {
    const { data } = await api.post('/compliance/seed-rules');
    return data;
  } catch (error) {
    handleApiError(error);
  }
}

export async function getComplianceChecksForDocument(documentId: string): Promise<any> {
  try {
    const { data } = await api.get(`/compliance/checks/document/${documentId}`);
    return data;
  } catch (error) {
    handleApiError(error);
  }
}

export async function getRiskSummary(): Promise<RiskSummaryResponse> {
  try {
    const { data } = await api.get<RiskSummaryResponse>('/patterns/risk-summary');
    return data;
  } catch (error) {
    handleApiError(error);
  }
}

export async function getFailureClusters(min_occurrences = 2): Promise<any> {
  try {
    const { data } = await api.get('/patterns/clusters', { params: { min_occurrences } });
    return data;
  } catch (error) {
    handleApiError(error);
  }
}

export async function getOverdueInspections(threshold_days = 180): Promise<any> {
  try {
    const { data } = await api.get('/patterns/overdue', { params: { threshold_days } });
    return data;
  } catch (error) {
    handleApiError(error);
  }
}

export async function getCooccurrencePatterns(window_days = 30): Promise<any> {
  try {
    const { data } = await api.get('/patterns/cooccurrence', { params: { window_days } });
    return data;
  } catch (error) {
    handleApiError(error);
  }
}

export async function seedInspectionRecords(): Promise<any> {
  try {
    const { data } = await api.post('/patterns/inspections/seed');
    return data;
  } catch (error) {
    handleApiError(error);
  }
}

export async function createManualInspection(payload: {
  equipment_tag: string;
  inspection_date: string;
  inspector_name: string;
  inspection_type: string;
  findings: string;
  severity: string;
}): Promise<any> {
  try {
    const { data } = await api.post('/patterns/inspections/manual', payload);
    return data;
  } catch (error) {
    handleApiError(error);
  }
}

export async function transcribeVoice(audio: File, language = ''): Promise<any> {
  try {
    const formData = new FormData();
    formData.append('file', audio);
    formData.append('language', language);
    const { data } = await api.post('/voice/transcribe', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return data;
  } catch (error) {
    handleApiError(error);
  }
}

export async function transcribeTextKnowledge(payload: { text: string; equipment_tag?: string; severity?: string; inspector_name?: string }): Promise<any> {
  try {
    const { data } = await api.post('/voice/transcribe-text', payload);
    return data;
  } catch (error) {
    handleApiError(error);
  }
}

export async function getRecentVoiceCaptures(): Promise<any> {
  try {
    const { data } = await api.get('/voice/recent-captures');
    return data;
  } catch (error) {
    handleApiError(error);
  }
}

export async function getWhatsAppWebhookHealth(): Promise<any> {
  try {
    const { data } = await api.get('/whatsapp/webhook');
    return data;
  } catch (error) {
    handleApiError(error);
  }
}

export async function getAdminStats(adminKey = ''): Promise<AdminStatsResponse> {
  try {
    const { data } = await api.get<AdminStatsResponse>('/admin/stats', {
      headers: adminKey ? { 'X-Admin-Key': adminKey } : {},
    });
    return data;
  } catch (error) {
    handleApiError(error);
  }
}

export async function getAdminQueryStats(adminKey = ''): Promise<any> {
  try {
    const { data } = await api.get('/admin/query-stats', {
      headers: adminKey ? { 'X-Admin-Key': adminKey } : {},
    });
    return data;
  } catch (error) {
    handleApiError(error);
  }
}

export async function getRecentLogs(adminKey = ''): Promise<any> {
  try {
    const { data } = await api.get('/admin/logs/recent', {
      headers: adminKey ? { 'X-Admin-Key': adminKey } : {},
    });
    return data;
  } catch (error) {
    handleApiError(error);
  }
}

export async function reprocessDocument(documentId: string, adminKey = ''): Promise<any> {
  try {
    const { data } = await api.post(`/admin/reprocess/${documentId}`, null, {
      headers: adminKey ? { 'X-Admin-Key': adminKey } : {},
    });
    return data;
  } catch (error) {
    handleApiError(error);
  }
}

// Backward-compatible names for older components.
export const checkHealth = healthCheck;
export const getDocuments = async () => (await listDocuments()).documents;
export const uploadDocument = uploadBackendDocument;
export const queryKnowledge = async (question: string) => askPlantBrain(question);

export async function streamQuery(
  question: string,
  onToken: (token: string) => void,
  onDone: (response: QuestionResponse) => void
): Promise<void> {
  const response = await askPlantBrain(question);
  onToken(response.answer);
  onDone(response);
}
