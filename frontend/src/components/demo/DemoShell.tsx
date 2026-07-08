'use client';

import { Activity, ArrowLeft, BookOpen, CheckCircle2, ClipboardCheck, FileUp, GitFork, LayoutDashboard, Mic2, Radar, Search, ShieldCheck, UserRoundCog } from 'lucide-react';
import Link from 'next/link';
import { useMemo, useState } from 'react';
import { API_BASE_URL } from '@/lib/plantbrain-api';
import { AdminConsolePanel } from './AdminConsolePanel';
import { AskPlantBrainPanel } from './AskPlantBrainPanel';
import { BackendStatus } from './BackendStatus';
import { CompliancePanel } from './CompliancePanel';
import { DemoHeader } from './DemoHeader';
import { DemoSidebar } from './DemoSidebar';
import { DocumentIngestionPanel } from './DocumentIngestionPanel';
import { EquipmentGraphPanel } from './EquipmentGraphPanel';
import { ExpertCapturePanel } from './ExpertCapturePanel';
import { RiskDashboardPanel } from './RiskDashboardPanel';
import { OperationsOverview } from './OperationsOverview';
import { PipelineDashboardPanel } from './PipelineDashboardPanel';
import { PlantRole, RoleSelect, roleNames } from './RoleSelect';

export type DemoStep = 'admin' | 'overview' | 'pipeline' | 'documents' | 'graph' | 'ask' | 'compliance' | 'voice' | 'risk';
export type CompletionState = Record<DemoStep, boolean>;

const steps: Array<{ id: DemoStep; label: string; icon: React.ComponentType<{ className?: string }> }> = [
  { id: 'admin', label: 'Administration', icon: ShieldCheck },
  { id: 'overview', label: 'Operations', icon: LayoutDashboard },
  { id: 'pipeline', label: 'AI Pipeline', icon: Activity },
  { id: 'documents', label: 'Connect Documents', icon: FileUp },
  { id: 'graph', label: 'Knowledge Graph', icon: GitFork },
  { id: 'ask', label: 'Ask PlantBrain', icon: Search },
  { id: 'compliance', label: 'Compliance', icon: ClipboardCheck },
  { id: 'voice', label: 'Expert Capture', icon: Mic2 },
  { id: 'risk', label: 'Risk Patterns', icon: Radar },
];

