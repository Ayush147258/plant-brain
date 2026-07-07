'use client';

import { Activity, AlertTriangle, CheckCircle2, Database, GitMerge, RefreshCw, SearchCheck, ShieldCheck } from 'lucide-react';
import { useEffect, useState } from 'react';
import { deepHealthCheck, getGraphStats, getPipelineOverview } from '@/lib/plantbrain-api';

type Stage = { name: string; status: string; message: string; updated_at?: string };
type Run = { document_id: string; filename: string; stages: Stage[]; updated_at?: string };

const stageLabels: Record<string, string> = {
  upload_received: 'Upload received',
  file_parsed: 'File parsed',
  gemini_multimodal_schema_extraction: 'Gemini schema extraction',
  json_validation: 'JSON validation',
  confidence_scoring: 'Confidence scoring',
  neo4j_merge: 'Neo4j MERGE',
  vector_index_update: 'Vector index update',
  review_queue: 'Review queue',
  query_readiness: 'Query readiness',
};

export function PipelineDashboardPanel({ onComplete }: { onComplete: () => void }) {
  const [pipeline, setPipeline] = useState<{ runs?: Run[]; metrics?: Record<string, unknown>; graph_backend?: string; neo4j_configured?: boolean }>({});
  const [graph, setGraph] = useState<Record<string, unknown>>({});
  const [health, setHealth] = useState<Record<string, unknown>>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const refresh = async () => {
    setLoading(true);
    setError('');
    try {
      const [pipelineResponse, graphResponse, healthResponse] = await Promise.all([
        getPipelineOverview(),
        getGraphStats(),
        deepHealthCheck(),
      ]);
      setPipeline(pipelineResponse as typeof pipeline);
      setGraph(graphResponse as Record<string, unknown>);
      setHealth(healthResponse as Record<string, unknown>);
      onComplete();
    } catch (err: any) {
      setError(err?.status ? `${err.message} (HTTP ${err.status})` : err?.message || 'Failed to load pipeline evidence.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    refresh();
    const interval = window.setInterval(refresh, 10000);
    return () => window.clearInterval(interval);
  }, []);

  const metrics = pipeline.metrics || {};
  const runs = pipeline.runs || [];
  const latest = runs[0];
  const checks = (health.checks || {}) as Record<string, boolean>;

  return (
    <div className="space-y-5">
      <section className="rounded-3xl border border-white/10 bg-white/[0.04] p-5 shadow-2xl shadow-black/20">
        <div className="mb-5 flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
          <div>
            <div className="text-xs font-semibold uppercase tracking-[0.2em] text-cyan-300">Plant intelligence pipeline</div>
            <h2 className="mt-2 text-2xl font-semibold text-white">Live proof that this is more than an API wrapper</h2>
            <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-400">Every uploaded plant document moves through parsing, Gemini schema extraction, validation, confidence review, Neo4j MERGE, vector indexing, and query readiness.</p>
          </div>
          <button onClick={refresh} disabled={loading} className="inline-flex items-center gap-2 rounded-xl border border-white/10 px-3 py-2 text-sm text-slate-200 hover:border-cyan-400/50 disabled:opacity-50"><RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} /> Refresh</button>
        </div>
        {error && <div className="mb-4 rounded-xl border border-red-400/20 bg-red-400/10 p-3 text-sm text-red-100">{error}</div>}
        <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
          <Metric icon={Database} label="Graph backend" value={String(pipeline.graph_backend || graph.graph_backend || 'unknown')} tone={pipeline.neo4j_configured ? 'emerald' : 'amber'} />
          <Metric icon={GitMerge} label="Neo4j nodes / edges" value={`${Number(graph.nodes || 0)} / ${Number(graph.edges || 0)}`} tone="cyan" />
          <Metric icon={SearchCheck} label="Vector chunks" value={Number(metrics.total_chunks_created || 0)} tone="cyan" />
          <Metric icon={AlertTriangle} label="Review queue" value={Number(metrics.low_confidence_fields || 0)} tone={Number(metrics.low_confidence_fields || 0) ? 'amber' : 'emerald'} />
          <Metric icon={Activity} label="Documents processed" value={Number(metrics.total_processed || 0)} tone="cyan" />
          <Metric icon={Activity} label="Pages processed" value={Number(metrics.pages_processed || 0)} tone="cyan" />
          <Metric icon={ShieldCheck} label="Equipment extracted" value={Number(metrics.equipment_extracted || 0)} tone="emerald" />
          <Metric icon={CheckCircle2} label="Failed jobs recovered" value={Number(metrics.failed_jobs_recovered || 0)} tone="emerald" />
        </div>
        <div className="mt-4 grid gap-3 md:grid-cols-4">
          {Object.entries({ database: checks.database, vector_store: checks.vector_store, neo4j: checks.neo4j, graph: checks.graph }).map(([key, value]) => (
            <div key={key} className={`rounded-2xl border p-3 text-sm ${value ? 'border-emerald-400/20 bg-emerald-400/10 text-emerald-100' : 'border-amber-400/20 bg-amber-400/10 text-amber-100'}`}>
              <span className="font-semibold capitalize">{key.replace('_', ' ')}</span>
              <span className="float-right">{value ? 'Ready' : 'Needs attention'}</span>
            </div>
          ))}
        </div>
      </section>

      <section className="rounded-3xl border border-white/10 bg-[#0b111b] p-5 shadow-2xl shadow-black/20">
        <div className="mb-4 flex items-center justify-between gap-3">
          <div>
            <div className="text-xs font-semibold uppercase tracking-[0.2em] text-violet-300">Current ingestion run</div>
            <h3 className="mt-2 text-xl font-semibold text-white">{latest?.filename || 'No active or recent document yet'}</h3>
          </div>
          {latest?.document_id && <span className="max-w-xs truncate font-mono text-xs text-slate-500">{latest.document_id}</span>}
        </div>
        {!latest ? <div className="rounded-2xl border border-white/10 bg-white/[0.03] p-8 text-center text-sm text-slate-400">Upload a P&ID, blueprint, or maintenance log to populate the live pipeline.</div> : <div className="grid gap-3 lg:grid-cols-3">
          {latest.stages.map((stage) => <StageCard key={stage.name} stage={stage} />)}
        </div>}
      </section>
    </div>
  );
}

