'use client';

import { RefreshCw, ServerCrash, ShieldCheck, TriangleAlert } from 'lucide-react';
import { useEffect, useState } from 'react';
import { deepHealthCheck, healthCheck } from '@/lib/plantbrain-api';

type Status = 'loading' | 'healthy' | 'degraded' | 'offline';

export function BackendStatus() {
  const [status, setStatus] = useState<Status>('loading');
  const [message, setMessage] = useState('Checking backend...');
  const [checkedAt, setCheckedAt] = useState('');
  const [loading, setLoading] = useState(false);

  const check = async () => {
    setLoading(true);
    try {
      const health = await healthCheck();
      try {
        const deep = await deepHealthCheck();
        const deepStatus = String(deep.status || '').toLowerCase();
        setStatus(deepStatus.includes('degraded') ? 'degraded' : 'healthy');
        setMessage(`Health: ${health.status || 'ok'} · Deep: ${deep.status || 'healthy'}`);
      } catch {
        setStatus('degraded');
        setMessage(`Health endpoint OK. Deep health unavailable.`);
      }
    } catch (error: any) {
      setStatus('offline');
      setMessage(error?.message || 'Backend is offline. Start FastAPI or set NEXT_PUBLIC_PLANTBRAIN_API_URL.');
    } finally {
      setCheckedAt(new Date().toLocaleTimeString());
      setLoading(false);
    }
  };

  useEffect(() => {
    check();
  }, []);

  const Icon = status === 'offline' ? ServerCrash : status === 'degraded' ? TriangleAlert : ShieldCheck;
  const tone = status === 'offline' ? 'border-red-400/30 bg-red-400/10 text-red-100' : status === 'degraded' ? 'border-amber-400/30 bg-amber-400/10 text-amber-100' : 'border-emerald-400/30 bg-emerald-400/10 text-emerald-100';

  return (
    <div className="rounded-2xl border border-white/10 bg-white/[0.04] p-4 shadow-2xl shadow-black/20">
      <div className="mb-3 flex items-center justify-between gap-3"><div className="text-sm font-semibold text-white">Backend Status</div><button onClick={check} disabled={loading} className="rounded-lg border border-white/10 p-2 text-slate-300 transition hover:text-white disabled:opacity-50"><RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} /></button></div>
      <div className={`rounded-xl border px-3 py-3 ${tone}`}><div className="flex items-center gap-2 text-sm font-semibold"><Icon className="h-4 w-4" /> {status === 'loading' ? 'Checking' : status[0].toUpperCase() + status.slice(1)}</div><p className="mt-2 text-xs leading-5 opacity-90">{message}</p>{checkedAt && <p className="mt-2 text-[11px] opacity-70">Last checked {checkedAt}</p>}</div>
    </div>
  );
}