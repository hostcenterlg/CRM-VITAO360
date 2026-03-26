'use client';

import { useEffect, useState } from 'react';
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
import KpiCard from '@/components/KpiCard';
import StatusBadge from '@/components/StatusBadge';

// ---------------------------------------------------------------------------
// Dashboard page — KPIs, sinaleiro donut, performance, distribuicao, top 10
// ---------------------------------------------------------------------------

// Color map for situacao distribution bars
const situacaoColors: Record<string, string> = {
  ATIVO: '#00B050',
  'INAT.REC': '#FFC000',
  'INAT.ANT': '#FF0000',
  INATIVO: '#FF0000',
  PROSPECT: '#808080',
};

// Color map for sinaleiro — LARANJA adicionado conforme spec
const sinaleiroColors: Record<string, string> = {
  VERDE: '#00B050',
  AMARELO: '#FFC000',
  LARANJA: '#FF8C00',
  VERMELHO: '#FF0000',
  ROXO: '#7030A0',
};

// Prioridade bar colors P0-P7 conforme spec
const prioridadeBarColors: Record<string, string> = {
  P0: '#FF0000',
  P1: '#FF4500',
  P2: '#FF8C00',
  P3: '#FFC000',
  P4: '#00B050',
  P5: '#2563eb',
  P6: '#9ca3af',
  P7: '#d1d5db',
};

// Performance status config
const performanceStatusConfig: Record<string, { bg: string; text: string; label: string }> = {
  BOM: { bg: '#00B050', text: '#fff', label: 'BOM' },
  ALERTA: { bg: '#FFC000', text: '#1a1a1a', label: 'ALERTA' },
  CRITICO: { bg: '#FF0000', text: '#fff', label: 'CRITICO' },
};

