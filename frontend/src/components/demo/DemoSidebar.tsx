'use client';

import type { ComponentType } from 'react';
import { BrainCircuit, CheckCircle2 } from 'lucide-react';
import type { CompletionState, DemoStep } from './DemoShell';

type StepConfig = { id: DemoStep; label: string; icon: ComponentType<{ className?: string }> };

export function DemoSidebar({ steps, activeStep, completion, onSelect }: { steps: StepConfig[]; activeStep: DemoStep; completion: CompletionState; onSelect: (step: DemoStep) => void }) {
  return (
    <aside className="hidden w-72 shrink-0 border-r border-white/10 bg-[#070a11] p-5 lg:block">
      <div className="mb-8 flex items-center gap-3">
        <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-cyan-400 text-slate-950 shadow-lg shadow-cyan-400/20"><BrainCircuit className="h-6 w-6" /></div>
        <div><div className="text-lg font-bold tracking-tight text-white">PlantBrain</div><div className="text-xs text-slate-500">Judge workflow</div></div>
      </div>
      <nav className="space-y-2">
        {steps.map((step, index) => {
          const Icon = step.icon;
          const active = step.id === activeStep;
          return (
            <button key={step.id} onClick={() => onSelect(step.id)} className={`group flex w-full items-center gap-3 rounded-xl border px-3 py-3 text-left text-sm transition ${active ? 'border-cyan-400/50 bg-cyan-400/10 text-white shadow-lg shadow-cyan-950/20' : 'border-white/5 bg-white/[0.02] text-slate-400 hover:border-white/15 hover:bg-white/[0.05] hover:text-slate-100'}`}>
              <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-white/[0.06]"><Icon className="h-4 w-4" /></span>
              <span className="min-w-0 flex-1"><span className="block text-[10px] uppercase tracking-[0.18em] text-slate-500">Step {String(index + 1).padStart(2, '0')}</span><span className="block truncate font-medium">{step.label}</span></span>
              {completion[step.id] && <CheckCircle2 className="h-4 w-4 text-emerald-300" />}
            </button>
          );
        })}
      </nav>
    </aside>
  );
}