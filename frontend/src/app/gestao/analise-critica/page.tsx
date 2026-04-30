'use client';

import Link from 'next/link';
import { RequireRole } from '@/components/auth';

// ---------------------------------------------------------------------------
// Análise Crítica do Cliente
// Página explicativa honesta. Nenhum dado financeiro fabricado (R8).
// Spec: SPEC_FEATURE_ANALISE_CRITICA_CRM_VITAO360.md
// Rebuild: BRIEFING_REBUILD_DDE_ANALISE_CRITICA.md — KILO squad 29/Abr/2026
// ---------------------------------------------------------------------------

// Camadas da arquitetura
const CAMADAS = [
  {
    num: 6,
    label: 'Interface',
    desc: 'Esta aba — exibe score, veredito, anomalias e ações priorizadas por cliente.',
    status: 'bloqueado' as const,
    detalhe: 'Aguarda camada 4',
  },
  {
    num: 5,
    label: 'LLM — Resumo CEO',
    desc: 'Gerado após o cálculo. Explica em linguagem natural o que a engine calculou. Não inventa, não substitui os dados.',
    status: 'bloqueado' as const,
    detalhe: 'Aguarda camada 4',
  },
  {
    num: 4,
    label: 'Engine de Regras (DDE)',
    desc: 'Motor Python determinístico. 92 regras. Calcula score, veredito e anomalias a partir dos dados do banco. Próximo passo.',
    status: 'pendente' as const,
    detalhe: 'Fase A — ~5 dias dev',
  },
  {
    num: 3,
    label: 'PostgreSQL — 9 tabelas',
    desc: 'Modelo de verdade. Armazena dados processados prontos para o engine. Parcialmente populado.',
    status: 'parcial' as const,
    detalhe: 'Schema definido, ingestão parcial',
  },
  {
    num: 2,
    label: 'Pipeline de Ingestão',
    desc: 'ETL mensal + diário. Processa Sales Hunter, SAP, Deskrio, Mercos e logs de frete/verbas.',
    status: 'parcial' as const,
    detalhe: 'Sales Hunter ativo — SAP, frete, verbas pendentes',
  },
  {
    num: 1,
    label: 'Fontes de Dados',
    desc: '8 fontes: SAP, Sales Hunter, Mercos, Deskrio, LOG Frete, LOG Verbas, LOG Despesas, Upload CFO.',
    status: 'parcial' as const,
    detalhe: '3 de 8 fontes integradas',
  },
];

const STATUS_CAMADA = {
  bloqueado: { bg: 'bg-red-50',    border: 'border-red-200',    text: 'text-red-600',    badge: 'bg-red-100 text-red-700',    label: 'Bloqueado' },
  pendente:  { bg: 'bg-yellow-50', border: 'border-yellow-200', text: 'text-yellow-700', badge: 'bg-yellow-100 text-yellow-800', label: 'Pendente' },
  parcial:   { bg: 'bg-blue-50',   border: 'border-blue-200',   text: 'text-blue-700',   badge: 'bg-blue-100 text-blue-700',   label: 'Parcial' },
  pronto:    { bg: 'bg-green-50',  border: 'border-green-200',  text: 'text-green-700',  badge: 'bg-green-100 text-green-700', label: 'Pronto' },
};

// Dependências da feature
const DEPENDENCIAS = [
  { feito: false, desc: 'DDE Engine (Fase A)', detalhe: 'Pré-requisito absoluto — sem ele não há score nem veredito' },
  { feito: false, desc: '5 endpoints API — routes_dde.py', detalhe: 'GET /dde/cliente/{cnpj}, POST /dde/recalcular, GET /dde/score/{cnpj}, GET /dde/anomalias/{cnpj}, GET /dde/acoes/{cnpj}' },
  { feito: false, desc: 'Parser uploads CFO', detalhe: 'Frete CT-e, verbas efetivadas, contratos, despesas promotor — desbloqueia L14–L17' },
  { feito: true,  desc: 'Schema PostgreSQL — definido', detalhe: '9 tabelas criadas: clientes, vendas, venda_itens, debitos_clientes, cliente_dre_periodo e mais' },
  { feito: true,  desc: 'Motor de regras base', detalhe: '92 regras existentes no código Python — precisam ser conectadas à camada de API' },
  { feito: true,  desc: 'Sinaleiro service', detalhe: 'Serviço de alertas já existe e pode alimentar anomalias da análise crítica' },
];

