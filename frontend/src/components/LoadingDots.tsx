import React from 'react';

interface LoadingDotsProps {
  label?: string;
}

export default function LoadingDots({ label = "Thinking" }: LoadingDotsProps) {
  return (
    <div className="flex items-center gap-2 text-text-secondary text-sm font-medium">
      <span>{label}</span>
      <div className="flex gap-1">
        <div className="w-1.5 h-1.5 rounded-full bg-accent-cyan animate-bounce" style={{ animationDelay: '0ms' }}></div>
        <div className="w-1.5 h-1.5 rounded-full bg-accent-cyan animate-bounce" style={{ animationDelay: '150ms' }}></div>
        <div className="w-1.5 h-1.5 rounded-full bg-accent-cyan animate-bounce" style={{ animationDelay: '300ms' }}></div>
      </div>
    </div>
  );
}
