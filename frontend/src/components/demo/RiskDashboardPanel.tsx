'use client';

import { RefreshCw, ShieldAlert } from 'lucide-react';
import { useEffect, useState } from 'react';
import { getFailureClusters, getOverdueInspections, getRiskSummary } from '@/lib/plantbrain-api';
import type { RiskSummaryResponse } from '@/types/plantbrain';

export function RiskDashboardPanel({ onComplete }: { onComplete: () => void }) {
  const [summary, setSummary] = useState<RiskSummaryResponse | null>(null);
  const [clusters, setClusters] = useState<Array<Record<string, unknown>>>([]);
  const [overdue, setOverdue] = useState<Array<Record<string, unknown>>>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const refresh = async () => {
    setLoading(true); setError('');
    try {
      const [risk, clusterResponse, overdueResponse] = await Promise.all([getRiskSummary(), getFailureClusters(2), getOverdueInspections(180)]);
      const clusterItems = (clusterResponse.failure_clusters || clusterResponse.clusters || []) as Array<Record<string, unknown>>;
      const overdueItems = (overdueResponse.overdue || overdueResponse.inspections || risk.critical_overdue || []) as Array<Record<string, unknown>>;
      setSummary(risk); setClusters(clusterItems); setOverdue(overdueItems); onComplete();
    } catch (err: any) { setError(err?.status ? `${err.message} (HTTP ${err.status})` : err?.message || 'Failed to load risk data.'); }
    finally { setLoading(false); }
  };
  useEffect(() => { refresh(); }, []);

  return <div className="space-y-5"><section className="rounded-3xl border border-white/10 bg-white/[0.04] p-5 shadow-2xl shadow-black/20"><div className="mb-5 flex flex-col gap-3 md:flex-row md:items-start md:justify-between"><div><div className="text-xs font-semibold uppercase tracking-[0.2em] text-cyan-300">Step 06 - Patterns surface automatically</div><h2 className="mt-2 text-2xl font-semibold text-white">Risk patterns and overdue inspections</h2><p className="mt-2 max-w-3xl text-sm leading-6 text-slate-400">PlantBrain detects recurring failures, overdue inspections, and equipment risk clusters across plant records.</p></div><button onClick={refresh} className="inline-flex items-center gap-2 rounded-xl border border-white/10 px-3 py-2 text-sm text-slate-200 hover:border-cyan-400/50"><RefreshCw className="h-4 w-4" /> Refresh</button></div>{error && <div className="rounded-xl border border-red-400/20 bg-red-400/10 p-3 text-sm text-red-100">{error}</div>}<div className="grid gap-3 md:grid-cols-4"><Metric label="Overall risk" value={summary?.overall_risk_level || 'Unknown'} /><Metric label="Overdue" value={summary?.overdue_inspections_count ?? overdue.length} /><Metric label="Failure clusters" value={clusters.length} /><Metric label="Co-occurrence" value={summary?.cooccurrence_patterns?.length || 0} /></div></section>{loading ? <div className="rounded-3xl border border-white/10 bg-white/[0.04] p-8 text-center text-slate-400">Loading risk data...</div> : (!summary && clusters.length === 0 && overdue.length === 0) ? <div className="rounded-3xl border border-white/10 bg-white/[0.04] p-8 text-center text-slate-400">No pattern data yet. Upload maintenance logs or seed inspection data from backend docs.</div> : <section className="grid gap-5 xl:grid-cols-2"><List title="Failure clusters" items={clusters} empty="No recurring failure clusters returned." /><List title="Overdue inspections" items={overdue} empty="No overdue inspections returned." /></section>}</div>;
}
function Metric({ label, value }: { label: string; value: unknown }) { return <div className="rounded-2xl border border-white/10 bg-white/[0.03] p-4"><div className="text-xs uppercase tracking-wide text-slate-500">{label}</div><div className="mt-2 text-2xl font-semibold text-white">{String(value)}</div></div>; }
function List({ title, items, empty }: { title: string; items: Array<Record<string, unknown>>; empty: string }) { return <div className="rounded-3xl border border-white/10 bg-white/[0.04] p-5"><h3 className="mb-4 flex items-center gap-2 text-lg font-semibold text-white"><ShieldAlert className="h-5 w-5 text-amber-300" /> {title}</h3>{items.length === 0 ? <div className="rounded-2xl border border-white/10 bg-white/[0.03] p-6 text-sm text-slate-400">{empty}</div> : <div className="space-y-3">{items.map((item, index) => <pre key={index} className="max-h-56 overflow-auto rounded-2xl border border-white/10 bg-[#060910] p-4 text-xs leading-6 text-slate-300">{JSON.stringify(item, null, 2)}</pre>)}</div>}</div>; }