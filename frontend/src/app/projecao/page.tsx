'use client';

import { useEffect, useState } from 'react';
import {
  fetchProjecao,
  fetchProjecaoConsultorDetalhe,
  Projecao,
  ProjecaoConsultorDetalhe,
  formatBRL,
  formatPercent,
} from '@/lib/api';

// ---------------------------------------------------------------------------
// Projecao page — Baseline, Meta 2026, Realizado, grafico mensal, tabela
// ---------------------------------------------------------------------------

// Fallbacks usados apenas quando a API nao retorna os dados
const BASELINE_2025_FALLBACK = 2_091_000;
const META_2026_FALLBACK = 4_747_200;
const PROJECAO_2026_FALLBACK = 3_377_120;

const CONSULTORES = ['MANU', 'LARISSA', 'DAIANE', 'JULIO'];

export default function ProjecaoPage() {
  const [data, setData] = useState<Projecao | null>(null);
  const [detalhe, setDetalhe] = useState<ProjecaoConsultorDetalhe | null>(null);
  const [loading, setLoading] = useState(true);
  const [detalheLoading, setDetalheLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [filtroConsultor, setFiltroConsultor] = useState<string>('MANU');

  useEffect(() => {
    fetchProjecao()
      .then(setData)
      .catch((e: Error) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    setDetalheLoading(true);
    setDetalhe(null);
    fetchProjecaoConsultorDetalhe(filtroConsultor)
      .then(setDetalhe)
      .catch(() => setDetalhe(null))
      .finally(() => setDetalheLoading(false));
  }, [filtroConsultor]);

  const porConsultor = data?.por_consultor ?? [];

  // Dados do resumo da API (com fallback para constantes)
  const baseline2025 = data?.resumo.baseline_2025 ?? BASELINE_2025_FALLBACK;
  const projecao2026 = data?.resumo.projecao_2026 ?? PROJECAO_2026_FALLBACK;
  const meta2026 = META_2026_FALLBACK; // nao vem da API, manter fallback

  // Realizado YTD vem do resumo da API
  const realizadoYTD = data?.resumo.faturamento_realizado ?? 0;
  const pctQ1 = meta2026 > 0 ? (realizadoYTD / meta2026) * 100 : 0;
  const pctQ1Color =
    pctQ1 >= 25 ? '#00B050' : pctQ1 >= 15 ? '#FFC000' : '#FF0000';

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
        <div className="flex items-start gap-3 p-4 bg-red-50 border border-red-200 rounded-lg">
          <svg className="w-5 h-5 text-red-500 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
              d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
          </svg>
          <div className="flex-1">
            <p className="text-sm font-semibold text-red-800">Erro ao carregar projecao</p>
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

      {/* Destaque — 4 cards principais */}
      <section>
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          {/* Baseline 2025 */}
          <div
            className="bg-white rounded-lg border border-gray-200 p-4 flex flex-col gap-1 shadow-sm"
            style={{ borderLeftColor: '#2563eb', borderLeftWidth: '4px' }}
          >
            <div className="flex items-center justify-between gap-2">
              <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide">
                Baseline 2025
              </p>
              <span
                className="w-7 h-7 rounded flex items-center justify-center flex-shrink-0"
                style={{ backgroundColor: '#2563eb18', color: '#2563eb' }}
                aria-hidden="true"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                    d="M12 22V12M12 12C12 9.239 9.761 7 7 7H3v2h4a3 3 0 010 6H3m9-3h4a3 3 0 110 6H3m9 0v3M12 3v4" />
                </svg>
              </span>
            </div>
            <p className="text-2xl font-bold text-gray-900 leading-tight">
              {loading ? '—' : formatBRL(baseline2025)}
            </p>
            <p className="text-xs text-gray-400 mt-0.5">
              Auditoria forense — PAINEL CEO
            </p>
          </div>

          {/* Meta 2026 */}
          <div
            className="bg-white rounded-lg border border-gray-200 p-4 flex flex-col gap-1 shadow-sm"
            style={{ borderLeftColor: '#00B050', borderLeftWidth: '4px' }}
          >
            <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide">
              Meta 2026
            </p>
            <p className="text-2xl font-bold text-gray-900 leading-tight">
              {formatBRL(meta2026)}
            </p>
            <p className="text-xs text-gray-400 mt-0.5">
              +{loading ? '—' : formatPercent(baseline2025 > 0 ? ((meta2026 - baseline2025) / baseline2025) * 100 : 0, 0)} vs Baseline
            </p>
          </div>

          {/* Realizado YTD */}
          <div
            className="bg-white rounded-lg border border-gray-200 p-4 flex flex-col gap-1 shadow-sm"
            style={{ borderLeftColor: pctQ1Color, borderLeftWidth: '4px' }}
          >
            <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide">
              Realizado 2026 YTD
            </p>
            <p className="text-2xl font-bold text-gray-900 leading-tight">
              {loading ? '—' : formatBRL(realizadoYTD)}
            </p>
            <p className="text-xs mt-0.5" style={{ color: pctQ1Color }}>
              {loading ? '—' : formatPercent(pctQ1)} da meta anual
            </p>
          </div>

          {/* Projecao 2026 */}
          <div
            className="bg-white rounded-lg border border-gray-200 p-4 flex flex-col gap-1 shadow-sm"
            style={{ borderLeftColor: '#7c3aed', borderLeftWidth: '4px' }}
          >
            <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide">
              Projecao 2026
            </p>
            <p className="text-2xl font-bold text-gray-900 leading-tight">
              {loading ? '—' : formatBRL(projecao2026)}
            </p>
            <p className="text-xs text-gray-400 mt-0.5">
              {loading ? '—' : `+${formatPercent(baseline2025 > 0 ? ((projecao2026 - baseline2025) / baseline2025) * 100 : 0, 0)} vs Baseline`}
            </p>
          </div>
        </div>
      </section>

      {/* Grafico Realizado vs Meta por Mes — por consultor */}
      <section className="bg-white rounded-lg border border-gray-200 p-5 shadow-sm">
        <div className="flex items-center justify-between flex-wrap gap-3 mb-4">
          <h2 className="text-sm font-semibold text-gray-700">
            Evolucao Mensal por Consultor (2026)
          </h2>
          <div className="flex items-center gap-2">
            <label className="text-xs text-gray-500 font-medium">Consultor:</label>
            <select
              value={filtroConsultor}
              onChange={(e) => setFiltroConsultor(e.target.value)}
              className="h-7 border border-gray-300 rounded px-2 text-xs text-gray-700 bg-white focus:outline-none focus:border-green-600"
            >
              {CONSULTORES.map((c) => (
                <option key={c} value={c}>
                  {c}
                </option>
              ))}
            </select>
          </div>
        </div>

        {detalheLoading ? (
          <div className="h-64 flex items-end gap-1.5 px-2 pb-8">
            {Array.from({ length: 12 }).map((_, i) => (
              <div key={i} className="flex-1 flex gap-0.5 items-end">
                <div
                  className="flex-1 bg-gray-100 animate-pulse rounded-t"
                  style={{ height: `${20 + (i % 5) * 15}%`, minHeight: 8 }}
                />
                <div
                  className="flex-1 bg-gray-200 animate-pulse rounded-t"
                  style={{ height: `${15 + (i % 4) * 12}%`, minHeight: 6, animationDelay: `${i * 60}ms` }}
                />
              </div>
            ))}
          </div>
        ) : detalhe?.mensal?.length ? (
          <GroupedBarChart data={detalhe.mensal} />
        ) : (
          <div className="h-64 flex items-center justify-center text-sm text-gray-400">
            <div className="text-center">
              <svg className="w-10 h-10 mx-auto mb-3 text-gray-200" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
                  d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
              </svg>
              Sem dados mensais para {filtroConsultor}
            </div>
          </div>
        )}

        {detalhe && (
          <div className="mt-3 pt-3 border-t border-gray-100 flex flex-wrap gap-6 text-xs text-gray-600">
            <span>
              <span className="font-semibold">Realizado:</span>{' '}
              {formatBRL(detalhe.faturamento_total)}
            </span>
            <span>
              <span className="font-semibold">Meta:</span>{' '}
              {formatBRL(detalhe.meta_total)}
            </span>
            <span style={{ color: detalhe.pct_alcancado >= 80 ? '#00B050' : detalhe.pct_alcancado >= 50 ? '#FFC000' : '#FF0000' }}>
              <span className="font-semibold">% Atingido:</span>{' '}
              {formatPercent(detalhe.pct_alcancado)}
            </span>
          </div>
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
                  {['Consultor', 'Faturamento', 'Meta', 'Pedidos', '% Alcancado', 'Status'].map((h) => (
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
                      <td className="px-4 py-3 text-xs text-gray-600 text-center">
                        {row.total_vendas.toLocaleString('pt-BR')}
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
  mes_referencia: string;
  faturamento: number;
  meta: number;
}

function GroupedBarChart({ data }: { data: MesData[] }) {
  const maxVal = Math.max(...data.flatMap((d) => [d.meta, d.faturamento]), 1);
  const CHART_H = 220;
  const BAR_W = 16;
  const GAP = 5;
  const GROUP_W = BAR_W * 2 + GAP + 10;
  const CHART_W = data.length * GROUP_W + 50;

  const MESES_LABELS = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez'];

  return (
    <div className="overflow-x-auto scrollbar-thin">
      <svg
        width={CHART_W}
        height={CHART_H + 50}
        aria-label="Grafico realizado vs meta por mes"
        role="img"
      >
        {/* Y axis lines */}
        {[0, 0.25, 0.5, 0.75, 1].map((frac) => {
          const y = 14 + (1 - frac) * CHART_H;
          const labelVal = maxVal * frac;
          const labelStr = labelVal >= 1000
            ? `${(labelVal / 1000).toFixed(labelVal >= 100000 ? 0 : 1)}K`
            : labelVal.toFixed(0);
          return (
            <g key={frac}>
              <line
                x1={36}
                y1={y}
                x2={CHART_W}
                y2={y}
                stroke="#F3F4F6"
                strokeWidth={1}
              />
              <text
                x={34}
                y={y + 3}
                textAnchor="end"
                fontSize="9"
                fill="#9CA3AF"
              >
                {labelStr}
              </text>
            </g>
          );
        })}

        {/* Bars */}
        {data.map((d, i) => {
          const x = 38 + i * GROUP_W;
          const metaH = maxVal > 0 ? (d.meta / maxVal) * CHART_H : 0;
          const realH = maxVal > 0 ? (d.faturamento / maxVal) * CHART_H : 0;
          const pct = d.meta > 0 ? (d.faturamento / d.meta) * 100 : 0;
          const barColor =
            pct >= 80 ? '#00B050' : pct >= 50 ? '#FFC000' : '#FF4500';

          const mesNum = parseInt(d.mes_referencia.split('-')[1] ?? '1', 10) - 1;
          const mesLabel = MESES_LABELS[mesNum] ?? d.mes_referencia;

          return (
            <g key={d.mes_referencia}>
              {/* Meta bar (background) */}
              <rect
                x={x}
                y={14 + CHART_H - metaH}
                width={BAR_W}
                height={metaH}
                fill="#E5E7EB"
                rx={3}
              />
              {/* Realizado bar */}
              <rect
                x={x + BAR_W + GAP}
                y={14 + CHART_H - realH}
                width={BAR_W}
                height={realH}
                fill={barColor}
                rx={3}
              />
              {/* Month label */}
              <text
                x={x + BAR_W + GAP / 2}
                y={14 + CHART_H + 14}
                textAnchor="middle"
                fontSize="9"
                fontWeight="500"
                fill="#6B7280"
              >
                {mesLabel}
              </text>
              {/* Pct label above realizado bar */}
              {pct > 0 && realH > 12 && (
                <text
                  x={x + BAR_W + GAP + BAR_W / 2}
                  y={14 + CHART_H - realH - 4}
                  textAnchor="middle"
                  fontSize="8"
                  fontWeight="700"
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
          <rect x={CHART_W - 130} y={4} width={12} height={8} fill="#E5E7EB" rx={2} />
          <text x={CHART_W - 115} y={12} fontSize="9" fill="#6B7280">
            Meta
          </text>
          <rect x={CHART_W - 85} y={4} width={12} height={8} fill="#00B050" rx={2} />
          <text x={CHART_W - 70} y={12} fontSize="9" fill="#6B7280">
            Realizado
          </text>
        </g>
      </svg>
    </div>
  );
}
