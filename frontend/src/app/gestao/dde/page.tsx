'use client';

import Link from 'next/link';
import { RequireRole } from '@/components/auth';
import { PreviewBanner } from '../_components/PreviewBanner';
import { CascataPL } from '../_components/CascataPL';
import type { CascataBlocoData } from '../_components/CascataPL';

// ---------------------------------------------------------------------------
// DDE — Diagnóstico Demonstrativo do Equilíbrio (cascata P&L por cliente)
// Spec: docs/specs/cowork/SPEC_DDE_CASCATA_REAL.md
// Motor Python pronto — integração FastAPI pendente (Fase 3a)
// ---------------------------------------------------------------------------

// ---------------------------------------------------------------------------
// Dados mockup — plausíveis para B2B alimentar, cliente referência (GMR-001)
// AVISO R8: valores ilustrativos, sinalizados em 2 pontos na UI
// Cliente referência: ticket ~R$1.07M/ano, margem negativa (-12.3%)
// Fonte: GOLDEN_MASTER_REFERENCIA.md + SPEC_DDE_CASCATA_REAL.md
// ---------------------------------------------------------------------------

const CASCATA_MOCKUP: CascataBlocoData[] = [
  {
    numero: 1,
    titulo: 'Receita Bruta',
    linhas: [
      {
        codigo: 'L1',
        conta: 'Faturamento bruto a tabela (valor produtos NF)',
        sinal: '+',
        valor: 1076343,
        pctRL: null,
        tier: 'REAL',
        fase: 'A',
        status: 'detalhe',
        observacao: 'Fonte: Sales Hunter fat_cliente — valor pós-desconto na tabela',
      },
      {
        codigo: 'L2',
        conta: 'IPI sobre vendas',
        sinal: '+',
        valor: null,
        pctRL: null,
        tier: 'PENDENTE',
        fase: 'A',
        status: 'detalhe',
        observacao: 'Pendente: ingest não persiste IPI (D1)',
      },
      {
        codigo: 'L3',
        conta: '= Receita Bruta com IPI',
        sinal: '=',
        valor: 1076343,
        pctRL: null,
        tier: 'SINTETICO',
        fase: 'A',
        status: 'subtotal',
        observacao: 'L2 ainda pendente — L3 equivale a L1 nesta fase',
      },
    ],
  },
  {
    numero: 2,
    titulo: 'Deduções da Receita',
    linhas: [
      {
        codigo: 'L4',
        conta: '(-) Devoluções (NF cliente + própria)',
        sinal: '-',
        valor: -180251,
        pctRL: 21.4,
        tier: 'REAL',
        fase: 'A',
        status: 'detalhe',
        observacao: 'Fonte: SH devolucao_cliente — devolução TOTAL (não só troca NF)',
      },
      {
        codigo: 'L5',
        conta: '(-) Desconto comercial + contrato',
        sinal: '-',
        valor: null,
        pctRL: null,
        tier: 'PENDENTE',
        fase: 'A',
        status: 'detalhe',
        observacao: 'Pendente: ingest não persiste desc_comercial_pct (D1)',
      },
      {
        codigo: 'L6',
        conta: '(-) Desconto financeiro',
        sinal: '-',
        valor: null,
        pctRL: null,
        tier: 'PENDENTE',
        fase: 'A',
        status: 'detalhe',
        observacao: 'Pendente: ingest não persiste desc_financeiro_pct (D1)',
      },
      {
        codigo: 'L7',
        conta: '(-) Bonificações',
        sinal: '-',
        valor: null,
        pctRL: null,
        tier: 'PENDENTE',
        fase: 'A',
        status: 'detalhe',
        observacao: 'Pendente: ingest não persiste total_bonificacao (D1)',
      },
      {
        codigo: 'L8',
        conta: '(-) IPI faturado',
        sinal: '-',
        valor: null,
        pctRL: null,
        tier: 'PENDENTE',
        fase: 'A',
        status: 'detalhe',
        observacao: 'Pendente: ingest não persiste ipi_total (D1)',
      },
      {
        codigo: 'L9',
        conta: '(-) ICMS',
        sinal: '-',
        valor: null,
        pctRL: null,
        tier: 'PENDENTE',
        fase: 'B',
        status: 'detalhe',
        observacao: 'Fase B — aguarda SAP módulo fiscal',
      },
      {
        codigo: 'L10a',
        conta: '(-) PIS',
        sinal: '-',
        valor: null,
        pctRL: null,
        tier: 'PENDENTE',
        fase: 'B',
        status: 'detalhe',
        observacao: 'Fase B — aguarda SAP fiscal',
      },
      {
        codigo: 'L10b',
        conta: '(-) COFINS',
        sinal: '-',
        valor: null,
        pctRL: null,
        tier: 'PENDENTE',
        fase: 'B',
        status: 'detalhe',
        observacao: 'Fase B — aguarda SAP fiscal',
      },
      {
        codigo: 'L10c',
        conta: '(-) ICMS-ST',
        sinal: '-',
        valor: null,
        pctRL: null,
        tier: 'PENDENTE',
        fase: 'B',
        status: 'detalhe',
        observacao: 'Fase B — aguarda SAP fiscal',
      },
      {
        codigo: 'L11',
        conta: '= Receita Líquida Comercial (Fase A)',
        sinal: '=',
        valor: 842321,
        pctRL: 100.0,
        tier: 'REAL',
        fase: 'A',
        status: 'subtotal',
        observacao: 'L1 - L4 (sem impostos — Fase A). Golden Master: R$842.320,94',
      },
    ],
  },
  {
    numero: 3,
    titulo: 'CMV — Custo dos Produtos Vendidos',
    linhas: [
      {
        codigo: 'L12',
        conta: '(-) CMV — custo comercial produto (ZSD062 × ZSDFAT)',
        sinal: '-',
        valor: -520153,
        pctRL: 61.7,
        tier: 'REAL',
        fase: 'A',
        status: 'detalhe',
        observacao: 'Fonte: ZSD062 col.23 Custo Comercial × ZSDFAT qtd. Golden Master: R$520.152,78',
      },
      {
        codigo: 'L13',
        conta: '= Margem Bruta',
        sinal: '=',
        valor: -125961,
        pctRL: -14.9,
        tier: 'REAL',
        fase: 'A',
        status: 'subtotal',
        observacao: 'NEGATIVA — cliente destrói valor. Golden Master: -R$125.961,21',
      },
    ],
  },
  {
    numero: 4,
    titulo: 'Despesas Variáveis do Cliente (Custo de Servir)',
    linhas: [
      {
        codigo: 'L14',
        conta: '(-) Frete CT-e mensal (229 CT-es)',
        sinal: '-',
        valor: -185834,
        pctRL: 22.1,
        tier: 'REAL',
        fase: 'A',
        status: 'detalhe',
        observacao: 'Fonte: LOG Frete por Cliente 2025 — 229 CT-es. Golden Master: R$185.834,10',
      },
      {
        codigo: 'L15',
        conta: '(-) Comissão representante (4,6% — não 3% default)',
        sinal: '-',
        valor: -38747,
        pctRL: 4.6,
        tier: 'REAL',
        fase: 'A',
        status: 'detalhe',
        observacao: 'Comissão 4,6% sobre RL — confirmar SAP CL1. Golden Master: R$38.746,76',
      },
      {
        codigo: 'L16',
        conta: '(-) Verbas efetivadas (LOG)',
        sinal: '-',
        valor: -4824,
        pctRL: 0.6,
        tier: 'REAL',
        fase: 'A',
        status: 'detalhe',
        observacao: 'Fonte: LOG Verbas por Cliente 2025. Golden Master: R$4.824,46',
      },
      {
        codigo: 'L17',
        conta: '(-) Promotor PDV (3 agências)',
        sinal: '-',
        valor: -45408,
        pctRL: 5.4,
        tier: 'REAL',
        fase: 'A',
        status: 'detalhe',
        observacao: 'Fonte: LOG Despesas Clientes 2025. Golden Master: R$45.408,00',
      },
      {
        codigo: 'L18',
        conta: '(-) Bonificação financeira (rebate)',
        sinal: '-',
        valor: null,
        pctRL: null,
        tier: 'PENDENTE',
        fase: 'A',
        status: 'detalhe',
        observacao: 'Aberto D5 — confirmar se comissao_pct é rebate ou vendedor',
      },
      {
        codigo: 'L19',
        conta: '(-) Custo de inadimplência (provisão aging)',
        sinal: '-',
        valor: -8423,
        pctRL: 1.0,
        tier: 'SINTETICO',
        fase: 'A',
        status: 'detalhe',
        observacao: 'Estimativa: títulos vencidos × prob_perda. Fonte: debitos_clientes',
      },
      {
        codigo: 'L20',
        conta: '(-) Custo financeiro — capital de giro',
        sinal: '-',
        valor: -12635,
        pctRL: 1.5,
        tier: 'SINTETICO',
        fase: 'A',
        status: 'detalhe',
        observacao: 'Estimativa: aging médio × CDI fixo × valor em aberto',
      },
      {
        codigo: 'L21',
        conta: '= Margem de Contribuição (Fase A)',
        sinal: '=',
        valor: -125961,
        pctRL: -14.9,
        tier: 'SINTETICO',
        fase: 'A',
        status: 'subtotal',
        observacao: 'Parcial Fase A — sem CMV implica MC sobre RL Comercial. Com CMV: -14,9%',
      },
    ],
  },
  {
    numero: 5,
    titulo: 'Despesas Fixas Alocadas',
    linhas: [
      {
        codigo: 'L22',
        conta: '(-) Estrutura comercial alocada (rateio % fat.)',
        sinal: '-',
        valor: null,
        pctRL: null,
        tier: 'PENDENTE',
        fase: 'B',
        status: 'detalhe',
        observacao: 'Fase B — aguarda SAP folha comercial',
      },
      {
        codigo: 'L23',
        conta: '(-) Estrutura administrativa alocada',
        sinal: '-',
        valor: null,
        pctRL: null,
        tier: 'PENDENTE',
        fase: 'B',
        status: 'detalhe',
        observacao: 'Fase B — aguarda SAP folha adm',
      },
      {
        codigo: 'L24',
        conta: '(-) Marketing alocado (% fat.)',
        sinal: '-',
        valor: null,
        pctRL: null,
        tier: 'PENDENTE',
        fase: 'B',
        status: 'detalhe',
        observacao: 'Fase B — aguarda SAP/contábil',
      },
      {
        codigo: 'L25',
        conta: '= Resultado Operacional Cliente (EBITDA)',
        sinal: '=',
        valor: null,
        pctRL: null,
        tier: 'PENDENTE',
        fase: 'B',
        status: 'total',
        observacao: 'Disponível na Fase B quando fixas forem integradas',
      },
    ],
  },
  {
    numero: 6,
    titulo: 'Indicadores Derivados (I1–I9)',
    linhas: [
      { codigo: 'I1', conta: 'Margem Bruta % (L13 ÷ L11)', sinal: '=', valor: -14.9, pctRL: null, tier: 'REAL', fase: 'A', status: 'detalhe', observacao: 'NEGATIVA — CMV desbloqueado via ZSD062' },
      { codigo: 'I2', conta: 'Margem Contribuição % (L21 ÷ L11)', sinal: '=', valor: -14.9, pctRL: null, tier: 'SINTETICO', fase: 'A', status: 'detalhe' },
      { codigo: 'I4', conta: 'Custo de Servir % (L14+L15+L17+L18) ÷ L11', sinal: '=', valor: 32.5, pctRL: null, tier: 'SINTETICO', fase: 'A', status: 'detalhe' },
      { codigo: 'I5', conta: 'Verba % Receita (L16 ÷ L11)', sinal: '=', valor: 0.6, pctRL: null, tier: 'REAL', fase: 'A', status: 'detalhe' },
      { codigo: 'I6', conta: 'Inadimplência % (L19 ÷ L11)', sinal: '=', valor: 1.0, pctRL: null, tier: 'SINTETICO', fase: 'A', status: 'detalhe' },
      { codigo: 'I7', conta: 'Devolução % (L4 ÷ L1)', sinal: '=', valor: 21.7, pctRL: null, tier: 'REAL', fase: 'A', status: 'detalhe', observacao: 'CRÍTICO: >10% — anomalia A1' },
      { codigo: 'I8', conta: 'Aging Médio / DSO (dias)', sinal: '=', valor: 52, pctRL: null, tier: 'REAL', fase: 'A', status: 'detalhe', observacao: 'Fonte: debitos_clientes' },
      { codigo: 'I9', conta: 'Score Saúde Financeira (composto I1–I8)', sinal: '=', valor: 32, pctRL: null, tier: 'SINTETICO', fase: 'A', status: 'subtotal', observacao: '<40 = SUBSTITUIR' },
    ],
  },
  {
    numero: 7,
    titulo: 'Veredito Determinístico',
    linhas: [
      {
        codigo: 'V1',
        conta: 'Veredito: SUBSTITUIR — "Margem negativa — cliente destrói valor"',
        sinal: '=',
        valor: null,
        pctRL: null,
        tier: 'REAL',
        fase: 'A',
        status: 'total',
        observacao: 'Regra: MC < 0 → SUBSTITUIR. Veredito determinístico, não LLM.',
      },
    ],
  },
];

