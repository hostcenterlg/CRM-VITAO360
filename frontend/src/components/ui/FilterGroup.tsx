'use client';
// frontend/src/components/ui/FilterGroup.tsx
// Declarative 3-level filter group: search + select (N1), pill-toggles (N2), collapsible extras (N3)
// date-range and number-range: TODO for iteration 2 (Wave 3)
import { useMemo, useState } from 'react';
import { cn } from '@/lib/cn';
import { Badge } from './Badge';

// ── Types ──────────────────────────────────────────────────────────────────

export type FilterFieldType =
  | 'search'
  | 'select'
  | 'pill-toggle'
  | 'date-range'    // TODO: iteration 2
  | 'number-range'; // TODO: iteration 2

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

/** @todo date-range — implement in Wave 3 iteration 2 */
export interface DateRangeField extends BaseFilterField {
  type: 'date-range';
  presets?: Array<{ id: string; label: string; from: string; to: string }>;
}

/** @todo number-range — implement in Wave 3 iteration 2 */
export interface NumberRangeField extends BaseFilterField {
  type: 'number-range';
  min?: number;
  max?: number;
  step?: number;
  format?: (n: number) => string;
}

export type FilterField =
  | SearchField
  | SelectField
  | PillToggleField
  | DateRangeField
  | NumberRangeField;

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

// ── Helpers ────────────────────────────────────────────────────────────────

function isActive(v: unknown): boolean {
  if (v == null) return false;
  if (typeof v === 'string') return v.length > 0;
  if (Array.isArray(v)) return v.length > 0;
  if (typeof v === 'object') return Object.values(v as Record<string, unknown>).some(Boolean);
  return Boolean(v);
}

// ── Field renderer ─────────────────────────────────────────────────────────

interface RendererProps {
  field: FilterField;
  value: unknown;
  onChange: (v: unknown) => void;
}

function FilterFieldRenderer({ field, value, onChange }: RendererProps) {
  if (field.type === 'search') {
    return (
      <div
        className={cn(
          'inline-flex items-center gap-2 bg-white border border-gray-200 rounded-lg px-3 h-9 focus-within:border-vitao-green focus-within:ring-2 focus-within:ring-vitao-green/20 transition-colors',
          field.className,
        )}
      >
        <svg className="w-4 h-4 text-gray-500 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-4.35-4.35M11 19a8 8 0 100-16 8 8 0 000 16z" />
        </svg>
        <input
          type="search"
          value={typeof value === 'string' ? value : ''}
          onChange={(e) => onChange(e.target.value)}
          placeholder={field.placeholder ?? `${field.label}...`}
          aria-label={field.label}
          className="flex-1 bg-transparent border-0 outline-none text-sm text-gray-900 placeholder:text-gray-400 min-w-[120px]"
        />
      </div>
    );
  }

  if (field.type === 'select') {
    return (
      <select
        value={typeof value === 'string' ? value : ''}
        onChange={(e) => onChange(e.target.value)}
        aria-label={field.label}
        className={cn(
          'h-9 bg-white border border-gray-200 rounded-lg px-3 text-sm text-gray-700 focus:outline-none focus:border-vitao-green focus:ring-2 focus:ring-vitao-green/20 transition-colors cursor-pointer',
          field.className,
        )}
      >
        <option value="">{field.placeholder ?? field.label}</option>
        {field.options.map((opt) => (
          <option key={opt.value} value={opt.value}>
            {opt.label}{opt.count != null ? ` (${opt.count})` : ''}
          </option>
        ))}
      </select>
    );
  }

  if (field.type === 'pill-toggle') {
    const pillField = field as PillToggleField;
    const selected: string[] = Array.isArray(value)
      ? (value as string[])
      : value && typeof value === 'string'
        ? [value]
        : [];

    const toggle = (val: string) => {
      if (pillField.multi) {
        const next = selected.includes(val)
          ? selected.filter((s) => s !== val)
          : [...selected, val];
        onChange(next);
      } else {
        onChange(selected.includes(val) ? '' : val);
      }
    };

    return (
      <div className={cn('flex flex-wrap gap-1.5', field.className)}>
        {field.options.map((opt) => {
          const active = selected.includes(opt.value);
          return (
            <button
              key={opt.value}
              type="button"
              onClick={() => toggle(opt.value)}
              aria-pressed={active}
              className={cn(
                'inline-flex items-center gap-1 text-xs font-semibold px-2 py-0.5 rounded-full border transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-vitao-green focus-visible:ring-offset-1',
                active
                  ? 'bg-vitao-green text-white border-vitao-green'
                  : 'bg-gray-100 text-gray-700 border-gray-200 hover:border-gray-300 hover:bg-gray-200',
              )}
            >
              {opt.icon && <span aria-hidden="true">{opt.icon}</span>}
              {opt.label}
              {opt.count != null && (
                <span className={cn(
                  'text-xs tabular-nums',
                  active ? 'opacity-80' : 'text-gray-500',
                )}>
                  {opt.count}
                </span>
              )}
            </button>
          );
        })}
      </div>
    );
  }

  // date-range and number-range: TODO iteration 2
  return (
    <div className={cn('text-xs text-gray-500 italic', field.className)}>
      {field.label} (em breve)
    </div>
  );
}

