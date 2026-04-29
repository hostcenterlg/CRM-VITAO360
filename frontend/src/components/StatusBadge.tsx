'use client';

/**
 * @deprecated Use componentes específicos de @/components/ui:
 *   - variant="situacao"    -> <StatusPill status={value} />
 *   - variant="temperatura" -> <StatusPill status={value} />
 *   - variant="abc"         -> <CurvaPill curva={value} />
 *   - variant="prioridade"  -> <PriorityPill prioridade={value} />
 *   - variant="sinaleiro"   -> <Sinaleiro cor={value.toLowerCase()} />
 *
 * Migração tracked em .planning/UX_REDESIGN_COMPONENTS_SPEC.md secao 14.
 * Este arquivo será removido em Wave 4 (após 100% dos consumers migrarem).
 */

// ---------------------------------------------------------------------------
// StatusBadge — colored badge for situacao / sinaleiro / prioridade / ABC / temperatura
// Colors follow R9 and CRM VITAO360 brand rules (LIGHT theme only)
// ---------------------------------------------------------------------------

export type BadgeVariant = 'situacao' | 'sinaleiro' | 'prioridade' | 'abc' | 'temperatura';

interface BadgeProps {
  value: string;
  variant?: BadgeVariant;
  small?: boolean;
  large?: boolean;
}

// Situacao: ATIVO=#00B050, INAT.REC=#FFC000, INAT.ANT=#FF0000, PROSPECT=#3B82F6
const situacaoMap: Record<string, { bg: string; text: string; label: string }> = {
  ATIVO:       { bg: '#00B050', text: '#fff',    label: 'ATIVO' },
  'INAT.REC':  { bg: '#FFC000', text: '#1a1a1a', label: 'INAT.REC' },
  'INAT.ANT':  { bg: '#FF0000', text: '#fff',    label: 'INAT.ANT' },
  INATIVO:     { bg: '#FF0000', text: '#fff',    label: 'INATIVO' },
  PROSPECT:    { bg: '#3B82F6', text: '#fff',    label: 'PROSPECT' },
  'EM RISCO':  { bg: '#F97316', text: '#fff',    label: 'EM RISCO' },
  LEAD:        { bg: '#8B5CF6', text: '#fff',    label: 'LEAD' },
  NOVO:        { bg: '#06B6D4', text: '#fff',    label: 'NOVO' },
};

// Sinaleiro: VERDE=#00B050, AMARELO=#FFC000, VERMELHO=#FF0000, ROXO=#7030A0
const sinaleiroMap: Record<string, { bg: string; text: string }> = {
  VERDE:    { bg: '#00B050', text: '#fff' },
  AMARELO:  { bg: '#FFC000', text: '#1a1a1a' },
  LARANJA:  { bg: '#FF8C00', text: '#fff' },
  VERMELHO: { bg: '#FF0000', text: '#fff' },
  ROXO:     { bg: '#7030A0', text: '#fff' },
};

// Prioridade: P0=red, P1=orange, P2=amber, P3=yellow, P4+=gray
const prioridadeMap: Record<string, { bg: string; text: string }> = {
  P0: { bg: '#FF0000', text: '#fff' },
  P1: { bg: '#FF6600', text: '#fff' },
  P2: { bg: '#FFC000', text: '#1a1a1a' },
  P3: { bg: '#FFFF00', text: '#1a1a1a' },
  P4: { bg: '#9CA3AF', text: '#fff' },
  P5: { bg: '#D1D5DB', text: '#374151' },
  P6: { bg: '#E5E7EB', text: '#6B7280' },
  P7: { bg: '#F3F4F6', text: '#9CA3AF' },
};

// Curva ABC: A=#00B050, B=#FFFF00, C=#FFC000
const abcMap: Record<string, { bg: string; text: string }> = {
  A: { bg: '#00B050', text: '#fff' },
  B: { bg: '#FFFF00', text: '#1a1a1a' },
  C: { bg: '#FFC000', text: '#1a1a1a' },
  D: { bg: '#9CA3AF', text: '#fff' },
};

// Temperatura: QUENTE=🔥, MORNO=⚠️, FRIO=❄️, CRITICO=🚨, PERDIDO=💀
const temperaturaMap: Record<string, { bg: string; text: string; emoji: string }> = {
  QUENTE:  { bg: '#EF4444', text: '#fff',    emoji: '🔥' },
  MORNO:   { bg: '#F97316', text: '#fff',    emoji: '⚠️' },
  FRIO:    { bg: '#60A5FA', text: '#fff',    emoji: '❄️' },
  CRITICO: { bg: '#7030A0', text: '#fff',    emoji: '🚨' },
  PERDIDO: { bg: '#6B7280', text: '#fff',    emoji: '💀' },
};

function getStyle(
  value: string,
  variant: BadgeVariant
): { bg: string; text: string; label?: string; emoji?: string } {
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
    case 'temperatura': {
      const entry = temperaturaMap[key];
      if (entry) return entry;
      return { bg: '#e5e7eb', text: '#374151' };
    }
    default:
      return { bg: '#e5e7eb', text: '#374151' };
  }
}

export default function StatusBadge({
  value,
  variant = 'situacao',
  small = false,
  large = false,
}: BadgeProps) {
  if (process.env.NODE_ENV === 'development') {
    console.warn(
      '[StatusBadge] Este componente está deprecado. ' +
      'Use os componentes de @/components/ui: StatusPill, CurvaPill, PriorityPill ou Sinaleiro. ' +
      'Ver .planning/UX_REDESIGN_COMPONENTS_SPEC.md seção 14.',
    );
  }
  if (!value) return <span className="text-gray-500">—</span>;

  const style = getStyle(value, variant);
  const key = value?.toUpperCase?.() ?? '';
  const display =
    variant === 'situacao' && situacaoMap[key]?.label
      ? situacaoMap[key].label
      : key;

  const emoji = variant === 'temperatura' ? (style.emoji ?? '') : '';

  const sizeClass = large
    ? 'px-2.5 py-1 text-xs'
    : small
    ? 'px-1.5 py-0 text-xs'
    : 'px-2 py-0.5 text-xs';

  return (
    <span
      role="status"
      aria-label={`${variant}: ${value}`}
      style={{ backgroundColor: style.bg, color: style.text }}
      className={`inline-flex items-center gap-0.5 font-semibold rounded uppercase tracking-wide ${sizeClass}`}
    >
      {emoji && <span aria-hidden="true">{emoji}</span>}
      {display}
    </span>
  );
}
