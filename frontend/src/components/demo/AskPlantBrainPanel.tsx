'use client';

import { AlertTriangle, Bot, CheckCircle2, FileText, GitFork, History, LockKeyhole, Mic2, Network, Radio, Send, ShieldCheck, Sparkles, User, Volume2 } from 'lucide-react';
import { useEffect, useMemo, useRef, useState } from 'react';
import { askQuestion, getQueryHistory } from '@/lib/plantbrain-api';
import type { AskResponse, QueryHistoryItem, SourceItem } from '@/types/plantbrain';
import { ConfidenceBadge } from './ConfidenceBadge';
import { SourceCitations } from './SourceCitations';

type BotState = 'idle' | 'listening' | 'thinking' | 'answering' | 'blocked';
type ChatRole = 'assistant' | 'user' | 'system';

type OperationalCard = {
  id: string;
  title: string;
  status: string;
  tone: 'cyan' | 'emerald' | 'amber' | 'red' | 'violet';
  icon: React.ComponentType<{ className?: string }>;
  rows: Array<{ label: string; value: string }>;
  caveat?: string;
};

type ChatMessage = {
  id: string;
  role: ChatRole;
  text: string;
  response?: AskResponse;
  sources?: SourceItem[];
  cards?: OperationalCard[];
  timestamp: string;
};

const chips = [
  'Generate a safe work pack for pump P-201 lockout.',
  'Show equipment connected to P-201 and cite the source.',
  'Check if this procedure has stale or low-confidence sources.',
  'What must happen during a shift change?',
  'What training must authorized employees receive?',
];

const actions = [
  { label: 'Generate work pack', prompt: 'Generate a source-cited work pack for the most relevant equipment in the uploaded documents.', icon: FileText },
  { label: 'Show graph path', prompt: 'Show the equipment graph path and connected assets mentioned in the uploaded documents.', icon: GitFork },
  { label: 'Check compliance', prompt: 'Check compliance caveats and cite rules from the uploaded documents.', icon: ShieldCheck },
  { label: 'Find stale sources', prompt: 'Identify stale, low-confidence, or missing-source information before answering.', icon: AlertTriangle },
];

const welcomeMessage: ChatMessage = {
  id: 'welcome',
  role: 'assistant',
  text: 'I am ready. Ask about a procedure, graph path, compliance rule, stale source, or equipment risk. I will only create operational cards when the backend returns evidence.',
  timestamp: 'Ready',
};

