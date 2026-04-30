'use client';

// TierPill — pill compacta de classificação de dado DDE
// REAL (verde) / SINTETICO (âmbar) / PENDENTE (cinza) / NULL (azul)
// R8: nenhum dado inventado — o tier indica a confiabilidade da linha

interface TierPillProps {
  tier: 'REAL' | 'SINTETICO' | 'PENDENTE' | 'NULL';
  /** Tooltip opcional (observação da linha) */
  title?: string;
}

const TIER_CONFIG = {
  REAL:     { label: 'REAL',      className: 'bg-green-100 text-green-800 border-green-200' },
  SINTETICO:{ label: 'SINTÉTICO', className: 'bg-amber-100 text-amber-800 border-amber-200' },
  PENDENTE: { label: 'PENDENTE',  className: 'bg-gray-100 text-gray-700 border-gray-300' },
  NULL:     { label: 'NULL',      className: 'bg-blue-50 text-blue-700 border-blue-200' },
} as const;

export function TierPill({ tier, title }: TierPillProps) {
  const cfg = TIER_CONFIG[tier] ?? TIER_CONFIG['NULL'];
  return (
    <span
      className={`inline-flex items-center px-1.5 py-0.5 rounded border text-xs font-semibold whitespace-nowrap ${cfg.className}`}
      title={title}
      aria-label={`Classificação: ${cfg.label}${title ? ` — ${title}` : ''}`}
    >
      {cfg.label}
    </span>
  );
}
