'use client';

import { ClienteRegistro, formatBRL } from '@/lib/api';
import StatusBadge from './StatusBadge';

// ---------------------------------------------------------------------------
// ClienteTable — tabela de clientes com ordenacao por coluna
// ---------------------------------------------------------------------------

export type SortDir = 'asc' | 'desc';

export interface SortState {
  by: string;
  dir: SortDir;
}

interface ClienteTableProps {
  registros: ClienteRegistro[];
  loading?: boolean;
  onRowClick?: (cliente: ClienteRegistro) => void;
  sort?: SortState;
  onSort?: (col: string) => void;
  showFaturamento?: boolean;
}

// Mapa: chave da coluna -> campo no ClienteRegistro
const COLS: { key: string; label: string; sortable: boolean; align?: 'right' }[] = [
  { key: 'cnpj',            label: 'CNPJ',         sortable: false },
  { key: 'nome_fantasia',   label: 'Cliente',       sortable: true },
  { key: 'uf',              label: 'UF',            sortable: true },
  { key: 'consultor',       label: 'Consultor',     sortable: true },
  { key: 'situacao',        label: 'Situacao',      sortable: true },
  { key: 'temperatura',     label: 'Temp.',         sortable: true },
  { key: 'score',           label: 'Score',         sortable: true, align: 'right' },
  { key: 'curva_abc',       label: 'ABC',           sortable: true },
  { key: 'sinaleiro',       label: 'Sinal.',        sortable: true },
  { key: 'faturamento_total', label: 'Faturamento', sortable: true, align: 'right' },
];

const SKELETON_ROWS = 8;

// Cores sinaleiro (R9)
const SINALEIRO_COLORS: Record<string, string> = {
  VERDE:    '#00B050',
  AMARELO:  '#FFC000',
  LARANJA:  '#FF8C00',
  VERMELHO: '#FF0000',
  ROXO:     '#7030A0',
};

function SinaleiroDot({ value }: { value?: string }) {
  if (!value) return <span className="text-gray-300">—</span>;
  const upper = value.toUpperCase();
  const color = SINALEIRO_COLORS[upper] ?? '#9CA3AF';
  return (
    <span
      className="inline-flex items-center justify-center"
      title={value}
      aria-label={`Sinaleiro: ${value}`}
    >
      <span
        className="inline-block rounded-full flex-shrink-0 shadow-sm"
        style={{ width: 12, height: 12, background: color }}
        role="img"
      />
    </span>
  );
}

function ScoreCell({ value }: { value?: number }) {
  if (value == null) return <span className="text-gray-300">—</span>;
  const pct = Math.min(100, Math.max(0, value));
  const color = pct >= 70 ? '#00B050' : pct >= 40 ? '#FFC000' : '#FF0000';
  return (
    <span className="inline-flex items-center gap-1.5">
      <span
        className="inline-block rounded-sm overflow-hidden flex-shrink-0"
        style={{ width: 60, height: 5, background: '#E5E7EB' }}
      >
        <span
          className="block h-full rounded-sm"
          style={{ width: `${pct}%`, background: color, transition: 'width 400ms ease-out' }}
        />
      </span>
      <span className="text-xs font-semibold text-gray-700 tabular-nums">{value.toFixed(0)}</span>
    </span>
  );
}

function SortIcon({ col, sort }: { col: string; sort?: SortState }) {
  if (!sort || sort.by !== col) {
    return (
      <svg className="w-3 h-3 text-gray-300 inline ml-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16V4m0 0L3 8m4-4l4 4M17 8v12m0 0l4-4m-4 4l-4-4" />
      </svg>
    );
  }
  return sort.dir === 'asc' ? (
    <svg className="w-3 h-3 text-green-600 inline ml-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 15l7-7 7 7" />
    </svg>
  ) : (
    <svg className="w-3 h-3 text-green-600 inline ml-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
    </svg>
  );
}

// Borda esquerda por sinaleiro (DS-04-G)
function rowBorderStyle(sinaleiro?: string): string {
  const s = sinaleiro?.toUpperCase();
  if (s === 'VERMELHO') return 'border-l-2 border-l-red-500';
  if (s === 'ROXO') return 'border-l-2 border-l-purple-700';
  return '';
}

