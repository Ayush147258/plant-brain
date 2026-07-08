'use client';

import { AlertTriangle, CheckCircle2, Download, GitFork, Link2, Loader2, Plus, RefreshCw, Save, Search, ShieldCheck, Sparkles, XCircle } from 'lucide-react';
import { useEffect, useMemo, useState, type ReactNode } from 'react';
import { createGraphRelationship, exportGraph, getAllEquipment, getEquipment, getGraphStats, listPendingGraphReviews, promotePendingGraphReview, rejectPendingGraphReview, saveEquipment } from '@/lib/plantbrain-api';
import type { EquipmentItem, GraphStatsResponse } from '@/types/plantbrain';

type GraphNode = { id?: string; tag?: string; labels?: string[]; attributes?: Record<string, unknown> };
type GraphEdge = { source?: string; target?: string; relationship?: string; attributes?: Record<string, unknown> };
type GraphData = { nodes?: GraphNode[]; edges?: GraphEdge[]; backend?: string; warning?: string };
type NodeKind = 'Equipment' | 'Valve' | 'Instrument' | 'MaintenanceEvent' | 'Document' | 'PendingReview' | 'Zone' | 'Node';
type RelationshipType = 'feeds_into' | 'controls' | 'bypasses' | 'connected_to' | 'part_of';
type SavingState = 'equipment' | 'relationship' | 'review' | '';
type EquipmentForm = { tag: string; name: string; equipment_type: string; location: string; description: string };
type RelationshipForm = { source_tag: string; target_tag: string; relationship_type: RelationshipType };
type PendingReviewItem = { id?: string; entity_type?: string; reason?: string; confidence?: string; payload?: Record<string, unknown> };

const EMPTY_EQUIPMENT_FORM: EquipmentForm = { tag: '', name: '', equipment_type: 'pump', location: '', description: '' };
const EMPTY_RELATIONSHIP_FORM: RelationshipForm = { source_tag: '', target_tag: '', relationship_type: 'connected_to' };
const RELATIONSHIP_TYPES: Array<{ value: RelationshipType; label: string }> = [
  { value: 'connected_to', label: 'Connected to' },
  { value: 'feeds_into', label: 'Feeds into' },
  { value: 'controls', label: 'Controls' },
  { value: 'bypasses', label: 'Bypasses' },
  { value: 'part_of', label: 'Part of' },
];
const NODE_FILTERS: Array<'all' | NodeKind> = ['all', 'Equipment', 'Valve', 'Instrument', 'MaintenanceEvent', 'Document', 'PendingReview', 'Zone'];
const TAG_PATTERN = /^[A-Z]{1,3}-\d{3,4}[A-Z]?$/;

