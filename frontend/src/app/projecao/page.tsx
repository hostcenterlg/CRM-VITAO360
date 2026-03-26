'use client';

import { useEffect, useState } from 'react';
import {
  fetchProjecao,
  fetchProjecaoDetalhada,
  Projecao,
  ProjecaoDetalhada,
  ProjecaoClienteItem,
  formatBRL,
  formatPercent,
} from '@/lib/api';

// ---------------------------------------------------------------------------
// Projecao page — Baseline, Meta 2026, Realizado, grafico mensal, tabela
// ---------------------------------------------------------------------------

const BASELINE_2025 = 2_091_000;
const META_2026 = 4_747_200;
const PROJECAO_2026 = 3_377_120;
const REALIZADO_Q1 = 415_904;

const MESES_LABELS = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez'];

const CONSULTORES = ['MANU', 'LARISSA', 'DAIANE', 'JULIO'];

export default function ProjecaoPage() {
  const [data, setData] = useState<Projecao | null>(null);
  const [detalhada, setDetalhada] = useState<ProjecaoDetalhada | null>(null);
  const [loading, setLoading] = useState(true);
  const [detalhadaLoading, setDetalhadaLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filtroConsultor, setFiltroConsultor] = useState<string>('');

  useEffect(() => {
    fetchProjecao()
      .then(setData)
      .catch((e: Error) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    setDetalhadaLoading(true);
    fetchProjecaoDetalhada({ consultor: filtroConsultor || undefined })
      .then(setDetalhada)
      .catch(() => setDetalhada(null))
      .finally(() => setDetalhadaLoading(false));
  }, [filtroConsultor]);

  const porConsultor = data?.por_consultor ?? [];

  const pctQ1 = ((REALIZADO_Q1 / META_2026) * 100);
  const pctQ1Color =
    pctQ1 >= 25 ? '#00B050' : pctQ1 >= 15 ? '#FFC000' : '#FF0000';

  const clientes = detalhada?.por_cliente ?? [];

  return (
    <div className="space-y-6">
      {/* Page heading */}
      <div>
        <h1 className="text-xl font-bold text-gray-900">Projecao Comercial 2026</h1>
        <p className="text-sm text-gray-500 mt-0.5">
          Metas vs realizado por consultor e periodo
        </p>
      </div>

      {error && (
        <div className="p-4 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700">
          Erro ao carregar projecao: {error}
        </div>
      )}

      {/* Destaque — 4 cards principais */}
      <section>
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          {/* Baseline 2025 */}
          <div className="bg-white rounded-lg border border-gray-200 p-4 flex flex-col gap-1 shadow-sm" style={{ borderLeftColor: '#2563eb', borderLeftWidth: '4px' }}>
            <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide">
              Baseline 2025
            </p>
            <p className="text-2xl font-bold text-gray-900 leading-tight">
              {formatBRL(BASELINE_2025)}
            </p>
            <p className="text-xs text-gray-400 mt-0.5">
              Auditoria forense — PAINEL CEO
            </p>
          </div>

          {/* Meta 2026 */}
          <div className="bg-white rounded-lg border border-gray-200 p-4 flex flex-col gap-1 shadow-sm" style={{ borderLeftColor: '#00B050', borderLeftWidth: '4px' }}>
            <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide">
              Meta 2026
            </p>
            <p className="text-2xl font-bold text-gray-900 leading-tight">
              {formatBRL(META_2026)}
            </p>
            <p className="text-xs text-gray-400 mt-0.5">
              +{formatPercent(((META_2026 - BASELINE_2025) / BASELINE_2025) * 100, 0)} vs Baseline 2025
            </p>
          </div>

          {/* Realizado Q1 */}
          <div
            className="bg-white rounded-lg border border-gray-200 p-4 flex flex-col gap-1 shadow-sm"
            style={{ borderLeftColor: pctQ1Color, borderLeftWidth: '4px' }}
          >
            <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide">
              Realizado 2026 YTD
            </p>
            <p className="text-2xl font-bold text-gray-900 leading-tight">
              {formatBRL(REALIZADO_Q1)}
            </p>
            <p className="text-xs mt-0.5" style={{ color: pctQ1Color }}>
              {formatPercent(pctQ1)} da meta anual
            </p>
          </div>

          {/* Projecao 2026 */}
          <div className="bg-white rounded-lg border border-gray-200 p-4 flex flex-col gap-1 shadow-sm" style={{ borderLeftColor: '#7c3aed', borderLeftWidth: '4px' }}>
            <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide">
              Projecao 2026
            </p>
            <p className="text-2xl font-bold text-gray-900 leading-tight">
              {formatBRL(PROJECAO_2026)}
            </p>
            <p className="text-xs text-gray-400 mt-0.5">
              +{formatPercent(((PROJECAO_2026 - BASELINE_2025) / BASELINE_2025) * 100, 0)} vs Baseline 2025
            </p>
          </div>
        </div>
      </section>

      {/* Grafico Realizado vs Meta por Mes */}
      <section className="bg-white rounded-lg border border-gray-200 p-5 shadow-sm">
        <h2 className="text-sm font-semibold text-gray-700 mb-4">
          Realizado vs Meta por Mes (2026)
        </h2>
        {detalhadaLoading ? (
          <div className="h-48 flex items-center justify-center">
            <div className="text-sm text-gray-400 animate-pulse">Carregando grafico...</div>
          </div>
        ) : detalhada?.por_mes?.length ? (
          <GroupedBarChart data={detalhada.por_mes} />
        ) : (
          <MesesBarChart />
        )}
      </section>

      {/* Performance por Consultor */}
      <section className="bg-white rounded-lg border border-gray-200 shadow-sm overflow-hidden">
        <div className="px-4 py-3 border-b border-gray-100">
          <h2 className="text-sm font-semibold text-gray-700">
            Desempenho por Consultor
          </h2>
        </div>

        {loading ? (
          <div className="p-4 space-y-3">
            {Array.from({ length: 4 }).map((_, i) => (
              <div key={i} className="h-5 bg-gray-100 animate-pulse rounded" />
            ))}
          </div>
        ) : porConsultor.length === 0 ? (
          <div className="py-10 text-center text-gray-400 text-sm">
            Sem dados por consultor disponíveis
          </div>
        ) : (
          <div className="overflow-x-auto scrollbar-thin">
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-gray-50 text-left">
                  {['Consultor', 'Faturamento', 'Meta', '% Alcancado', 'Status'].map((h) => (
                    <th
                      key={h}
                      className="px-4 py-2.5 text-[10px] font-semibold text-gray-500 uppercase tracking-wide whitespace-nowrap"
                    >
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {porConsultor.map((row) => {
                  const pct = row.pct_alcancado;
                  const color =
                    pct >= 80 ? '#00B050' : pct >= 50 ? '#FFC000' : '#FF0000';
                  const status =
                    pct >= 100
                      ? 'Meta atingida'
                      : pct >= 80
                      ? 'Proximo da meta'
                      : pct >= 50
                      ? 'Em andamento'
                      : 'Abaixo da meta';

                  return (
                    <tr key={row.consultor} className="border-t border-gray-50 hover:bg-gray-50 transition-colors">
                      <td className="px-4 py-3 font-semibold text-gray-900">
                        {row.consultor}
                      </td>
                      <td className="px-4 py-3 font-mono text-gray-800 text-xs">
                        {formatBRL(row.faturamento)}
                      </td>
                      <td className="px-4 py-3 font-mono text-gray-600 text-xs">
                        {formatBRL(row.meta)}
                      </td>
                      <td className="px-4 py-3">
                        <div className="flex items-center gap-2">
                          <div className="w-24 bg-gray-100 rounded-full h-2 overflow-hidden">
                            <div
                              className="h-full rounded-full transition-all duration-500"
                              style={{
                                width: `${Math.min(100, pct)}%`,
                                backgroundColor: color,
                              }}
                            />
                          </div>
                          <span
                            className="text-xs font-semibold w-12"
                            style={{ color }}
                          >
                            {formatPercent(pct)}
                          </span>
                        </div>
                      </td>
                      <td className="px-4 py-3">
                        <span
                          className="text-xs font-medium px-2 py-0.5 rounded"
                          style={{
                            backgroundColor: color + '20',
                            color,
                          }}
                        >
                          {status}
                        </span>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </section>

      {/* Tabela por Cliente */}
      <section className="bg-white rounded-lg border border-gray-200 shadow-sm overflow-hidden">
        <div className="px-4 py-3 border-b border-gray-100 flex items-center justify-between flex-wrap gap-3">
          <h2 className="text-sm font-semibold text-gray-700">
            Meta vs Realizado por Cliente
          </h2>

          {/* Filtro consultor */}
          <div className="flex items-center gap-2">
            <label className="text-xs text-gray-500 font-medium">Consultor:</label>
            <select
              value={filtroConsultor}
              onChange={(e) => setFiltroConsultor(e.target.value)}
              className="h-7 border border-gray-300 rounded px-2 text-xs text-gray-700 bg-white focus:outline-none focus:border-green-600"
            >
              <option value="">Todos</option>
              {CONSULTORES.map((c) => (
                <option key={c} value={c}>
                  {c}
                </option>
              ))}
            </select>
          </div>
        </div>

        {detalhadaLoading ? (
          <div className="p-4 space-y-3">
            {Array.from({ length: 6 }).map((_, i) => (
              <div key={i} className="h-4 bg-gray-100 animate-pulse rounded" />
            ))}
          </div>
        ) : clientes.length === 0 ? (
          <div className="py-10 text-center text-gray-400 text-sm">
            Sem dados de clientes disponíveis
          </div>
        ) : (
          <ClienteProjecaoTable itens={clientes} />
        )}
      </section>

      {/* Notas */}
      <div className="bg-blue-50 border border-blue-100 rounded-lg p-4 text-xs text-blue-700 space-y-1">
        <p>
          <strong>Baseline 2025:</strong> R$ 2.091.000 — auditoria forense 68 arquivos (PAINEL CEO DEFINITIVO, 2026-03-23).
        </p>
        <p>
          <strong>Anterior (supersedido):</strong> R$ 2.156.179 — diferenca de R$ 65K resolvida em CONFLITOS. Nao utilizar.
        </p>
        <p>
          <strong>Meta 2026:</strong> R$ 4.747.200 | <strong>Projecao 2026:</strong> R$ 3.377.120 (+69% vs baseline).
        </p>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// GroupedBarChart — Realizado vs Meta por mes (SVG)
// ---------------------------------------------------------------------------

interface MesData {
  mes: string;
  meta: number;
  realizado: number;
}

function GroupedBarChart({ data }: { data: MesData[] }) {
  const maxVal = Math.max(...data.flatMap((d) => [d.meta, d.realizado]), 1);
  const CHART_H = 160;
  const BAR_W = 14;
  const GAP = 4;
  const GROUP_W = BAR_W * 2 + GAP + 8;
  const CHART_W = data.length * GROUP_W + 40;

  return (
    <div className="overflow-x-auto scrollbar-thin">
      <svg
        width={CHART_W}
        height={CHART_H + 40}
        aria-label="Grafico realizado vs meta por mes"
        role="img"
      >
        {/* Y axis lines */}
        {[0, 0.25, 0.5, 0.75, 1].map((frac) => {
          const y = 10 + (1 - frac) * CHART_H;
          return (
            <g key={frac}>
              <line
                x1={30}
                y1={y}
                x2={CHART_W}
                y2={y}
                stroke="#F3F4F6"
                strokeWidth={1}
              />
              <text
                x={28}
                y={y + 3}
                textAnchor="end"
                fontSize="8"
                fill="#9CA3AF"
              >
                {(maxVal * frac / 1000).toFixed(0)}K
              </text>
            </g>
          );
        })}

        {/* Bars */}
        {data.map((d, i) => {
          const x = 32 + i * GROUP_W;
          const metaH = maxVal > 0 ? (d.meta / maxVal) * CHART_H : 0;
          const realH = maxVal > 0 ? (d.realizado / maxVal) * CHART_H : 0;
          const pct = d.meta > 0 ? (d.realizado / d.meta) * 100 : 0;
          const barColor =
            pct >= 80 ? '#00B050' : pct >= 50 ? '#FFC000' : '#FF4500';

          return (
            <g key={d.mes}>
              {/* Meta bar (background) */}
              <rect
                x={x}
                y={10 + CHART_H - metaH}
                width={BAR_W}
                height={metaH}
                fill="#E5E7EB"
                rx={2}
              />
              {/* Realizado bar */}
              <rect
                x={x + BAR_W + GAP}
                y={10 + CHART_H - realH}
                width={BAR_W}
                height={realH}
                fill={barColor}
                rx={2}
              />
              {/* Month label */}
              <text
                x={x + BAR_W}
                y={10 + CHART_H + 12}
                textAnchor="middle"
                fontSize="8"
                fill="#6B7280"
              >
                {d.mes.substring(0, 3)}
              </text>
              {/* Pct label */}
              {pct > 0 && (
                <text
                  x={x + BAR_W + GAP + BAR_W / 2}
                  y={10 + CHART_H - realH - 3}
                  textAnchor="middle"
                  fontSize="7"
                  fontWeight="600"
                  fill={barColor}
                >
                  {pct.toFixed(0)}%
                </text>
              )}
            </g>
          );
        })}

        {/* Legend */}
        <g>
          <rect x={CHART_W - 120} y={4} width={10} height={8} fill="#E5E7EB" rx={1} />
          <text x={CHART_W - 107} y={11} fontSize="8" fill="#6B7280">
            Meta
          </text>
          <rect x={CHART_W - 80} y={4} width={10} height={8} fill="#00B050" rx={1} />
          <text x={CHART_W - 67} y={11} fontSize="8" fill="#6B7280">
            Realizado
          </text>
        </g>
      </svg>
    </div>
  );
}

// Fallback chart quando nao ha dados mensais da API
function MesesBarChart() {
  const metasMensais = META_2026 / 12;
  const realizadoPorMes = [
    REALIZADO_Q1 * 0.33,
    REALIZADO_Q1 * 0.35,
    REALIZADO_Q1 * 0.32,
    0, 0, 0, 0, 0, 0, 0, 0, 0,
  ];

  const mockData = MESES_LABELS.map((mes, i) => ({
    mes,
    meta: metasMensais,
    realizado: realizadoPorMes[i] ?? 0,
  }));

  return <GroupedBarChart data={mockData} />;
}

// ---------------------------------------------------------------------------
// ClienteProjecaoTable
// ---------------------------------------------------------------------------

function ClienteProjecaoTable({ itens }: { itens: ProjecaoClienteItem[] }) {
  function formatCnpj(cnpj: string): string {
    const d = cnpj.replace(/\D/g, '').padStart(14, '0');
    if (d.length !== 14) return cnpj;
    return `${d.slice(0, 2)}.${d.slice(2, 5)}.${d.slice(5, 8)}/${d.slice(8, 12)}-${d.slice(12)}`;
  }

  return (
    <div className="overflow-x-auto scrollbar-thin">
      <table className="w-full text-sm" role="table">
        <thead>
          <tr className="bg-gray-50">
            {['CNPJ', 'Cliente', 'Consultor', 'Meta Anual', 'Realizado', '% Ating', 'Gap', 'Status Meta'].map(
              (h) => (
                <th
                  key={h}
                  scope="col"
                  className="px-3 py-2.5 text-left text-[10px] font-semibold text-gray-500 uppercase tracking-wide whitespace-nowrap"
                >
                  {h}
                </th>
              )
            )}
          </tr>
        </thead>
        <tbody>
          {itens.map((item) => {
            const pct = item.pct_atingimento;
            const pc = pct >= 80 ? '#00B050' : pct >= 50 ? '#FFC000' : '#FF0000';
            const isNegGap = item.gap < 0;

            return (
              <tr
                key={item.cnpj}
                className="border-t border-gray-50 hover:bg-gray-50 transition-colors"
              >
                <td className="px-3 py-2.5 font-mono text-[11px] text-gray-400 whitespace-nowrap">
                  {formatCnpj(item.cnpj)}
                </td>
                <td className="px-3 py-2.5 max-w-[180px]">
                  <p className="font-medium text-gray-900 truncate text-xs">
                    {item.nome_fantasia}
                  </p>
                </td>
                <td className="px-3 py-2.5 text-xs text-gray-700 whitespace-nowrap">
                  {item.consultor}
                </td>
                <td className="px-3 py-2.5 font-mono text-xs text-gray-700 whitespace-nowrap">
                  {formatBRL(item.meta_anual)}
                </td>
                <td className="px-3 py-2.5 font-mono text-xs text-gray-800 whitespace-nowrap font-medium">
                  {formatBRL(item.realizado)}
                </td>
                <td className="px-3 py-2.5 whitespace-nowrap">
                  <div className="flex items-center gap-1.5">
                    <div className="w-12 bg-gray-100 rounded-full h-1.5 overflow-hidden">
                      <div
                        className="h-full rounded-full transition-all duration-500"
                        style={{
                          width: `${Math.min(100, pct)}%`,
                          backgroundColor: pc,
                        }}
                      />
                    </div>
                    <span className="text-xs font-semibold" style={{ color: pc }}>
                      {formatPercent(pct)}
                    </span>
                  </div>
                </td>
                <td
                  className="px-3 py-2.5 font-mono text-xs whitespace-nowrap font-medium"
                  style={{ color: isNegGap ? '#DC2626' : '#00B050' }}
                >
                  {isNegGap
                    ? `(${formatBRL(Math.abs(item.gap))})`
                    : `+${formatBRL(item.gap)}`}
                </td>
                <td className="px-3 py-2.5 whitespace-nowrap">
                  <span
                    className="text-[10px] font-bold px-2 py-0.5 rounded uppercase"
                    style={{
                      backgroundColor: pc + '20',
                      color: pc,
                    }}
                  >
                    {item.status_meta || (pct >= 100 ? 'META ATINGIDA' : pct >= 50 ? 'EM ANDAMENTO' : 'CRITICO')}
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
