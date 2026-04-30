'use client';

// Análise Crítica — Página individual /gestao/analise-critica/[cnpj]
// Foco em DECISÃO: veredito gigante + anomalias + ações priorizadas
// Cascata resumida (L1, L11, L21, MC%) + link para DDE completo
// R8: dados PENDENTE/NULL → "—", nunca inferidos

import { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import { RequireRole } from '@/components/auth';
import { ScoreGauge } from '../../_components/ScoreGauge';
import { VeredictoBadge } from '../../_components/VeredictoBadge';
import { CanalIneligivelMessage } from '../../_components/CanalIneligivelMessage';
import { fetchDDECliente } from '@/lib/api';
import type { ResultadoDDE, LinhaDRE, IndicadoresDDE } from '@/lib/api';
import { formatBRL } from '@/lib/api';

type ErrorType = 'canal_inelegivel' | 'fora_escopo' | 'nao_encontrado' | 'generico' | null;

// ---------------------------------------------------------------------------
// Anomalias detectadas client-side a partir dos indicadores
// ---------------------------------------------------------------------------

interface Anomalia {
  label: string;
  valor: string;
  detalhe: string;
  nivel: 'CRITICO' | 'ALERTA' | 'OBSERVACAO';
}

function detectarAnomalias(ind: IndicadoresDDE): Anomalia[] {
  const anomalias: Anomalia[] = [];

  if (ind.I2 != null && ind.I2 < 0) {
    anomalias.push({ label: 'Margem de Contribuição negativa', valor: `${ind.I2.toFixed(1)}%`, detalhe: 'Cliente destrói valor — cada venda gera prejuízo para a Vitao.', nivel: 'CRITICO' });
  } else if (ind.I2 != null && ind.I2 < 5) {
    anomalias.push({ label: 'Margem de Contribuição crítica', valor: `${ind.I2.toFixed(1)}%`, detalhe: 'Abaixo de 5% — margem insuficiente para cobrir custos fixos alocados.', nivel: 'ALERTA' });
  }

  if (ind.I6 != null && ind.I6 > 5) {
    anomalias.push({ label: 'Inadimplência elevada', valor: `${ind.I6.toFixed(1)}%`, detalhe: 'Risco de crédito acima do limite aceitável. Avaliar bloqueio de novos pedidos.', nivel: 'CRITICO' });
  } else if (ind.I6 != null && ind.I6 > 3) {
    anomalias.push({ label: 'Inadimplência acima do limite', valor: `${ind.I6.toFixed(1)}%`, detalhe: 'Percentual de débito provisionado como perda acima de 3%.', nivel: 'ALERTA' });
  }

  if (ind.I3 != null && ind.I3 > 10) {
    anomalias.push({ label: 'Comissão excessiva', valor: `${ind.I3.toFixed(1)}%`, detalhe: 'Comissão do representante acima de 10% da Receita Líquida.', nivel: 'ALERTA' });
  }

  if (ind.I4 != null && ind.I4 > 7) {
    anomalias.push({ label: 'Frete desproporcional', valor: `${ind.I4.toFixed(1)}%`, detalhe: 'Custo de frete CT-e acima de 7% comprime fortemente a margem.', nivel: 'ALERTA' });
  }

  if (ind.I7 != null && ind.I7 > 5) {
    anomalias.push({ label: 'Taxa de devolução crítica', valor: `${ind.I7.toFixed(1)}%`, detalhe: 'Devolução acima de 5% — possível problema de qualidade, prazo ou sell-out.', nivel: 'CRITICO' });
  }

  if (ind.I8 != null && ind.I8 > 60) {
    anomalias.push({ label: 'Aging crítico', valor: `${Math.round(ind.I8)}d`, detalhe: 'Prazo médio de recebimento acima de 60 dias. Risco de inadimplência crescente.', nivel: 'ALERTA' });
  }

  return anomalias.slice(0, 3);
}

// ---------------------------------------------------------------------------
// Ações priorizadas client-side
// ---------------------------------------------------------------------------

interface AcaoPriorizada {
  ordem: number;
  acao: string;
  impacto: string;
  contexto: string;
}

function gerarAcoes(resultado: ResultadoDDE): AcaoPriorizada[] {
  const { indicadores: ind, veredito } = resultado;
  const acoes: AcaoPriorizada[] = [];
  let ordem = 1;

  if (veredito === 'SUBSTITUIR') {
    acoes.push({ ordem: ordem++, acao: 'Iniciar processo de substituição ou inativação', impacto: 'Eliminar prejuízo recorrente', contexto: 'Veredito SUBSTITUIR — cliente destrói valor em todos os indicadores.' });
  }

  if (veredito === 'RENEGOCIAR' || (ind.I2 != null && ind.I2 < 10)) {
    acoes.push({ ordem: ordem++, acao: 'Renegociar contrato e condições comerciais', impacto: `+${ind.I2 != null ? (10 - ind.I2).toFixed(1) : '?'}pp de MC esperado`, contexto: 'Margem de Contribuição abaixo do patamar mínimo.' });
  }

  if (ind.I5 != null && ind.I5 > 4) {
    acoes.push({ ordem: ordem++, acao: `Reduzir verba de ${ind.I5.toFixed(1)}% para máximo 4%`, impacto: `Economia de ~${(ind.I5 - 4).toFixed(1)}pp na MC`, contexto: 'Verba acima do benchmark da carteira.' });
  }

  if (ind.I4 != null && ind.I4 > 5) {
    acoes.push({ ordem: ordem++, acao: 'Renegociar frete — avaliar backlog e roteirização', impacto: `Redução estimada de ${(ind.I4 - 5).toFixed(1)}pp em custo`, contexto: 'Frete CT-e acima de 5% da Receita Líquida.' });
  }

  if (ind.I6 != null && ind.I6 > 3) {
    acoes.push({ ordem: ordem++, acao: 'Bloquear crédito e cobrar débitos em aberto', impacto: 'Reduzir inadimplência para < 3%', contexto: `Inadimplência atual: ${ind.I6.toFixed(1)}%.` });
  }

  if (acoes.length < 3 && veredito === 'REVISAR') {
    acoes.push({ ordem: ordem++, acao: 'Revisar mix de produtos — focar em SKUs de maior margem', impacto: 'Melhorar MC sem alterar volume', contexto: 'Margem em zona de atenção.' });
  }

  if (acoes.length === 0) {
    acoes.push({ ordem: 1, acao: 'Manter condições atuais e monitorar evolução trimestral', impacto: 'Preservar saúde do relacionamento', contexto: 'Cliente com indicadores dentro dos parâmetros.' });
  }

  return acoes.slice(0, 5);
}

// ---------------------------------------------------------------------------
// Cascata resumida (apenas L1, L11, L21)
// ---------------------------------------------------------------------------

const CODIGOS_RESUMO = ['L1', 'L11', 'L21'];

function CascataResumo({ linhas }: { linhas: LinhaDRE[] }) {
  const resumo = linhas.filter((l) => CODIGOS_RESUMO.includes(l.codigo));
  if (resumo.length === 0) return null;

  return (
    <div className="divide-y divide-gray-100 border border-gray-200 rounded-lg overflow-hidden">
      {resumo.map((linha) => (
        <div key={linha.codigo} className="flex items-center gap-3 px-4 py-3 bg-gray-50">
          <span className="font-mono text-xs text-gray-400 w-8 flex-shrink-0">{linha.codigo}</span>
          <span className="text-xs font-semibold text-gray-700 flex-1">{linha.conta}</span>
          <span className="tabular-nums text-sm font-bold text-gray-800">
            {linha.valor != null ? formatBRL(linha.valor) : '—'}
          </span>
          <span className="text-xs text-gray-500 w-14 text-right tabular-nums">
            {linha.pct_receita != null ? `${linha.pct_receita.toFixed(1)}%` : '—'}
          </span>
        </div>
      ))}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Componente principal
// ---------------------------------------------------------------------------

function AnaliseCriticaClienteContent() {
  const params = useParams();
  const router = useRouter();
  const cnpj = decodeURIComponent((params.cnpj as string) ?? '');
  const [resultado, setResultado] = useState<ResultadoDDE | null>(null);
  const [loading, setLoading] = useState(true);
  const [erroTipo, setErroTipo] = useState<ErrorType>(null);
  const [erroMsg, setErroMsg] = useState<string | null>(null);
  const [canalInelegivel, setCanalInelegivel] = useState<string | undefined>(undefined);

  useEffect(() => {
    if (!cnpj) return;
    setLoading(true);
    setErroTipo(null);
    setErroMsg(null);
    setResultado(null);

    fetchDDECliente(cnpj)
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
          const match = msg.match(/canal\s+([A-Z_]+)/i);
          setCanalInelegivel(match?.[1]);
        } else {
          setErroTipo('generico');
          setErroMsg(msg);
        }
      })
      .finally(() => setLoading(false));
  }, [cnpj, router]);

  const anomalias = resultado ? detectarAnomalias(resultado.indicadores) : [];
  const acoes = resultado ? gerarAcoes(resultado) : [];

  return (
    <div className="space-y-6 px-3 md:px-4 lg:px-6 pb-12">
      {/* Breadcrumb */}
      <div className="pt-1 flex items-center gap-1.5 text-xs text-gray-400">
        <Link href="/dashboard" className="hover:text-gray-700 transition-colors">Dashboard</Link>
        <span>/</span>
        <Link href="/gestao/analise-critica" className="hover:text-gray-700 transition-colors">Análise Crítica</Link>
        <span>/</span>
        <span className="font-mono text-gray-600">{cnpj}</span>
      </div>

      {/* Loading */}
      {loading && (
        <div className="flex items-center justify-center py-20">
          <svg className="w-8 h-8 text-purple-500 animate-spin" fill="none" viewBox="0 0 24 24" aria-label="Carregando análise">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
          </svg>
        </div>
      )}

      {/* Erros */}
      {!loading && erroTipo === 'canal_inelegivel' && (
        <div className="bg-white border border-gray-200 rounded-xl shadow-sm">
          <CanalIneligivelMessage canal={canalInelegivel} />
        </div>
      )}
      {!loading && erroTipo === 'fora_escopo' && (
        <div className="bg-gray-50 border border-gray-200 rounded-xl p-8 text-center">
          <p className="text-sm font-semibold text-gray-700">Cliente fora do seu escopo</p>
        </div>
      )}
      {!loading && erroTipo === 'nao_encontrado' && (
        <div className="bg-gray-50 border border-gray-200 rounded-xl p-8 text-center">
          <p className="text-sm font-semibold text-gray-700 mb-1">CNPJ não encontrado</p>
          <Link href="/gestao/analise-critica" className="text-xs text-purple-700 font-semibold hover:underline">
            Voltar para Análise Crítica
          </Link>
        </div>
      )}
      {!loading && erroTipo === 'generico' && (
        <div className="bg-amber-50 border border-amber-200 rounded-lg px-4 py-3 text-xs text-amber-800">
          <span className="font-semibold">Erro:</span> {erroMsg}
        </div>
      )}

      {/* Resultado */}
      {!loading && resultado && (
        <>
          {/* Veredito GIGANTE + Score */}
          <div className="bg-white border border-gray-200 rounded-xl p-6 shadow-sm">
            <div className="flex flex-col sm:flex-row items-start sm:items-center gap-6 flex-wrap">
              <div className="flex-1">
                <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">Decisão</p>
                <VeredictoBadge
                  veredito={resultado.veredito}
                  descricao={resultado.veredito_descricao}
                  size="lg"
                />
              </div>
              <ScoreGauge score={resultado.indicadores.I9} size={130} />
            </div>
          </div>

          {/* Anomalias */}
          {anomalias.length > 0 && (
            <div className="bg-white border border-gray-200 rounded-xl p-5 shadow-sm">
              <h2 className="text-sm font-bold text-gray-900 mb-3">
                Anomalias detectadas ({anomalias.length})
              </h2>
              <div className="space-y-2">
                {anomalias.map((a, i) => (
                  <div
                    key={i}
                    className={`flex items-start gap-3 px-3 py-2.5 rounded-lg border ${
                      a.nivel === 'CRITICO'
                        ? 'bg-red-50 border-red-200'
                        : a.nivel === 'ALERTA'
                        ? 'bg-amber-50 border-amber-200'
                        : 'bg-blue-50 border-blue-200'
                    }`}
                  >
                    <span className={`flex-shrink-0 text-xs font-bold px-1.5 py-0.5 rounded mt-0.5 tabular-nums ${
                      a.nivel === 'CRITICO' ? 'bg-red-100 text-red-700' :
                      a.nivel === 'ALERTA' ? 'bg-amber-100 text-amber-700' :
                      'bg-blue-100 text-blue-700'
                    }`}>
                      {a.valor}
                    </span>
                    <div className="min-w-0">
                      <p className="text-xs font-semibold text-gray-800">{a.label}</p>
                      <p className="text-xs text-gray-600 mt-0.5 leading-snug">{a.detalhe}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Ações priorizadas */}
          <div className="bg-white border border-gray-200 rounded-xl p-5 shadow-sm">
            <h2 className="text-sm font-bold text-gray-900 mb-3">
              Ações priorizadas ({acoes.length})
            </h2>
            <div className="space-y-2">
              {acoes.map((acao) => (
                <div key={acao.ordem} className="flex items-start gap-3 px-3 py-3 rounded-lg border border-gray-200 bg-gray-50">
                  <span className="flex-shrink-0 w-6 h-6 rounded-full bg-white border border-gray-300 flex items-center justify-center text-xs font-bold text-gray-600 mt-0.5">
                    {acao.ordem}
                  </span>
                  <div className="min-w-0 flex-1">
                    <p className="text-xs font-semibold text-gray-800">{acao.acao}</p>
                    <p className="text-xs text-gray-500 mt-0.5 leading-snug">{acao.contexto}</p>
                  </div>
                  <span className="flex-shrink-0 text-xs font-medium text-green-700 bg-green-50 border border-green-200 px-1.5 py-0.5 rounded whitespace-nowrap">
                    {acao.impacto}
                  </span>
                </div>
              ))}
            </div>
          </div>

          {/* Cascata resumida */}
          <div className="bg-white border border-gray-200 rounded-xl p-5 shadow-sm">
            <h2 className="text-sm font-bold text-gray-900 mb-3">
              Resumo financeiro — Receita / Líquida / MC
            </h2>
            <CascataResumo linhas={resultado.linhas} />
          </div>

          {/* CTA DDE completo */}
          <div className="bg-green-50 border border-green-200 rounded-xl p-4 flex items-start gap-3">
            <svg className="w-4 h-4 text-green-600 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
            </svg>
            <div>
              <p className="text-xs font-semibold text-green-800 mb-1">Ver DDE completo (21 linhas)</p>
              <p className="text-xs text-green-700 leading-snug">
                Cascata P&L detalhada com todos os indicadores, tiers e fontes.{' '}
                <Link
                  href={`/gestao/dde/${cnpj}`}
                  className="font-semibold underline hover:text-green-900 transition-colors"
                >
                  Abrir DDE completo →
                </Link>
              </p>
            </div>
          </div>
        </>
      )}
    </div>
  );
}

export default function AnaliseCriticaClientePage() {
  return (
    <RequireRole minRole="GERENTE">
      <AnaliseCriticaClienteContent />
    </RequireRole>
  );
}
