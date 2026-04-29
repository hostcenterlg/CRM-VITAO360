// frontend/src/components/ui/Badge.tsx
// Base generic badge — no 'use client' (server-safe display primitive)
import type { ReactNode, HTMLAttributes } from 'react';
import { cn } from '@/lib/cn';

export type BadgeVariant =
  | 'success'  // verde — ATIVO, OK, concluido
  | 'warning'  // laranja — INAT.REC, atencao
  | 'danger'   // vermelho — EM RISCO, CRITICO, INATIVO
  | 'info'     // azul — PROSPECT, neutro positivo
  | 'neutral'  // cinza — INAT.ANT, sem dado
  | 'brand'    // verde Vitao solido — destaque CTA
  | 'lead'     // roxo — LEAD
  | 'fresh';   // cyan — NOVO

export type BadgeSize = 'xs' | 'sm' | 'md';

const BASE = 'inline-flex items-center gap-1 font-semibold rounded-full whitespace-nowrap';

const VARIANT_CLASSES: Record<BadgeVariant, string> = {
  success: 'bg-green-100 text-green-800',
  warning: 'bg-orange-100 text-orange-800',
  danger:  'bg-red-100 text-red-800',
  info:    'bg-blue-100 text-blue-800',
  neutral: 'bg-gray-100 text-gray-700',
  brand:   'bg-vitao-green text-white',
  lead:    'bg-purple-100 text-purple-800',
  fresh:   'bg-cyan-100 text-cyan-800',
};

const SIZE_CLASSES: Record<BadgeSize, string> = {
  xs: 'text-[10px] px-1.5 py-0 leading-4',
  sm: 'text-xs px-2 py-0.5 leading-5',
  md: 'text-sm px-2.5 py-1 leading-5',
};

export interface BadgeProps extends Omit<HTMLAttributes<HTMLSpanElement>, 'children'> {
  variant?: BadgeVariant;
  size?: BadgeSize;
  dot?: boolean;
  icon?: ReactNode;
  children: ReactNode;
}

export function Badge({
  variant = 'neutral',
  size = 'sm',
  dot,
  icon,
  className,
  children,
  ...rest
}: BadgeProps) {
  return (
    <span
      className={cn(BASE, VARIANT_CLASSES[variant], SIZE_CLASSES[size], className)}
      {...rest}
    >
      {icon ? (
        <span aria-hidden="true" className="inline-flex">{icon}</span>
      ) : dot ? (
        <span aria-hidden="true" className="w-1.5 h-1.5 rounded-full bg-current opacity-70" />
      ) : null}
      {children}
    </span>
  );
}