export function AskPlantBrainPanel({ onComplete }: { onComplete: () => void }) {
  const [draft, setDraft] = useState('');
  const [language, setLanguage] = useState('auto');
  const [topK, setTopK] = useState(5);
  const [includeGraph, setIncludeGraph] = useState(true);
  const [messages, setMessages] = useState<ChatMessage[]>([welcomeMessage]);
  const [history, setHistory] = useState<QueryHistoryItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [botState, setBotState] = useState<BotState>('idle');
  const sessionId = 'judge-demo-session';
  const scrollRef = useRef<HTMLDivElement | null>(null);

  const latestAssistant = useMemo(() => [...messages].reverse().find((message) => message.role === 'assistant' && message.response), [messages]);

  const refreshHistory = async () => {
    try {
      setHistory((await getQueryHistory(sessionId, 10)).queries || []);
    } catch {
      setHistory([]);
    }
  };

  useEffect(() => { refreshHistory(); }, []);
  useEffect(() => { scrollRef.current?.scrollIntoView({ behavior: 'smooth', block: 'end' }); }, [messages, loading]);

  const send = async (text = draft) => {
    const trimmed = text.trim();
    if (!trimmed || loading) return;

    const userMessage: ChatMessage = {
      id: `user-${Date.now()}`,
      role: 'user',
      text: trimmed,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    };
    setMessages((current) => [...current, userMessage]);
    setDraft('');
    setLoading(true);
    setBotState('thinking');

    try {
      const result = await askQuestion({ question: trimmed, language, top_k: topK, session_id: sessionId, include_graph_context: includeGraph });
      const answer = result.answer || result.response || '';
      const sources = result.sources || result.citations || [];
      const assistantMessage: ChatMessage = {
        id: `assistant-${Date.now()}`,
        role: 'assistant',
        text: answer || 'The backend responded, but no answer text was returned. Treat this as insufficient evidence.',
        response: result,
        sources,
        cards: buildOperationalCards(result, answer, sources),
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      };
      setMessages((current) => [...current, assistantMessage]);
      setBotState('answering');
      onComplete();
      refreshHistory();
    } catch (err: any) {
      const message = err?.status ? `${err.message} (HTTP ${err.status})` : err?.message || 'Question failed.';
      setMessages((current) => [...current, {
        id: `error-${Date.now()}`,
        role: 'system',
        text: `Backend unavailable: ${message}. I will not create operational cards without source evidence.`,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      }]);
      setBotState('blocked');
    } finally {
      setLoading(false);
    }
  };

  const clearChat = () => {
    setMessages([welcomeMessage]);
    setBotState('idle');
  };

  return (
    <div className="space-y-5">
      <div className="grid gap-5 xl:grid-cols-[280px_minmax(0,1fr)]">
        <aside className="space-y-4">
        <section className="overflow-hidden rounded-3xl border border-violet-300/20 bg-[radial-gradient(circle_at_80%_0%,rgba(139,92,246,0.32),transparent_32%),linear-gradient(145deg,rgba(248,250,252,0.10),rgba(15,23,42,0.88))] p-5 shadow-2xl shadow-black/30">
          <div className="mb-4 flex items-center justify-between gap-3">
            <div>
              <div className="text-xs font-semibold uppercase tracking-[0.2em] text-violet-200">Live PlantBrain Bot</div>
              <h2 className="mt-2 text-xl font-semibold text-white">Chat, verify, act.</h2>
            </div>
            <StatePill state={botState} loading={loading} />
          </div>
          <div className="relative min-h-[250px] rounded-3xl border border-white/10 bg-[#f4f0ff] p-5 text-slate-950 shadow-inner shadow-white/40">
            <div className="pointer-events-none absolute -left-10 -top-10 h-32 w-32 rounded-full bg-violet-300/30" />
            <div className="pointer-events-none absolute right-7 top-7 h-3 w-3 rounded-full bg-violet-500/60" />
            <div className="relative z-10 flex items-start justify-between gap-3">
              <div className="min-w-0">
                <div className="text-xs font-black uppercase tracking-[0.18em] text-violet-700">Meet</div>
                <div className="mt-1 font-black tracking-tight"><span className="block text-3xl leading-none text-slate-950">PlantBrain</span><span className="block bg-gradient-to-r from-violet-700 to-indigo-700 bg-clip-text text-5xl leading-none text-transparent">BOT</span></div>
                <p className="mt-3 max-w-[180px] text-xs font-medium leading-5 text-slate-600">A working chat layer over citations, graph context, confidence, and freshness checks.</p>
              </div>
              <RobotAvatar state={botState} />
            </div>
            <div className="relative z-10 mt-4 rounded-2xl bg-white p-3 shadow-lg ring-1 ring-violet-100">
              <div className="mb-2 flex items-center gap-2 text-[11px] font-bold uppercase tracking-[0.16em] text-violet-700"><Bot className="h-3.5 w-3.5" /> Bot state</div>
              <div className="text-sm font-medium leading-6 text-slate-700">{botMessage(botState, latestAssistant !== undefined)}</div>
              {(loading || botState === 'answering') && <TypingDots />}
            </div>
          </div>
        </section>

        <section className="rounded-3xl border border-white/10 bg-white/[0.04] p-4">
          <div className="mb-3 text-sm font-semibold text-white">Bot actions</div>
          <div className="grid grid-cols-2 gap-2">
            {actions.map(({ label, prompt, icon: Icon }) => (
              <button key={label} onClick={() => send(prompt)} disabled={loading} className="flex min-h-[70px] flex-col items-center justify-center rounded-2xl border border-white/10 bg-white/[0.03] p-2 text-center text-xs font-semibold text-slate-200 transition hover:border-violet-300/50 hover:bg-violet-400/10 disabled:opacity-60">
                <Icon className="mb-2 h-5 w-5 text-violet-200" />{label}
              </button>
            ))}
          </div>
        </section>

        <section className="rounded-3xl border border-white/10 bg-white/[0.04] p-4">
          <h3 className="mb-3 flex items-center gap-2 text-sm font-semibold text-white"><History className="h-4 w-4 text-cyan-300" /> Recent backend history</h3>
          {history.length === 0 ? <div className="rounded-2xl border border-white/10 bg-white/[0.03] p-4 text-xs text-slate-400">No backend history for this session yet.</div> : <div className="space-y-2">{history.slice(0, 4).map((item) => <button key={item.id || item.question} onClick={() => item.question && send(item.question)} className="w-full rounded-xl border border-white/10 bg-white/[0.03] p-3 text-left text-xs text-slate-300 hover:border-cyan-400/40"><span className="line-clamp-2 text-white">{item.question}</span></button>)}</div>}
        </section>
      </aside>

      <section className="flex min-h-[660px] flex-col overflow-hidden rounded-3xl border border-white/10 bg-[#090f18] shadow-2xl shadow-black/30">
        <header className="border-b border-white/10 bg-white/[0.04] p-5">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <div className="text-xs font-semibold uppercase tracking-[0.2em] text-cyan-300">Working chat panel</div>
              <h2 className="mt-2 text-2xl font-semibold text-white">Ask PlantBrain with citations</h2>
              <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-400">Every assistant response can generate cards, but cards stay tied to backend evidence, confidence, equipment tags, and source citations.</p>
            </div>
            <button type="button" onClick={() => setBotState((state) => state === 'listening' ? 'idle' : 'listening')} className="inline-flex items-center gap-2 rounded-full border border-violet-300/30 bg-violet-400/10 px-4 py-2 text-sm font-semibold text-violet-100 hover:border-violet-200/60"><Mic2 className="h-4 w-4" /> {botState === 'listening' ? 'Listening...' : 'Voice mode'}</button>
          </div>
        </header>

        <div className="flex-1 space-y-5 overflow-y-auto p-5">
          {messages.map((message) => <ChatBubble key={message.id} message={message} />)}
          {loading && <div className="flex items-start gap-3"><Avatar role="assistant" /><div className="rounded-3xl rounded-tl-md border border-violet-300/20 bg-violet-400/10 p-4 text-sm text-violet-50"><div className="font-semibold text-white">PlantBrain is checking evidence</div><div className="mt-1 text-violet-100/80">Retrieving citations, graph context, confidence, and freshness signals.</div><TypingDots /></div></div>}
          <div ref={scrollRef} />
        </div>

        <footer className="border-t border-white/10 bg-[#0b101a] p-4">
          <div className="mb-3 flex flex-wrap gap-2">{chips.map((chip) => <button key={chip} onClick={() => send(chip)} disabled={loading} className="rounded-full border border-white/10 bg-white/[0.03] px-3 py-2 text-xs text-slate-300 hover:border-cyan-400/50 hover:text-white disabled:opacity-60">{chip}</button>)}</div>
          <div className="rounded-2xl border border-white/10 bg-white/[0.04] p-3">
            <textarea value={draft} onChange={(event) => setDraft(event.target.value)} onKeyDown={(event) => { if (event.key === 'Enter' && !event.shiftKey) { event.preventDefault(); send(); } }} placeholder="Ask a real plant question. Press Enter to send, Shift+Enter for a new line." className="min-h-20 w-full resize-none bg-transparent text-sm leading-6 text-white outline-none placeholder:text-slate-600" />
            <div className="mt-3 flex flex-wrap items-center gap-3 border-t border-white/10 pt-3">
              <select value={language} onChange={(event) => setLanguage(event.target.value)} className="rounded-lg border border-white/10 bg-[#111827] px-3 py-2 text-sm text-white"><option value="auto">Auto</option><option value="en">English</option><option value="hi">Hindi</option></select>
              <select value={topK} onChange={(event) => setTopK(Number(event.target.value))} className="rounded-lg border border-white/10 bg-[#111827] px-3 py-2 text-sm text-white">{[3, 5, 8, 10].map((value) => <option key={value} value={value}>Top {value}</option>)}</select>
              <label className="flex items-center gap-2 text-sm text-slate-300"><input type="checkbox" checked={includeGraph} onChange={(event) => setIncludeGraph(event.target.checked)} /> Include graph context</label>
              <button type="button" onClick={clearChat} className="rounded-lg border border-white/10 px-3 py-2 text-sm text-slate-300 hover:border-white/30 hover:text-white">Clear</button>
              <button onClick={() => send()} disabled={loading || !draft.trim()} className="ml-auto inline-flex items-center gap-2 rounded-xl bg-cyan-300 px-4 py-2 text-sm font-semibold text-slate-950 hover:bg-cyan-200 disabled:opacity-50"><Send className="h-4 w-4" /> {loading ? 'Sending...' : 'Send'}</button>
            </div>
          </div>
        </footer>
      </section>
      </div>

      <EvidenceWorkspace message={latestAssistant} />
    </div>
  );
}

