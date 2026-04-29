// frontend/src/components/ui/Sinaleiro.tsx
// Status dot with native tooltip — for dense tables where full pill doesn't fit
// Server-safe (no 'use client')
import { cn } from '@/lib/cn';

export type SinaleiroCor = 'verde' | 'amarelo' | 'laranja' | 'vermelho' | 'roxo' | 'cinza';

export interface SinaleiroProps {
  cor: SinaleiroCor | string;
  size?: 'sm' | 'md' | 'lg';
  pulse?: boolean;
  tooltip?: string;
  ariaLabel?: string;
  className?: string;
}

const COR_CLASSES: Record<SinaleiroCor, string> = {
  verde:    'bg-green-500',
  amarelo:  'bg-yellow-400',
  laranja:  'bg-orange-500',
  vermelho: 'bg-red-500',
  roxo:     'bg-purple-500',
  cinza:    'bg-gray-400',
};

const COR_TOOLTIPS: Record<SinaleiroCor, string> = {
  verde:    'Cliente saudável (compras regulares)',
  amarelo:  'Atenção - frequência caindo',
  laranja:  'Risco - sem compra recente',
  vermelho: 'Crítico - possível perda',
  roxo:     'Cliente especial / observação',
  cinza:    'Sem dados ou prospect',
};

const SIZE_CLASSES = {
  sm: 'w-2 h-2',
  md: 'w-2.5 h-2.5',
  lg: 'w-3 h-3',
};

export function Sinaleiro({
  cor,
  size = 'md',
  pulse,
  tooltip,
  ariaLabel,
  className,
}: SinaleiroProps) {
  const key = String(cor ?? '').trim().toLowerCase() as SinaleiroCor;
  const colorClass = COR_CLASSES[key] ?? 'bg-gray-300';
  const tooltipText = tooltip ?? COR_TOOLTIPS[key] ?? 'Status desconhecido';
  return (
    <span
      role="status"
      aria-label={ariaLabel ?? tooltipText}
      title={tooltipText}
      className={cn(
        'inline-block rounded-full ring-1 ring-white/40',
        SIZE_CLASSES[size],
        colorClass,
        pulse && 'animate-pulse',
        className,
      )}
    />
  );
}
