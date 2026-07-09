'use client';

import { ClipboardCheck, FileText, RefreshCw } from 'lucide-react';
import { useEffect, useMemo, useState } from 'react';
import { checkCompliance, listComplianceRules, listDocuments } from '@/lib/plantbrain-api';
import type { ComplianceResult, ComplianceRule, DocumentItem } from '@/types/plantbrain';

function docId(document: DocumentItem) { return String(document.document_id || document.id || ''); }
function docName(document: DocumentItem) { return String(document.original_filename || document.filename || docId(document) || 'Uploaded document'); }
function statusTone(status?: string) { const value = String(status || '').toLowerCase(); if (value.includes('non')) return 'border-red-400/20 bg-red-400/10 text-red-100'; if (value.includes('partial') || value.includes('warning')) return 'border-amber-400/20 bg-amber-400/10 text-amber-100'; return 'border-emerald-400/20 bg-emerald-400/10 text-emerald-100'; }
function documentTone(status?: string) { const value = String(status || '').toLowerCase(); if (value.includes('failed')) return 'border-red-400/20 bg-red-400/10 text-red-100'; if (value.includes('completed')) return 'border-emerald-400/20 bg-emerald-400/10 text-emerald-100'; return 'border-amber-400/20 bg-amber-400/10 text-amber-100'; }

