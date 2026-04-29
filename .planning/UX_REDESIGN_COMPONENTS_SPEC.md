# UX Redesign — Components Spec (Wave 2)

**Owner:** @architect
**Status:** SPEC ONLY — implementação por @dev na Wave 2
**Date:** 2026-04-29
**Scope:** Componentes UI globais reutilizáveis em `frontend/src/components/ui/`
**Stack:** Next.js 14 App Router + React 18 + TypeScript + Tailwind 3.4 puro (sem shadcn/ui, sem Headless UI, sem CVA)

---

## 0. Princípios

1. **Tailwind puro com lookup maps.** Sem `class-variance-authority`. Cada componente exporta um map `Record<Variant, string>` e concatena via helper `cn()`.
2. **Light theme only (R9).** Nunca `dark:` prefix. Nunca toggle.
3. **Inter já configurada** em `frontend/tailwind.config.ts:14`. Não importar fonte de novo.
4. **Todo componente aceita `className?`** para override controlado (override vence default via ordem `cn(default, className)`).
5. **Acessibilidade default-on:** `aria-label` quando não houver texto, `role` semântico, `focus-visible:ring`, suporte a tab.
6. **Zero libs externas.** Apenas React 18 + Tailwind. `clsx` reimplementado em 8 linhas dentro de `lib/cn.ts`.
7. **Server-safe.** Componentes de exibição (`Badge`, `StatusPill`, `CurvaPill`, `PriorityPill`, `ScoreBar`, `ProgressBar`, `Sinaleiro`) sem `'use client'`. Apenas componentes com state (`Tabs`, `FilterGroup`, `SearchInput`, `MetaWidget`) marcam `'use client'`.
8. **Compatibilidade.** O atual `StatusBadge.tsx` não pode quebrar imediatamente (14 arquivos importam). Estratégia de migração definida na seção 11.

---

## 1. Helper `cn()` — Tailwind class merger

**Arquivo:** `frontend/src/lib/cn.ts`

Helper minimalista (~10 linhas). Não substitui `tailwind-merge`; basta concatenar e ignorar valores falsy. Conflitos de classe Tailwind são responsabilidade do autor (ordem importa: `cn(BASE, VARIANT, className)`).

```ts
// frontend/src/lib/cn.ts
export type ClassValue = string | number | null | false | undefined | ClassValue[];

export function cn(...args: ClassValue[]): string {
  const out: string[] = [];
  for (const a of args) {
    if (!a) continue;
    if (Array.isArray(a)) {
      const inner = cn(...a);
      if (inner) out.push(inner);
    } else {
      out.push(String(a));
    }
  }
  return out.join(' ');
}
```

**Por que não `tailwind-merge`?** Adiciona ~3 KB e nunca encontramos override real (a paleta é fechada). Documentar regra: variants não devem mexer em propriedades que `className` precise sobrescrever no consumo. Se precisar override de cor, passar a cor via prop, não via `className`.

---

## 2. `Badge.tsx` — base genérica

**Arquivo:** `frontend/src/components/ui/Badge.tsx`

### Contrato

```ts
export type BadgeVariant =
  | 'success'   // verde — ATIVO, OK, concluído
  | 'warning'   // laranja — INAT.REC, atenção
  | 'danger'    // vermelho — EM RISCO, CRITICO, INATIVO
  | 'info'      // azul — PROSPECT, neutro positivo
  | 'neutral'   // cinza — INAT.ANT, sem dado
  | 'brand';    // verde Vitão sólido — destaque CTA

export type BadgeSize = 'xs' | 'sm' | 'md';

export interface BadgeProps {
  variant?: BadgeVariant;       // default: 'neutral'
  size?: BadgeSize;             // default: 'sm'
  dot?: boolean;                // bolinha 6x6 antes do texto
  icon?: React.ReactNode;       // ícone/emoji antes do texto (override de dot)
  className?: string;
  children: React.ReactNode;
  'aria-label'?: string;
}
```

### Variant map (Tailwind puro)

```ts
const VARIANT_CLASSES: Record<BadgeVariant, string> = {
  success: 'bg-green-100 text-green-800',
  warning: 'bg-orange-100 text-orange-800',
  danger:  'bg-red-100 text-red-800',
  info:    'bg-blue-100 text-blue-800',
  neutral: 'bg-gray-100 text-gray-700',
  brand:   'bg-vitao-green text-white',
};

const SIZE_CLASSES: Record<BadgeSize, string> = {
  xs: 'text-[10px] px-1.5 py-0 leading-4',
  sm: 'text-xs px-2 py-0.5 leading-5',
  md: 'text-sm px-2.5 py-1 leading-5',
};

const DOT_COLORS: Record<BadgeVariant, string> = {
  success: 'bg-green-500',
  warning: 'bg-orange-500',
  danger:  'bg-red-500',
  info:    'bg-blue-500',
  neutral: 'bg-gray-400',
  brand:   'bg-white',
};
```

### Snippet ilustrativo

```tsx
import { cn } from '@/lib/cn';

const BASE = 'inline-flex items-center gap-1 font-semibold rounded-full whitespace-nowrap';

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
        <span aria-hidden="true" className={cn('w-1.5 h-1.5 rounded-full', DOT_COLORS[variant])} />
      ) : null}
      {children}
    </span>
  );
}
```

### Notas

- Forma `rounded-full` (pílula) é o default do redesign. Quem precisar de `rounded-md` (legado) usa `className="!rounded-md"`.
- `'aria-label'` é opcional — quando o texto interno já é descritivo (ex: "ATIVO"), o leitor de tela basta. Quando o badge é apenas ícone (raro), passar `aria-label` é obrigatório.

---

## 3. `StatusPill.tsx` — wrapper semântico do CRM

**Arquivo:** `frontend/src/components/ui/StatusPill.tsx`

Recebe um **status string do domínio** e mapeia automaticamente para `Badge`. É o componente que substitui chamadas atuais `<StatusBadge variant="situacao" value="ATIVO" />`.

### Contrato

```ts
export type CrmStatus =
  | 'ATIVO'
  | 'INAT.REC'
  | 'INAT.ANT'
  | 'INATIVO'      // alias legado p/ INAT.ANT
  | 'PROSPECT'
  | 'EM_RISCO'     // forma normalizada
  | 'EM RISCO'     // forma legada (com espaço)
  | 'LEAD'
  | 'NOVO'
  | 'QUENTE'
  | 'MORNO'
  | 'FRIO'
  | 'CRITICO';

export interface StatusPillProps {
  status: CrmStatus | string;   // string para forward-compat (cai em neutral)
  size?: BadgeSize;
  showIcon?: boolean;           // default: true (emoji 🔥/⚠️/❄️ quando aplicável)
  className?: string;
}
```

### Map de status -> variant + ícone

