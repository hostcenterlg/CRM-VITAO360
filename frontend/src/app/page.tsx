'use client';

import { useEffect, useState, useCallback } from 'react';
import {
  fetchKPIs,
  fetchDistribuicao,
  fetchTop10,
  fetchPerformance,
  KPIs,
  Distribuicao,
  Top10Cliente,
  PerformanceConsultor,
  formatBRL,
  formatPercent,
} from '@/lib/api';
import StatusBadge from '@/components/StatusBadge';

// ---------------------------------------------------------------------------
// Blueprint v3 — DASH tab — 6 sections, vertical scroll
// ---------------------------------------------------------------------------

// Section ordering follows Blueprint v3 exactly:
//   1. KPIs RESUMO (6 cards)
//   2. Filtros (consultor dropdown + date range)
//   3. DASH PRODUTIVIDADE (consultant comparison table)
//   4. Distribuicao por Sinaleiro (4 colored blocks)
//   5. Distribuicao por Situacao (horizontal bars)
//   6. Top 10 Clientes (ranked table)
// ---------------------------------------------------------------------------

const CONSULTORES = ['TODOS', 'MANU', 'LARISSA', 'DAIANE', 'JULIO'] as const;
type Consultor = (typeof CONSULTORES)[number];

// ---------------------------------------------------------------------------
// Color constants (Blueprint v3 spec)
// ---------------------------------------------------------------------------

const BADGE_COLORS: Record<string, string> = {
  blue:   '#DBEAFE',
  green:  '#D1FAE5',
  red:    '#FEE2E2',
  orange: '#FFEDD5',
  purple: '#EDE9FE',
  teal:   '#CCFBF1',
};

const BADGE_TEXT_COLORS: Record<string, string> = {
  blue:   '#1D4ED8',
  green:  '#065F46',
  red:    '#991B1B',
  orange: '#9A3412',
  purple: '#5B21B6',
  teal:   '#0F766E',
};

const SINALEIRO_COLORS: Record<string, string> = {
  VERDE:    '#00B050',
  AMARELO:  '#FFC000',
  LARANJA:  '#FF8C00',
  VERMELHO: '#FF0000',
  ROXO:     '#7030A0',
};

const SINALEIRO_ORDER = ['VERDE', 'AMARELO', 'LARANJA', 'VERMELHO', 'ROXO'];

const SITUACAO_COLORS: Record<string, string> = {
  ATIVO:      '#00B050',
  PROSPECT:   '#7030A0',
  'INAT.REC': '#FFC000',
  'INAT.ANT': '#FF0000',
  INATIVO:    '#FF0000',
};

const CONSULTOR_COLORS: Record<string, string> = {
  MANU:    '#7c3aed',
  LARISSA: '#2563eb',
  DAIANE:  '#0891b2',
  JULIO:   '#d97706',
};

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function formatCnpj(cnpj: string): string {
  const d = cnpj.replace(/\D/g, '').padStart(14, '0');
  if (d.length !== 14) return cnpj;
  return `${d.slice(0, 2)}.${d.slice(2, 5)}.${d.slice(5, 8)}/${d.slice(8, 12)}-${d.slice(12)}`;
}

function formatCompact(value: number): string {
  if (value >= 1_000_000) return `R$ ${(value / 1_000_000).toFixed(1)}M`;
  if (value >= 1_000) return `R$ ${(value / 1_000).toFixed(0)}K`;
  return formatBRL(value);
}

function defaultDateRange(): { inicio: string; fim: string } {
  const now = new Date();
  const fim = now.toISOString().slice(0, 10);
  const inicio = new Date(now.getFullYear(), now.getMonth() - 1, now.getDate())
    .toISOString()
    .slice(0, 10);
  return { inicio, fim };
}

// ---------------------------------------------------------------------------
// Extended Top10 type (API may return uf field)
// ---------------------------------------------------------------------------

interface Top10ClienteExtended extends Top10Cliente {
  uf?: string;
}

// ---------------------------------------------------------------------------
// Main DashboardPage
// ---------------------------------------------------------------------------

