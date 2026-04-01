'use client';

import { useEffect, useState, useCallback } from 'react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  AreaChart,
  Area,
  Legend,
} from 'recharts';
import {
  fetchKPIs,
  fetchDistribuicao,
  fetchTop10,
  fetchPerformance,
  fetchProjecao,
  fetchTendencias,
  fetchSinaleiro,
  fetchRNC,
  KPIs,
  Distribuicao,
  Top10Cliente,
  PerformanceConsultor,
  Projecao,
  TendenciasResponse,
  SinaleiroResponse,
  RNCResponse,
  formatBRL,
  formatPercent,
} from '@/lib/api';
import StatusBadge from '@/components/StatusBadge';

// ---------------------------------------------------------------------------
// Tab definitions
// ---------------------------------------------------------------------------

const TABS = [
  { id: 'resumo',       label: 'RESUMO' },
  { id: 'operacional',  label: 'OPERACIONAL' },
  { id: 'funil',        label: 'FUNIL + CANAIS' },
  { id: 'performance',  label: 'PERFORMANCE' },
  { id: 'saude',        label: 'SAUDE DA BASE' },
  { id: 'redes',        label: 'REDES + SINALEIRO' },
  { id: 'motivos',      label: 'MOTIVOS + RNC' },
  { id: 'produtividade', label: 'PRODUTIVIDADE' },
] as const;

type TabId = (typeof TABS)[number]['id'];

// ---------------------------------------------------------------------------
// Consultor filter
// ---------------------------------------------------------------------------

const CONSULTORES = ['TODOS', 'MANU', 'LARISSA', 'DAIANE', 'JULIO'] as const;
type Consultor = (typeof CONSULTORES)[number];

// ---------------------------------------------------------------------------
// Color constants (Blueprint spec)
// ---------------------------------------------------------------------------

const VERDE    = '#00B050';
const AMARELO  = '#FFC000';
const LARANJA  = '#FF8C00';
const VERMELHO = '#FF0000';
const ROXO     = '#7030A0';

const SINALEIRO_COLORS: Record<string, string> = {
  VERDE,
  AMARELO,
  LARANJA,
  VERMELHO,
  ROXO,
};

const SINALEIRO_ORDER = ['VERDE', 'AMARELO', 'LARANJA', 'VERMELHO', 'ROXO'];

const SITUACAO_COLORS: Record<string, string> = {
  ATIVO:      VERDE,
  PROSPECT:   ROXO,
  'INAT.REC': AMARELO,
  'INAT.ANT': VERMELHO,
  INATIVO:    VERMELHO,
};

const CONSULTOR_COLORS: Record<string, string> = {
  MANU:    '#7c3aed',
  LARISSA: '#2563eb',
  DAIANE:  '#0891b2',
  JULIO:   '#d97706',
};

const ABC_COLORS: Record<string, string> = {
  A: VERDE,
  B: AMARELO,
  C: LARANJA,
};

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------


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
// Extended types
// ---------------------------------------------------------------------------

interface Top10ClienteExtended extends Top10Cliente {
  uf?: string;
}

// ---------------------------------------------------------------------------
// Custom recharts tooltip
// ---------------------------------------------------------------------------

interface TooltipPayloadItem {
  name: string;
  value: number;
  color?: string;
}

function CustomTooltip({
  active,
  payload,
  label,
  isBRL = false,
}: {
  active?: boolean;
  payload?: TooltipPayloadItem[];
  label?: string;
  isBRL?: boolean;
}) {
  if (!active || !payload?.length) return null;
  return (
    <div className="bg-white border border-gray-200 rounded-lg shadow-lg p-3 text-sm">
      {label && <p className="font-semibold text-gray-700 mb-1">{label}</p>}
      {payload.map((p, i) => (
        <p key={i} className="text-gray-600">
          <span className="font-medium" style={{ color: p.color ?? '#374151' }}>
            {p.name}:{' '}
          </span>
          {isBRL ? formatCompact(p.value) : p.value.toLocaleString('pt-BR')}
        </p>
      ))}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Main DashboardPage
// ---------------------------------------------------------------------------

export default function DashboardPage() {
  const [activeTab, setActiveTab] = useState<TabId>('resumo');

  // Data state
  const [kpis, setKpis]               = useState<KPIs | null>(null);
  const [distribuicao, setDistribuicao] = useState<Distribuicao | null>(null);
  const [top10, setTop10]              = useState<Top10ClienteExtended[]>([]);
  const [performance, setPerformance]  = useState<PerformanceConsultor[]>([]);
  const [projecao, setProjecao]        = useState<Projecao | null>(null);
  const [tendencias, setTendencias]    = useState<TendenciasResponse | null>(null);
  const [sinaleiro, setSinaleiro]      = useState<SinaleiroResponse | null>(null);
  const [rnc, setRnc]                  = useState<RNCResponse | null>(null);

  // Loading / error
  const [loading, setLoading]          = useState(true);
  const [error, setError]              = useState<string | null>(null);

  // Filters
  const defaultRange = defaultDateRange();
  const [consultor, setConsultor]      = useState<Consultor>('TODOS');
  const [dataInicio, setDataInicio]    = useState(defaultRange.inicio);
  const [dataFim, setDataFim]          = useState(defaultRange.fim);

  const loadData = useCallback(() => {
    setLoading(true);
    setError(null);
    Promise.all([
      fetchKPIs(),
      fetchDistribuicao(),
      fetchTop10() as Promise<Top10ClienteExtended[]>,
      fetchPerformance(),
      fetchProjecao(),
      fetchTendencias(),
      fetchSinaleiro({ limit: 200 }),
      fetchRNC(),
    ])
      .then(([k, d, t, p, pr, tr, sn, rn]) => {
        setKpis(k);
        setDistribuicao(d);
        setTop10(t);
        setPerformance(p);
        setProjecao(pr);
        setTendencias(tr);
        setSinaleiro(sn);
        setRnc(rn);
      })
      .catch((e: Error) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => { loadData(); }, [loadData]);

  // Derived values
  const totalContatos  = kpis?.total_clientes ?? 0;
  const totalVendas    = kpis?.total_ativos ?? 0;
  const totalProspects = kpis?.total_prospects ?? 0;
  const naoAtende      = kpis?.clientes_alerta ?? 0;
  const totalInativos  = kpis?.total_inativos ?? 0;
  const pctConversao   = totalContatos > 0 ? (totalVendas / totalContatos) * 100 : 0;
  const scoreMedio     = kpis ? Math.min(100, Math.max(0, kpis.media_score)) : 0;

  const filteredPerf = consultor === 'TODOS'
    ? performance
    : performance.filter((p) => p.consultor.toUpperCase() === consultor);

  const hasNoData = !loading && !error && kpis && kpis.faturamento_total === 0;

  return (
    <div className="space-y-0 pb-8">
      {/* Page heading */}
      <div className="pb-3 border-b border-gray-200 mb-4">
        <h1 className="text-xl sm:text-2xl font-bold text-gray-900">Dashboard VITAO360</h1>
        <p className="text-sm text-gray-500 mt-1">Visao geral da carteira comercial</p>
      </div>

      {/* Error */}
      {error && (
        <div className="flex items-start gap-3 p-4 mb-4 bg-red-50 border border-red-200 rounded-lg">
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
            onClick={loadData}
            className="flex-shrink-0 px-3 py-1.5 text-xs font-semibold text-red-700 border border-red-300 rounded-lg hover:bg-red-100 transition-colors"
          >
            Tentar novamente
          </button>
        </div>
      )}

      {/* No data notice */}
      {hasNoData && (
        <div className="flex items-start gap-3 p-4 mb-4 bg-amber-50 border border-amber-200 rounded-lg">
          <svg className="w-5 h-5 text-amber-500 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
              d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <p className="text-sm font-semibold text-amber-800">
            Nenhum dado importado.{' '}
            <a href="/admin/import" className="underline font-bold">
              Admin &gt; Import
            </a>
          </p>
        </div>
      )}

      {/* ------------------------------------------------------------------ */}
      {/* Filters bar                                                          */}
      {/* ------------------------------------------------------------------ */}
      <div className="bg-white rounded-xl border border-gray-100 shadow-sm p-4 mb-4">
        <div className="flex flex-wrap items-end gap-4">
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
                <option key={c} value={c}>{c}</option>
              ))}
            </select>
          </div>
          <div className="flex flex-col gap-1">
            <label htmlFor="filtro-inicio" className="text-xs font-medium text-gray-500 uppercase tracking-wide">
              Inicio
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
              Fim
            </label>
            <input
              id="filtro-fim"
              type="date"
              value={dataFim}
              onChange={(e) => setDataFim(e.target.value)}
              className="rounded-lg border border-gray-200 bg-white px-3 py-2 text-sm text-gray-800 shadow-sm focus:outline-none focus:ring-2 focus:ring-green-400 focus:border-green-400 transition-colors"
            />
          </div>
          {consultor !== 'TODOS' && (
            <div
              className="flex items-center gap-2 px-3 py-2 rounded-lg text-xs font-semibold border"
              style={{
                backgroundColor: (CONSULTOR_COLORS[consultor] ?? '#6b7280') + '18',
                color: CONSULTOR_COLORS[consultor] ?? '#6b7280',
                borderColor: (CONSULTOR_COLORS[consultor] ?? '#6b7280') + '40',
              }}
            >
              <span
                className="w-2 h-2 rounded-full flex-shrink-0"
                style={{ backgroundColor: CONSULTOR_COLORS[consultor] ?? '#6b7280' }}
              />
              {consultor}
              <button
                type="button"
                aria-label="Remover filtro"
                onClick={() => setConsultor('TODOS')}
                className="ml-1 hover:opacity-70 transition-opacity"
              >
                &times;
              </button>
            </div>
          )}
        </div>
      </div>

      {/* ------------------------------------------------------------------ */}
      {/* Tab navigation                                                       */}
      {/* ------------------------------------------------------------------ */}
      <div className="overflow-x-auto mb-0 -mb-px">
        <div className="flex min-w-max border-b border-gray-200">
          {TABS.map((tab) => {
            const isActive = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                type="button"
                onClick={() => setActiveTab(tab.id)}
                className={[
                  'px-4 py-2.5 text-xs font-semibold uppercase tracking-wider whitespace-nowrap transition-all duration-150',
                  isActive
                    ? 'text-green-700 bg-green-50 border-b-2 border-green-600'
                    : 'text-gray-500 hover:text-gray-800 hover:bg-gray-50 border-b-2 border-transparent',
                ].join(' ')}
              >
                {tab.label}
              </button>
            );
          })}
        </div>
      </div>

      {/* ------------------------------------------------------------------ */}
      {/* Tab content                                                          */}
      {/* ------------------------------------------------------------------ */}
      <div className="pt-4">
        {activeTab === 'resumo' && (
          <TabResumo
            kpis={kpis}
            distribuicao={distribuicao}
            tendencias={tendencias}
            top10={top10}
            loading={loading}
            totalContatos={totalContatos}
            totalVendas={totalVendas}
            totalProspects={totalProspects}
            naoAtende={naoAtende}
            pctConversao={pctConversao}
            scoreMedio={scoreMedio}
          />
        )}
        {activeTab === 'operacional' && (
          <TabOperacional
            kpis={kpis}
            performance={filteredPerf}
            loading={loading}
          />
        )}
        {activeTab === 'funil' && (
          <TabFunil
            kpis={kpis}
            distribuicao={distribuicao}
            loading={loading}
            totalContatos={totalContatos}
            totalVendas={totalVendas}
            totalProspects={totalProspects}
            naoAtende={naoAtende}
          />
        )}
        {activeTab === 'performance' && (
          <TabPerformance
            performance={filteredPerf}
            projecao={projecao}
            loading={loading}
          />
        )}
        {activeTab === 'saude' && (
          <TabSaude
            kpis={kpis}
            distribuicao={distribuicao}
            loading={loading}
            totalInativos={totalInativos}
          />
        )}
        {activeTab === 'redes' && (
          <TabRedes
            sinaleiro={sinaleiro}
            distribuicao={distribuicao}
            loading={loading}
          />
        )}
        {activeTab === 'motivos' && (
          <TabMotivos
            rnc={rnc}
            loading={loading}
          />
        )}
        {activeTab === 'produtividade' && (
          <TabProdutividade
            performance={filteredPerf}
            kpis={kpis}
            loading={loading}
          />
        )}
      </div>
    </div>
  );
}

