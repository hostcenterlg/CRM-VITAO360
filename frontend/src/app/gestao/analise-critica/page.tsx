'use client';

import Link from 'next/link';

// ---------------------------------------------------------------------------
// Analise Critica do Cliente
// Placeholder demo-quality — BLOQUEADO ate conclusao do DDE (Fase 3a)
// Feature: Score 0-100 + 9 KPIs + 5 Acoes priorizadas por cliente
// ---------------------------------------------------------------------------

// ---------------------------------------------------------------------------
// Gauge SVG — arco 270 graus
// ---------------------------------------------------------------------------

function ScoreGauge({ score, cor }: { score: number; cor: string }) {
  // Arco de 270 graus centrado em 135deg..405deg
  const R = 36;
  const CX = 50;
  const CY = 52;
  const ANGLE_START = 135; // graus
  const ANGLE_RANGE = 270; // graus
  const STROKE = 8;

  function polarToXY(cx: number, cy: number, r: number, angleDeg: number) {
    const rad = ((angleDeg - 90) * Math.PI) / 180;
    return {
      x: cx + r * Math.cos(rad),
      y: cy + r * Math.sin(rad),
    };
  }

  function arcPath(cx: number, cy: number, r: number, startDeg: number, endDeg: number) {
    const start = polarToXY(cx, cy, r, startDeg);
    const end = polarToXY(cx, cy, r, endDeg);
    const large = endDeg - startDeg > 180 ? 1 : 0;
    return `M ${start.x} ${start.y} A ${r} ${r} 0 ${large} 1 ${end.x} ${end.y}`;
  }

  const endAngle = ANGLE_START + (score / 100) * ANGLE_RANGE;

  return (
    <svg viewBox="0 0 100 80" className="w-28 h-24" aria-label={`Score ${score}`}>
      {/* Trilho cinza */}
      <path
        d={arcPath(CX, CY, R, ANGLE_START, ANGLE_START + ANGLE_RANGE)}
        fill="none"
        stroke="#E5E7EB"
        strokeWidth={STROKE}
        strokeLinecap="round"
      />
      {/* Arco preenchido */}
      {score > 0 && (
        <path
          d={arcPath(CX, CY, R, ANGLE_START, endAngle)}
          fill="none"
          stroke={cor}
          strokeWidth={STROKE}
          strokeLinecap="round"
        />
      )}
      {/* Texto do score */}
      <text x={CX} y={CY - 2} textAnchor="middle" dominantBaseline="middle"
        fontSize="16" fontWeight="700" fill="#111827">
        {score}
      </text>
      <text x={CX} y={CY + 13} textAnchor="middle" dominantBaseline="middle"
        fontSize="7" fontWeight="500" fill="#9CA3AF">
        /100
      </text>
    </svg>
  );
}

// ---------------------------------------------------------------------------
// KPI Card
// ---------------------------------------------------------------------------

interface KPIItem {
  label: string;
  valor: string;
  status: 'ok' | 'atencao' | 'critico';
  detalhe?: string;
}

const KPI_CORES = {
  ok: { bg: '#00B05010', text: '#00B050', border: '#00B05030' },
  atencao: { bg: '#FFC00015', text: '#B45309', border: '#FFC00050' },
  critico: { bg: '#FF000010', text: '#DC2626', border: '#FF000030' },
};

