'use client';

import Link from 'next/link';
import { RequireRole } from '@/components/auth';
import { PreviewBanner } from '../_components/PreviewBanner';
import { ScoreGauge } from '../_components/ScoreGauge';
import { KPICards } from '../_components/KPICards';
import { AnomaliasList } from '../_components/AnomaliasList';
import { AcoesPriorizadasList } from '../_components/AcoesPriorizadasList';
import type { KPIItem } from '../_components/KPICards';
import type { AnomaliaItem } from '../_components/AnomaliasList';
import type { AcaoItem } from '../_components/AcoesPriorizadasList';

// ---------------------------------------------------------------------------
// Análise Crítica do Cliente
// Spec: SPEC_FEATURE_ANALISE_CRITICA_CRM_VITAO360.md + BRIEFING_UI_ABA_ANALISE_CRITICA.md
// Score 0-100 + 9 KPIs (I1-I9) + 3 Anomalias + 5 Ações priorizadas por cliente
// BLOQUEADO até DDE Engine integrar (Fase 3a) — dados ilustrativos sinalizados (R8)
// ---------------------------------------------------------------------------

// ---------------------------------------------------------------------------
// Dados mockup — plausíveis para B2B alimentar
// Cliente Referência (GMR-001) — margem negativa, alto frete, devolução elevada
// AVISO R8: valores ilustrativos — 2 sinalizações na UI
// ---------------------------------------------------------------------------

const SCORE_MOCK = 32;

const KPIS_MOCK: KPIItem[] = [
  {
    codigo: 'I1',
    label: 'Margem Bruta %',
    valor: '-14,9%',
    status: 'critico',
    detalhe: 'Meta: >25%',
    variacao: '▼ vs meta',
  },
  {
    codigo: 'I2',
    label: 'Margem Contrib. %',
    valor: '-14,9%',
    status: 'critico',
    detalhe: 'Mín. aceitável: 5%',
  },
  {
    codigo: 'I3',
    label: 'EBITDA Cliente %',
    valor: null,
    status: 'pendente',
    faseBloqueio: 'Fase B',
  },
  {
    codigo: 'I4',
    label: 'Custo de Servir',
    valor: '32,5%',
    status: 'critico',
    detalhe: 'Limite: <15%',
  },
  {
    codigo: 'I5',
    label: 'Verba % Receita',
    valor: '0,6%',
    status: 'ok',
    detalhe: 'Limite: <5%',
  },
  {
    codigo: 'I6',
    label: 'Inadimplência %',
    valor: '1,0%',
    status: 'ok',
    detalhe: 'Limite: <3%',
  },
  {
    codigo: 'I7',
    label: 'Devolução %',
    valor: '21,7%',
    status: 'critico',
    detalhe: 'Limite: <5%',
    variacao: '▲ anomalia A1',
  },
  {
    codigo: 'I8',
    label: 'Aging Médio (DSO)',
    valor: '52d',
    status: 'atencao',
    detalhe: 'Ideal: <45d',
  },
  {
    codigo: 'I9',
    label: 'Score Saúde Fin.',
    valor: '32/100',
    status: 'critico',
    detalhe: '<40 = SUBSTITUIR',
  },
];

const ANOMALIAS_MOCK: AnomaliaItem[] = [
  {
    codigo: 'A1',
    titulo: 'Devolução muito elevada',
    descricao: 'Devolução 21,7% do faturamento — indica problemas recorrentes de qualidade, quebra de portfólio ou NF incorreta. Limite aceitável: 10%.',
    valorObservado: '21,7% — R$ 180.251',
    limite: '< 10%',
    severidade: 'CRITICO',
  },
  {
    codigo: 'A2',
    titulo: 'Margem de Contribuição negativa',
    descricao: 'MC = -R$ 125.961 (-14,9%). Cada R$ vendido gera prejuízo antes mesmo dos fixos. Cliente destrói valor. Ação imediata requerida.',
    valorObservado: '-R$ 125.961 (-14,9%)',
    limite: '≥ R$ 0 (MC mínima aceitável)',
    severidade: 'CRITICO',
  },
  {
    codigo: 'A3',
    titulo: 'Frete CT-e representa 22,1% da Receita Líquida',
    descricao: 'Frete R$ 185.834 sobre RL R$ 842.321 — 2x o limite recomendado. Verificar: rotas alternativas, consolidação de pedidos, frequência de entrega.',
    valorObservado: '22,1% — R$ 185.834',
    limite: '< 12%',
    severidade: 'ALTA',
  },
  {
    codigo: 'A4',
    titulo: 'Comissão 4,6% — acima do padrão',
    descricao: 'Representante com comissão 4,6% vs média carteira 3,0%. Para um cliente com MC negativa, cada 0,1pp de comissão equivale a ~R$ 842/mês.',
    valorObservado: '4,6%',
    limite: 'Padrão carteira: 3,0%',
    severidade: 'MEDIA',
  },
];