function ChatBubble({ message }: { message: ChatMessage }) {
  const isUser = message.role === 'user';
  const isSystem = message.role === 'system';
  return (
    <div className={`flex items-start gap-3 ${isUser ? 'justify-end' : ''}`}>
      {!isUser && <Avatar role={message.role} />}
      <div className={`${isUser ? 'max-w-[min(520px,70%)]' : 'max-w-[min(980px,88%)]'} rounded-3xl p-4 text-sm leading-7 ${isUser ? 'rounded-tr-md bg-cyan-300 text-slate-950' : isSystem ? 'rounded-tl-md border border-red-300/20 bg-red-400/10 text-red-50' : 'rounded-tl-md border border-white/10 bg-white/[0.04] text-slate-100'}`}>
        <div className="mb-2 flex items-center justify-between gap-4 text-xs opacity-80"><span className="font-semibold">{isUser ? 'You' : isSystem ? 'System guardrail' : 'PlantBrain BOT'}</span><span>{message.timestamp}</span></div>
        {message.response ? (
          <div className="min-w-0">
            <div className="max-h-[520px] overflow-y-auto whitespace-pre-wrap pr-2 text-sm leading-7">{message.text}</div>
            <div className="mt-3 flex flex-wrap items-center gap-2">
              <ConfidenceBadge confidence={message.response.confidence} />
              {message.response.response_time_ms && <span className="rounded-full border border-white/10 px-2 py-1 text-xs text-slate-300">{message.response.response_time_ms} ms</span>}
              {message.response.equipment_mentioned?.map((tag) => <span key={tag} className="rounded-full border border-emerald-400/20 bg-emerald-400/10 px-2 py-1 text-xs text-emerald-100">{tag}</span>)}
            </div>
          </div>
        ) : <div className="whitespace-pre-wrap">{message.text}</div>}
      </div>
      {isUser && <Avatar role="user" />}
    </div>
  );
}

