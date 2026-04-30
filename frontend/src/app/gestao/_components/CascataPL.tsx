// gestao/_components/CascataPL.tsx
// Tabela cascata P&L — 7 blocos, 25 linhas, spec SPEC_DDE_CASCATA_REAL.md
// Com tier pills (REAL/SINTÉTICO/PENDENTE/NULL) e barras de proporção visual
// Server-safe (no 'use client')

export type Tier = 'REAL' | 'SINTETICO' | 'PENDENTE' | 'NULL';
export type Fase = 'A' | 'B' | 'C';
export type LinhaStatus = 'detalhe' | 'subtotal' | 'total' | 'separador';

export interface CascataLinhaData {
  codigo: string;
  conta: string;
  sinal?: '+' | '-' | '=';
  valor: number | null; // null = PENDENTE
  pctRL?: number | null;
  tier: Tier;
  fase: Fase;
  status: LinhaStatus;
  observacao?: string;
}

export interface CascataBlocoData {
  numero: number;
  titulo: string;
  linhas: CascataLinhaData[];
}

// Configuração visual por tier
const TIER_CONFIG: Record<Tier, { label: string; bgClass: string; textClass: string; borderClass: string }> = {
  REAL:     { label: 'REAL',      bgClass: 'bg-green-50',  textClass: 'text-green-700',  borderClass: 'border-green-200' },
  SINTETICO:{ label: 'SINTÉTICO', bgClass: 'bg-blue-50',   textClass: 'text-blue-700',   borderClass: 'border-blue-200' },
  PENDENTE: { label: 'PENDENTE',  bgClass: 'bg-gray-100',  textClass: 'text-gray-500',   borderClass: 'border-gray-200' },
  NULL:     { label: 'NULL',      bgClass: 'bg-gray-50',   textClass: 'text-gray-400',   borderClass: 'border-gray-100' },
};

// Cores de fundo por bloco (index 0-6)
const BLOCO_CORES = [
  '#F0FDF420', // Bloco 1 — Receita Bruta — verde claro
  '#FFFBEB20', // Bloco 2 — Deduções — âmbar claro
  '#FEF2F220', // Bloco 3 — CMV — vermelho claro
  '#EFF6FF20', // Bloco 4 — Despesas Variáveis — azul claro
  '#FAF5FF20', // Bloco 5 — Fixas Alocadas — roxo claro
  '#ECFDF520', // Bloco 6 — Indicadores — verde claro
  '#F9FAFB20', // Bloco 7 — Vereditos — cinza
];

function fmtBRL(v: number | null): string {
  if (v === null) return '—';
  return v.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL', maximumFractionDigits: 0 });
}

function fmtPct(v: number | null): string {
  if (v === null || v === 0) return '—';
  return `${v.toFixed(1)}%`;
}

function TierPill({ tier }: { tier: Tier }) {
  const cfg = TIER_CONFIG[tier];
  if (!cfg) return null;
  return (
    <span
      className={`inline-flex items-center px-1.5 py-0 rounded text-[10px] font-bold uppercase tracking-wide border ${cfg.bgClass} ${cfg.textClass} ${cfg.borderClass}`}
    >
      {cfg.label}
    </span>
  );
}

// Barra proporcional para coluna visual
function PropBar({ valor, maxAbs, sinal }: { valor: number | null; maxAbs: number; sinal?: string }) {
  if (valor === null || maxAbs === 0) {
    return <span className="block w-16 h-2 bg-gray-100 rounded-full" />;
  }
  const pct = Math.min(100, (Math.abs(valor) / maxAbs) * 100);
  const isDeducao = valor < 0 || sinal === '-';
  return (
    <span className="block w-16 bg-gray-100 rounded-full h-2 overflow-hidden">
      <span
        className={`block h-full rounded-full ${isDeducao ? 'bg-red-300' : 'bg-green-400'}`}
        style={{ width: `${pct}%` }}
      />
    </span>
  );
}

interface CascataPLProps {
  blocos: CascataBlocoData[];
  /** Valor de referência para barras (padrão: max absoluto de todos valores) */
  refValue?: number;
  /** Mostra a coluna de tier (padrão: true) */
  showTier?: boolean;
  /** Mostra a coluna de fase (padrão: false) */
  showFase?: boolean;
}