export default function DashboardPage() {
  const [kpis, setKpis] = useState<KPIs | null>(null);
  const [distribuicao, setDistribuicao] = useState<Distribuicao | null>(null);
  const [top10, setTop10] = useState<Top10Cliente[]>([]);
  const [performance, setPerformance] = useState<PerformanceConsultor[]>([]);
  const [loading, setLoading] = useState(true);
  const [perfLoading, setPerfLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setLoading(true);
    Promise.all([fetchKPIs(), fetchDistribuicao(), fetchTop10()])
      .then(([k, d, t]) => {
        setKpis(k);
        setDistribuicao(d);
        setTop10(t);
      })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    setPerfLoading(true);
    fetchPerformance()
      .then(setPerformance)
      .catch(() => {
        // Performance endpoint optional — silently degrade
        setPerformance([]);
      })
      .finally(() => setPerfLoading(false));
  }, []);

  return (
    <div className="space-y-6">
      {/* Page heading */}
      <div className="pb-3 sm:pb-4 border-b border-gray-200">
        <h1 className="text-xl sm:text-2xl font-bold text-gray-900">Dashboard CEO</h1>
        <p className="text-sm text-gray-500 mt-1">
          Visao geral da carteira comercial VITAO360
        </p>
      </div>

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
            onClick={() => window.location.reload()}
            className="flex-shrink-0 px-3 py-1.5 text-xs font-semibold text-red-700 border border-red-300 rounded-lg hover:bg-red-100 transition-colors"
          >
            Tentar novamente
          </button>
        </div>
      )}

      {/* KPI Cards */}
      <section>
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          <KpiCard
            title="Total de Clientes"
            value={kpis?.total_clientes.toLocaleString('pt-BR') ?? '—'}
            subtitle={`${kpis?.total_prospects ?? 0} prospects`}
            accentColor="#2563eb"
            loading={loading}
            icon={
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                  d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0z" />
              </svg>
            }
          />
          <KpiCard
            title="Clientes Ativos"
            value={kpis?.total_ativos.toLocaleString('pt-BR') ?? '—'}
            subtitle={`${kpis?.total_inativos ?? 0} inativos`}
            accentColor="#00B050"
            loading={loading}
            icon={
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                  d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            }
          />
          <KpiCard
            title="Faturamento Total"
            value={kpis ? formatFaturamentoCEO(kpis.faturamento_total) : '—'}
            subtitle="Baseline 2025"
            accentColor="#7c3aed"
            loading={loading}
            icon={
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                  d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            }
          />
          <KpiCard
            title="Score Medio"
            value={kpis ? kpis.media_score.toFixed(1) : '—'}
            subtitle={`${kpis?.clientes_criticos ?? 0} criticos / ${kpis?.clientes_alerta ?? 0} em alerta`}
            accentColor="#dc2626"
            loading={loading}
            icon={
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                  d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
              </svg>
            }
          />
        </div>
      </section>

      {/* Separador */}
      <div className="border-t border-gray-200" />

      {/* Bloco 2: Donut Sinaleiro + Performance por Consultor */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Donut Sinaleiro */}
        <section className="bg-white rounded-lg border border-gray-200 p-4 shadow-sm">
          <h2 className="text-sm font-semibold text-gray-700 mb-4">
            Sinaleiro de Carteira
          </h2>
          {loading ? (
            <SkeletonDonut />
          ) : distribuicao?.por_sinaleiro.length ? (
            <DonutSinaleiro
              items={distribuicao.por_sinaleiro}
              colorMap={sinaleiroColors}
            />
          ) : (
            <EmptyState />
          )}
        </section>

        {/* Performance por Consultor */}
        <section className="bg-white rounded-lg border border-gray-200 shadow-sm overflow-hidden">
          <div className="px-4 py-3 border-b border-gray-100">
            <h2 className="text-sm font-semibold text-gray-700">
              Performance por Consultor
            </h2>
          </div>
          {perfLoading ? (
            <div className="p-4 space-y-3">
              {Array.from({ length: 4 }).map((_, i) => (
                <div key={i} className="h-5 bg-gray-100 animate-pulse rounded" />
              ))}
            </div>
          ) : performance.length === 0 ? (
            <div className="py-8 text-center text-gray-400 text-sm">
              Sem dados de performance disponíveis
            </div>
          ) : (
            <PerformanceTable rows={performance} />
          )}
        </section>
      </div>

      {/* Separador */}
      <div className="border-t border-gray-200" />

      {/* Distribution charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Situacao distribution */}
        <section className="bg-white rounded-lg border border-gray-200 p-4 shadow-sm">
          <h2 className="text-sm font-semibold text-gray-700 mb-4">
            Distribuicao por Situacao
          </h2>
          {loading ? (
            <SkeletonBars />
          ) : distribuicao?.por_situacao.length ? (
            <BarChart
              items={distribuicao.por_situacao}
              colorMap={situacaoColors}
            />
          ) : (
            <EmptyState />
          )}
        </section>

        {/* Prioridade distribution */}
        <section className="bg-white rounded-lg border border-gray-200 p-4 shadow-sm">
          <h2 className="text-sm font-semibold text-gray-700 mb-4">
            Distribuicao por Prioridade
          </h2>
          {loading ? (
            <SkeletonBars />
          ) : distribuicao?.por_prioridade.length ? (
            <PrioridadeChart items={distribuicao.por_prioridade} />
          ) : (
            <EmptyState />
          )}
        </section>

        {/* Consultor distribution */}
        <section className="bg-white rounded-lg border border-gray-200 p-4 shadow-sm">
          <h2 className="text-sm font-semibold text-gray-700 mb-4">
            Distribuicao por Consultor
          </h2>
          {loading ? (
            <SkeletonBars />
          ) : distribuicao?.por_consultor.length ? (
            <BarChart
              items={distribuicao.por_consultor}
              colorMap={{}}
              defaultColor="#2563eb"
            />
          ) : (
            <EmptyState />
          )}
        </section>

        {/* Placeholder slot for future chart */}
        <section className="bg-white rounded-lg border border-gray-200 p-4 shadow-sm">
          <h2 className="text-sm font-semibold text-gray-700 mb-4">
            Resumo de Sinaleiro por Consultor
          </h2>
          {loading ? (
            <SkeletonBars />
          ) : distribuicao?.por_sinaleiro.length ? (
            <BarChart
              items={distribuicao.por_sinaleiro}
              colorMap={sinaleiroColors}
            />
          ) : (
            <EmptyState />
          )}
        </section>
      </div>

      {/* Separador */}
      <div className="border-t border-gray-200" />

      {/* Top 10 table */}
      <section className="bg-white rounded-lg border border-gray-200 shadow-sm">
        <div className="px-4 py-3 border-b border-gray-100">
          <h2 className="text-sm font-semibold text-gray-700">
            Top 10 Clientes por Faturamento
          </h2>
        </div>
        <div className="overflow-x-auto scrollbar-thin">
          {loading ? (
            <div className="p-4 space-y-3">
              {Array.from({ length: 6 }).map((_, i) => (
                <div key={i} className="h-4 bg-gray-100 animate-pulse rounded" />
              ))}
            </div>
          ) : top10.length === 0 ? (
            <EmptyState />
          ) : (
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-gray-50">
                  {['#', 'Cliente', 'Consultor', 'Faturamento', 'Score', 'Prioridade', 'Sinaleiro'].map((h) => (
                    <th
                      key={h}
                      className="px-4 py-2.5 text-left text-[11px] font-semibold text-gray-500 uppercase tracking-wide whitespace-nowrap"
                    >
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {top10.map((c, idx) => (
                  <tr key={c.cnpj} className="border-t border-gray-50 hover:bg-gray-50 transition-colors">
                    <td className="px-4 py-2.5 text-gray-400 font-mono text-xs w-8">{idx + 1}</td>
                    <td className="px-4 py-2.5">
                      <p className="font-medium text-gray-900">{c.nome_fantasia}</p>
                      <p className="text-[11px] text-gray-400 font-mono">{formatCnpj(c.cnpj)}</p>
                    </td>
                    <td className="px-4 py-2.5 text-gray-700 whitespace-nowrap">{c.consultor}</td>
                    <td className="px-4 py-2.5 font-mono text-gray-800 whitespace-nowrap font-medium">
                      {formatBRL(c.faturamento_total)}
                    </td>
                    <td className="px-4 py-2.5 text-gray-700">{c.score.toFixed(1)}</td>
                    <td className="px-4 py-2.5">
                      <StatusBadge value={c.prioridade} variant="prioridade" />
                    </td>
                    <td className="px-4 py-2.5">
                      <StatusBadge value={c.sinaleiro} variant="sinaleiro" />
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
// DonutSinaleiro — SVG donut com legenda lateral
// ---------------------------------------------------------------------------

interface DonutItem {
  label: string;
  count: number;
  pct: number;
}

interface DonutSinaleiroProps {
  items: DonutItem[];
  colorMap: Record<string, string>;
}

function DonutSinaleiro({ items, colorMap }: DonutSinaleiroProps) {
  const SIZE = 120;
  const RADIUS = 45;
  const STROKE = 20;
  const CX = SIZE / 2;
  const CY = SIZE / 2;
  const CIRCUMFERENCE = 2 * Math.PI * RADIUS;

  // Sort by order: VERDE, AMARELO, LARANJA, VERMELHO, ROXO, others
  const ORDER = ['VERDE', 'AMARELO', 'LARANJA', 'VERMELHO', 'ROXO'];
  const sorted = [...items].sort((a, b) => {
    const ai = ORDER.indexOf(a.label.toUpperCase());
    const bi = ORDER.indexOf(b.label.toUpperCase());
    if (ai === -1 && bi === -1) return b.pct - a.pct;
    if (ai === -1) return 1;
    if (bi === -1) return -1;
    return ai - bi;
  });

  // Build segments
  let cumulative = 0;
  const segments = sorted.map((item) => {
    const color = colorMap[item.label.toUpperCase()] ?? '#9ca3af';
    const dashLen = (item.pct / 100) * CIRCUMFERENCE;
    const gapLen = CIRCUMFERENCE - dashLen;
    const offset = CIRCUMFERENCE - (cumulative / 100) * CIRCUMFERENCE;
    cumulative += item.pct;
    return { ...item, color, dashLen, gapLen, offset };
  });

  const total = items.reduce((s, i) => s + i.count, 0);

  return (
    <div className="flex items-center gap-6">
      {/* Donut SVG */}
      <div className="flex-shrink-0">
        <svg
          width={SIZE}
          height={SIZE}
          viewBox={`0 0 ${SIZE} ${SIZE}`}
          aria-label="Grafico rosca sinaleiro"
          role="img"
        >
          {/* Track */}
          <circle
            cx={CX}
            cy={CY}
            r={RADIUS}
            fill="none"
            stroke="#E5E7EB"
            strokeWidth={STROKE}
          />
          {/* Segments */}
          {segments.map((seg) => (
            <circle
              key={seg.label}
              cx={CX}
              cy={CY}
              r={RADIUS}
              fill="none"
              stroke={seg.color}
              strokeWidth={STROKE}
              strokeDasharray={`${seg.dashLen} ${seg.gapLen}`}
              strokeDashoffset={seg.offset}
              style={{ transition: 'stroke-dashoffset 800ms ease-out' }}
              transform={`rotate(-90 ${CX} ${CY})`}
            />
          ))}
          {/* Center text */}
          <text
            x={CX}
            y={CY - 6}
            textAnchor="middle"
            dominantBaseline="middle"
            fontSize="14"
            fontWeight="700"
            fill="#111827"
          >
            {total.toLocaleString('pt-BR')}
          </text>
          <text
            x={CX}
            y={CY + 10}
            textAnchor="middle"
            dominantBaseline="middle"
            fontSize="9"
            fill="#6B7280"
          >
            clientes
          </text>
        </svg>
      </div>

      {/* Legend */}
      <div className="flex-1 space-y-2">
        {segments.map((seg) => (
          <div key={seg.label} className="flex items-center justify-between gap-2">
            <div className="flex items-center gap-2 min-w-0">
              <span
                className="flex-shrink-0 w-2.5 h-2.5 rounded-full"
                style={{ backgroundColor: seg.color }}
                aria-hidden="true"
              />
              <span className="text-xs font-medium text-gray-700 uppercase">
                {seg.label}
              </span>
            </div>
            <div className="text-right flex-shrink-0">
              <span className="text-xs font-semibold text-gray-800">
                {seg.count.toLocaleString('pt-BR')}
              </span>
              <span className="text-xs text-gray-400 ml-1.5">
                {formatPercent(seg.pct)}
              </span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// PerformanceTable
// ---------------------------------------------------------------------------

function PerformanceTable({ rows }: { rows: PerformanceConsultor[] }) {
  return (
    <div className="overflow-x-auto scrollbar-thin">
      <table className="w-full text-sm">
        <thead>
          <tr className="bg-gray-50">
            {['Consultor', 'Territorio', 'Clientes', 'Fat Real', 'Meta 2026', '% Ating', 'Status'].map((h) => (
              <th
                key={h}
                className="px-3 py-2.5 text-left text-[10px] font-semibold text-gray-500 uppercase tracking-wide whitespace-nowrap"
              >
                {h}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => {
            const cfg = performanceStatusConfig[row.status] ?? performanceStatusConfig.ALERTA;
            const pctColor =
              row.pct_atingimento >= 70
                ? '#00B050'
                : row.pct_atingimento >= 40
                ? '#FFC000'
                : '#FF0000';
            const isCritico = row.status === 'CRITICO';

            return (
              <tr
                key={row.consultor}
                className="border-t border-gray-50 hover:bg-gray-50 transition-colors"
                style={isCritico ? { backgroundColor: '#FEF2F2' } : undefined}
              >
                <td className="px-3 py-2.5 font-semibold text-gray-900 whitespace-nowrap">
                  {row.consultor}
                </td>
                <td className="px-3 py-2.5 text-gray-500 text-xs whitespace-nowrap">
                  {row.territorio || '—'}
                </td>
                <td className="px-3 py-2.5 text-gray-700 text-center">
                  {row.total_clientes.toLocaleString('pt-BR')}
                </td>
                <td className="px-3 py-2.5 font-mono text-gray-800 whitespace-nowrap text-xs">
                  {formatBRL(row.faturamento_real)}
                </td>
                <td className="px-3 py-2.5 font-mono text-gray-600 whitespace-nowrap text-xs">
                  {formatBRL(row.meta_2026)}
                </td>
                <td className="px-3 py-2.5">
                  <div className="flex items-center gap-1.5">
                    <div className="w-16 bg-gray-100 rounded-full h-1.5 overflow-hidden">
                      <div
                        className="h-full rounded-full transition-all duration-500"
                        style={{
                          width: `${Math.min(100, row.pct_atingimento)}%`,
                          backgroundColor: pctColor,
                        }}
                      />
                    </div>
                    <span
                      className="text-xs font-semibold"
                      style={{ color: pctColor }}
                    >
                      {formatPercent(row.pct_atingimento)}
                    </span>
                  </div>
                </td>
                <td className="px-3 py-2.5">
                  <span
                    className="inline-flex items-center px-2 py-0.5 rounded text-[10px] font-bold uppercase"
                    style={{ backgroundColor: cfg.bg, color: cfg.text }}
                  >
                    {cfg.label}
                  </span>
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
// BarChart
// ---------------------------------------------------------------------------

interface BarChartProps {
  items: { label: string; count: number; pct: number }[];
  colorMap: Record<string, string>;
  defaultColor?: string;
}

function BarChart({ items, colorMap, defaultColor = '#6b7280' }: BarChartProps) {
  const maxPct = Math.max(...items.map((i) => i.pct), 1);

  return (
    <div className="space-y-2.5">
      {items.map((item) => {
        const color = colorMap[item.label.toUpperCase()] ?? defaultColor;
        const barWidth = (item.pct / maxPct) * 100;

        return (
          <div key={item.label} className="flex items-center gap-2 sm:gap-3">
            <span className="w-16 sm:w-20 text-xs text-gray-600 text-right flex-shrink-0 font-medium truncate">
              {item.label}
            </span>
            <div className="flex-1 bg-gray-100 rounded-full h-3 sm:h-4 overflow-hidden">
              <div
                className="h-full rounded-full transition-all duration-500"
                style={{ width: `${barWidth}%`, backgroundColor: color }}
              />
            </div>
            <span className="w-16 sm:w-20 text-xs text-gray-500 flex-shrink-0 text-right">
              <span className="hidden sm:inline">{item.count.toLocaleString('pt-BR')} ({formatPercent(item.pct)})</span>
              <span className="sm:hidden">{formatPercent(item.pct)}</span>
            </span>
          </div>
        );
      })}
    </div>
  );
}

function PrioridadeChart({ items }: { items: { label: string; count: number; pct: number }[] }) {
  return (
    <BarChart
      items={items}
      colorMap={prioridadeBarColors}
      defaultColor="#9ca3af"
    />
  );
}

// ---------------------------------------------------------------------------
// Skeleton / Empty states
// ---------------------------------------------------------------------------

function SkeletonBars() {
  return (
    <div className="space-y-3">
      {Array.from({ length: 4 }).map((_, i) => (
        <div key={i} className="flex items-center gap-3">
          <div className="w-20 h-3 bg-gray-100 animate-pulse rounded" />
          <div className="flex-1 h-4 bg-gray-100 animate-pulse rounded-full" style={{ maxWidth: `${40 + i * 15}%` }} />
          <div className="w-12 h-3 bg-gray-100 animate-pulse rounded" />
        </div>
      ))}
    </div>
  );
}

function SkeletonDonut() {
  return (
    <div className="flex items-center gap-6">
      <div className="w-[120px] h-[120px] rounded-full bg-gray-100 animate-pulse flex-shrink-0" />
      <div className="flex-1 space-y-3">
        {Array.from({ length: 4 }).map((_, i) => (
          <div key={i} className="flex items-center gap-2">
            <div className="w-2.5 h-2.5 rounded-full bg-gray-200 animate-pulse" />
            <div className="h-3 bg-gray-100 animate-pulse rounded" style={{ width: `${60 + i * 10}%` }} />
          </div>
        ))}
      </div>
    </div>
  );
}

function EmptyState() {
  return (
    <div className="py-8 text-center text-gray-400 text-sm">
      Sem dados disponíveis
    </div>
  );
}

// Formata faturamento para CEO card (sem centavos, com prefixo R$)
function formatFaturamentoCEO(value: number): string {
  const rounded = Math.round(value);
  return 'R$ ' + rounded.toLocaleString('pt-BR');
}

function formatCnpj(cnpj: string): string {
  const d = cnpj.replace(/\D/g, '').padStart(14, '0');
  if (d.length !== 14) return cnpj;
  return `${d.slice(0, 2)}.${d.slice(2, 5)}.${d.slice(5, 8)}/${d.slice(8, 12)}-${d.slice(12)}`;
}