export function DemoShell({ initialRole = null }: { initialRole?: PlantRole | null }) {
  const [role, setRole] = useState<PlantRole | null>(initialRole);
  const [activeStep, setActiveStep] = useState<DemoStep>(initialRole === 'admin' ? 'admin' : 'overview');
  const [completion, setCompletion] = useState<CompletionState>({ admin: false, overview: false, pipeline: false, documents: false, graph: false, ask: false, compliance: false, voice: false, risk: false });
  const [stats, setStats] = useState({ documents: 0, equipment: 0 });

  const roleSteps: Record<PlantRole, DemoStep[]> = {
    technician: ['overview', 'pipeline', 'documents', 'graph', 'ask', 'voice', 'risk'],
    manager: ['overview', 'pipeline', 'documents', 'graph', 'ask', 'compliance', 'risk'],
    head: ['overview', 'pipeline', 'ask', 'compliance', 'risk'],
    maintenance: ['overview', 'pipeline', 'documents', 'graph', 'ask', 'compliance', 'voice', 'risk'],
    stores: ['overview', 'pipeline', 'documents', 'graph', 'risk'],
    admin: ['admin', 'overview', 'pipeline', 'documents', 'graph', 'ask', 'compliance', 'voice', 'risk'],
  };
  const visibleSteps = role ? steps.filter((step) => roleSteps[role].includes(step.id)) : steps;
  const activeIndex = visibleSteps.findIndex((step) => step.id === activeStep);
  const completedCount = useMemo(() => visibleSteps.filter((step) => completion[step.id]).length, [completion, visibleSteps]);
  const showUtilityRail = activeStep !== 'ask';

  const markComplete = (step: DemoStep) => setCompletion((current) => ({ ...current, [step]: true }));

  const panel = {
    admin: <AdminConsolePanel onComplete={() => markComplete('admin')} />,
    overview: role ? <OperationsOverview role={role} onNavigate={setActiveStep} /> : null,
    pipeline: <PipelineDashboardPanel onComplete={() => markComplete('pipeline')} />,
    documents: <div className="space-y-10"><DocumentIngestionPanel onComplete={() => markComplete('documents')} onStatsChange={(count) => setStats((s) => ({ ...s, documents: count }))} /><EquipmentGraphPanel onComplete={() => markComplete('graph')} onStatsChange={(count) => setStats((s) => ({ ...s, equipment: count }))} /><AskPlantBrainPanel onComplete={() => markComplete('ask')} /></div>,
    graph: <EquipmentGraphPanel onComplete={() => markComplete('graph')} onStatsChange={(count) => setStats((s) => ({ ...s, equipment: count }))} />,
    ask: <AskPlantBrainPanel onComplete={() => markComplete('ask')} />,
    compliance: <CompliancePanel onComplete={() => markComplete('compliance')} />,
    voice: <ExpertCapturePanel onComplete={() => markComplete('voice')} onAskAboutNote={() => setActiveStep('ask')} />,
    risk: <RiskDashboardPanel onComplete={() => markComplete('risk')} />,
  }[activeStep];

  if (!role) return <RoleSelect onSelect={(selected) => { setRole(selected); setActiveStep(selected === 'admin' ? 'admin' : 'overview'); markComplete(selected === 'admin' ? 'admin' : 'overview'); }} />;

  return (
    <div className="min-h-screen bg-[#080b12] text-slate-100">
      <div className="flex min-h-screen">
        <DemoSidebar steps={visibleSteps} activeStep={activeStep} completion={completion} onSelect={setActiveStep} />
        <main className="flex min-w-0 flex-1 flex-col">
          <DemoHeader currentStep={activeIndex + 1} totalSteps={visibleSteps.length} completedCount={completedCount} documentsCount={stats.documents} equipmentCount={stats.equipment} />
          <div className="border-b border-white/10 bg-[#0b101a]/80 px-6 py-3 backdrop-blur">
            <div className="flex flex-wrap items-center gap-3 text-xs text-slate-300">
              <button onClick={() => setRole(null)} className="inline-flex items-center gap-2 border border-white/10 bg-white/[0.03] px-3 py-1 text-slate-200"><UserRoundCog className="h-3.5 w-3.5" /> {roleNames[role]} | Switch role</button>
              <span className="inline-flex items-center gap-2 rounded-full border border-cyan-400/20 bg-cyan-400/10 px-3 py-1 font-medium text-cyan-200"><Activity className="h-3.5 w-3.5" /> Recommended judge flow</span>
              {['Upload files', 'Watch AI pipeline', 'Inspect Neo4j graph', 'Ask with citations', 'Run compliance', 'Capture voice', 'View risk'].map((item, index) => (
                <span key={item} className="inline-flex items-center gap-1.5 rounded-full border border-white/10 bg-white/[0.03] px-2.5 py-1"><span className="text-slate-500">{index + 1}</span>{item}</span>
              ))}
            </div>
          </div>
          <div className={`flex min-h-0 flex-1 flex-col gap-5 overflow-auto p-6 ${showUtilityRail ? 'xl:flex-row' : ''}`}>
            <section className="min-w-0 flex-1">{panel}</section>
            {showUtilityRail && <aside className="w-full shrink-0 xl:w-80">
              <div className="sticky top-6 space-y-4">
                <BackendStatus />
                <div className="rounded-2xl border border-white/10 bg-white/[0.04] p-4 shadow-2xl shadow-black/20">
                  <div className="mb-3 flex items-center gap-2 text-sm font-semibold text-white"><BookOpen className="h-4 w-4 text-cyan-300" /> Demo links</div>
                  <div className="grid gap-2 text-sm">
                    <Link className="inline-flex items-center gap-2 rounded-lg border border-white/10 px-3 py-2 text-slate-200 transition hover:border-cyan-400/50 hover:text-white" href="/"><ArrowLeft className="h-4 w-4" /> Back to Landing</Link>
                    <a className="inline-flex items-center gap-2 rounded-lg border border-white/10 px-3 py-2 text-slate-200 transition hover:border-cyan-400/50 hover:text-white" href={`${API_BASE_URL}/docs`} target="_blank" rel="noreferrer"><BookOpen className="h-4 w-4" /> View API Docs</a>
                    <div className="rounded-lg border border-emerald-400/20 bg-emerald-400/10 px-3 py-2 text-xs text-emerald-100"><CheckCircle2 className="mr-1 inline h-3.5 w-3.5" /> {completedCount}/{visibleSteps.length} workflow steps completed</div>
                  </div>
                </div>
              </div>
            </aside>}
          </div>
        </main>
      </div>
    </div>
  );
}