export function CompliancePanel({ onComplete }: { onComplete: () => void }) {
  const [rules, setRules] = useState<ComplianceRule[]>([]);
  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [documentId, setDocumentId] = useState('');
  const [procedureText, setProcedureText] = useState('');
  const [ruleCodes, setRuleCodes] = useState('');
  const [results, setResults] = useState<ComplianceResult[]>([]);
  const [loadingRules, setLoadingRules] = useState(false);
  const [loadingDocuments, setLoadingDocuments] = useState(false);
  const [checking, setChecking] = useState(false);
  const [error, setError] = useState('');

  const refreshDocuments = async () => {
    setLoadingDocuments(true);
    try {
      const docsResponse = await listDocuments(0, 100);
      const nextDocuments = docsResponse.documents || [];
      setDocuments(nextDocuments);
      setDocumentId((current) => current || docId(nextDocuments.find((doc) => String(doc.status).toLowerCase() === 'completed') || nextDocuments[0] || {} as DocumentItem));
    } catch (err: any) {
      setError(err?.status ? `${err.message} (HTTP ${err.status})` : err?.message || 'Failed to load uploaded documents.');
    } finally {
      setLoadingDocuments(false);
    }
  };

  const refreshRules = async () => {
    setLoadingRules(true);
    try {
      const rulesResponse = await listComplianceRules();
      setRules((rulesResponse.rules || []) as ComplianceRule[]);
    } catch (err: any) {
      setError(err?.status ? `${err.message} (HTTP ${err.status})` : err?.message || 'Failed to load compliance rules.');
    } finally {
      setLoadingRules(false);
    }
  };

  const refresh = () => {
    setError('');
    void refreshDocuments();
    void refreshRules();
  };

  useEffect(() => { refresh(); }, []);

  const selectedDocument = documents.find((document) => docId(document) === documentId);

  const runCheck = async () => {
    if (!documentId && !procedureText.trim()) { setError('Select a document or paste procedure text.'); return; }
    setChecking(true); setError('');
    try {
      const response = await checkCompliance({ document_id: documentId, procedure_text: procedureText, rule_codes: ruleCodes.split(',').map((code) => code.trim()).filter(Boolean) });
      const next = (response.results || []) as ComplianceResult[];
      setResults(next); onComplete();
    } catch (err: any) { setError(err?.status ? `${err.message} (HTTP ${err.status})` : err?.message || 'Compliance check failed.'); }
    finally { setChecking(false); }
  };

  const grouped = useMemo(() => ({ compliant: results.filter((r) => String(r.status).toLowerCase().includes('compliant') && !String(r.status).toLowerCase().includes('non')).length, partial: results.filter((r) => String(r.status).toLowerCase().includes('partial')).length, non: results.filter((r) => String(r.status).toLowerCase().includes('non')).length }), [results]);

  return <div className="space-y-5"><section className="rounded-3xl border border-white/10 bg-white/[0.04] p-5 shadow-2xl shadow-black/20"><div className="mb-5 flex flex-col gap-3 md:flex-row md:items-start md:justify-between"><div><div className="text-xs font-semibold uppercase tracking-[0.2em] text-cyan-300">Step 04 - Compliance stays current</div><h2 className="mt-2 text-2xl font-semibold text-white">Run real compliance checks</h2><p className="mt-2 max-w-3xl text-sm leading-6 text-slate-400">PlantBrain checks whether procedures align with OISD, Factory Act, and PESO rules and surfaces gaps before audits.</p></div><button onClick={refresh} className="inline-flex items-center gap-2 rounded-xl border border-white/10 px-3 py-2 text-sm text-slate-200 hover:border-cyan-400/50"><RefreshCw className="h-4 w-4" /> Refresh</button></div>{error && <div className="mb-4 rounded-xl border border-red-400/20 bg-red-400/10 p-3 text-sm text-red-100">{error}</div>}<div className="grid gap-4 lg:grid-cols-2"><div className="space-y-3 rounded-2xl border border-white/10 bg-[#090f18] p-4"><select value={documentId} onChange={(event) => setDocumentId(event.target.value)} className="w-full rounded-xl border border-white/10 bg-white/[0.04] px-3 py-3 text-sm text-white"><option value="">No document selected - use pasted text</option>{documents.map((document) => <option key={docId(document)} value={docId(document)}>{docName(document)}</option>)}</select><div className="rounded-2xl border border-white/10 bg-white/[0.03] p-3"><div className="mb-2 flex items-center justify-between gap-2 text-xs font-semibold uppercase tracking-[0.14em] text-slate-400"><span>Uploaded documents</span>{loadingDocuments && <span className="text-cyan-200">Loading...</span>}</div>{documents.length === 0 ? <div className="rounded-xl border border-amber-300/20 bg-amber-400/10 p-3 text-sm leading-6 text-amber-100">No uploaded documents found yet. Upload or load a demo PDF in Step 01, then refresh compliance.</div> : <div className="max-h-44 space-y-2 overflow-y-auto pr-1">{documents.map((document) => { const id = docId(document); const selected = id === documentId; return <button key={id} onClick={() => setDocumentId(id)} className={`flex w-full items-center justify-between gap-3 rounded-xl border p-3 text-left text-sm transition ${selected ? 'border-cyan-300/60 bg-cyan-300/10 text-white' : 'border-white/10 bg-black/10 text-slate-200 hover:border-cyan-400/40'}`}><span className="min-w-0"><span className="block truncate font-semibold"><FileText className="mr-2 inline h-4 w-4 text-cyan-300" />{docName(document)}</span><span className="mt-1 block text-xs text-slate-500">{document.total_chunks || 0} chunks indexed</span></span><span className={`shrink-0 rounded-full border px-2 py-1 text-[10px] font-bold uppercase ${documentTone(document.status)}`}>{document.status || 'unknown'}</span></button>; })}</div>}</div>{selectedDocument && <div className="rounded-xl border border-emerald-400/20 bg-emerald-400/10 p-3 text-sm text-emerald-100">Selected: {docName(selectedDocument)}</div>}<textarea value={procedureText} onChange={(event) => setProcedureText(event.target.value)} placeholder="Optional: paste procedure text instead of using the selected uploaded document..." className="min-h-32 w-full resize-none rounded-xl border border-white/10 bg-white/[0.04] p-3 text-sm leading-6 text-white outline-none placeholder:text-slate-600" /><input value={ruleCodes} onChange={(event) => setRuleCodes(event.target.value)} placeholder="Optional rule codes, comma separated: OISD-116-3.2, PESO-2016-5.3" className="w-full rounded-xl border border-white/10 bg-white/[0.04] px-3 py-3 text-sm text-white outline-none placeholder:text-slate-600" /><button onClick={runCheck} disabled={checking || loadingDocuments || loadingRules} className="inline-flex w-full items-center justify-center gap-2 rounded-xl bg-cyan-300 px-4 py-3 text-sm font-semibold text-slate-950 hover:bg-cyan-200 disabled:opacity-50"><ClipboardCheck className="h-4 w-4" /> {checking ? 'Checking...' : 'Run Compliance Check'}</button></div><div className="rounded-2xl border border-white/10 bg-white/[0.03] p-4"><div className="mb-3 text-sm font-semibold text-white">Compliance rules</div>{loadingRules ? <div className="text-sm text-slate-400">Loading rules...</div> : rules.length === 0 ? <div className="text-sm leading-6 text-slate-400">No compliance rules found. The backend should seed built-in rules automatically; refresh once after deploy.</div> : <div className="max-h-72 space-y-2 overflow-auto">{rules.map((rule) => <button key={rule.id || rule.rule_code} onClick={() => setRuleCodes((current) => current ? current : String(rule.rule_code || ''))} className="w-full rounded-xl border border-white/10 bg-white/[0.03] p-3 text-left transition hover:border-cyan-400/40"><div className="font-mono text-xs text-cyan-200">{rule.rule_code}</div><div className="mt-1 text-sm text-white">{rule.title}</div><div className="mt-1 text-xs text-slate-500">{rule.regulation_body} · {rule.category}</div></button>)}</div>}</div></div></section><section className="rounded-3xl border border-white/10 bg-white/[0.04] p-5"><div className="mb-4 grid gap-3 md:grid-cols-3"><Metric label="Compliant" value={grouped.compliant} tone="emerald" /><Metric label="Partial" value={grouped.partial} tone="amber" /><Metric label="Non-compliant" value={grouped.non} tone="red" /></div>{results.length === 0 ? <div className="rounded-2xl border border-white/10 bg-white/[0.03] p-8 text-center text-slate-400">Run a check to see backend compliance findings.</div> : <div className="grid gap-3">{results.map((result, index) => <div key={`${result.rule_code}-${index}`} className="rounded-2xl border border-white/10 bg-white/[0.03] p-4"><div className="flex flex-wrap items-start justify-between gap-3"><div><div className="font-mono text-sm text-cyan-200">{result.rule_code}</div><div className="mt-1 text-white">{result.rule_title}</div></div><span className={`rounded-full border px-3 py-1 text-xs font-semibold ${statusTone(result.status)}`}>{result.status || 'UNKNOWN'}</span></div><p className="mt-3 text-sm leading-6 text-slate-300">{result.findings || 'No findings text returned.'}</p>{result.recommendation && <p className="mt-2 text-sm leading-6 text-emerald-100">Recommendation: {result.recommendation}</p>}</div>)}</div>}</section></div>;
}
function Metric({ label, value, tone }: { label: string; value: number; tone: 'emerald' | 'amber' | 'red' }) { const map = { emerald: 'border-emerald-400/20 bg-emerald-400/10 text-emerald-100', amber: 'border-amber-400/20 bg-amber-400/10 text-amber-100', red: 'border-red-400/20 bg-red-400/10 text-red-100' }; return <div className={`rounded-2xl border p-4 ${map[tone]}`}><div className="text-xs uppercase tracking-wide opacity-70">{label}</div><div className="mt-2 text-2xl font-semibold">{value}</div></div>; }