// ── Main component ─────────────────────────────────────────────────────────

export function FilterGroup({
  fields,
  state,
  onChange,
  onReset,
  defaultLevel3Open = false,
  className,
  resultsCount,
}: FilterGroupProps) {
  const [openL3, setOpenL3] = useState(defaultLevel3Open);

  const byLevel = useMemo(() => ({
    1: fields.filter((f) => f.level === 1),
    2: fields.filter((f) => f.level === 2),
    3: fields.filter((f) => f.level === 3),
  }), [fields]);

  const activeL3Count = byLevel[3].filter((f) => isActive(state[f.id])).length;

  function setField(id: string, value: unknown) {
    onChange({ ...state, [id]: value });
  }

  return (
    <div
      className={cn(
        'w-full bg-white border border-gray-200 rounded-xl p-3 sm:p-4 space-y-3',
        className,
      )}
    >
      {/* Level 1 — search + selects */}
      <div className="flex flex-wrap items-center gap-2">
        {byLevel[1].map((f) => (
          <FilterFieldRenderer
            key={f.id}
            field={f}
            value={state[f.id]}
            onChange={(v) => setField(f.id, v)}
          />
        ))}
        {typeof resultsCount === 'number' && (
          <span className="ml-auto text-xs text-gray-500 tabular-nums">
            {resultsCount} resultados
          </span>
        )}
      </div>

      {/* Level 2 — pill toggles */}
      {byLevel[2].length > 0 && (
        <div className="flex flex-wrap items-center gap-1.5 pt-1">
          {byLevel[2].map((f) => (
            <FilterFieldRenderer
              key={f.id}
              field={f}
              value={state[f.id]}
              onChange={(v) => setField(f.id, v)}
            />
          ))}
        </div>
      )}

      {/* Level 3 — collapsible extras */}
      {byLevel[3].length > 0 && (
        <div className="border-t border-gray-100 pt-2">
          <div className="flex items-center justify-between">
            <button
              type="button"
              onClick={() => setOpenL3((o) => !o)}
              className="text-xs font-medium text-gray-600 hover:text-vitao-green inline-flex items-center gap-1 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-vitao-green rounded px-1"
              aria-expanded={openL3}
              aria-controls="filter-level-3"
            >
              <span aria-hidden="true">{openL3 ? '▾' : '▸'}</span>
              Mais filtros
              {activeL3Count > 0 && (
                <Badge variant="brand" size="xs" className="ml-1">
                  {activeL3Count}
                </Badge>
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
            <div
              id="filter-level-3"
              className="mt-2 grid grid-cols-1 sm:grid-cols-2 gap-2"
            >
              {byLevel[3].map((f) => (
                <FilterFieldRenderer
                  key={f.id}
                  field={f}
                  value={state[f.id]}
                  onChange={(v) => setField(f.id, v)}
                />
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