function EvidenceWorkspace({ message }: { message?: ChatMessage }) {
  const cards = message?.cards || [];
  const sources = message?.sources || [];

  return (
    <section className="rounded-3xl border border-white/10 bg-[#090f18] p-5 shadow-2xl shadow-black/25">
      <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
        <div>
          <div className="text-xs font-semibold uppercase tracking-[0.2em] text-cyan-300">Operational evidence</div>
          <h3 className="mt-2 text-xl font-semibold text-white">Cards outside the chat panel</h3>
        </div>
        {message?.response ? <ConfidenceBadge confidence={message.response.confidence} /> : <span className="rounded-full border border-white/10 px-3 py-1.5 text-xs font-semibold text-slate-400">Waiting for backend answer</span>}
      </div>

      {message?.response ? (
        <div className="grid gap-4 2xl:grid-cols-[minmax(0,1fr)_minmax(360px,0.55fr)]">
          <div className="grid gap-3 lg:grid-cols-3">
            {cards.map((card) => <OperationalCardView key={card.id} card={card} />)}
          </div>
          <div className="min-w-0 rounded-2xl border border-white/10 bg-white/[0.03] p-4">
            <div className="mb-3 flex items-center gap-2 text-sm font-semibold text-white"><FileText className="h-4 w-4 text-cyan-300" /> References</div>
            {sources.length > 0 ? (
              <div className="max-h-[320px] overflow-y-auto pr-1">
                <SourceCitations sources={sources} />
              </div>
            ) : (
              <div className="rounded-xl border border-amber-300/20 bg-amber-400/10 p-3 text-sm leading-6 text-amber-100">No citations were returned by the backend for the latest answer.</div>
            )}
          </div>
        </div>
      ) : (
        <div className="grid gap-3 md:grid-cols-3">
          {['Procedure Summary', 'Graph Context', 'Trust Gate'].map((title) => (
            <div key={title} className="rounded-2xl border border-white/10 bg-white/[0.03] p-4 text-sm text-slate-400">{title} will appear here after a sourced answer.</div>
          ))}
        </div>
      )}
    </section>
  );
}

