'use client';

import { AlertTriangle, BellRing, CheckCircle2, ClipboardCheck, GitFork, Gauge, RefreshCw, ShieldAlert, Target } from 'lucide-react';
import type { ComponentType, ReactNode } from 'react';
import { useEffect, useState } from 'react';
import { getFailureClusters, getFailureIntelligence, getOverdueInspections, getRiskSummary } from '@/lib/plantbrain-api';
import type { FailureIntelligenceResponse, RiskSummaryResponse } from '@/types/plantbrain';

type EvidenceRecord = Record<string, unknown>;

export function RiskDashboardPanel({ onComplete }: { onComplete: () => void }) {
  const [summary, setSummary] = useState<RiskSummaryResponse | null>(null);
  const [intelligence, setIntelligence] = useState<FailureIntelligenceResponse | null>(null);
  const [clusters, setClusters] = useState<EvidenceRecord[]>([]);
  const [overdue, setOverdue] = useState<EvidenceRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const refresh = async () => {
    setLoading(true);
    setError('');
    try {
      const [risk, intelligenceResponse, clusterResponse, overdueResponse] = await Promise.all([
        getRiskSummary(),
        getFailureIntelligence(),
        getFailureClusters(2),
        getOverdueInspections(180),
      ]);
      const clusterItems = asRecordArray(clusterResponse.failure_clusters || clusterResponse.clusters || []);
      const overdueItems = asRecordArray(
        overdueResponse.overdue_inspections || overdueResponse.overdue || overdueResponse.inspections || risk.critical_overdue || []
      );
      setSummary(risk);
      setIntelligence(intelligenceResponse);
      setClusters(clusterItems);
      setOverdue(overdueItems);
      onComplete();
    } catch (err: unknown) {
      setError(formatApiError(err, 'Failed to load risk intelligence.'));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { refresh(); }, []);

  const warnings = asRecordArray(intelligence?.warnings || []);
  const qmsSignals = asRecordArray(intelligence?.qms_signals || []);
  const systemicPatterns = asRecordArray(intelligence?.systemic_patterns || []);
  const validationMetrics = asRecordArray(intelligence?.validation_metrics || []);
  const coverage = intelligence?.source_coverage || {};

  return (
    <div className="space-y-5">
      <section className="rounded-3xl border border-white/10 bg-white/[0.04] p-5 shadow-2xl shadow-black/20">
        <div className="mb-5 flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
          <div>
            <div className="text-xs font-semibold uppercase tracking-[0.2em] text-cyan-300">Step 06 - Failure intelligence</div>
            <h2 className="mt-2 text-2xl font-semibold text-white">Lessons learned and proactive warnings</h2>
            <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-400">
              PlantBrain links incident patterns, near-miss language, QMS review gaps, and equipment graph context before the next team repeats the same failure.
            </p>
          </div>
          <button onClick={refresh} className="inline-flex items-center gap-2 rounded-xl border border-white/10 px-3 py-2 text-sm text-slate-200 hover:border-cyan-400/50">
            <RefreshCw className="h-4 w-4" /> Refresh
          </button>
        </div>

        {error && <div className="mb-4 rounded-xl border border-red-400/20 bg-red-400/10 p-3 text-sm text-red-100">{error}</div>}

        <div className="grid gap-3 md:grid-cols-5">
          <Metric icon={Gauge} label="Overall risk" value={summary?.overall_risk_level || 'Unknown'} />
          <Metric icon={BellRing} label="Warnings" value={warnings.length} />
          <Metric icon={ShieldAlert} label="Failure clusters" value={clusters.length} />
          <Metric icon={ClipboardCheck} label="QMS signals" value={qmsSignals.length} />
          <Metric icon={GitFork} label="Evidence mode" value={formatEvidenceMode(intelligence?.evidence_mode)} compact />
        </div>
      </section>

      {loading ? (
        <div className="rounded-3xl border border-white/10 bg-white/[0.04] p-8 text-center text-slate-400">Loading failure intelligence...</div>
      ) : (!summary && !intelligence && clusters.length === 0 && overdue.length === 0) ? (
        <div className="rounded-3xl border border-white/10 bg-white/[0.04] p-8 text-center text-slate-400">No pattern data yet. Upload maintenance logs or seed inspection data from backend docs.</div>
      ) : (
        <>
          <FailureIntelligenceCard intelligence={intelligence} warnings={warnings} coverage={coverage} validationMetrics={validationMetrics} />

          <section className="grid gap-5 xl:grid-cols-2">
            <EvidenceList
              title="Systemic patterns"
              icon={Target}
              items={systemicPatterns}
              empty="No systemic patterns returned yet."
              renderItem={(item) => <PatternItem item={item} />}
            />
            <EvidenceList
              title="QMS and compliance signals"
              icon={ClipboardCheck}
              items={qmsSignals}
              empty="No QMS signals returned yet."
              renderItem={(item) => <QmsItem item={item} />}
            />
          </section>

          <section className="grid gap-5 xl:grid-cols-2">
            <EvidenceList
              title="Failure clusters"
              icon={ShieldAlert}
              items={clusters}
              empty="No recurring failure clusters returned."
              renderItem={(item) => <ClusterItem item={item} />}
            />
            <EvidenceList
              title="Overdue inspections"
              icon={AlertTriangle}
              items={overdue}
              empty="No overdue inspections returned."
              renderItem={(item) => <OverdueItem item={item} />}
            />
          </section>
        </>
      )}
    </div>
  );
}

function FailureIntelligenceCard({
  intelligence,
  warnings,
  coverage,
  validationMetrics,
}: {
  intelligence: FailureIntelligenceResponse | null;
  warnings: EvidenceRecord[];
  coverage: Record<string, number>;
  validationMetrics: EvidenceRecord[];
}) {
  const pipeline = intelligence?.pipeline || [];
  return (
    <section className="rounded-3xl border border-amber-300/20 bg-[#15120b] p-5 shadow-2xl shadow-black/20">
      <div className="flex flex-col gap-4 xl:flex-row xl:items-start xl:justify-between">
        <div>
          <div className="inline-flex items-center gap-2 rounded-full border border-amber-300/25 bg-amber-300/10 px-3 py-1 text-xs font-bold uppercase tracking-wide text-amber-100">
            <BellRing className="h-3.5 w-3.5" /> {intelligence?.engine || 'Failure Intelligence Engine'}
          </div>
          <h3 className="mt-3 text-xl font-semibold text-white">Warnings pushed before conditions recur</h3>
          <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-300">{intelligence?.objective || 'PlantBrain is ready to analyze incident, audit, QMS, and graph evidence.'}</p>
        </div>
        <div className="grid min-w-64 grid-cols-2 gap-2 text-xs text-slate-300">
          {Object.entries(coverage).slice(0, 6).map(([key, value]) => (
            <div key={key} className="rounded-2xl border border-white/10 bg-black/20 p-3">
              <div className="text-slate-500">{formatLabel(key)}</div>
              <div className="mt-1 text-lg font-semibold text-white">{value}</div>
            </div>
          ))}
        </div>
      </div>

      {pipeline.length > 0 && (
        <div className="mt-5 grid gap-2 md:grid-cols-5">
          {pipeline.map((step, index) => (
            <div key={step} className="rounded-2xl border border-white/10 bg-black/20 p-3 text-sm text-slate-200">
              <div className="mb-2 text-xs font-semibold text-amber-200">0{index + 1}</div>
              {step}
            </div>
          ))}
        </div>
      )}

      <div className="mt-5 grid gap-4 xl:grid-cols-[1.25fr_0.75fr]">
        <div className="space-y-3">
          {warnings.length === 0 ? (
            <div className="rounded-2xl border border-white/10 bg-black/20 p-4 text-sm text-slate-400">No proactive warnings returned yet.</div>
          ) : warnings.slice(0, 4).map((warning) => <WarningCard key={String(warning.id || warning.title)} warning={warning} />)}
        </div>
        <div className="rounded-2xl border border-white/10 bg-black/20 p-4">
          <div className="mb-3 flex items-center gap-2 text-sm font-semibold text-white"><CheckCircle2 className="h-4 w-4 text-emerald-300" /> Demo validation metrics</div>
          <div className="space-y-2">
            {validationMetrics.map((metric) => (
              <div key={getString(metric, 'name')} className="rounded-xl border border-white/10 bg-white/[0.03] p-3">
                <div className="text-xs uppercase tracking-wide text-slate-500">{getString(metric, 'status', 'tracked')}</div>
                <div className="mt-1 text-sm font-semibold text-white">{getString(metric, 'name')}</div>
                <div className="mt-1 text-sm text-cyan-200">{getString(metric, 'value')}</div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}

function WarningCard({ warning }: { warning: EvidenceRecord }) {
  const tone = toneForSeverity(getString(warning, 'severity'));
  const assets = getStringList(warning.related_assets);
  return (
    <div className={`rounded-2xl border p-4 ${tone.card}`}>
      <div className="flex flex-col gap-2 md:flex-row md:items-start md:justify-between">
        <div>
          <div className={`inline-flex items-center gap-2 rounded-full border px-2.5 py-1 text-xs font-bold uppercase tracking-wide ${tone.badge}`}>
            <AlertTriangle className="h-3.5 w-3.5" /> {getString(warning, 'severity', 'medium')}
          </div>
          <h4 className="mt-3 text-lg font-semibold text-white">{getString(warning, 'title', 'Operational warning')}</h4>
          <p className="mt-1 text-sm text-slate-300">{getString(warning, 'trigger')}</p>
        </div>
        <div className="text-xs text-slate-400">{getString(warning, 'source_type', 'evidence')}</div>
      </div>
      {assets.length > 0 && <AssetChips assets={assets} />}
      <div className="mt-3 grid gap-3 md:grid-cols-2">
        <InfoBlock label="Evidence" value={getString(warning, 'evidence')} />
        <InfoBlock label="Recommended action" value={getString(warning, 'recommended_action')} />
      </div>
    </div>
  );
}

function EvidenceList({
  title,
  icon: Icon,
  items,
  empty,
  renderItem,
}: {
  title: string;
  icon: ComponentType<{ className?: string }>;
  items: EvidenceRecord[];
  empty: string;
  renderItem: (item: EvidenceRecord, index: number) => ReactNode;
}) {
  return (
    <div className="rounded-3xl border border-white/10 bg-white/[0.04] p-5">
      <h3 className="mb-4 flex items-center gap-2 text-lg font-semibold text-white"><Icon className="h-5 w-5 text-amber-300" /> {title}</h3>
      {items.length === 0 ? (
        <div className="rounded-2xl border border-white/10 bg-white/[0.03] p-6 text-sm text-slate-400">{empty}</div>
      ) : (
        <div className="space-y-3">{items.map((item, index) => <div key={`${title}-${index}`}>{renderItem(item, index)}</div>)}</div>
      )}
    </div>
  );
}

function PatternItem({ item }: { item: EvidenceRecord }) {
  const assets = getStringList(item.assets);
  return (
    <div className="rounded-2xl border border-white/10 bg-[#060910] p-4">
      <div className="text-sm font-semibold text-white">{getString(item, 'pattern', 'Pattern')}</div>
      {assets.length > 0 && <AssetChips assets={assets} />}
      <InfoBlock label="Evidence" value={getString(item, 'evidence')} />
      <InfoBlock label="Lesson" value={getString(item, 'lesson')} />
    </div>
  );
}

function QmsItem({ item }: { item: EvidenceRecord }) {
  return (
    <div className="rounded-2xl border border-white/10 bg-[#060910] p-4">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div className="text-sm font-semibold text-white">{getString(item, 'signal', 'QMS signal')}</div>
        <span className="rounded-full border border-cyan-300/20 bg-cyan-300/10 px-2 py-1 text-xs font-semibold uppercase text-cyan-100">{getString(item, 'status', 'open')}</span>
      </div>
      <InfoBlock label="Evidence" value={getString(item, 'evidence')} />
      <InfoBlock label="Owner" value={getString(item, 'owner')} />
    </div>
  );
}

function ClusterItem({ item }: { item: EvidenceRecord }) {
  return (
    <div className="rounded-2xl border border-white/10 bg-[#060910] p-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="text-lg font-semibold text-white">{getString(item, 'equipment_tag', 'Unknown')}</div>
        <span className="rounded-full border border-red-300/20 bg-red-300/10 px-3 py-1 text-xs font-bold text-red-100">Risk {getString(item, 'risk_score', '0')}</span>
      </div>
      <div className="mt-3 grid gap-2 md:grid-cols-3">
        <InfoBlock label="Occurrences" value={getString(item, 'occurrence_count', '0')} />
        <InfoBlock label="Frequency" value={`${getString(item, 'frequency_per_month', '0')}/month`} />
        <InfoBlock label="Last seen" value={trimDate(getString(item, 'last_seen'))} />
      </div>
      <InfoBlock label="AI pattern summary" value={getString(item, 'ai_summary', 'No summary returned.')} />
    </div>
  );
}

function OverdueItem({ item }: { item: EvidenceRecord }) {
  return (
    <div className="rounded-2xl border border-white/10 bg-[#060910] p-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="text-lg font-semibold text-white">{getString(item, 'equipment_tag', 'Unknown')}</div>
        <span className="rounded-full border border-amber-300/20 bg-amber-300/10 px-3 py-1 text-xs font-bold text-amber-100">{getString(item, 'risk_level', 'medium')} risk</span>
      </div>
      <div className="mt-3 grid gap-2 md:grid-cols-3">
        <InfoBlock label="Last inspection" value={trimDate(getString(item, 'last_inspection_date'))} />
        <InfoBlock label="Days since" value={getString(item, 'days_since_last_inspection', '0')} />
        <InfoBlock label="Overdue by" value={`${getString(item, 'overdue_by_days', '0')} days`} />
      </div>
    </div>
  );
}

function Metric({ icon: Icon, label, value, compact = false }: { icon: ComponentType<{ className?: string }>; label: string; value: unknown; compact?: boolean }) {
  return (
    <div className="rounded-2xl border border-white/10 bg-white/[0.03] p-4">
      <div className="flex items-center gap-2 text-xs uppercase tracking-wide text-slate-500"><Icon className="h-4 w-4 text-cyan-300" /> {label}</div>
      <div className={`mt-2 font-semibold text-white ${compact ? 'text-base leading-tight' : 'text-2xl'}`}>{String(value)}</div>
    </div>
  );
}

function InfoBlock({ label, value }: { label: string; value: string }) {
  if (!value) return null;
  return (
    <div className="mt-3 rounded-xl border border-white/10 bg-white/[0.03] p-3">
      <div className="text-xs uppercase tracking-wide text-slate-500">{label}</div>
      <div className="mt-1 text-sm leading-5 text-slate-200">{value}</div>
    </div>
  );
}

function AssetChips({ assets }: { assets: string[] }) {
  return <div className="mt-3 flex flex-wrap gap-2">{assets.map((asset) => <span key={asset} className="rounded-full border border-cyan-300/20 bg-cyan-300/10 px-2.5 py-1 text-xs font-semibold text-cyan-100">{asset}</span>)}</div>;
}

function asRecordArray(value: unknown): EvidenceRecord[] {
  if (!Array.isArray(value)) return [];
  return value.filter((item): item is EvidenceRecord => typeof item === 'object' && item !== null && !Array.isArray(item));
}

function getString(record: EvidenceRecord, key: string, fallback = ''): string {
  const value = record[key];
  if (value === null || value === undefined || value === '') return fallback;
  if (typeof value === 'number') return Number.isFinite(value) ? String(value) : fallback;
  if (typeof value === 'string') return value;
  if (Array.isArray(value)) return value.map((item) => String(item)).join(', ');
  return String(value);
}

function getStringList(value: unknown): string[] {
  if (!Array.isArray(value)) return [];
  return value.map((item) => String(item)).filter(Boolean);
}

function toneForSeverity(severity: string) {
  const normalized = severity.toLowerCase();
  if (normalized.includes('critical')) return { card: 'border-red-400/30 bg-red-500/10', badge: 'border-red-300/30 bg-red-300/10 text-red-100' };
  if (normalized.includes('high')) return { card: 'border-amber-400/30 bg-amber-500/10', badge: 'border-amber-300/30 bg-amber-300/10 text-amber-100' };
  return { card: 'border-cyan-400/20 bg-cyan-500/10', badge: 'border-cyan-300/30 bg-cyan-300/10 text-cyan-100' };
}

function formatEvidenceMode(value: unknown): string {
  const text = String(value || 'live').replace(/_/g, ' ');
  return text.length > 28 ? `${text.slice(0, 25)}...` : text;
}

function formatLabel(value: string): string {
  return value.replace(/_/g, ' ').replace(/\b\w/g, (char) => char.toUpperCase());
}

function trimDate(value: string): string {
  if (!value) return 'Unknown';
  return value.slice(0, 10);
}

function formatApiError(err: unknown, fallback: string): string {
  if (err instanceof Error) {
    const maybeStatus = (err as Error & { status?: number }).status;
    return maybeStatus ? `${err.message} (HTTP ${maybeStatus})` : err.message || fallback;
  }
  return fallback;
}
