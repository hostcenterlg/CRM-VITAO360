'use client';

import Link from 'next/link';
import { RequireRole } from '@/components/auth';

// ---------------------------------------------------------------------------
// DDE — Demonstração de Desempenho Econômico
// Página explicativa honesta. Nenhum dado financeiro fabricado (R8).
// Spec: docs/specs/cowork/SPEC_DDE_CASCATA_REAL.md
// Rebuild: BRIEFING_REBUILD_DDE_ANALISE_CRITICA.md — KILO squad 29/Abr/2026
// ---------------------------------------------------------------------------

// Estrutura da cascata: blocos e linhas com status de disponibilidade
type LinhaStatus = 'disponivel' | 'pendente' | 'externo' | 'bloqueado' | 'aberto';

interface LinhaCascata {
  codigo: string;
  conta: string;
  sinal: '+' | '-' | '=';
  status: LinhaStatus;
  fonte: string;
}

interface BlocoCascata {
  numero: number;
  titulo: string;
  linhas: LinhaCascata[];
}

const BLOCOS: BlocoCascata[] = [
  {
    numero: 1,
    titulo: 'Receita Bruta',
    linhas: [
      { codigo: 'L1',  conta: 'Faturamento bruto a tabela',  sinal: '+', status: 'disponivel', fonte: 'Sales Hunter' },
      { codigo: 'L2',  conta: 'IPI sobre vendas',            sinal: '+', status: 'pendente',   fonte: 'SH — campo existe, falta persistir (D1)' },
      { codigo: 'L3',  conta: '= Receita Bruta com IPI',     sinal: '=', status: 'pendente',   fonte: 'Calculado (aguarda L2)' },
    ],
  },
  {
    numero: 2,
    titulo: 'Deduções da Receita',
    linhas: [
      { codigo: 'L4',  conta: '(-) Devoluções',              sinal: '-', status: 'disponivel', fonte: 'Sales Hunter' },
      { codigo: 'L5',  conta: '(-) Desconto comercial',      sinal: '-', status: 'pendente',   fonte: 'SH — desc_comercial_pct (D1)' },
      { codigo: 'L6',  conta: '(-) Desconto financeiro',     sinal: '-', status: 'pendente',   fonte: 'SH — desc_financeiro_pct (D1)' },
      { codigo: 'L7',  conta: '(-) Bonificações',            sinal: '-', status: 'pendente',   fonte: 'SH — total_bonificacao (D1)' },
      { codigo: 'L8',  conta: '(-) IPI faturado',            sinal: '-', status: 'pendente',   fonte: 'SH — ipi_total (D1)' },
      { codigo: 'L9',  conta: '(-) ICMS',                    sinal: '-', status: 'externo',    fonte: 'SAP módulo fiscal — Fase B' },
      { codigo: 'L10', conta: '(-) PIS / COFINS / ICMS-ST',  sinal: '-', status: 'externo',    fonte: 'SAP fiscal — Fase B' },
      { codigo: 'L11', conta: '= Receita Líquida',           sinal: '=', status: 'pendente',   fonte: 'Parcial Fase A (sem impostos)' },
    ],
  },
  {
    numero: 3,
    titulo: 'CMV — Custo dos Produtos Vendidos',
    linhas: [
      { codigo: 'L12', conta: '(-) CMV',                     sinal: '-', status: 'externo',    fonte: 'SAP / Sales Hunter (D6)' },
      { codigo: 'L13', conta: '= Margem Bruta',              sinal: '=', status: 'bloqueado',  fonte: 'Bloqueado — depende de L12' },
    ],
  },
  {
    numero: 4,
    titulo: 'Despesas Variáveis do Cliente',
    linhas: [
      { codigo: 'L14', conta: '(-) Frete CT-e',              sinal: '-', status: 'pendente',   fonte: 'Schema pronto — falta parser upload' },
      { codigo: 'L15', conta: '(-) Comissão',                sinal: '-', status: 'pendente',   fonte: 'Calculado sobre RL' },
      { codigo: 'L16', conta: '(-) Verbas',                  sinal: '-', status: 'pendente',   fonte: 'Schema pronto — falta parser upload' },
      { codigo: 'L17', conta: '(-) Promotor PDV',            sinal: '-', status: 'pendente',   fonte: 'Schema pronto — falta parser upload' },
      { codigo: 'L18', conta: '(-) Rebate',                  sinal: '-', status: 'aberto',     fonte: 'Decisão pendente D5 — rebate ou comissão vendedor?' },
      { codigo: 'L19', conta: '(-) Inadimplência',           sinal: '-', status: 'disponivel', fonte: 'debitos_clientes — aging × prob_perda' },
      { codigo: 'L20', conta: '(-) Custo financeiro',        sinal: '-', status: 'pendente',   fonte: 'Calculado — aging médio × CDI × valor em aberto' },
      { codigo: 'L21', conta: '= Margem de Contribuição',    sinal: '=', status: 'pendente',   fonte: 'Parcial Fase A' },
    ],
  },
  {
    numero: 5,
    titulo: 'Despesas Fixas Alocadas',
    linhas: [
      { codigo: 'L22', conta: '(-) Estrutura comercial alocada', sinal: '-', status: 'externo', fonte: 'SAP folha comercial — Fase B' },
      { codigo: 'L23', conta: '(-) Estrutura administrativa',    sinal: '-', status: 'externo', fonte: 'SAP folha adm — Fase B' },
      { codigo: 'L24', conta: '(-) Marketing alocado',           sinal: '-', status: 'externo', fonte: 'SAP / contábil — Fase B' },
      { codigo: 'L25', conta: '= Resultado Operacional (EBITDA)', sinal: '=', status: 'externo', fonte: 'Disponível na Fase B' },
    ],
  },
  {
    numero: 6,
    titulo: 'Indicadores Derivados e Score',
    linhas: [
      { codigo: 'I1–I8', conta: '8 indicadores compostos (margem, devolução, inadimpl., comissão, frete, verba, aging, ciclo)', sinal: '=', status: 'pendente', fonte: 'Calculados pelo engine Python após L1–L21' },
      { codigo: 'I9',    conta: 'Score Saúde Financeira (0–100)',                                                                sinal: '=', status: 'pendente', fonte: 'Composto de I1–I8' },
    ],
  },
  {
    numero: 7,
    titulo: 'Veredito Determinístico',
    linhas: [
      { codigo: 'V1', conta: 'Veredito: SAUDÁVEL / REVISAR / RENEGOCIAR / SUBSTITUIR / ALERTA_CRÉDITO', sinal: '=', status: 'pendente', fonte: '92 regras Python — determinístico, não LLM' },
    ],
  },
];