// Vereditos possíveis
const VEREDITOS = [
  { label: 'SAUDAVEL',        cor: 'bg-green-100 text-green-800 border-green-300',   regra: 'Margem de contribuição > 15% e crédito em dia' },
  { label: 'REVISAR',         cor: 'bg-yellow-100 text-yellow-800 border-yellow-300', regra: 'Margem de contribuição entre 5% e 15%' },
  { label: 'RENEGOCIAR',      cor: 'bg-orange-100 text-orange-800 border-orange-300', regra: 'Margem de contribuição abaixo de 5%' },
  { label: 'SUBSTITUIR',      cor: 'bg-red-100 text-red-800 border-red-300',          regra: 'Margem de contribuição negativa — cliente destrói valor' },
  { label: 'ALERTA_CREDITO',  cor: 'bg-purple-100 text-purple-800 border-purple-300', regra: 'Margem aceitável, mas aging superior a 90 dias' },
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
              <span className="text-sm font-normal text-gray-500">Score + Veredito + Anomalias + Ações por cliente</span>
            </div>
            <p className="text-sm text-gray-700 leading-relaxed max-w-2xl">
              Transforma 30–45 minutos de análise manual em <strong>decisão em segundos</strong>.
              Para cada cliente: score 0–100, veredito automático, anomalias detectadas e ações priorizadas
              com impacto estimado.
            </p>
          </div>
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

        {/* O QUE É */}
        <div className="bg-white shadow-sm border border-gray-200 rounded-xl p-5">
          <h2 className="text-sm font-bold text-gray-900 mb-3">O que é a Análise Crítica</h2>
          <p className="text-sm text-gray-700 leading-relaxed">
            A Análise Crítica é a camada de <strong>decisão comercial</strong> do CRM. Para cada cliente,
            combina quatro elementos em uma visão única:
          </p>
          <ul className="mt-3 space-y-2">
            <li className="flex items-start gap-2.5 text-sm text-gray-700">
              <span className="w-1.5 h-1.5 rounded-full bg-gray-400 flex-shrink-0 mt-2" />
              <span><strong>DDE (cascata P&amp;L):</strong> os números — receita, custo, margem, frete, verba.</span>
            </li>
            <li className="flex items-start gap-2.5 text-sm text-gray-700">
              <span className="w-1.5 h-1.5 rounded-full bg-gray-400 flex-shrink-0 mt-2" />
              <span><strong>Diagnóstico automático:</strong> as anomalias — o que está fora do padrão e por quê.</span>
            </li>
            <li className="flex items-start gap-2.5 text-sm text-gray-700">
              <span className="w-1.5 h-1.5 rounded-full bg-gray-400 flex-shrink-0 mt-2" />
              <span><strong>Veredito determinístico:</strong> a decisão — SAUDÁVEL, REVISAR, RENEGOCIAR, SUBSTITUIR.</span>
            </li>
            <li className="flex items-start gap-2.5 text-sm text-gray-700">
              <span className="w-1.5 h-1.5 rounded-full bg-gray-400 flex-shrink-0 mt-2" />
              <span><strong>Ações priorizadas:</strong> o que fazer, com impacto estimado em resultado.</span>
            </li>
          </ul>
          <div className="mt-4 p-3 bg-gray-50 border border-gray-200 rounded-lg">
            <p className="text-xs text-gray-600 leading-snug">
              O veredito é calculado por motor Python com 92 regras — não por IA generativa. A IA entra
              apenas na geração do <strong>Resumo CEO</strong> (PDF de 1 página), explicando em linguagem
              natural o que a engine calculou. Ela não inventa e não substitui os dados.
            </p>
          </div>
        </div>

        {/* ARQUITETURA EM 6 CAMADAS */}
        <div className="bg-white shadow-sm border border-gray-200 rounded-xl p-5">
          <h2 className="text-sm font-bold text-gray-900 mb-1">Arquitetura em 6 Camadas</h2>
          <p className="text-xs text-gray-600 mb-4">
            A Análise Crítica é a camada mais alta. As camadas inferiores precisam estar prontas antes
            que ela possa funcionar. Status atual: camadas 1–3 parcialmente prontas. Camada 4 é o
            próximo passo obrigatório.
          </p>
          <div className="space-y-2">
            {CAMADAS.map((camada) => {
              const cfg = STATUS_CAMADA[camada.status];
              return (
                <div key={camada.num} className={`flex items-start gap-3 px-4 py-3 rounded-lg border ${cfg.bg} ${cfg.border}`}>
                  <span className="flex-shrink-0 w-6 h-6 rounded-full bg-white border border-gray-300 flex items-center justify-center text-xs font-bold text-gray-600 mt-0.5">
                    {camada.num}
                  </span>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className={`text-sm font-semibold ${cfg.text}`}>{camada.label}</span>
                      <span className={`text-xs px-1.5 py-0.5 rounded font-semibold ${cfg.badge}`}>
                        {cfg.label}
                      </span>
                    </div>
                    <p className="text-xs text-gray-600 mt-1 leading-snug">{camada.desc}</p>
                    <p className={`text-xs mt-0.5 font-medium ${cfg.text}`}>{camada.detalhe}</p>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* O QUE VAI APARECER */}
        <div className="bg-white shadow-sm border border-gray-200 rounded-xl p-5">
          <h2 className="text-sm font-bold text-gray-900 mb-4">O que vai aparecer ao abrir um cliente</h2>
          <div className="space-y-4">

            <div className="flex gap-3">
              <span className="flex-shrink-0 w-6 h-6 rounded-full bg-gray-100 border border-gray-300 flex items-center justify-center text-xs font-bold text-gray-600">1</span>
              <div>
                <p className="text-sm font-semibold text-gray-800">Score (0–100) com gauge visual</p>
                <p className="text-xs text-gray-600 mt-1 leading-relaxed">
                  Composto de 8 indicadores: margem de contribuição, taxa de devolução, inadimplência,
                  comissão do representante, frete sobre receita líquida, verbas, aging médio e ciclo
                  financeiro. Cada indicador tem peso proporcional ao impacto na margem.
                </p>
              </div>
            </div>

            <div className="flex gap-3">
              <span className="flex-shrink-0 w-6 h-6 rounded-full bg-gray-100 border border-gray-300 flex items-center justify-center text-xs font-bold text-gray-600">2</span>
              <div>
                <p className="text-sm font-semibold text-gray-800">Veredito automático</p>
                <p className="text-xs text-gray-600 mt-1 mb-2 leading-relaxed">
                  Calculado por regras Python determinísticas — não por IA. Cinco possibilidades:
                </p>
                <div className="flex flex-wrap gap-2">
                  {VEREDITOS.map((v) => (
                    <div key={v.label} className={`px-2.5 py-1.5 rounded-lg border text-xs ${v.cor}`}>
                      <span className="font-bold">{v.label}</span>
                      <span className="ml-2 font-normal opacity-80">{v.regra}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            <div className="flex gap-3">
              <span className="flex-shrink-0 w-6 h-6 rounded-full bg-gray-100 border border-gray-300 flex items-center justify-center text-xs font-bold text-gray-600">3</span>
              <div>
                <p className="text-sm font-semibold text-gray-800">Anomalias detectadas (top 3)</p>
                <p className="text-xs text-gray-600 mt-1 leading-relaxed">
                  Regras determinísticas que identificam desvios: verba caiu sem justificativa, frete sem
                  CT-e correspondente, margem negativa, devolução acima do limite, aging elevado, comissão
                  acima do padrão da carteira, entre outros.
                </p>
              </div>
            </div>

            <div className="flex gap-3">
              <span className="flex-shrink-0 w-6 h-6 rounded-full bg-gray-100 border border-gray-300 flex items-center justify-center text-xs font-bold text-gray-600">4</span>
              <div>
                <p className="text-sm font-semibold text-gray-800">Ações priorizadas (top 5)</p>
                <p className="text-xs text-gray-600 mt-1 leading-relaxed">
                  Cada ação tem impacto estimado em resultado — calculado a partir dos dados reais do
                  cliente, não de percentuais genéricos. Exemplos: renegociar frete, reduzir devolução,
                  revisar comissão, ajustar mix de SKUs.
                </p>
              </div>
            </div>

            <div className="flex gap-3">
              <span className="flex-shrink-0 w-6 h-6 rounded-full bg-gray-100 border border-gray-300 flex items-center justify-center text-xs font-bold text-gray-600">5</span>
              <div>
                <p className="text-sm font-semibold text-gray-800">Resumo CEO (1 página PDF)</p>
                <p className="text-xs text-gray-600 mt-1 leading-relaxed">
                  Gerado por LLM a partir dos dados calculados. Narrativa executiva: o que está acontecendo
                  com o cliente, qual é o veredito e quais ações estão sendo recomendadas. Pronto para
                  apresentar em reunião sem preparação adicional.
                </p>
              </div>
            </div>

          </div>
        </div>

        {/* DEPENDÊNCIAS */}
        <div className="bg-white shadow-sm border border-gray-200 rounded-xl p-5">
          <h2 className="text-sm font-bold text-gray-900 mb-1">Dependências</h2>
          <p className="text-xs text-gray-600 mb-4">
            Os itens marcados como pendentes precisam ser entregues antes que a Análise Crítica possa
            funcionar. Os itens prontos já estão no repositório.
          </p>
          <div className="space-y-2">
            {DEPENDENCIAS.map((dep, i) => (
              <div key={i} className="flex items-start gap-3">
                {dep.feito ? (
                  <span
                    className="mt-0.5 flex-shrink-0 w-5 h-5 rounded-full flex items-center justify-center"
                    style={{ backgroundColor: '#00A85920' }}
                  >
                    <svg className="w-3 h-3" fill="none" stroke="#00A859" viewBox="0 0 24 24" aria-hidden="true">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
                    </svg>
                  </span>
                ) : (
                  <span className="mt-0.5 flex-shrink-0 w-5 h-5 rounded-full flex items-center justify-center bg-red-50 border border-red-200">
                    <svg className="w-3 h-3 text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                    </svg>
                  </span>
                )}
                <div className="min-w-0">
                  <p className={`text-xs font-semibold ${dep.feito ? 'text-gray-700' : 'text-gray-800'}`}>
                    {dep.desc}
                  </p>
                  <p className="text-xs text-gray-500 mt-0.5 leading-snug">{dep.detalhe}</p>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Link para DDE */}
        <div className="bg-blue-50 border border-blue-200 rounded-xl p-4 flex items-start gap-3">
          <svg className="w-4 h-4 text-blue-500 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <div>
            <p className="text-xs font-semibold text-blue-800 mb-1">Próximo passo: DDE Engine</p>
            <p className="text-xs text-blue-700 leading-snug">
              A Análise Crítica depende diretamente do{' '}
              <Link href="/gestao/dde" className="font-semibold underline hover:text-blue-900 transition-colors">
                DDE (Demonstração de Desempenho Econômico)
              </Link>.
              {' '}Acesse a página do DDE para ver o roadmap de dados, decisões pendentes e estrutura da
              cascata P&amp;L que alimentará esta análise.
            </p>
          </div>
        </div>

        {/* Rodapé */}
        <p className="text-xs text-gray-400">
          Análise Crítica — Spec: SPEC_FEATURE_ANALISE_CRITICA_CRM_VITAO360.md ·
          Aguarda DDE Engine (Fase A) · Rebuild KILO 29/Abr/2026
        </p>

      </div>
    </RequireRole>
  );
}
