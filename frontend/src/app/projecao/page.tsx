'use client';

import { useEffect, useState } from 'react';
import { fetchProjecao, Projecao, formatBRL, formatPercent } from '@/lib/api';
import KpiCard from '@/components/KpiCard';

// ---------------------------------------------------------------------------
// Projecao page — Q1 performance vs meta, baseline vs projecao 2026
// ---------------------------------------------------------------------------

const BASELINE_2025 = 2091000;
const PROJECAO_2026 = 3377120;

export default function ProjecaoPage() {
  const [data, setData] = useState<Projecao | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchProjecao()
      .then(setData)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  const resumo = data?.resumo;
  const porConsultor = data?.por_consultor ?? [];

  // Progress bar for % alcancado — capped at 100 visually
  const pctBar = Math.min(100, resumo?.pct_alcancado ?? 0);
  const pctColor =
    pctBar >= 80 ? '#00B050' : pctBar >= 50 ? '#FFC000' : '#FF0000';

  return (
    <div className="space-y-6">
      {/* Page heading */}
      <div>
        <h1 className="text-xl font-bold text-gray-900">Projecao de Faturamento</h1>
        <p className="text-sm text-gray-500 mt-0.5">
          Acompanhamento de meta Q1 2026 e projecao anual
        </p>
      </div>

      {error && (
        <div className="p-4 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700">
          Erro ao carregar projecao: {error}
        </div>
      )}

      {/* Summary KPI cards */}
      <section>
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          <KpiCard
            title="Realizado Q1 2026"
            value={resumo ? formatBRL(resumo.faturamento_realizado) : '—'}
            subtitle="Faturamento acumulado Q1"
            accentColor="#00B050"
            loading={loading}
          />
          <KpiCard
            title="Meta Q1 2026"
            value={resumo ? formatBRL(resumo.meta_q1) : '—'}
            subtitle="Objetivo trimestral"
            accentColor="#2563eb"
            loading={loading}
          />
          <KpiCard
            title="% Alcancado"
            value={resumo ? formatPercent(resumo.pct_alcancado) : '—'}
            subtitle={resumo && resumo.pct_alcancado >= 100 ? 'Meta atingida' : 'Em andamento'}
            accentColor={pctColor}
            loading={loading}
          />
          <KpiCard
            title="Projecao 2026"
            value={formatBRL(PROJECAO_2026)}
            subtitle={`+${formatPercent(((PROJECAO_2026 - BASELINE_2025) / BASELINE_2025) * 100)} vs 2025`}
            accentColor="#7c3aed"
            loading={loading}
          />
        </div>
      </section>

      {/* Q1 progress bar */}
      <section className="bg-white rounded-lg border border-gray-200 p-5 shadow-sm">
        <div className="flex justify-between items-center mb-3">
          <h2 className="text-sm font-semibold text-gray-700">
            Progresso Meta Q1 2026
          </h2>
          {resumo && (
            <span className="text-sm font-bold" style={{ color: pctColor }}>
              {formatPercent(resumo.pct_alcancado)}
            </span>
          )}
        </div>

        <div className="w-full bg-gray-100 rounded-full h-5 overflow-hidden">
          {loading ? (
            <div className="h-full w-full bg-gray-200 animate-pulse rounded-full" />
          ) : (
            <div
              className="h-full rounded-full transition-all duration-700 flex items-center justify-end pr-2"
              style={{ width: `${pctBar}%`, backgroundColor: pctColor }}
            >
              {pctBar > 15 && (
                <span className="text-[11px] font-semibold text-white">
                  {formatBRL(resumo?.faturamento_realizado ?? 0)}
                </span>
              )}
            </div>
          )}
        </div>

        {resumo && (
          <div className="flex justify-between mt-2 text-xs text-gray-500">
            <span>R$ 0</span>
            <span>Meta: {formatBRL(resumo.meta_q1)}</span>
          </div>
        )}
      </section>

      {/* Baseline vs Projecao card */}
      <section className="bg-white rounded-lg border border-gray-200 p-5 shadow-sm">
        <h2 className="text-sm font-semibold text-gray-700 mb-4">
          Baseline 2025 vs Projecao 2026
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="space-y-3">
            <ComparisonRow
              label="Baseline 2025 (auditoria forense)"
              value={BASELINE_2025}
              isBaseline
            />
            <ComparisonRow
              label="Projecao 2026"
              value={PROJECAO_2026}
              deltaVs={BASELINE_2025}
            />
          </div>

          {/* Visual comparison bars */}
          <div className="space-y-4">
            <ProgressBar
              label="Baseline 2025"
              value={BASELINE_2025}
              max={PROJECAO_2026}
              color="#2563eb"
            />
            <ProgressBar
              label="Projecao 2026"
              value={PROJECAO_2026}
              max={PROJECAO_2026}
              color="#00B050"
            />
          </div>
        </div>
      </section>

      {/* Per consultant table */}
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
                      className="px-4 py-2.5 text-[11px] font-semibold text-gray-500 uppercase tracking-wide whitespace-nowrap"
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
                    <tr key={row.consultor} className="border-t border-gray-50 hoverable">
                      <td className="px-4 py-3 font-semibold text-gray-900">
                        {row.consultor}
                      </td>
                      <td className="px-4 py-3 font-mono text-gray-800">
                        {formatBRL(row.faturamento)}
                      </td>
                      <td className="px-4 py-3 font-mono text-gray-600">
                        {formatBRL(row.meta)}
                      </td>
                      <td className="px-4 py-3">
                        <div className="flex items-center gap-2">
                          <div className="w-24 bg-gray-100 rounded-full h-2 overflow-hidden">
                            <div
                              className="h-full rounded-full"
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

      {/* Notes */}
      <div className="bg-blue-50 border border-blue-100 rounded-lg p-4 text-xs text-blue-700 space-y-1">
        <p>
          <strong>Baseline 2025:</strong> R$ 2.091.000 — auditoria forense 68 arquivos (PAINEL CEO DEFINITIVO, 2026-03-23).
        </p>
        <p>
          <strong>Anterior (supersedido):</strong> R$ 2.156.179 — diferenca de R$ 65K resolvida em CONFLITOS. Nao utilizar.
        </p>
        <p>
          <strong>Projecao 2026:</strong> R$ 3.377.120 (+61,5% vs baseline 2025).
        </p>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Sub-components
// ---------------------------------------------------------------------------

interface ComparisonRowProps {
  label: string;
  value: number;
  isBaseline?: boolean;
  deltaVs?: number;
}

function ComparisonRow({ label, value, isBaseline, deltaVs }: ComparisonRowProps) {
  const delta = deltaVs != null ? value - deltaVs : null;
  const deltaPct = deltaVs != null ? ((value - deltaVs) / deltaVs) * 100 : null;

  return (
    <div className="flex justify-between items-start gap-4 py-2 border-b border-gray-100">
      <span className="text-sm text-gray-600 flex-shrink-0">{label}</span>
      <div className="text-right">
        <p className={`text-sm font-bold ${isBaseline ? 'text-gray-800' : 'text-green-700'}`}>
          {formatBRL(value)}
        </p>
        {delta != null && (
          <p className="text-[11px] text-green-600">
            +{formatBRL(delta)} ({formatPercent(deltaPct ?? 0)})
          </p>
        )}
      </div>
    </div>
  );
}

interface ProgressBarProps {
  label: string;
  value: number;
  max: number;
  color: string;
}

function ProgressBar({ label, value, max, color }: ProgressBarProps) {
  const pct = max > 0 ? (value / max) * 100 : 0;

  return (
    <div>
      <div className="flex justify-between mb-1">
        <span className="text-xs text-gray-500">{label}</span>
        <span className="text-xs font-semibold text-gray-700">{formatBRL(value)}</span>
      </div>
      <div className="w-full bg-gray-100 rounded-full h-3 overflow-hidden">
        <div
          className="h-full rounded-full"
          style={{ width: `${pct}%`, backgroundColor: color }}
        />
      </div>
    </div>
  );
}
