// frontend/src/components/ui/PriorityPill.tsx
// Priority P0-P7 pill — gradient red -> green
// Server-safe (no 'use client')
import { cn } from '@/lib/cn';
import type { BadgeSize } from './Badge';

export type Prioridade = 'P0' | 'P1' | 'P2' | 'P3' | 'P4' | 'P5' | 'P6' | 'P7';

export interface PriorityPillProps {
  prioridade: Prioridade | string;
  size?: BadgeSize;
  className?: string;
}

const BASE = 'inline-flex items-center font-semibold rounded-full';

const SIZE_CLASSES: Record<BadgeSize, string> = {
  xs: 'text-[10px] px-1.5 py-0 leading-4',
  sm: 'text-xs px-2 py-0.5 leading-5',
  md: 'text-sm px-2.5 py-1 leading-5',
};

// P0=most urgent (red), P7=coldest (very light gray)
const PRIORITY_CLASSES: Record<Prioridade, string> = {
  P0: 'bg-red-600 text-white',
  P1: 'bg-red-500 text-white',
  P2: 'bg-orange-500 text-white',
  P3: 'bg-yellow-400 text-gray-900',
  P4: 'bg-gray-400 text-white',
  P5: 'bg-gray-300 text-gray-700',
  P6: 'bg-gray-200 text-gray-700',
  P7: 'bg-gray-100 text-gray-500',
};

export function PriorityPill({
  prioridade,
  size = 'sm',
  className,
}: PriorityPillProps) {
  const key = String(prioridade ?? '').trim().toUpperCase() as Prioridade;
  const colorClass = PRIORITY_CLASSES[key] ?? 'bg-gray-200 text-gray-600';
  const isUrgent = key === 'P0' || key === 'P1';
  return (
    <span
      className={cn(BASE, SIZE_CLASSES[size], colorClass, isUrgent && 'font-bold', className)}
      aria-label={`Prioridade ${key}`}
    >
      {key}
    </span>
  );
}
