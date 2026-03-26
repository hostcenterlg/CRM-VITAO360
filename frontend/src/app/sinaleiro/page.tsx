'use client';

import { useEffect, useState, useCallback } from 'react';
import {
  fetchSinaleiro,
  SinaleiroResponse,
  SinaleiroItem,
  SinaleiroResumo,
  formatBRL,
  formatPercent,
} from '@/lib/api';

// ---------------------------------------------------------------------------
// Sinaleiro page — saude da carteira por cor de sinaleiro
// ---------------------------------------------------------------------------

const SINALEIRO_CONFIG: Record<string, { bg: string; text: string; border: string; label: string }> = {
  VERDE: {
    bg: '#00B050',
    text: '#fff',
    border: '#00B050',
    label: 'VERDE',
  },
  AMARELO: {
    bg: '#FFC000',
    text: '#1a1a1a',
    border: '#FFC000',
    label: 'AMARELO',
  },
  LARANJA: {
    bg: '#FF8C00',
    text: '#fff',
    border: '#FF8C00',
    label: 'LARANJA',
  },
  VERMELHO: {
    bg: '#FF0000',
    text: '#fff',
    border: '#FF0000',
    label: 'VERMELHO',
  },
  ROXO: {
    bg: '#7030A0',
    text: '#fff',
    border: '#7030A0',
    label: 'ROXO',
  },
};

const COR_ORDER = ['VERDE', 'AMARELO', 'LARANJA', 'VERMELHO', 'ROXO'];

function formatCnpj(cnpj: string): string {
  const d = cnpj.replace(/\D/g, '').padStart(14, '0');
  if (d.length !== 14) return cnpj;
  return `${d.slice(0, 2)}.${d.slice(2, 5)}.${d.slice(5, 8)}/${d.slice(8, 12)}-${d.slice(12)}`;
}

function pctColor(pct: number): string {
  if (pct >= 100) return '#00B050';
  if (pct >= 80) return '#00B050';
  if (pct >= 50) return '#FFC000';
  if (pct >= 1) return '#FF0000';
  return '#7030A0';
}

