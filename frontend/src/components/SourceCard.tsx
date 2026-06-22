import React from 'react';
import { SourceCitation } from '@/lib/api';

interface SourceCardProps {
  citation: SourceCitation;
}

export default function SourceCard({ citation }: SourceCardProps) {
  const getBadgeClasses = (type: string) => {
    const base = "badge border";
    switch (type.toLowerCase()) {
      case 'manual': return `${base} bg-accent-cyan/10 text-accent-cyan border-accent-cyan/20`;
      case 'procedure': return `${base} bg-accent-green/10 text-accent-green border-accent-green/20`;
      case 'work_order': return `${base} bg-accent-orange/10 text-accent-orange border-accent-orange/20`;
      case 'regulation': return `${base} bg-accent-red/10 text-accent-red border-accent-red/20`;
      case 'inspection': return `${base} bg-yellow-500/10 text-yellow-500 border-yellow-500/20`;
      default: return `${base} bg-accent-cyan/10 text-accent-cyan border-accent-cyan/20`;
    }
  };

  const score = citation.freshness_score;
  const isStale = score < 0.6;
  const freshnessColor = score >= 0.8 ? 'bg-accent-green' : score >= 0.5 ? 'bg-yellow-500' : 'bg-accent-red';

  return (
    <div className="card text-sm mb-4">
      <div className="flex flex-wrap items-center justify-between gap-3 mb-3">
        <div className="flex items-center gap-3">
          <span className="font-semibold text-text-primary text-base">{citation.document_title}</span>
          <span className={getBadgeClasses(citation.source_type)}>
            {citation.source_type.replace('_', ' ')}
          </span>
        </div>
        
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-1.5 px-2 py-1 rounded-md bg-surface-raised border border-border">
            <span className={`w-2 h-2 rounded-full ${freshnessColor}`}></span>
            <span className="font-mono text-xs text-text-secondary">{Math.round(score * 100)}% fresh</span>
          </div>
          {isStale && (
            <span className="text-accent-orange font-bold text-xs flex items-center gap-1.5 bg-accent-orange/10 px-2 py-1 rounded-md border border-accent-orange/30 shadow-sm">
              <span className="text-base leading-none">⚠</span> Stale source
            </span>
          )}
        </div>
      </div>
      
      <div className="font-mono text-xs text-text-muted bg-surface-raised p-3 rounded-md border-l-2 border-l-border mb-3 leading-relaxed">
        "{citation.excerpt}"
      </div>
      
      <div className="text-xs text-text-secondary font-medium">
        Ref: <span className="text-text-primary">{citation.page_or_section}</span>
      </div>
    </div>
  );
}
