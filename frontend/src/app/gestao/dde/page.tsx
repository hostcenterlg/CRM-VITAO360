'use client';

// DDE — Demonstração de Desempenho Econômico — Página de Listagem
// Substitui página honesta KILO. Consome /api/dde/* (PAPA squad).
// R8: dados PENDENTE/NULL → "—", nunca inferidos.
// RequireRole(GERENTE) preservado (FOXTROT/KILO).

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { RequireRole } from '@/components/auth';
import { useAuth } from '@/contexts/AuthContext';
import { ClienteSelector } from '../_components/ClienteSelector';
import { VeredictoBadge } from '../_components/VeredictoBadge';
import { fetchDDEConsultor } from '@/lib/api';
import type { DDEComparativoItem } from '@/lib/api';
import { formatBRL } from '@/lib/api';

function ComparativoTable({ items }: { items: DDEComparativoItem[] }) {
  if (items.length === 0) {
    return (
      <div className="flex items-center justify-center py-10 text-sm text-gray-500">
        Nenhum cliente DDE encontrado para o período selecionado.
      </div>
    );
  }

  return (
    <div className="overflow-x-auto rounded-lg border border-gray-200">
      <table className="min-w-full text-xs" aria-label="Comparativo DDE por consultor">
        <thead>
          <tr className="bg-gray-50 border-b border-gray-200">
            <th scope="col" className="px-3 py-2 text-left font-semibold text-gray-600">Cliente</th>
            <th scope="col" className="px-3 py-2 text-left font-semibold text-gray-600 font-mono">CNPJ</th>
            <th scope="col" className="px-3 py-2 text-right font-semibold text-gray-600 tabular-nums">Rec. Bruta</th>
            <th scope="col" className="px-3 py-2 text-right font-semibold text-gray-600 tabular-nums">MC%</th>
            <th scope="col" className="px-3 py-2 text-right font-semibold text-gray-600 tabular-nums">Score</th>
            <th scope="col" className="px-3 py-2 text-center font-semibold text-gray-600">Veredito</th>
            <th scope="col" className="px-3 py-2 text-center font-semibold text-gray-600">Detalhe</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-100">
          {items.slice(0, 10).map((item) => (
            <tr key={item.cnpj} className="bg-white hover:bg-green-50 transition-colors">
              <td className="px-3 py-2.5 text-gray-800 font-medium max-w-[180px] truncate">
                {item.razao_social ?? '—'}
              </td>
              <td className="px-3 py-2.5 font-mono text-gray-500">{item.cnpj}</td>
              <td className="px-3 py-2.5 text-right tabular-nums text-gray-700">
                {item.receita_bruta != null ? formatBRL(item.receita_bruta) : '—'}
              </td>
              <td className="px-3 py-2.5 text-right tabular-nums text-gray-700">
                {item.mc_pct != null ? `${item.mc_pct.toFixed(1)}%` : '—'}
              </td>
              <td className="px-3 py-2.5 text-right tabular-nums">
                {item.score != null ? (
                  <span className={`font-bold ${item.score >= 70 ? 'text-green-700' : item.score >= 50 ? 'text-amber-700' : 'text-red-600'}`}>
                    {Math.round(item.score)}
                  </span>
                ) : '—'}
              </td>
              <td className="px-3 py-2.5 text-center">
                <VeredictoBadge veredito={item.veredito} size="sm" />
              </td>
              <td className="px-3 py-2.5 text-center">
                <Link
                  href={`/gestao/dde/${item.cnpj}`}
                  className="inline-flex items-center gap-1 px-2.5 py-1 rounded text-xs font-semibold text-green-700 border border-green-200 bg-green-50 hover:bg-green-100 transition-colors min-h-[32px]"
                  aria-label={`Ver DDE de ${item.razao_social ?? item.cnpj}`}
                >
                  Ver DDE
                </Link>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function DDEContent() {
  const { user, isAdmin, isGerente } = useAuth();
  const [items, setItems] = useState<DDEComparativoItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [erro, setErro] = useState<string | null>(null);
  const [ano] = useState(new Date().getFullYear());

  useEffect(() => {
    if (!user) return;
    const nome = user.consultor_nome ?? user.nome;
    if (!nome) return;

    setLoading(true);
    setErro(null);
    fetchDDEConsultor(nome, ano)
      .then((res) => setItems(res.items ?? []))
      .catch((err: Error) => setErro(err.message))
      .finally(() => setLoading(false));
  }, [user, ano]);

  return (
    <div className="space-y-6 px-3 md:px-4 lg:px-6 pb-12">
      {/* Breadcrumb */}
      <div className="pt-1 flex items-center gap-1.5 text-xs text-gray-400">
        <Link href="/dashboard" className="hover:text-gray-700 transition-colors">Dashboard</Link>
        <span>/</span>
        <span className="text-gray-600">DDE</span>
      </div>

      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-4">
        <div className="flex-1">
          <div className="flex items-center gap-3 flex-wrap mb-2">
            <div
              className="flex-shrink-0 w-10 h-10 rounded-xl flex items-center justify-center"
              style={{ backgroundColor: '#00A85915' }}
            >
              <svg className="w-5 h-5" fill="none" stroke="#00A859" viewBox="0 0 24 24" aria-hidden="true">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
              </svg>
            </div>
            <h1 className="text-2xl font-bold text-gray-900 tracking-tight">DDE</h1>
            <span className="text-sm font-normal text-gray-500">Demonstração de Desempenho Econômico</span>
          </div>
          <p className="text-sm text-gray-700 leading-relaxed max-w-2xl">
            Cascata P&amp;L por cliente — do Faturamento Bruto ao Resultado Operacional.
            Responde: <strong>&ldquo;Esse cliente dá lucro ou prejuízo para a Vitao?&rdquo;</strong>
          </p>
        </div>
        <div className="flex-shrink-0 flex items-center gap-2">
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-semibold bg-blue-50 text-blue-700 border border-blue-200">
            Fase A
          </span>
          <span className="text-xs text-gray-500">{ano}</span>
        </div>
      </div>

      {/* PreviewBanner */}
      <div className="bg-amber-50 border border-amber-200 rounded-lg px-4 py-3 flex items-start gap-2.5">
        <svg className="w-4 h-4 text-amber-600 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
        <p className="text-xs text-amber-800 leading-relaxed">
          <span className="font-semibold">Fase A ativa.</span> Apenas canais{' '}
          <span className="font-medium">Direto, Indireto e Food Service</span> são elegíveis.
          Linhas com tier <span className="font-mono bg-amber-100 px-1 rounded">PENDENTE</span> aguardam
          dados de frete, verbas e impostos (Fase B). Cascata parcial é honesta — nenhum valor fabricado.
        </p>
      </div>

      {/* ClienteSelector */}
      <div className="bg-white border border-gray-200 rounded-xl p-5 shadow-sm">
        <p className="text-sm font-semibold text-gray-800 mb-3">Consultar cliente específico</p>
        <ClienteSelector
          destinoBase="/gestao/dde"
          placeholder="Buscar por CNPJ ou razão social…"
        />
      </div>

      {/* Comparativo da carteira */}
      <div className="bg-white border border-gray-200 rounded-xl p-5 shadow-sm">
        <div className="flex items-center justify-between mb-4 flex-wrap gap-2">
          <h2 className="text-sm font-bold text-gray-900">
            Carteira — Top clientes DDE {ano}
          </h2>
          {loading && (
            <span className="text-xs text-gray-500 flex items-center gap-1">
              <svg className="w-3.5 h-3.5 animate-spin" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
              </svg>
              Carregando…
            </span>
          )}
        </div>

        {erro && (
          <div className="text-xs text-amber-700 bg-amber-50 border border-amber-200 rounded-lg px-3 py-2 mb-4">
            {erro.includes('403') || erro.includes('scopo')
              ? 'Dados de DDE fora do seu escopo de acesso.'
              : erro.includes('422')
              ? 'Canal não elegível para DDE.'
              : `Erro ao carregar comparativo: ${erro}`}
          </div>
        )}

        {!loading && !erro && <ComparativoTable items={items} />}

        {loading && (
          <div className="flex items-center justify-center py-10">
            <svg className="w-6 h-6 text-green-500 animate-spin" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
            </svg>
          </div>
        )}
      </div>

      {/* CTA canais — admin/gerente */}
      {(isAdmin || isGerente) && (
        <div className="bg-white border border-gray-200 rounded-xl p-5 shadow-sm">
          <h2 className="text-sm font-bold text-gray-900 mb-3">Consolidado por canal</h2>
          <div className="flex flex-wrap gap-2">
            {[
              { id: 1, label: 'Direto' },
              { id: 2, label: 'Indireto' },
              { id: 3, label: 'Food Service' },
            ].map((c) => (
              <Link
                key={c.id}
                href={`/gestao/dde/canal/${c.id}`}
                className="inline-flex items-center gap-1.5 px-3 py-2 rounded-lg border border-gray-200 bg-gray-50 hover:bg-green-50 hover:border-green-200 text-xs font-semibold text-gray-700 hover:text-green-700 transition-colors min-h-[44px]"
              >
                <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
                </svg>
                Canal {c.label}
              </Link>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

export default function DDEPage() {
  return (
    <RequireRole minRole="GERENTE">
      <DDEContent />
    </RequireRole>
  );
}
