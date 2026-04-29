'use client';

import Link from 'next/link';

// ---------------------------------------------------------------------------
// DDE — Diagnostico Demonstrativo do Cliente
// Placeholder demo-quality para apresentacao de roadmap (Missao B9)
// Motor Python ja existe — falta integracao FastAPI + endpoint /api/dde/cliente
// ---------------------------------------------------------------------------

// ---------------------------------------------------------------------------
// Cascata mockup: 7 blocos, 25 linhas
// AVISO: valores sao illustrativos — mockup apenas
// ---------------------------------------------------------------------------

interface CascataLinha {
  codigo: string;
  descricao: string;
  valor: number;
  percentual: number;
  destaque?: boolean;
  recuo?: boolean;
}

interface CascataBloco {
  titulo: string;
  cor: string;
  linhas: CascataLinha[];
}

const CASCATA: CascataBloco[] = [
  {
    titulo: 'Bloco 1 — Receita Bruta',
    cor: '#00B05012',
    linhas: [
      { codigo: 'L1', descricao: 'Vendas Brutas', valor: 1250000, percentual: 100.0, recuo: true },
      { codigo: 'L2', descricao: 'Devoluções e Cancelamentos', valor: -25000, percentual: -2.0, recuo: true },
      { codigo: 'B1', descricao: 'Receita Bruta Ajustada', valor: 1225000, percentual: 98.0, destaque: true },
    ],
  },
  {
    titulo: 'Bloco 2 — Deduções Fiscais',
    cor: '#FFC00012',
    linhas: [
      { codigo: 'L3', descricao: 'PIS/COFINS (9,25%)', valor: -113312, percentual: -9.1, recuo: true },
      { codigo: 'L4', descricao: 'ICMS (8,0% médio)', valor: -98000, percentual: -7.8, recuo: true },
      { codigo: 'L5', descricao: 'ISS / Outras Retenções', valor: -6125, percentual: -0.5, recuo: true },
      { codigo: 'B2', descricao: 'Receita Líquida', valor: 1007563, percentual: 80.6, destaque: true },
    ],
  },
  {
    titulo: 'Bloco 3 — Custo dos Produtos',
    cor: '#FF000010',
    linhas: [
      { codigo: 'L6', descricao: 'CMV — Custo Mercadoria Vendida', valor: -602500, percentual: -48.2, recuo: true },
      { codigo: 'L7', descricao: 'Frete CIF (inbound)', valor: -37500, percentual: -3.0, recuo: true },
      { codigo: 'B3', descricao: 'Margem Bruta', valor: 367563, percentual: 29.4, destaque: true },
    ],
  },
  {
    titulo: 'Bloco 4 — Despesas Variáveis',
    cor: '#FFC00012',
    linhas: [
      { codigo: 'L8', descricao: 'Comissão Consultor (3,0%)', valor: -37500, percentual: -3.0, recuo: true },
      { codigo: 'L9', descricao: 'Frete Outbound (entrega)', valor: -25000, percentual: -2.0, recuo: true },
      { codigo: 'L10', descricao: 'Desconto Comercial', valor: -18750, percentual: -1.5, recuo: true },
      { codigo: 'L11', descricao: 'Bonificações / Degustação', valor: -12500, percentual: -1.0, recuo: true },
      { codigo: 'B4', descricao: 'Margem de Contribuição Bruta', valor: 273813, percentual: 21.9, destaque: true },
    ],
  },
  {
    titulo: 'Bloco 5 — Rateio de Estrutura',
    cor: '#00000008',
    linhas: [
      { codigo: 'L12', descricao: 'Rateio Estrutura Comercial', valor: -31250, percentual: -2.5, recuo: true },
      { codigo: 'L13', descricao: 'Rateio Logística e Armazém', valor: -18750, percentual: -1.5, recuo: true },
      { codigo: 'L14', descricao: 'Rateio TI e Sistemas', valor: -6250, percentual: -0.5, recuo: true },
      { codigo: 'B5', descricao: 'Margem de Contribuição Líquida', valor: 217563, percentual: 17.4, destaque: true },
    ],
  },
  {
    titulo: 'Bloco 6 — Encargos e Financeiro',
    cor: '#FFC00012',
    linhas: [
      { codigo: 'L15', descricao: 'Inadimplência Provisionada (0,8%)', valor: -10000, percentual: -0.8, recuo: true },
      { codigo: 'L16', descricao: 'Custo Financeiro Prazo (1,2%)', valor: -15000, percentual: -1.2, recuo: true },
      { codigo: 'L17', descricao: 'IOF / Tarifas Bancárias', valor: -2500, percentual: -0.2, recuo: true },
      { codigo: 'L18', descricao: 'Desconto Antecipação', valor: -3125, percentual: -0.3, recuo: true },
      { codigo: 'B6', descricao: 'Resultado Operacional', valor: 186938, percentual: 15.0, destaque: true },
    ],
  },
  {
    titulo: 'Bloco 7 — Resultado Final',
    cor: '#00B05018',
    linhas: [
      { codigo: 'L19', descricao: 'Ajuste Devolução Pós-Período', valor: -1250, percentual: -0.1, recuo: true },
      { codigo: 'L20', descricao: 'Créditos de Campanha', valor: 2500, percentual: 0.2, recuo: true },
      { codigo: 'L21', descricao: 'Margem de Contribuição Final', valor: 188188, percentual: 15.1, destaque: true },
      { codigo: 'L22', descricao: 'Margem sobre Receita Bruta', valor: 0, percentual: 15.1, recuo: true },
      { codigo: 'L23', descricao: 'Validação ±0,5% (cliente de referência)', valor: 0, percentual: 0.0, recuo: true },
    ],
  },
];

