'use client';

import { CheckCircle2, FileCheck2, FileText, Loader2, RefreshCw, UploadCloud, XCircle } from 'lucide-react';
import { useCallback, useEffect, useRef, useState } from 'react';
import { getDocumentStatus, listDocuments, loadDemoDocument, uploadDocument } from '@/lib/plantbrain-api';
import type { DocumentItem, UploadResponse } from '@/types/plantbrain';

function documentId(document: DocumentItem) { return String(document.document_id || document.id || ''); }
function chunks(document: DocumentItem) { return Number(document.total_chunks || document.chunks || 0); }
function isTerminal(status: string) { return ['completed', 'failed'].includes(status.toLowerCase()); }

type UploadActivity = { id: string; filename: string; status: string; chunks: number; message: string };

export function DocumentIngestionPanel({ onComplete, onStatsChange }: { onComplete: () => void; onStatsChange: (count: number) => void }) {
  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [file, setFile] = useState<File | null>(null);
  const [description, setDescription] = useState('');
  const [extractionKind, setExtractionKind] = useState('auto');
  const [zone, setZone] = useState('');
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [loadingDemo, setLoadingDemo] = useState(false);
  const [activity, setActivity] = useState<UploadActivity | null>(null);
  const [error, setError] = useState('');
  const fileInput = useRef<HTMLInputElement>(null);
  const completeRef = useRef(onComplete);
  const statsRef = useRef(onStatsChange);
  completeRef.current = onComplete;
  statsRef.current = onStatsChange;

  const refresh = useCallback(async (showLoader = false) => {
    if (showLoader) setLoading(true);
    try {
      const response = await listDocuments(0, 100);
      const items = response.documents || [];
      setDocuments(items);
      statsRef.current(Number(response.total ?? items.length));
      if (items.some((item) => String(item.status || '').toLowerCase() === 'completed')) completeRef.current();
    } catch (err: any) {
      setError(err?.status ? `${err.message} (HTTP ${err.status})` : err?.message || 'Failed to load documents.');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    refresh(true);
    const interval = window.setInterval(() => refresh(false), 5000);
    return () => window.clearInterval(interval);
  }, [refresh]);

  const track = async (result: UploadResponse, fallbackFilename: string) => {
    const id = String(result.document_id || result.id || '');
    const filename = String(result.filename || fallbackFilename);
    setActivity({ id, filename, status: String(result.status || 'processing'), chunks: 0, message: String(result.message || 'Upload accepted') });
    await refresh(false);
    if (!id) return;
    for (let attempt = 0; attempt < 45; attempt += 1) {
      const current = await getDocumentStatus(id);
      const status = String(current.status || 'processing');
      setActivity({ id, filename: String(current.original_filename || current.filename || filename), status, chunks: Number(current.total_chunks || 0), message: status === 'completed' ? 'Indexed and ready for questions' : status === 'failed' ? String(current.error_message || 'Processing failed') : 'Backend is parsing and indexing this file' });
      await refresh(false);
      if (isTerminal(status)) {
        if (status === 'completed') onComplete();
        return;
      }
      await new Promise((resolve) => setTimeout(resolve, 1200));
    }
    setActivity((current) => current ? { ...current, message: 'Still processing. The list will update automatically.' } : current);
  };

  const upload = async () => {
    if (!file) { setError('Choose a file before uploading.'); return; }
    const selected = file;
    setUploading(true); setError('');
    setActivity({ id: '', filename: selected.name, status: 'uploading', chunks: 0, message: `Sending ${(selected.size / 1024).toFixed(1)} KB to PlantBrain` });
    try {
      const result = await uploadDocument(selected, description, extractionKind, zone);
      await track(result, selected.name);
      setFile(null); setDescription(''); setZone('');
      if (fileInput.current) fileInput.current.value = '';
    } catch (err: any) {
      const message = err?.status ? `${err.message} (HTTP ${err.status})` : err?.message || 'Upload failed.';
      setError(message);
      setActivity((current) => current ? { ...current, status: 'failed', message } : current);
    } finally { setUploading(false); }
  };

  const useDemoPdf = async () => {
    setLoadingDemo(true); setError('');
    setActivity({ id: '', filename: 'OSHA_3120_Lockout_Tagout.pdf', status: 'requesting', chunks: 0, message: 'Loading the official OSHA maintenance-safety booklet' });
    try { await track(await loadDemoDocument(), 'OSHA_3120_Lockout_Tagout.pdf'); }
    catch (err: any) { const message = err?.message || 'Could not load the demo PDF.'; setError(message); setActivity((current) => current ? { ...current, status: 'failed', message } : current); }
    finally { setLoadingDemo(false); }
  };

  const activityTone = activity?.status === 'completed' ? 'border-emerald-400/30 bg-emerald-400/10' : activity?.status === 'failed' ? 'border-red-400/30 bg-red-400/10' : 'border-cyan-400/30 bg-cyan-400/10';
  const ActivityIcon = activity?.status === 'completed' ? CheckCircle2 : activity?.status === 'failed' ? XCircle : Loader2;

  return <div className="space-y-5">
    <section className="rounded-3xl border border-white/10 bg-white/[0.04] p-5 shadow-2xl shadow-black/20">
      <div className="mb-5 flex flex-col gap-3 md:flex-row md:items-start md:justify-between"><div><div className="text-xs font-semibold uppercase tracking-[0.2em] text-cyan-300">Step 01 - Connect your documents</div><h2 className="mt-2 text-2xl font-semibold text-white">Upload real plant files</h2><p className="mt-2 max-w-3xl text-sm leading-6 text-slate-400">Select a file, confirm its name, then watch it move through upload, parsing, and indexing.</p></div><button onClick={() => refresh(true)} className="inline-flex items-center gap-2 rounded-xl border border-white/10 px-3 py-2 text-sm text-slate-200 hover:border-cyan-400/50"><RefreshCw className="h-4 w-4" /> Refresh</button></div>
      {error && <div className="mb-4 rounded-xl border border-red-400/20 bg-red-400/10 p-3 text-sm text-red-100">{error}</div>}
      {activity && <div className={`mb-4 flex items-start gap-3 rounded-xl border p-4 ${activityTone}`}><ActivityIcon className={`mt-0.5 h-5 w-5 shrink-0 ${!isTerminal(activity.status) ? 'animate-spin text-cyan-300' : activity.status === 'completed' ? 'text-emerald-300' : 'text-red-300'}`} /><div className="min-w-0 flex-1"><div className="flex flex-wrap items-center justify-between gap-2"><span className="break-all font-semibold text-white">{activity.filename}</span><span className="rounded-full border border-white/10 px-2 py-1 text-[10px] font-semibold uppercase tracking-wide text-slate-200">{activity.status}</span></div><p className="mt-1 text-xs text-slate-300">{activity.message}{activity.chunks ? ` | ${activity.chunks} indexed chunks` : ''}</p>{activity.id && <p className="mt-1 truncate font-mono text-[10px] text-slate-500">Document ID: {activity.id}</p>}</div></div>}
      <div className="mb-4 grid gap-3 md:grid-cols-2"><button onClick={useDemoPdf} disabled={loadingDemo || uploading} className="flex items-center gap-3 border border-emerald-400/25 bg-emerald-400/10 p-4 text-left disabled:opacity-60"><FileCheck2 className="h-7 w-7 text-emerald-300" /><span><span className="block font-semibold text-white">{loadingDemo ? 'Loading OSHA PDF...' : 'Use official OSHA safety PDF'}</span><span className="mt-1 block text-xs text-emerald-100/70">OSHA 3120 - real lockout/tagout guidance</span></span></button><div className="border border-white/10 bg-white/[0.03] p-4"><div className="font-semibold text-white">Or upload your own document</div><div className="mt-1 text-xs text-slate-400">PDF, DOCX, images, text, and spreadsheets.</div></div></div>
      <div className="grid gap-4 lg:grid-cols-[1fr_320px]"><div className="rounded-2xl border border-dashed border-cyan-400/30 bg-cyan-400/5 p-5"><label className="flex cursor-pointer flex-col items-center justify-center gap-3 rounded-xl border border-white/10 bg-[#090f18] p-8 text-center hover:border-cyan-400/50"><UploadCloud className="h-10 w-10 text-cyan-300" /><span className="break-all text-sm font-semibold text-white">{file ? file.name : 'Choose PDF, DOCX, TXT, PNG, JPG, XLSX'}</span><span className="text-xs text-slate-500">{file ? `${file.type || 'Document'} | ${(file.size / 1024).toFixed(1)} KB selected` : 'No file selected yet'}</span><input ref={fileInput} className="hidden" type="file" accept=".pdf,.docx,.txt,.png,.jpg,.jpeg,.xlsx" onChange={(event) => { setFile(event.target.files?.[0] || null); setError(''); }} /></label>{file && <div className="mt-3 flex items-center gap-2 rounded-lg border border-cyan-400/20 bg-cyan-400/10 px-3 py-2 text-xs text-cyan-100"><FileText className="h-4 w-4" /><span className="min-w-0 flex-1 truncate">Ready to upload: {file.name}</span></div>}<input value={description} onChange={(event) => setDescription(event.target.value)} placeholder="Optional description" className="mt-4 w-full rounded-xl border border-white/10 bg-white/[0.04] px-3 py-3 text-sm text-white outline-none" /><div className="mt-3 grid gap-3 sm:grid-cols-2"><select value={extractionKind} onChange={(event) => setExtractionKind(event.target.value)} className="rounded-xl border border-white/10 bg-white/[0.04] px-3 py-3 text-sm text-white outline-none"><option value="auto">Auto detect</option><option value="pid">P&ID / blueprint</option><option value="maintenance_log">Maintenance log</option><option value="none">Index only</option></select><input value={zone} onChange={(event) => setZone(event.target.value)} placeholder="Zone, e.g. Zone 3" className="rounded-xl border border-white/10 bg-white/[0.04] px-3 py-3 text-sm text-white outline-none" /></div><button onClick={upload} disabled={!file || uploading || loadingDemo} className="mt-4 inline-flex w-full items-center justify-center gap-2 rounded-xl bg-cyan-300 px-4 py-3 text-sm font-semibold text-slate-950 disabled:cursor-not-allowed disabled:opacity-50"><UploadCloud className="h-4 w-4" />{uploading ? `Uploading ${file?.name || 'document'}...` : file ? `Upload ${file.name}` : 'Choose a file to upload'}</button></div><div className="rounded-2xl border border-white/10 bg-white/[0.03] p-4"><div className="mb-3 text-sm font-semibold text-white">What appears after upload</div>{['Exact filename and document ID','Live processing status','Indexed chunk count','Upload date and time'].map((item)=><div key={item} className="mb-2 flex items-center gap-2 text-xs text-slate-300"><CheckCircle2 className="h-3.5 w-3.5 text-emerald-300" />{item}</div>)}</div></div>
    </section>
    <section className="rounded-3xl border border-white/10 bg-white/[0.04] p-5 shadow-2xl shadow-black/20"><div className="mb-4 flex items-center justify-between"><h3 className="text-lg font-semibold text-white">Uploaded documents</h3><span className="rounded-full border border-white/10 px-3 py-1 text-xs text-slate-300">{documents.length} visible</span></div>{loading ? <div className="p-8 text-center text-slate-400">Loading documents...</div> : documents.length === 0 ? <div className="p-8 text-center text-slate-400">No documents yet. Select a file or load the demo PDF.</div> : <div className="overflow-x-auto rounded-2xl border border-white/10"><table className="min-w-[760px] w-full text-left text-sm"><thead className="bg-white/[0.04] text-xs uppercase text-slate-500"><tr><th className="px-4 py-3">Uploaded file</th><th className="px-4 py-3">Status</th><th className="px-4 py-3">Chunks</th><th className="px-4 py-3">Uploaded</th><th className="px-4 py-3">Document ID</th></tr></thead><tbody>{documents.map((document)=><tr key={documentId(document) || document.filename} className="border-t border-white/10"><td className="px-4 py-3 font-medium text-white"><FileText className="mr-2 inline h-4 w-4 text-cyan-300" />{document.original_filename || document.filename || 'Untitled'}</td><td className="px-4 py-3"><span className={`rounded-full border px-2 py-1 text-xs ${String(document.status).toLowerCase()==='completed'?'border-emerald-400/20 bg-emerald-400/10 text-emerald-100':'border-cyan-400/20 bg-cyan-400/10 text-cyan-100'}`}>{document.status || 'unknown'}</span></td><td className="px-4 py-3 text-slate-300">{chunks(document)}</td><td className="px-4 py-3 text-slate-400">{document.uploaded_at ? new Date(document.uploaded_at).toLocaleString() : '-'}</td><td className="max-w-48 truncate px-4 py-3 font-mono text-xs text-slate-500" title={documentId(document)}>{documentId(document) || '-'}</td></tr>)}</tbody></table></div>}</section>
  </div>;
}


