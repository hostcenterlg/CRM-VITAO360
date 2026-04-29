'use client';
// frontend/src/components/ui/MetaWidget.tsx
// Sidebar bottom widget — meta mensal com gradient verde Vitao
import { cn } from '@/lib/cn';

export interface MetaWidgetProps {
  meta: number;
  realizado: number;
  mes: string;
  diasRestantes?: number;
  format?: (n: number) => string;
  className?: string;
  collapsed?: boolean;
}

function brl(n: number): string {
  if (n >= 1_000_000) return `R$ ${(n / 1_000_000).toFixed(1)}M`;
  if (n >= 1_000) return `R$ ${(n / 1_000).toFixed(0)}K`;
  return `R$ ${n.toFixed(0)}`;
}

export function MetaWidget({
  meta,
  realizado,
  mes,
  diasRestantes,
  format = brl,
  className,
  collapsed,
}: MetaWidgetProps) {
  const safeMeta = Math.max(1, meta);
  const pct = Math.max(0, Math.min(100, Math.round((realizado / safeMeta) * 100)));

  if (collapsed) {
    return (
      <div
        className={cn(
          'relative w-9 h-9 mx-auto rounded-lg bg-gradient-to-br from-vitao-green to-vitao-darkgreen flex items-center justify-center text-white text-xs font-bold',
          className,
        )}
        title={`Meta ${mes}: ${pct}%`}
      >
        {pct}%
      </div>
    );
  }

  return (
    <div
      className={cn(
        'rounded-xl p-3 bg-gradient-to-br from-vitao-green to-vitao-darkgreen text-white shadow-sm',
        className,
      )}
    >
      <div className="flex items-center justify-between mb-1">
        <span className="text-xs uppercase tracking-wider opacity-80 font-semibold">
          Meta {mes}
        </span>
        <span className="text-xs font-bold tabular-nums">{pct}%</span>
      </div>
      <div className="text-sm font-bold tabular-nums">{format(realizado)}</div>
      <div className="text-xs opacity-75 tabular-nums">de {format(meta)}</div>
      <div className="mt-2 h-1.5 bg-white/25 rounded-full overflow-hidden">
        <div
          className="h-full bg-white rounded-full transition-[width] duration-500"
          style={{ width: `${pct}%` }}
          role="progressbar"
          aria-valuenow={pct}
          aria-valuemin={0}
          aria-valuemax={100}
          aria-label={`Meta ${mes}: ${pct}%`}
        />
      </div>
      {typeof diasRestantes === 'number' && (
        <div className="text-xs opacity-75 mt-1">
          {diasRestantes} dia{diasRestantes !== 1 ? 's' : ''} restante{diasRestantes !== 1 ? 's' : ''}
        </div>
      )}
    </div>
  );
}
