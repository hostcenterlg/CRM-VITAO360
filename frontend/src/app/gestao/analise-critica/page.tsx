'use client';

// Análise Crítica — Página de Listagem
// Substitui página honesta KILO. Consome /api/dde/* (PAPA squad).
// Foco: priorização — REVISAR/RENEGOCIAR/SUBSTITUIR primeiro.
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

type FiltroVeredito = 'TODOS' | 'REVISAR' | 'RENEGOCIAR' | 'SUBSTITUIR' | 'SAUDAVEL' | 'ALERTA_CREDITO';

const PRIORIDADE_VEREDITO: Record<string, number> = {
  SUBSTITUIR: 0,
  RENEGOCIAR: 1,
  ALERTA_CREDITO: 2,
  REVISAR: 3,
  SEM_DADOS: 4,
  SAUDAVEL: 5,
};

function ordenarPorPrioridade(items: DDEComparativoItem[]): DDEComparativoItem[] {
  return [...items].sort((a, b) => {
    const pa = PRIORIDADE_VEREDITO[a.veredito] ?? 99;
    const pb = PRIORIDADE_VEREDITO[b.veredito] ?? 99;
    return pa - pb;
  });
}

function AnaliseCriticaContent() {
  const { user } = useAuth();
  const [items, setItems] = useState<DDEComparativoItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [erro, setErro] = useState<string | null>(null);
  const [filtro, setFiltro] = useState<FiltroVeredito>('TODOS');
  const [ano] = useState(new Date().getFullYear());

  useEffect(() => {
    if (!user) return;
    const nome = user.consultor_nome ?? user.nome;
    if (!nome) return;

    setLoading(true);
    setErro(null);
    fetchDDEConsultor(nome, ano)
      .then((res) => setItems(ordenarPorPrioridade(res.items ?? [])))
      .catch((err: Error) => setErro(err.message))
      .finally(() => setLoading(false));
  }, [user, ano]);

  const itensFiltrados = filtro === 'TODOS'
    ? items
    : items.filter((i) => i.veredito === filtro);

  const contadores = {
    SUBSTITUIR: items.filter((i) => i.veredito === 'SUBSTITUIR').length,
    RENEGOCIAR: items.filter((i) => i.veredito === 'RENEGOCIAR').length,
    REVISAR: items.filter((i) => i.veredito === 'REVISAR').length,
    ALERTA_CREDITO: items.filter((i) => i.veredito === 'ALERTA_CREDITO').length,
    SAUDAVEL: items.filter((i) => i.veredito === 'SAUDAVEL').length,
  };

  const precisamAtencao = contadores.SUBSTITUIR + contadores.RENEGOCIAR + contadores.REVISAR;

  return (
    <div className="space-y-6 px-3 md:px-4 lg:px-6 pb-12">
      {/* Breadcrumb */}
      <div className="pt-1 flex items-center gap-1.5 text-xs text-gray-400">
        <Link href="/dashboard" className="hover:text-gray-700 transition-colors">Dashboard</Link>
        <span>/</span>
        <span className="text-gray-600">Análise Crítica</span>
      </div>

      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-4">
        <div className="flex-1">
          <div className="flex items-center gap-3 flex-wrap mb-2">
            <div
              className="flex-shrink-0 w-10 h-10 rounded-xl flex items-center justify-center"
              style={{ backgroundColor: '#7C3AED15' }}
            >
              <svg className="w-5 h-5" fill="none" stroke="#7C3AED" viewBox="0 0 24 24" aria-hidden="true">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                  d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
              </svg>
            </div>
            <h1 className="text-2xl font-bold text-gray-900 tracking-tight">Análise Crítica</h1>
            <span className="text-sm font-normal text-gray-500">Score + Veredito + Ações por cliente</span>
          </div>
          <p className="text-sm text-gray-700 leading-relaxed max-w-2xl">
            Clientes priorizados por urgência. <strong>SUBSTITUIR/RENEGOCIAR primeiro</strong> —
            cada cliente sem atenção está destruindo margem.
          </p>
        </div>
        {!loading && precisamAtencao > 0 && (
          <div className="flex-shrink-0">
            <span className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-bold bg-red-50 text-red-700 border border-red-200">
              <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
              </svg>
              {precisamAtencao} precisam de atenção
            </span>
          </div>
        )}
      </div>

      {/* ClienteSelector */}
      <div className="bg-white border border-gray-200 rounded-xl p-5 shadow-sm">
        <p className="text-sm font-semibold text-gray-800 mb-3">Consultar cliente específico</p>
        <ClienteSelector
          destinoBase="/gestao/analise-critica"
          placeholder="Buscar por CNPJ ou razão social…"
        />
      </div>

      {/* Filtros */}
      {items.length > 0 && (
        <div className="flex flex-wrap gap-2">
          {([
            { key: 'TODOS', label: `Todos (${items.length})` },
            { key: 'SUBSTITUIR', label: `Substituir (${contadores.SUBSTITUIR})` },
            { key: 'RENEGOCIAR', label: `Renegociar (${contadores.RENEGOCIAR})` },
            { key: 'REVISAR', label: `Revisar (${contadores.REVISAR})` },
            { key: 'ALERTA_CREDITO', label: `Alerta Crédito (${contadores.ALERTA_CREDITO})` },
            { key: 'SAUDAVEL', label: `Saudável (${contadores.SAUDAVEL})` },
          ] as { key: FiltroVeredito; label: string }[]).map((f) => (
            <button
              key={f.key}
              type="button"
              onClick={() => setFiltro(f.key)}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold border transition-colors min-h-[32px] ${
                filtro === f.key
                  ? 'bg-gray-800 text-white border-gray-800'
                  : 'bg-white text-gray-600 border-gray-200 hover:bg-gray-50'
              }`}
              aria-pressed={filtro === f.key}
            >
              {f.label}
            </button>
          ))}
        </div>
      )}

      {/* Lista priorizada */}
      <div className="bg-white border border-gray-200 rounded-xl shadow-sm overflow-hidden">
        <div className="px-5 py-4 border-b border-gray-100 flex items-center justify-between">
          <h2 className="text-sm font-bold text-gray-900">
            Clientes — ordenados por urgência
          </h2>
          {loading && (
            <svg className="w-4 h-4 text-gray-400 animate-spin" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
            </svg>
          )}
        </div>

        {erro && (
          <div className="px-5 py-4 text-xs text-amber-700 bg-amber-50">
            {erro.includes('403') ? 'Dados fora do seu escopo.' : `Erro: ${erro}`}
          </div>
        )}

        {!loading && !erro && itensFiltrados.length === 0 && (
          <div className="flex items-center justify-center py-12 text-sm text-gray-500">
            Nenhum cliente encontrado com o filtro selecionado.
          </div>
        )}

        {loading && (
          <div className="flex items-center justify-center py-12">
            <svg className="w-6 h-6 text-green-500 animate-spin" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
            </svg>
          </div>
        )}

        {!loading && !erro && itensFiltrados.length > 0 && (
          <div className="overflow-x-auto">
            <table className="min-w-full text-xs" aria-label="Análise crítica por cliente">
              <thead>
                <tr className="bg-gray-50 border-b border-gray-200">
                  <th scope="col" className="px-3 py-2 text-left font-semibold text-gray-600">Cliente</th>
                  <th scope="col" className="px-3 py-2 text-left font-semibold text-gray-600 font-mono">CNPJ</th>
                  <th scope="col" className="px-3 py-2 text-right font-semibold text-gray-600 tabular-nums">Rec. Bruta</th>
                  <th scope="col" className="px-3 py-2 text-right font-semibold text-gray-600 tabular-nums">MC%</th>
                  <th scope="col" className="px-3 py-2 text-right font-semibold text-gray-600 tabular-nums">Score</th>
                  <th scope="col" className="px-3 py-2 text-center font-semibold text-gray-600">Veredito</th>
                  <th scope="col" className="px-3 py-2 text-center font-semibold text-gray-600">Ações</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {itensFiltrados.map((item) => {
                  const urgente = ['SUBSTITUIR', 'RENEGOCIAR'].includes(item.veredito);
                  return (
                    <tr
                      key={item.cnpj}
                      className={`${urgente ? 'bg-red-50 hover:bg-red-100' : 'bg-white hover:bg-gray-50'} transition-colors`}
                    >
                      <td className="px-3 py-2.5 text-gray-800 font-medium max-w-[180px] truncate">
                        {item.razao_social ?? '—'}
                        {urgente && (
                          <span className="ml-1.5 inline-block w-1.5 h-1.5 rounded-full bg-red-500" aria-hidden="true" />
                        )}
                      </td>
                      <td className="px-3 py-2.5 font-mono text-gray-500">{item.cnpj}</td>
                      <td className="px-3 py-2.5 text-right tabular-nums text-gray-700">
                        {item.receita_bruta != null ? formatBRL(item.receita_bruta) : '—'}
                      </td>
                      <td className={`px-3 py-2.5 text-right tabular-nums font-semibold ${
                        item.mc_pct == null ? 'text-gray-400' :
                        item.mc_pct < 5 ? 'text-red-600' :
                        item.mc_pct < 15 ? 'text-amber-600' : 'text-green-700'
                      }`}>
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
                        <div className="flex items-center justify-center gap-1.5">
                          <Link
                            href={`/gestao/analise-critica/${item.cnpj}`}
                            className="inline-flex items-center gap-1 px-2 py-1 rounded text-xs font-semibold text-purple-700 border border-purple-200 bg-purple-50 hover:bg-purple-100 transition-colors min-h-[32px]"
                            aria-label={`Análise crítica de ${item.razao_social ?? item.cnpj}`}
                          >
                            Analisar
                          </Link>
                          <Link
                            href={`/gestao/dde/${item.cnpj}`}
                            className="inline-flex items-center gap-1 px-2 py-1 rounded text-xs font-semibold text-gray-600 border border-gray-200 bg-white hover:bg-gray-50 transition-colors min-h-[32px]"
                            aria-label={`Ver DDE de ${item.razao_social ?? item.cnpj}`}
                          >
                            DDE
                          </Link>
                        </div>
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

export default function AnaliseCriticaPage() {
  return (
    <RequireRole minRole="GERENTE">
      <AnaliseCriticaContent />
    </RequireRole>
  );
}
