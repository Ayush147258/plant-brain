'use client';

import React, { useEffect, useState } from 'react';

interface ConfidenceBarProps {
  score: number; // 0.0 to 1.0
  modelUsed: string;
}

export default function ConfidenceBar({ score, modelUsed }: ConfidenceBarProps) {
  const [width, setWidth] = useState(0);

  useEffect(() => {
    // Animate from 0 to target score on mount
    const timeout = setTimeout(() => {
      setWidth(score * 100);
    }, 100);
    return () => clearTimeout(timeout);
  }, [score]);

  const getColor = (s: number) => {
    if (s >= 0.8) return 'bg-accent-green';
    if (s >= 0.5) return 'bg-yellow-500';
    return 'bg-accent-red';
  };

  const barColor = getColor(score);
  const percentage = Math.round(score * 100);
  const isFallback = modelUsed === 'gemini-3.5-flash';
  const displayModel = isFallback ? 'gemini-3.5-flash ⚡' : 'claude-sonnet-4-6';

  return (
    <div className="w-full">
      <div className="flex justify-between items-center mb-1.5 text-xs font-medium text-text-secondary">
        <span>Confidence Score</span>
        <span className="text-text-primary font-mono">{percentage}%</span>
      </div>
      <div className="h-2 w-full bg-surface-raised rounded-full overflow-hidden border border-border">
        <div 
          className={`h-full transition-all duration-1000 ease-out ${barColor}`} 
          style={{ width: `${width}%` }}
        />
      </div>
      <div className="mt-1.5 text-[10px] text-text-muted text-right font-mono tracking-wide uppercase">
        Model: {displayModel}
      </div>
    </div>
  );
}

