// frontend/src/components/ui/CurvaPill.tsx
// Curva ABC pill — solid Vitao brand colors (R9)
// Server-safe (no 'use client')
import { cn } from '@/lib/cn';
import type { BadgeSize } from './Badge';

export type Curva = 'A' | 'B' | 'C';

export interface CurvaPillProps {
  curva: Curva | string;
  size?: BadgeSize;
  showLabel?: boolean;
  className?: string;
}

const BASE = 'inline-flex items-center font-semibold rounded-full';

const SIZE_CLASSES: Record<BadgeSize, string> = {
  xs: 'text-[10px] px-1.5 py-0 leading-4',
  sm: 'text-xs px-2 py-0.5 leading-5',
  md: 'text-sm px-2.5 py-1 leading-5',
};

// Curva A = vitao-green (#00A859), Curva B = vitao-blue (#0066CC), Curva C = gray
const CURVA_CLASSES: Record<Curva, string> = {
  A: 'bg-vitao-green text-white',
  B: 'bg-vitao-blue text-white',
  C: 'bg-gray-400 text-white',
};

export function CurvaPill({
  curva,
  size = 'sm',
  showLabel = true,
  className,
}: CurvaPillProps) {
  const key = String(curva ?? '').trim().toUpperCase() as Curva;
  const colorClass = CURVA_CLASSES[key] ?? 'bg-gray-300 text-gray-700';
  const text = showLabel ? `Curva ${key}` : key;
  return (
    <span
      className={cn(BASE, SIZE_CLASSES[size], colorClass, className)}
      aria-label={`Curva ${key}`}
    >
      {text}
    </span>
  );
}