function KPICard({ kpi }: { kpi: KPIItem }) {
  const cores = KPI_CORES[kpi.status];
  return (
    <div
      className="rounded-lg p-3 border"
      style={{ backgroundColor: cores.bg, borderColor: cores.border }}
    >
      <p className="text-[9px] font-semibold uppercase tracking-wide text-gray-500">{kpi.label}</p>
      <p className="text-base font-bold mt-0.5" style={{ color: cores.text }}>{kpi.valor}</p>
      {kpi.detalhe && (
        <p className="text-[9px] text-gray-400 mt-0.5 leading-tight">{kpi.detalhe}</p>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Dados mockup
// ---------------------------------------------------------------------------

const SCORE_MOCK = 78;
const SCORE_COR = '#00B050';
const VEREDITO = 'SAUDAVEL';
const VEREDITO_DESC =
  'Cliente em curva A com margem 15,2% acima do minimo aceitavel. ' +
  'Recompra dentro do ciclo medio (28 dias). Ticket medio estavel nos ultimos 3 meses. ' +
  'Risco de churn baixo (Score >70).';

const ANOMALIAS = [
  { tipo: 'atencao' as const, texto: 'Comissao 2,5% — abaixo da media da carteira (3,0%)', acao: 'Revisar tabela' },
  { tipo: 'atencao' as const, texto: 'Frete cobrado fora do mes — verificar com logistica', acao: 'Alinhar NF' },
];

const ACOES: { posicao: number; descricao: string; impacto: string }[] = [
  { posicao: 1, descricao: 'Renovar tabela de preco (vencida ha 45d)', impacto: '+R$ 2.500/mes' },
  { posicao: 2, descricao: 'Negociar prazo 30 → 45 dias para fidelizacao', impacto: '+R$ 1.800' },
  { posicao: 3, descricao: 'Propor mix ampliado — 3 SKUs sem compra em 60d', impacto: '+R$ 1.200' },
  { posicao: 4, descricao: 'Revisar comissao para padrao da carteira (3,0%)', impacto: 'Margem +0,5%' },
  { posicao: 5, descricao: 'Agendar visita tecnica — ultimo contato > 30d', impacto: 'Retencao' },
];

const KPIS: KPIItem[] = [
  { label: 'Margem Bruta', valor: '29,4%', status: 'ok', detalhe: 'Meta: >25%' },
  { label: 'Comissao', valor: '2,5%', status: 'atencao', detalhe: 'Media: 3,0%' },
  { label: 'CMV', valor: '48,2%', status: 'ok', detalhe: 'Limite: <55%' },
  { label: 'Frete/Venda', valor: '5,0%', status: 'atencao', detalhe: 'Meta: <4%' },
  { label: 'Inadimplencia', valor: '0,8%', status: 'ok', detalhe: 'Limite: <2%' },
  { label: 'Desconto Med.', valor: '1,5%', status: 'ok', detalhe: 'Max: 3%' },
  { label: 'Ciclo Recompra', valor: '28d', status: 'ok', detalhe: 'Ideal: <35d' },
  { label: 'Ticket Medio', valor: 'R$ 104k', status: 'ok', detalhe: 'Curva A' },
  { label: 'ICMS Efetivo', valor: '7,8%', status: 'ok', detalhe: 'Regime normal' },
];

// ---------------------------------------------------------------------------
// Page
// ---------------------------------------------------------------------------

export default function AnaliseCriticaPage() {
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
            <h1 className="text-xl font-bold text-gray-900">Analise Critica do Cliente</h1>
            <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-md text-xs font-bold uppercase tracking-wide bg-gray-200 text-gray-600 border border-gray-300">
              <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5}
                  d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
              </svg>
              BLOQUEADO
            </span>
          </div>
          <p className="text-sm text-gray-500 mt-1 leading-snug max-w-xl">
            Score 0-100 + 9 KPIs + 5 acoes priorizadas por cliente, gerados automaticamente
            a partir do DDE. Disponivel imediatamente apos conclusao da Fase 3a.
          </p>
        </div>
        <div
          className="flex-shrink-0 w-9 h-9 rounded-xl flex items-center justify-center"
          style={{ backgroundColor: '#F3F4F6' }}
        >
          <svg className="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
              d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
          </svg>
        </div>
      </div>

      {/* Banner de bloqueio */}
      <div className="bg-amber-50 border border-amber-200 rounded-xl px-4 py-3 flex items-start gap-3">
        <svg className="w-4 h-4 text-amber-500 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
            d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
        </svg>
        <div>
          <p className="text-xs font-semibold text-amber-800">Feature bloqueada — aguarda DDE</p>
          <p className="text-xs text-amber-700 mt-0.5">
            Esta feature depende do motor DDE (em construcao).
            Sera liberada automaticamente apos conclusao da Fase 3a — previsao Maio / 2026.
          </p>
        </div>
      </div>

      {/* Card de Status */}
      <div className="bg-white rounded-xl border border-gray-100 shadow-sm p-5">
        <h2 className="text-xs font-bold text-gray-500 uppercase tracking-wider mb-4">Status da Feature</h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="flex items-start gap-2">
            <span className="mt-0.5 flex-shrink-0 w-4 h-4 rounded-full flex items-center justify-center" style={{ backgroundColor: '#00B05020' }}>
              <svg className="w-2.5 h-2.5" fill="none" stroke="#00B050" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
              </svg>
            </span>
            <div>
              <p className="text-xs font-semibold text-gray-700">Spec aprovada</p>
              <p className="text-[10px] text-gray-400">Algoritmo definido</p>
            </div>
          </div>
          <div className="flex items-start gap-2">
            <span className="mt-0.5 flex-shrink-0 w-4 h-4 rounded-full flex items-center justify-center" style={{ backgroundColor: '#00B05020' }}>
              <svg className="w-2.5 h-2.5" fill="none" stroke="#00B050" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
              </svg>
            </span>
            <div>
              <p className="text-xs font-semibold text-gray-700">Mockup visual</p>
              <p className="text-[10px] text-gray-400">Layout aprovado</p>
            </div>
          </div>
          <div className="flex items-start gap-2">
            <span className="mt-0.5 flex-shrink-0 w-4 h-4 rounded-full flex items-center justify-center bg-gray-100 border border-gray-200">
              <svg className="w-2.5 h-2.5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5}
                  d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
              </svg>
            </span>
            <div>
              <p className="text-xs font-semibold text-gray-400">Implementacao</p>
              <p className="text-[10px] text-gray-400">Aguarda DDE</p>
            </div>
          </div>
          <div className="flex items-start gap-2">
            <span className="mt-0.5 flex-shrink-0 w-4 h-4 rounded-full flex items-center justify-center bg-amber-50 border border-amber-200">
              <svg className="w-2.5 h-2.5 text-amber-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5}
                  d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </span>
            <div>
              <p className="text-xs font-semibold text-gray-500">Previsao</p>
              <p className="text-[10px] text-amber-700 font-semibold">Maio / 2026</p>
            </div>
          </div>
        </div>
      </div>

      {/* Preview — o que vai aparecer */}
      <div className="bg-white rounded-xl border border-gray-100 shadow-sm p-5">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xs font-bold text-gray-500 uppercase tracking-wider">Preview — o que vai aparecer</h2>
          <span className="inline-flex items-center px-2 py-0.5 rounded text-[9px] font-semibold uppercase text-amber-700 bg-amber-50 border border-amber-200">
            Mockup ilustrativo — feature em desenvolvimento
          </span>
        </div>

        {/* Score + Veredito */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-5">
          <div
            className="rounded-xl p-4 flex flex-col items-center justify-center"
            style={{ backgroundColor: '#00B05008', border: '1px solid #00B05030' }}
          >
            <ScoreGauge score={SCORE_MOCK} cor={SCORE_COR} />
            <p className="text-[10px] font-bold uppercase tracking-widest mt-1" style={{ color: SCORE_COR }}>
              {VEREDITO}
            </p>
          </div>
          <div
            className="rounded-xl p-4"
            style={{ backgroundColor: '#00B05008', border: '1px solid #00B05030' }}
          >
            <p className="text-[9px] font-bold text-gray-400 uppercase tracking-wide mb-2">Veredito Automatico</p>
            <p className="text-xs text-gray-700 leading-relaxed">{VEREDITO_DESC}</p>
          </div>
        </div>

        {/* Anomalias */}
        <div className="mb-5">
          <p className="text-[10px] font-bold text-gray-500 uppercase tracking-wider mb-2">Anomalias Detectadas</p>
          <ul className="space-y-2">
            {ANOMALIAS.map((a, i) => (
              <li key={i} className="flex items-start gap-2 text-xs">
                <svg className="w-3.5 h-3.5 flex-shrink-0 mt-0.5" fill="none" stroke="#F97316" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                    d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                </svg>
                <span className="text-gray-700 flex-1">{a.texto}</span>
                <span className="text-[9px] font-semibold uppercase text-orange-600 bg-orange-50 border border-orange-200 px-1.5 py-0.5 rounded flex-shrink-0">
                  {a.acao}
                </span>
              </li>
            ))}
          </ul>
        </div>

        {/* Top 5 Acoes */}
        <div className="mb-5">
          <p className="text-[10px] font-bold text-gray-500 uppercase tracking-wider mb-2">Top 5 Acoes Priorizadas</p>
          <ol className="space-y-2">
            {ACOES.map((a) => (
              <li key={a.posicao} className="flex items-center gap-2.5 text-xs">
                <span
                  className="flex-shrink-0 w-5 h-5 rounded-full flex items-center justify-center text-white font-bold text-[10px]"
                  style={{ backgroundColor: '#00B050' }}
                >
                  {a.posicao}
                </span>
                <span className="flex-1 text-gray-700">{a.descricao}</span>
                <span
                  className="text-[9px] font-semibold px-1.5 py-0.5 rounded flex-shrink-0"
                  style={{ backgroundColor: '#00B05015', color: '#00B050' }}
                >
                  {a.impacto}
                </span>
              </li>
            ))}
          </ol>
        </div>

        {/* 9 KPIs */}
        <div>
          <p className="text-[10px] font-bold text-gray-500 uppercase tracking-wider mb-2">9 KPIs do Cliente</p>
          <div className="grid grid-cols-3 gap-2">
            {KPIS.map((kpi, i) => (
              <KPICard key={i} kpi={kpi} />
            ))}
          </div>
        </div>
      </div>

      {/* Nota de rodape */}
      <p className="text-[10px] text-gray-400">
        Analise Critica v1.0 — Spec aprovada. Implementacao aguarda conclusao do DDE (Fase 3a).
        Esta pagina e uma preview de roadmap para apresentacao interna.
      </p>

    </div>
  );
}
