'use client';

import { Check, ClipboardCheck, FileSearch, Globe2, LockKeyhole, Mic2, Network, Play, Search, ShieldAlert, Sparkles, Truck } from 'lucide-react';
import { useEffect, useMemo, useState } from 'react';

const capabilities = [
  { label: 'Browse P&IDs', icon: Search },
  { label: 'Voice Ask', icon: Mic2 },
  { label: 'Graph Route', icon: Network },
  { label: 'Safe Procedure', icon: LockKeyhole },
  { label: 'Multi Language', icon: Globe2 },
];

const flow = [
  { title: 'Listening', message: 'Ask me: prepare safe work pack for P-201 seal replacement.', icon: Mic2 },
  { title: 'Reading sources', message: 'Scanning P&ID zone, LOTO procedure, OEM manual, and last inspection notes.', icon: FileSearch },
  { title: 'Building graph path', message: 'Found P-201 connected to XV-14, HX-204, and PT-201A in Zone 3.', icon: Network },
  { title: 'Safety review', message: 'OISD-116 requires lockout verification before confined-space adjacent work.', icon: ShieldAlert },
  { title: 'Work pack ready', message: 'Generated cited work pack with stale-source warning and review actions.', icon: ClipboardCheck },
];

export function PlantBrainAgentCard() {
  const [phase, setPhase] = useState(0);
  const [running, setRunning] = useState(true);
  const active = flow[phase];
  const ActiveIcon = active.icon;
  const completed = phase === flow.length - 1;

  useEffect(() => {
    if (!running) return;
    const timer = window.setInterval(() => {
      setPhase((current) => (current + 1) % flow.length);
    }, 2300);
    return () => window.clearInterval(timer);
  }, [running]);

  const cardStatus = useMemo(() => {
    if (phase < 2) return { label: 'Working', tone: 'text-amber-200 bg-amber-400/15 border-amber-300/20' };
    if (phase < 4) return { label: 'Checking', tone: 'text-cyan-200 bg-cyan-400/15 border-cyan-300/20' };
    return { label: 'Ready', tone: 'text-emerald-200 bg-emerald-400/15 border-emerald-300/20' };
  }, [phase]);

  return (
    <section className="overflow-hidden rounded-3xl border border-violet-300/20 bg-[radial-gradient(circle_at_85%_10%,rgba(139,92,246,0.30),transparent_34%),linear-gradient(135deg,rgba(248,250,252,0.09),rgba(139,92,246,0.10))] p-4 shadow-2xl shadow-violet-950/30">
      <div className="relative rounded-2xl border border-white/10 bg-[#f3efff] p-4 text-slate-950 shadow-inner shadow-white/30">
        <div className="pointer-events-none absolute -left-8 -top-8 h-28 w-28 rounded-full bg-violet-300/30" />
        <div className="pointer-events-none absolute right-5 top-6 h-3 w-3 rounded-full bg-violet-500/60" />
        <div className="pointer-events-none absolute bottom-20 left-7 h-2.5 w-2.5 rounded-full bg-violet-500/50" />

        <div className="relative z-10 flex items-start justify-between gap-4">
          <div>
            <div className="text-xs font-bold uppercase tracking-[0.18em] text-violet-700">Meet</div>
            <div className="mt-1 font-black tracking-tight text-slate-950">
              <span className="block text-3xl leading-none">PlantBrain</span>
              <span className="block bg-gradient-to-r from-violet-700 to-indigo-700 bg-clip-text text-5xl leading-none text-transparent">BOT</span>
            </div>
            <p className="mt-3 max-w-[190px] text-xs font-medium leading-5 text-slate-600">A working AI plant assistant that reads documents, speaks, and creates cited action cards.</p>
          </div>
          <RobotAvatar speaking={running && !completed} />
        </div>

        <div className="relative z-10 mt-4 rounded-2xl bg-[#2f1d5b] p-3 text-white shadow-xl shadow-violet-950/25">
          <div className="flex items-start gap-3">
            <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-violet-500 text-white shadow-lg shadow-violet-950/30">
              <ActiveIcon className="h-4 w-4" />
            </div>
            <div className="min-w-0 flex-1">
              <div className="flex items-center justify-between gap-2">
                <div className="text-xs font-black uppercase tracking-[0.14em] text-violet-100">{active.title}</div>
                <span className={`rounded-full border px-2 py-0.5 text-[10px] font-bold ${cardStatus.tone}`}>{cardStatus.label}</span>
              </div>
              <p className="mt-2 text-xs leading-5 text-violet-100">{active.message}</p>
              <div className="mt-3 flex gap-1.5">
                {flow.map((item, index) => (
                  <span key={item.title} className={`h-1.5 flex-1 rounded-full ${index <= phase ? 'bg-amber-300' : 'bg-white/15'}`} />
                ))}
              </div>
            </div>
          </div>
        </div>

        <div className="relative z-10 mt-4 grid grid-cols-2 gap-2 sm:grid-cols-5 xl:grid-cols-2 2xl:grid-cols-5">
          {capabilities.map(({ label, icon: Icon }) => (
            <button key={label} onClick={() => setRunning(true)} className="flex min-h-[76px] flex-col items-center justify-center rounded-2xl bg-white/90 p-2 text-center shadow-lg shadow-violet-900/10 ring-1 ring-violet-100 transition hover:-translate-y-0.5 hover:ring-violet-300">
              <div className="flex h-9 w-9 items-center justify-center rounded-full bg-violet-100 text-violet-700">
                <Icon className="h-5 w-5" />
              </div>
              <span className="mt-2 text-[10px] font-black leading-tight text-slate-700">{label}</span>
            </button>
          ))}
        </div>

        <div className="relative z-10 mt-4 overflow-hidden rounded-2xl bg-[#3b246c] text-white shadow-xl shadow-violet-950/25">
          <div className="flex items-center justify-between border-b border-amber-300/60 px-3 py-2 text-xs font-bold">
            <span className="inline-flex items-center gap-2"><Truck className="h-4 w-4 text-amber-300" /> Generated Work Pack</span>
            <span className="text-emerald-300">94% cited</span>
          </div>
          <div className="space-y-2 p-3 text-[11px] text-violet-100">
            <WorkLine label="Asset" value="P-201 seal replacement" />
            <WorkLine label="Graph route" value="P-201 -> XV-14 -> HX-204" />
            <WorkLine label="Required source" value="LOTO-07, OEM page 42" />
            <div className="rounded-xl border border-orange-300/30 bg-orange-300/10 p-2 text-orange-100">Warning: OISD-116 source freshness is 58%. Review before execution.</div>
            <button className="mt-1 flex h-10 w-full items-center justify-center gap-2 rounded-xl bg-amber-300 text-xs font-black text-slate-950 shadow-lg shadow-amber-950/20">
              <Check className="h-4 w-4" /> Create reviewed work pack
            </button>
          </div>
        </div>

        <div className="relative z-10 mt-3 flex items-center gap-2">
          <button onClick={() => { setPhase(0); setRunning(true); }} className="inline-flex items-center gap-2 rounded-full bg-violet-700 px-3 py-2 text-xs font-bold text-white shadow-lg shadow-violet-900/20">
            <Play className="h-3.5 w-3.5" /> Run flow
          </button>
          <button onClick={() => setRunning((value) => !value)} className="inline-flex items-center gap-2 rounded-full bg-white px-3 py-2 text-xs font-bold text-violet-800 shadow-lg ring-1 ring-violet-100">
            <Sparkles className="h-3.5 w-3.5" /> {running ? 'Pause bot' : 'Resume bot'}
          </button>
          <div className="ml-auto flex rounded-2xl bg-white px-3 py-2 shadow-lg ring-1 ring-violet-100">
            <span className="h-2 w-2 animate-bounce rounded-full bg-amber-400 [animation-delay:-0.2s]" />
            <span className="mx-1 h-2 w-2 animate-bounce rounded-full bg-amber-400 [animation-delay:-0.1s]" />
            <span className="h-2 w-2 animate-bounce rounded-full bg-amber-400" />
          </div>
        </div>
      </div>
    </section>
  );
}