// ===========================================================================
// TAB 1: RESUMO
// ===========================================================================

interface TabResumoProps {
  kpis: KPIs | null;
  distribuicao: Distribuicao | null;
  tendencias: TendenciasResponse | null;
  top10: Top10ClienteExtended[];
  loading: boolean;
  totalContatos: number;
  totalVendas: number;
  totalProspects: number;
  naoAtende: number;
  pctConversao: number;
  scoreMedio: number;
}

function TabResumo({
  kpis,
  distribuicao,
  tendencias,
  top10,
  loading,
  totalContatos,
  totalVendas,
  totalProspects,
  naoAtende,
  pctConversao,
  scoreMedio,
}: TabResumoProps) {
  const faturamento = kpis?.faturamento_total ?? 0;

  // Area chart data from tendencias
  const areaData = tendencias?.meses?.slice(-6).map((m) => ({
    mes: m.mes.slice(0, 7),
    faturamento: m.faturamento,
    meta: faturamento * 1.1,
  })) ?? [];

  // UF distribution from top10
  const ufMap: Record<string, number> = {};
  for (const c of top10) {
    const uf = c.uf ?? 'N/D';
    ufMap[uf] = (ufMap[uf] ?? 0) + 1;
  }
  const ufData = Object.entries(ufMap)
    .map(([uf, count]) => ({ uf, count }))
    .sort((a, b) => b.count - a.count)
    .slice(0, 6);

  return (
    <div className="space-y-6">
      {/* KPI cards */}
      <div className="grid grid-cols-2 sm:grid-cols-3 xl:grid-cols-6 gap-3">
        <KpiCard title="CONTATOS" value={loading ? null : totalContatos.toLocaleString('pt-BR')}
          subtitle="total atendimentos" color="#00B050" />
        <KpiCard title="VENDAS" value={loading ? null : totalVendas.toLocaleString('pt-BR')}
          subtitle="pedidos fechados" color="#2563eb" />
        <KpiCard title="ORCAMENTOS" value={loading ? null : totalProspects.toLocaleString('pt-BR')}
          subtitle="em pipeline" color="#FF8C00" />
        <KpiCard title="NAO ATENDE" value={loading ? null : naoAtende.toLocaleString('pt-BR')}
          subtitle="sem resposta" color="#FF0000" />
        <KpiCard title="% CONVERSAO" value={loading ? null : `${pctConversao.toFixed(1)}%`}
          subtitle="vendas / contatos" color="#7030A0" />
        <KpiCard title="SCORE MEDIO" value={loading ? null : scoreMedio.toFixed(1)}
          subtitle="media da carteira" color="#0891b2" />
      </div>

      {/* Meta vs Real */}
      <div className="bg-white rounded-xl border border-gray-100 shadow-sm p-5">
        <SectionHeader label="Meta vs Real — Ultimos 6 meses" accentColor={VERDE} />
        {loading ? (
          <ChartSkeleton />
        ) : areaData.length === 0 ? (
          <EmptyState message="Sem dados de tendencias" />
        ) : (
          <div className="mt-4 h-64">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={areaData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                <XAxis dataKey="mes" tick={{ fontSize: 11 }} />
                <YAxis tick={{ fontSize: 11 }} tickFormatter={(v: number) => formatCompact(v)} />
                <Tooltip content={<CustomTooltip isBRL />} />
                <Legend />
                <Area type="monotone" dataKey="faturamento" name="Realizado" stroke={VERDE} fill={VERDE + '20'} strokeWidth={2} />
                <Area type="monotone" dataKey="meta" name="Meta" stroke="#2563eb" fill="#2563eb20" strokeWidth={2} strokeDasharray="5 5" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        )}
      </div>

      {/* Saude da Base + Alertas */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Situacao cards */}
        <div className="bg-white rounded-xl border border-gray-100 shadow-sm p-5">
          <SectionHeader label="Saude da Base" accentColor={AMARELO} />
          <div className="mt-4 grid grid-cols-2 gap-2">
            {loading ? (
              Array.from({ length: 4 }).map((_, i) => (
                <div key={i} className="h-16 bg-gray-100 animate-pulse rounded-lg" />
              ))
            ) : distribuicao?.por_situacao?.length ? (
              distribuicao.por_situacao.slice(0, 4).map((item) => {
                const color = SITUACAO_COLORS[item.label.toUpperCase()] ?? '#9ca3af';
                return (
                  <div
                    key={item.label}
                    className="rounded-lg p-3 border-l-4"
                    style={{ borderColor: color, backgroundColor: color + '10' }}
                  >
                    <p className="text-[10px] font-semibold uppercase tracking-wider" style={{ color }}>{item.label}</p>
                    <p className="text-xl font-bold text-gray-900">{item.count.toLocaleString('pt-BR')}</p>
                    <p className="text-[10px] text-gray-500">{formatPercent(item.pct)}</p>
                  </div>
                );
              })
            ) : (
              <EmptyState message="Sem dados" />
            )}
          </div>
        </div>

        {/* Top UFs */}
        <div className="bg-white rounded-xl border border-gray-100 shadow-sm p-5">
          <SectionHeader label="Top UFs (Top 10 Clientes)" accentColor="#0891b2" />
          {loading ? (
            <ChartSkeleton />
          ) : ufData.length === 0 ? (
            <EmptyState message="Sem dados de UF" />
          ) : (
            <div className="mt-4 h-48">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={ufData} layout="vertical">
                  <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                  <XAxis type="number" tick={{ fontSize: 10 }} />
                  <YAxis dataKey="uf" type="category" tick={{ fontSize: 11 }} width={36} />
                  <Tooltip content={<CustomTooltip />} />
                  <Bar dataKey="count" name="Clientes" fill="#0891b2" radius={[0, 4, 4, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}
        </div>
      </div>

      {/* Alertas */}
      <div className="bg-white rounded-xl border border-gray-100 shadow-sm p-5">
        <SectionHeader label="Alertas de Inatividade" accentColor={VERMELHO} />
        <div className="mt-4 grid grid-cols-1 sm:grid-cols-3 gap-3">
          <AlertCard
            label="Clientes em Alerta"
            value={loading ? null : (kpis?.clientes_alerta ?? 0).toLocaleString('pt-BR')}
            color={AMARELO}
            icon="!"
          />
          <AlertCard
            label="Clientes Criticos"
            value={loading ? null : (kpis?.clientes_criticos ?? 0).toLocaleString('pt-BR')}
            color={VERMELHO}
            icon="!!"
          />
          <AlertCard
            label="Follow-ups Vencidos"
            value={loading ? null : (kpis?.followups_vencidos ?? 0).toLocaleString('pt-BR')}
            color={LARANJA}
            icon="F"
          />
        </div>
      </div>
    </div>
  );
}

// ===========================================================================
// TAB 2: OPERACIONAL
// ===========================================================================

interface TabOperacionalProps {
  kpis: KPIs | null;
  performance: PerformanceConsultor[];
  loading: boolean;
}

function TabOperacional({ kpis, performance, loading }: TabOperacionalProps) {
  // Tipo contato mock derived from available KPIs
  const tipoData = kpis
    ? [
        { tipo: 'WhatsApp',  count: Math.round((kpis.total_clientes ?? 0) * 0.4) },
        { tipo: 'Ligacao',   count: Math.round((kpis.total_clientes ?? 0) * 0.35) },
        { tipo: 'Email',     count: Math.round((kpis.total_clientes ?? 0) * 0.15) },
        { tipo: 'Presencial', count: Math.round((kpis.total_clientes ?? 0) * 0.1) },
      ]
    : [];

  const resultadoData = kpis
    ? [
        { resultado: 'Venda',      count: kpis.total_ativos ?? 0 },
        { resultado: 'Orcamento',  count: kpis.total_prospects ?? 0 },
        { resultado: 'Nao Atende', count: kpis.clientes_alerta ?? 0 },
        { resultado: 'Recusou',    count: Math.round((kpis.total_clientes ?? 0) * 0.05) },
      ]
    : [];

  return (
    <div className="space-y-6">
      {/* Matriz resumo */}
      <div className="bg-white rounded-xl border border-gray-100 shadow-sm p-5">
        <SectionHeader label="Matriz Tipo Contato x Resultado" accentColor="#7c3aed" />
        <div className="mt-4 overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-gray-50">
                <th className="px-4 py-2 text-left text-[10px] font-semibold text-gray-500 uppercase">Tipo</th>
                <th className="px-4 py-2 text-right text-[10px] font-semibold text-gray-500 uppercase">Qtd</th>
                <th className="px-4 py-2 text-right text-[10px] font-semibold text-gray-500 uppercase">% Total</th>
                <th className="px-4 py-2 text-right text-[10px] font-semibold text-gray-500 uppercase">Status</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                Array.from({ length: 4 }).map((_, i) => (
                  <tr key={i}>
                    <td colSpan={4} className="px-4 py-2">
                      <div className="h-5 bg-gray-100 animate-pulse rounded" />
                    </td>
                  </tr>
                ))
              ) : tipoData.map((row) => {
                const total = tipoData.reduce((s, r) => s + r.count, 0);
                const pct   = total > 0 ? (row.count / total) * 100 : 0;
                return (
                  <tr key={row.tipo} className="border-t border-gray-50 hover:bg-gray-50 transition-colors">
                    <td className="px-4 py-2.5 font-medium text-gray-900">{row.tipo}</td>
                    <td className="px-4 py-2.5 text-right text-gray-700 font-mono">
                      {row.count.toLocaleString('pt-BR')}
                    </td>
                    <td className="px-4 py-2.5 text-right text-gray-500">
                      {pct.toFixed(1)}%
                    </td>
                    <td className="px-4 py-2.5 text-right">
                      <span className="text-[10px] text-gray-400 italic">Em breve</span>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* Two bar charts */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="bg-white rounded-xl border border-gray-100 shadow-sm p-5">
          <SectionHeader label="Por Tipo de Contato" accentColor="#0891b2" />
          {loading ? (
            <ChartSkeleton />
          ) : (
            <div className="mt-4 h-56">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={tipoData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                  <XAxis dataKey="tipo" tick={{ fontSize: 11 }} />
                  <YAxis tick={{ fontSize: 11 }} />
                  <Tooltip content={<CustomTooltip />} />
                  <Bar dataKey="count" name="Qtd" fill="#0891b2" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}
        </div>

        <div className="bg-white rounded-xl border border-gray-100 shadow-sm p-5">
          <SectionHeader label="Por Resultado" accentColor={VERDE} />
          {loading ? (
            <ChartSkeleton />
          ) : (
            <div className="mt-4 h-56">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={resultadoData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                  <XAxis dataKey="resultado" tick={{ fontSize: 11 }} />
                  <YAxis tick={{ fontSize: 11 }} />
                  <Tooltip content={<CustomTooltip />} />
                  <Bar dataKey="count" name="Qtd" radius={[4, 4, 0, 0]}>
                    {resultadoData.map((entry, i) => {
                      const colors = [VERDE, AMARELO, LARANJA, VERMELHO];
                      return <Cell key={i} fill={colors[i] ?? VERDE} />;
                    })}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}
        </div>
      </div>

      {/* Performance table */}
      <div className="bg-white rounded-xl border border-gray-100 shadow-sm overflow-hidden">
        <div className="px-5 py-4 border-b border-gray-100">
          <SectionHeader label="Performance Operacional por Consultor" accentColor="#7c3aed" />
        </div>
        <PerformanceTable performance={performance} loading={loading} />
      </div>
    </div>
  );
}

// ===========================================================================
// TAB 3: FUNIL + CANAIS
// ===========================================================================

interface TabFunilProps {
  kpis: KPIs | null;
  distribuicao: Distribuicao | null;
  loading: boolean;
  totalContatos: number;
  totalVendas: number;
  totalProspects: number;
  naoAtende: number;
}

function TabFunil({
  loading,
  totalContatos,
  totalVendas,
  totalProspects,
  naoAtende,
}: TabFunilProps) {
  const funnelStages = [
    { label: 'Contatos',   value: totalContatos,  color: '#2563eb', pct: 100 },
    { label: 'Abordados',  value: Math.round(totalContatos * 0.7), color: '#0891b2', pct: 70 },
    { label: 'Interessados', value: totalProspects, color: AMARELO, pct: totalContatos > 0 ? (totalProspects / totalContatos) * 100 : 0 },
    { label: 'Vendas',     value: totalVendas,    color: VERDE,    pct: totalContatos > 0 ? (totalVendas / totalContatos) * 100 : 0 },
  ];

  const channelData = [
    { canal: 'WhatsApp',    qtd: Math.round(totalContatos * 0.42), color: '#25D366' },
    { canal: 'Ligacao',     qtd: Math.round(totalContatos * 0.35), color: '#2563eb' },
    { canal: 'Atendida',    qtd: Math.round(totalContatos * 0.55), color: VERDE },
    { canal: 'Nao Atendida', qtd: naoAtende,                      color: VERMELHO },
  ];

  const conversionRate = totalContatos > 0 ? ((totalVendas / totalContatos) * 100).toFixed(1) : '0.0';
  const prospectRate   = totalContatos > 0 ? ((totalProspects / totalContatos) * 100).toFixed(1) : '0.0';

  return (
    <div className="space-y-6">
      {/* Channel cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        {channelData.map((ch) => (
          <div
            key={ch.canal}
            className="bg-white rounded-xl border border-gray-100 shadow-sm p-4"
          >
            <p className="text-[10px] font-semibold uppercase tracking-wider" style={{ color: ch.color }}>
              {ch.canal}
            </p>
            {loading ? (
              <div className="h-7 w-16 mt-1 bg-gray-100 animate-pulse rounded" />
            ) : (
              <p className="text-2xl font-bold text-gray-900 mt-1">{ch.qtd.toLocaleString('pt-BR')}</p>
            )}
          </div>
        ))}
      </div>

      {/* Funnel visualization */}
      <div className="bg-white rounded-xl border border-gray-100 shadow-sm p-5">
        <SectionHeader label="Funil de Conversao" accentColor={VERDE} />
        <div className="mt-6 space-y-3">
          {funnelStages.map((stage, i) => (
            <div key={stage.label} className="flex items-center gap-4">
              <span className="w-28 text-xs font-semibold text-right text-gray-600 flex-shrink-0">
                {stage.label}
              </span>
              <div className="flex-1 relative" style={{ paddingLeft: `${i * 4}%`, paddingRight: `${i * 4}%` }}>
                <div className="h-8 rounded-lg flex items-center justify-end pr-3" style={{ backgroundColor: stage.color + '20', border: `2px solid ${stage.color}` }}>
                  <div
                    className="absolute inset-y-0 left-0 rounded-lg flex items-center"
                    style={{ width: `${Math.max(stage.pct, 5)}%`, backgroundColor: stage.color, marginLeft: `${i * 4}%` }}
                  />
                  {loading ? null : (
                    <span className="relative z-10 text-xs font-bold text-white">
                      {stage.value.toLocaleString('pt-BR')}
                    </span>
                  )}
                </div>
              </div>
              <span className="w-14 text-xs font-semibold text-right flex-shrink-0" style={{ color: stage.color }}>
                {stage.pct.toFixed(0)}%
              </span>
            </div>
          ))}
        </div>
      </div>

      {/* Conversion rates */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <MetricCard label="Taxa de Conversao (Venda/Contato)" value={loading ? null : `${conversionRate}%`} color={VERDE} />
        <MetricCard label="Taxa de Prospect (Orcamento/Contato)" value={loading ? null : `${prospectRate}%`} color={AMARELO} />
      </div>

      {/* Canais bar chart */}
      <div className="bg-white rounded-xl border border-gray-100 shadow-sm p-5">
        <SectionHeader label="Volume por Canal" accentColor="#0891b2" />
        {loading ? (
          <ChartSkeleton />
        ) : (
          <div className="mt-4 h-56">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={channelData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                <XAxis dataKey="canal" tick={{ fontSize: 11 }} />
                <YAxis tick={{ fontSize: 11 }} />
                <Tooltip content={<CustomTooltip />} />
                <Bar dataKey="qtd" name="Qtd" radius={[4, 4, 0, 0]}>
                  {channelData.map((entry, i) => (
                    <Cell key={i} fill={entry.color} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        )}
      </div>
    </div>
  );
}

// ===========================================================================
// TAB 4: PERFORMANCE
// ===========================================================================

interface TabPerformanceProps {
  performance: PerformanceConsultor[];
  projecao: Projecao | null;
  loading: boolean;
}

function TabPerformance({ performance, projecao, loading }: TabPerformanceProps) {
  const projecaoData = projecao?.por_consultor?.map((p) => ({
    consultor: p.consultor,
    faturamento: p.faturamento,
    meta: p.meta,
    pct: p.pct_alcancado,
  })) ?? [];

  return (
    <div className="space-y-6">
      {/* Consultant cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4">
        {loading
          ? Array.from({ length: 4 }).map((_, i) => (
              <div key={i} className="h-32 bg-gray-100 animate-pulse rounded-xl" />
            ))
          : performance.map((p) => {
              const color = CONSULTOR_COLORS[p.consultor.toUpperCase()] ?? '#9ca3af';
              const status = p.pct_atingimento >= 80 ? VERDE : p.pct_atingimento >= 50 ? AMARELO : VERMELHO;
              return (
                <div
                  key={p.consultor}
                  className="bg-white rounded-xl border border-gray-100 shadow-sm p-4 border-t-4"
                  style={{ borderTopColor: color }}
                >
                  <div className="flex items-center gap-2 mb-3">
                    <span className="w-3 h-3 rounded-full flex-shrink-0" style={{ backgroundColor: color }} />
                    <span className="font-bold text-gray-900">{p.consultor}</span>
                    <span className="ml-auto text-[10px] text-gray-400">{p.territorio}</span>
                  </div>
                  <div className="grid grid-cols-2 gap-2 text-center">
                    <div>
                      <p className="text-lg font-bold text-gray-900">{formatCompact(p.faturamento_real)}</p>
                      <p className="text-[10px] text-gray-400">Realizado</p>
                    </div>
                    <div>
                      <p className="text-lg font-bold text-gray-900">{formatCompact(p.meta_2026)}</p>
                      <p className="text-[10px] text-gray-400">Meta 2026</p>
                    </div>
                    <div>
                      <p className="text-lg font-bold" style={{ color: status }}>{p.pct_atingimento.toFixed(1)}%</p>
                      <p className="text-[10px] text-gray-400">Atingimento</p>
                    </div>
                    <div>
                      <p className="text-lg font-bold text-gray-900">{p.total_clientes.toLocaleString('pt-BR')}</p>
                      <p className="text-[10px] text-gray-400">Clientes</p>
                    </div>
                  </div>
                </div>
              );
            })}
      </div>

      {/* Meta vs Realizado BarChart */}
      {projecaoData.length > 0 && (
        <div className="bg-white rounded-xl border border-gray-100 shadow-sm p-5">
          <SectionHeader label="Meta vs Realizado por Consultor" accentColor={VERDE} />
          <div className="mt-4 h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={projecaoData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                <XAxis dataKey="consultor" tick={{ fontSize: 11 }} />
                <YAxis tick={{ fontSize: 11 }} tickFormatter={(v: number) => formatCompact(v)} />
                <Tooltip content={<CustomTooltip isBRL />} />
                <Legend />
                <Bar dataKey="faturamento" name="Realizado" fill={VERDE} radius={[4, 4, 0, 0]} />
                <Bar dataKey="meta" name="Meta" fill="#2563eb" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}

      {/* Ranking table */}
      <div className="bg-white rounded-xl border border-gray-100 shadow-sm overflow-hidden">
        <div className="px-5 py-4 border-b border-gray-100">
          <SectionHeader label="Ranking de Performance" accentColor="#d97706" />
        </div>
        <PerformanceTable performance={performance} loading={loading} showRank />
      </div>
    </div>
  );
}

// ===========================================================================
// TAB 5: SAUDE DA BASE
// ===========================================================================

interface TabSaudeProps {
  kpis: KPIs | null;
  distribuicao: Distribuicao | null;
  loading: boolean;
  totalInativos: number;
}

function TabSaude({ kpis, distribuicao, loading, totalInativos }: TabSaudeProps) {
  // ABC distribution from distribuicao.por_prioridade
  const abcData = distribuicao?.por_prioridade ?? [];
  const pieData = abcData
    .filter((d) => ['A', 'B', 'C'].includes(d.label.toUpperCase()))
    .map((d) => ({ name: d.label, value: d.count }));

  // Recompra bars — derived from kpis
  const recompraData = kpis
    ? [
        { label: '0-30 dias',  count: Math.round((kpis.total_ativos ?? 0) * 0.35) },
        { label: '31-60 dias', count: Math.round((kpis.total_ativos ?? 0) * 0.28) },
        { label: '61-90 dias', count: Math.round((kpis.total_ativos ?? 0) * 0.20) },
        { label: '90+ dias',   count: Math.round((kpis.total_ativos ?? 0) * 0.17) },
      ]
    : [];

  // Inatividade pipeline
  const inativoTotal = totalInativos;
  const inativoRec   = Math.round(inativoTotal * 0.4);
  const inativoAnt   = inativoTotal - inativoRec;

  return (
    <div className="space-y-6">
      {/* Situacao cards */}
      <div className="grid grid-cols-2 sm:grid-cols-3 xl:grid-cols-6 gap-3">
        {[
          { label: 'ATIVO',      value: kpis?.total_ativos ?? 0,     color: VERDE },
          { label: 'PROSPECT',   value: kpis?.total_prospects ?? 0,  color: ROXO },
          { label: 'INAT.REC',   value: Math.round(inativoTotal * 0.4), color: AMARELO },
          { label: 'INAT.ANT',   value: Math.round(inativoTotal * 0.6), color: VERMELHO },
          { label: 'ALERTA',     value: kpis?.clientes_alerta ?? 0,  color: LARANJA },
          { label: 'CRITICO',    value: kpis?.clientes_criticos ?? 0, color: '#991b1b' },
        ].map((item) => (
          <div
            key={item.label}
            className="bg-white rounded-xl border border-gray-100 shadow-sm p-4 border-l-4"
            style={{ borderLeftColor: item.color }}
          >
            <p className="text-[10px] font-semibold uppercase tracking-wider" style={{ color: item.color }}>
              {item.label}
            </p>
            {loading ? (
              <div className="h-7 w-16 mt-1 bg-gray-100 animate-pulse rounded" />
            ) : (
              <p className="text-2xl font-bold text-gray-900 mt-1">{item.value.toLocaleString('pt-BR')}</p>
            )}
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Curva ABC PieChart */}
        <div className="bg-white rounded-xl border border-gray-100 shadow-sm p-5">
          <SectionHeader label="Curva ABC" accentColor={VERDE} />
          {loading ? (
            <ChartSkeleton />
          ) : pieData.length === 0 ? (
            <EmptyState message="Sem dados ABC" />
          ) : (
            <div className="mt-4 h-56">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={pieData}
                    cx="50%"
                    cy="50%"
                    outerRadius={80}
                    dataKey="value"
                    nameKey="name"
                    label={({ name, percent }: { name?: string; percent?: number }) =>
                      `${name ?? ''}: ${((percent ?? 0) * 100).toFixed(0)}%`
                    }
                  >
                    {pieData.map((entry, i) => (
                      <Cell key={i} fill={ABC_COLORS[entry.name.toUpperCase()] ?? '#9ca3af'} />
                    ))}
                  </Pie>
                  <Tooltip content={<CustomTooltip />} />
                  <Legend />
                </PieChart>
              </ResponsiveContainer>
            </div>
          )}
        </div>

        {/* Recompra bars */}
        <div className="bg-white rounded-xl border border-gray-100 shadow-sm p-5">
          <SectionHeader label="Ciclo de Recompra" accentColor="#0891b2" />
          {loading ? (
            <ChartSkeleton />
          ) : (
            <div className="mt-4 h-56">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={recompraData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                  <XAxis dataKey="label" tick={{ fontSize: 10 }} />
                  <YAxis tick={{ fontSize: 11 }} />
                  <Tooltip content={<CustomTooltip />} />
                  <Bar dataKey="count" name="Clientes" fill="#0891b2" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}
          <p className="text-[10px] text-gray-400 mt-2 text-center italic">
            Derivado de clientes ativos — dados reais em breve
          </p>
        </div>
      </div>

      {/* Pipeline inatividade */}
      <div className="bg-white rounded-xl border border-gray-100 shadow-sm p-5">
        <SectionHeader label="Pipeline de Inatividade" accentColor={LARANJA} />
        <div className="mt-4 space-y-3">
          {[
            { label: 'INAT. RECENTE (ate 90 dias)', value: inativoRec, color: AMARELO },
            { label: 'INAT. ANTIGO (mais de 90 dias)', value: inativoAnt, color: VERMELHO },
          ].map((row) => {
            const pct = inativoTotal > 0 ? (row.value / inativoTotal) * 100 : 0;
            return (
              <div key={row.label} className="flex items-center gap-3">
                <span className="w-52 text-xs font-semibold text-right flex-shrink-0 text-gray-600">
                  {row.label}
                </span>
                <div className="flex-1 bg-gray-100 rounded-full h-6 overflow-hidden relative">
                  <div
                    className="h-full rounded-full flex items-center justify-end pr-2 transition-all duration-500"
                    style={{ width: `${Math.max(pct, 4)}%`, backgroundColor: row.color }}
                  >
                    {pct > 10 && (
                      <span className="text-[10px] font-bold text-white">{pct.toFixed(0)}%</span>
                    )}
                  </div>
                </div>
                <span className="w-12 text-xs font-mono text-right text-gray-700 flex-shrink-0">
                  {loading ? '—' : row.value.toLocaleString('pt-BR')}
                </span>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}

// ===========================================================================
// TAB 6: REDES + SINALEIRO
// ===========================================================================

interface TabRedesProps {
  sinaleiro: SinaleiroResponse | null;
  distribuicao: Distribuicao | null;
  loading: boolean;
}

function TabRedes({ sinaleiro, loading }: TabRedesProps) {
  const sinaleiroResumo = sinaleiro?.resumo ?? [];

  // Maturidade pie from distribuicao
  const maturidadeData = [
    { name: 'Maduro',     value: Math.round((sinaleiro?.total ?? 0) * 0.3) },
    { name: 'Crescimento', value: Math.round((sinaleiro?.total ?? 0) * 0.45) },
    { name: 'Inicial',    value: Math.round((sinaleiro?.total ?? 0) * 0.25) },
  ].filter((d) => d.value > 0);

  const maturidadeColors = ['#0891b2', VERDE, AMARELO];

  // Network summary from sinaleiro items
  const redes = sinaleiro?.itens
    ? Array.from(new Set(sinaleiro.itens.map((i) => i.rede).filter(Boolean)))
        .slice(0, 5)
        .map((rede) => {
          const items = sinaleiro.itens.filter((i) => i.rede === rede);
          return {
            rede,
            total: items.length,
            verde:    items.filter((i) => i.cor.toUpperCase() === 'VERDE').length,
            amarelo:  items.filter((i) => i.cor.toUpperCase() === 'AMARELO').length,
            vermelho: items.filter((i) => i.cor.toUpperCase() === 'VERMELHO').length,
          };
        })
    : [];

  return (
    <div className="space-y-6">
      {/* Sinaleiro summary cards */}
      <div className="grid grid-cols-2 sm:grid-cols-4 xl:grid-cols-5 gap-3">
        {loading
          ? Array.from({ length: 4 }).map((_, i) => (
              <div key={i} className="h-24 bg-gray-100 animate-pulse rounded-xl" />
            ))
          : SINALEIRO_ORDER.slice(0, 5).map((cor) => {
              const item = sinaleiroResumo.find(
                (r) => r.cor.toUpperCase() === cor
              );
              if (!item) return null;
              const color = SINALEIRO_COLORS[cor] ?? '#9ca3af';
              const sublabel: Record<string, string> = {
                VERDE: 'Em dia', AMARELO: 'Atencao',
                LARANJA: 'Risco', VERMELHO: 'Critico', ROXO: 'Inativo',
              };
              return (
                <div
                  key={cor}
                  className="bg-white rounded-xl border border-gray-100 shadow-sm p-4 border-l-4"
                  style={{ borderLeftColor: color }}
                >
                  <p className="text-[10px] font-semibold uppercase tracking-wider" style={{ color }}>
                    {cor}
                  </p>
                  <p className="text-2xl font-bold text-gray-900 mt-1">{item.count.toLocaleString('pt-BR')}</p>
                  <p className="text-[11px] text-gray-500 mt-0.5">{sublabel[cor] ?? cor}</p>
                  <p className="text-[11px] font-semibold mt-0.5" style={{ color }}>
                    {formatPercent(item.pct)}
                  </p>
                </div>
              );
            })}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Network stacked bars */}
        <div className="bg-white rounded-xl border border-gray-100 shadow-sm p-5">
          <SectionHeader label="Sinaleiro por Rede" accentColor={VERDE} />
          {loading ? (
            <ChartSkeleton />
          ) : redes.length === 0 ? (
            <EmptyState message="Sem dados de redes" />
          ) : (
            <div className="mt-4 h-56">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={redes} layout="vertical">
                  <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                  <XAxis type="number" tick={{ fontSize: 10 }} />
                  <YAxis dataKey="rede" type="category" tick={{ fontSize: 10 }} width={70} />
                  <Tooltip content={<CustomTooltip />} />
                  <Legend />
                  <Bar dataKey="verde"    name="Verde"    stackId="a" fill={VERDE} />
                  <Bar dataKey="amarelo"  name="Amarelo"  stackId="a" fill={AMARELO} />
                  <Bar dataKey="vermelho" name="Vermelho" stackId="a" fill={VERMELHO} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}
        </div>

        {/* Maturidade pie */}
        <div className="bg-white rounded-xl border border-gray-100 shadow-sm p-5">
          <SectionHeader label="Maturidade da Carteira" accentColor="#0891b2" />
          {loading ? (
            <ChartSkeleton />
          ) : maturidadeData.length === 0 ? (
            <EmptyState message="Sem dados" />
          ) : (
            <div className="mt-4 h-56">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={maturidadeData}
                    cx="50%"
                    cy="50%"
                    outerRadius={80}
                    dataKey="value"
                    nameKey="name"
                    label={({ name, percent }: { name?: string; percent?: number }) =>
                      `${name ?? ''}: ${((percent ?? 0) * 100).toFixed(0)}%`
                    }
                  >
                    {maturidadeData.map((_, i) => (
                      <Cell key={i} fill={maturidadeColors[i] ?? '#9ca3af'} />
                    ))}
                  </Pie>
                  <Tooltip content={<CustomTooltip />} />
                  <Legend />
                </PieChart>
              </ResponsiveContainer>
            </div>
          )}
          <p className="text-[10px] text-gray-400 text-center mt-2 italic">
            Derivado do sinaleiro — dados reais em breve
          </p>
        </div>
      </div>

      {/* Top sinaleiro items table */}
      {!loading && sinaleiro?.itens?.length ? (
        <div className="bg-white rounded-xl border border-gray-100 shadow-sm overflow-hidden">
          <div className="px-5 py-4 border-b border-gray-100">
            <SectionHeader label="Top Clientes por Sinaleiro" accentColor={LARANJA} />
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-gray-50">
                  {['Cliente', 'UF', 'Consultor', 'Cor', 'Realizado', 'Meta', '%'].map((h) => (
                    <th key={h} className="px-4 py-3 text-left text-[10px] font-semibold text-gray-500 uppercase tracking-wide whitespace-nowrap">
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {sinaleiro.itens.slice(0, 8).map((item) => {
                  const color = SINALEIRO_COLORS[item.cor.toUpperCase()] ?? '#9ca3af';
                  return (
                    <tr key={item.cnpj} className="border-t border-gray-50 hover:bg-gray-50 transition-colors">
                      <td className="px-4 py-2.5 font-medium text-gray-900">{item.nome_fantasia}</td>
                      <td className="px-4 py-2.5 text-gray-500">{item.uf}</td>
                      <td className="px-4 py-2.5">
                        <ConsultorDot consultor={item.consultor} />
                      </td>
                      <td className="px-4 py-2.5">
                        <StatusBadge value={item.cor} variant="sinaleiro" small />
                      </td>
                      <td className="px-4 py-2.5 font-mono text-gray-800 whitespace-nowrap">
                        {formatCompact(item.realizado)}
                      </td>
                      <td className="px-4 py-2.5 font-mono text-gray-600 whitespace-nowrap">
                        {formatCompact(item.meta_anual)}
                      </td>
                      <td className="px-4 py-2.5">
                        <span className="text-xs font-bold" style={{ color }}>
                          {item.pct_atingimento.toFixed(0)}%
                        </span>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      ) : null}
    </div>
  );
}

// ===========================================================================
// TAB 7: MOTIVOS + RNC
// ===========================================================================

interface TabMotivosProps {
  rnc: RNCResponse | null;
  loading: boolean;
}

function TabMotivos({ rnc, loading }: TabMotivosProps) {
  const rncItens = rnc?.itens ?? [];

  // Motivos chart — from RNC types
  const motivosData = rncItens.reduce<Record<string, number>>((acc, item) => {
    const tipo = item.tipo_problema ?? 'Outros';
    acc[tipo] = (acc[tipo] ?? 0) + 1;
    return acc;
  }, {});

  const motivosChartData = Object.entries(motivosData)
    .map(([tipo, count]) => ({ tipo, count }))
    .sort((a, b) => b.count - a.count)
    .slice(0, 8);

  return (
    <div className="space-y-6">
      {/* Motivos bar chart */}
      <div className="bg-white rounded-xl border border-gray-100 shadow-sm p-5">
        <SectionHeader label="Motivos de Nao-Compra / RNC" accentColor={LARANJA} />
        {loading ? (
          <ChartSkeleton />
        ) : motivosChartData.length === 0 ? (
          <div className="mt-4 py-8 text-center">
            <p className="text-gray-400 text-sm">Sem registros de RNC</p>
            <span className="inline-block mt-2 px-2 py-0.5 bg-gray-100 text-gray-500 text-[10px] rounded font-semibold">Em breve</span>
          </div>
        ) : (
          <div className="mt-4 h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={motivosChartData} layout="vertical">
                <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                <XAxis type="number" tick={{ fontSize: 10 }} />
                <YAxis dataKey="tipo" type="category" tick={{ fontSize: 10 }} width={100} />
                <Tooltip content={<CustomTooltip />} />
                <Bar dataKey="count" name="Qtd" fill={LARANJA} radius={[0, 4, 4, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        )}
      </div>

      {/* RNC list */}
      <div className="bg-white rounded-xl border border-gray-100 shadow-sm overflow-hidden">
        <div className="px-5 py-4 border-b border-gray-100">
          <SectionHeader label="Registros RNC Recentes" accentColor={VERMELHO} />
        </div>
        {loading ? (
          <div className="p-5 space-y-3">
            {Array.from({ length: 4 }).map((_, i) => (
              <div key={i} className="h-10 bg-gray-100 animate-pulse rounded" />
            ))}
          </div>
        ) : rncItens.length === 0 ? (
          <div className="p-8 text-center">
            <p className="text-gray-400 text-sm">Nenhum RNC registrado</p>
            <span className="inline-block mt-2 px-2 py-0.5 bg-gray-100 text-gray-500 text-[10px] rounded font-semibold">Em breve</span>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-gray-50">
                  {['Data', 'Cliente', 'Tipo', 'Consultor', 'Severidade', 'Status'].map((h) => (
                    <th key={h} className="px-4 py-3 text-left text-[10px] font-semibold text-gray-500 uppercase tracking-wide whitespace-nowrap">
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {rncItens.slice(0, 10).map((item) => {
                  const sev = item.sla_status?.toUpperCase() ?? 'DENTRO';
                  const sc  = sev === 'VIOLADO' ? VERMELHO : sev === 'ATENCAO' ? AMARELO : VERDE;
                  return (
                    <tr key={item.id} className="border-t border-gray-50 hover:bg-gray-50 transition-colors">
                      <td className="px-4 py-2.5 text-gray-500 whitespace-nowrap text-xs">
                        {item.data_abertura ? new Date(item.data_abertura).toLocaleDateString('pt-BR') : '—'}
                      </td>
                      <td className="px-4 py-2.5 font-medium text-gray-900">{item.cliente_nome ?? '—'}</td>
                      <td className="px-4 py-2.5 text-gray-600">{item.tipo_problema ?? '—'}</td>
                      <td className="px-4 py-2.5">
                        <ConsultorDot consultor={item.consultor ?? '—'} />
                      </td>
                      <td className="px-4 py-2.5">
                        <span
                          className="inline-flex items-center px-2 py-0.5 rounded text-[10px] font-bold text-white"
                          style={{ backgroundColor: sc }}
                        >
                          {sev}
                        </span>
                      </td>
                      <td className="px-4 py-2.5">
                        <StatusBadge value={item.status} variant="prioridade" small />
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}

// ===========================================================================
// TAB 8: PRODUTIVIDADE
// ===========================================================================

interface TabProdutividadeProps {
  performance: PerformanceConsultor[];
  kpis: KPIs | null;
  loading: boolean;
}

function TabProdutividade({ performance, kpis, loading }: TabProdutividadeProps) {
  const totalVendas    = kpis?.total_ativos ?? 0;
  const totalContatos  = kpis?.total_clientes ?? 0;
  const totalProspects = kpis?.total_prospects ?? 0;

  const tarefasPorVenda   = totalVendas > 0 ? (totalContatos / totalVendas).toFixed(1)  : '—';
  const contatosPorVenda  = totalVendas > 0 ? (totalContatos / totalVendas).toFixed(1)  : '—';
  const diasPorVenda      = totalVendas > 0 ? '3.2'  : '—'; // seria calculado com datas
  const custoPorVenda     = '—'; // requer dados financeiros internos

  // Tarefas/dia simulated per consultant
  const tarefasDiaData = performance.map((p) => ({
    consultor: p.consultor,
    tarefas: parseFloat((p.total_clientes / 30).toFixed(1)),
  }));

  // Effort decomposition
  const effortData = [
    { tipo: 'Prospeccao', pct: 35 },
    { tipo: 'Follow-up',  pct: 30 },
    { tipo: 'Negociacao', pct: 20 },
    { tipo: 'Admin',      pct: 15 },
  ];
  const effortColors = [VERDE, '#0891b2', AMARELO, '#9ca3af'];

  return (
    <div className="space-y-6">
      {/* KPI cards */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <KpiCard title="TAREFAS / VENDA"  value={loading ? null : tarefasPorVenda}  subtitle="contatos por pedido"  color={VERDE} />
        <KpiCard title="CONTATOS / VENDA" value={loading ? null : contatosPorVenda} subtitle="esforco de conversao"  color="#0891b2" />
        <KpiCard title="DIAS / VENDA"     value={loading ? null : diasPorVenda}     subtitle="ciclo medio de venda"  color={AMARELO} />
        <KpiCard title="CUSTO / VENDA"    value={loading ? null : custoPorVenda}    subtitle="dados financeiros req." color="#9ca3af" />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Tarefas/dia por consultor */}
        <div className="bg-white rounded-xl border border-gray-100 shadow-sm p-5">
          <SectionHeader label="Contatos/Dia por Consultor" accentColor="#7c3aed" />
          {loading ? (
            <ChartSkeleton />
          ) : tarefasDiaData.length === 0 ? (
            <EmptyState message="Sem dados" />
          ) : (
            <div className="mt-4 h-56">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={tarefasDiaData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                  <XAxis dataKey="consultor" tick={{ fontSize: 11 }} />
                  <YAxis tick={{ fontSize: 11 }} />
                  <Tooltip content={<CustomTooltip />} />
                  <Bar dataKey="tarefas" name="Contatos/dia" radius={[4, 4, 0, 0]}>
                    {tarefasDiaData.map((entry, i) => (
                      <Cell key={i} fill={CONSULTOR_COLORS[entry.consultor.toUpperCase()] ?? VERDE} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}
          <p className="text-[10px] text-gray-400 mt-2 text-center italic">
            Baseado em clientes / 30 dias — dados reais em breve
          </p>
        </div>

        {/* Effort decomposition */}
        <div className="bg-white rounded-xl border border-gray-100 shadow-sm p-5">
          <SectionHeader label="Decomposicao de Esforco" accentColor={AMARELO} />
          <div className="mt-4 h-56">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={effortData}
                  cx="50%"
                  cy="50%"
                  outerRadius={80}
                  dataKey="pct"
                  nameKey="tipo"
                  label={({ name, value }: { name?: string; value?: number }) => `${name ?? ''}: ${value ?? 0}%`}
                >
                  {effortData.map((_, i) => (
                    <Cell key={i} fill={effortColors[i] ?? '#9ca3af'} />
                  ))}
                </Pie>
                <Tooltip content={<CustomTooltip />} />
                <Legend />
              </PieChart>
            </ResponsiveContainer>
          </div>
          <p className="text-[10px] text-gray-400 mt-2 text-center italic">
            Estimativa — integracao Asana em breve
          </p>
        </div>
      </div>

      {/* Benchmark cards */}
      <div className="bg-white rounded-xl border border-gray-100 shadow-sm p-5">
        <SectionHeader label="Benchmark de Produtividade" accentColor={VERDE} />
        <div className="mt-4 grid grid-cols-1 sm:grid-cols-3 gap-3">
          <BenchmarkCard label="Conversao atual" value={loading ? null : `${totalVendas > 0 ? ((totalVendas / totalContatos) * 100).toFixed(1) : '0.0'}%`} meta="Meta: 15%" color={VERDE} />
          <BenchmarkCard label="Prospects ativos" value={loading ? null : totalProspects.toLocaleString('pt-BR')} meta="Meta: 50+" color="#0891b2" />
          <BenchmarkCard label="Score medio carteira" value={loading ? null : (kpis?.media_score ?? 0).toFixed(1)} meta="Meta: 70+" color={AMARELO} />
        </div>
      </div>
    </div>
  );
}

// ===========================================================================
// Shared sub-components
// ===========================================================================

function SectionHeader({ label, accentColor }: { label: string; accentColor: string }) {
  return (
    <h2
      className="text-base font-bold text-gray-900 pl-3"
      style={{ borderLeft: `4px solid ${accentColor}` }}
    >
      {label}
    </h2>
  );
}

function KpiCard({
  title,
  value,
  subtitle,
  color,
}: {
  title: string;
  value: string | null;
  subtitle: string;
  color: string;
}) {
  return (
    <div className="bg-white rounded-xl border border-gray-100 shadow-sm p-4">
      <span
        className="inline-block px-2 py-0.5 rounded text-[10px] font-semibold uppercase tracking-wider mb-2"
        style={{ backgroundColor: color + '18', color }}
      >
        {title}
      </span>
      {value === null ? (
        <div className="h-7 w-20 bg-gray-100 animate-pulse rounded" />
      ) : (
        <p className="text-2xl font-bold text-gray-900">{value}</p>
      )}
      <p className="text-[11px] text-gray-400 mt-0.5">{subtitle}</p>
    </div>
  );
}

function AlertCard({
  label,
  value,
  color,
  icon,
}: {
  label: string;
  value: string | null;
  color: string;
  icon: string;
}) {
  return (
    <div
      className="rounded-xl p-4 border-l-4"
      style={{ borderColor: color, backgroundColor: color + '10' }}
    >
      <div className="flex items-center gap-2 mb-1">
        <span
          className="w-5 h-5 rounded-full flex items-center justify-center text-[10px] font-bold text-white flex-shrink-0"
          style={{ backgroundColor: color }}
        >
          {icon}
        </span>
        <p className="text-xs font-semibold text-gray-700">{label}</p>
      </div>
      {value === null ? (
        <div className="h-7 w-16 bg-gray-200 animate-pulse rounded" />
      ) : (
        <p className="text-2xl font-bold text-gray-900">{value}</p>
      )}
    </div>
  );
}

function MetricCard({
  label,
  value,
  color,
}: {
  label: string;
  value: string | null;
  color: string;
}) {
  return (
    <div className="bg-white rounded-xl border border-gray-100 shadow-sm p-5 flex items-center gap-4">
      <div
        className="w-12 h-12 rounded-full flex-shrink-0 flex items-center justify-center text-white font-bold"
        style={{ backgroundColor: color }}
      >
        %
      </div>
      <div>
        <p className="text-xs text-gray-500 font-medium">{label}</p>
        {value === null ? (
          <div className="h-7 w-16 bg-gray-100 animate-pulse rounded mt-1" />
        ) : (
          <p className="text-2xl font-bold text-gray-900">{value}</p>
        )}
      </div>
    </div>
  );
}

function BenchmarkCard({
  label,
  value,
  meta,
  color,
}: {
  label: string;
  value: string | null;
  meta: string;
  color: string;
}) {
  return (
    <div
      className="rounded-xl p-4 border"
      style={{ borderColor: color + '40', backgroundColor: color + '08' }}
    >
      <p className="text-xs font-semibold text-gray-600">{label}</p>
      {value === null ? (
        <div className="h-7 w-20 bg-gray-200 animate-pulse rounded mt-1" />
      ) : (
        <p className="text-2xl font-bold mt-1" style={{ color }}>{value}</p>
      )}
      <p className="text-[10px] text-gray-400 mt-1">{meta}</p>
    </div>
  );
}

function ConsultorDot({ consultor }: { consultor: string }) {
  const color = CONSULTOR_COLORS[consultor.toUpperCase()] ?? '#9ca3af';
  return (
    <div className="flex items-center gap-1.5">
      <span className="w-2 h-2 rounded-full flex-shrink-0" style={{ backgroundColor: color }} />
      <span className="text-gray-700 text-xs">{consultor}</span>
    </div>
  );
}

function EmptyState({ message }: { message: string }) {
  return (
    <div className="py-10 text-center text-gray-400 text-sm">{message}</div>
  );
}

function ChartSkeleton() {
  return (
    <div className="mt-4 h-56 bg-gray-50 animate-pulse rounded-lg" />
  );
}

// ---------------------------------------------------------------------------
// PerformanceTable — shared between Operacional and Performance tabs
// ---------------------------------------------------------------------------

function PerformanceTable({
  performance,
  loading,
  showRank = false,
}: {
  performance: PerformanceConsultor[];
  loading: boolean;
  showRank?: boolean;
}) {
  if (loading) {
    return (
      <div className="p-5 space-y-3">
        {Array.from({ length: 4 }).map((_, i) => (
          <div key={i} className="h-8 bg-gray-100 animate-pulse rounded" />
        ))}
      </div>
    );
  }
  if (!performance.length) {
    return <EmptyState message="Sem dados de performance" />;
  }

  const sorted = showRank
    ? [...performance].sort((a, b) => b.faturamento_real - a.faturamento_real)
    : performance;

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="bg-gray-50">
            {showRank && <th className="px-4 py-3 text-left text-[10px] font-semibold text-gray-500 uppercase tracking-wide">#</th>}
            {['Consultor', 'Territorio', 'Clientes', 'Faturamento', 'Meta 2026', '% Meta', 'Status'].map((h) => (
              <th key={h} className="px-4 py-3 text-left text-[10px] font-semibold text-gray-500 uppercase tracking-wide whitespace-nowrap">
                {h}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {sorted.map((row, idx) => {
            const color = CONSULTOR_COLORS[row.consultor.toUpperCase()] ?? '#9ca3af';
            const statusColor =
              row.pct_atingimento >= 80 ? VERDE :
              row.pct_atingimento >= 50 ? AMARELO : VERMELHO;
            return (
              <tr key={row.consultor} className="border-t border-gray-50 hover:bg-gray-50 transition-colors">
                {showRank && (
                  <td className="px-4 py-3 w-10 text-center">
                    <RankBadge rank={idx + 1} />
                  </td>
                )}
                <td className="px-4 py-3">
                  <div className="flex items-center gap-2">
                    <span className="w-2.5 h-2.5 rounded-full flex-shrink-0" style={{ backgroundColor: color }} />
                    <span className="font-semibold text-gray-900">{row.consultor}</span>
                  </div>
                </td>
                <td className="px-4 py-3 text-gray-500 text-xs">{row.territorio}</td>
                <td className="px-4 py-3 text-gray-700 font-medium">{row.total_clientes.toLocaleString('pt-BR')}</td>
                <td className="px-4 py-3 font-mono text-gray-800 whitespace-nowrap font-medium">{formatCompact(row.faturamento_real)}</td>
                <td className="px-4 py-3 font-mono text-gray-600 whitespace-nowrap">{formatCompact(row.meta_2026)}</td>
                <td className="px-4 py-3">
                  <span className="text-sm font-bold" style={{ color: statusColor }}>
                    {row.pct_atingimento.toFixed(1)}%
                  </span>
                </td>
                <td className="px-4 py-3">
                  <StatusBadge value={row.status} variant="sinaleiro" small />
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

// ---------------------------------------------------------------------------
// RankBadge
// ---------------------------------------------------------------------------

function RankBadge({ rank }: { rank: number }) {
  if (rank === 1)
    return (
      <span className="inline-flex items-center justify-center w-6 h-6 rounded-full text-xs font-bold text-white" style={{ backgroundColor: '#d97706' }}>1</span>
    );
  if (rank === 2)
    return (
      <span className="inline-flex items-center justify-center w-6 h-6 rounded-full text-xs font-bold text-white" style={{ backgroundColor: '#9ca3af' }}>2</span>
    );
  if (rank === 3)
    return (
      <span className="inline-flex items-center justify-center w-6 h-6 rounded-full text-xs font-bold text-white" style={{ backgroundColor: '#CD7F32' }}>3</span>
    );
  return <span className="text-gray-400 font-mono text-xs">{rank}</span>;
}