export function EquipmentGraphPanel({ onComplete, onStatsChange }: { onComplete: () => void; onStatsChange: (count: number) => void }) {
  const [stats, setStats] = useState<GraphStatsResponse & Record<string, unknown>>({});
  const [equipment, setEquipment] = useState<EquipmentItem[]>([]);
  const [selected, setSelected] = useState<EquipmentItem | null>(null);
  const [selectedGraphNode, setSelectedGraphNode] = useState<GraphNode | null>(null);
  const [selectedNodeId, setSelectedNodeId] = useState('');
  const [graphData, setGraphData] = useState<GraphData>({});
  const [equipmentForm, setEquipmentForm] = useState<EquipmentForm>(EMPTY_EQUIPMENT_FORM);
  const [relationshipForm, setRelationshipForm] = useState<RelationshipForm>(EMPTY_RELATIONSHIP_FORM);
  const [query, setQuery] = useState('');
  const [kindFilter, setKindFilter] = useState<'all' | NodeKind>('all');
  const [adminKey, setAdminKey] = useState('');
  const [pending, setPending] = useState<PendingReviewItem[]>([]);
  const [selectedReview, setSelectedReview] = useState<PendingReviewItem | null>(null);
  const [reviewPayloadText, setReviewPayloadText] = useState('{}');
  const [loading, setLoading] = useState(true);
  const [pendingLoading, setPendingLoading] = useState(false);
  const [saving, setSaving] = useState<SavingState>('');
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');

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
      setGraphData(exported as GraphData);
      const warning = String((statsResponse as Record<string, unknown>).warning || (equipmentResponse as Record<string, unknown>).warning || (exported as Record<string, unknown>).warning || '');
      const failures = [statsResult, equipmentResult, exportResult].filter((result) => result.status === 'rejected') as PromiseRejectedResult[];
      if (failures.length === 3) setError(formatApiError(failures[0]?.reason, 'Failed to load graph.'));
      else if (warning) setError('Neo4j is unavailable, showing fallback graph. Check NEO4J_URI/NEO4J_USER/NEO4J_PASSWORD.');
      onStatsChange(items.length || Number((statsResponse as Record<string, unknown>).nodes || 0));
      if (items.length || Number((statsResponse as Record<string, unknown>).nodes || 0)) onComplete();
    } catch (err) {
      setError(formatApiError(err, 'Failed to load graph.'));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { refresh(); }, []);

  const nodes = useMemo<GraphNode[]>(() => {
    const exportedNodes = (graphData.nodes || []).filter((node) => nodeId(node));
    if (exportedNodes.length > 0) return exportedNodes;
    return equipment.filter((item) => item.tag).map((item) => ({ id: String(item.tag), tag: String(item.tag), labels: ['Equipment'], attributes: { id: item.tag, name: item.name, type: item.equipment_type, equipment_type: item.equipment_type, location: item.location, description: item.description, ...(item.attributes || {}) } }));
  }, [equipment, graphData.nodes]);
  const edges = useMemo<GraphEdge[]>(() => (graphData.edges || []).filter((edge) => edge.source && edge.target), [graphData.edges]);
  const equipmentTags = useMemo(() => new Set(equipment.map((item) => String(item.tag || '').toUpperCase()).filter(Boolean)), [equipment]);
  const nodeIndex = useMemo(() => new Map(nodes.map((node) => [nodeId(node).toUpperCase(), node])), [nodes]);
  const filteredEquipment = useMemo(() => equipment.filter((item) => `${item.tag || ''} ${item.name || ''} ${item.equipment_type || ''} ${item.location || ''}`.toLowerCase().includes(query.toLowerCase())), [equipment, query]);
  const visibleNodes = useMemo(() => nodes.filter((node) => (kindFilter === 'all' || nodeKind(node) === kindFilter) && (!query.trim() || nodeSearchText(node).includes(query.toLowerCase()))).slice(0, 90), [kindFilter, nodes, query]);
  const visibleNodeIds = useMemo(() => new Set(visibleNodes.map((node) => nodeId(node).toUpperCase())), [visibleNodes]);
  const visibleEdges = useMemo(() => edges.filter((edge) => visibleNodeIds.has(String(edge.source || '').toUpperCase()) && visibleNodeIds.has(String(edge.target || '').toUpperCase())).slice(0, 140), [edges, visibleNodeIds]);
  const selectedKind = selectedGraphNode ? nodeKind(selectedGraphNode) : selected ? 'Equipment' : 'Node';
  const selectedAttrs = selectedGraphNode?.attributes || selected?.attributes || {};

  const selectNode = async (id: string) => {
    const normalizedId = id.trim().toUpperCase();
    if (!normalizedId) return;
    const graphNode = nodeIndex.get(normalizedId) || null;
    setSelectedNodeId(normalizedId);
    setSelectedGraphNode(graphNode || { id: normalizedId, tag: normalizedId, labels: ['Equipment'], attributes: { id: normalizedId } });
    setRelationshipForm((current) => ({ ...current, source_tag: normalizedId }));
    setNotice('');
    setError('');
    if (graphNode && nodeKind(graphNode) !== 'Equipment') {
      setSelected(null);
      setEquipmentForm(equipmentFormFromNode(normalizedId, graphNode));
      return;
    }
    try {
      const details = await getEquipment(normalizedId);
      const merged = { tag: normalizedId, ...details };
      setSelected(merged);
      setEquipmentForm(equipmentFormFromEquipment(merged));
      onComplete();
    } catch (err) {
      setSelected(null);
      setEquipmentForm(equipmentFormFromNode(normalizedId, graphNode));
      setError(formatApiError(err, 'Equipment selected, but full details could not be loaded.'));
    }
  };

  const startNewEquipment = () => {
    setSelected(null);
    setSelectedGraphNode(null);
    setSelectedNodeId('');
    setEquipmentForm(EMPTY_EQUIPMENT_FORM);
    setRelationshipForm(EMPTY_RELATIONSHIP_FORM);
    setSelectedReview(null);
    setReviewPayloadText('{}');
    setNotice('Ready to add a new equipment node.');
    setError('');
  };

  const saveEquipmentForm = async () => {
    const payload = { ...equipmentForm, tag: equipmentForm.tag.trim().toUpperCase() };
    if (!payload.tag) return setError('Equipment tag is required.');
    if (!TAG_PATTERN.test(payload.tag)) return setError('Use a plant-style equipment tag like P-201, E-105, HX-204, or V-101.');
    setSaving('equipment');
    setError('');
    try {
      await saveEquipment(payload);
      setNotice(`${payload.tag} saved to the graph.`);
      setEquipmentForm(payload);
      await refresh();
      await selectNode(payload.tag);
    } catch (err) {
      setError(formatApiError(err, 'Failed to save equipment.'));
    } finally {
      setSaving('');
    }
  };

  const createRelationship = async () => {
    const source = relationshipForm.source_tag.trim().toUpperCase();
    const target = relationshipForm.target_tag.trim().toUpperCase();
    if (!source || !target) return setError('Choose both source and target equipment tags before adding a relationship.');
    if (!TAG_PATTERN.test(source) || !TAG_PATTERN.test(target)) return setError('Relationships in this simple editor currently connect equipment-style tags only.');
    setSaving('relationship');
    setError('');
    try {
      if (!equipmentTags.has(source)) await saveEquipment({ tag: source });
      if (!equipmentTags.has(target)) await saveEquipment({ tag: target });
      await createGraphRelationship({ source_tag: source, target_tag: target, relationship_type: relationshipForm.relationship_type });
      setNotice(`${source} ${relationshipLabel(relationshipForm.relationship_type).toLowerCase()} ${target}.`);
      setRelationshipForm((current) => ({ ...current, source_tag: source, target_tag: '' }));
      await refresh();
      await selectNode(source);
    } catch (err) {
      setError(formatApiError(err, 'Failed to add relationship.'));
    } finally {
      setSaving('');
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
    } catch (err) { setError(formatApiError(err, 'Failed to export graph.')); }
  };

  const loadPendingReviews = async () => {
    setPendingLoading(true);
    setError('');
    try {
      const response = await listPendingGraphReviews(adminKey, 100);
      const items = (response.items || []) as PendingReviewItem[];
      setPending(items);
      setNotice(items.length ? `${items.length} pending review item${items.length === 1 ? '' : 's'} loaded.` : 'No pending review items right now.');
    } catch (err) {
      setError(formatApiError(err, 'Failed to load pending reviews. Add the admin key if production security is enabled.'));
    } finally {
      setPendingLoading(false);
    }
  };

  const selectReview = (review: PendingReviewItem) => {
    setSelectedReview(review);
    const payload = review.payload || {};
    setReviewPayloadText(JSON.stringify(payload, null, 2));
    setSelectedGraphNode({ id: review.id, labels: ['PendingReview'], attributes: { ...payload, confidence: review.confidence, reason: review.reason } });
    setSelectedNodeId(String(review.id || ''));
    if (review.entity_type === 'equipment') {
      setEquipmentForm({ tag: String(payload.id || payload.tag || ''), name: String(payload.name || ''), equipment_type: String(payload.type || payload.equipment_type || 'equipment'), location: String(payload.location || ''), description: String(payload.description || '') });
    }
  };

  const promoteReview = async () => {
    if (!selectedReview?.id) return;
    setSaving('review');
    setError('');
    try {
      const correctedFields = JSON.parse(reviewPayloadText || '{}') as Record<string, unknown>;
      await promotePendingGraphReview(selectedReview.id, correctedFields, adminKey);
      setNotice('Pending review promoted into the trusted graph.');
      setSelectedReview(null);
      setReviewPayloadText('{}');
      await loadPendingReviews();
      await refresh();
    } catch (err) {
      setError(err instanceof SyntaxError ? 'Corrected fields must be valid JSON before promotion.' : formatApiError(err, 'Failed to promote pending review.'));
    } finally { setSaving(''); }
  };

  const rejectReview = async () => {
    if (!selectedReview?.id) return;
    setSaving('review');
    setError('');
    try {
      await rejectPendingGraphReview(selectedReview.id, 'Rejected from manual graph editor', adminKey);
      setNotice('Pending review rejected and archived.');
      setSelectedReview(null);
      setReviewPayloadText('{}');
      await loadPendingReviews();
    } catch (err) { setError(formatApiError(err, 'Failed to reject pending review.')); }
    finally { setSaving(''); }
  };

  return <div className="space-y-5">
    <section className="rounded-3xl border border-white/10 bg-white/[0.04] p-5 shadow-2xl shadow-black/20">
      <div className="mb-5 flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
        <div><div className="text-xs font-semibold uppercase tracking-[0.2em] text-cyan-300">Editable plant knowledge graph</div><h2 className="mt-2 text-2xl font-semibold text-white">Neo4j Graph Workbench</h2><p className="mt-2 max-w-3xl text-sm leading-6 text-slate-400">Inspect extracted equipment, correct bad tags, add missing relationships, and promote low-confidence Gemini extractions only after a human checks them.</p></div>
        <div className="flex flex-wrap gap-2"><button onClick={startNewEquipment} className="inline-flex items-center gap-2 rounded-xl border border-emerald-400/30 bg-emerald-400/10 px-3 py-2 text-sm font-semibold text-emerald-100 hover:border-emerald-300/70"><Plus className="h-4 w-4" /> Add equipment</button><button onClick={refresh} className="inline-flex items-center gap-2 rounded-xl border border-white/10 px-3 py-2 text-sm text-slate-200 hover:border-cyan-400/50"><RefreshCw className="h-4 w-4" /> Refresh</button><button onClick={downloadGraph} className="inline-flex items-center gap-2 rounded-xl bg-cyan-300 px-3 py-2 text-sm font-semibold text-slate-950 hover:bg-cyan-200"><Download className="h-4 w-4" /> Export</button></div>
      </div>
      {error && <StatusMessage tone="error" text={error} />}
      {notice && <StatusMessage tone="success" text={notice} />}
      <div className="grid gap-3 md:grid-cols-5"><Metric label="Backend" value={String(stats.graph_backend || graphData.backend || 'fallback')} /><Metric label="Nodes" value={Number(stats.nodes || nodes.length || 0)} /><Metric label="Edges" value={Number(stats.edges || edges.length || 0)} /><Metric label="Low review" value={pending.length || Number(stats.pending_review_count || 0)} /><Metric label="Events" value={Number(stats.maintenance_event_count || 0)} /></div>
    </section>

    <section className="grid gap-5 2xl:grid-cols-[minmax(0,1fr)_420px]">
      <div className="overflow-hidden rounded-3xl border border-white/10 bg-[#0b111b] p-5 shadow-2xl shadow-black/20">
        <div className="mb-4 flex flex-col gap-3 xl:flex-row xl:items-end xl:justify-between"><div><div className="text-xs font-semibold uppercase tracking-[0.2em] text-violet-300">Graph canvas</div><h3 className="mt-2 text-xl font-semibold text-white">Click a node to inspect or edit it</h3></div><div className="flex flex-col gap-2 sm:flex-row sm:items-center"><div className="flex items-center gap-2 rounded-xl border border-white/10 bg-white/[0.03] px-3 py-2"><Search className="h-4 w-4 text-slate-500" /><input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search tags, events, confidence..." className="w-full min-w-[220px] bg-transparent text-sm text-white outline-none placeholder:text-slate-600" /></div><select value={kindFilter} onChange={(event) => setKindFilter(event.target.value as typeof kindFilter)} className="rounded-xl border border-white/10 bg-[#111827] px-3 py-2 text-sm text-slate-200 outline-none">{NODE_FILTERS.map((filter) => <option key={filter} value={filter}>{filter === 'all' ? 'All nodes' : filter}</option>)}</select></div></div>
        <GraphCanvas nodes={visibleNodes} edges={visibleEdges} selectedId={selectedNodeId} onSelect={selectNode} />
      </div>
      <GraphEditorPanel selectedId={selectedNodeId} selectedKind={selectedKind} selectedAttrs={selectedAttrs} selected={selected} equipmentForm={equipmentForm} relationshipForm={relationshipForm} selectedReview={selectedReview} reviewPayloadText={reviewPayloadText} saving={saving} onEquipmentChange={setEquipmentForm} onRelationshipChange={setRelationshipForm} onReviewPayloadChange={setReviewPayloadText} onSaveEquipment={saveEquipmentForm} onCreateRelationship={createRelationship} onPromoteReview={promoteReview} onRejectReview={rejectReview} />
    </section>

    <section className="grid gap-5 xl:grid-cols-[380px_1fr]">
      <div className="rounded-3xl border border-white/10 bg-white/[0.04] p-5">
        <div className="mb-4 flex items-center justify-between gap-3"><div><div className="text-xs font-semibold uppercase tracking-[0.18em] text-cyan-300">Equipment index</div><h3 className="mt-1 text-lg font-semibold text-white">Known assets</h3></div><span className="rounded-full border border-white/10 px-2.5 py-1 text-xs text-slate-400">{filteredEquipment.length}</span></div>
        {loading ? <Empty text="Loading equipment graph..." /> : filteredEquipment.length === 0 ? <Empty text="No equipment yet. Add one manually or upload a P&ID." /> : <div className="max-h-[520px] space-y-2 overflow-auto pr-1">{filteredEquipment.map((item) => <button key={String(item.tag)} onClick={() => selectNode(String(item.tag || ''))} className={`w-full rounded-xl border p-3 text-left transition ${selectedNodeId === String(item.tag || '').toUpperCase() ? 'border-cyan-300/70 bg-cyan-300/10' : 'border-white/10 bg-white/[0.03] hover:border-cyan-400/40'}`}><div className="flex items-center justify-between gap-2"><div className="font-semibold text-white">{item.tag || 'Unknown tag'}</div><span className="text-xs text-slate-500">{item.neighbor_count || 0} links</span></div><div className="mt-1 text-xs text-slate-400">{item.name || item.equipment_type || 'Equipment node'}</div></button>)}</div>}
      </div>

      <div className="rounded-3xl border border-white/10 bg-white/[0.04] p-5">
        <div className="mb-4 flex flex-col gap-3 lg:flex-row lg:items-end lg:justify-between"><div><div className="text-xs font-semibold uppercase tracking-[0.18em] text-amber-300">Human review queue</div><h3 className="mt-1 flex items-center gap-2 text-lg font-semibold text-white"><ShieldCheck className="h-5 w-5 text-amber-300" /> Low-confidence extractions</h3></div><div className="flex flex-col gap-2 sm:flex-row"><input value={adminKey} onChange={(event) => setAdminKey(event.target.value)} placeholder="Admin key if required" className="rounded-xl border border-white/10 bg-white/[0.03] px-3 py-2 text-sm text-white outline-none placeholder:text-slate-600" type="password" /><button onClick={loadPendingReviews} disabled={pendingLoading} className="inline-flex items-center justify-center gap-2 rounded-xl border border-amber-300/30 bg-amber-300/10 px-3 py-2 text-sm font-semibold text-amber-100 hover:border-amber-200/70 disabled:cursor-not-allowed disabled:opacity-60">{pendingLoading ? <Loader2 className="h-4 w-4 animate-spin" /> : <RefreshCw className="h-4 w-4" />} Load reviews</button></div></div>
        {pending.length === 0 ? <Empty text="Low-confidence nodes will appear here as PendingReview items instead of entering the trusted graph directly." /> : <div className="grid gap-2 md:grid-cols-2 2xl:grid-cols-3">{pending.map((item) => <button key={String(item.id)} onClick={() => selectReview(item)} className={`rounded-xl border p-3 text-left transition ${selectedReview?.id === item.id ? 'border-amber-300/70 bg-amber-300/10' : 'border-white/10 bg-white/[0.03] hover:border-amber-300/40'}`}><div className="flex items-center justify-between gap-2 text-xs uppercase tracking-wide text-slate-500"><span>{item.entity_type || 'review'}</span><span className="text-amber-200">{item.confidence || 'low'}</span></div><div className="mt-2 truncate text-sm font-semibold text-white">{String(item.payload?.id || item.payload?.tag || item.payload?.Asset_ID || item.id || 'Pending item')}</div><div className="mt-1 line-clamp-2 text-xs text-slate-400">{item.reason || 'Needs human confirmation'}</div></button>)}</div>}
      </div>
    </section>
  </div>;
}