const ACOES_MOCK: AcaoItem[] = [
  {
    posicao: 1,
    titulo: 'Investigar e reduzir devolução 21,7% → meta 10%',
    descricao: 'Abrir análise NF por NF — identificar motivo principal (qualidade, prazo, mix). Potencial recuperação de R$ 98k/ano.',
    impacto: '+R$ 98.000/ano estimado',
    status: 'ABERTO',
    prazo: 'Imediato',
  },
  {
    posicao: 2,
    titulo: 'Renegociar estrutura de frete — consolidar entregas',
    descricao: 'Reduzir de 229 CT-es para entrega consolidada. Meta: reduzir frete de 22,1% para 12–14% da RL.',
    impacto: '-R$ 86.000/ano estimado',
    status: 'ABERTO',
    prazo: '30 dias',
  },
  {
    posicao: 3,
    titulo: 'Renegociar CMV — reposicionar SKUs com custo alto',
    descricao: 'CMV de 61,7% da RL está acima do benchmark setor (48–52%). Priorizar SKUs de maior volume e menor margem.',
    impacto: 'Margem +5pp estimado',
    status: 'ABERTO',
    prazo: '60 dias',
  },
  {
    posicao: 4,
    titulo: 'Revisar comissão de representante para padrão carteira',
    descricao: 'De 4,6% para 3,0% do padrão. Com MC negativa, não há base para manter comissão premium.',
    impacto: '+R$ 13.400/ano',
    status: 'EM_ANDAMENTO',
    prazo: 'Próxima renovação',
  },
  {
    posicao: 5,
    titulo: 'Gerar Resumo CEO e apresentar à diretoria',
    descricao: 'Consolidar análise e recomendar plano de reversão ou substitução em 90 dias.',
    impacto: 'Decisão estratégica',
    status: 'ABERTO',
    prazo: 'Sprint Fase 3a',
  },
];