export default function SinaleiroPage() {
  const [data, setData] = useState<SinaleiroResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Filters
  const [filtroCor, setFiltroCor] = useState<string>('');
  const [filtroConsultor, setFiltroConsultor] = useState<string>('');
  const [filtroRede, setFiltroRede] = useState<string>('');

  const load = useCallback(
    (cor: string, consultor: string, rede: string) => {
      setLoading(true);
      fetchSinaleiro({
        cor: cor || undefined,
        consultor: consultor || undefined,
        rede: rede || undefined,
        limit: 200,
      })
        .then(setData)
        .catch((e: Error) => setError(e.message))
        .finally(() => setLoading(false));
    },
    []
  );

  useEffect(() => {
    load(filtroCor, filtroConsultor, filtroRede);
  }, [filtroCor, filtroConsultor, filtroRede, load]);

  // Derived lists for filter dropdowns
  const consultores = Array.from(
    new Set((data?.itens ?? []).map((i) => i.consultor).filter(Boolean))
  ).sort();
  const redes = Array.from(
    new Set(
      (data?.itens ?? [])
        .map((i) => i.rede)
        .filter((r) => r && r !== '—' && r !== '')
    )
  ).sort();

  const hasFilters = filtroCor || filtroConsultor || filtroRede;

  function clearFilters() {
    setFiltroCor('');
    setFiltroConsultor('');
    setFiltroRede('');
  }

  // Sort resumo by canonical order
  const resumo: SinaleiroResumo[] = [...(data?.resumo ?? [])].sort((a, b) => {
    const ai = COR_ORDER.indexOf(a.cor.toUpperCase());
    const bi = COR_ORDER.indexOf(b.cor.toUpperCase());
    return (ai === -1 ? 99 : ai) - (bi === -1 ? 99 : bi);
  });

  return (
    <div className="space-y-6">
      {/* Page heading */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-gray-900">Sinaleiro de Carteira</h1>
          <p className="text-sm text-gray-500 mt-0.5">
            {data ? `${data.total.toLocaleString('pt-BR')} clientes analisados` : 'Saude do ciclo de compra por cliente'}
          </p>
        </div>
      </div>

      {error && (
        <div className="flex items-start gap-3 p-4 bg-red-50 border border-red-200 rounded-lg">
          <svg className="w-5 h-5 text-red-500 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
              d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
          </svg>
          <div className="flex-1">
            <p className="text-sm font-semibold text-red-800">Erro ao carregar sinaleiro</p>
            <p className="text-xs text-red-600 mt-0.5">{error}</p>
          </div>
          <button
            type="button"
            onClick={() => load(filtroCor, filtroConsultor, filtroRede)}
            className="flex-shrink-0 px-3 py-1.5 text-xs font-semibold text-red-700 border border-red-300 rounded-lg hover:bg-red-100 transition-colors"
          >
            Tentar novamente
          </button>
        </div>
      )}

      {/* KPI Cards — 5 cores clicaveis */}
      <section>
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3">
          {loading
            ? Array.from({ length: 5 }).map((_, i) => (
                <div
                  key={i}
                  className="rounded-lg border border-gray-200 p-4 h-24 bg-gray-50 animate-pulse"
                />
              ))
            : resumo.length > 0
            ? resumo.map((item) => {
                const cfg = SINALEIRO_CONFIG[item.cor.toUpperCase()];
                if (!cfg) return null;
                const isSelected = filtroCor === item.cor.toUpperCase();

                return (
                  <button
                    key={item.cor}
                    onClick={() =>
                      setFiltroCor(isSelected ? '' : item.cor.toUpperCase())
                    }
                    className="rounded-lg text-left transition-all duration-150 hover:shadow-md focus:outline-none focus:ring-2 focus:ring-offset-1"
                    style={{
                      border: isSelected
                        ? `3px solid ${cfg.border}`
                        : '1px solid #E5E7EB',
                      backgroundColor: isSelected ? cfg.bg + '18' : '#fff',
                      padding: isSelected ? '14px' : '16px',
                    }}
                    aria-pressed={isSelected}
                    aria-label={`Filtrar por sinaleiro ${cfg.label}`}
                  >
                    <div className="flex items-center gap-2 mb-2">
                      <span
                        className="inline-block w-3 h-3 rounded-full flex-shrink-0 shadow-sm"
                        style={{ backgroundColor: cfg.bg }}
                      />
                      <span
                        className="text-xs font-bold uppercase tracking-wide"
                        style={{ color: isSelected ? cfg.border : '#374151' }}
                      >
                        {cfg.label}
                      </span>
                    </div>
                    <p className="text-3xl font-bold text-gray-900 leading-tight">
                      {item.count.toLocaleString('pt-BR')}
                    </p>
                    <p className="text-xs text-gray-500 mt-0.5 font-medium">
                      {formatPercent(item.pct)}
                    </p>
                    {item.faturamento > 0 && (
                      <p
                        className="text-xs mt-1 font-semibold truncate"
                        style={{ color: cfg.border }}
                      >
                        {formatBRL(item.faturamento)}
                      </p>
                    )}
                  </button>
                );
              })
            : COR_ORDER.map((cor) => {
                const cfg = SINALEIRO_CONFIG[cor];
                return (
                  <div
                    key={cor}
                    className="rounded-lg border border-gray-200 p-4 h-24 flex items-center justify-center"
                  >
                    <span className="text-xs text-gray-400">{cfg.label}</span>
                  </div>
                );
              })}
        </div>
      </section>

      {/* Filtros */}
      <section className="bg-white rounded-lg border border-gray-200 p-3 shadow-sm">
        <div className="flex flex-wrap items-center gap-3">
          {/* Cor filter */}
          <div className="flex flex-col gap-1">
            <label className="text-[10px] font-semibold text-gray-500 uppercase tracking-wide">
              Cor
            </label>
            <select
              value={filtroCor}
              onChange={(e) => setFiltroCor(e.target.value)}
              className="h-8 border border-gray-300 rounded px-2 text-xs text-gray-700 bg-white focus:outline-none focus:border-green-600"
              aria-label="Filtrar por cor"
            >
              <option value="">Todas</option>
              {COR_ORDER.map((cor) => (
                <option key={cor} value={cor}>
                  {cor}
                </option>
              ))}
            </select>
          </div>

          {/* Consultor filter */}
          <div className="flex flex-col gap-1">
            <label className="text-[10px] font-semibold text-gray-500 uppercase tracking-wide">
              Consultor
            </label>
            <select
              value={filtroConsultor}
              onChange={(e) => setFiltroConsultor(e.target.value)}
              className="h-8 border border-gray-300 rounded px-2 text-xs text-gray-700 bg-white focus:outline-none focus:border-green-600"
              aria-label="Filtrar por consultor"
            >
              <option value="">Todos</option>
              {consultores.map((c) => (
                <option key={c} value={c}>
                  {c}
                </option>
              ))}
            </select>
          </div>

          {/* Rede filter */}
          {redes.length > 0 && (
            <div className="flex flex-col gap-1">
              <label className="text-[10px] font-semibold text-gray-500 uppercase tracking-wide">
                Rede
              </label>
              <select
                value={filtroRede}
                onChange={(e) => setFiltroRede(e.target.value)}
                className="h-8 border border-gray-300 rounded px-2 text-xs text-gray-700 bg-white focus:outline-none focus:border-green-600"
                aria-label="Filtrar por rede"
              >
                <option value="">Todas</option>
                {redes.map((r) => (
                  <option key={r} value={r}>
                    {r}
                  </option>
                ))}
              </select>
            </div>
          )}

          {/* Limpar */}
          {hasFilters && (
            <button
              onClick={clearFilters}
              className="mt-4 text-xs text-gray-500 hover:text-gray-800 underline underline-offset-2 transition-colors"
            >
              Limpar filtros
            </button>
          )}

          {/* Active filters summary */}
          {hasFilters && (
            <div className="mt-4 flex gap-2 flex-wrap">
              {filtroCor && (
                <ActiveFilterChip
                  label={`Cor: ${filtroCor}`}
                  color={SINALEIRO_CONFIG[filtroCor]?.bg}
                  onRemove={() => setFiltroCor('')}
                />
              )}
              {filtroConsultor && (
                <ActiveFilterChip
                  label={`Consultor: ${filtroConsultor}`}
                  onRemove={() => setFiltroConsultor('')}
                />
              )}
              {filtroRede && (
                <ActiveFilterChip
                  label={`Rede: ${filtroRede}`}
                  onRemove={() => setFiltroRede('')}
                />
              )}
            </div>
          )}
        </div>
      </section>

      {/* Tabela principal */}
      <section className="bg-white rounded-lg border border-gray-200 shadow-sm overflow-hidden">
        <div className="px-4 py-3 border-b border-gray-100 flex items-center justify-between">
          <h2 className="text-sm font-semibold text-gray-700">
            Clientes por Sinaleiro
          </h2>
          {data && (
            <span className="text-xs text-gray-400">
              {(data.itens?.length ?? 0).toLocaleString('pt-BR')} registros
            </span>
          )}
        </div>

        <div className="overflow-x-auto scrollbar-thin">
          {loading ? (
            <TableSkeleton cols={10} rows={8} />
          ) : !data?.itens?.length ? (
            <div className="py-12 text-center text-gray-400 text-sm">
              Nenhum cliente encontrado com os filtros selecionados
            </div>
          ) : (
            <SinaleiroTable itens={data.itens} />
          )}
        </div>
      </section>

      {/* Legenda */}
      <div className="bg-blue-50 border border-blue-100 rounded-lg p-4 text-xs text-blue-700 space-y-1">
        <p>
          <strong>Sinaleiro:</strong> saude do ciclo de compra baseada em dias sem compra / ciclo medio.
        </p>
        <p>
          VERDE: saudavel (dentro do ciclo) | AMARELO: atencao | LARANJA: risco medio |
          VERMELHO: em risco critico | ROXO: sem historico de compra
        </p>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// SinaleiroTable
// ---------------------------------------------------------------------------

function SinaleiroTable({ itens }: { itens: SinaleiroItem[] }) {
  return (
    <table className="w-full text-sm" role="table">
      <thead>
        <tr className="bg-gray-50">
          {[
            'CNPJ',
            'Nome',
            'UF',
            'Consultor',
            'Rede',
            'Meta Anual',
            'Realizado',
            '% Ating',
            'Gap',
            'Cor',
            'Maturidade',
            'Acao Recomendada',
          ].map((h) => (
            <th
              key={h}
              scope="col"
              className="px-3 py-2.5 text-left text-[10px] font-semibold text-gray-500 uppercase tracking-wide whitespace-nowrap sticky top-0 bg-gray-50"
            >
              {h}
            </th>
          ))}
        </tr>
      </thead>
      <tbody>
        {itens.map((item) => {
          const cfg = SINALEIRO_CONFIG[item.cor.toUpperCase()];
          const pc = pctColor(item.pct_atingimento);
          const isNegativeGap = item.gap < 0;
          const rowBorderColor = cfg?.border ?? 'transparent';

          return (
            <tr
              key={item.cnpj}
              className="border-t border-gray-50 hover:bg-gray-50 transition-colors"
              style={{ borderLeft: `3px solid ${rowBorderColor}` }}
            >
              {/* CNPJ */}
              <td className="px-3 py-2.5 font-mono text-[11px] text-gray-500 whitespace-nowrap">
                {formatCnpj(item.cnpj)}
              </td>

              {/* Nome */}
              <td className="px-3 py-2.5 max-w-[200px]">
                <p className="font-medium text-gray-900 truncate text-xs">
                  {item.nome_fantasia}
                </p>
              </td>

              {/* UF */}
              <td className="px-3 py-2.5 text-xs text-gray-600 whitespace-nowrap">
                {item.uf || '—'}
              </td>

              {/* Consultor */}
              <td className="px-3 py-2.5 text-xs text-gray-700 whitespace-nowrap">
                {item.consultor || '—'}
              </td>

              {/* Rede */}
              <td className="px-3 py-2.5 text-xs text-gray-500 whitespace-nowrap">
                {item.rede || '—'}
              </td>

              {/* Meta */}
              <td className="px-3 py-2.5 font-mono text-xs text-gray-700 whitespace-nowrap">
                {item.meta_anual > 0 ? formatBRL(item.meta_anual) : '—'}
              </td>

              {/* Realizado */}
              <td className="px-3 py-2.5 font-mono text-xs text-gray-800 whitespace-nowrap font-medium">
                {formatBRL(item.realizado)}
              </td>

              {/* % Atingimento */}
              <td className="px-3 py-2.5 whitespace-nowrap">
                <div className="flex items-center gap-1.5">
                  <div className="w-12 bg-gray-100 rounded-full h-1.5 overflow-hidden">
                    <div
                      className="h-full rounded-full transition-all duration-500"
                      style={{
                        width: `${Math.min(100, item.pct_atingimento)}%`,
                        backgroundColor: pc,
                      }}
                    />
                  </div>
                  <span className="text-xs font-semibold" style={{ color: pc }}>
                    {formatPercent(item.pct_atingimento)}
                  </span>
                </div>
              </td>

              {/* Gap */}
              <td
                className="px-3 py-2.5 font-mono text-xs whitespace-nowrap font-medium"
                style={{ color: isNegativeGap ? '#DC2626' : '#00B050' }}
              >
                {isNegativeGap
                  ? `(${formatBRL(Math.abs(item.gap))})`
                  : `+${formatBRL(item.gap)}`}
              </td>

              {/* Cor — badge grande */}
              <td className="px-3 py-2.5 whitespace-nowrap">
                {cfg ? (
                  <span
                    className="inline-flex items-center gap-1 px-2.5 py-1 rounded text-[11px] font-bold uppercase"
                    style={{ backgroundColor: cfg.bg, color: cfg.text }}
                    aria-label={`Sinaleiro: ${cfg.label}`}
                  >
                    <span
                      className="w-2 h-2 rounded-full bg-current opacity-70"
                      aria-hidden="true"
                    />
                    {cfg.label}
                  </span>
                ) : (
                  <span className="text-gray-400 text-xs">{item.cor}</span>
                )}
              </td>

              {/* Maturidade */}
              <td className="px-3 py-2.5 text-xs text-gray-600 whitespace-nowrap">
                {item.maturidade || '—'}
              </td>

              {/* Acao */}
              <td className="px-3 py-2.5 max-w-[180px]">
                <p className="text-xs text-gray-700 truncate" title={item.acao_recomendada}>
                  {item.acao_recomendada || '—'}
                </p>
              </td>
            </tr>
          );
        })}
      </tbody>
    </table>
  );
}

// ---------------------------------------------------------------------------
// ActiveFilterChip
// ---------------------------------------------------------------------------

interface ActiveFilterChipProps {
  label: string;
  color?: string;
  onRemove: () => void;
}

function ActiveFilterChip({ label, color, onRemove }: ActiveFilterChipProps) {
  return (
    <span
      className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium border"
      style={
        color
          ? { backgroundColor: color + '18', borderColor: color + '50', color: '#374151' }
          : { backgroundColor: '#F3F4F6', borderColor: '#D1D5DB', color: '#374151' }
      }
    >
      {label}
      <button
        onClick={onRemove}
        className="ml-0.5 hover:text-red-500 transition-colors"
        aria-label={`Remover filtro ${label}`}
      >
        x
      </button>
    </span>
  );
}

// ---------------------------------------------------------------------------
// TableSkeleton
// ---------------------------------------------------------------------------

function TableSkeleton({ cols, rows }: { cols: number; rows: number }) {
  return (
    <table className="w-full text-sm">
      <thead>
        <tr className="bg-gray-50">
          {Array.from({ length: cols }).map((_, i) => (
            <th key={i} className="px-3 py-2.5">
              <div className="h-3 bg-gray-200 animate-pulse rounded" />
            </th>
          ))}
        </tr>
      </thead>
      <tbody>
        {Array.from({ length: rows }).map((_, r) => (
          <tr key={r} className="border-t border-gray-50">
            {Array.from({ length: cols }).map((_, c) => (
              <td key={c} className="px-3 py-2.5">
                <div
                  className="h-3 bg-gray-100 animate-pulse rounded"
                  style={{ width: `${50 + ((r + c) % 5) * 10}%` }}
                />
              </td>
            ))}
          </tr>
        ))}
      </tbody>
    </table>
  );
}