function GraphEditorPanel({ selectedId, selectedKind, selectedAttrs, selected, equipmentForm, relationshipForm, selectedReview, reviewPayloadText, saving, onEquipmentChange, onRelationshipChange, onReviewPayloadChange, onSaveEquipment, onCreateRelationship, onPromoteReview, onRejectReview }: { selectedId: string; selectedKind: NodeKind; selectedAttrs: Record<string, unknown>; selected: EquipmentItem | null; equipmentForm: EquipmentForm; relationshipForm: RelationshipForm; selectedReview: PendingReviewItem | null; reviewPayloadText: string; saving: SavingState; onEquipmentChange: (value: EquipmentForm) => void; onRelationshipChange: (value: RelationshipForm) => void; onReviewPayloadChange: (value: string) => void; onSaveEquipment: () => void; onCreateRelationship: () => void; onPromoteReview: () => void; onRejectReview: () => void }) {
  const canEditEquipment = selectedKind === 'Equipment' || !selectedId;
  const neighbors = (selected?.neighbors || []) as Array<Record<string, unknown>>;
  return <aside className="rounded-3xl border border-white/10 bg-white/[0.04] p-5 shadow-2xl shadow-black/20">
    <div className="mb-5 flex items-start justify-between gap-3"><div><div className="text-xs font-semibold uppercase tracking-[0.18em] text-emerald-300">Manual edit</div><h3 className="mt-1 text-xl font-semibold text-white">{selectedId || 'Create graph node'}</h3><p className="mt-1 text-sm text-slate-400">{selectedId ? `${selectedKind} selected` : 'Add a trusted equipment node by hand.'}</p></div><NodePill kind={selectedKind} confidence={String(selectedAttrs.confidence || selectedReview?.confidence || '')} /></div>
    {selectedId && selectedKind !== 'Equipment' && <div className="mb-4 rounded-2xl border border-violet-300/20 bg-violet-300/10 p-3 text-sm leading-6 text-violet-100">This node is readable now. Direct manual editing is enabled for Equipment nodes first; valve/instrument changes should flow through PendingReview promotion so relationships stay sane.</div>}
    <div className="space-y-4">
      <div className="rounded-2xl border border-white/10 bg-[#0b111b] p-4"><div className="mb-3 flex items-center gap-2 text-sm font-semibold text-white"><Save className="h-4 w-4 text-emerald-300" /> Equipment fields</div><div className="grid gap-3"><Field label="Tag"><input value={equipmentForm.tag} onChange={(event) => onEquipmentChange({ ...equipmentForm, tag: event.target.value.toUpperCase() })} disabled={!canEditEquipment} placeholder="P-201" className="rounded-xl border border-white/10 bg-white/[0.03] px-3 py-2 text-sm text-white outline-none placeholder:text-slate-600 disabled:cursor-not-allowed disabled:opacity-50" /></Field><Field label="Name"><input value={equipmentForm.name} onChange={(event) => onEquipmentChange({ ...equipmentForm, name: event.target.value })} disabled={!canEditEquipment} placeholder="Main transfer pump" className="rounded-xl border border-white/10 bg-white/[0.03] px-3 py-2 text-sm text-white outline-none placeholder:text-slate-600 disabled:cursor-not-allowed disabled:opacity-50" /></Field><div className="grid gap-3 sm:grid-cols-2"><Field label="Type"><input value={equipmentForm.equipment_type} onChange={(event) => onEquipmentChange({ ...equipmentForm, equipment_type: event.target.value })} disabled={!canEditEquipment} placeholder="pump" className="rounded-xl border border-white/10 bg-white/[0.03] px-3 py-2 text-sm text-white outline-none placeholder:text-slate-600 disabled:cursor-not-allowed disabled:opacity-50" /></Field><Field label="Location"><input value={equipmentForm.location} onChange={(event) => onEquipmentChange({ ...equipmentForm, location: event.target.value })} disabled={!canEditEquipment} placeholder="Zone 3" className="rounded-xl border border-white/10 bg-white/[0.03] px-3 py-2 text-sm text-white outline-none placeholder:text-slate-600 disabled:cursor-not-allowed disabled:opacity-50" /></Field></div><Field label="Description"><textarea value={equipmentForm.description} onChange={(event) => onEquipmentChange({ ...equipmentForm, description: event.target.value })} disabled={!canEditEquipment} placeholder="Short engineering note" rows={3} className="rounded-xl border border-white/10 bg-white/[0.03] px-3 py-2 text-sm text-white outline-none placeholder:text-slate-600 disabled:cursor-not-allowed disabled:opacity-50 resize-none" /></Field><button onClick={onSaveEquipment} disabled={!canEditEquipment || saving === 'equipment'} className="inline-flex items-center justify-center gap-2 rounded-xl bg-emerald-300 px-3 py-2 text-sm font-semibold text-slate-950 hover:bg-emerald-200 disabled:cursor-not-allowed disabled:opacity-60">{saving === 'equipment' ? <Loader2 className="h-4 w-4 animate-spin" /> : <CheckCircle2 className="h-4 w-4" />} Save equipment</button></div></div>
      <div className="rounded-2xl border border-white/10 bg-[#0b111b] p-4"><div className="mb-3 flex items-center gap-2 text-sm font-semibold text-white"><Link2 className="h-4 w-4 text-cyan-300" /> Add relationship</div><div className="grid gap-3"><div className="grid gap-3 sm:grid-cols-2"><Field label="From"><input value={relationshipForm.source_tag} onChange={(event) => onRelationshipChange({ ...relationshipForm, source_tag: event.target.value.toUpperCase() })} placeholder="P-201" className="rounded-xl border border-white/10 bg-white/[0.03] px-3 py-2 text-sm text-white outline-none placeholder:text-slate-600 disabled:cursor-not-allowed disabled:opacity-50" /></Field><Field label="To"><input value={relationshipForm.target_tag} onChange={(event) => onRelationshipChange({ ...relationshipForm, target_tag: event.target.value.toUpperCase() })} placeholder="HX-204" className="rounded-xl border border-white/10 bg-white/[0.03] px-3 py-2 text-sm text-white outline-none placeholder:text-slate-600 disabled:cursor-not-allowed disabled:opacity-50" /></Field></div><Field label="Relationship"><select value={relationshipForm.relationship_type} onChange={(event) => onRelationshipChange({ ...relationshipForm, relationship_type: event.target.value as RelationshipType })} className="rounded-xl border border-white/10 bg-white/[0.03] px-3 py-2 text-sm text-white outline-none placeholder:text-slate-600 disabled:cursor-not-allowed disabled:opacity-50">{RELATIONSHIP_TYPES.map((item) => <option key={item.value} value={item.value}>{item.label}</option>)}</select></Field><button onClick={onCreateRelationship} disabled={saving === 'relationship'} className="inline-flex items-center justify-center gap-2 rounded-xl border border-cyan-300/30 bg-cyan-300/10 px-3 py-2 text-sm font-semibold text-cyan-100 hover:border-cyan-200/70 disabled:cursor-not-allowed disabled:opacity-60">{saving === 'relationship' ? <Loader2 className="h-4 w-4 animate-spin" /> : <GitFork className="h-4 w-4" />} Add connection</button></div></div>
      {selectedReview && <div className="rounded-2xl border border-amber-300/20 bg-amber-300/10 p-4"><div className="mb-3 flex items-center gap-2 text-sm font-semibold text-amber-100"><AlertTriangle className="h-4 w-4" /> Review correction JSON</div><textarea value={reviewPayloadText} onChange={(event) => onReviewPayloadChange(event.target.value)} rows={8} className="w-full rounded-xl border border-amber-300/20 bg-slate-950/70 px-3 py-2 font-mono text-xs text-amber-50 outline-none" /><div className="mt-3 grid gap-2 sm:grid-cols-2"><button onClick={onPromoteReview} disabled={saving === 'review'} className="inline-flex items-center justify-center gap-2 rounded-xl bg-amber-300 px-3 py-2 text-sm font-semibold text-slate-950 hover:bg-amber-200 disabled:cursor-not-allowed disabled:opacity-60">{saving === 'review' ? <Loader2 className="h-4 w-4 animate-spin" /> : <Sparkles className="h-4 w-4" />} Promote</button><button onClick={onRejectReview} disabled={saving === 'review'} className="inline-flex items-center justify-center gap-2 rounded-xl border border-red-300/30 bg-red-300/10 px-3 py-2 text-sm font-semibold text-red-100 hover:border-red-200/70 disabled:cursor-not-allowed disabled:opacity-60"><XCircle className="h-4 w-4" /> Reject</button></div></div>}
      <div className="rounded-2xl border border-white/10 bg-[#0b111b] p-4"><div className="mb-3 text-sm font-semibold text-white">Neighbors</div>{neighbors.length === 0 ? <Empty text="Select trusted equipment to see direct graph neighbors." /> : <div className="space-y-2">{neighbors.map((neighbor, index) => <div key={index} className="rounded-xl border border-white/10 bg-white/[0.03] p-3 text-sm text-slate-300"><span className="font-semibold text-white">{String(neighbor.tag || neighbor.target || 'Node')}</span><span className="mx-2 text-slate-600">/</span>{humanizeRelationship(String(neighbor.relationship || 'connected'))}</div>)}</div>}</div>
    </div>
  </aside>;
}