// Configuração visual por status
const STATUS_CONFIG: Record<LinhaStatus, { label: string; dot: string; text: string; bg: string; border: string }> = {
  disponivel: { label: 'Disponível',  dot: 'bg-green-500',  text: 'text-green-700',  bg: 'bg-green-50',  border: 'border-green-200' },
  pendente:   { label: 'Pendente',    dot: 'bg-yellow-400', text: 'text-yellow-700', bg: 'bg-yellow-50', border: 'border-yellow-200' },
  externo:    { label: 'Externo',     dot: 'bg-gray-400',   text: 'text-gray-500',   bg: 'bg-gray-50',   border: 'border-gray-200' },
  bloqueado:  { label: 'Bloqueado',   dot: 'bg-red-400',    text: 'text-red-600',    bg: 'bg-red-50',    border: 'border-red-200' },
  aberto:     { label: 'Em aberto',   dot: 'bg-blue-400',   text: 'text-blue-600',   bg: 'bg-blue-50',   border: 'border-blue-200' },
};

// Ícone de sinal da linha
function SinalCell({ sinal }: { sinal: '+' | '-' | '=' }) {
  if (sinal === '+') return <span className="font-mono text-green-600 font-bold">+</span>;
  if (sinal === '-') return <span className="font-mono text-red-500 font-bold">−</span>;
  return <span className="font-mono text-gray-400">=</span>;
}