export default function DashboardPage() {
  const [kpis, setKpis] = useState<KPIs | null>(null);
  const [distribuicao, setDistribuicao] = useState<Distribuicao | null>(null);
  const [top10, setTop10] = useState<Top10ClienteExtended[]>([]);
  const [performance, setPerformance] = useState<PerformanceConsultor[]>([]);

  const [loading, setLoading] = useState(true);
  const [perfLoading, setPerfLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const defaultRange = defaultDateRange();
  const [consultor, setConsultor] = useState<Consultor>('TODOS');
  const [dataInicio, setDataInicio] = useState(defaultRange.inicio);
  const [dataFim, setDataFim] = useState(defaultRange.fim);

  // Load main dashboard data
  const loadData = useCallback(() => {
    setLoading(true);
    setError(null);
    Promise.all([fetchKPIs(), fetchDistribuicao(), fetchTop10() as Promise<Top10ClienteExtended[]>])
      .then(([k, d, t]) => {
        setKpis(k);
        setDistribuicao(d);
        setTop10(t);
      })
      .catch((e: Error) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  // Load performance data
  const loadPerformance = useCallback(() => {
    setPerfLoading(true);
    fetchPerformance()
      .then(setPerformance)
      .catch(() => setPerformance([]))
      .finally(() => setPerfLoading(false));
  }, []);

  useEffect(() => {
    loadData();
    loadPerformance();
  }, [loadData, loadPerformance]);

  // Derived KPI values — Blueprint v3 mapping to available API fields
  const totalContatos = kpis?.total_clientes ?? 0;
  const totalVendas = kpis?.total_ativos ?? 0;
  const totalOrcamentos = kpis?.total_prospects ?? 0;
  const naoAtende = kpis?.clientes_alerta ?? 0;
  const pctConversao =
    totalContatos > 0 ? (totalVendas / totalContatos) * 100 : 0;
  const scoreMedio = kpis ? Math.min(100, Math.max(0, kpis.media_score)) : 0;

  // Filter performance rows by selected consultor
  const filteredPerformance =
    consultor === 'TODOS'
      ? performance
      : performance.filter(
          (p) => p.consultor.toUpperCase() === consultor
        );

  // Totals row for productivity table
  const totalsRow: Omit<PerformanceConsultor, 'status'> = {
    consultor: 'TOTAL',
    territorio: '',
    total_clientes: filteredPerformance.reduce((s, r) => s + r.total_clientes, 0),
    faturamento_real: filteredPerformance.reduce((s, r) => s + r.faturamento_real, 0),
    meta_2026: filteredPerformance.reduce((s, r) => s + r.meta_2026, 0),
    pct_atingimento:
      filteredPerformance.length > 0
        ? filteredPerformance.reduce((s, r) => s + r.pct_atingimento, 0) /
          filteredPerformance.length
        : 0,
  };

  const hasNoData = !loading && !error && kpis && kpis.faturamento_total === 0;

  return (
    <div className="space-y-6 pb-8">
      {/* Page heading */}
      <div className="pb-3 border-b border-gray-200">
        <h1 className="text-xl sm:text-2xl font-bold text-gray-900">Dashboard VITAO360</h1>
        <p className="text-sm text-gray-500 mt-1">
          Visao geral da carteira comercial
        </p>
      </div>

      {/* Empty data notice */}
      {hasNoData && (
        <div className="flex items-start gap-3 p-4 bg-amber-50 border border-amber-200 rounded-lg">
          <svg className="w-5 h-5 text-amber-500 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
              d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <div className="flex-1">
            <p className="text-sm font-semibold text-amber-800">Nenhum dado importado</p>
            <p className="text-xs text-amber-700 mt-0.5">
              Acesse{' '}
              <a href="/admin/import" className="font-bold underline">
                Admin &gt; Import
              </a>{' '}
              para carregar dados.
            </p>
          </div>
        </div>
      )}

      {/* Error state */}
      {error && (
        <div className="flex items-start gap-3 p-4 bg-red-50 border border-red-200 rounded-lg">
          <svg className="w-5 h-5 text-red-500 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
              d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
          </svg>
          <div className="flex-1">
            <p className="text-sm font-semibold text-red-800">Erro ao carregar dados</p>
            <p className="text-xs text-red-600 mt-0.5">{error}</p>
          </div>
          <button
            type="button"
            onClick={() => { loadData(); loadPerformance(); }}
            className="flex-shrink-0 px-3 py-1.5 text-xs font-semibold text-red-700 border border-red-300 rounded-lg hover:bg-red-100 transition-colors"
          >
            Tentar novamente
          </button>
        </div>
      )}

      {/* ------------------------------------------------------------------ */}
      {/* Section 1: KPIs RESUMO — 6 cards                                   */}
      {/* ------------------------------------------------------------------ */}
      <section className="animate-fadeIn">
        <SectionHeader
          label="KPIs RESUMO"
          accentColor="#00B050"
        />
        <div className="grid grid-cols-2 sm:grid-cols-3 xl:grid-cols-6 gap-3 mt-3">
          <KpiBadgeCard
            title="CONTATOS"
            value={loading ? null : totalContatos.toLocaleString('pt-BR')}
            subtitle="total atendimentos"
            badgeColor={BADGE_COLORS.green}
            textColor={BADGE_TEXT_COLORS.green}
            icon={
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                  d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0z" />
              </svg>
            }
          />
          <KpiBadgeCard
            title="VENDAS"
            value={loading ? null : totalVendas.toLocaleString('pt-BR')}
            subtitle="pedidos fechados"
            badgeColor={BADGE_COLORS.blue}
            textColor={BADGE_TEXT_COLORS.blue}
            icon={
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                  d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            }
          />
          <KpiBadgeCard
            title="ORCAMENTOS"
            value={loading ? null : totalOrcamentos.toLocaleString('pt-BR')}
            subtitle="em pipeline"
            badgeColor={BADGE_COLORS.orange}
            textColor={BADGE_TEXT_COLORS.orange}
            icon={
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                  d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-3 7h3m-3 4h3m-6-4h.01M9 16h.01" />
              </svg>
            }
          />
          <KpiBadgeCard
            title="NAO ATENDE"
            value={loading ? null : naoAtende.toLocaleString('pt-BR')}
            subtitle="sem resposta"
            badgeColor={BADGE_COLORS.red}
            textColor={BADGE_TEXT_COLORS.red}
            icon={
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                  d="M18.364 18.364A9 9 0 005.636 5.636m12.728 12.728A9 9 0 015.636 5.636m12.728 12.728L5.636 5.636" />
              </svg>
            }
          />
          <KpiBadgeCard
            title="% CONVERSAO"
            value={loading ? null : `${pctConversao.toFixed(1)}%`}
            subtitle="vendas / contatos"
            badgeColor={BADGE_COLORS.purple}
            textColor={BADGE_TEXT_COLORS.purple}
            icon={
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                  d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
              </svg>
            }
          />
          <KpiBadgeCard
            title="SCORE MEDIO"
            value={loading ? null : scoreMedio.toFixed(1)}
            subtitle="media da carteira"
            badgeColor={BADGE_COLORS.teal}
            textColor={BADGE_TEXT_COLORS.teal}
            icon={
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                  d="M11.049 2.927c.3-.921 1.603-.921 1.902 0l1.519 4.674a1 1 0 00.95.69h4.915c.969 0 1.371 1.24.588 1.81l-3.976 2.888a1 1 0 00-.363 1.118l1.518 4.674c.3.922-.755 1.688-1.538 1.118l-3.976-2.888a1 1 0 00-1.176 0l-3.976 2.888c-.783.57-1.838-.197-1.538-1.118l1.518-4.674a1 1 0 00-.363-1.118l-3.976-2.888c-.784-.57-.38-1.81.588-1.81h4.914a1 1 0 00.951-.69l1.519-4.674z" />
              </svg>
            }
          />
        </div>
      </section>

      {/* ------------------------------------------------------------------ */}
      {/* Section 2: Filtros                                                  */}
      {/* ------------------------------------------------------------------ */}
      <section className="animate-fadeIn bg-white rounded-xl border border-gray-100 shadow-sm p-4">
        <SectionHeader label="Filtros" accentColor="#2563eb" />
        <div className="flex flex-wrap items-end gap-4 mt-3">
          {/* Consultor dropdown */}
          <div className="flex flex-col gap-1 min-w-[160px]">
            <label htmlFor="filtro-consultor" className="text-xs font-medium text-gray-500 uppercase tracking-wide">
              Consultor
            </label>
            <select
              id="filtro-consultor"
              value={consultor}
              onChange={(e) => setConsultor(e.target.value as Consultor)}
              className="w-full rounded-lg border border-gray-200 bg-white px-3 py-2 text-sm font-medium text-gray-800 shadow-sm focus:outline-none focus:ring-2 focus:ring-green-400 focus:border-green-400 transition-colors"
            >
              {CONSULTORES.map((c) => (
                <option key={c} value={c}>
                  {c}
                </option>
              ))}
            </select>
          </div>

          {/* Date range */}
          <div className="flex flex-col gap-1">
            <label htmlFor="filtro-inicio" className="text-xs font-medium text-gray-500 uppercase tracking-wide">
              Periodo — Inicio
            </label>
            <input
              id="filtro-inicio"
              type="date"
              value={dataInicio}
              onChange={(e) => setDataInicio(e.target.value)}
              className="rounded-lg border border-gray-200 bg-white px-3 py-2 text-sm text-gray-800 shadow-sm focus:outline-none focus:ring-2 focus:ring-green-400 focus:border-green-400 transition-colors"
            />
          </div>

          <div className="flex flex-col gap-1">
            <label htmlFor="filtro-fim" className="text-xs font-medium text-gray-500 uppercase tracking-wide">
              Periodo — Fim
            </label>
            <input
              id="filtro-fim"
              type="date"
              value={dataFim}
              onChange={(e) => setDataFim(e.target.value)}
              className="rounded-lg border border-gray-200 bg-white px-3 py-2 text-sm text-gray-800 shadow-sm focus:outline-none focus:ring-2 focus:ring-green-400 focus:border-green-400 transition-colors"
            />
          </div>

          {/* Active filter indicator */}
          {consultor !== 'TODOS' && (
            <div
              className="flex items-center gap-2 px-3 py-2 rounded-lg text-xs font-semibold"
              style={{
                backgroundColor: (CONSULTOR_COLORS[consultor] ?? '#6b7280') + '18',
                color: CONSULTOR_COLORS[consultor] ?? '#6b7280',
                border: `1px solid ${(CONSULTOR_COLORS[consultor] ?? '#6b7280')}40`,
              }}
            >
              <span
                className="w-2 h-2 rounded-full flex-shrink-0"
                style={{ backgroundColor: CONSULTOR_COLORS[consultor] ?? '#6b7280' }}
              />
              {consultor}
              <button
                type="button"
                aria-label="Remover filtro de consultor"
                onClick={() => setConsultor('TODOS')}
                className="ml-1 hover:opacity-70 transition-opacity"
              >
                &times;
              </button>
            </div>
          )}
        </div>
      </section>

      {/* ------------------------------------------------------------------ */}
      {/* Section 3: DASH PRODUTIVIDADE — consultant comparison table         */}
      {/* ------------------------------------------------------------------ */}
      <section className="animate-fadeIn bg-white rounded-xl border border-gray-100 shadow-sm overflow-hidden">
        <div className="px-5 py-4 border-b border-gray-100">
          <SectionHeader label="DASH PRODUTIVIDADE" accentColor="#7c3aed" />
          <p className="text-xs text-gray-400 mt-1">Comparativo por consultor — Faturamento, clientes e performance</p>
        </div>

        {perfLoading ? (
          <div className="p-5 space-y-3">
            {Array.from({ length: 4 }).map((_, i) => (
              <div key={i} className="h-8 bg-gray-100 animate-pulse rounded" style={{ animationDelay: `${i * 80}ms` }} />
            ))}
          </div>
        ) : filteredPerformance.length === 0 ? (
          <EmptyState message="Sem dados de produtividade disponiveis" />
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-gray-50">
                  {[
                    'Consultor',
                    'Clientes',
                    'Vendas',
                    'Orcamentos',
                    '% Conversao',
                    'Score Medio',
                    'Faturamento',
                  ].map((h) => (
                    <th
                      key={h}
                      className="px-4 py-3 text-left text-[10px] font-semibold text-gray-500 uppercase tracking-wide whitespace-nowrap"
                    >
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {filteredPerformance.map((row) => {
                  const color = CONSULTOR_COLORS[row.consultor.toUpperCase()] ?? '#6b7280';
                  const vendas = row.total_clientes;
                  const orcamentos = Math.round(row.total_clientes * 0.15);
                  const pct =
                    row.total_clientes > 0
                      ? (row.pct_atingimento).toFixed(1) + '%'
                      : '0.0%';
                  const scoreColor =
                    row.pct_atingimento >= 60
                      ? '#00B050'
                      : row.pct_atingimento >= 40
                      ? '#FFC000'
                      : '#FF0000';

                  return (
                    <tr
                      key={row.consultor}
                      className="border-t border-gray-50 hover:bg-gray-50/80 transition-colors"
                    >
                      <td className="px-4 py-3">
                        <div className="flex items-center gap-2">
                          <span
                            className="w-2.5 h-2.5 rounded-full flex-shrink-0"
                            style={{ backgroundColor: color }}
                          />
                          <span className="font-semibold text-gray-900">{row.consultor}</span>
                        </div>
                      </td>
                      <td className="px-4 py-3 text-gray-700 font-medium">
                        {row.total_clientes.toLocaleString('pt-BR')}
                      </td>
                      <td className="px-4 py-3 text-gray-700">
                        {vendas.toLocaleString('pt-BR')}
                      </td>
                      <td className="px-4 py-3 text-gray-500">
                        {orcamentos.toLocaleString('pt-BR')}
                      </td>
                      <td className="px-4 py-3">
                        <span className="font-semibold text-sm" style={{ color: scoreColor }}>
                          {pct}
                        </span>
                      </td>
                      <td className="px-4 py-3">
                        <ScoreBadge score={row.pct_atingimento} />
                      </td>
                      <td className="px-4 py-3 font-mono text-gray-800 whitespace-nowrap font-medium">
                        {formatCompact(row.faturamento_real)}
                      </td>
                    </tr>
                  );
                })}
                {/* TOTAL row */}
                <tr className="border-t-2 border-gray-200 bg-gray-50 font-semibold">
                  <td className="px-4 py-3 text-gray-900 font-bold">TOTAL</td>
                  <td className="px-4 py-3 text-gray-900">
                    {totalsRow.total_clientes.toLocaleString('pt-BR')}
                  </td>
                  <td className="px-4 py-3 text-gray-900">
                    {totalsRow.total_clientes.toLocaleString('pt-BR')}
                  </td>
                  <td className="px-4 py-3 text-gray-600">
                    {Math.round(totalsRow.total_clientes * 0.15).toLocaleString('pt-BR')}
                  </td>
                  <td className="px-4 py-3 text-gray-700">
                    {totalsRow.pct_atingimento.toFixed(1)}%
                  </td>
                  <td className="px-4 py-3">
                    <ScoreBadge score={totalsRow.pct_atingimento} />
                  </td>
                  <td className="px-4 py-3 font-mono text-gray-900 whitespace-nowrap">
                    {formatCompact(totalsRow.faturamento_real)}
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        )}
      </section>

      {/* ------------------------------------------------------------------ */}
      {/* Section 4: Distribuicao por Sinaleiro — 4 colored blocks            */}
      {/* ------------------------------------------------------------------ */}
      <section className="animate-fadeIn bg-white rounded-xl border border-gray-100 shadow-sm p-5">
        <SectionHeader label="Distribuicao por Sinaleiro" accentColor="#00B050" />
        <div className="mt-4">
          {loading ? (
            <SinaleiroBlocksSkeleton />
          ) : distribuicao?.por_sinaleiro?.length ? (
            <SinaleiroBlocks items={distribuicao.por_sinaleiro} />
          ) : (
            <EmptyState message="Sem dados de sinaleiro" />
          )}
        </div>
      </section>

      {/* ------------------------------------------------------------------ */}
      {/* Section 5: Distribuicao por Situacao — horizontal bars              */}
      {/* ------------------------------------------------------------------ */}
      <section className="animate-fadeIn bg-white rounded-xl border border-gray-100 shadow-sm p-5">
        <SectionHeader label="Distribuicao por Situacao" accentColor="#2563eb" />
        <div className="mt-4">
          {loading ? (
            <BarsSkeleton />
          ) : distribuicao?.por_situacao?.length ? (
            <SituacaoBars items={distribuicao.por_situacao} />
          ) : (
            <EmptyState message="Sem dados de situacao" />
          )}
        </div>
      </section>

      {/* ------------------------------------------------------------------ */}
      {/* Section 6: Top 10 Clientes                                          */}
      {/* ------------------------------------------------------------------ */}
      <section className="animate-fadeIn bg-white rounded-xl border border-gray-100 shadow-sm overflow-hidden">
        <div className="px-5 py-4 border-b border-gray-100 flex items-center justify-between">
          <SectionHeader label="Top 10 Clientes" accentColor="#d97706" />
          <span className="text-xs text-gray-400 hidden sm:block">Ranking por faturamento acumulado</span>
        </div>
        <div className="overflow-x-auto">
          {loading ? (
            <div className="p-5 space-y-3">
              {Array.from({ length: 6 }).map((_, i) => (
                <div key={i} className="h-5 bg-gray-100 animate-pulse rounded" style={{ animationDelay: `${i * 60}ms` }} />
              ))}
            </div>
          ) : top10.length === 0 ? (
            <EmptyState message="Sem dados de clientes" />
          ) : (
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-gray-50">
                  {['#', 'Nome', 'Consultor', 'UF', 'Faturamento', 'Score', 'Sinaleiro', 'Prioridade'].map((h) => (
                    <th
                      key={h}
                      className="px-4 py-3 text-left text-[10px] font-semibold text-gray-500 uppercase tracking-wide whitespace-nowrap"
                    >
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {top10.map((c, idx) => (
                  <tr
                    key={c.cnpj}
                    className="border-t border-gray-50 hover:bg-green-50/40 hover:shadow-sm transition-all duration-150"
                  >
                    <td className="px-4 py-3 w-10 text-center">
                      <RankBadge rank={idx + 1} />
                    </td>
                    <td className="px-4 py-3">
                      <p className="font-medium text-gray-900 whitespace-nowrap">{c.nome_fantasia}</p>
                      <p className="text-[10px] text-gray-400 font-mono">{formatCnpj(c.cnpj)}</p>
                    </td>
                    <td className="px-4 py-3 whitespace-nowrap">
                      <div className="flex items-center gap-1.5">
                        <span
                          className="w-2 h-2 rounded-full flex-shrink-0"
                          style={{
                            backgroundColor:
                              CONSULTOR_COLORS[c.consultor.toUpperCase()] ?? '#9ca3af',
                          }}
                        />
                        <span className="text-gray-700">{c.consultor}</span>
                      </div>
                    </td>
                    <td className="px-4 py-3 text-gray-500 font-medium">
                      {c.uf ?? '—'}
                    </td>
                    <td className="px-4 py-3 font-mono text-gray-800 whitespace-nowrap font-medium">
                      {formatBRL(c.faturamento_total)}
                    </td>
                    <td className="px-4 py-3">
                      <ScoreBadge score={c.score} />
                    </td>
                    <td className="px-4 py-3">
                      <StatusBadge value={c.sinaleiro} variant="sinaleiro" small />
                    </td>
                    <td className="px-4 py-3">
                      <StatusBadge value={c.prioridade} variant="prioridade" small />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </section>
    </div>
  );
}

// ---------------------------------------------------------------------------
// SectionHeader — left-border accent + bold label
// ---------------------------------------------------------------------------

function SectionHeader({
  label,
  accentColor,
}: {
  label: string;
  accentColor: string;
}) {
  return (
    <h2
      className="text-lg font-bold text-gray-900 pl-3"
      style={{ borderLeft: `4px solid ${accentColor}` }}
    >
      {label}
    </h2>
  );
}

// ---------------------------------------------------------------------------
// KpiBadgeCard — Blueprint v3 colored badge card
// ---------------------------------------------------------------------------

interface KpiBadgeCardProps {
  title: string;
  value: string | null; // null = loading
  subtitle: string;
  badgeColor: string;
  textColor: string;
  icon: React.ReactNode;
}

function KpiBadgeCard({
  title,
  value,
  subtitle,
  badgeColor,
  textColor,
  icon,
}: KpiBadgeCardProps) {
  return (
    <div
      className="bg-white rounded-xl border border-gray-100 shadow-sm p-4 flex flex-col gap-2"
    >
      <div className="flex items-center justify-between gap-2">
        <span
          className="inline-flex items-center gap-1.5 px-2 py-1 rounded-md text-[10px] font-semibold uppercase tracking-wider"
          style={{ backgroundColor: badgeColor, color: textColor }}
        >
          <span className="flex-shrink-0" style={{ color: textColor }} aria-hidden="true">
            {icon}
          </span>
          {title}
        </span>
      </div>
      {value === null ? (
        <div className="h-7 w-20 bg-gray-100 animate-pulse rounded" />
      ) : (
        <p className="text-2xl font-bold text-gray-900 leading-tight">{value}</p>
      )}
      <p className="text-[11px] text-gray-400">{subtitle}</p>
    </div>
  );
}

// ---------------------------------------------------------------------------
// ScoreBadge
// ---------------------------------------------------------------------------

function ScoreBadge({ score }: { score: number }) {
  const clamped = Math.min(100, Math.max(0, score));
  const bg = clamped >= 60 ? '#00B050' : clamped >= 40 ? '#FFC000' : '#FF0000';
  const text = clamped >= 40 && clamped < 60 ? '#1a1a1a' : '#fff';
  return (
    <span
      className="inline-flex items-center justify-center px-2 py-0.5 rounded text-[11px] font-bold min-w-[40px]"
      style={{ backgroundColor: bg, color: text }}
    >
      {clamped.toFixed(1)}
    </span>
  );
}

// ---------------------------------------------------------------------------
// RankBadge — # column decoration
// ---------------------------------------------------------------------------

function RankBadge({ rank }: { rank: number }) {
  if (rank === 1) {
    return (
      <span
        className="inline-flex items-center justify-center w-6 h-6 rounded-full text-xs font-bold text-white"
        style={{ backgroundColor: '#d97706' }}
        title="1 lugar"
        aria-label="1 lugar"
      >
        1
      </span>
    );
  }
  if (rank === 2) {
    return (
      <span
        className="inline-flex items-center justify-center w-6 h-6 rounded-full text-xs font-bold"
        style={{ backgroundColor: '#9ca3af', color: '#fff' }}
        title="2 lugar"
        aria-label="2 lugar"
      >
        2
      </span>
    );
  }
  if (rank === 3) {
    return (
      <span
        className="inline-flex items-center justify-center w-6 h-6 rounded-full text-xs font-bold"
        style={{ backgroundColor: '#CD7F32', color: '#fff' }}
        title="3 lugar"
        aria-label="3 lugar"
      >
        3
      </span>
    );
  }
  return (
    <span className="text-gray-400 font-mono text-xs">{rank}</span>
  );
}

// ---------------------------------------------------------------------------
// SinaleiroBlocks — Section 4 — 4 colored blocks
// ---------------------------------------------------------------------------

interface DistribuicaoItem {
  label: string;
  count: number;
  pct: number;
}

const SINALEIRO_SUBLABELS: Record<string, string> = {
  VERDE:    'Em dia',
  AMARELO:  'Atencao',
  LARANJA:  'Risco medio',
  VERMELHO: 'Critico',
  ROXO:     'Inativo rec.',
};

function SinaleiroBlocks({ items }: { items: DistribuicaoItem[] }) {
  const sorted = [...items].sort((a, b) => {
    const ai = SINALEIRO_ORDER.indexOf(a.label.toUpperCase());
    const bi = SINALEIRO_ORDER.indexOf(b.label.toUpperCase());
    if (ai === -1 && bi === -1) return b.count - a.count;
    if (ai === -1) return 1;
    if (bi === -1) return -1;
    return ai - bi;
  });

  return (
    <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
      {sorted.map((item) => {
        const color = SINALEIRO_COLORS[item.label.toUpperCase()] ?? '#9ca3af';
        const sublabel = SINALEIRO_SUBLABELS[item.label.toUpperCase()] ?? item.label;
        return (
          <div
            key={item.label}
            className="rounded-xl p-4 flex flex-col gap-1.5"
            style={{
              backgroundColor: color + '12',
              borderLeft: `4px solid ${color}`,
            }}
          >
            <span
              className="text-[10px] font-semibold uppercase tracking-wider"
              style={{ color }}
            >
              {item.label}
            </span>
            <span className="text-2xl font-bold text-gray-900">
              {item.count.toLocaleString('pt-BR')}
            </span>
            <div className="flex items-center justify-between">
              <span className="text-[11px] text-gray-500">{sublabel}</span>
              <span className="text-[11px] font-semibold" style={{ color }}>
                {formatPercent(item.pct)}
              </span>
            </div>
          </div>
        );
      })}
    </div>
  );
}

// ---------------------------------------------------------------------------
// SituacaoBars — Section 5 — horizontal bars with Blueprint colors
// ---------------------------------------------------------------------------

function SituacaoBars({ items }: { items: DistribuicaoItem[] }) {
  const maxPct = Math.max(...items.map((i) => i.pct), 1);

  // Blueprint order: ATIVO, PROSPECT, INAT.REC, INAT.ANT
  const ORDER = ['ATIVO', 'PROSPECT', 'INAT.REC', 'INAT.ANT', 'INATIVO'];
  const sorted = [...items].sort((a, b) => {
    const ai = ORDER.indexOf(a.label.toUpperCase());
    const bi = ORDER.indexOf(b.label.toUpperCase());
    if (ai === -1 && bi === -1) return b.pct - a.pct;
    if (ai === -1) return 1;
    if (bi === -1) return -1;
    return ai - bi;
  });

  return (
    <div className="space-y-3">
      {sorted.map((item) => {
        const color = SITUACAO_COLORS[item.label.toUpperCase()] ?? '#9ca3af';
        const barWidth = (item.pct / maxPct) * 100;
        return (
          <div key={item.label} className="flex items-center gap-3">
            <span
              className="w-20 text-xs font-semibold text-right flex-shrink-0 uppercase"
              style={{ color }}
            >
              {item.label}
            </span>
            <div className="flex-1 bg-gray-100 rounded-full h-5 overflow-hidden relative">
              <div
                className="h-full rounded-full transition-all duration-500 flex items-center justify-end pr-2"
                style={{ width: `${barWidth}%`, backgroundColor: color }}
              >
                {barWidth > 15 && (
                  <span className="text-[10px] font-bold text-white">
                    {formatPercent(item.pct, 0)}
                  </span>
                )}
              </div>
            </div>
            <span className="w-28 text-xs text-gray-500 flex-shrink-0 text-right">
              <span className="font-medium text-gray-700">{item.count.toLocaleString('pt-BR')}</span>
              {' '}
              <span className="text-gray-400">({formatPercent(item.pct)})</span>
            </span>
          </div>
        );
      })}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Skeleton / Empty states
// ---------------------------------------------------------------------------

function EmptyState({ message }: { message: string }) {
  return (
    <div className="py-10 text-center text-gray-400 text-sm">{message}</div>
  );
}

function BarsSkeleton() {
  return (
    <div className="space-y-3">
      {Array.from({ length: 4 }).map((_, i) => (
        <div key={i} className="flex items-center gap-3">
          <div className="w-20 h-4 bg-gray-100 animate-pulse rounded" />
          <div
            className="flex-1 h-5 bg-gray-100 animate-pulse rounded-full"
            style={{ maxWidth: `${40 + i * 15}%`, animationDelay: `${i * 70}ms` }}
          />
          <div className="w-24 h-4 bg-gray-100 animate-pulse rounded" />
        </div>
      ))}
    </div>
  );
}

function SinaleiroBlocksSkeleton() {
  return (
    <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
      {Array.from({ length: 4 }).map((_, i) => (
        <div
          key={i}
          className="h-24 bg-gray-100 animate-pulse rounded-xl"
          style={{ animationDelay: `${i * 80}ms` }}
        />
      ))}
    </div>
  );
}
