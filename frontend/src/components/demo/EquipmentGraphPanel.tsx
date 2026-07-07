'use client';

import { Download, GitFork, RefreshCw, Search } from 'lucide-react';
import { useEffect, useMemo, useState } from 'react';
import { exportGraph, getAllEquipment, getEquipment, getGraphStats } from '@/lib/plantbrain-api';
import type { EquipmentItem, GraphStatsResponse } from '@/types/plantbrain';

type GraphNode = { id?: string; tag?: string; labels?: string[]; attributes?: Record<string, unknown> };
type GraphEdge = { source?: string; target?: string; relationship?: string; attributes?: Record<string, unknown> };

export function EquipmentGraphPanel({ onComplete, onStatsChange }: { onComplete: () => void; onStatsChange: (count: number) => void }) {
  const [stats, setStats] = useState<GraphStatsResponse & Record<string, unknown>>({});
  const [equipment, setEquipment] = useState<EquipmentItem[]>([]);
  const [selected, setSelected] = useState<EquipmentItem | null>(null);
  const [graphData, setGraphData] = useState<{ nodes?: GraphNode[]; edges?: GraphEdge[]; backend?: string }>({});
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const refresh = async () => {
    setLoading(true);
    setError('');
    try {
      const [statsResult, equipmentResult, exportResult] = await Promise.allSettled([getGraphStats(), getAllEquipment(), exportGraph()]);
      const statsResponse = statsResult.status === 'fulfilled' ? statsResult.value : {};
      const equipmentResponse = equipmentResult.status === 'fulfilled' ? equipmentResult.value : { equipment: [] };
      const exported = exportResult.status === 'fulfilled' ? exportResult.value : { nodes: [], edges: [] };
      const items = equipmentResponse.equipment || [];
      setStats(statsResponse as typeof stats);
      setEquipment(items);
      setGraphData(exported as typeof graphData);
      const warning = String(
        (statsResponse as Record<string, unknown>).warning ||
        (equipmentResponse as Record<string, unknown>).warning ||
        (exported as Record<string, unknown>).warning ||
        ''
      );
      const failures = [statsResult, equipmentResult, exportResult].filter((result) => result.status === 'rejected') as PromiseRejectedResult[];
      if (failures.length === 3) {
        const reason = failures[0]?.reason as { status?: number; message?: string } | undefined;
        setError(reason?.status ? `${reason.message || 'Failed to load graph'} (HTTP ${reason.status})` : reason?.message || 'Failed to load graph.');
      } else if (warning) {
        setError('Neo4j is unavailable, showing fallback graph. Check NEO4J_URI/NEO4J_USER/NEO4J_PASSWORD.');
      }
      onStatsChange(items.length || Number(statsResponse.nodes || 0));
      if (items.length || Number(statsResponse.nodes || 0)) onComplete();
    } catch (err: any) {
      setError(err?.status ? `${err.message} (HTTP ${err.status})` : err?.message || 'Failed to load graph.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { refresh(); }, []);

  const filtered = useMemo(() => equipment.filter((item) => `${item.tag || ''} ${item.name || ''} ${item.equipment_type || ''}`.toLowerCase().includes(query.toLowerCase())), [equipment, query]);
  const nodes = graphData.nodes || [];
  const edges = graphData.edges || [];

  const inspect = async (item: EquipmentItem | string) => {
    const tag = typeof item === 'string' ? item : String(item.tag || '');
    if (!tag) return;
    setError('');
    try {
      const details = await getEquipment(tag);
      setSelected({ ...(typeof item === 'string' ? { tag } : item), ...details });
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
      a.download = 'plantbrain-neo4j-graph.json';
      a.click();
      URL.revokeObjectURL(url);
      onComplete();
    } catch (err: any) { setError(err?.message || 'Failed to export graph.'); }
  };

  const neighbors = (selected?.neighbors || []) as Array<Record<string, unknown>>;

  return <div className="space-y-5">
    <section className="rounded-3xl border border-white/10 bg-white/[0.04] p-5 shadow-2xl shadow-black/20">
      <div className="mb-5 flex flex-col gap-3 md:flex-row md:items-start md:justify-between"><div><div className="text-xs font-semibold uppercase tracking-[0.2em] text-cyan-300">Production graph state</div><h2 className="mt-2 text-2xl font-semibold text-white">Neo4j Knowledge Graph</h2><p className="mt-2 max-w-3xl text-sm leading-6 text-slate-400">Equipment, valves, instruments, zones, maintenance events, and relationships are exported from the graph backend for live inspection.</p></div><div className="flex gap-2"><button onClick={refresh} className="inline-flex items-center gap-2 rounded-xl border border-white/10 px-3 py-2 text-sm text-slate-200 hover:border-cyan-400/50"><RefreshCw className="h-4 w-4" /> Refresh</button><button onClick={downloadGraph} className="inline-flex items-center gap-2 rounded-xl bg-cyan-300 px-3 py-2 text-sm font-semibold text-slate-950 hover:bg-cyan-200"><Download className="h-4 w-4" /> Export</button></div></div>
      {error && <div className={`mb-4 rounded-xl border p-3 text-sm ${error.startsWith('Neo4j is unavailable') ? 'border-amber-400/20 bg-amber-400/10 text-amber-100' : 'border-red-400/20 bg-red-400/10 text-red-100'}`}>{error}</div>}
      <div className="grid gap-3 md:grid-cols-5"><Metric label="Backend" value={String(stats.graph_backend || graphData.backend || 'fallback')} /><Metric label="Nodes" value={Number(stats.nodes || nodes.length || 0)} /><Metric label="Edges" value={Number(stats.edges || edges.length || 0)} /><Metric label="Valves" value={Number(stats.valve_count || 0)} /><Metric label="Events" value={Number(stats.maintenance_event_count || 0)} /></div>
    </section>

    <section className="overflow-hidden rounded-3xl border border-white/10 bg-[#0b111b] p-5 shadow-2xl shadow-black/20">
      <div className="mb-5 flex items-end justify-between gap-4"><div><div className="text-xs font-semibold uppercase tracking-[0.2em] text-violet-300">Real graph visualization</div><h3 className="mt-2 text-xl font-semibold text-white">Nodes, edges, and relationship labels</h3></div><span className="text-xs text-slate-500">CONNECTED_THROUGH | HAD_EVENT | HAS_INSTRUMENT</span></div>
      <GraphCanvas nodes={nodes} edges={edges} onSelect={inspect} />
    </section>

    <section className="grid gap-5 xl:grid-cols-[380px_1fr]"><div className="rounded-3xl border border-white/10 bg-white/[0.04] p-5"><div className="mb-4 flex items-center gap-2 rounded-xl border border-white/10 bg-white/[0.03] px-3 py-2"><Search className="h-4 w-4 text-slate-500" /><input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search equipment tag..." className="w-full bg-transparent text-sm text-white outline-none placeholder:text-slate-600" /></div>{loading ? <Empty text="Loading equipment graph..." /> : filtered.length === 0 ? <Empty text="No equipment graph yet. Upload a P&ID or maintenance log, then return here." /> : <div className="max-h-[520px] space-y-2 overflow-auto pr-1">{filtered.map((item) => <button key={String(item.tag)} onClick={() => inspect(item)} className="w-full rounded-xl border border-white/10 bg-white/[0.03] p-3 text-left transition hover:border-cyan-400/40"><div className="font-semibold text-white">{item.tag || 'Unknown tag'}</div><div className="mt-1 text-xs text-slate-400">{item.name || item.equipment_type || 'Equipment node'}</div></button>)}</div>}</div><div className="rounded-3xl border border-white/10 bg-white/[0.04] p-5"><h3 className="mb-4 flex items-center gap-2 text-lg font-semibold text-white"><GitFork className="h-5 w-5 text-cyan-300" /> Equipment details</h3>{selected ? <div className="space-y-4"><div className="rounded-2xl border border-cyan-400/20 bg-cyan-400/10 p-4"><div className="text-2xl font-semibold text-white">{selected.tag}</div><div className="mt-1 text-slate-300">{selected.name || selected.attributes?.name as string || 'No name returned'}</div><div className="mt-3 flex flex-wrap gap-2 text-xs text-cyan-100"><span className="rounded-full border border-cyan-400/20 px-2 py-1">{selected.equipment_type || selected.attributes?.type as string || selected.attributes?.equipment_type as string || 'type unknown'}</span><span className="rounded-full border border-cyan-400/20 px-2 py-1">{selected.location || selected.attributes?.location as string || 'location unknown'}</span></div></div><div><div className="mb-2 text-sm font-semibold text-white">Neighbors / relationships</div>{neighbors.length === 0 ? <Empty text="No neighbors returned for this equipment." /> : <div className="space-y-2">{neighbors.map((neighbor, index) => <div key={index} className="rounded-xl border border-white/10 bg-white/[0.03] p-3 text-sm text-slate-300"><span className="font-semibold text-white">{String(neighbor.tag || neighbor.target || 'Node')}</span><span className="mx-2 text-slate-600">-</span>{String(neighbor.relationship || 'connected')}</div>)}</div>}</div></div> : <Empty text="Select equipment to inspect graph context." />}</div></section>
  </div>;
}

function GraphCanvas({ nodes, edges, onSelect }: { nodes: GraphNode[]; edges: GraphEdge[]; onSelect: (tag: string) => void }) {
  const visibleNodes = nodes.slice(0, 28);
  const width = 980;
  const height = 520;
  const centerX = width / 2;
  const centerY = height / 2;
  const radius = Math.min(width, height) * 0.36;
  const positions = new Map<string, { x: number; y: number }>();
  visibleNodes.forEach((node, index) => {
    const id = node.id || node.tag || `node-${index}`;
    const angle = (Math.PI * 2 * index) / Math.max(visibleNodes.length, 1) - Math.PI / 2;
    positions.set(id, { x: centerX + Math.cos(angle) * radius, y: centerY + Math.sin(angle) * radius });
  });
  const visibleEdges = edges.filter((edge) => edge.source && edge.target && positions.has(String(edge.source)) && positions.has(String(edge.target))).slice(0, 60);
  if (visibleNodes.length === 0) return <Empty text="Graph nodes will appear here after Neo4j receives extracted equipment, valves, instruments, and maintenance events." />;
  return <div className="overflow-x-auto rounded-2xl border border-white/10 bg-[#070b12] p-4"><svg viewBox={`0 0 ${width} ${height}`} className="h-[520px] min-w-[900px] w-full">
    <defs><marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse"><path d="M 0 0 L 10 5 L 0 10 z" fill="#64748b" /></marker></defs>
    {visibleEdges.map((edge, index) => { const source = positions.get(String(edge.source))!; const target = positions.get(String(edge.target))!; const midX = (source.x + target.x) / 2; const midY = (source.y + target.y) / 2; return <g key={`${edge.source}-${edge.target}-${index}`}><line x1={source.x} y1={source.y} x2={target.x} y2={target.y} stroke="#334155" strokeWidth="1.4" markerEnd="url(#arrow)" /><text x={midX} y={midY - 5} textAnchor="middle" className="fill-slate-400 text-[10px] font-mono">{edge.relationship}</text></g>; })}
    {visibleNodes.map((node, index) => { const id = node.id || node.tag || `node-${index}`; const position = positions.get(id)!; const label = (node.labels || ['Node'])[0]; const color = label === 'Valve' ? '#f59e0b' : label === 'Instrument' ? '#a78bfa' : label === 'MaintenanceEvent' ? '#fb7185' : label === 'Zone' ? '#22d3ee' : '#34d399'; return <g key={id} onClick={() => onSelect(id)} className="cursor-pointer"><circle cx={position.x} cy={position.y} r="28" fill={`${color}22`} stroke={color} strokeWidth="2" /><text x={position.x} y={position.y - 2} textAnchor="middle" className="fill-white text-[12px] font-semibold">{id}</text><text x={position.x} y={position.y + 14} textAnchor="middle" className="fill-slate-400 text-[9px] uppercase">{label}</text></g>; })}
  </svg></div>;
}

function Metric({ label, value }: { label: string; value: number | string }) { return <div className="rounded-2xl border border-white/10 bg-white/[0.03] p-4"><div className="text-xs uppercase tracking-wide text-slate-500">{label}</div><div className="mt-2 text-2xl font-semibold text-white">{value}</div></div>; }
function Empty({ text }: { text: string }) { return <div className="rounded-2xl border border-white/10 bg-white/[0.03] p-6 text-center text-sm leading-6 text-slate-400">{text}</div>; }
