'use client';

// DDE — Página individual do cliente /gestao/dde/[cnpj]
// Consome GET /api/dde/cliente/{cnpj}?ano=YYYY
// Tratamento de erros: 401 redirect, 403 empty state, 404 not found, 422 canal inelegível
// R8: tier PENDENTE/NULL → "—", nunca inferido

import { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import { RequireRole } from '@/components/auth';
import { CascataPL } from '../_components/CascataPL';
import { ScoreGauge } from '../_components/ScoreGauge';
import { IndicadoresGrid } from '../_components/IndicadoresGrid';
import { VeredictoBadge } from '../_components/VeredictoBadge';
import { CanalIneligivelMessage } from '../_components/CanalIneligivelMessage';
import { fetchDDECliente } from '@/lib/api';
import type { ResultadoDDE } from '@/lib/api';

// Re-export dos componentes do dir pai para satisfazer Next.js
import '../_components/CascataPL';

type ErrorType = 'canal_inelegivel' | 'fora_escopo' | 'nao_encontrado' | 'generico' | null;

interface StatusCounts {
  REAL: number;
  SINTETICO: number;
  PENDENTE: number;
  NULL: number;
}

function contarTiers(resultado: ResultadoDDE): StatusCounts {
  const counts: StatusCounts = { REAL: 0, SINTETICO: 0, PENDENTE: 0, NULL: 0 };
  for (const linha of resultado.linhas) {
    const tier = linha.classificacao as keyof StatusCounts;
    if (tier in counts) counts[tier]++;
  }
  return counts;
}

function DDEClienteContent() {
  const params = useParams();
  const router = useRouter();
  const cnpj = decodeURIComponent((params.cnpj as string) ?? '');
  const [resultado, setResultado] = useState<ResultadoDDE | null>(null);
  const [loading, setLoading] = useState(true);
  const [erroTipo, setErroTipo] = useState<ErrorType>(null);
  const [erroMsg, setErroMsg] = useState<string | null>(null);
  const [canalInelegivel, setCanalInelegivel] = useState<string | undefined>(undefined);
  const [ano, setAno] = useState(new Date().getFullYear());

  useEffect(() => {
    if (!cnpj) return;
    setLoading(true);
    setErroTipo(null);
    setErroMsg(null);
    setResultado(null);

    fetchDDECliente(cnpj, ano)
      .then((res) => setResultado(res))
      .catch((err: Error) => {
        const msg = err.message ?? '';
        if (msg.includes('401') || msg.includes('expirada')) {
          router.push('/login');
        } else if (msg.includes('403') || msg.includes('scopo')) {
          setErroTipo('fora_escopo');
        } else if (msg.includes('404')) {
          setErroTipo('nao_encontrado');
        } else if (msg.includes('422') || msg.includes('elegível') || msg.includes('elegivel')) {
          setErroTipo('canal_inelegivel');
          // Extrai nome do canal da mensagem de erro se disponível
          const match = msg.match(/canal\s+([A-Z_]+)/i);
          setCanalInelegivel(match?.[1]);
        } else {
          setErroTipo('generico');
          setErroMsg(msg);
        }
      })
      .finally(() => setLoading(false));
  }, [cnpj, ano, router]);

  const anoAtual = new Date().getFullYear();
  const anos = [anoAtual, anoAtual - 1, anoAtual - 2];

  return (
    <div className="space-y-6 px-3 md:px-4 lg:px-6 pb-12">
      {/* Breadcrumb */}
      <div className="pt-1 flex items-center gap-1.5 text-xs text-gray-400">
        <Link href="/dashboard" className="hover:text-gray-700 transition-colors">Dashboard</Link>
        <span>/</span>
        <Link href="/gestao/dde" className="hover:text-gray-700 transition-colors">DDE</Link>
        <span>/</span>
        <span className="font-mono text-gray-600">{cnpj}</span>
      </div>

      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
        <div>
          <h1 className="text-xl font-bold text-gray-900">
            DDE — {resultado?.cnpj ?? cnpj}
          </h1>
          <p className="text-sm text-gray-500 font-mono mt-0.5">{cnpj}</p>
        </div>
        {/* Seletor de ano */}
        <div className="flex items-center gap-2">
          <span className="text-xs text-gray-500">Ano:</span>
          <div className="flex rounded-lg border border-gray-200 overflow-hidden">
            {anos.map((a) => (
              <button
                key={a}
                type="button"
                onClick={() => setAno(a)}
                className={`px-3 py-1.5 text-xs font-semibold transition-colors min-w-[50px] min-h-[32px] ${
                  a === ano
                    ? 'bg-green-600 text-white'
                    : 'bg-white text-gray-600 hover:bg-gray-50'
                }`}
                aria-pressed={a === ano}
              >
                {a}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Loading */}
      {loading && (
        <div className="flex items-center justify-center py-20">
          <svg className="w-8 h-8 text-green-500 animate-spin" fill="none" viewBox="0 0 24 24" aria-label="Carregando DDE">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
          </svg>
        </div>
      )}

      {/* Erro: canal inelegível */}
      {!loading && erroTipo === 'canal_inelegivel' && (
        <div className="bg-white border border-gray-200 rounded-xl shadow-sm">
          <CanalIneligivelMessage canal={canalInelegivel} />
        </div>
      )}

      {/* Erro: fora do escopo */}
      {!loading && erroTipo === 'fora_escopo' && (
        <div className="bg-gray-50 border border-gray-200 rounded-xl p-8 text-center">
          <p className="text-sm font-semibold text-gray-700 mb-1">Cliente fora do seu escopo</p>
          <p className="text-xs text-gray-500">Você não tem acesso ao DDE deste cliente.</p>
        </div>
      )}

      {/* Erro: não encontrado */}
      {!loading && erroTipo === 'nao_encontrado' && (
        <div className="bg-gray-50 border border-gray-200 rounded-xl p-8 text-center">
          <p className="text-sm font-semibold text-gray-700 mb-1">CNPJ não encontrado</p>
          <p className="text-xs text-gray-500">O CNPJ <span className="font-mono">{cnpj}</span> não está cadastrado no sistema.</p>
          <Link href="/gestao/dde" className="mt-3 inline-block text-xs text-green-700 font-semibold hover:underline">
            Voltar para DDE
          </Link>
        </div>
      )}

      {/* Erro genérico */}
      {!loading && erroTipo === 'generico' && (
        <div className="bg-amber-50 border border-amber-200 rounded-lg px-4 py-3 text-xs text-amber-800">
          <span className="font-semibold">Erro ao carregar DDE:</span> {erroMsg}
        </div>
      )}

      {/* Resultado principal */}
      {!loading && resultado && (
        <>
          {/* Score + Veredito */}
          <div className="bg-white border border-gray-200 rounded-xl p-5 shadow-sm">
            <div className="flex flex-col sm:flex-row items-start sm:items-center gap-6 flex-wrap">
              <ScoreGauge score={resultado.indicadores.I9} size={140} />
              <div className="flex flex-col gap-2">
                <VeredictoBadge
                  veredito={resultado.veredito}
                  descricao={resultado.veredito_descricao}
                  size="lg"
                />
                <div className="flex flex-wrap gap-2 mt-1">
                  <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-semibold bg-blue-50 text-blue-700 border border-blue-200">
                    Fase {resultado.fase_ativa}
                  </span>
                  <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-semibold bg-gray-50 text-gray-600 border border-gray-200">
                    Ano {resultado.ano}
                  </span>
                </div>
              </div>
            </div>
          </div>

          {/* Cascata P&L */}
          <div className="bg-white border border-gray-200 rounded-xl p-5 shadow-sm">
            <h2 className="text-sm font-bold text-gray-900 mb-4">Cascata P&L — {resultado.linhas.length} linhas</h2>
            <CascataPL linhas={resultado.linhas} />
          </div>

          {/* Indicadores 3x3 */}
          <div className="bg-white border border-gray-200 rounded-xl p-5 shadow-sm">
            <h2 className="text-sm font-bold text-gray-900 mb-4">Indicadores Econômicos (I1–I9)</h2>
            <IndicadoresGrid indicadores={resultado.indicadores} />
          </div>

          {/* Sidebar de status dos tiers */}
          {(() => {
            const counts = contarTiers(resultado);
            const totalLinhas = resultado.linhas.length;
            return (
              <div className="bg-white border border-gray-200 rounded-xl p-5 shadow-sm">
                <h2 className="text-sm font-bold text-gray-900 mb-3">Qualidade dos dados</h2>
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                  {[
                    { tier: 'REAL', count: counts.REAL, bg: 'bg-green-50', text: 'text-green-800', border: 'border-green-200', label: 'REAL' },
                    { tier: 'SINTETICO', count: counts.SINTETICO, bg: 'bg-amber-50', text: 'text-amber-800', border: 'border-amber-200', label: 'SINTÉTICO' },
                    { tier: 'PENDENTE', count: counts.PENDENTE, bg: 'bg-gray-50', text: 'text-gray-700', border: 'border-gray-200', label: 'PENDENTE' },
                    { tier: 'NULL', count: counts.NULL, bg: 'bg-blue-50', text: 'text-blue-700', border: 'border-blue-200', label: 'NULL' },
                  ].map((row) => (
                    <div key={row.tier} className={`rounded-lg border ${row.border} ${row.bg} p-3 text-center`}>
                      <div className={`text-2xl font-extrabold tabular-nums ${row.text}`}>{row.count}</div>
                      <div className={`text-xs font-semibold mt-0.5 ${row.text}`}>{row.label}</div>
                      <div className="text-xs text-gray-500 mt-0.5">
                        {totalLinhas > 0 ? `${((row.count / totalLinhas) * 100).toFixed(0)}%` : '—'}
                      </div>
                    </div>
                  ))}
                </div>
                <p className="text-xs text-gray-500 mt-3 leading-relaxed">
                  Linhas <span className="font-semibold">PENDENTE</span> e <span className="font-semibold">NULL</span>{' '}
                  aguardam dados de Fase B (SAP fiscal, frete CT-e, verbas). Valores exibidos como{' '}
                  <span className="font-mono">—</span> — nenhum dado fabricado (R8).
                </p>
              </div>
            );
          })()}

          {/* Link análise crítica */}
          <div className="bg-blue-50 border border-blue-200 rounded-xl p-4 flex items-start gap-3">
            <svg className="w-4 h-4 text-blue-500 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
            </svg>
            <div>
              <p className="text-xs font-semibold text-blue-800 mb-1">Ver Análise Crítica</p>
              <p className="text-xs text-blue-700 leading-snug">
                Decisão priorizada com anomalias detectadas e ações recomendadas.{' '}
                <Link
                  href={`/gestao/analise-critica/${cnpj}`}
                  className="font-semibold underline hover:text-blue-900 transition-colors"
                >
                  Abrir Análise Crítica →
                </Link>
              </p>
            </div>
          </div>
        </>
      )}
    </div>
  );
}

export default function DDEClientePage() {
  return (
    <RequireRole minRole="GERENTE">
      <DDEClienteContent />
    </RequireRole>
  );
}