function fmtValor(v: number): string {
  if (v === 0) return '—';
  return v.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL', maximumFractionDigits: 0 });
}

function fmtPct(v: number): string {
  if (v === 0) return '—';
  return `${v > 0 ? '+' : ''}${v.toFixed(1)}%`;
}

function corValor(v: number): string {
  if (v === 0) return 'text-gray-400';
  return v < 0 ? 'text-red-600' : 'text-gray-900';
}

// ---------------------------------------------------------------------------
// Checklist de status
// ---------------------------------------------------------------------------

interface StatusItem {
  feito: boolean;
  texto: string;
}

const STATUS_ITEMS: StatusItem[] = [
  { feito: true, texto: 'Engine Python — cascata 25 linhas' },
  { feito: true, texto: 'Schema banco aprovado (venda_itens)' },
  { feito: true, texto: 'Algoritmo validado manualmente em cliente de referência' },
  { feito: false, texto: 'Integração FastAPI — service layer' },
  { feito: false, texto: 'Endpoint /api/dde/cliente/{cnpj}' },
  { feito: false, texto: 'Pytest Golden Master ±0,5%' },
];

// ---------------------------------------------------------------------------
// Page
// ---------------------------------------------------------------------------

export default function DDEPage() {
  return (
    <div className="space-y-6 px-3 md:px-4 lg:px-6 pb-10">

      {/* Voltar */}
      <div className="pt-1">
        <Link
          href="/dashboard"
          className="inline-flex items-center gap-1.5 text-xs text-gray-500 hover:text-gray-800 transition-colors min-h-[44px] py-2"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
          </svg>
          Voltar ao Dashboard
        </Link>
      </div>

      {/* Cabecalho */}
      <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-3">
        <div>
          <div className="flex items-center gap-3 flex-wrap">
            <h1 className="text-xl font-bold text-gray-900">DDE</h1>
            <span className="inline-flex items-center px-2.5 py-1 rounded-md text-xs font-bold uppercase tracking-wide bg-orange-100 text-orange-700 border border-orange-200 animate-pulse">
              EM CONSTRUCAO
            </span>
          </div>
          <p className="text-sm text-gray-500 mt-1 leading-snug max-w-xl">
            Diagnostico Demonstrativo do Cliente — cascata de margem P&amp;L cliente-a-cliente,
            25 linhas, 7 blocos, validacao automatica ±0,5% (calibrado em cliente de referência).
          </p>
        </div>
        <div
          className="flex-shrink-0 w-9 h-9 rounded-xl flex items-center justify-center"
          style={{ backgroundColor: '#00B05015' }}
        >
          <svg className="w-5 h-5" fill="none" stroke="#00B050" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
              d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
          </svg>
        </div>
      </div>

      {/* Cards de Status + Previsao */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">

        {/* Card Status */}
        <div className="bg-white rounded-xl border border-gray-100 shadow-sm p-5">
          <h2 className="text-xs font-bold text-gray-500 uppercase tracking-wider mb-3">Status de Desenvolvimento</h2>
          <ul className="space-y-2.5">
            {STATUS_ITEMS.map((s, i) => (
              <li key={i} className="flex items-start gap-2.5">
                {s.feito ? (
                  <span className="mt-0.5 flex-shrink-0 w-4 h-4 rounded-full flex items-center justify-center" style={{ backgroundColor: '#00B05020' }}>
                    <svg className="w-2.5 h-2.5" fill="none" stroke="#00B050" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
                    </svg>
                  </span>
                ) : (
                  <span className="mt-0.5 flex-shrink-0 w-4 h-4 rounded-full flex items-center justify-center bg-amber-50 border border-amber-200">
                    <svg className="w-2.5 h-2.5 text-amber-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5}
                        d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                  </span>
                )}
                <span className={`text-xs leading-snug ${s.feito ? 'text-gray-700' : 'text-amber-700'}`}>
                  {s.texto}
                </span>
              </li>
            ))}
          </ul>
        </div>

        {/* Card Previsao */}
        <div className="bg-white rounded-xl border border-gray-100 shadow-sm p-5">
          <h2 className="text-xs font-bold text-gray-500 uppercase tracking-wider mb-3">Previsao de Entrega</h2>
          <dl className="space-y-3">
            <div>
              <dt className="text-[10px] font-semibold text-gray-400 uppercase tracking-wide">Sprint</dt>
              <dd className="text-sm font-bold text-gray-900 mt-0.5">Fase 3a — Maio / 2026</dd>
            </div>
            <div>
              <dt className="text-[10px] font-semibold text-gray-400 uppercase tracking-wide">Estimativa de dev</dt>
              <dd className="text-sm text-gray-700 mt-0.5">4 a 6 horas de implementacao</dd>
            </div>
            <div>
              <dt className="text-[10px] font-semibold text-gray-400 uppercase tracking-wide">Validacao</dt>
              <dd className="text-sm text-gray-700 mt-0.5">Cliente referência ±0,5% por linha</dd>
            </div>
            <div>
              <dt className="text-[10px] font-semibold text-gray-400 uppercase tracking-wide">Desbloqueio</dt>
              <dd className="text-sm text-gray-700 mt-0.5">
                Libera <span className="font-semibold text-gray-900">Analise Critica</span> imediatamente
              </dd>
            </div>
          </dl>

          {/* Progresso visual */}
          <div className="mt-4">
            <div className="flex items-center justify-between mb-1">
              <span className="text-[10px] font-semibold text-gray-400 uppercase">Progresso</span>
              <span className="text-[10px] font-bold text-orange-600">50%</span>
            </div>
            <div className="h-1.5 bg-gray-100 rounded-full overflow-hidden">
              <div
                className="h-full rounded-full transition-all"
                style={{ width: '50%', backgroundColor: '#F97316' }}
              />
            </div>
            <p className="text-[10px] text-gray-400 mt-1">3 de 6 etapas concluidas</p>
          </div>
        </div>
      </div>

      {/* Preview da Cascata */}
      <div className="bg-white rounded-xl border border-gray-100 shadow-sm p-5">
        <div className="flex items-center justify-between mb-1">
          <h2 className="text-xs font-bold text-gray-500 uppercase tracking-wider">Preview da Cascata P&amp;L</h2>
          <span className="inline-flex items-center px-2 py-0.5 rounded text-[9px] font-semibold uppercase text-amber-700 bg-amber-50 border border-amber-200">
            Mockup ilustrativo — dados reais em breve
          </span>
        </div>
        <p className="text-[11px] text-gray-400 mb-4">
          Cliente de exemplo — valores fictícios para demonstracao do layout.
          Faturamento anual R$ 1,25M (cliente A representativo).
        </p>

        <div className="overflow-x-auto -mx-5">
          <div className="min-w-[560px] px-5">
            <table className="w-full text-xs border-collapse">
              <thead>
                <tr className="border-b border-gray-200">
                  <th className="text-left py-1.5 px-2 text-[10px] font-semibold text-gray-400 uppercase tracking-wide w-10">Cod.</th>
                  <th className="text-left py-1.5 px-2 text-[10px] font-semibold text-gray-400 uppercase tracking-wide">Descricao</th>
                  <th className="text-right py-1.5 px-2 text-[10px] font-semibold text-gray-400 uppercase tracking-wide w-32">Valor (R$)</th>
                  <th className="text-right py-1.5 px-2 text-[10px] font-semibold text-gray-400 uppercase tracking-wide w-16">%</th>
                </tr>
              </thead>
              <tbody>
                {CASCATA.map((bloco) => (
                  <>
                    {/* Header do bloco */}
                    <tr
                      key={`bloco-${bloco.titulo}`}
                      style={{ backgroundColor: bloco.cor }}
                    >
                      <td colSpan={4} className="py-1.5 px-2 text-[10px] font-bold text-gray-700 uppercase tracking-wide">
                        {bloco.titulo}
                      </td>
                    </tr>
                    {/* Linhas do bloco */}
                    {bloco.linhas.map((linha) => (
                      <tr
                        key={linha.codigo}
                        className={`border-b border-gray-50 transition-colors hover:bg-gray-50 ${
                          linha.destaque ? 'font-semibold' : ''
                        }`}
                        style={linha.destaque ? { backgroundColor: bloco.cor } : undefined}
                      >
                        <td className={`py-1.5 px-2 font-mono text-[10px] ${linha.destaque ? 'text-gray-600 font-bold' : 'text-gray-300'}`}>
                          {linha.codigo}
                        </td>
                        <td className={`py-1.5 px-2 ${linha.recuo ? 'pl-5' : 'pl-2'} ${linha.destaque ? 'text-gray-900' : 'text-gray-600'}`}>
                          {linha.descricao}
                        </td>
                        <td className={`py-1.5 px-2 text-right font-mono ${linha.destaque ? 'font-bold text-gray-900' : corValor(linha.valor)}`}>
                          {fmtValor(linha.valor)}
                        </td>
                        <td className={`py-1.5 px-2 text-right font-mono ${linha.destaque ? 'font-bold text-gray-900' : corValor(linha.percentual)}`}>
                          {fmtPct(linha.percentual)}
                        </td>
                      </tr>
                    ))}
                  </>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        <div className="mt-4 flex items-center gap-2 text-[10px] text-gray-400">
          <svg className="w-3.5 h-3.5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
              d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          Valores totalmente ilustrativos. O motor real usa dados SAP + Mercos por CNPJ.
          Validacao automatica em cada linha com tolerancia ±0,5% (R9).
        </div>
      </div>

      {/* Nota de rodape */}
      <p className="text-[10px] text-gray-400">
        DDE v1.0 — Motor Python pronto. Integracao FastAPI em desenvolvimento.
        Esta pagina e uma preview de roadmap para apresentacao interna.
      </p>

    </div>
  );
}
