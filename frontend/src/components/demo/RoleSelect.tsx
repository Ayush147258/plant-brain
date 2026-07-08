'use client';

import Link from 'next/link';
import { ArrowRight, Box, BriefcaseBusiness, Building2, HardHat, ShieldCheck, Sparkles, Wrench } from 'lucide-react';

export type PlantRole = 'technician' | 'manager' | 'head' | 'maintenance' | 'stores' | 'admin';

type RoleConfig = {
  id: PlantRole;
  title: string;
  description: string;
  access: string[];
  icon: React.ComponentType<{ className?: string }>;
  code: string;
  accent: string;
  border: string;
  iconBox: string;
  glow: string;
};

const roles: RoleConfig[] = [
  {
    id: 'technician',
    title: 'Technician',
    description: 'Field-ready access for plant checks, work orders, and equipment questions.',
    access: ['Technician', 'Field ops'],
    icon: HardHat,
    code: 'FIELD OPS',
    accent: 'text-sky-300',
    border: 'border-sky-400/45 hover:border-sky-300/80 hover:shadow-sky-500/25',
    iconBox: 'border-sky-300/45 bg-sky-400/10 text-sky-300 shadow-sky-400/30',
    glow: 'from-sky-500/20 via-transparent to-transparent',
  },
  {
    id: 'manager',
    title: 'Manager',
    description: 'Operations workspace for approvals, performance, alerts, and plant decisions.',
    access: ['Access', 'Manager'],
    icon: BriefcaseBusiness,
    code: 'OPERATIONS',
    accent: 'text-emerald-300',
    border: 'border-emerald-400/45 hover:border-emerald-300/80 hover:shadow-emerald-500/25',
    iconBox: 'border-emerald-300/45 bg-emerald-400/10 text-emerald-300 shadow-emerald-400/30',
    glow: 'from-emerald-500/20 via-transparent to-transparent',
  },
  {
    id: 'head',
    title: 'Plant Head',
    description: 'Executive view for KPIs, risk, compliance posture, and ROI-level insight.',
    access: ['Admin', 'Executive'],
    icon: Building2,
    code: 'EXECUTIVE',
    accent: 'text-violet-300',
    border: 'border-violet-400/45 hover:border-violet-300/80 hover:shadow-violet-500/25',
    iconBox: 'border-violet-300/45 bg-violet-400/10 text-violet-300 shadow-violet-400/30',
    glow: 'from-violet-500/20 via-transparent to-transparent',
  },
  {
    id: 'maintenance',
    title: 'Maintenance',
    description: 'Reliability workspace for asset health, scheduling, failures, and risk trends.',
    access: ['Access', 'Reliability'],
    icon: Wrench,
    code: 'RELIABILITY',
    accent: 'text-amber-300',
    border: 'border-amber-400/45 hover:border-amber-300/80 hover:shadow-amber-500/25',
    iconBox: 'border-amber-300/45 bg-amber-400/10 text-amber-300 shadow-amber-400/30',
    glow: 'from-amber-500/20 via-transparent to-transparent',
  },
  {
    id: 'stores',
    title: 'Stores',
    description: 'Supply workspace for parts, inventory documents, stock risk, and vendors.',
    access: ['Access', 'Supply'],
    icon: Box,
    code: 'SUPPLY',
    accent: 'text-cyan-300',
    border: 'border-cyan-400/45 hover:border-cyan-300/80 hover:shadow-cyan-500/25',
    iconBox: 'border-cyan-300/45 bg-cyan-400/10 text-cyan-300 shadow-cyan-400/30',
    glow: 'from-cyan-500/20 via-transparent to-transparent',
  },
  {
    id: 'admin',
    title: 'Admin',
    description: 'Platform controls for users, integrations, system health, and audit access.',
    access: ['Admin', 'Platform'],
    icon: ShieldCheck,
    code: 'PLATFORM',
    accent: 'text-rose-300',
    border: 'border-rose-400/45 hover:border-rose-300/80 hover:shadow-rose-500/25',
    iconBox: 'border-rose-300/45 bg-rose-400/10 text-rose-300 shadow-rose-400/30',
    glow: 'from-rose-500/20 via-transparent to-transparent',
  },
];