function GraphCanvas({ nodes, edges, selectedId, onSelect }: { nodes: GraphNode[]; edges: GraphEdge[]; selectedId: string; onSelect: (tag: string) => void }) {
  const width = 1120;
  const height = 620;
  const positions = useMemo(() => layoutNodes(nodes, edges, width, height, selectedId), [edges, nodes, selectedId]);
  if (nodes.length === 0) return <Empty text="Graph nodes will appear here after Neo4j receives extracted equipment, valves, instruments, maintenance events, or manual edits." />;
  return <div className="overflow-x-auto rounded-2xl border border-white/10 bg-[#070b12] p-4"><svg viewBox={`0 0 ${width} ${height}`} className="h-[620px] min-w-[980px] w-full" role="img" aria-label="Editable PlantBrain knowledge graph"><defs><filter id="nodeGlow" x="-40%" y="-40%" width="180%" height="180%"><feGaussianBlur stdDeviation="5" result="blur" /><feMerge><feMergeNode in="blur" /><feMergeNode in="SourceGraphic" /></feMerge></filter><marker id="graphArrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse"><path d="M 0 0 L 10 5 L 0 10 z" fill="#64748b" /></marker></defs>
    {edges.map((edge, index) => { const source = positions.get(String(edge.source || '').toUpperCase()); const target = positions.get(String(edge.target || '').toUpperCase()); if (!source || !target) return null; const curve = curvedPath(source.x, source.y, target.x, target.y, index); const midX = (source.x + target.x) / 2; const midY = (source.y + target.y) / 2; return <g key={`${edge.source}-${edge.target}-${index}`}><path d={curve} fill="none" stroke="#475569" strokeWidth="1.3" opacity="0.8" markerEnd="url(#graphArrow)" />{index < 55 && <text x={midX} y={midY - 6} textAnchor="middle" className="fill-slate-500 text-[10px] font-mono">{humanizeRelationship(String(edge.relationship || 'RELATED'))}</text>}</g>; })}
    {nodes.map((node, index) => { const id = nodeId(node); const position = positions.get(id.toUpperCase()) || { x: 80 + index * 36, y: 80 }; const isSelected = selectedId.toUpperCase() === id.toUpperCase(); const kind = nodeKind(node); const colors = nodeColors(node); const radius = isSelected ? 34 : kind === 'Equipment' ? 27 : kind === 'Valve' ? 23 : 20; return <g key={`${id}-${index}`} onClick={() => onSelect(id)} className="cursor-pointer outline-none" role="button" tabIndex={0} onKeyDown={(event) => { if (event.key === 'Enter') onSelect(id); }}>{isSelected && <circle cx={position.x} cy={position.y} r={radius + 11} fill={colors.stroke} opacity="0.14" filter="url(#nodeGlow)" />}<circle cx={position.x} cy={position.y} r={radius} fill={colors.fill} stroke={colors.stroke} strokeWidth={isSelected ? 3 : 2} />{confidenceOf(node) === 'low' && <circle cx={position.x} cy={position.y} r={radius + 5} fill="none" stroke="#fb7185" strokeDasharray="4 5" strokeWidth="1.5" />}<text x={position.x} y={position.y - 2} textAnchor="middle" className="fill-white text-[11px] font-semibold">{shortLabel(id, isSelected ? 16 : 11)}</text><text x={position.x} y={position.y + 13} textAnchor="middle" className="text-[8px] uppercase" fill={colors.text}>{shortLabel(kind, 14)}</text></g>; })}
  </svg></div>;
}

