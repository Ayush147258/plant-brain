import type { SourceItem } from '@/types/plantbrain';

export function SourceCitations({ sources }: { sources?: SourceItem[] }) {
  const items = sources || [];
  if (items.length === 0) return <div className="rounded-xl border border-amber-400/20 bg-amber-400/10 p-3 text-sm text-amber-100">No citations returned by backend.</div>;
  return (
    <div className="space-y-2">
      {items.map((source, index) => (
        <div key={index} className="rounded-xl border border-white/10 bg-white/[0.04] p-3">
          <div className="text-sm font-semibold text-cyan-100">{source.filename || source.document || source.source || `Source ${index + 1}`}</div>
          <div className="mt-1 text-xs text-slate-400">{source.section || source.page_or_section || (source.page_number ? `Page ${source.page_number}` : source.chunk_index !== undefined ? `Chunk ${source.chunk_index + 1}` : 'Referenced context')}</div>
          <p className="mt-2 text-sm leading-6 text-slate-300">{source.snippet || source.text_preview || source.excerpt || 'Citation metadata returned without preview text.'}</p>
        </div>
      ))}
    </div>
  );
}