// Pill de status
function StatusPill({ status }: { status: LinhaStatus }) {
  const cfg = STATUS_CONFIG[status];
  return (
    <span className={`inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-xs font-semibold ${cfg.bg} ${cfg.border} border ${cfg.text} whitespace-nowrap`}>
      <span className={`w-1.5 h-1.5 rounded-full flex-shrink-0 ${cfg.dot}`} />
      {cfg.label}
    </span>
  );
}

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
              Responde: <strong>&quot;Esse cliente dá lucro ou prejuízo para a Vitao?&quot;</strong>
            </p>
          </div>
          <div className="flex-shrink-0">
            <span className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-bold uppercase tracking-wide bg-orange-50 text-orange-700 border border-orange-200">
              <span className="w-1.5 h-1.5 rounded-full bg-orange-400 flex-shrink-0" />
              Em Construção
            </span>
          </div>
        </div>

        {/* O QUE É */}
        <div className="bg-white shadow-sm border border-gray-200 rounded-xl p-5">
          <h2 className="text-sm font-bold text-gray-900 mb-3">O que é o DDE</h2>
          <p className="text-sm text-gray-700 leading-relaxed">
            O DDE é a cascata P&amp;L individualizada por cliente. Cada linha tem um dado <strong>rastreável a uma
            fonte real</strong> — Sales Hunter, SAP, LOG de frete, LOG de verbas. Nenhum valor é inventado.
          </p>
          <p className="text-sm text-gray-700 leading-relaxed mt-2">
            A cascata percorre: Receita Bruta → Deduções → CMV → Despesas Variáveis → Rateio de Fixas →
            Resultado Operacional. O resultado final é um <strong>Veredito determinístico</strong> (SAUDÁVEL,
            REVISAR, RENEGOCIAR, SUBSTITUIR) calculado por motor Python com 92 regras — sem inteligência
            artificial no caminho crítico.
          </p>
          <div className="mt-4 p-3 bg-blue-50 border border-blue-200 rounded-lg">
            <p className="text-xs font-semibold text-blue-800 mb-1">Onde vai aparecer</p>
            <p className="text-xs text-blue-700 leading-snug">
              O DDE não é uma página independente. Vai aparecer como aba <strong>&quot;Análise&quot;</strong> dentro
              do detalhe de cada cliente (<code className="font-mono bg-blue-100 px-1 rounded">/clientes/[cnpj]</code>).
              Disponível apenas para clientes dos canais <strong>Direto</strong> e <strong>Indireto</strong>
              {' '}(e Food Service quando com dados estruturados). Canais Interno, Farma, Body e Digital não têm
              massa de dados suficiente para a cascata.
            </p>
          </div>
        </div>

        {/* ESTRUTURA DA CASCATA */}
        <div className="bg-white shadow-sm border border-gray-200 rounded-xl p-5">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-sm font-bold text-gray-900">Estrutura da Cascata — 7 Blocos, 25 Linhas</h2>
          </div>

          {/* Legenda */}
          <div className="flex flex-wrap gap-3 mb-5 pb-4 border-b border-gray-100">
            {(Object.entries(STATUS_CONFIG) as [LinhaStatus, typeof STATUS_CONFIG[LinhaStatus]][]).map(([key, cfg]) => (
              <span key={key} className="inline-flex items-center gap-1.5 text-xs text-gray-600">
                <span className={`w-2 h-2 rounded-full flex-shrink-0 ${cfg.dot}`} />
                {cfg.label}
              </span>
            ))}
          </div>

          <div className="space-y-5">
            {BLOCOS.map((bloco) => (
              <div key={bloco.numero}>
                <div className="flex items-center gap-2 mb-2">
                  <span className="text-xs font-bold text-gray-400 uppercase tracking-wider">
                    Bloco {bloco.numero}
                  </span>
                  <span className="text-xs font-semibold text-gray-700">{bloco.titulo}</span>
                </div>
                <div className="divide-y divide-gray-50 border border-gray-100 rounded-lg overflow-hidden">
                  {bloco.linhas.map((linha) => {
                    const cfg = STATUS_CONFIG[linha.status];
                    const isTotal = linha.sinal === '=';
                    return (
                      <div
                        key={linha.codigo}
                        className={`flex items-start gap-3 px-3 py-2.5 ${isTotal ? 'bg-gray-50' : 'bg-white'}`}
                      >
                        <span className="font-mono text-xs text-gray-400 w-8 flex-shrink-0 pt-0.5">{linha.codigo}</span>
                        <span className="w-4 flex-shrink-0 pt-0.5 text-sm">
                          <SinalCell sinal={linha.sinal} />
                        </span>
                        <div className="flex-1 min-w-0">
                          <span className={`text-xs ${isTotal ? 'font-semibold text-gray-800' : 'text-gray-700'}`}>
                            {linha.conta}
                          </span>
                          <p className={`text-xs mt-0.5 ${cfg.text}`}>{linha.fonte}</p>
                        </div>
                        <div className="flex-shrink-0 pt-0.5">
                          <StatusPill status={linha.status} />
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* ROADMAP DE DADOS */}
        <div className="bg-white shadow-sm border border-gray-200 rounded-xl p-5">
          <h2 className="text-sm font-bold text-gray-900 mb-4">Roadmap de Dados</h2>
          <div className="space-y-4">

            <div className="flex gap-3">
              <div className="flex flex-col items-center">
                <span className="w-6 h-6 rounded-full bg-green-100 border-2 border-green-400 flex items-center justify-center flex-shrink-0">
                  <span className="w-2 h-2 rounded-full bg-green-500" />
                </span>
                <div className="flex-1 w-px bg-gray-200 mt-1" />
              </div>
              <div className="pb-4">
                <p className="text-sm font-semibold text-gray-800">Fase A — Cascata Comercial (próximo passo)</p>
                <p className="text-xs text-gray-600 mt-1 leading-relaxed">
                  Dados do Sales Hunter: Faturamento, Devoluções e Inadimplência já disponíveis no banco.
                  Pendentes: persistir 4 campos de desconto/bonificação/IPI (decisão D1) e parsers de upload
                  para frete, verbas e promotor.
                </p>
                <p className="text-xs text-gray-500 mt-1">
                  Estimativa: ~5 dias dev após aprovação das decisões D1–D6.
                </p>
              </div>
            </div>

            <div className="flex gap-3">
              <div className="flex flex-col items-center">
                <span className="w-6 h-6 rounded-full bg-gray-100 border-2 border-gray-300 flex items-center justify-center flex-shrink-0">
                  <span className="w-2 h-2 rounded-full bg-gray-400" />
                </span>
                <div className="flex-1 w-px bg-gray-200 mt-1" />
              </div>
              <div className="pb-4">
                <p className="text-sm font-semibold text-gray-600">Fase B — Impostos e CMV (depende SAP)</p>
                <p className="text-xs text-gray-500 mt-1 leading-relaxed">
                  ICMS, PIS, COFINS, ICMS-ST e Custo dos Produtos Vendidos. Depende de acesso ao módulo
                  fiscal do SAP. Sem esses dados, a Margem Bruta (L13) permanece bloqueada.
                </p>
              </div>
            </div>

            <div className="flex gap-3">
              <span className="w-6 h-6 rounded-full bg-gray-100 border-2 border-gray-300 flex items-center justify-center flex-shrink-0">
                <span className="w-2 h-2 rounded-full bg-gray-400" />
              </span>
              <div>
                <p className="text-sm font-semibold text-gray-600">Fase C — Sell-out e Ruptura (futuro)</p>
                <p className="text-xs text-gray-500 mt-1 leading-relaxed">
                  Dados de PDV: sell-out, ruptura e giro de estoque. Depende de integração POS ainda não
                  contratada.
                </p>
              </div>
            </div>

          </div>
        </div>

        {/* DECISÕES L3 PENDENTES */}
        <div className="bg-white shadow-sm border border-gray-200 rounded-xl p-5">
          <h2 className="text-sm font-bold text-gray-900 mb-1">Decisões Pendentes (L3 — Leandro Aprova)</h2>
          <p className="text-xs text-gray-600 mb-4">
            Estas decisões precisam ser tomadas antes de iniciar a Fase A. Cada uma desbloqueia linhas
            específicas da cascata.
          </p>
          <div className="space-y-2">
            {[
              { id: 'D1', desc: 'Persistir 4 campos do Sales Hunter por cliente', detalhe: 'desc_comercial_pct, desc_financeiro_pct, total_bonificacao, ipi_total — desbloqueia L5, L6, L7, L8', urgencia: 'alta' },
              { id: 'D2', desc: 'Criar routes_dde.py com 5 endpoints de API', detalhe: 'Desbloqueia conexão frontend–backend da cascata', urgencia: 'alta' },
              { id: 'D3', desc: 'Impostos sem dado real: NULL honesto ou alíquota sintética?', detalhe: 'Recomendação: NULL — DDE parcial honesta é melhor que cascata com valores fabricados', urgencia: 'media' },
              { id: 'D4', desc: 'Implementar Fase A agora sem esperar SAP?', detalhe: 'Recomendação: GO — entrega valor parcial imediato com dados comerciais disponíveis', urgencia: 'media' },
              { id: 'D5', desc: 'produtos.comissao_pct é comissão do vendedor ou rebate do cliente?', detalhe: 'Afeta classificação de L15 vs L18 — impacto direto no score final', urgencia: 'media' },
              { id: 'D6', desc: 'RelatorioDeMargemPorProduto do Sales Hunter tem custo unitário?', detalhe: 'Se sim, desbloqueia CMV (L12) na Fase A sem depender do SAP', urgencia: 'media' },
            ].map((d) => (
              <div
                key={d.id}
                className={`flex items-start gap-3 px-3 py-2.5 rounded-lg border ${
                  d.urgencia === 'alta' ? 'bg-amber-50 border-amber-200' : 'bg-gray-50 border-gray-200'
                }`}
              >
                <span className={`flex-shrink-0 text-xs font-bold px-1.5 py-0.5 rounded mt-0.5 ${
                  d.urgencia === 'alta' ? 'bg-amber-100 text-amber-700' : 'bg-gray-200 text-gray-600'
                }`}>
                  {d.id}
                </span>
                <div className="min-w-0">
                  <p className="text-xs font-semibold text-gray-800">{d.desc}</p>
                  <p className="text-xs text-gray-500 mt-0.5">{d.detalhe}</p>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* APLICABILIDADE POR CANAL */}
        <div className="bg-white shadow-sm border border-gray-200 rounded-xl p-5">
          <h2 className="text-sm font-bold text-gray-900 mb-3">Aplicabilidade por Canal</h2>
          <p className="text-xs text-gray-600 mb-4">
            O DDE só faz sentido para clientes com massa de dados suficiente: contrato, verba, frete CT-e,
            promotor e volume de vendas estruturado. Forçar a cascata em canais sem esses dados geraria
            linhas vazias sem utilidade analítica.
          </p>
          <div className="divide-y divide-gray-100 border border-gray-100 rounded-lg overflow-hidden">
            {[
              { canal: 'DIRETO',       elegivel: 'sim',    motivo: 'Manu, Larissa, Daiane, Julio — dados comerciais completos' },
              { canal: 'INDIRETO',     elegivel: 'sim',    motivo: 'Distribuidores com contrato e verba formalizados' },
              { canal: 'FOOD SERVICE', elegivel: 'cond',   motivo: 'Somente se tiver dados estruturados de frete e verba' },
              { canal: 'INTERNO',      elegivel: 'nao',    motivo: 'Funcional VITAO — não é cliente externo' },
              { canal: 'FARMA',        elegivel: 'nao',    motivo: 'Sem massa de dados para a cascata completa' },
              { canal: 'BODY',         elegivel: 'nao',    motivo: 'Sem massa de dados para a cascata completa' },
              { canal: 'DIGITAL',      elegivel: 'nao',    motivo: 'E-commerce / B2C — modelo de negócio diferente' },
            ].map((row) => (
              <div key={row.canal} className="flex items-center gap-3 px-3 py-2.5 bg-white">
                <span className="font-mono text-xs font-bold text-gray-700 w-28 flex-shrink-0">{row.canal}</span>
                <span className={`inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-xs font-semibold border flex-shrink-0 ${
                  row.elegivel === 'sim'  ? 'bg-green-50 border-green-200 text-green-700' :
                  row.elegivel === 'cond' ? 'bg-yellow-50 border-yellow-200 text-yellow-700' :
                                           'bg-red-50 border-red-200 text-red-600'
                }`}>
                  {row.elegivel === 'sim' ? 'Sim' : row.elegivel === 'cond' ? 'Condicional' : 'Não'}
                </span>
                <span className="text-xs text-gray-600 leading-snug">{row.motivo}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Rodapé */}
        <p className="text-xs text-gray-400">
          DDE — Spec: SPEC_DDE_CASCATA_REAL.md · Motor Python em desenvolvimento (dde_engine.py) ·
          Integração FastAPI pendente decisões D1–D6 · Rebuild KILO 29/Abr/2026
        </p>

      </div>
    </RequireRole>
  );
}
