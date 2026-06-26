'use client';

import { FileText, RefreshCw, UploadCloud } from 'lucide-react';
import { useEffect, useState } from 'react';
import { getDocumentStatus, listDocuments, uploadDocument } from '@/lib/plantbrain-api';
import type { DocumentItem } from '@/types/plantbrain';

function documentId(document: DocumentItem) {
  return String(document.document_id || document.id || '');
}

function chunks(document: DocumentItem) {
  return Number(document.total_chunks || document.chunks || 0);
}

export function DocumentIngestionPanel({ onComplete, onStatsChange }: { onComplete: () => void; onStatsChange: (count: number) => void }) {
  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [file, setFile] = useState<File | null>(null);
  const [description, setDescription] = useState('');
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState('');

  const refresh = async () => {
    setLoading(true);
    setError('');
    try {
      const response = await listDocuments(0, 100);
      const items = response.documents || [];
      setDocuments(items);
      onStatsChange(Number(response.total ?? items.length));
      if (items.some((item) => String(item.status || '').toLowerCase() === 'completed')) onComplete();
    } catch (err: any) {
      setError(err?.status ? `${err.message} (HTTP ${err.status})` : err?.message || 'Failed to load documents.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    refresh();
  }, []);

  const upload = async () => {
    if (!file) return;
    setUploading(true);
    setError('');
    try {
      const result = await uploadDocument(file, description);
      const id = String(result.document_id || result.id || '');
      onComplete();
      if (id) {
        for (let attempt = 0; attempt < 5; attempt += 1) {
          await new Promise((resolve) => setTimeout(resolve, 1500));
          await getDocumentStatus(id).catch(() => null);
        }
      }
      setFile(null);
      setDescription('');
      await refresh();
    } catch (err: any) {
      setError(err?.status ? `${err.message} (HTTP ${err.status})` : err?.message || 'Upload failed.');
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="space-y-5">
      <section className="rounded-3xl border border-white/10 bg-white/[0.04] p-5 shadow-2xl shadow-black/20">
        <div className="mb-5 flex flex-col gap-3 md:flex-row md:items-start md:justify-between"><div><div className="text-xs font-semibold uppercase tracking-[0.2em] text-cyan-300">Step 01 - Connect your documents</div><h2 className="mt-2 text-2xl font-semibold text-white">Upload real plant files</h2><p className="mt-2 max-w-3xl text-sm leading-6 text-slate-400">Upload P&IDs, maintenance records, safety procedures, inspection reports, OEM manuals, or compliance guidelines. PlantBrain processes real files through the backend ingestion pipeline.</p></div><button onClick={refresh} className="inline-flex items-center gap-2 rounded-xl border border-white/10 px-3 py-2 text-sm text-slate-200 hover:border-cyan-400/50"><RefreshCw className="h-4 w-4" /> Refresh</button></div>
        {error && <div className="mb-4 rounded-xl border border-red-400/20 bg-red-400/10 p-3 text-sm text-red-100">{error}</div>}
        <div className="grid gap-4 lg:grid-cols-[1fr_320px]">
          <div className="rounded-2xl border border-dashed border-cyan-400/30 bg-cyan-400/5 p-5">
            <label className="flex cursor-pointer flex-col items-center justify-center gap-3 rounded-xl border border-white/10 bg-[#090f18] p-8 text-center transition hover:border-cyan-400/50"><UploadCloud className="h-10 w-10 text-cyan-300" /><span className="text-sm font-semibold text-white">{file ? file.name : 'Choose PDF, DOCX, TXT, PNG, JPG, XLSX'}</span><span className="text-xs text-slate-500">Actual upload goes to POST /api/v1/ingest/upload</span><input className="hidden" type="file" accept=".pdf,.docx,.txt,.png,.jpg,.jpeg,.xlsx" onChange={(event) => setFile(event.target.files?.[0] || null)} /></label>
            <input value={description} onChange={(event) => setDescription(event.target.value)} placeholder="Optional description for this document" className="mt-4 w-full rounded-xl border border-white/10 bg-white/[0.04] px-3 py-3 text-sm text-white outline-none placeholder:text-slate-600 focus:border-cyan-400/50" />
            <button onClick={upload} disabled={!file || uploading} className="mt-4 inline-flex w-full items-center justify-center gap-2 rounded-xl bg-cyan-300 px-4 py-3 text-sm font-semibold text-slate-950 transition hover:bg-cyan-200 disabled:cursor-not-allowed disabled:opacity-50"><UploadCloud className="h-4 w-4" /> {uploading ? 'Uploading and polling...' : 'Upload Document'}</button>
          </div>
          <div className="rounded-2xl border border-white/10 bg-white/[0.03] p-4"><div className="mb-3 text-sm font-semibold text-white">Suggested file names</div>{['P&ID - Crude Distillation Unit.pdf', 'Pump P-201 OEM Manual.pdf', 'Furnace F-7 Safety Procedure.docx', 'OISD Inspection Checklist.pdf'].map((name) => <div key={name} className="mb-2 rounded-lg border border-white/10 bg-white/[0.03] px-3 py-2 text-xs text-slate-300">{name}</div>)}</div>
        </div>
      </section>

      <section className="rounded-3xl border border-white/10 bg-white/[0.04] p-5 shadow-2xl shadow-black/20">
        <div className="mb-4 flex items-center justify-between"><h3 className="text-lg font-semibold text-white">Backend document list</h3><span className="rounded-full border border-white/10 px-3 py-1 text-xs text-slate-300">{documents.length} loaded</span></div>
        {loading ? <div className="rounded-2xl border border-white/10 bg-white/[0.03] p-8 text-center text-slate-400">Loading documents...</div> : documents.length === 0 ? <div className="rounded-2xl border border-white/10 bg-white/[0.03] p-8 text-center text-slate-400">No documents yet. Upload a real file to begin.</div> : <div className="overflow-hidden rounded-2xl border border-white/10"><table className="w-full text-left text-sm"><thead className="bg-white/[0.04] text-xs uppercase tracking-wide text-slate-500"><tr><th className="px-4 py-3">File</th><th className="px-4 py-3">ID</th><th className="px-4 py-3">Status</th><th className="px-4 py-3">Chunks</th><th className="px-4 py-3">Uploaded</th></tr></thead><tbody>{documents.map((document) => <tr key={documentId(document) || document.filename} className="border-t border-white/10"><td className="px-4 py-3 text-white"><FileText className="mr-2 inline h-4 w-4 text-cyan-300" />{document.original_filename || document.filename || 'Untitled'}</td><td className="px-4 py-3 font-mono text-xs text-slate-400">{documentId(document) || '-'}</td><td className="px-4 py-3"><span className="rounded-full border border-emerald-400/20 bg-emerald-400/10 px-2 py-1 text-xs text-emerald-100">{document.status || 'unknown'}</span></td><td className="px-4 py-3 text-slate-300">{chunks(document)}</td><td className="px-4 py-3 text-slate-400">{document.uploaded_at ? new Date(document.uploaded_at).toLocaleString() : '-'}</td></tr>)}</tbody></table></div>}
      </section>
    </div>
  );
}