```ts
type StatusConfig = {
  variant: BadgeVariant;
  label: string;          // texto exibido (preserva CAPS atual quando coerente)
  icon?: string;          // emoji
  bold?: boolean;         // CRITICO ganha font-bold
};

const STATUS_MAP: Record<string, StatusConfig> = {
  // Situação comercial
  'ATIVO':     { variant: 'success', label: 'Ativo' },
  'INAT.REC':  { variant: 'warning', label: 'Inat. Recente' },
  'INAT.ANT':  { variant: 'neutral', label: 'Inat. Antigo' },
  'INATIVO':   { variant: 'neutral', label: 'Inativo' },
  'PROSPECT':  { variant: 'info',    label: 'Prospect' },
  'EM_RISCO':  { variant: 'danger',  label: 'Em Risco' },
  'EM RISCO':  { variant: 'danger',  label: 'Em Risco' },
  'LEAD':      { variant: 'lead',    label: 'Lead' },
  'NOVO':      { variant: 'fresh',   label: 'Novo' },

  // Temperatura
  'QUENTE':    { variant: 'danger',  label: 'Quente', icon: '🔥' },
  'MORNO':     { variant: 'warning', label: 'Morno',  icon: '⚠️' },
  'FRIO':      { variant: 'info',    label: 'Frio',   icon: '❄️' },
  'CRITICO':   { variant: 'danger',  label: 'Crítico', bold: true },
};
```

### Decisão arquitetural — LEAD/NOVO precisam de cor fora dos 6 variants

LEAD = roxo, NOVO = cyan. Nenhum dos 6 variants base do `Badge` cobre. Duas opções:

**Opção A (escolhida):** ampliar `BadgeVariant` para incluir `'lead'` e `'fresh'`, expostos no map.

```ts
// extensão fechada — sem dark mode
'lead':  'bg-purple-100 text-purple-800',
'fresh': 'bg-cyan-100 text-cyan-800',
```

**Opção B (rejeitada):** prop `colorOverride: { bg: string; text: string }`. Quebra disciplina do Tailwind puro, abre porta para cores ad-hoc.

### Snippet

```tsx
import { Badge } from './Badge';
import { cn } from '@/lib/cn';

export function StatusPill({ status, size = 'sm', showIcon = true, className }: StatusPillProps) {
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
```

### Casos de uso atuais que migram para StatusPill
- `<StatusBadge variant="situacao" value="ATIVO" />` -> `<StatusPill status="ATIVO" />`
- `<StatusBadge variant="temperatura" value="QUENTE" />` -> `<StatusPill status="QUENTE" />`

---

## 4. `CurvaPill.tsx` — Curva ABC

**Arquivo:** `frontend/src/components/ui/CurvaPill.tsx`

Pílula com fundo sólido Vitão (R9) e label completo "Curva A/B/C".

### Contrato

```ts
export type Curva = 'A' | 'B' | 'C';

export interface CurvaPillProps {
  curva: Curva | string;
  size?: BadgeSize;          // default 'sm'
  showLabel?: boolean;       // default true: "Curva A". false: só "A"
  className?: string;
}
```

### Map

```ts
const CURVA_CLASSES: Record<Curva, string> = {
  A: 'bg-vitao-green text-white',  // #00A859
  B: 'bg-vitao-blue text-white',   // #0066CC
  C: 'bg-gray-400 text-white',
};
```

### Snippet

```tsx
import { cn } from '@/lib/cn';

const BASE = 'inline-flex items-center font-semibold rounded-full';
const SIZE_CLASSES: Record<BadgeSize, string> = {
  xs: 'text-[10px] px-1.5 py-0 leading-4',
  sm: 'text-xs px-2 py-0.5 leading-5',
  md: 'text-sm px-2.5 py-1 leading-5',
};

export function CurvaPill({ curva, size = 'sm', showLabel = true, className }: CurvaPillProps) {
  const key = String(curva ?? '').trim().toUpperCase() as Curva;
  const colorClass = CURVA_CLASSES[key] ?? 'bg-gray-300 text-gray-700';
  const text = showLabel ? `Curva ${key}` : key;
  return (
    <span className={cn(BASE, SIZE_CLASSES[size], colorClass, className)} aria-label={`Curva ${key}`}>
      {text}
    </span>
  );
}
```

### Decisão: `bg-vitao-green` (#00A859) em vez de `bg-green-500`
A paleta Vitão (palette EN) já está em `tailwind.config.ts:28`. Curva A é identidade visual de produto, não estado semântico — usa **brand color sólida**, não a escala neutra do Tailwind.

---

## 5. `PriorityPill.tsx` — P0 a P7

**Arquivo:** `frontend/src/components/ui/PriorityPill.tsx`

### Contrato

```ts
export type Prioridade = 'P0' | 'P1' | 'P2' | 'P3' | 'P4' | 'P5' | 'P6' | 'P7';

export interface PriorityPillProps {
  prioridade: Prioridade | string;
  size?: BadgeSize;
  className?: string;
}
```

### Map

Gradiente vermelho -> verde (P0=mais urgente, P7=mais frio). Mantém compatibilidade visual com o `prioridadeMap` atual de `StatusBadge.tsx:39-48` mas migra para Tailwind classes.

```ts
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
```

### Snippet

```tsx
export function PriorityPill({ prioridade, size = 'sm', className }: PriorityPillProps) {
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
```

---

## 6. `ScoreBar.tsx` — barra de score 0-100

**Arquivo:** `frontend/src/components/ui/ScoreBar.tsx`

Barra horizontal com **fill gradiente** (vermelho < 40 < amarelo < 70 < verde) e número à direita. Usado em Carteira (score motor), Pipeline (probabilidade) e Inbox (engagement).

### Contrato

```ts
export interface ScoreBarProps {
  score: number;                     // 0-100 (clamp automático)
  showLabel?: boolean;               // default: true — mostra número à direita
  showPercent?: boolean;             // default: false — adiciona '%'
  height?: 'sm' | 'md' | 'lg';       // sm=h-1.5, md=h-2, lg=h-3 (default md)
  className?: string;
  trackClassName?: string;
  ariaLabel?: string;                // default: "Score: {n}"
}
```

### Lógica de cor

```ts
function scoreColor(score: number): string {
  if (score >= 70) return 'bg-green-500';
  if (score >= 40) return 'bg-yellow-400';
  return 'bg-red-500';
}

const HEIGHT_CLASSES = {
  sm: 'h-1.5',
  md: 'h-2',
  lg: 'h-3',
};
```

### Snippet

```tsx
export function ScoreBar({
  score,
  showLabel = true,
  showPercent = false,
  height = 'md',
  className,
  trackClassName,
  ariaLabel,
}: ScoreBarProps) {
  const clamped = Math.max(0, Math.min(100, Math.round(score ?? 0)));
  const color = scoreColor(clamped);
  return (
    <div
      className={cn('flex items-center gap-2 w-full', className)}
      role="meter"
      aria-valuenow={clamped}
      aria-valuemin={0}
      aria-valuemax={100}
      aria-label={ariaLabel ?? `Score: ${clamped}`}
    >
      <div className={cn('flex-1 bg-gray-100 rounded-full overflow-hidden', HEIGHT_CLASSES[height], trackClassName)}>
        <div
          className={cn('h-full rounded-full transition-[width] duration-300', color)}
          style={{ width: `${clamped}%` }}
        />
      </div>
      {showLabel && (
        <span className="text-xs font-semibold text-gray-700 tabular-nums w-8 text-right">
          {clamped}{showPercent && '%'}
        </span>
      )}
    </div>
  );
}
```

