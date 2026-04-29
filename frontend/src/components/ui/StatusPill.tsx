// frontend/src/components/ui/StatusPill.tsx
// Semantic wrapper — maps CRM status string to Badge automatically
// Server-safe (no 'use client')
import { Badge } from './Badge';
import type { BadgeVariant, BadgeSize } from './Badge';
import { cn } from '@/lib/cn';

export type CrmStatus =
  | 'ATIVO'
  | 'INAT.REC'
  | 'INAT.ANT'
  | 'INATIVO'
  | 'PROSPECT'
  | 'EM_RISCO'
  | 'EM RISCO'
  | 'LEAD'
  | 'NOVO'
  | 'QUENTE'
  | 'MORNO'
  | 'FRIO'
  | 'CRITICO';

export interface StatusPillProps {
  status: CrmStatus | string;
  size?: BadgeSize;
  showIcon?: boolean;
  className?: string;
}

type StatusConfig = {
  variant: BadgeVariant;
  label: string;
  icon?: string;
  bold?: boolean;
};

const STATUS_MAP: Record<string, StatusConfig> = {
  // Situacao comercial
  'ATIVO':    { variant: 'success', label: 'Ativo' },
  'INAT.REC': { variant: 'warning', label: 'Inat. Recente' },
  'INAT.ANT': { variant: 'neutral', label: 'Inat. Antigo' },
  'INATIVO':  { variant: 'neutral', label: 'Inativo' },
  'PROSPECT': { variant: 'info',    label: 'Prospect' },
  'EM_RISCO': { variant: 'danger',  label: 'Em Risco' },
  'EM RISCO': { variant: 'danger',  label: 'Em Risco' },
  'LEAD':     { variant: 'lead',    label: 'Lead' },
  'NOVO':     { variant: 'fresh',   label: 'Novo' },

  // Temperatura
  'QUENTE':   { variant: 'danger',  label: 'Quente', icon: '🔥' },
  'MORNO':    { variant: 'warning', label: 'Morno',  icon: '⚠️' },
  'FRIO':     { variant: 'info',    label: 'Frio',   icon: '❄️' },
  'CRITICO':  { variant: 'danger',  label: 'Crítico', bold: true },
};

export function StatusPill({
  status,
  size = 'sm',
  showIcon = true,
  className,
}: StatusPillProps) {
  const key = String(status ?? '').trim().toUpperCase();
  const cfg = STATUS_MAP[key];

  if (!cfg) {
    return (
      <Badge variant="neutral" size={size} className={className}>
        {key || '—'}
      </Badge>
    );
  }

  return (
    <Badge
      variant={cfg.variant}
      size={size}
      icon={showIcon && cfg.icon ? cfg.icon : undefined}
      className={cn(cfg.bold && 'font-bold', className)}
    >
      {cfg.label}
    </Badge>
  );
}