export function CascataPL({ blocos, refValue, showTier = true, showFase = false }: CascataPLProps) {
  // Calcular max absoluto para barras
  const allValues = blocos.flatMap(b => b.linhas.map(l => l.valor)).filter((v): v is number => v !== null);
  const maxAbs = refValue ?? Math.max(...allValues.map(v => Math.abs(v)), 1);

  return (
    <div className="overflow-x-auto -mx-5">
      <div className="min-w-[600px] px-5">
        <table className="w-full text-xs border-collapse">
          <thead>
            <tr className="border-b-2 border-gray-200">
              <th className="text-left py-2 px-2 font-semibold text-gray-400 uppercase tracking-wide w-12">Cód.</th>
              <th className="text-left py-2 px-2 font-semibold text-gray-400 uppercase tracking-wide">Conta</th>
              <th className="text-right py-2 px-2 font-semibold text-gray-400 uppercase tracking-wide w-32 tabular-nums">Valor (R$)</th>
              <th className="text-right py-2 px-2 font-semibold text-gray-400 uppercase tracking-wide w-16 tabular-nums">% RL</th>
              {showTier && (
                <th className="text-center py-2 px-2 font-semibold text-gray-400 uppercase tracking-wide w-24">Tier</th>
              )}
              {showFase && (
                <th className="text-center py-2 px-2 font-semibold text-gray-400 uppercase tracking-wide w-12">Fase</th>
              )}
              <th className="py-2 px-2 w-20" aria-label="Proporção" />
            </tr>
          </thead>
          <tbody>
            {blocos.map((bloco, bIdx) => (
              <>
                {/* Cabeçalho do bloco */}
                <tr key={`bloco-${bloco.numero}`}>
                  <td
                    colSpan={4 + (showTier ? 1 : 0) + (showFase ? 1 : 0) + 1}
                    className="py-1.5 px-2 text-[10px] font-bold text-gray-500 uppercase tracking-widest border-t border-b border-gray-200"
                    style={{ backgroundColor: BLOCO_CORES[bIdx] ?? '#F9FAFB20' }}
                  >
                    <span className="text-gray-400 font-normal mr-1">BLOCO {bloco.numero}</span>
                    {bloco.titulo}
                  </td>
                </tr>

                {/* Linhas do bloco */}
                {bloco.linhas.map((linha) => {
                  const isPendente = linha.tier === 'PENDENTE' || linha.tier === 'NULL' || linha.valor === null;
                  const isSubtotal = linha.status === 'subtotal' || linha.status === 'total';
                  const isSintetico = linha.tier === 'SINTETICO';

                  return (
                    <tr
                      key={linha.codigo}
                      className={`border-b border-gray-50 transition-colors hover:bg-gray-50 ${
                        isSubtotal
                          ? 'bg-gray-50 border-t border-gray-200'
                          : ''
                      } ${isPendente ? 'opacity-60' : ''}`}
                    >
                      {/* Código */}
                      <td className={`py-2 px-2 font-mono text-[10px] ${isSubtotal ? 'font-bold text-gray-600' : 'text-gray-400'}`}>
                        {linha.codigo}
                      </td>

                      {/* Conta */}
                      <td className={`py-2 px-2 ${linha.status === 'detalhe' ? 'pl-5' : 'pl-2'} leading-snug ${isSubtotal ? 'font-semibold text-gray-900' : 'text-gray-600'}`}>
                        {linha.sinal && (
                          <span className={`inline-block w-3 font-mono mr-0.5 ${linha.sinal === '=' ? 'text-gray-400' : linha.sinal === '-' ? 'text-red-400' : 'text-green-500'}`}>
                            {linha.sinal}
                          </span>
                        )}
                        {linha.conta}
                        {isSintetico && (
                          <span className="ml-1 text-blue-400 font-bold" title="Estimativa sintética — baseada em média/proxy">*</span>
                        )}
                        {linha.observacao && (
                          <span className="ml-1 text-gray-400" title={linha.observacao}>ⓘ</span>
                        )}
                      </td>

                      {/* Valor */}
                      <td className={`py-2 px-2 text-right tabular-nums ${isSubtotal ? 'font-bold text-gray-900' : ''}`}>
                        {isPendente ? (
                          <span className="text-gray-300 tracking-widest font-mono">░░░░░</span>
                        ) : (
                          <span className={linha.valor !== null && linha.valor < 0 ? 'text-red-600' : 'text-gray-900'}>
                            {fmtBRL(linha.valor)}
                          </span>
                        )}
                      </td>

                      {/* % RL */}
                      <td className="py-2 px-2 text-right tabular-nums text-gray-500">
                        {fmtPct(linha.pctRL ?? null)}
                      </td>

                      {/* Tier pill */}
                      {showTier && (
                        <td className="py-2 px-2 text-center">
                          <TierPill tier={linha.tier} />
                        </td>
                      )}

                      {/* Fase badge */}
                      {showFase && (
                        <td className="py-2 px-2 text-center">
                          <span className={`text-[10px] font-bold px-1 rounded ${
                            linha.fase === 'A' ? 'bg-green-100 text-green-700' :
                            linha.fase === 'B' ? 'bg-blue-100 text-blue-700' :
                            'bg-purple-100 text-purple-700'
                          }`}>
                            {linha.fase}
                          </span>
                        </td>
                      )}

                      {/* Barra proporcional */}
                      <td className="py-2 px-2">
                        {!isPendente && <PropBar valor={linha.valor} maxAbs={maxAbs} sinal={linha.sinal} />}
                      </td>
                    </tr>
                  );
                })}
              </>
            ))}
          </tbody>
        </table>

        {/* Legenda */}
        <div className="mt-4 flex flex-wrap items-center gap-3 text-[10px] text-gray-500 border-t border-gray-100 pt-3">
          <span className="flex items-center gap-1">
            <span className="inline-flex items-center px-1.5 py-0 rounded border bg-green-50 text-green-700 border-green-200 font-bold uppercase text-[10px]">REAL</span>
            Dado rastreável (SH/SAP/LOG)
          </span>
          <span className="flex items-center gap-1">
            <span className="inline-flex items-center px-1.5 py-0 rounded border bg-blue-50 text-blue-700 border-blue-200 font-bold uppercase text-[10px]">SINTÉTICO*</span>
            Estimativa marcada
          </span>
          <span className="flex items-center gap-1">
            <span className="tracking-widest text-gray-300 font-mono">░░░</span>
            <span className="inline-flex items-center px-1.5 py-0 rounded border bg-gray-100 text-gray-500 border-gray-200 font-bold uppercase text-[10px]">PENDENTE</span>
            Aguardando integração
          </span>
        </div>
      </div>
    </div>
  );
}