export default function AnaliseCriticaPage() {
  return (
    <RequireRole minRole="GERENTE">
      <div className="space-y-6 px-3 md:px-4 lg:px-6 pb-12">

        {/* Breadcrumb */}
        <div className="pt-1 flex items-center gap-1.5 text-xs text-gray-400">
          <Link href="/dashboard" className="hover:text-gray-700 transition-colors">Dashboard</Link>
          <span>/</span>
          <span className="text-gray-600">Análise Crítica</span>
        </div>

        {/* ---------------------------------------------------------------- */}
        {/* Header principal */}
        {/* ---------------------------------------------------------------- */}
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
              <span className="text-sm font-normal text-gray-500">Score + P&amp;L + Anomalias + Ações por cliente</span>
            </div>
            <p className="text-sm text-gray-600 leading-relaxed max-w-2xl">
              Transforma 30–45 min de trabalho manual em <strong>decisão em segundos</strong>.
              Score 0–100 + 9 KPIs + anomalias detectadas + 5 ações priorizadas com impacto R$.
              Alimentado pelo DDE (Fase 3a).
            </p>
          </div>

          {/* Badge bloqueado */}
          <div className="flex-shrink-0">
            <span className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-bold uppercase tracking-wide bg-gray-100 text-gray-600 border border-gray-300">
              <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5}
                  d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
              </svg>
              Bloqueado — aguarda DDE
            </span>
          </div>
        </div>

        {/* ---------------------------------------------------------------- */}
        {/* Banner obrigatório — Mockup ilustrativo (R8) — primeiro ponto */}
        {/* ---------------------------------------------------------------- */}
        <PreviewBanner
          mensagem="PREVIEW — Bloqueado até DDE Engine integrar (Fase 3a). Dados abaixo são ilustrativos baseados em Cliente Referência (GMR-001)."
          fase="Fase 3a — Maio/2026"
        />

        {/* ---------------------------------------------------------------- */}
        {/* SEÇÃO 1: Score + Veredito */}
        {/* ---------------------------------------------------------------- */}
        <section aria-labelledby="sec-score">
          <div className="flex items-center justify-between mb-3">
            <h2 id="sec-score" className="text-xs font-bold text-gray-400 uppercase tracking-wider">
              Score + Veredito Automático
            </h2>
            {/* Segundo ponto de sinalização R8 */}
            <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold uppercase text-amber-700 bg-amber-50 border border-amber-200">
              Mockup ilustrativo
            </span>
          </div>
          <ScoreGauge
            score={SCORE_MOCK}
            veredito="SUBSTITUIR"
            fasTag="Fase A · Dados comerciais"
            dataAtualizacao="29/Abr/2026 14:32 — simulação"
          />
        </section>

        {/* ---------------------------------------------------------------- */}
        {/* SEÇÃO 2: 9 KPIs em grid (I1-I9) */}
        {/* ---------------------------------------------------------------- */}
        <section aria-labelledby="sec-kpis">
          <h2 id="sec-kpis" className="text-xs font-bold text-gray-400 uppercase tracking-wider mb-3">
            Indicadores — I1 a I9
          </h2>
          <KPICards kpis={KPIS_MOCK} colunas={3} />

          {/* Thresholds para referência */}
          <details className="mt-3">
            <summary className="text-xs text-gray-400 cursor-pointer hover:text-gray-600 transition-colors">
              Ver thresholds de cor
            </summary>
            <div className="mt-2 overflow-x-auto">
              <table className="text-xs border-collapse w-full max-w-lg">
                <thead>
                  <tr className="border-b border-gray-200">
                    <th className="text-left py-1 px-2 text-gray-500 font-semibold">Indicador</th>
                    <th className="text-center py-1 px-2 text-green-600 font-semibold">Verde</th>
                    <th className="text-center py-1 px-2 text-yellow-600 font-semibold">Amarelo</th>
                    <th className="text-center py-1 px-2 text-red-600 font-semibold">Vermelho</th>
                  </tr>
                </thead>
                <tbody className="text-gray-600">
                  <tr className="border-b border-gray-100">
                    <td className="py-1 px-2">MC % (I2)</td>
                    <td className="py-1 px-2 text-center">≥ 15%</td>
                    <td className="py-1 px-2 text-center">5–15%</td>
                    <td className="py-1 px-2 text-center">&lt; 5%</td>
                  </tr>
                  <tr className="border-b border-gray-100">
                    <td className="py-1 px-2">Custo Servir (I4)</td>
                    <td className="py-1 px-2 text-center">&lt; 15%</td>
                    <td className="py-1 px-2 text-center">15–25%</td>
                    <td className="py-1 px-2 text-center">&gt; 25%</td>
                  </tr>
                  <tr className="border-b border-gray-100">
                    <td className="py-1 px-2">Devolução (I7)</td>
                    <td className="py-1 px-2 text-center">&lt; 5%</td>
                    <td className="py-1 px-2 text-center">5–10%</td>
                    <td className="py-1 px-2 text-center">&gt; 10%</td>
                  </tr>
                  <tr className="border-b border-gray-100">
                    <td className="py-1 px-2">DSO/Aging (I8)</td>
                    <td className="py-1 px-2 text-center">&lt; 45d</td>
                    <td className="py-1 px-2 text-center">45–90d</td>
                    <td className="py-1 px-2 text-center">&gt; 90d</td>
                  </tr>
                  <tr>
                    <td className="py-1 px-2">Verba % (I5)</td>
                    <td className="py-1 px-2 text-center">&lt; 5%</td>
                    <td className="py-1 px-2 text-center">5–8%</td>
                    <td className="py-1 px-2 text-center">&gt; 8%</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </details>
        </section>

        {/* ---------------------------------------------------------------- */}
        {/* SEÇÃO 3: Anomalias detectadas */}
        {/* ---------------------------------------------------------------- */}
        <section aria-labelledby="sec-anomalias">
          <div className="flex items-center justify-between mb-3">
            <h2 id="sec-anomalias" className="text-xs font-bold text-gray-400 uppercase tracking-wider">
              Anomalias Detectadas
            </h2>
            <span className="text-xs font-semibold text-red-600 bg-red-50 border border-red-200 px-2 py-0.5 rounded">
              {ANOMALIAS_MOCK.length} anomalias
            </span>
          </div>
          <AnomaliasList anomalias={ANOMALIAS_MOCK} />
        </section>

        {/* ---------------------------------------------------------------- */}
        {/* SEÇÃO 4: Ações priorizadas */}
        {/* ---------------------------------------------------------------- */}
        <section aria-labelledby="sec-acoes">
          <h2 id="sec-acoes" className="text-xs font-bold text-gray-400 uppercase tracking-wider mb-3">
            Top 5 Ações Priorizadas
          </h2>
          <AcoesPriorizadasList acoes={ACOES_MOCK} />
        </section>

        {/* ---------------------------------------------------------------- */}
        {/* SEÇÃO 5: Cascata P&L resumida (referência ao DDE) */}
        {/* ---------------------------------------------------------------- */}
        <section aria-labelledby="sec-cascata-resumo">
          <h2 id="sec-cascata-resumo" className="text-xs font-bold text-gray-400 uppercase tracking-wider mb-3">
            Cascata P&amp;L — Resumo Executivo
          </h2>
          <div className="bg-white rounded-xl border border-gray-100 shadow-sm p-5">
            <p className="text-xs text-gray-500 mb-4">
              Visualização resumida da DRE. Para cascata completa (25 linhas, 7 blocos, tier pills),
              acesse{' '}
              <Link href="/gestao/dde" className="text-blue-600 hover:underline font-semibold">
                DDE completo →
              </Link>
            </p>

            {/* Mini-cascata — 6 linhas chave */}
            <div className="space-y-1.5">
              {[
                { cod: 'L1',  label: 'Faturamento Bruto',        valor:  1076343, cor: 'text-gray-900',  bold: false },
                { cod: 'L4',  label: '(-) Devoluções (21,7%)',    valor:  -180251, cor: 'text-red-500',   bold: false },
                { cod: 'L11', label: '= Receita Líquida (Comerc.)', valor: 842321, cor: 'text-gray-900',  bold: true  },
                { cod: 'L12', label: '(-) CMV (61,7%)',           valor:  -520153, cor: 'text-red-500',   bold: false },
                { cod: 'L13', label: '= Margem Bruta',            valor:  -125961, cor: 'text-red-600',   bold: true  },
                { cod: 'L21', label: '= Margem Contribuição',     valor:  -125961, cor: 'text-red-600',   bold: true  },
              ].map((row) => (
                <div
                  key={row.cod}
                  className={`flex items-center justify-between px-3 py-2 rounded-lg text-xs ${
                    row.bold ? 'bg-gray-50 font-semibold' : ''
                  }`}
                >
                  <div className="flex items-center gap-2">
                    <span className="font-mono text-[10px] text-gray-400 w-8">{row.cod}</span>
                    <span className="text-gray-700">{row.label}</span>
                  </div>
                  <span className={`font-mono tabular-nums ${row.cor} ${row.bold ? 'font-bold' : ''}`}>
                    {row.valor.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL', maximumFractionDigits: 0 })}
                  </span>
                </div>
              ))}
            </div>

            <div className="mt-3 px-3 py-2 bg-red-50 border border-red-200 rounded-lg">
              <p className="text-xs font-semibold text-red-700">
                Veredito: SUBSTITUIR — Margem de Contribuição negativa (-14,9%)
              </p>
              <p className="text-xs text-red-600 mt-0.5">
                Cada R$ 1,00 vendido gera R$ 0,149 de prejuízo. Cliente destrói valor sem renegociação imediata.
              </p>
            </div>
          </div>
        </section>

        {/* ---------------------------------------------------------------- */}
        {/* SEÇÃO 6: Status da feature */}
        {/* ---------------------------------------------------------------- */}
        <section aria-labelledby="sec-status-feature">
          <h2 id="sec-status-feature" className="text-xs font-bold text-gray-400 uppercase tracking-wider mb-3">
            Status da Feature
          </h2>
          <div className="bg-white rounded-xl border border-gray-100 shadow-sm p-5">
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
              {[
                { done: true,  label: 'Spec aprovada',    detalhe: 'Algoritmo definido (v1.0)' },
                { done: true,  label: 'Golden Master',    detalhe: 'GMR-001 calibrado ±0,5%' },
                { done: false, label: 'Implementação',    detalhe: 'Aguarda DDE Fase 3a' },
                { done: false, label: 'Previsão',         detalhe: 'Maio/2026', destaque: true },
              ].map((item, i) => (
                <div key={i} className="flex items-start gap-2.5">
                  {item.done ? (
                    <span
                      className="mt-0.5 flex-shrink-0 w-5 h-5 rounded-full flex items-center justify-center"
                      style={{ backgroundColor: '#00A85920' }}
                    >
                      <svg className="w-3 h-3" fill="none" stroke="#00A859" viewBox="0 0 24 24" aria-hidden="true">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
                      </svg>
                    </span>
                  ) : (
                    <span className="mt-0.5 flex-shrink-0 w-5 h-5 rounded-full flex items-center justify-center bg-amber-50 border border-amber-200">
                      <svg className="w-3 h-3 text-amber-400" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                      </svg>
                    </span>
                  )}
                  <div>
                    <p className={`text-xs font-semibold ${item.done ? 'text-gray-700' : 'text-gray-500'}`}>
                      {item.label}
                    </p>
                    <p className={`text-xs mt-0.5 ${item.destaque ? 'text-amber-700 font-semibold' : 'text-gray-400'}`}>
                      {item.detalhe}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* Rodapé */}
        <p className="text-xs text-gray-400">
          Análise Crítica v1.1 — Spec: SPEC_FEATURE_ANALISE_CRITICA_CRM_VITAO360.md v1.0 ·
          Implementação aguarda DDE Fase 3a · Dados ilustrativos baseados em Cliente Referência (GMR-001) ·
          Esta página é preview de roadmap para apresentação interna.
        </p>

      </div>
    </RequireRole>
  );
}