// Checklist de desenvolvimento
const STATUS_ITEMS: { feito: boolean; texto: string; fase: 'A' | 'B' | 'aguarda' }[] = [
  { feito: true,  texto: 'Engine Python — cascata 25 linhas (dde_engine.py)',    fase: 'A' },
  { feito: true,  texto: 'Schema banco aprovado (cliente_dre_periodo, venda_itens)', fase: 'A' },
  { feito: true,  texto: 'Golden Master validado — Cliente Referência (GMR-001) ±0,5% por linha', fase: 'A' },
  { feito: false, texto: 'Integração FastAPI — service layer DDE',               fase: 'A' },
  { feito: false, texto: 'Endpoint GET /api/dde/cliente/{cnpj}?ano=X',           fase: 'A' },
  { feito: false, texto: 'Pytest Golden Master automatizado ±0,5%',              fase: 'A' },
];

export default function DDEPage() {
  return (
    <RequireRole minRole="GERENTE">
      <div className="space-y-6 px-3 md:px-4 lg:px-6 pb-12">

        {/* Breadcrumb */}
        <div className="pt-1 flex items-center gap-1.5 text-xs text-gray-400">
          <Link href="/dashboard" className="hover:text-gray-700 transition-colors">Dashboard</Link>
          <span>/</span>
          <span className="text-gray-600">DDE</span>
        </div>

        {/* ---------------------------------------------------------------- */}
        {/* Header principal */}
        {/* ---------------------------------------------------------------- */}
        <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-4">
          <div className="flex-1">
            <div className="flex items-center gap-3 flex-wrap mb-2">
              {/* Ícone */}
              <div
                className="flex-shrink-0 w-10 h-10 rounded-xl flex items-center justify-center"
                style={{ backgroundColor: '#00A85915' }}
              >
                <svg className="w-5 h-5" fill="none" stroke="#00A859" viewBox="0 0 24 24" aria-hidden="true">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
                </svg>
              </div>
              <h1 className="text-2xl font-bold text-gray-900 tracking-tight">DDE</h1>
              <span className="text-sm font-normal text-gray-500">Diagnóstico Demonstrativo do Equilíbrio</span>
            </div>
            <p className="text-sm text-gray-600 leading-relaxed max-w-2xl">
              Cascata P&amp;L por cliente — 7 blocos, 25 linhas — do Faturamento Bruto ao
              EBITDA Cliente. Cada linha classificada como <strong>REAL</strong>, <strong>SINTÉTICO</strong> ou{' '}
              <strong>PENDENTE</strong>. Validação automática ±0,5% contra Golden Master (Cliente Referência GMR-001).
            </p>
          </div>

          {/* Badge "em construção" — discreto, não pulsante */}
          <div className="flex-shrink-0">
            <span className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-bold uppercase tracking-wide bg-orange-50 text-orange-700 border border-orange-200">
              <span className="w-1.5 h-1.5 rounded-full bg-orange-400 flex-shrink-0" />
              Em Construção
            </span>
          </div>
        </div>

        {/* ---------------------------------------------------------------- */}
        {/* Banner obrigatório — Mockup ilustrativo (R8) */}
        {/* ---------------------------------------------------------------- */}
        <PreviewBanner
          mensagem="PREVIEW — dados ilustrativos baseados em Cliente Referência (GMR-001). Integração real em Fase 3a."
          fase="Fase 3a — Maio/2026 (4–6h estimado)"
        />

        {/* ---------------------------------------------------------------- */}
        {/* Grid: Status + Previsão */}
        {/* ---------------------------------------------------------------- */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">

          {/* Sidebar de Status */}
          <div className="bg-white rounded-xl border border-gray-100 shadow-sm p-5">
            <h2 className="text-xs font-bold text-gray-400 uppercase tracking-wider mb-4">
              Status de Desenvolvimento
            </h2>
            <ul className="space-y-3">
              {STATUS_ITEMS.map((s, i) => (
                <li key={i} className="flex items-start gap-3">
                  {s.feito ? (
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
                  <div className="min-w-0 flex-1">
                    <span className={`text-xs leading-snug ${s.feito ? 'text-gray-700' : 'text-amber-700'}`}>
                      {s.texto}
                    </span>
                    <span
                      className={`ml-1.5 text-[10px] font-bold px-1 rounded uppercase ${
                        s.fase === 'A' ? 'bg-green-100 text-green-700' : 'bg-blue-100 text-blue-700'
                      }`}
                    >
                      {s.fase}
                    </span>
                  </div>
                </li>
              ))}
            </ul>

            {/* Barra de progresso */}
            <div className="mt-5 pt-4 border-t border-gray-100">
              <div className="flex items-center justify-between mb-1.5">
                <span className="text-xs font-semibold text-gray-400 uppercase tracking-wide">Progresso Fase A</span>
                <span className="text-xs font-bold text-orange-600">50%</span>
              </div>
              <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
                <div
                  className="h-full rounded-full"
                  style={{ width: '50%', backgroundColor: '#F97316' }}
                />
              </div>
              <p className="text-xs text-gray-400 mt-1.5">3 de 6 etapas concluídas</p>
            </div>
          </div>

          {/* Previsão e Validação */}
          <div className="space-y-4">
            {/* Card Previsão */}
            <div className="bg-white rounded-xl border border-gray-100 shadow-sm p-5">
              <h2 className="text-xs font-bold text-gray-400 uppercase tracking-wider mb-4">
                Previsão de Entrega
              </h2>
              <dl className="space-y-3">
                <div>
                  <dt className="text-[10px] font-semibold text-gray-400 uppercase tracking-wide">Sprint</dt>
                  <dd className="text-sm font-bold text-gray-900 mt-0.5">Fase 3a — Maio/2026</dd>
                </div>
                <div>
                  <dt className="text-[10px] font-semibold text-gray-400 uppercase tracking-wide">Estimativa Dev</dt>
                  <dd className="text-sm text-gray-700 mt-0.5">4 a 6 horas de implementação</dd>
                </div>
                <div>
                  <dt className="text-[10px] font-semibold text-gray-400 uppercase tracking-wide">Desbloqueio</dt>
                  <dd className="text-sm text-gray-700 mt-0.5">
                    Libera <strong className="text-gray-900">Análise Crítica</strong> imediatamente
                  </dd>
                </div>
              </dl>
            </div>

            {/* Card Validação — Cliente Referência GMR-001 */}
            <div
              className="rounded-xl border p-4"
              style={{ backgroundColor: '#F0FDF4', borderColor: '#BBF7D0' }}
            >
              <h2 className="text-xs font-bold text-green-800 uppercase tracking-wider mb-2">
                Cliente Referência (GMR-001) — Validado
              </h2>
              <p className="text-xs text-green-700 leading-snug mb-3">
                Cascata calibrada contra Golden Master manual. Tolerância ±0,5% por linha.
              </p>
              <ul className="space-y-1.5 text-xs text-green-800">
                <li className="flex items-center gap-2">
                  <span className="w-1.5 h-1.5 rounded-full bg-green-500 flex-shrink-0" />
                  L1 = R$ 1.076.343 (Fat. bruto)
                </li>
                <li className="flex items-center gap-2">
                  <span className="w-1.5 h-1.5 rounded-full bg-green-500 flex-shrink-0" />
                  L11 = R$ 842.321 (RL Comercial)
                </li>
                <li className="flex items-center gap-2">
                  <span className="w-1.5 h-1.5 rounded-full bg-green-500 flex-shrink-0" />
                  L14 = R$ 185.834 (Frete CT-e)
                </li>
                <li className="flex items-center gap-2">
                  <span className="w-1.5 h-1.5 rounded-full bg-red-400 flex-shrink-0" />
                  L21 = -R$ 125.961 (MC negativa)
                </li>
                <li className="flex items-center gap-2">
                  <span className="w-1.5 h-1.5 rounded-full bg-green-500 flex-shrink-0" />
                  Veredito: SUBSTITUIR (regra determinística)
                </li>
              </ul>
            </div>
          </div>
        </div>

        {/* ---------------------------------------------------------------- */}
        {/* Cascata P&L — Tabela principal */}
        {/* ---------------------------------------------------------------- */}
        <div className="bg-white rounded-xl border border-gray-100 shadow-sm p-5">
          <div className="flex flex-wrap items-center justify-between gap-3 mb-1">
            <div>
              <h2 className="text-sm font-bold text-gray-900">
                Demonstração de Resultado — Cascata P&amp;L
              </h2>
              <p className="text-xs text-gray-500 mt-0.5">
                7 blocos · 25 linhas · Ano 2025 · Cliente Referência (GMR-001) — ilustrativo
              </p>
            </div>
            {/* Badge mockup — segundo ponto de sinalização R8 */}
            <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold uppercase text-amber-700 bg-amber-50 border border-amber-200">
              Mockup ilustrativo
            </span>
          </div>

          <CascataPL blocos={CASCATA_MOCKUP} showTier showFase />
        </div>

        {/* ---------------------------------------------------------------- */}
        {/* Decisões L3 pendentes */}
        {/* ---------------------------------------------------------------- */}
        <div className="bg-white rounded-xl border border-gray-100 shadow-sm p-5">
          <h2 className="text-xs font-bold text-gray-400 uppercase tracking-wider mb-4">
            Decisões L3 Pendentes (Leandro Aprova)
          </h2>
          <div className="space-y-3">
            {[
              { id: 'D1', titulo: 'Persistir 4 campos do Sales Hunter no Cliente', detalhe: 'desc_comercial_pct, desc_financeiro_pct, total_bonificacao, ipi_total — sem isso L7-L9 vazias', urgencia: 'alta' },
              { id: 'D3', titulo: 'Linhas de imposto sem dado real: NULL vs alíquota sintética', detalhe: 'Recomendação: NULL — DDE parcial honesta > inventada', urgencia: 'media' },
              { id: 'D5', titulo: 'produtos.comissao_pct é comissão vendedor ou rebate cliente?', detalhe: 'Afeta L18 vs L15. Confirmar com SAP.', urgencia: 'media' },
              { id: 'D6', titulo: 'Baixar RelatorioDeMargemPorProduto — tem custo unitário?', detalhe: 'Se sim, desbloqueia CMV (L12) na Fase A. ZSD062 já confirmado via Golden Master.', urgencia: 'resolvido' },
            ].map((d) => (
              <div
                key={d.id}
                className={`flex items-start gap-3 px-3 py-2.5 rounded-lg ${
                  d.urgencia === 'resolvido' ? 'bg-green-50 border border-green-100' :
                  d.urgencia === 'alta' ? 'bg-amber-50 border border-amber-200' :
                  'bg-gray-50 border border-gray-200'
                }`}
              >
                <span
                  className={`flex-shrink-0 text-xs font-bold px-1.5 py-0.5 rounded mt-0.5 ${
                    d.urgencia === 'resolvido' ? 'bg-green-100 text-green-700' :
                    d.urgencia === 'alta' ? 'bg-amber-100 text-amber-700' :
                    'bg-gray-200 text-gray-600'
                  }`}
                >
                  {d.id}
                </span>
                <div className="min-w-0">
                  <p className={`text-xs font-semibold ${d.urgencia === 'resolvido' ? 'text-green-800' : 'text-gray-800'}`}>
                    {d.titulo}
                    {d.urgencia === 'resolvido' && (
                      <span className="ml-2 text-[10px] font-bold text-green-600">RESOLVIDO</span>
                    )}
                  </p>
                  <p className="text-xs text-gray-500 mt-0.5">{d.detalhe}</p>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Rodapé */}
        <p className="text-xs text-gray-400">
          DDE v1.1 — Spec: SPEC_DDE_CASCATA_REAL.md v1.0 · Motor Python pronto (dde_engine.py) ·
          Integração FastAPI em desenvolvimento (Fase 3a) ·
          Esta página é preview de roadmap para apresentação interna — dados ilustrativos.
        </p>

      </div>
    </RequireRole>
  );
}