function layoutNodes(nodes: GraphNode[], edges: GraphEdge[], width: number, height: number, selectedId: string) {
  const degree = new Map<string, number>();
  edges.forEach((edge) => { const source = String(edge.source || '').toUpperCase(); const target = String(edge.target || '').toUpperCase(); if (source) degree.set(source, (degree.get(source) || 0) + 1); if (target) degree.set(target, (degree.get(target) || 0) + 1); });
  const sorted = [...nodes].sort((a, b) => { const aSelected = nodeId(a).toUpperCase() === selectedId.toUpperCase() ? 1 : 0; const bSelected = nodeId(b).toUpperCase() === selectedId.toUpperCase() ? 1 : 0; return bSelected - aSelected || (degree.get(nodeId(b).toUpperCase()) || 0) - (degree.get(nodeId(a).toUpperCase()) || 0); });
  const centerX = width / 2;
  const centerY = height / 2;
  const positions = new Map<string, { x: number; y: number }>();
  sorted.forEach((node, index) => { const id = nodeId(node).toUpperCase(); if (selectedId && id === selectedId.toUpperCase()) { positions.set(id, { x: centerX, y: centerY }); return; } const kind = nodeKind(node); const ring = kind === 'Equipment' ? 0.3 : kind === 'Valve' ? 0.42 : kind === 'Instrument' ? 0.52 : kind === 'PendingReview' ? 0.58 : 0.48; const groupOffset = kind === 'Equipment' ? 0 : kind === 'Valve' ? 0.7 : kind === 'Instrument' ? 1.4 : kind === 'MaintenanceEvent' ? 2.1 : 2.8; const radiusX = width * ring; const radiusY = height * (ring * 0.62); const angle = (Math.PI * 2 * index) / Math.max(sorted.length, 1) - Math.PI / 2 + groupOffset; positions.set(id, { x: centerX + Math.cos(angle) * radiusX, y: centerY + Math.sin(angle) * radiusY }); });
  return positions;
}