function Avatar({ role }: { role: ChatRole }) {
  if (role === 'user') return <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-cyan-300 text-slate-950"><User className="h-4 w-4" /></div>;
  if (role === 'system') return <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-red-400/20 text-red-100"><AlertTriangle className="h-4 w-4" /></div>;
  return <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-violet-400/20 text-violet-100"><Bot className="h-4 w-4" /></div>;
}

function StatePill({ state, loading }: { state: BotState; loading: boolean }) {
  const label = loading ? 'Thinking' : state === 'idle' ? 'Ready' : state === 'listening' ? 'Listening' : state === 'answering' ? 'Cards ready' : 'Needs backend';
  const className = state === 'blocked' ? 'border-red-300/30 bg-red-400/10 text-red-100' : state === 'answering' ? 'border-emerald-300/30 bg-emerald-400/10 text-emerald-100' : 'border-violet-300/30 bg-violet-400/10 text-violet-100';
  return <div className={`inline-flex items-center gap-2 rounded-full border px-3 py-1.5 text-xs font-bold ${className}`}><Radio className="h-3.5 w-3.5" /> {label}</div>;
}

function RobotAvatar({ state }: { state: BotState }) {
  const speaking = state === 'thinking' || state === 'answering' || state === 'listening';
  return <div className="relative h-36 w-28 shrink-0"><div className="absolute left-1/2 top-0 h-8 w-3 -translate-x-1/2 rounded-full bg-violet-800" /><div className="absolute left-1/2 top-0 h-5 w-5 -translate-x-1/2 rounded-full bg-gradient-to-br from-violet-400 to-violet-900 shadow-lg" /><div className="absolute left-1/2 top-8 h-20 w-28 -translate-x-1/2 rounded-[2rem] bg-gradient-to-br from-violet-500 to-violet-900 p-2 shadow-xl shadow-violet-900/30"><div className="flex h-full items-center justify-center rounded-[1.45rem] bg-white"><div className="flex items-center gap-5"><span className="h-7 w-4 rounded-full bg-gradient-to-b from-blue-400 to-indigo-700 shadow-inner" /><span className={`${speaking ? 'h-7 w-7' : 'h-3 w-7'} rounded-full border-[5px] border-amber-400 bg-slate-950 transition-all`} /><span className="h-7 w-4 rounded-full bg-gradient-to-b from-blue-400 to-indigo-700 shadow-inner" /></div></div></div><div className="absolute -left-2 top-16 h-10 w-5 rounded-full bg-violet-700" /><div className="absolute -right-2 top-16 h-10 w-5 rounded-full bg-violet-700" /><div className="absolute left-5 top-[108px] h-20 w-20 rounded-[2rem] bg-gradient-to-br from-violet-500 to-violet-900 shadow-xl shadow-violet-900/30"><div className="absolute inset-x-0 top-7 text-center text-sm font-black tracking-wide text-white">PB</div></div><div className="absolute -left-1 top-[118px] h-6 w-10 rotate-[-18deg] rounded-full bg-white shadow" /><div className="absolute right-0 top-[114px] h-6 w-10 rotate-[18deg] rounded-full bg-white shadow" />{state === 'listening' && <div className="absolute -right-2 top-2 flex h-8 w-8 items-center justify-center rounded-full bg-emerald-400 text-slate-950 shadow-lg"><Volume2 className="h-4 w-4" /></div>}</div>;
}

