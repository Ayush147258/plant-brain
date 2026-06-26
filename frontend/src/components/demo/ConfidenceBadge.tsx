export function ConfidenceBadge({ confidence }: { confidence?: number | string }) {
  const text = confidence === undefined || confidence === null ? 'Unknown' : String(confidence);
  const numeric = typeof confidence === 'number' ? confidence : Number.NaN;
  const tone = text.toLowerCase().includes('high') || numeric >= 0.8 ? 'border-emerald-400/30 bg-emerald-400/10 text-emerald-100' : text.toLowerCase().includes('low') || numeric < 0.5 ? 'border-red-400/30 bg-red-400/10 text-red-100' : 'border-amber-400/30 bg-amber-400/10 text-amber-100';
  return <span className={`inline-flex rounded-full border px-2.5 py-1 text-xs font-semibold ${tone}`}>Confidence: {text}</span>;
}