function Metric({ label, value }: { label: string; value: number | string }) { return <div className="rounded-2xl border border-white/10 bg-white/[0.03] p-4"><div className="text-xs uppercase tracking-wide text-slate-500">{label}</div><div className="mt-2 truncate text-2xl font-semibold text-white">{value}</div></div>; }
function Empty({ text }: { text: string }) { return <div className="rounded-2xl border border-white/10 bg-white/[0.03] p-6 text-center text-sm leading-6 text-slate-400">{text}</div>; }
function Field({ label, children }: { label: string; children: ReactNode }) { return <label className="grid gap-1.5 text-xs font-medium uppercase tracking-wide text-slate-500"><span>{label}</span>{children}</label>; }
function StatusMessage({ tone, text }: { tone: 'error' | 'success'; text: string }) { const style = tone === 'success' ? 'border-emerald-400/20 bg-emerald-400/10 text-emerald-100' : 'border-red-400/20 bg-red-400/10 text-red-100'; return <div className={`mb-4 rounded-xl border p-3 text-sm ${style}`}>{text}</div>; }
function NodePill({ kind, confidence }: { kind: NodeKind; confidence: string }) { const colors = confidence.toLowerCase() === 'low' || kind === 'PendingReview' ? 'border-red-300/30 bg-red-300/10 text-red-100' : confidence.toLowerCase() === 'medium' ? 'border-amber-300/30 bg-amber-300/10 text-amber-100' : 'border-cyan-300/30 bg-cyan-300/10 text-cyan-100'; return <span className={`rounded-full border px-3 py-1 text-xs font-semibold ${colors}`}>{kind}{confidence ? ` / ${confidence}` : ''}</span>; }
function nodeId(node?: GraphNode | null) { const attrs = node?.attributes || {}; return String(node?.id || node?.tag || attrs.id || attrs.tag || attrs.name || '').trim(); }
function nodeKind(node?: GraphNode | null): NodeKind { const labels = (node?.labels || []).map((label) => String(label).toLowerCase()); const attrs = node?.attributes || {}; const typed = String(attrs.node_type || attrs.entity_type || '').toLowerCase(); const haystack = [...labels, typed].join(' '); if (haystack.includes('pendingreview') || haystack.includes('pending_review')) return 'PendingReview'; if (haystack.includes('maintenanceevent') || haystack.includes('maintenance_event')) return 'MaintenanceEvent'; if (haystack.includes('instrument')) return 'Instrument'; if (haystack.includes('valve')) return 'Valve'; if (haystack.includes('document')) return 'Document'; if (haystack.includes('zone')) return 'Zone'; if (haystack.includes('equipment')) return 'Equipment'; return TAG_PATTERN.test(nodeId(node).toUpperCase()) ? 'Equipment' : 'Node'; }
function confidenceOf(node: GraphNode) { const raw = String(node.attributes?.confidence || node.attributes?.status || '').toLowerCase(); if (raw.includes('low') || raw.includes('pending')) return 'low'; if (raw.includes('medium') || raw.includes('warning')) return 'medium'; if (raw.includes('high') || raw.includes('healthy') || raw.includes('reviewed')) return 'high'; return ''; }
function nodeColors(node: GraphNode) { const confidence = confidenceOf(node); if (confidence === 'low' || nodeKind(node) === 'PendingReview') return { stroke: '#fb7185', fill: '#fb718522', text: '#fecdd3' }; if (confidence === 'medium') return { stroke: '#f59e0b', fill: '#f59e0b22', text: '#fde68a' }; switch (nodeKind(node)) { case 'Equipment': return { stroke: '#34d399', fill: '#34d39922', text: '#a7f3d0' }; case 'Valve': return { stroke: '#fbbf24', fill: '#fbbf2422', text: '#fde68a' }; case 'Instrument': return { stroke: '#a78bfa', fill: '#a78bfa22', text: '#ddd6fe' }; case 'MaintenanceEvent': return { stroke: '#fb7185', fill: '#fb718522', text: '#fecdd3' }; case 'Document': return { stroke: '#60a5fa', fill: '#60a5fa22', text: '#bfdbfe' }; case 'Zone': return { stroke: '#22d3ee', fill: '#22d3ee22', text: '#a5f3fc' }; default: return { stroke: '#94a3b8', fill: '#94a3b822', text: '#cbd5e1' }; } }
function nodeSearchText(node: GraphNode) { return `${nodeId(node)} ${(node.labels || []).join(' ')} ${JSON.stringify(node.attributes || {})}`.toLowerCase(); }
function equipmentFormFromEquipment(item: EquipmentItem): EquipmentForm { const attrs = item.attributes || {}; return { tag: String(item.tag || attrs.id || ''), name: String(item.name || attrs.name || ''), equipment_type: String(item.equipment_type || attrs.type || attrs.equipment_type || 'equipment'), location: String(item.location || attrs.location || ''), description: String(item.description || attrs.description || '') }; }
function equipmentFormFromNode(id: string, node?: GraphNode | null): EquipmentForm { const attrs = node?.attributes || {}; return { tag: id, name: String(attrs.name || ''), equipment_type: String(attrs.type || attrs.equipment_type || 'equipment'), location: String(attrs.location || attrs.zone || ''), description: String(attrs.description || '') }; }
function curvedPath(x1: number, y1: number, x2: number, y2: number, index: number) { const midX = (x1 + x2) / 2; const midY = (y1 + y2) / 2; const dx = x2 - x1; const dy = y2 - y1; const length = Math.max(Math.sqrt(dx * dx + dy * dy), 1); const bend = ((index % 5) - 2) * 9; return `M ${x1} ${y1} Q ${midX - (dy / length) * bend} ${midY + (dx / length) * bend} ${x2} ${y2}`; }
function shortLabel(value: string, max = 12) { return value.length > max ? `${value.slice(0, Math.max(max - 1, 1))}…` : value; }
function relationshipLabel(type: RelationshipType) { return RELATIONSHIP_TYPES.find((item) => item.value === type)?.label || 'Connected to'; }
function humanizeRelationship(value: string) { return value.replace(/_/g, ' ').toLowerCase().replace(/\b\w/g, (letter) => letter.toUpperCase()); }
function formatApiError(err: unknown, fallback: string) { const apiError = err as { status?: number; message?: string } | undefined; return apiError?.status ? `${apiError.message || fallback} (HTTP ${apiError.status})` : apiError?.message || fallback; }
