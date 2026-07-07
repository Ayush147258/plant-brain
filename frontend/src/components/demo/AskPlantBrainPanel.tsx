'use client';

import { History, Send } from 'lucide-react';
import { useEffect, useState } from 'react';
import { askQuestion, getQueryHistory } from '@/lib/plantbrain-api';
import type { AskResponse, QueryHistoryItem } from '@/types/plantbrain';
import { ConfidenceBadge } from './ConfidenceBadge';
import { SourceCitations } from './SourceCitations';

const chips = [
  'When can tagout devices be used instead of lockout devices?',
  'How often must energy-control procedures be inspected?',
  'What training must authorized employees receive?',
  'What must happen during a shift change?',
  'ठेकेदारों के साथ lockout/tagout की क्या requirements हैं?',
];

export function AskPlantBrainPanel({ onComplete }: { onComplete: () => void }) {
  const [question, setQuestion] = useState('');
  const [language, setLanguage] = useState('auto');
  const [topK, setTopK] = useState(5);
  const [includeGraph, setIncludeGraph] = useState(true);
  const [response, setResponse] = useState<AskResponse | null>(null);
  const [history, setHistory] = useState<QueryHistoryItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const sessionId = 'judge-demo-session';

  const refreshHistory = async () => {
    try { setHistory((await getQueryHistory(sessionId, 10)).queries || []); } catch { setHistory([]); }
  };

  useEffect(() => { refreshHistory(); }, []);

  const ask = async (text = question) => {
    const trimmed = text.trim();
    if (!trimmed) return;
    setLoading(true);
    setError('');
    try {
      const result = await askQuestion({ question: trimmed, language, top_k: topK, session_id: sessionId, include_graph_context: includeGraph });
      setResponse(result);
      setQuestion(trimmed);
      onComplete();
      refreshHistory();
    } catch (err: any) {
      setError(err?.status ? `${err.message} (HTTP ${err.status})` : err?.message || 'Question failed.');
    } finally {
      setLoading(false);
    }
  };

  const answer = response?.answer || response?.response || '';
  const sources = response?.sources || response?.citations || [];

  return <div className="space-y-5"><section className="rounded-3xl border border-white/10 bg-white/[0.04] p-5 shadow-2xl shadow-black/20"><div className="text-xs font-semibold uppercase tracking-[0.2em] text-cyan-300">Step 03 - Your team just asks</div><h2 className="mt-2 text-2xl font-semibold text-white">Ask PlantBrain with citations</h2><p className="mt-2 max-w-3xl text-sm leading-6 text-slate-400">Ask in English or Hindi. PlantBrain should answer using uploaded documents, source citations, confidence levels, and graph context.</p>{error && <div className="mt-4 rounded-xl border border-red-400/20 bg-red-400/10 p-3 text-sm text-red-100">{error}</div>}<div className="mt-5 rounded-2xl border border-white/10 bg-[#090f18] p-4"><textarea value={question} onChange={(event) => setQuestion(event.target.value)} placeholder="Ask a real question against uploaded documents..." className="min-h-28 w-full resize-none bg-transparent text-sm leading-6 text-white outline-none placeholder:text-slate-600" /><div className="mt-3 flex flex-wrap items-center gap-3 border-t border-white/10 pt-3"><select value={language} onChange={(event) => setLanguage(event.target.value)} className="rounded-lg border border-white/10 bg-white/[0.04] px-3 py-2 text-sm text-white"><option value="auto">Auto</option><option value="en">English</option><option value="hi">Hindi</option></select><select value={topK} onChange={(event) => setTopK(Number(event.target.value))} className="rounded-lg border border-white/10 bg-white/[0.04] px-3 py-2 text-sm text-white">{[3,5,8,10].map((value) => <option key={value} value={value}>Top {value}</option>)}</select><label className="flex items-center gap-2 text-sm text-slate-300"><input type="checkbox" checked={includeGraph} onChange={(event) => setIncludeGraph(event.target.checked)} /> Include graph context</label><button onClick={() => ask()} disabled={loading || !question.trim()} className="ml-auto inline-flex items-center gap-2 rounded-xl bg-cyan-300 px-4 py-2 text-sm font-semibold text-slate-950 hover:bg-cyan-200 disabled:opacity-50"><Send className="h-4 w-4" /> {loading ? 'Asking...' : 'Ask'}</button></div></div><div className="mt-4 flex flex-wrap gap-2">{chips.map((chip) => <button key={chip} onClick={() => ask(chip)} className="rounded-full border border-white/10 bg-white/[0.03] px-3 py-2 text-xs text-slate-300 hover:border-cyan-400/50 hover:text-white">{chip}</button>)}</div></section>{response && <section className="rounded-3xl border border-white/10 bg-white/[0.04] p-5"><div className="mb-3 flex items-center justify-between"><h3 className="text-lg font-semibold text-white">Backend answer</h3><ConfidenceBadge confidence={response.confidence} /></div><div className="rounded-2xl border border-cyan-400/20 bg-cyan-400/10 p-4 text-sm leading-7 text-cyan-50 whitespace-pre-wrap">{answer || 'Backend returned no answer text.'}</div>{response.equipment_mentioned && response.equipment_mentioned.length > 0 && <div className="mt-3 flex flex-wrap gap-2">{response.equipment_mentioned.map((tag) => <span key={tag} className="rounded-full border border-emerald-400/20 bg-emerald-400/10 px-2 py-1 text-xs text-emerald-100">{tag}</span>)}</div>}<div className="mt-4"><SourceCitations sources={sources} /></div></section>}<section className="rounded-3xl border border-white/10 bg-white/[0.04] p-5"><h3 className="mb-3 flex items-center gap-2 text-lg font-semibold text-white"><History className="h-5 w-5 text-cyan-300" /> Query history</h3>{history.length === 0 ? <div className="rounded-2xl border border-white/10 bg-white/[0.03] p-6 text-sm text-slate-400">No backend history for this session yet.</div> : <div className="space-y-2">{history.map((item) => <button key={item.id || item.question} onClick={() => item.question && ask(item.question)} className="w-full rounded-xl border border-white/10 bg-white/[0.03] p-3 text-left text-sm text-slate-300 hover:border-cyan-400/40"><span className="text-white">{item.question}</span></button>)}</div>}</section></div>;
}