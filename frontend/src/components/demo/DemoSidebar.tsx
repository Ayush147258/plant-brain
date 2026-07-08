'use client';

import type { ComponentType } from 'react';
import { useState } from 'react';
import { BrainCircuit, CheckCircle2 } from 'lucide-react';
import type { CompletionState, DemoStep } from './DemoShell';

type StepConfig = { id: DemoStep; label: string; icon: ComponentType<{ className?: string }> };

export function DemoSidebar({ steps, activeStep, completion, onSelect }: { steps: StepConfig[]; activeStep: DemoStep; completion: CompletionState; onSelect: (step: DemoStep) => void }) {
  const [expanded, setExpanded] = useState(false);

  return (
    <aside
      className={`hidden shrink-0 border-r border-white/10 bg-[#070a11] transition-[width,padding] duration-300 ease-out lg:block ${expanded ? 'w-72 p-5' : 'w-16 px-3 py-5'}`}
      onClick={() => setExpanded(true)}
      onMouseLeave={() => setExpanded(false)}
    >
      <div className={`mb-8 flex items-center gap-3 ${expanded ? '' : 'justify-center'}`}>
        <button
          type="button"
          aria-label="Expand PlantBrain demo navigation"
          className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-cyan-400 text-slate-950 shadow-lg shadow-cyan-400/20 transition-transform duration-300 hover:scale-105"
          onClick={() => setExpanded(true)}
        >
          <BrainCircuit className="h-6 w-6" />
        </button>
        <div className={`min-w-0 overflow-hidden transition-all duration-300 ${expanded ? 'w-40 opacity-100' : 'w-0 opacity-0'}`}>
          <div className="text-lg font-bold tracking-tight text-white">PlantBrain</div>
          <div className="whitespace-nowrap text-xs text-slate-500">Judge workflow</div>
        </div>
      </div>
      <nav className="space-y-2">
        {steps.map((step, index) => {
          const Icon = step.icon;
          const active = step.id === activeStep;
          return (
            <button
              key={step.id}
              onClick={() => { setExpanded(true); onSelect(step.id); }}
              title={expanded ? undefined : step.label}
              aria-label={step.label}
              className={`group relative flex w-full items-center rounded-xl border py-3 text-left text-sm transition-all duration-300 ${expanded ? 'gap-3 px-3' : 'justify-center px-0'} ${active ? 'border-cyan-400/50 bg-cyan-400/10 text-white shadow-lg shadow-cyan-950/20' : 'border-white/5 bg-white/[0.02] text-slate-400 hover:border-white/15 hover:bg-white/[0.05] hover:text-slate-100'}`}
            >
              <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-white/[0.06]"><Icon className="h-4 w-4" /></span>
              <span className={`min-w-0 flex-1 overflow-hidden transition-all duration-300 ${expanded ? 'w-40 opacity-100' : 'w-0 opacity-0'}`}>
                <span className="block whitespace-nowrap text-[10px] uppercase tracking-[0.18em] text-slate-500">Step {String(index + 1).padStart(2, '0')}</span>
                <span className="block truncate font-medium">{step.label}</span>
              </span>
              {completion[step.id] && (expanded
                ? <CheckCircle2 className="h-4 w-4 shrink-0 text-emerald-300" />
                : <span className="absolute right-1.5 top-1.5 h-2 w-2 rounded-full bg-emerald-300 shadow-[0_0_10px_rgba(110,231,183,0.8)]" />
              )}
            </button>
          );
        })}
      </nav>
    </aside>
  );
}