function TypingDots() {
  return <div className="mt-3 flex w-fit rounded-2xl bg-white/90 px-3 py-2 shadow-sm"><span className="h-2 w-2 animate-bounce rounded-full bg-amber-400 [animation-delay:-0.2s]" /><span className="mx-1 h-2 w-2 animate-bounce rounded-full bg-amber-400 [animation-delay:-0.1s]" /><span className="h-2 w-2 animate-bounce rounded-full bg-amber-400" /></div>;
}

function botMessage(state: BotState, hasResponse: boolean) {
  if (state === 'blocked') return 'Backend did not return evidence. I blocked card generation instead of inventing output.';
  if (state === 'listening') return 'Listening mode is ready. Ask for a procedure, graph path, compliance check, or stale-source review.';
  if (state === 'thinking') return 'Checking retrieved sources, graph context, confidence, and freshness before generating cards.';
  if (hasResponse) return 'Latest answer has been converted into source-aware operational cards.';
  return 'Choose an action or ask a question. I will only generate cards from backend evidence.';
}

function buildOperationalCards(response: AskResponse | null, answer: string, sources: SourceItem[]): OperationalCard[] {
  if (!response) return [];
  const confidence = normalizeConfidence(response.confidence);
  const equipment = response.equipment_mentioned || [];
  const source = sources[0];
  const sourceName = sourceLabel(source);
  const hasSources = sources.length > 0;
  const caveat = hasSources ? undefined : 'No source citation returned. Treat as insufficient evidence until documents are indexed.';

  return [
    {
      id: 'procedure',
      title: 'Procedure Summary',
      status: hasSources ? 'Source cited' : 'Evidence missing',
      tone: hasSources ? 'cyan' : 'red',
      icon: FileText,
      rows: [
        { label: 'Primary source', value: sourceName },
        { label: 'Page / chunk', value: source?.page_number ? `Page ${source.page_number}` : source?.chunk_index !== undefined ? `Chunk ${Number(source.chunk_index) + 1}` : 'Not returned' },
        { label: 'Answer length', value: answer ? `${answer.length} chars` : 'No answer text' },
      ],
      caveat,
    },
    {
      id: 'graph',
      title: 'Graph Context',
      status: equipment.length ? `${equipment.length} asset tags` : 'No tags returned',
      tone: equipment.length ? 'emerald' : 'amber',
      icon: Network,
      rows: [
        { label: 'Mentioned equipment', value: equipment.slice(0, 4).join(', ') || 'None returned' },
        { label: 'Graph mode', value: 'Include graph context enabled in request' },
        { label: 'Use', value: 'Trace connected assets before field action' },
      ],
      caveat: equipment.length ? undefined : 'No equipment tags were returned by the backend for this answer.',
    },
    {
      id: 'confidence',
      title: 'Trust Gate',
      status: confidence.label,
      tone: confidence.tone,
      icon: confidence.tone === 'red' ? AlertTriangle : CheckCircle2,
      rows: [
        { label: 'Confidence', value: confidence.label },
        { label: 'Freshness', value: freshnessLabel(source) },
        { label: 'Rule', value: 'Low confidence must be reviewed, not auto-trusted' },
      ],
      caveat: confidence.caveat,
    },
  ];
}

