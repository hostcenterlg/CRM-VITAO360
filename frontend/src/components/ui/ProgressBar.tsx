// frontend/src/components/ui/ProgressBar.tsx
// Meta vs realizado progress bar — fill always vitao-green (unless warnAt/dangerAt)
// Server-safe (no 'use client')
import { cn } from '@/lib/cn';

export interface ProgressBarProps {
  current: number;
  total: number;
  label?: string;
  showPercent?: boolean;
  showFraction?: boolean;
  format?: (n: number) => string;
  height?: 'sm' | 'md' | 'lg';
  warnAt?: number;
  dangerAt?: number;
  className?: string;
}

const HEIGHT_CLASSES = {
  sm: 'h-1.5',
  md: 'h-2',
  lg: 'h-3',
};

export function ProgressBar({
  current,
  total,
  label,
  showPercent = true,
  showFraction = false,
  format,
  height = 'lg',
  warnAt,
  dangerAt,
  className,
}: ProgressBarProps) {
  const safeTotal = Math.max(1, total);
  const pct = Math.max(0, Math.min(100, Math.round((current / safeTotal) * 100)));

  let color = 'bg-vitao-green';
  if (dangerAt != null && pct < dangerAt) color = 'bg-red-500';
  else if (warnAt != null && pct < warnAt) color = 'bg-yellow-400';

  const fmt = format ?? ((n: number) => n.toLocaleString('pt-BR'));

  return (
    <div className={cn('w-full', className)}>
      {(label || showPercent || showFraction) && (
        <div className="flex items-center justify-between mb-1 text-xs">
          {label && <span className="font-semibold text-gray-700">{label}</span>}
          <span className="font-semibold text-gray-900 tabular-nums">
            {showFraction && `${fmt(current)} / ${fmt(total)}`}
            {showFraction && showPercent && '  '}
            {showPercent && `${pct}%`}
          </span>
        </div>
      )}
      <div className={cn('w-full bg-gray-100 rounded-full overflow-hidden', HEIGHT_CLASSES[height])}>
        <div
          className={cn('h-full rounded-full transition-[width] duration-500', color)}
          style={{ width: `${pct}%` }}
          role="progressbar"
          aria-valuenow={pct}
          aria-valuemin={0}
          aria-valuemax={100}
          aria-label={label ?? `Progresso: ${pct}%`}
        />
      </div>
    </div>
  );
}