export const roleNames = Object.fromEntries(roles.map((role) => [role.id, role.title])) as Record<PlantRole, string>;

export function RoleSelect({ onSelect }: { onSelect: (role: PlantRole) => void }) {
  return (
    <div className="relative min-h-screen overflow-hidden bg-[#050b12] px-5 py-12 text-white sm:py-16">
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_18%_16%,rgba(14,165,233,0.16),transparent_28%),radial-gradient(circle_at_82%_18%,rgba(20,184,166,0.12),transparent_30%),linear-gradient(180deg,#07111d_0%,#050b12_48%,#07101b_100%)]" />
      <div className="absolute inset-0 opacity-35 [background-image:radial-gradient(rgba(125,211,252,0.32)_1px,transparent_1px)] [background-size:22px_22px]" />
      <div className="absolute inset-x-0 top-0 h-48 bg-gradient-to-b from-cyan-400/10 to-transparent" />

      <div className="relative mx-auto max-w-6xl">
        <header className="mx-auto max-w-3xl text-center">
          <div className="mb-5 inline-flex items-center gap-2 rounded-full border border-cyan-300/35 bg-cyan-300/10 px-4 py-1.5 text-xs font-bold uppercase tracking-[0.16em] text-cyan-200 shadow-[0_0_28px_rgba(34,211,238,0.18)]">
            <Sparkles className="h-3.5 w-3.5" /> Select your workspace
          </div>
          <h1 className="text-4xl font-black leading-[1.08] tracking-normal text-white drop-shadow-[0_10px_28px_rgba(15,23,42,0.65)] md:text-6xl">
            Choose how you experience PlantBrain.
          </h1>
          <p className="mx-auto mt-5 max-w-xl text-base leading-7 text-slate-400 md:text-lg">
            A premium, production-grade role selection for the PlantBrain industrial AI platform in your space.
          </p>
        </header>

        <div className="mt-12 grid gap-7 md:grid-cols-2 xl:grid-cols-3">
          {roles.map((role) => {
            const Icon = role.icon;
            return (
              <Link
                key={role.id}
                href={`/demo?role=${role.id}`}
                onClick={() => onSelect(role.id)}
                className={`group relative min-h-72 overflow-hidden rounded-[22px] border bg-slate-950/56 p-6 text-left shadow-2xl backdrop-blur-xl transition-all duration-300 hover:-translate-y-1 ${role.border}`}
              >
                <div className={`absolute inset-0 bg-gradient-to-br opacity-80 transition-opacity duration-300 group-hover:opacity-100 ${role.glow}`} />
                <div className="absolute inset-px rounded-[21px] bg-gradient-to-br from-white/[0.09] via-white/[0.02] to-black/25" />
                <div className="relative flex h-full min-h-60 flex-col">
                  <div className="flex items-start justify-between gap-4">
                    <span className={`flex h-20 w-20 items-center justify-center rounded-[18px] border shadow-2xl transition-transform duration-300 group-hover:scale-105 ${role.iconBox}`}>
                      <Icon className="h-10 w-10" />
                    </span>
                    <span className={`rounded-md border border-current/30 bg-black/20 px-3 py-1 font-mono text-[11px] font-bold tracking-[0.14em] ${role.accent}`}>
                      {role.code}
                    </span>
                  </div>

                  <div className="mt-7">
                    <h2 className="text-3xl font-black tracking-normal text-white">{role.title}</h2>
                    <p className="mt-3 max-w-xs text-sm leading-6 text-slate-400">{role.description}</p>
                  </div>

                  <div className="mt-auto flex items-end justify-between gap-4 pt-7">
                    <div className="flex flex-wrap gap-2">
                      {role.access.map((item) => (
                        <span key={item} className="rounded-full border border-white/10 bg-white/10 px-3 py-1 text-xs font-semibold text-slate-200 shadow-inner shadow-white/5">
                          {item}
                        </span>
                      ))}
                    </div>
                    <ArrowRight className="h-5 w-5 shrink-0 text-slate-500 transition-all duration-300 group-hover:translate-x-1 group-hover:text-white" />
                  </div>
                </div>
              </Link>
            );
          })}
        </div>
      </div>
    </div>
  );
}