function WorkLine({ label, value }: { label: string; value: string }) {
  return <div className="flex justify-between gap-3"><span className="font-bold uppercase tracking-[0.12em] text-violet-300">{label}</span><span className="text-right font-semibold text-white">{value}</span></div>;
}

function RobotAvatar({ speaking }: { speaking: boolean }) {
  return (
    <div className="relative h-36 w-28 shrink-0">
      <div className="absolute left-1/2 top-0 h-8 w-3 -translate-x-1/2 rounded-full bg-violet-800" />
      <div className="absolute left-1/2 top-0 h-5 w-5 -translate-x-1/2 rounded-full bg-gradient-to-br from-violet-400 to-violet-900 shadow-lg" />
      <div className="absolute left-1/2 top-8 h-20 w-28 -translate-x-1/2 rounded-[2rem] bg-gradient-to-br from-violet-500 to-violet-900 p-2 shadow-xl shadow-violet-900/30">
        <div className="flex h-full items-center justify-center rounded-[1.45rem] bg-white">
          <div className="flex items-center gap-5">
            <span className="h-7 w-4 rounded-full bg-gradient-to-b from-blue-400 to-indigo-700 shadow-inner" />
            <span className={`${speaking ? 'h-7 w-7 border-[7px]' : 'h-3 w-6 border-[4px]'} rounded-full border-amber-400 bg-slate-950 transition-all duration-300`} />
            <span className="h-7 w-4 rounded-full bg-gradient-to-b from-blue-400 to-indigo-700 shadow-inner" />
          </div>
        </div>
      </div>
      <div className="absolute -left-2 top-16 h-10 w-5 rounded-full bg-violet-700" />
      <div className="absolute -right-2 top-16 h-10 w-5 rounded-full bg-violet-700" />
      <div className="absolute left-5 top-[108px] h-20 w-20 rounded-[2rem] bg-gradient-to-br from-violet-500 to-violet-900 shadow-xl shadow-violet-900/30">
        <div className="absolute inset-x-0 top-7 text-center text-sm font-black tracking-wide text-white">PB</div>
      </div>
      <div className="absolute -left-1 top-[118px] h-6 w-10 rotate-[-18deg] rounded-full bg-white shadow" />
      <div className="absolute right-0 top-[114px] h-6 w-10 rotate-[18deg] rounded-full bg-white shadow" />
    </div>
  );
}
