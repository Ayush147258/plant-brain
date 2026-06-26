'use client';

import { Mic2, Send, UploadCloud } from 'lucide-react';
import { useState } from 'react';
import { transcribeVoice } from '@/lib/plantbrain-api';
import type { VoiceResponse } from '@/types/plantbrain';

export function ExpertCapturePanel({ onComplete, onAskAboutNote }: { onComplete: () => void; onAskAboutNote: () => void }) {
  const [file, setFile] = useState<File | null>(null);
  const [language, setLanguage] = useState('');
  const [note, setNote] = useState('');
  const [result, setResult] = useState<VoiceResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const transcribe = async () => {
    if (!file) { setError('Choose an audio file first.'); return; }
    setLoading(true); setError('');
    try { const response = await transcribeVoice(file, language); setResult(response); onComplete(); }
    catch (err: any) { setError(err?.status ? `${err.message} (HTTP ${err.status})` : err?.message || 'Voice transcription failed.'); }
    finally { setLoading(false); }
  };
  const text = result?.text || result?.transcript || note;

  return <div className="space-y-5"><section className="rounded-3xl border border-white/10 bg-white/[0.04] p-5 shadow-2xl shadow-black/20"><div className="text-xs font-semibold uppercase tracking-[0.2em] text-cyan-300">Step 05 - Capture expert knowledge</div><h2 className="mt-2 text-2xl font-semibold text-white">Upload a real technician voice note</h2><p className="mt-2 max-w-3xl text-sm leading-6 text-slate-400">Field technicians can speak into their phone. PlantBrain transcribes the note and links knowledge to the right equipment and procedures.</p>{error && <div className="mt-4 rounded-xl border border-red-400/20 bg-red-400/10 p-3 text-sm text-red-100">{error}</div>}<div className="mt-5 grid gap-4 lg:grid-cols-[1fr_320px]"><div className="rounded-2xl border border-dashed border-cyan-400/30 bg-cyan-400/5 p-5"><label className="flex cursor-pointer flex-col items-center justify-center gap-3 rounded-xl border border-white/10 bg-[#090f18] p-8 text-center hover:border-cyan-400/50"><Mic2 className="h-10 w-10 text-cyan-300" /><span className="text-sm font-semibold text-white">{file ? file.name : 'Choose MP3, WAV, M4A, or WEBM'}</span><input className="hidden" type="file" accept=".mp3,.wav,.m4a,.webm,audio/*" onChange={(event) => setFile(event.target.files?.[0] || null)} /></label><select value={language} onChange={(event) => setLanguage(event.target.value)} className="mt-4 w-full rounded-xl border border-white/10 bg-white/[0.04] px-3 py-3 text-sm text-white"><option value="">Auto language</option><option value="en">English</option><option value="hi">Hindi</option></select><button onClick={transcribe} disabled={loading || !file} className="mt-4 inline-flex w-full items-center justify-center gap-2 rounded-xl bg-cyan-300 px-4 py-3 text-sm font-semibold text-slate-950 hover:bg-cyan-200 disabled:opacity-50"><UploadCloud className="h-4 w-4" /> {loading ? 'Transcribing...' : 'Transcribe Voice Note'}</button></div><div className="rounded-2xl border border-white/10 bg-white/[0.03] p-4"><div className="mb-2 text-sm font-semibold text-white">Text fallback mode</div><p className="mb-3 text-xs leading-5 text-slate-500">Use this only if audio upload is difficult. It is marked as text mode and does not pretend to be voice transcription.</p><textarea value={note} onChange={(event) => { setNote(event.target.value); if (event.target.value.trim()) onComplete(); }} placeholder="Paste technician note..." className="min-h-40 w-full resize-none rounded-xl border border-white/10 bg-white/[0.04] p-3 text-sm leading-6 text-white outline-none placeholder:text-slate-600" /></div></div></section><section className="rounded-3xl border border-white/10 bg-white/[0.04] p-5"><h3 className="mb-4 text-lg font-semibold text-white">Transcript and extracted knowledge</h3>{!text ? <div className="rounded-2xl border border-white/10 bg-white/[0.03] p-8 text-center text-slate-400">Upload audio or paste a technician note to continue.</div> : <div className="space-y-4"><div className="rounded-2xl border border-cyan-400/20 bg-cyan-400/10 p-4 text-sm leading-7 text-cyan-50 whitespace-pre-wrap">{text}</div>{result?.equipment_tags_found && <div className="flex flex-wrap gap-2">{result.equipment_tags_found.map((tag) => <span key={tag} className="rounded-full border border-emerald-400/20 bg-emerald-400/10 px-3 py-1 text-xs text-emerald-100">{tag}</span>)}</div>}<pre className="max-h-72 overflow-auto rounded-2xl border border-white/10 bg-[#060910] p-4 text-xs leading-6 text-slate-300">{JSON.stringify(result?.knowledge_extracted || result || { mode: 'text', note }, null, 2)}</pre><button onClick={onAskAboutNote} className="inline-flex items-center gap-2 rounded-xl border border-white/10 px-4 py-2 text-sm text-slate-200 hover:border-cyan-400/50"><Send className="h-4 w-4" /> Ask PlantBrain about this note</button></div>}</section></div>;
}