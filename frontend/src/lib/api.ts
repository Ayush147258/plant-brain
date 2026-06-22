import axios, { AxiosError } from 'axios';

// -- Interfaces matching Pydantic Models --

export interface SourceCitation {
  document_title: string;
  source_type: string;
  excerpt: string;
  page_or_section: string;
  freshness_score: number;
}

export interface DocumentSummary {
  title: string;
  freshness_score: number;
  id?: string;
  source_type?: string;
  last_validated_date?: string;
  equipment_tags?: string[];
}

export interface QueryResponse {
  answer: string;
  sources_used: SourceCitation[];
  confidence_score: number;
  model_used: string;
  latency_ms: number;
  fallback_triggered: boolean;
  retrieved_documents: DocumentSummary[];
}

export interface DocumentUploadResponse {
  document_id: string;
  message: string;
}

export interface HealthChecks {
  supabase: string;
  claude: string;
  gemini: string;
}

export interface HealthResponse {
  status: string;
  version: string;
  uptime_seconds: number;
  checks: HealthChecks;
}

export interface AppError {
  code: string;
  message: string;
  status: number;
}

// -- API Configuration --

const BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: `${BASE_URL}/api`,
  headers: {
    'Content-Type': 'application/json',
  },
});

function handleApiError(error: unknown): never {
  if (axios.isAxiosError(error)) {
    const axiosError = error as AxiosError<any>;
    const appError: AppError = {
      code: axiosError.response?.data?.error || axiosError.code || 'UNKNOWN_ERROR',
      message: axiosError.response?.data?.message || axiosError.message,
      status: axiosError.response?.status || 500,
    };
    throw appError;
  }
  throw { code: 'CLIENT_ERROR', message: (error as Error).message, status: 0 };
}

// -- API Methods --

export async function queryKnowledge(question: string, equipmentContext?: string): Promise<QueryResponse> {
  try {
    const { data } = await api.post<QueryResponse>('/query', { question, equipment_context: equipmentContext });
    return data;
  } catch (error) {
    handleApiError(error);
  }
}

export async function getDocuments(): Promise<DocumentSummary[]> {
  try {
    const { data } = await api.get<DocumentSummary[]>('/documents');
    return data;
  } catch (error) {
    handleApiError(error);
  }
}

export async function uploadDocument(file: File, sourceType: string): Promise<DocumentUploadResponse> {
  try {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('source_type', sourceType);
    formData.append('metadata', JSON.stringify({ freshness_score: 1.0 }));
    
    const { data } = await api.post<DocumentUploadResponse>('/documents/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return data;
  } catch (error) {
    handleApiError(error);
  }
}

export async function checkHealth(): Promise<HealthResponse> {
  try {
    const { data } = await api.get<HealthResponse>('/health');
    return data;
  } catch (error) {
    handleApiError(error);
  }
}

export async function streamQuery(
  question: string,
  onToken: (token: string) => void,
  onDone: (response: QueryResponse) => void
): Promise<void> {
  try {
    const res = await fetch(`${BASE_URL}/api/query/stream`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question }),
    });

    if (!res.ok) {
      const errorText = await res.text();
      throw { code: 'STREAM_ERROR', message: errorText, status: res.status } as AppError;
    }

    if (!res.body) throw new Error('ReadableStream not supported in this browser.');

    const reader = res.body.getReader();
    const decoder = new TextDecoder('utf-8');
    let buffer = '';

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n\n');
      buffer = lines.pop() || ''; // Keep incomplete part

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const dataStr = line.substring(6);
          try {
            const parsed = JSON.parse(dataStr);
            if (parsed.type === 'token') {
              onToken(parsed.data);
            } else if (parsed.type === 'done') {
              onDone(parsed.data);
            } else if (parsed.type === 'error') {
              throw new Error(parsed.data);
            }
          } catch (e) {
            console.error('Failed to parse SSE chunk:', line, e);
          }
        }
      }
    }
  } catch (error) {
    if ((error as AppError).code) throw error;
    throw { code: 'FETCH_ERROR', message: (error as Error).message, status: 0 } as AppError;
  }
}
