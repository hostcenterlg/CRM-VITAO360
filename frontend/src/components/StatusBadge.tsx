'use client';

// ---------------------------------------------------------------------------
// StatusBadge — colored badge for situacao / sinaleiro / prioridade / ABC
// Colors follow R9 and CRM VITAO360 brand rules (LIGHT theme only)
// ---------------------------------------------------------------------------

export type BadgeVariant = 'situacao' | 'sinaleiro' | 'prioridade' | 'abc';

interface BadgeProps {
  value: string;
  variant?: BadgeVariant;
  small?: boolean;
}

// Situacao: ATIVO=#00B050, INAT.REC=#FFC000, INAT.ANT=#FF0000, PROSPECT=#808080
const situacaoMap: Record<string, { bg: string; text: string; label: string }> = {
  ATIVO: { bg: '#00B050', text: '#fff', label: 'ATIVO' },
  'INAT.REC': { bg: '#FFC000', text: '#1a1a1a', label: 'INAT.REC' },
  'INAT.ANT': { bg: '#FF0000', text: '#fff', label: 'INAT.ANT' },
  INATIVO: { bg: '#FF0000', text: '#fff', label: 'INATIVO' },
  PROSPECT: { bg: '#808080', text: '#fff', label: 'PROSPECT' },
};

// Sinaleiro: VERDE=#00B050, AMARELO=#FFC000, VERMELHO=#FF0000, ROXO=#800080
const sinaleiroMap: Record<string, { bg: string; text: string }> = {
  VERDE: { bg: '#00B050', text: '#fff' },
  AMARELO: { bg: '#FFC000', text: '#1a1a1a' },
  VERMELHO: { bg: '#FF0000', text: '#fff' },
  ROXO: { bg: '#800080', text: '#fff' },
};

// Prioridade: P0=red, P1=orange, P2=amber, P3=yellow, P4=gray
const prioridadeMap: Record<string, { bg: string; text: string }> = {
  P0: { bg: '#FF0000', text: '#fff' },
  P1: { bg: '#FF6600', text: '#fff' },
  P2: { bg: '#FFC000', text: '#1a1a1a' },
  P3: { bg: '#FFFF00', text: '#1a1a1a' },
  P4: { bg: '#9ca3af', text: '#fff' },
  P5: { bg: '#d1d5db', text: '#374151' },
};

// Curva ABC: A=#00B050, B=#FFFF00, C=#FFC000
const abcMap: Record<string, { bg: string; text: string }> = {
  A: { bg: '#00B050', text: '#fff' },
  B: { bg: '#FFFF00', text: '#1a1a1a' },
  C: { bg: '#FFC000', text: '#1a1a1a' },
  D: { bg: '#9ca3af', text: '#fff' },
};

function getStyle(
  value: string,
  variant: BadgeVariant
): { bg: string; text: string; label?: string } {
  const key = value?.toUpperCase?.() ?? '';

  switch (variant) {
    case 'situacao': {
      const entry = situacaoMap[key];
      if (entry) return entry;
      return { bg: '#e5e7eb', text: '#374151' };
    }
    case 'sinaleiro': {
      const entry = sinaleiroMap[key];
      if (entry) return entry;
      return { bg: '#e5e7eb', text: '#374151' };
    }
    case 'prioridade': {
      const entry = prioridadeMap[key];
      if (entry) return entry;
      return { bg: '#e5e7eb', text: '#374151' };
    }
    case 'abc': {
      const entry = abcMap[key];
      if (entry) return entry;
      return { bg: '#e5e7eb', text: '#374151' };
    }
    default:
      return { bg: '#e5e7eb', text: '#374151' };
  }
}

export default function StatusBadge({ value, variant = 'situacao', small = false }: BadgeProps) {
  if (!value) return <span className="text-gray-400">—</span>;

  const style = getStyle(value, variant);
  const display =
    variant === 'situacao' && situacaoMap[value?.toUpperCase?.()]?.label
      ? situacaoMap[value.toUpperCase()].label
      : value.toUpperCase();

  return (
    <span
      style={{ backgroundColor: style.bg, color: style.text }}
      className={`inline-flex items-center font-semibold rounded ${
        small ? 'px-1.5 py-0 text-[10px]' : 'px-2 py-0.5 text-xs'
      }`}
    >
      {display}
    </span>
  );
}
