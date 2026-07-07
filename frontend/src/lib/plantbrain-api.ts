import type {
  AskPayload,
  AskResponse,
  CompliancePayload,
  DocumentListResponse,
  EquipmentItem,
  EquipmentListResponse,
  GraphStatsResponse,
  HealthResponse,
  QueryHistoryResponse,
  RiskSummaryResponse,
  UploadResponse,
  VoiceResponse,
} from '@/types/plantbrain';

export const API_BASE_URL = process.env.NEXT_PUBLIC_PLANTBRAIN_API_URL || 'https://ayush712145-plantbrain-backend.hf.space';

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const headers = new Headers(init?.headers);
  const isFormData = init?.body instanceof FormData;
  if (!isFormData && init?.body && !headers.has('Content-Type')) {
    headers.set('Content-Type', 'application/json');
  }

  let response: Response;
  try {
    response = await fetch(`${API_BASE_URL}${path}`, {
      ...init,
      headers,
    });
  } catch (error) {
    const apiError = new Error(`Backend is unreachable at ${API_BASE_URL}`) as Error & { status?: number; details?: unknown };
    apiError.details = error;
    throw apiError;
  }

  const contentType = response.headers.get('content-type') || '';
  const body = contentType.includes('application/json') ? await response.json().catch(() => null) : await response.text().catch(() => '');

  if (!response.ok) {
    const message = typeof body === 'object' && body && ('detail' in body || 'error' in body)
      ? String((body as { detail?: unknown; error?: unknown }).detail || (body as { error?: unknown }).error)
      : `Request failed with HTTP ${response.status}`;
    const apiError = new Error(message) as Error & { status?: number; details?: unknown };
    apiError.status = response.status;
    apiError.details = body;
    throw apiError;
  }

  return body as T;
}

function toQuery(params: Record<string, string | number | boolean | undefined>) {
  const search = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== '') search.set(key, String(value));
  });
  const query = search.toString();
  return query ? `?${query}` : '';
}

export function healthCheck() {
  return request<HealthResponse>('/api/v1/health');
}

export function deepHealthCheck() {
  return request<HealthResponse>('/api/v1/health/deep');
}

export function uploadDocument(file: File, description = '', extractionKind = 'auto', zone = '') {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('description', description || '');
  formData.append('extraction_kind', extractionKind);
  formData.append('zone', zone || '');
  return request<UploadResponse>('/api/v1/ingest/upload', { method: 'POST', body: formData });
}

export function loadDemoDocument() {
  return request<UploadResponse>('/api/v1/ingest/demo-document', { method: 'POST' });
}

export function getDocumentStatus(documentId: string) {
  return request<UploadResponse>(`/api/v1/ingest/status/${encodeURIComponent(documentId)}`);
}

export function listDocuments(skip = 0, limit = 50) {
  return request<DocumentListResponse>(`/api/v1/ingest/list${toQuery({ skip, limit })}`);
}

export function getPipelineOverview() {
  return request<{ runs?: unknown[]; metrics?: Record<string, unknown>; graph_backend?: string; neo4j_configured?: boolean }>('/api/v1/ingest/pipeline');
}

export function askQuestion(payload: AskPayload) {
  return request<AskResponse>('/api/v1/query/ask', {
    method: 'POST',
    body: JSON.stringify({ channel: 'web', language: 'auto', top_k: 5, include_graph_context: true, ...payload }),
  });
}

export function getQueryHistory(sessionId = '', limit = 20) {
  return request<QueryHistoryResponse>(`/api/v1/query/history${toQuery({ session_id: sessionId, limit })}`);
}

export function getGraphStats() {
  return request<GraphStatsResponse>('/api/v1/graph/stats');
}

export function getAllEquipment() {
  return request<EquipmentListResponse>('/api/v1/graph/equipment');
}

export function getEquipment(tag: string) {
  return request<EquipmentItem>(`/api/v1/graph/equipment/${encodeURIComponent(tag)}`);
}

export function exportGraph() {
  return request<{ nodes?: unknown[]; edges?: unknown[] }>('/api/v1/graph/export');
}

export function checkCompliance(payload: CompliancePayload) {
  return request<{ results?: unknown[]; [key: string]: unknown }>('/api/v1/compliance/check', {
    method: 'POST',
    body: JSON.stringify({ document_id: '', procedure_text: '', rule_codes: [], ...payload }),
  });
}

export function listComplianceRules() {
  return request<{ rules?: unknown[]; total?: number }>('/api/v1/compliance/rules');
}

export function getRiskSummary() {
  return request<RiskSummaryResponse>('/api/v1/patterns/risk-summary');
}

export function getFailureClusters(minOccurrences = 2) {
  return request<{ clusters?: unknown[]; failure_clusters?: unknown[]; [key: string]: unknown }>(`/api/v1/patterns/clusters${toQuery({ min_occurrences: minOccurrences })}`);
}

export function getOverdueInspections(thresholdDays = 180) {
  return request<{ overdue?: unknown[]; inspections?: unknown[]; [key: string]: unknown }>(`/api/v1/patterns/overdue${toQuery({ threshold_days: thresholdDays })}`);
}

export function transcribeVoice(file: File, language = '') {
  const formData = new FormData();
  formData.append('file', file);
  if (language) formData.append('language', language);
  return request<VoiceResponse>('/api/v1/voice/transcribe', { method: 'POST', body: formData });
}

export function getAdminStats(adminKey = '') {
  return request<Record<string, unknown>>('/api/v1/admin/stats', {
    headers: adminKey ? { 'X-Admin-Key': adminKey } : undefined,
  });
}

export function getAdminQueryStats(adminKey = '') {
  return request<Record<string, unknown>>('/api/v1/admin/query-stats', { headers: adminKey ? { 'X-Admin-Key': adminKey } : undefined });
}
export function getAdminLogs(adminKey = '') {
  return request<{ lines?: string[]; total_lines?: number }>('/api/v1/admin/logs/recent', { headers: adminKey ? { 'X-Admin-Key': adminKey } : undefined });
}
export function getWhatsAppConfigStatus() {
  return request<{ configured: boolean; webhook_url: string; from_number: string }>('/api/v1/whatsapp/config-status');
}
export function sendWhatsAppAlert(to_number: string, message: string) {
  return request<{ message_sid: string; status: string }>('/api/v1/whatsapp/send-alert', { method: 'POST', body: JSON.stringify({ to_number, message }) });
}
export function captureTypedKnowledge(payload: { text: string; equipment_tag?: string; severity?: string; inspector_name?: string }) {
  return request<VoiceResponse>('/api/v1/voice/transcribe-text', { method: 'POST', body: JSON.stringify(payload) });
}

