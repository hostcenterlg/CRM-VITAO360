// frontend/src/components/ui/ScoreBar.tsx
// Score bar 0-100 with color gradient: red(<40) yellow(<70) green(>=70)
// Server-safe (no 'use client')
import { cn } from '@/lib/cn';

export interface ScoreBarProps {
  score: number;
  showLabel?: boolean;
  showPercent?: boolean;
  height?: 'sm' | 'md' | 'lg';
  className?: string;
  trackClassName?: string;
  ariaLabel?: string;
}

const HEIGHT_CLASSES = {
  sm: 'h-1.5',
  md: 'h-2',
  lg: 'h-3',
};

function scoreColor(score: number): string {
  if (score >= 70) return 'bg-green-500';
  if (score >= 40) return 'bg-yellow-400';
  return 'bg-red-500';
}

export function ScoreBar({
  score,
  showLabel = true,
  showPercent = false,
  height = 'md',
  className,
  trackClassName,
  ariaLabel,
}: ScoreBarProps) {
  const clamped = Math.max(0, Math.min(100, Math.round(score ?? 0)));
  const color = scoreColor(clamped);
  return (
    <div
      className={cn('flex items-center gap-2 w-full', className)}
      role="meter"
      aria-valuenow={clamped}
      aria-valuemin={0}
      aria-valuemax={100}
      aria-label={ariaLabel ?? `Score: ${clamped}`}
    >
      <div
        className={cn(
          'flex-1 bg-gray-100 rounded-full overflow-hidden',
          HEIGHT_CLASSES[height],
          trackClassName,
        )}
      >
        <div
          className={cn('h-full rounded-full transition-[width] duration-300', color)}
          style={{ width: `${clamped}%` }}
        />
      </div>
      {showLabel && (
        <span className="text-xs font-semibold text-gray-700 tabular-nums w-8 text-right">
          {clamped}{showPercent && '%'}
        </span>
      )}
    </div>
  );
}
