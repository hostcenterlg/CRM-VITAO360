'use client';

import { useEffect, useState } from 'react';
import {
  fetchKPIs,
  fetchDistribuicao,
  fetchTop10,
  KPIs,
  Distribuicao,
  Top10Cliente,
  formatBRL,
  formatPercent,
} from '@/lib/api';
import KpiCard from '@/components/KpiCard';
import StatusBadge from '@/components/StatusBadge';

// ---------------------------------------------------------------------------
// Dashboard page — KPIs, distribuicao, top 10 clientes
// Client component: data from external API via useEffect
// ---------------------------------------------------------------------------

// Color map for situacao distribution bars
const situacaoColors: Record<string, string> = {
  ATIVO: '#00B050',
  'INAT.REC': '#FFC000',
  'INAT.ANT': '#FF0000',
  INATIVO: '#FF0000',
  PROSPECT: '#808080',
};

// Color map for sinaleiro
const sinaleiroColors: Record<string, string> = {
  VERDE: '#00B050',
  AMARELO: '#FFC000',
  VERMELHO: '#FF0000',
  ROXO: '#800080',
};

export default function DashboardPage() {
  const [kpis, setKpis] = useState<KPIs | null>(null);
  const [distribuicao, setDistribuicao] = useState<Distribuicao | null>(null);
  const [top10, setTop10] = useState<Top10Cliente[]>([]);
  const [loading, setLoading] = useState(true);
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

  return (
    <div className="space-y-6">
      {/* Page heading */}
      <div>
        <h1 className="text-xl font-bold text-gray-900">Dashboard</h1>
        <p className="text-sm text-gray-500 mt-0.5">
          Visao geral da carteira comercial VITAO360
        </p>
      </div>

      {error && (
        <div className="p-4 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700">
          Erro ao carregar dados: {error}
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
          />
          <KpiCard
            title="Clientes Ativos"
            value={kpis?.total_ativos.toLocaleString('pt-BR') ?? '—'}
            subtitle={`${kpis?.total_inativos ?? 0} inativos`}
            accentColor="#00B050"
            loading={loading}
          />
          <KpiCard
            title="Faturamento Total"
            value={kpis ? formatBRL(kpis.faturamento_total) : '—'}
            subtitle="Baseline 2025"
            accentColor="#7c3aed"
            loading={loading}
          />
          <KpiCard
            title="Score Medio"
            value={kpis ? kpis.media_score.toFixed(1) : '—'}
            subtitle={`${kpis?.clientes_criticos ?? 0} criticos / ${kpis?.clientes_alerta ?? 0} em alerta`}
            accentColor="#dc2626"
            loading={loading}
          />
        </div>
      </section>

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

        {/* Sinaleiro distribution */}
        <section className="bg-white rounded-lg border border-gray-200 p-4 shadow-sm">
          <h2 className="text-sm font-semibold text-gray-700 mb-4">
            Distribuicao por Sinaleiro
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
      </div>

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
                  <tr key={c.cnpj} className="border-t border-gray-50 hoverable">
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
// Sub-components
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
          <div key={item.label} className="flex items-center gap-3">
            <span className="w-20 text-xs text-gray-600 text-right flex-shrink-0 font-medium truncate">
              {item.label}
            </span>
            <div className="flex-1 bg-gray-100 rounded-full h-4 overflow-hidden">
              <div
                className="h-full rounded-full transition-all duration-500"
                style={{ width: `${barWidth}%`, backgroundColor: color }}
              />
            </div>
            <span className="w-16 text-xs text-gray-500 flex-shrink-0">
              {item.count.toLocaleString('pt-BR')} ({formatPercent(item.pct)})
            </span>
          </div>
        );
      })}
    </div>
  );
}

const prioridadeBarColors: Record<string, string> = {
  P0: '#FF0000',
  P1: '#FF6600',
  P2: '#FFC000',
  P3: '#FFFF00',
  P4: '#9ca3af',
  P5: '#d1d5db',
};

function PrioridadeChart({ items }: { items: { label: string; count: number; pct: number }[] }) {
  return (
    <BarChart
      items={items}
      colorMap={prioridadeBarColors}
      defaultColor="#9ca3af"
    />
  );
}

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

function EmptyState() {
  return (
    <div className="py-8 text-center text-gray-400 text-sm">
      Sem dados disponíveis
    </div>
  );
}

function formatCnpj(cnpj: string): string {
  const d = cnpj.replace(/\D/g, '').padStart(14, '0');
  if (d.length !== 14) return cnpj;
  return `${d.slice(0, 2)}.${d.slice(2, 5)}.${d.slice(5, 8)}/${d.slice(8, 12)}-${d.slice(12)}`;
}
