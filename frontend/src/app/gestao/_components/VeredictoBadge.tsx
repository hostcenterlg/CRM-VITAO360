'use client';

// VeredictoBadge — badge grande do veredito DDE
// 6 estados: SAUDAVEL / REVISAR / RENEGOCIAR / SUBSTITUIR / ALERTA_CREDITO / SEM_DADOS
// Exibe veredito_descricao abaixo do badge

type Veredito =
  | 'SAUDAVEL'
  | 'REVISAR'
  | 'RENEGOCIAR'
  | 'SUBSTITUIR'
  | 'ALERTA_CREDITO'
  | 'SEM_DADOS';

interface VeredictoBadgeProps {
  veredito: Veredito | string;
  descricao?: string;
  size?: 'sm' | 'md' | 'lg';
}

const VEREDITO_CONFIG: Record<string, { label: string; bg: string; text: string; border: string; icon: string }> = {
  SAUDAVEL: {
    label: 'SAUDÁVEL',
    bg: 'bg-green-50',
    text: 'text-green-800',
    border: 'border-green-300',
    icon: 'M5 13l4 4L19 7',
  },
  REVISAR: {
    label: 'REVISAR',
    bg: 'bg-amber-50',
    text: 'text-amber-800',
    border: 'border-amber-300',
    icon: 'M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z',
  },
  RENEGOCIAR: {
    label: 'RENEGOCIAR',
    bg: 'bg-orange-50',
    text: 'text-orange-800',
    border: 'border-orange-300',
    icon: 'M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z',
  },
  SUBSTITUIR: {
    label: 'SUBSTITUIR',
    bg: 'bg-red-50',
    text: 'text-red-800',
    border: 'border-red-300',
    icon: 'M6 18L18 6M6 6l12 12',
  },
  ALERTA_CREDITO: {
    label: 'ALERTA CRÉDITO',
    bg: 'bg-purple-50',
    text: 'text-purple-800',
    border: 'border-purple-300',
    icon: 'M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z',
  },
  SEM_DADOS: {
    label: 'SEM DADOS',
    bg: 'bg-gray-50',
    text: 'text-gray-600',
    border: 'border-gray-300',
    icon: 'M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z',
  },
};

export function VeredictoBadge({ veredito, descricao, size = 'md' }: VeredictoBadgeProps) {
  const cfg = VEREDITO_CONFIG[veredito] ?? VEREDITO_CONFIG['SEM_DADOS'];

  const iconSize = size === 'lg' ? 'w-6 h-6' : size === 'sm' ? 'w-3.5 h-3.5' : 'w-4 h-4';
  const labelSize = size === 'lg' ? 'text-lg font-extrabold' : size === 'sm' ? 'text-xs font-bold' : 'text-sm font-bold';
  const padding = size === 'lg' ? 'px-5 py-3' : size === 'sm' ? 'px-2 py-1' : 'px-3 py-2';

  return (
    <div className="inline-flex flex-col items-start gap-1">
      <span
        className={`inline-flex items-center gap-2 rounded-lg border ${cfg.bg} ${cfg.text} ${cfg.border} ${padding}`}
        aria-label={`Veredito DDE: ${cfg.label}`}
      >
        <svg className={`${iconSize} flex-shrink-0`} fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d={cfg.icon} />
        </svg>
        <span className={labelSize}>{cfg.label}</span>
      </span>
      {descricao && (
        <p className="text-xs text-gray-600 leading-snug max-w-xs">{descricao}</p>
      )}
    </div>
  );
}