export default function ClienteTable({
  registros,
  loading = false,
  onRowClick,
  sort,
  onSort,
  showFaturamento = true,
}: ClienteTableProps) {
  const visibleCols = showFaturamento
    ? COLS
    : COLS.filter((c) => c.key !== 'faturamento_total');

  if (loading) {
    return (
      <div className="overflow-x-auto">
        <table className="w-full text-sm" role="table">
          <thead>
            <TableHead cols={visibleCols} sort={sort} onSort={onSort} />
          </thead>
          <tbody>
            {Array.from({ length: SKELETON_ROWS }).map((_, i) => (
              <tr key={i} className="border-t border-gray-100">
                {visibleCols.map((c) => (
                  <td key={c.key} className="px-3 py-2.5">
                    <div
                      className="h-3.5 bg-gray-100 animate-pulse rounded"
                      style={{ width: `${55 + (i * 7 + visibleCols.indexOf(c) * 11) % 40}%` }}
                    />
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    );
  }

  if (registros.length === 0) {
    return (
      <div className="py-16 text-center text-gray-400">
        <svg className="w-10 h-10 mx-auto mb-3 text-gray-200" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
            d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0z" />
        </svg>
        <p className="text-sm font-medium text-gray-500">Nenhum cliente encontrado</p>
        <p className="text-xs text-gray-400 mt-1">Tente ajustar os filtros ou limpar a busca.</p>
      </div>
    );
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm" role="table">
        <thead>
          <TableHead cols={visibleCols} sort={sort} onSort={onSort} />
        </thead>
        <tbody>
          {registros.map((c) => (
            <tr
              key={c.cnpj}
              className={`border-t border-gray-100 transition-colors ${
                onRowClick
                  ? 'cursor-pointer hover:bg-green-50/40 active:bg-green-50'
                  : 'hover:bg-gray-50'
              } ${rowBorderStyle(c.sinaleiro)}`}
              onClick={() => onRowClick?.(c)}
            >
              {/* CNPJ */}
              <td className="px-3 py-2.5 font-mono text-xs text-gray-500 whitespace-nowrap">
                {formatCnpj(c.cnpj)}
              </td>
              {/* Cliente */}
              <td className="px-3 py-2.5 max-w-[200px]">
                <p className="font-medium text-gray-900 truncate">{c.nome_fantasia ?? '—'}</p>
                {c.razao_social && c.razao_social !== c.nome_fantasia && (
                  <p className="text-[11px] text-gray-400 truncate">{c.razao_social}</p>
                )}
              </td>
              {/* UF */}
              <td className="px-3 py-2.5 text-gray-600 whitespace-nowrap text-xs">
                {c.uf ?? '—'}
              </td>
              {/* Consultor */}
              <td className="px-3 py-2.5 text-gray-700 whitespace-nowrap text-xs">
                {c.consultor ?? '—'}
              </td>
              {/* Situacao */}
              <td className="px-3 py-2.5 whitespace-nowrap">
                <StatusBadge value={c.situacao} variant="situacao" small />
              </td>
              {/* Temperatura */}
              <td className="px-3 py-2.5 whitespace-nowrap">
                {c.temperatura ? (
                  <StatusBadge value={c.temperatura} variant="temperatura" small />
                ) : (
                  <span className="text-gray-300">—</span>
                )}
              </td>
              {/* Score */}
              <td className="px-3 py-2.5 whitespace-nowrap">
                <ScoreCell value={c.score} />
              </td>
              {/* ABC */}
              <td className="px-3 py-2.5 whitespace-nowrap">
                {c.curva_abc ? (
                  <StatusBadge value={c.curva_abc} variant="abc" small />
                ) : (
                  <span className="text-gray-300">—</span>
                )}
              </td>
              {/* Sinaleiro */}
              <td className="px-3 py-2.5 whitespace-nowrap">
                <SinaleiroDot value={c.sinaleiro} />
              </td>
              {/* Faturamento */}
              {showFaturamento && (
                <td className="px-3 py-2.5 text-right whitespace-nowrap font-mono text-xs text-gray-800">
                  {c.faturamento_total != null ? formatBRL(c.faturamento_total) : '—'}
                </td>
              )}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Sub-componentes internos
// ---------------------------------------------------------------------------

interface ColDef { key: string; label: string; sortable: boolean; align?: 'right' }

function TableHead({
  cols,
  sort,
  onSort,
}: {
  cols: ColDef[];
  sort?: SortState;
  onSort?: (col: string) => void;
}) {
  return (
    <tr className="bg-gray-50 text-left sticky top-0 z-10" role="row">
      {cols.map((col) => (
        <th
          key={col.key}
          scope="col"
          className={`px-3 py-2 text-[11px] font-semibold text-gray-500 uppercase tracking-wide whitespace-nowrap select-none ${
            col.align === 'right' ? 'text-right' : ''
          } ${col.sortable && onSort ? 'cursor-pointer hover:text-gray-700' : ''}`}
          onClick={() => col.sortable && onSort?.(col.key)}
          aria-sort={
            sort?.by === col.key
              ? sort.dir === 'asc'
                ? 'ascending'
                : 'descending'
              : 'none'
          }
        >
          {col.label}
          {col.sortable && <SortIcon col={col.key} sort={sort} />}
        </th>
      ))}
    </tr>
  );
}

function formatCnpj(cnpj: string): string {
  const digits = cnpj.replace(/\D/g, '').padStart(14, '0');
  if (digits.length !== 14) return cnpj;
  return `${digits.slice(0, 2)}.${digits.slice(2, 5)}.${digits.slice(5, 8)}/${digits.slice(8, 12)}-${digits.slice(12)}`;
}