function Metric({ icon: Icon, label, value, tone }: { icon: React.ComponentType<{ className?: string }>; label: string; value: React.ReactNode; tone: 'cyan' | 'emerald' | 'amber' }) {
  const tones = {
    cyan: 'border-cyan-400/20 bg-cyan-400/10 text-cyan-100',
    emerald: 'border-emerald-400/20 bg-emerald-400/10 text-emerald-100',
    amber: 'border-amber-400/20 bg-amber-400/10 text-amber-100',
  };
  return <div className={`rounded-2xl border p-4 ${tones[tone]}`}><Icon className="h-5 w-5 opacity-80" /><div className="mt-4 text-2xl font-semibold">{value}</div><div className="mt-1 text-xs uppercase tracking-[0.14em] opacity-70">{label}</div></div>;
}

function StageCard({ stage }: { stage: Stage }) {
  const status = stage.status || 'pending';
  const tone = status === 'completed' ? 'border-emerald-400/20 bg-emerald-400/10 text-emerald-100' : status === 'failed' ? 'border-red-400/20 bg-red-400/10 text-red-100' : status === 'needs_review' ? 'border-amber-400/20 bg-amber-400/10 text-amber-100' : status === 'running' ? 'border-cyan-400/20 bg-cyan-400/10 text-cyan-100' : 'border-white/10 bg-white/[0.03] text-slate-300';
  return <div className={`rounded-2xl border p-4 ${tone}`}><div className="flex items-center justify-between gap-3"><span className="font-semibold text-white">{stageLabels[stage.name] || stage.name}</span><span className="rounded-full border border-white/10 px-2 py-1 text-[10px] uppercase tracking-wider">{status}</span></div><p className="mt-3 text-xs leading-5 opacity-80">{stage.message}</p></div>;
}
