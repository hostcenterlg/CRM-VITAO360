'use client';

import { useRef, useState } from 'react';
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
  onResetFilters?: () => void;
  hasActiveFilters?: boolean;
}

// Mapa: chave da coluna -> campo no ClienteRegistro
// mobileHidden: true = oculto em mobile, visivel apenas a partir de md
const COLS: { key: string; label: string; sortable: boolean; align?: 'right'; mobileHidden?: boolean }[] = [
  { key: 'cnpj',            label: 'CNPJ',         sortable: false,  mobileHidden: true },
  { key: 'nome_fantasia',   label: 'Cliente',       sortable: true },
  { key: 'uf',              label: 'UF',            sortable: true,   mobileHidden: true },
  { key: 'consultor',       label: 'Consultor',     sortable: true },
  { key: 'situacao',        label: 'Situacao',      sortable: true },
  { key: 'temperatura',     label: 'Temp.',         sortable: true,   mobileHidden: true },
  { key: 'score',           label: 'Score',         sortable: true,   align: 'right' },
  { key: 'curva_abc',       label: 'ABC',           sortable: true,   mobileHidden: true },
  { key: 'sinaleiro',       label: 'Sinal.',        sortable: true,   mobileHidden: true },
  { key: 'faturamento_total', label: 'Faturamento', sortable: true,   align: 'right', mobileHidden: true },
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

// ---------------------------------------------------------------------------
// Long-press context menu — mobile only
// Shows actions: Ligar, WhatsApp, Ver detalhe
// Triggers after 500ms press without significant movement
// ---------------------------------------------------------------------------

const LONGPRESS_DURATION = 500;
const LONGPRESS_MOVE_THRESHOLD = 8; // px

interface ContextMenuProps {
  cliente: ClienteRegistro;
  anchorY: number;
  onClose: () => void;
  onVerDetalhe: () => void;
}

function LongPressContextMenu({ cliente, anchorY, onClose, onVerDetalhe }: ContextMenuProps) {
  const tel = cliente.cnpj; // Use CNPJ as identifier for calls when no phone available

  return (
    <>
      {/* Overlay */}
      <div
        className="fixed inset-0 z-40"
        onClick={onClose}
        aria-hidden="true"
      />
      {/* Menu */}
      <div
        className="fixed left-4 right-4 z-50 bg-white border border-gray-200 rounded-xl shadow-xl overflow-hidden"
        style={{ top: Math.min(anchorY, window.innerHeight - 200) }}
        role="menu"
        aria-label={`Acoes para ${cliente.nome_fantasia}`}
      >
        {/* Header */}
        <div className="px-4 py-3 border-b border-gray-100 bg-gray-50">
          <p className="text-sm font-bold text-gray-900 truncate">{cliente.nome_fantasia ?? 'Cliente'}</p>
          <p className="text-[11px] text-gray-400 font-mono mt-0.5">{formatCnpj(cliente.cnpj)}</p>
        </div>

        {/* Actions */}
        <div className="py-1">
          {/* Ligar */}
          <a
            href={`tel:${tel}`}
            role="menuitem"
            className="flex items-center gap-3 px-4 py-3 hover:bg-gray-50 transition-colors"
            onClick={onClose}
          >
            <div className="w-8 h-8 rounded-full bg-blue-50 flex items-center justify-center flex-shrink-0">
              <svg className="w-4 h-4 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                  d="M3 5a2 2 0 012-2h3.28a1 1 0 01.948.684l1.498 4.493a1 1 0 01-.502 1.21l-2.257 1.13a11.042 11.042 0 005.516 5.516l1.13-2.257a1 1 0 011.21-.502l4.493 1.498a1 1 0 01.684.949V19a2 2 0 01-2 2h-1C9.716 21 3 14.284 3 6V5z" />
              </svg>
            </div>
            <span className="text-sm font-medium text-gray-800">Ligar</span>
          </a>

          {/* WhatsApp */}
          <a
            href={`https://wa.me/55${tel.replace(/\D/g, '')}`}
            target="_blank"
            rel="noopener noreferrer"
            role="menuitem"
            className="flex items-center gap-3 px-4 py-3 hover:bg-gray-50 transition-colors"
            onClick={onClose}
          >
            <div className="w-8 h-8 rounded-full bg-green-50 flex items-center justify-center flex-shrink-0">
              <svg className="w-4 h-4 text-green-600" fill="currentColor" viewBox="0 0 24 24">
                <path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347z" />
                <path d="M12 0C5.373 0 0 5.373 0 12c0 2.139.558 4.144 1.535 5.879L.057 23.55a.5.5 0 00.608.608l5.693-1.479A11.952 11.952 0 0012 24c6.627 0 12-5.373 12-12S18.627 0 12 0zm0 22c-1.96 0-3.799-.56-5.354-1.527l-.383-.231-3.979 1.034 1.054-3.867-.252-.4A9.956 9.956 0 012 12C2 6.477 6.477 2 12 2s10 4.477 10 10-4.477 10-10 10z" />
              </svg>
            </div>
            <span className="text-sm font-medium text-gray-800">WhatsApp</span>
          </a>

          {/* Ver detalhe */}
          <button
            type="button"
            role="menuitem"
            className="w-full flex items-center gap-3 px-4 py-3 hover:bg-gray-50 transition-colors"
            onClick={() => { onClose(); onVerDetalhe(); }}
          >
            <div className="w-8 h-8 rounded-full bg-gray-100 flex items-center justify-center flex-shrink-0">
              <svg className="w-4 h-4 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                  d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                  d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
              </svg>
            </div>
            <span className="text-sm font-medium text-gray-800">Ver detalhe</span>
          </button>
        </div>
      </div>
    </>
  );
}

// ---------------------------------------------------------------------------
// ClienteRow — individual row with long-press detection on touch devices
// ---------------------------------------------------------------------------

interface ClienteRowProps {
  cliente: ClienteRegistro;
  idx: number;
  onRowClick?: (c: ClienteRegistro) => void;
  showFaturamento: boolean;
}

function ClienteRow({ cliente: c, idx, onRowClick, showFaturamento }: ClienteRowProps) {
  const [contextMenu, setContextMenu] = useState<{ y: number } | null>(null);
  const longPressTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const touchStartPos = useRef<{ x: number; y: number } | null>(null);
  const longPressTriggered = useRef(false);

  function handleTouchStart(e: React.TouchEvent<HTMLTableRowElement>) {
    const touch = e.touches[0];
    touchStartPos.current = { x: touch.clientX, y: touch.clientY };
    longPressTriggered.current = false;

    longPressTimer.current = setTimeout(() => {
      longPressTriggered.current = true;
      setContextMenu({ y: touch.clientY });
    }, LONGPRESS_DURATION);
  }

  function handleTouchMove(e: React.TouchEvent<HTMLTableRowElement>) {
    if (!touchStartPos.current || !longPressTimer.current) return;
    const touch = e.touches[0];
    const dx = Math.abs(touch.clientX - touchStartPos.current.x);
    const dy = Math.abs(touch.clientY - touchStartPos.current.y);
    if (dx > LONGPRESS_MOVE_THRESHOLD || dy > LONGPRESS_MOVE_THRESHOLD) {
      clearTimeout(longPressTimer.current);
      longPressTimer.current = null;
    }
  }

  function handleTouchEnd() {
    if (longPressTimer.current) {
      clearTimeout(longPressTimer.current);
      longPressTimer.current = null;
    }
  }

  function handleClick() {
    if (longPressTriggered.current) {
      longPressTriggered.current = false;
      return; // Long press already handled by context menu
    }
    onRowClick?.(c);
  }

  return (
    <>
      <tr
        className={`border-t border-gray-100 transition-colors ${
          idx % 2 === 1 ? 'bg-gray-50/50' : 'bg-white'
        } ${
          onRowClick
            ? 'cursor-pointer hover:bg-green-50/60 active:bg-green-50'
            : 'hover:bg-gray-50'
        } ${rowBorderStyle(c.sinaleiro)}`}
        onClick={handleClick}
        onTouchStart={handleTouchStart}
        onTouchMove={handleTouchMove}
        onTouchEnd={handleTouchEnd}
      >
        {/* CNPJ — hidden on mobile */}
        <td className="hidden md:table-cell px-3 py-2.5 font-mono text-xs text-gray-500 whitespace-nowrap">
          {formatCnpj(c.cnpj)}
        </td>
        {/* Cliente */}
        <td className="px-3 py-2.5 max-w-[160px] md:max-w-[200px]">
          <p className="font-medium text-gray-900 truncate">{c.nome_fantasia ?? '—'}</p>
          {c.razao_social && c.razao_social !== c.nome_fantasia && (
            <p className="text-[11px] text-gray-400 truncate hidden md:block">{c.razao_social}</p>
          )}
        </td>
        {/* UF — hidden on mobile */}
        <td className="hidden md:table-cell px-3 py-2.5 text-gray-600 whitespace-nowrap text-xs">
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
        {/* Temperatura — hidden on mobile */}
        <td className="hidden md:table-cell px-3 py-2.5 whitespace-nowrap">
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
        {/* ABC — hidden on mobile */}
        <td className="hidden md:table-cell px-3 py-2.5 whitespace-nowrap">
          {c.curva_abc ? (
            <StatusBadge value={c.curva_abc} variant="abc" small />
          ) : (
            <span className="text-gray-300">—</span>
          )}
        </td>
        {/* Sinaleiro — hidden on mobile */}
        <td className="hidden md:table-cell px-3 py-2.5 whitespace-nowrap">
          <SinaleiroDot value={c.sinaleiro} />
        </td>
        {/* Faturamento — hidden on mobile */}
        {showFaturamento && (
          <td className="hidden md:table-cell px-3 py-2.5 text-right whitespace-nowrap font-mono text-xs text-gray-800">
            {c.faturamento_total != null ? formatBRL(c.faturamento_total) : '—'}
          </td>
        )}
      </tr>

      {/* Context menu portal (rendered as sibling in tbody — positioned fixed) */}
      {contextMenu && (
        <tr className="sr-only" aria-hidden="true">
          <td>
            <LongPressContextMenu
              cliente={c}
              anchorY={contextMenu.y}
              onClose={() => setContextMenu(null)}
              onVerDetalhe={() => onRowClick?.(c)}
            />
          </td>
        </tr>
      )}
    </>
  );
}

export default function ClienteTable({
  registros,
  loading = false,
  onRowClick,
  sort,
  onSort,
  showFaturamento = true,
  onResetFilters,
  hasActiveFilters = false,
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
                  <td key={c.key} className={`px-3 py-2.5 ${c.mobileHidden ? 'hidden md:table-cell' : ''}`}>
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

  if (!registros || registros.length === 0) {
    return (
      <div className="py-16 text-center text-gray-400">
        <svg className="w-10 h-10 mx-auto mb-3 text-gray-200" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
            d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0z" />
        </svg>
        <p className="text-sm font-medium text-gray-500">Nenhum cliente encontrado</p>
        {hasActiveFilters ? (
          <>
            <p className="text-xs text-gray-400 mt-1">Nenhum cliente corresponde aos filtros selecionados.</p>
            {onResetFilters && (
              <button
                type="button"
                onClick={onResetFilters}
                className="mt-3 px-4 py-1.5 text-xs font-semibold text-green-700 border border-green-300 rounded-lg bg-white hover:bg-green-50 hover:border-green-400 transition-colors"
              >
                Limpar filtros
              </button>
            )}
          </>
        ) : (
          <p className="text-xs text-gray-400 mt-1">Tente ajustar os filtros ou limpar a busca.</p>
        )}
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
          {(registros ?? []).map((c, idx) => (
            <ClienteRow
              key={c.cnpj}
              cliente={c}
              idx={idx}
              onRowClick={onRowClick}
              showFaturamento={showFaturamento}
            />
          ))}
        </tbody>
      </table>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Sub-componentes internos
// ---------------------------------------------------------------------------

interface ColDef { key: string; label: string; sortable: boolean; align?: 'right'; mobileHidden?: boolean }

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
          } ${col.sortable && onSort ? 'cursor-pointer hover:text-gray-700' : ''} ${
            col.mobileHidden ? 'hidden md:table-cell' : ''
          }`}
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