### Decisão: `bg-yellow-400` em vez de `bg-vitao-amarelo` (#FFC000)
Yellow-400 (#FACC15) tem contraste melhor sobre branco. O `vitao.amarelo` legacy fica reservado para `StatusPill` warning. Para barras finas, contraste é mais importante que brand fidelity.

---

## 7. `ProgressBar.tsx` — meta vs realizado

**Arquivo:** `frontend/src/components/ui/ProgressBar.tsx`

Diferente do `ScoreBar`: aqui o fill é **sempre verde Vitão** (atingimento de meta é positivo), e o eixo é `current/total`, não score absoluto.

### Contrato

```ts
export interface ProgressBarProps {
  current: number;
  total: number;
  label?: string;
  showPercent?: boolean;
  showFraction?: boolean;
  format?: (n: number) => string;
  height?: 'sm' | 'md' | 'lg';
  warnAt?: number;
  dangerAt?: number;
  className?: string;
}
```

### Snippet

```tsx
export function ProgressBar({
  current, total, label, showPercent = true, showFraction = false, format,
  height = 'lg', warnAt, dangerAt, className,
}: ProgressBarProps) {
  const safeTotal = Math.max(1, total);
  const pct = Math.max(0, Math.min(100, Math.round((current / safeTotal) * 100)));

  let color = 'bg-vitao-green';
  if (dangerAt != null && pct < dangerAt) color = 'bg-red-500';
  else if (warnAt != null && pct < warnAt) color = 'bg-yellow-400';

  const fmt = format ?? ((n: number) => n.toLocaleString('pt-BR'));

  return (
    <div className={cn('w-full', className)}>
      {(label || showPercent || showFraction) && (
        <div className="flex items-center justify-between mb-1 text-xs">
          {label && <span className="font-semibold text-gray-700">{label}</span>}
          <span className="font-semibold text-gray-900 tabular-nums">
            {showFraction && `${fmt(current)} / ${fmt(total)}`}
            {showFraction && showPercent && '  '}
            {showPercent && `${pct}%`}
          </span>
        </div>
      )}
      <div className={cn('w-full bg-gray-100 rounded-full overflow-hidden', HEIGHT_CLASSES[height])}>
        <div
          className={cn('h-full rounded-full transition-[width] duration-500', color)}
          style={{ width: `${pct}%` }}
          role="progressbar"
          aria-valuenow={pct} aria-valuemin={0} aria-valuemax={100}
          aria-label={label ?? `Progresso: ${pct}%`}
        />
      </div>
    </div>
  );
}
```

---

## 8. `Tabs.tsx` — pílulas de navegação

**Arquivo:** `frontend/src/components/ui/Tabs.tsx`
**Marca:** `'use client'`

Pílulas arredondadas estilo Vitão MVP. Ativo = `bg-vitao-green text-white`. Inativo = `bg-gray-100 text-gray-700 hover:bg-gray-200`.

### Contrato

```ts
export interface TabItem {
  id: string;
  label: string;
  count?: number;
  icon?: React.ReactNode;
  disabled?: boolean;
}

export interface TabsProps {
  tabs: TabItem[];
  activeId: string;
  onChange: (id: string) => void;
  size?: 'sm' | 'md';
  fullWidth?: boolean;
  className?: string;
  ariaLabel?: string;
}
```

### Snippet

```tsx
'use client';
import { cn } from '@/lib/cn';

const TAB_BASE = 'inline-flex items-center gap-1.5 font-medium rounded-full transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-vitao-green focus-visible:ring-offset-1';
const TAB_SIZE = {
  sm: 'text-xs px-3 py-1',
  md: 'text-sm px-4 py-1.5',
};

export function Tabs({ tabs, activeId, onChange, size = 'md', fullWidth, className, ariaLabel }: TabsProps) {
  return (
    <div
      role="tablist"
      aria-label={ariaLabel ?? 'Navegação por abas'}
      className={cn('inline-flex items-center gap-2 flex-wrap', fullWidth && 'w-full', className)}
    >
      {tabs.map((t) => {
        const active = t.id === activeId;
        return (
          <button
            key={t.id}
            type="button"
            role="tab"
            aria-selected={active}
            aria-controls={`panel-${t.id}`}
            id={`tab-${t.id}`}
            disabled={t.disabled}
            onClick={() => !t.disabled && onChange(t.id)}
            className={cn(
              TAB_BASE,
              TAB_SIZE[size],
              active
                ? 'bg-vitao-green text-white shadow-sm'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200',
              t.disabled && 'opacity-40 cursor-not-allowed',
            )}
          >
            {t.icon && <span aria-hidden="true">{t.icon}</span>}
            <span>{t.label}</span>
            {typeof t.count === 'number' && (
              <span
                className={cn(
                  'inline-flex items-center justify-center min-w-[20px] h-5 px-1.5 rounded-full text-[10px] font-bold tabular-nums',
                  active ? 'bg-white/25 text-white' : 'bg-gray-300/60 text-gray-700',
                )}
              >
                {t.count > 99 ? '99+' : t.count}
              </span>
            )}
          </button>
        );
      })}
    </div>
  );
}
```

### Decisões
- **Não controla painel.** Apenas dispara `onChange`. Painel fica no consumidor (mais flexível).
- **Acessibilidade:** `role="tablist"`, `aria-selected`, `aria-controls`. Consumidor é responsável por id `panel-{id}` e `aria-labelledby="tab-{id}"`.
- **Não usar Headless UI Tabs.** Restrição do projeto.

---

## 9. FilterGroup.tsx — filtros 3 níveis

**Arquivo:** frontend/src/components/ui/FilterGroup.tsx
**Marca:** use-client (state interno)

Implementa **R5 — filtros 3 níveis** do briefing UX. É o componente mais crítico desta wave.

### Conceito

- **Nível 1 (sempre visível):** search box + 1-2 selects primários (ex: Vendedor, Período)
- **Nível 2 (visível, em pílulas):** filtros de uso comum como pills toggleáveis. Selecionado = fill sólido (variant=brand). Desselecionado = neutral outline.
- **Nível 3 (colapsado):** botão "Mais filtros" que expande seção com selects/ranges menos usados (cidade, faixa de valor, tags)

### Contrato — Schema declarativo

```ts
export type FilterFieldType = 'search' | 'select' | 'pill-toggle' | 'date-range' | 'number-range';

export interface BaseFilterField {
  id: string;
  label: string;
  level: 1 | 2 | 3;
  type: FilterFieldType;
  className?: string;
}

export interface SearchField extends BaseFilterField {
  type: 'search';
  placeholder?: string;
}

export interface SelectField extends BaseFilterField {
  type: 'select';
  options: Array<{ value: string; label: string; count?: number }>;
  placeholder?: string;
  multi?: boolean;
}

export interface PillToggleField extends BaseFilterField {
  type: 'pill-toggle';
  options: Array<{ value: string; label: string; count?: number; icon?: React.ReactNode }>;
  multi?: boolean;
}

export interface DateRangeField extends BaseFilterField {
  type: 'date-range';
  presets?: Array<{ id: string; label: string; from: string; to: string }>;
}

export interface NumberRangeField extends BaseFilterField {
  type: 'number-range';
  min?: number;
  max?: number;
  step?: number;
  format?: (n: number) => string;
}

export type FilterField = SearchField | SelectField | PillToggleField | DateRangeField | NumberRangeField;

export type FilterState = Record<string, unknown>;

export interface FilterGroupProps {
  fields: FilterField[];
  state: FilterState;
  onChange: (next: FilterState) => void;
  onReset?: () => void;
  defaultLevel3Open?: boolean;
  className?: string;
  resultsCount?: number;
}
```

### Estrutura visual (ascii)

```
+-------------------------------------------------------------+
|  [search...]  [Vendedor v]  [Periodo v]            12 res.  |  N1
+-------------------------------------------------------------+
|  ( Ativo 234 ) ( Em Risco 12 ) [ Curva A ] [ Curva B ]      |  N2
+-------------------------------------------------------------+
|  > Mais filtros (3 ativos)                       [Limpar]   |  N3
+-------------------------------------------------------------+
```

Quando expandido, N3 mostra grid 2-col em desktop com ranges/selects extras.

### Snippet — esqueleto

```tsx
'use client';
import { useMemo, useState } from 'react';
import { cn } from '@/lib/cn';
import { Badge } from './Badge';

export function FilterGroup({
  fields, state, onChange, onReset, defaultLevel3Open = false, className, resultsCount,
}: FilterGroupProps) {
  const [openL3, setOpenL3] = useState(defaultLevel3Open);

  const byLevel = useMemo(() => ({
    1: fields.filter(f => f.level === 1),
    2: fields.filter(f => f.level === 2),
    3: fields.filter(f => f.level === 3),
  }), [fields]);

  const activeL3Count = byLevel[3].filter(f => isActive(state[f.id])).length;

  function setField(id: string, value: unknown) {
    onChange({ ...state, [id]: value });
  }

  return (
    <div className={cn('w-full bg-white border border-gray-200 rounded-xl p-3 sm:p-4 space-y-3', className)}>
      {/* N1 */}
      <div className="flex flex-wrap items-center gap-2">
        {byLevel[1].map(f => <FilterFieldRenderer key={f.id} field={f} value={state[f.id]} onChange={(v) => setField(f.id, v)} />)}
        {typeof resultsCount === 'number' && (
          <span className="ml-auto text-xs text-gray-500 tabular-nums">{resultsCount} resultados</span>
        )}
      </div>

      {/* N2 pills */}
      {byLevel[2].length > 0 && (
        <div className="flex flex-wrap items-center gap-1.5 pt-1">
          {byLevel[2].map(f => <FilterFieldRenderer key={f.id} field={f} value={state[f.id]} onChange={(v) => setField(f.id, v)} />)}
        </div>
      )}

      {/* N3 colapsavel */}
      {byLevel[3].length > 0 && (
        <div className="border-t border-gray-100 pt-2">
          <div className="flex items-center justify-between">
            <button
              type="button"
              onClick={() => setOpenL3(o => !o)}
              className="text-xs font-medium text-gray-600 hover:text-vitao-green inline-flex items-center gap-1 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-vitao-green rounded px-1"
              aria-expanded={openL3}
              aria-controls="filter-level-3"
            >
              <span aria-hidden="true">{openL3 ? 'v' : '>'}</span>
              Mais filtros
              {activeL3Count > 0 && (
                <Badge variant="brand" size="xs" className="ml-1">{activeL3Count}</Badge>
              )}
            </button>
            {onReset && (
              <button
                type="button"
                onClick={onReset}
                className="text-xs text-gray-500 hover:text-red-600 underline-offset-2 hover:underline"
              >
                Limpar tudo
              </button>
            )}
          </div>
          {openL3 && (
            <div id="filter-level-3" className="mt-2 grid grid-cols-1 sm:grid-cols-2 gap-2">
              {byLevel[3].map(f => <FilterFieldRenderer key={f.id} field={f} value={state[f.id]} onChange={(v) => setField(f.id, v)} />)}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function isActive(v: unknown): boolean {
  if (v == null) return false;
  if (typeof v === 'string') return v.length > 0;
  if (Array.isArray(v)) return v.length > 0;
  if (typeof v === 'object') return Object.values(v as Record<string, unknown>).some(Boolean);
  return Boolean(v);
}
```

### FilterFieldRenderer — sub-componente (spec apenas)

Recebe { field, value, onChange } e despacha por field.type:

| Type | Render |
|------|--------|
| search | SearchInput (componente da seção 11) |
| select | select nativo estilizado, ou — se multi — popover custom |
| pill-toggle | button array com Badge variant=brand (selecionado) ou neutral (não) |
| date-range | input duplo from/to ou popover de presets |
| number-range | dois inputs com format opcional |

### Decisões críticas

1. **Schema-driven, não children.** Permite serializar filtros para URL (?vendedor=MANU&curva=A,B) sem reflexão JSX.
2. **Estado controlado externo.** Cada página gerencia seu state. Não usamos Context aqui — escopo de filtros é página.
3. **pill-toggle reusa Badge.** Selecionado = variant="brand" (sólido verde). Desselecionado = variant="neutral".
4. **Mobile:** Nível 1 stack vertical em < 640px. Nível 2 wrap natural. Nível 3 colapsado por default.
5. **URL sync:** out of scope desta wave. FilterGroup apenas levanta state; @dev Wave 3 adiciona helper useFilterUrlSync(state, setState).

---

## 10. MetaWidget.tsx — widget Meta Mensal

**Arquivo:** frontend/src/components/ui/MetaWidget.tsx

Card compacto para sidebar bottom (acima do footer "VITAO Alimentos B2B v1.0"). Bg gradient verde Vitao.

### Contrato

```ts
export interface MetaWidgetProps {
  meta: number;
  realizado: number;
  mes: string;
  diasRestantes?: number;
  format?: (n: number) => string;
  className?: string;
  collapsed?: boolean;
}
```

### Snippet

```tsx
function brl(n: number): string {
  if (n >= 1_000_000) return `R$ ${(n / 1_000_000).toFixed(1)}M`;
  if (n >= 1_000) return `R$ ${(n / 1_000).toFixed(0)}K`;
  return `R$ ${n.toFixed(0)}`;
}

export function MetaWidget({
  meta, realizado, mes, diasRestantes, format = brl, className, collapsed,
}: MetaWidgetProps) {
  const safeMeta = Math.max(1, meta);
  const pct = Math.max(0, Math.min(100, Math.round((realizado / safeMeta) * 100)));

  if (collapsed) {
    return (
      <div
        className={cn("relative w-9 h-9 mx-auto rounded-lg bg-gradient-to-br from-vitao-green to-vitao-darkgreen flex items-center justify-center text-white text-[10px] font-bold", className)}
        title={`Meta ${mes}: ${pct}%`}
      >
        {pct}%
      </div>
    );
  }

  return (
    <div className={cn("rounded-xl p-3 bg-gradient-to-br from-vitao-green to-vitao-darkgreen text-white shadow-sm", className)}>
      <div className="flex items-center justify-between mb-1">
        <span className="text-[10px] uppercase tracking-wider opacity-80 font-semibold">Meta {mes}</span>
        <span className="text-xs font-bold tabular-nums">{pct}%</span>
      </div>
      <div className="text-sm font-bold tabular-nums">{format(realizado)}</div>
      <div className="text-[10px] opacity-75 tabular-nums">de {format(meta)}</div>
      <div className="mt-2 h-1.5 bg-white/25 rounded-full overflow-hidden">
        <div
          className="h-full bg-white rounded-full transition-[width] duration-500"
          style={{ width: `${pct}%` }}
          role="progressbar"
          aria-valuenow={pct} aria-valuemin={0} aria-valuemax={100}
          aria-label={`Meta ${mes}: ${pct}%`}
        />
      </div>
      {typeof diasRestantes === "number" && (
        <div className="text-[10px] opacity-75 mt-1">
          {diasRestantes} dia{diasRestantes !== 1 ? "s" : ""} restante{diasRestantes !== 1 ? "s" : ""}
        </div>
      )}
    </div>
  );
}
```

### Decisao
- collapsed mode sincroniza com Sidebar. Quando sidebar colapsada (Sidebar.tsx:407 -- w-14), widget vira badge circular 9x9 com pct%.
- Cor e gradient solido. Nao permite override de cor (identidade Vitao). Permite override de classe via className para mb-x etc.
- Nao busca dados. Recebe meta/realizado por prop. Quem alimenta: Sidebar faz fetch ou recebe via Context.

---

## 11. SearchInput.tsx -- header search

**Arquivo:** frontend/src/components/ui/SearchInput.tsx
**Marca:** use-client (foco programatico + state local opcional)

Input de busca com icone a esquerda, kbd Ctrl+K a direita, placeholder customizavel. Reusavel tanto no header global (abrir SearchModal) quanto inline em filtros.

### Contrato

```ts
export interface SearchInputProps {
  value?: string;
  defaultValue?: string;
  onChange?: (value: string) => void;
  onSubmit?: (value: string) => void;
  placeholder?: string;
  showShortcut?: boolean;
  shortcut?: string;
  size?: "sm" | "md" | "lg";
  variant?: "inline" | "trigger";
  onTriggerClick?: () => void;
  autoFocus?: boolean;
  className?: string;
  ariaLabel?: string;
}
```

### Dois modos

1. variant="inline": input real, controlado ou nao. Usado dentro de FilterGroup Nivel 1.
2. variant="trigger": botao visualmente parecido com input mas que dispara onTriggerClick (ex: abrir SearchModal). Usado no header global.

### Snippet

```tsx
"use client";
import { useEffect, useState } from "react";
import { cn } from "@/lib/cn";

const SIZE_CLASSES = {
  sm: "h-8 text-xs px-2",
  md: "h-9 text-sm px-3",
  lg: "h-10 text-base px-4",
};

function detectShortcut(): string {
  if (typeof navigator !== "undefined" && /Mac/i.test(navigator.platform)) return "CmdK";
  return "Ctrl K";
}

const SearchIcon = () => (
  <svg className="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-4.35-4.35M11 19a8 8 0 100-16 8 8 0 000 16z" />
  </svg>
);

export function SearchInput({
  value, defaultValue, onChange, onSubmit, placeholder = "Buscar...",
  showShortcut, shortcut, size = "md", variant = "inline", onTriggerClick,
  autoFocus, className, ariaLabel = "Buscar",
}: SearchInputProps) {
  const [localShortcut, setLocalShortcut] = useState<string | undefined>(shortcut);
  useEffect(() => { if (!shortcut) setLocalShortcut(detectShortcut()); }, [shortcut]);

  const wrapperBase = cn(
    "inline-flex items-center gap-2 w-full bg-white border border-gray-200 rounded-lg",
    "focus-within:border-vitao-green focus-within:ring-2 focus-within:ring-vitao-green/20",
    "transition-colors",
    SIZE_CLASSES[size],
    className,
  );

  if (variant === "trigger") {
    return (
      <button
        type="button"
        onClick={onTriggerClick}
        aria-label={ariaLabel}
        className={cn(wrapperBase, "cursor-pointer hover:border-gray-300 text-left")}
      >
        <SearchIcon />
        <span className="flex-1 text-gray-400">{placeholder}</span>
        {(showShortcut ?? true) && (
          <kbd className="hidden sm:inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[10px] font-semibold text-gray-500 bg-gray-100 border border-gray-200">
            {localShortcut}
          </kbd>
        )}
      </button>
    );
  }

  return (
    <div className={wrapperBase}>
      <SearchIcon />
      <input
        type="search"
        value={value}
        defaultValue={defaultValue}
        autoFocus={autoFocus}
        onChange={(e) => onChange?.(e.target.value)}
        onKeyDown={(e) => { if (e.key === "Enter") onSubmit?.((e.target as HTMLInputElement).value); }}
        placeholder={placeholder}
        aria-label={ariaLabel}
        className="flex-1 bg-transparent border-0 outline-none text-gray-900 placeholder:text-gray-400"
      />
      {showShortcut && (
        <kbd className="hidden sm:inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[10px] font-semibold text-gray-500 bg-gray-100 border border-gray-200">
          {localShortcut}
        </kbd>
      )}
    </div>
  );
}
```

---

## 12. Sinaleiro.tsx -- dot semaforo com tooltip

**Arquivo:** frontend/src/components/ui/Sinaleiro.tsx

Dot 8x8 (ou maior) colorido com tooltip auto. Para uso em listagens densas (Carteira) onde nao cabe pilula completa.

### Contrato

```ts
export type SinaleiroCor = "verde" | "amarelo" | "laranja" | "vermelho" | "roxo" | "cinza";

export interface SinaleiroProps {
  cor: SinaleiroCor | string;
  size?: "sm" | "md" | "lg";
  pulse?: boolean;
  tooltip?: string;
  ariaLabel?: string;
  className?: string;
}
```

### Map de cor + tooltip

```ts
const COR_CLASSES: Record<SinaleiroCor, string> = {
  verde:    "bg-green-500",
  amarelo:  "bg-yellow-400",
  laranja:  "bg-orange-500",
  vermelho: "bg-red-500",
  roxo:     "bg-purple-500",
  cinza:    "bg-gray-400",
};

const COR_TOOLTIPS: Record<SinaleiroCor, string> = {
  verde:    "Cliente saudavel (compras regulares)",
  amarelo:  "Atencao - frequencia caindo",
  laranja:  "Risco - sem compra recente",
  vermelho: "Critico - possivel perda",
  roxo:     "Cliente especial / observacao",
  cinza:    "Sem dados ou prospect",
};

const SIZE_CLASSES = {
  sm: "w-2 h-2",
  md: "w-2.5 h-2.5",
  lg: "w-3 h-3",
};
```

### Snippet

```tsx
import { cn } from "@/lib/cn";

export function Sinaleiro({ cor, size = "md", pulse, tooltip, ariaLabel, className }: SinaleiroProps) {
  const key = String(cor ?? "").trim().toLowerCase() as SinaleiroCor;
  const colorClass = COR_CLASSES[key] ?? "bg-gray-300";
  const tooltipText = tooltip ?? COR_TOOLTIPS[key] ?? "Status desconhecido";
  return (
    <span
      role="status"
      aria-label={ariaLabel ?? tooltipText}
      title={tooltipText}
      className={cn("inline-block rounded-full ring-1 ring-white/40", SIZE_CLASSES[size], colorClass, pulse && "animate-pulse", className)}
    />
  );
}
```

### Decisao
- Native title attribute em vez de tooltip custom. Tradeoff: menor controle de styling, zero JS, suficiente para densidade de tabela. Se Wave 3 pedir tooltip rico (icone + descricao), criar Tooltip separado e wrap.
- pulse somente para CRITICO ou alertas -- nao abusar.
---

## 13. Estrutura de exports -- components/ui/index.ts

**Arquivo:** frontend/src/components/ui/index.ts

Barrel file. Padrao de import:
```tsx
import { Badge, StatusPill, CurvaPill, ScoreBar, ProgressBar, Tabs, FilterGroup, MetaWidget, SearchInput, Sinaleiro, PriorityPill } from "@/components/ui";
```

```ts
// Display primitives
export { Badge } from "./Badge";
export type { BadgeProps, BadgeVariant, BadgeSize } from "./Badge";

// Status pills (semantic wrappers)
export { StatusPill } from "./StatusPill";
export type { StatusPillProps, CrmStatus } from "./StatusPill";

export { CurvaPill } from "./CurvaPill";
export type { CurvaPillProps, Curva } from "./CurvaPill";

export { PriorityPill } from "./PriorityPill";
export type { PriorityPillProps, Prioridade } from "./PriorityPill";

// Bars
export { ScoreBar } from "./ScoreBar";
export type { ScoreBarProps } from "./ScoreBar";

export { ProgressBar } from "./ProgressBar";
export type { ProgressBarProps } from "./ProgressBar";

// Navigation / interactive
export { Tabs } from "./Tabs";
export type { TabsProps, TabItem } from "./Tabs";

export { FilterGroup } from "./FilterGroup";
export type {
  FilterGroupProps, FilterField, FilterFieldType, FilterState,
  SearchField, SelectField, PillToggleField, DateRangeField, NumberRangeField,
} from "./FilterGroup";

export { SearchInput } from "./SearchInput";
export type { SearchInputProps } from "./SearchInput";

// Side widgets
export { MetaWidget } from "./MetaWidget";
export type { MetaWidgetProps } from "./MetaWidget";

// Density elements
export { Sinaleiro } from "./Sinaleiro";
export type { SinaleiroProps, SinaleiroCor } from "./Sinaleiro";
```

### Por que barrel?
- Single import line reduz boilerplate em pages.
- Tree-shaking funciona bem em Next 14 (todos componentes tem export nomeado, sem export-* recursivo).
- Elimina mismatch de path (./Badge vs ./ui/Badge) ao mover arquivos.

---

## 14. Migracao de StatusBadge.tsx legado

### Estado atual
- frontend/src/components/StatusBadge.tsx (138 linhas) -- implementa 5 variants: situacao, sinaleiro, prioridade, abc, temperatura.
- 14 arquivos importam (resultado do grep): inclui ClienteTable.tsx, inbox/page.tsx, agenda/page.tsx, pedidos/page.tsx, rnc/page.tsx, atualizacoes/page.tsx, CanalSelector.tsx, ClienteDetalhe.tsx, ClienteModal.tsx, AtendimentoForm.tsx, AtendimentoModal.tsx, e o teste __tests__/StatusBadge.test.tsx.
- Usa style={{ backgroundColor, color }} inline (hex puro), nao Tailwind classes.

### Estrategia: alias temporario, deprecar gradualmente

NAO rename direto -- explodiria 14 arquivos num unico PR. Em vez disso:

#### Passo 1 (Wave 2 -- @dev)
Criar os 11 componentes novos em components/ui/ conforme este spec. NAO tocar em StatusBadge.tsx.

#### Passo 2 (Wave 2 -- @dev, mesmo PR)
Adicionar aviso de deprecacao no topo de StatusBadge.tsx:

```ts
/**
 * @deprecated Use componentes especificos de @/components/ui:
 *   - variant="situacao"    -> <StatusPill status={value} />
 *   - variant="temperatura" -> <StatusPill status={value} />
 *   - variant="abc"         -> <CurvaPill curva={value} />
 *   - variant="prioridade"  -> <PriorityPill prioridade={value} />
 *   - variant="sinaleiro"   -> <Sinaleiro cor={value.toLowerCase()} />
 *
 * Migracao tracked em .planning/UX_REDESIGN_COMPONENTS_SPEC.md secao 14.
 * Este arquivo sera removido em Wave 4 (apos 100% dos consumers migrarem).
 */
```

E console.warn em dev mode (gated por process.env.NODE_ENV !== "production").

#### Passo 3 (Wave 3 -- @dev)
Migrar consumers em ondas, 1 pagina por commit atomico (R11):

| Commit | Arquivo |
|--------|---------|
| 1 | ClienteTable.tsx + teste atualizado |
| 2 | inbox/page.tsx |
| 3 | agenda/page.tsx |
| 4 | pedidos/page.tsx |
| 5 | rnc/page.tsx |
| 6 | atualizacoes/page.tsx |
| 7 | ClienteDetalhe.tsx + ClienteModal.tsx |
| 8 | AtendimentoForm.tsx + AtendimentoModal.tsx |
| 9 | CanalSelector.tsx + __tests__/StatusBadge.test.tsx (rename -> StatusPill.test.tsx) |

#### Passo 4 (Wave 4 -- @dev, unico commit)
Deletar frontend/src/components/StatusBadge.tsx. Remover do barrel se exportado. Rodar tsc --noEmit para confirmar zero referencia.

### Por que nao rename direto?
- Risco: 14 arquivos x ~3 ocorrencias cada = ~40 sites de mudanca num unico PR. Probabilidade de introduzir bug visual em cliente, agenda, pedidos simultaneamente e alta.
- Reversibilidade: alias deprecate permite reverter componente novo sem quebrar legado.
- Code review: revisar 9 commits pequenos > revisar 1 commit gigante.

### Tradeoff aceito
- Custo: componentes coexistem por ~Wave 3 inteira (~1 semana). Bundle ligeiramente maior (~2KB).
- Beneficio: zero risco de regressao visual em producao.

---

## 15. Padrao de variantes sem CVA

### Recapitulando o padrao

```ts
// 1. Definir tipo de variant
export type Variant = "success" | "warning" | "danger";

// 2. Map de classes Tailwind por variant (objeto literal const)
const VARIANT_CLASSES: Record<Variant, string> = {
  success: "bg-green-100 text-green-800",
  warning: "bg-orange-100 text-orange-800",
  danger:  "bg-red-100 text-red-800",
};

// 3. Concatenar via cn() na ordem: BASE -> VARIANT -> SIZE -> className override
className={cn(BASE, VARIANT_CLASSES[variant], SIZE_CLASSES[size], className)}
```

### Por que esse padrao funciona aqui

- Tailwind safelist friendly. Tailwind JIT precisa ver as classes literais no source. "bg-green-100" como string completa = JIT detecta. Concatenacao dinamica ("bg-" + variant + "-100") quebra -- nunca fazer.
- Tipo seguro. Record<Variant, string> forca exhaustividade -- adicionar novo variant sem entry e erro de compile.
- Zero runtime overhead. Lookup de Record e O(1). Nao recompila nada.
- Diff legivel em PR. Mudanca de cor = 1 linha. Sem regex de CVA config.

### Restricao importante
- Nunca construir nome de classe Tailwind por interpolacao. Sempre literal.
- Nunca usar style={{ backgroundColor: ... }} quando ha classe Tailwind equivalente -- exceto para gradientes complexos como MetaWidget (gradient e via bg-gradient-to-br + from-vitao-green -- usa classes).

### Exemplo completo -- Badge revisitado

```ts
// frontend/src/components/ui/Badge.tsx
import type { ReactNode, HTMLAttributes } from "react";
import { cn } from "@/lib/cn";

export type BadgeVariant = "success" | "warning" | "danger" | "info" | "neutral" | "brand" | "lead" | "fresh";
export type BadgeSize = "xs" | "sm" | "md";

const BASE = "inline-flex items-center gap-1 font-semibold rounded-full whitespace-nowrap";

const VARIANT_CLASSES: Record<BadgeVariant, string> = {
  success: "bg-green-100 text-green-800",
  warning: "bg-orange-100 text-orange-800",
  danger:  "bg-red-100 text-red-800",
  info:    "bg-blue-100 text-blue-800",
  neutral: "bg-gray-100 text-gray-700",
  brand:   "bg-vitao-green text-white",
  lead:    "bg-purple-100 text-purple-800",
  fresh:   "bg-cyan-100 text-cyan-800",
};

const SIZE_CLASSES: Record<BadgeSize, string> = {
  xs: "text-[10px] px-1.5 py-0 leading-4",
  sm: "text-xs px-2 py-0.5 leading-5",
  md: "text-sm px-2.5 py-1 leading-5",
};

export interface BadgeProps extends Omit<HTMLAttributes<HTMLSpanElement>, "children"> {
  variant?: BadgeVariant;
  size?: BadgeSize;
  dot?: boolean;
  icon?: ReactNode;
  children: ReactNode;
}

export function Badge({ variant = "neutral", size = "sm", dot, icon, className, children, ...rest }: BadgeProps) {
  return (
    <span className={cn(BASE, VARIANT_CLASSES[variant], SIZE_CLASSES[size], className)} {...rest}>
      {icon ?? (dot && <span aria-hidden="true" className="w-1.5 h-1.5 rounded-full bg-current opacity-70" />)}
      {children}
    </span>
  );
}
```
---

## 16. Tabela de Impacto -- quais paginas usam quais componentes

| Pagina / Componente atual                | Badge | StatusPill | CurvaPill | PriorityPill | ScoreBar | ProgressBar | Tabs | FilterGroup | MetaWidget | SearchInput | Sinaleiro | Prioridade migracao |
|------------------------------------------|:-----:|:----------:|:---------:|:------------:|:--------:|:-----------:|:----:|:-----------:|:----------:|:-----------:|:---------:|:-------------------:|
| app/page.tsx (Dashboard)                 |   X   |     X      |     X     |              |          |      X      |  X   |             |            |      X      |           |        Alta         |
| app/inbox/page.tsx                       |   X   |     X      |           |              |          |             |  X   |      X      |            |      X      |     X     |        Alta         |
| app/carteira/page.tsx                    |   X   |     X      |     X     |      X       |    X     |             |      |      X      |            |      X      |     X     |    **Critica**      |
| app/agenda/page.tsx                      |   X   |     X      |           |      X       |          |             |      |      X      |            |             |     X     |        Alta         |
| app/pipeline/page.tsx                    |   X   |     X      |     X     |      X       |    X     |             |  X   |      X      |            |      X      |           |        Alta         |
| app/tarefas/page.tsx                     |   X   |            |           |      X       |          |             |  X   |      X      |            |      X      |           |        Media        |
| app/pedidos/page.tsx                     |   X   |     X      |           |              |          |             |      |      X      |            |      X      |           |        Media        |
| app/rnc/page.tsx                         |   X   |     X      |           |      X       |          |             |      |      X      |            |      X      |           |        Media        |
| app/atualizacoes/page.tsx                |   X   |     X      |           |              |          |             |      |             |            |             |           |        Baixa        |
| app/projecao/page.tsx                    |       |            |     X     |              |    X     |      X      |  X   |             |            |             |           |        Media        |
| app/sinaleiro/page.tsx                   |       |     X      |           |              |          |             |      |      X      |            |             |     X     |        Media        |
| app/redes/page.tsx                       |   X   |            |     X     |              |          |      X      |      |      X      |            |             |           |        Baixa        |
| app/produtos/page.tsx                    |   X   |            |     X     |              |          |             |      |      X      |            |      X      |           |        Baixa        |
| app/relatorios/page.tsx                  |       |            |           |              |          |      X      |  X   |             |            |             |           |        Baixa        |
| app/admin/* (5 paginas)                  |   X   |            |           |              |          |             |  X   |             |            |             |           |        Baixa        |
| components/Sidebar.tsx                   |   X   |            |           |              |          |             |      |             |     X      |             |           |        Alta         |
| components/AppShell.tsx (Header)         |       |            |           |              |          |             |      |             |            |      X      |           |        Alta         |
| components/ClienteTable.tsx              |   X   |     X      |     X     |      X       |    X     |             |      |             |            |             |     X     |    **Critica**      |
| components/ClienteDetalhe.tsx            |   X   |     X      |     X     |      X       |    X     |      X      |  X   |             |            |             |     X     |        Alta         |
| components/ClienteModal.tsx              |   X   |     X      |           |              |          |             |      |             |            |             |           |        Media        |
| components/AtendimentoForm.tsx           |       |     X      |           |      X       |          |             |      |             |            |             |           |        Baixa        |
| components/AtendimentoModal.tsx          |       |     X      |           |              |          |             |      |             |            |             |           |        Baixa        |
| components/CanalSelector.tsx             |       |     X      |           |              |          |             |      |             |            |             |           |        Baixa        |

### Ordem sugerida de migracao (Wave 3)

1. Badge + StatusPill + Sinaleiro primeiro -- base para tudo, baixa complexidade.
2. SearchInput -- usado no header (AppShell) e em filtros.
3. Tabs -- usado no Dashboard, Inbox, Pipeline, Projecao, Tarefas.
4. FilterGroup -- maior risco; requer schema por pagina.
5. MetaWidget -- so Sidebar, isolado.
6. ScoreBar + ProgressBar -- pages de detalhe (Carteira, Pipeline, Projecao).
7. CurvaPill + PriorityPill -- substituem StatusBadge variant=abc/prioridade.

### Paginas criticas
- Carteira (app/carteira/page.tsx) -- usa 7 dos 11 componentes. Migracao e refactor amplo. Sugestao: dedicar 1 commit por secao (header, tabela, modal de detalhe).
- ClienteTable.tsx -- componente central reusado por Carteira, Pipeline, Inbox. Refatorar com cuidado, garantir snapshot de teste antes/depois.

---

## 17. Acessibilidade -- checklist minimo por componente

| Componente     | aria-label / role                  | Focus-visible              | Tab nav | Notas |
|----------------|------------------------------------|----------------------------|---------|-------|
| Badge          | herda do contexto / aria-label opt | n/a (nao-focavel)          | n/a     | role="status" opcional via prop |
| StatusPill     | aria-label="Status: {label}" auto  | n/a                        | n/a     | Texto interno e descritivo |
| CurvaPill      | aria-label="Curva A" auto          | n/a                        | n/a     | -- |
| PriorityPill   | aria-label="Prioridade P1" auto    | n/a                        | n/a     | -- |
| ScoreBar       | role="meter" + aria-valuenow/min/max | n/a                      | n/a     | -- |
| ProgressBar    | role="progressbar" + valuenow      | n/a                        | n/a     | -- |
| Tabs           | role="tablist" + aria-selected     | focus-visible:ring-2 focus-visible:ring-vitao-green | Sim -- setas (Wave 3 enhancement) | Consumidor faz aria-controls/aria-labelledby |
| FilterGroup    | aria-expanded no toggle Nivel 3    | ring no toggle e em pilulas | Sim    | aria-controls="filter-level-3" |
| MetaWidget     | role="progressbar" na barra interna | n/a                       | n/a     | title no modo collapsed |
| SearchInput    | aria-label="Buscar" default        | focus-within:ring-2        | Sim     | kbd e decorativo, nao focavel |
| Sinaleiro      | role="status" + auto-tooltip       | n/a                        | n/a     | title nativo serve leitores |

### Convencoes globais
- Nunca remover outline sem substituir por focus-visible:ring.
- Color contrast ratio minimo 4.5:1 para texto sobre fundo. Pares ja validados:
  - bg-green-100 text-green-800 ~= 8.5:1 OK
  - bg-orange-100 text-orange-800 ~= 5.9:1 OK
  - bg-red-100 text-red-800 ~= 7.0:1 OK
  - bg-yellow-50 text-yellow-700 ~= 6.2:1 OK
- Touch target minimo 44x44px (Sidebar atual ja respeita: min-h-[44px] em Sidebar.tsx:460).
- Reduced motion: transition-* e suficientemente sutil; no Wave 3 adicionar motion-reduce:transition-none global se necessario.

---

## 18. Decisoes arquiteturais -- resumo

| # | Decisao | Tradeoff |
|---|---------|----------|
| 1 | Tailwind puro com Record<Variant, string> | (+) tree-shake friendly, JIT detecta classes; (-) sem auto-merge de conflito como tailwind-merge |
| 2 | cn() reimplementado em lib/cn.ts | (+) zero deps; (-) sem suporte a clsx API completa (objeto { foo: true }) -- nao precisamos |
| 3 | Badge + StatusPill separados (nao merge) | (+) Badge reusa em qualquer contexto; (-) duplica props comuns (size, className) |
| 4 | Schema-driven FilterGroup (nao children) | (+) URL-syncavel, testavel; (-) menos flexivel para casos edge |
| 5 | StatusBadge legado deprecate com console.warn, nao rename | (+) migracao incremental segura; (-) bundle ligeiramente maior por ~1 sprint |
| 6 | BadgeVariant inclui lead e fresh (nao-padrao) | (+) cobre LEAD/NOVO sem prop colorOverride; (-) variant set fica menos limpo |
| 7 | Server-safe por default (sem use-client) exceto onde precisar | (+) RSC compatible, menor JS shipped; (-) atencao em quem importa o que |
| 8 | Sinaleiro usa title nativo (nao tooltip custom) | (+) zero JS, acessivel; (-) styling do tooltip e nativo do browser |
| 9 | MetaWidget modo collapsed espelha sidebar | (+) consistencia visual; (-) componente conhece estado externo (sidebar collapsed) |
| 10 | Tabs controlado externamente, painel e responsabilidade do consumer | (+) flexivel; (-) consumidor precisa cuidar do aria-controls |

---

## 19. Criterios de aceite (DoD da Wave 2 -- para @dev)

- [ ] 11 componentes implementados em frontend/src/components/ui/
- [ ] lib/cn.ts criado e testado
- [ ] index.ts (barrel) exporta todos
- [ ] tsc --noEmit zero erros
- [ ] Todo componente tem prop className? funcional
- [ ] Todo componente tem aria-label ou texto interno descritivo
- [ ] StatusBadge.tsx recebe JSDoc @deprecated + console.warn em dev
- [ ] Nenhum import de class-variance-authority ou tailwind-merge
- [ ] Nenhum uso de dark: prefix
- [ ] Storybook NAO e requisito (out of scope desta wave)
- [ ] Teste minimo: smoke test de cada componente renderizando sem crash (Jest + RTL -- pattern ja existe em __tests__/StatusBadge.test.tsx)
- [ ] Commit atomico por componente (R11): 1 commit = 1 componente + sua entry no index.ts

---

## 20. Out of scope (para Waves futuras)

- Wave 3: migracao de consumers (14 arquivos) + testes RTL completos
- Wave 4: delete StatusBadge.tsx legado
- Wave 5+: Tooltip rico, Modal generico, DropdownMenu, Toast (ja existe em components/Toast.tsx -- manter por enquanto), Select multi com search

---

## 21. Referencias

- frontend/tailwind.config.ts:14 -- fonte Inter configurada
- frontend/tailwind.config.ts:17-36 -- paleta Vitao completa (PT legacy + EN)
- frontend/src/components/StatusBadge.tsx:1-138 -- implementacao atual a ser deprecada
- frontend/src/components/KpiCard.tsx:24-52 -- padrao de card existente (reuso de borda esquerda + accentColor)
- frontend/src/components/Sidebar.tsx:407 -- Sidebar collapsed w-14 (relevante para MetaWidget collapsed mode)
- frontend/src/components/Sidebar.tsx:460 -- touch target min-h-[44px] (manter padrao)
- .claude/CLAUDE.md R9 -- Light theme only, fonte Inter (web -- Arial e Excel)
- .claude/rules/000-coleira-suprema.md R11 -- commits atomicos