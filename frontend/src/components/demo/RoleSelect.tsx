'use client';

import Link from 'next/link';
import { ArrowUpRight, Boxes, BriefcaseBusiness, Building2, HardHat, PackageSearch, ShieldCheck, Sparkles } from 'lucide-react';

export type PlantRole = 'technician' | 'manager' | 'head' | 'maintenance' | 'stores' | 'admin';

const roles: Array<{ id: PlantRole; title: string; description: string; access: string[]; icon: React.ComponentType<{ className?: string }>; accent: string; code: string }> = [
  { id: 'technician', title: 'Plant Technician', description: 'Asset monitoring, work orders, and field maintenance', access: ['Assets', 'Work orders', 'Ask'], icon: HardHat, accent: 'text-blue-300 border-blue-400/40', code: 'FIELD OPS' },
  { id: 'manager', title: 'Plant Manager', description: 'Operations overview, approvals, and procurement', access: ['Dashboard', 'Assets', 'Insights'], icon: BriefcaseBusiness, accent: 'text-emerald-300 border-emerald-400/40', code: 'OPERATIONS' },
  { id: 'head', title: 'Plant Head / CFO', description: 'Executive KPIs, cost savings, and ROI analytics', access: ['Dashboard', 'Insights', 'Ask'], icon: Building2, accent: 'text-violet-300 border-violet-400/40', code: 'EXECUTIVE' },
  { id: 'maintenance', title: 'Maintenance Manager', description: 'Asset health, team scheduling, and work planning', access: ['Assets', 'Work orders', 'Risk'], icon: Boxes, accent: 'text-orange-300 border-orange-400/40', code: 'RELIABILITY' },
  { id: 'stores', title: 'Stores / Procurement', description: 'Parts stock, purchase orders, and vendor tracking', access: ['Inventory', 'Documents', 'Orders'], icon: PackageSearch, accent: 'text-cyan-300 border-cyan-400/40', code: 'SUPPLY' },
  { id: 'admin', title: 'System Administrator', description: 'Users, integrations, system health, and audit controls', access: ['Users', 'Integrations', 'Audit'], icon: ShieldCheck, accent: 'text-rose-300 border-rose-400/40', code: 'PLATFORM' },
];

export const roleNames = Object.fromEntries(roles.map((role) => [role.id, role.title])) as Record<PlantRole, string>;

export function RoleSelect({ onSelect }: { onSelect: (role: PlantRole) => void }) {
  return (
    <div className="min-h-screen bg-[#080b10] px-5 pb-16 pt-24 text-white">
      <div className="mx-auto max-w-6xl">
        <header className="grid gap-8 border-b border-white/10 pb-8 lg:grid-cols-[1fr_380px] lg:items-end">
          <div>
            <div className="mb-5 inline-flex items-center gap-2 border border-cyan-400/20 bg-cyan-400/10 px-3 py-1.5 text-xs font-semibold uppercase tracking-[0.16em] text-cyan-200">
              <Sparkles className="h-3.5 w-3.5" /> Role-aware workspace
            </div>
            <h1 className="max-w-2xl text-4xl font-semibold leading-tight md:text-5xl">Choose how you work with PlantBrain.</h1>
          </div>
          <p className="text-sm leading-6 text-slate-400">Each workspace prioritizes the tools, alerts, and decisions that matter to that position. You can switch roles at any time.</p>
        </header>
        <div className="mt-8 grid gap-4 md:grid-cols-2 xl:grid-cols-3">
          {roles.map((role) => {
            const Icon = role.icon;
            return (
              <Link
                key={role.id}
                href={`/demo?role=${role.id}`}
                onClick={() => onSelect(role.id)}
                className="group relative min-h-64 overflow-hidden border border-white/10 bg-[#0e131b] p-6 text-left transition hover:-translate-y-0.5 hover:border-white/25 hover:bg-[#121925]"
              >
                <div className="flex items-start justify-between">
                  <span className={`flex h-12 w-12 items-center justify-center border bg-black/20 ${role.accent}`}><Icon className="h-6 w-6" /></span>
                  <span className="font-mono text-[10px] tracking-[0.18em] text-slate-600">{role.code}</span>
                </div>
                <div className="mt-8">
                  <h2 className="text-xl font-semibold">{role.title}</h2>
                  <p className="mt-2 text-sm leading-6 text-slate-400">{role.description}</p>
                  <div className="mt-5 flex flex-wrap gap-2">
                    {role.access.map((item) => <span key={item} className="border border-white/10 bg-white/[0.04] px-2 py-1 text-[11px] text-slate-300">{item}</span>)}
                  </div>
                </div>
                <ArrowUpRight className="absolute bottom-6 right-6 h-5 w-5 text-slate-600 transition group-hover:text-cyan-300" />
              </Link>
            );
          })}
        </div>
      </div>
    </div>
  );
}