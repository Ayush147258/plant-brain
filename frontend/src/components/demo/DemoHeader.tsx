import { Database, GitFork, ShieldCheck } from 'lucide-react';

export function DemoHeader({ currentStep, totalSteps, completedCount, documentsCount, equipmentCount }: { currentStep: number; totalSteps: number; completedCount: number; documentsCount: number; equipmentCount: number }) {
  return (
    <header className="border-b border-white/10 bg-[#0a0f19]/95 px-6 py-5 backdrop-blur">
      <div className="flex flex-col gap-4 xl:flex-row xl:items-center xl:justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight text-white">PlantBrain Interactive Demo</h1>
          <p className="mt-1 text-sm text-slate-400">Run a real backend-connected plant intelligence workflow</p>
        </div>
        <div className="flex flex-wrap gap-2 text-xs">
          <span className="inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/[0.04] px-3 py-2 text-slate-200"><ShieldCheck className="h-4 w-4 text-emerald-300" /> Step {currentStep}/{totalSteps}</span>
          <span className="inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/[0.04] px-3 py-2 text-slate-200"><Database className="h-4 w-4 text-cyan-300" /> {documentsCount} docs</span>
          <span className="inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/[0.04] px-3 py-2 text-slate-200"><GitFork className="h-4 w-4 text-amber-300" /> {equipmentCount} equipment</span>
          <span className="inline-flex items-center gap-2 rounded-full border border-emerald-400/20 bg-emerald-400/10 px-3 py-2 text-emerald-100">{completedCount}/{totalSteps} complete</span>
        </div>
      </div>
    </header>
  );
}