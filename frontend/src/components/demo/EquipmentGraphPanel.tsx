'use client';

import { Download, GitFork, RefreshCw, Search } from 'lucide-react';
import { useEffect, useMemo, useState } from 'react';
import { exportGraph, getAllEquipment, getEquipment, getGraphStats } from '@/lib/plantbrain-api';
import type { EquipmentItem, GraphStatsResponse } from '@/types/plantbrain';

export function EquipmentGraphPanel({ onComplete, onStatsChange }: { onComplete: () => void; onStatsChange: (count: number) => void }) {
  const [stats, setStats] = useState<GraphStatsResponse>({});
  const [equipment, setEquipment] = useState<EquipmentItem[]>([]);
  const [selected, setSelected] = useState<EquipmentItem | null>(null);
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const refresh = async () => {
    setLoading(true);
    setError('');
    try {
      const [statsResponse, equipmentResponse] = await Promise.all([getGraphStats(), getAllEquipment()]);
      const items = equipmentResponse.equipment || [];
      setStats(statsResponse);
      setEquipment(items);
      onStatsChange(items.length || Number(statsResponse.nodes || 0));
      if (items.length || Number(statsResponse.nodes || 0)) onComplete();
    } catch (err: any) {
      setError(err?.status ? `${err.message} (HTTP ${err.status})` : err?.message || 'Failed to load graph.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    refresh();
  }, []);

  const filtered = useMemo(() => equipment.filter((item) => `${item.tag || ''} ${item.name || ''} ${item.equipment_type || ''}`.toLowerCase().includes(query.toLowerCase())), [equipment, query]);

  const inspect = async (item: EquipmentItem) => {
    const tag = String(item.tag || '');
    if (!tag) return;
    setError('');
    try {
      const details = await getEquipment(tag);
      setSelected({ ...item, ...details });
      onComplete();
    } catch (err: any) {
      setError(err?.status ? `${err.message} (HTTP ${err.status})` : err?.message || 'Failed to load equipment.');
    }
  };

  const downloadGraph = async () => {
    try {
      const graph = await exportGraph();
      const blob = new Blob([JSON.stringify(graph, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'plantbrain-graph.json';
      a.click();
      URL.revokeObjectURL(url);
      onComplete();
    } catch (err: any) {
      setError(err?.message || 'Failed to export graph.');
    }
  };

  const neighbors = (selected?.neighbors || []) as Array<Record<string, unknown>>;

  return (
    <div className="space-y-5">
      <section className="rounded-3xl border border-white/10 bg-white/[0.04] p-5 shadow-2xl shadow-black/20"><div className="mb-5 flex flex-col gap-3 md:flex-row md:items-start md:justify-between"><div><div className="text-xs font-semibold uppercase tracking-[0.2em] text-cyan-300">Step 02 - It learns every relationship</div><h2 className="mt-2 text-2xl font-semibold text-white">Knowledge Graph</h2><p className="mt-2 max-w-3xl text-sm leading-6 text-slate-400">PlantBrain maps equipment, procedures, documents, regulations, work orders, and failure events into a living plant knowledge graph.</p></div><div className="flex gap-2"><button onClick={refresh} className="inline-flex items-center gap-2 rounded-xl border border-white/10 px-3 py-2 text-sm text-slate-200 hover:border-cyan-400/50"><RefreshCw className="h-4 w-4" /> Refresh</button><button onClick={downloadGraph} className="inline-flex items-center gap-2 rounded-xl bg-cyan-300 px-3 py-2 text-sm font-semibold text-slate-950 hover:bg-cyan-200"><Download className="h-4 w-4" /> Export</button></div></div>{error && <div className="mb-4 rounded-xl border border-red-400/20 bg-red-400/10 p-3 text-sm text-red-100">{error}</div>}
        <div className="grid gap-3 md:grid-cols-4"><Metric label="Nodes" value={stats.nodes || 0} /><Metric label="Edges" value={stats.edges || 0} /><Metric label="Equipment" value={equipment.length} /><Metric label="Top connected" value={stats.top_connected?.length || 0} /></div></section>
      <section className="grid gap-5 xl:grid-cols-[380px_1fr]"><div className="rounded-3xl border border-white/10 bg-white/[0.04] p-5"><div className="mb-4 flex items-center gap-2 rounded-xl border border-white/10 bg-white/[0.03] px-3 py-2"><Search className="h-4 w-4 text-slate-500" /><input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search equipment tag..." className="w-full bg-transparent text-sm text-white outline-none placeholder:text-slate-600" /></div>{loading ? <Empty text="Loading equipment graph..." /> : filtered.length === 0 ? <Empty text="No equipment graph yet. Upload documents containing equipment tags like P-201, C-14, F-7, or T-09, then return here." /> : <div className="max-h-[520px] space-y-2 overflow-auto pr-1">{filtered.map((item) => <button key={String(item.tag)} onClick={() => inspect(item)} className="w-full rounded-xl border border-white/10 bg-white/[0.03] p-3 text-left transition hover:border-cyan-400/40"><div className="font-semibold text-white">{item.tag || 'Unknown tag'}</div><div className="mt-1 text-xs text-slate-400">{item.name || item.equipment_type || 'Equipment node'}</div></button>)}</div>}</div><div className="rounded-3xl border border-white/10 bg-white/[0.04] p-5"><h3 className="mb-4 flex items-center gap-2 text-lg font-semibold text-white"><GitFork className="h-5 w-5 text-cyan-300" /> Equipment details</h3>{selected ? <div className="space-y-4"><div className="rounded-2xl border border-cyan-400/20 bg-cyan-400/10 p-4"><div className="text-2xl font-semibold text-white">{selected.tag}</div><div className="mt-1 text-slate-300">{selected.name || selected.attributes?.name as string || 'No name returned'}</div><div className="mt-3 flex flex-wrap gap-2 text-xs text-cyan-100"><span className="rounded-full border border-cyan-400/20 px-2 py-1">{selected.equipment_type || selected.attributes?.equipment_type as string || 'type unknown'}</span><span className="rounded-full border border-cyan-400/20 px-2 py-1">{selected.location || selected.attributes?.location as string || 'location unknown'}</span></div></div><div><div className="mb-2 text-sm font-semibold text-white">Neighbors / relationships</div>{neighbors.length === 0 ? <Empty text="No neighbors returned for this equipment." /> : <div className="space-y-2">{neighbors.map((neighbor, index) => <div key={index} className="rounded-xl border border-white/10 bg-white/[0.03] p-3 text-sm text-slate-300"><span className="font-semibold text-white">{String(neighbor.tag || neighbor.target || 'Node')}</span><span className="mx-2 text-slate-600">-</span>{String(neighbor.relationship || 'connected')}</div>)}</div>}</div></div> : <Empty text="Select equipment to inspect graph context." />}</div></section>
    </div>
  );
}

function Metric({ label, value }: { label: string; value: number | string }) { return <div className="rounded-2xl border border-white/10 bg-white/[0.03] p-4"><div className="text-xs uppercase tracking-wide text-slate-500">{label}</div><div className="mt-2 text-2xl font-semibold text-white">{value}</div></div>; }
function Empty({ text }: { text: string }) { return <div className="rounded-2xl border border-white/10 bg-white/[0.03] p-6 text-center text-sm leading-6 text-slate-400">{text}</div>; }