function OperationalCardView({ card, compact = false }: { card: OperationalCard; compact?: boolean }) {
  const tone = {
    cyan: 'border-cyan-300/20 bg-cyan-400/10 text-cyan-100',
    emerald: 'border-emerald-300/20 bg-emerald-400/10 text-emerald-100',
    amber: 'border-amber-300/20 bg-amber-400/10 text-amber-100',
    red: 'border-red-300/20 bg-red-400/10 text-red-100',
    violet: 'border-violet-300/20 bg-violet-400/10 text-violet-100',
  }[card.tone];
  const Icon = card.icon;
  return <article className={`rounded-2xl border ${compact ? "p-3" : "p-4"} ${tone}`}><div className="flex items-start justify-between gap-3"><div className="flex items-center gap-2"><span className="flex h-8 w-8 items-center justify-center rounded-xl bg-white/10"><Icon className="h-4 w-4" /></span><div><h4 className="text-sm font-semibold text-white">{card.title}</h4><p className="text-[11px] opacity-80">{card.status}</p></div></div></div><div className="mt-3 space-y-1.5">{card.rows.map((row) => <div key={row.label} className="flex justify-between gap-3 border-t border-white/10 pt-1.5 text-[11px]"><span className="opacity-70">{row.label}</span><span className="max-w-[58%] text-right font-semibold text-white">{row.value}</span></div>)}</div>{card.caveat && <div className="mt-2 rounded-xl border border-white/10 bg-black/10 p-2 text-[11px] leading-5 text-white/85"><AlertTriangle className="mr-1 inline h-3.5 w-3.5" /> {card.caveat}</div>}</article>;
}

function sourceLabel(source?: SourceItem) {
  if (!source) return 'No citation returned';
  return String(source.filename || source.document || source.source || 'Uploaded document');
}

function freshnessLabel(source?: SourceItem) {
  const raw = source?.score ?? source?.confidence;
  if (typeof raw !== 'number') return 'Not returned';
  const score = raw <= 1 ? Math.round(raw * 100) : Math.round(raw);
  if (score >= 80) return `${score}% fresh`;
  if (score >= 60) return `${score}% review soon`;
  return `${score}% stale - review`;
}

function normalizeConfidence(value: AskResponse['confidence']) {
  const text = String(value ?? 'unknown').toLowerCase();
  if (typeof value === 'number') {
    if (value >= 0.75) return { label: `${Math.round(value * 100)}% High`, tone: 'emerald' as const };
    if (value >= 0.45) return { label: `${Math.round(value * 100)}% Medium`, tone: 'amber' as const, caveat: 'Medium confidence: verify citations before execution.' };
    return { label: `${Math.round(value * 100)}% Low`, tone: 'red' as const, caveat: 'Low confidence: route to review before field use.' };
  }
  if (text.includes('high')) return { label: 'High', tone: 'emerald' as const };
  if (text.includes('medium')) return { label: 'Medium', tone: 'amber' as const, caveat: 'Medium confidence: verify citations before execution.' };
  if (text.includes('low')) return { label: 'Low', tone: 'red' as const, caveat: 'Low confidence: route to review before field use.' };
  return { label: 'Unknown', tone: 'amber' as const, caveat: 'Confidence was not returned by the backend.' };
}

