// gestao/_components/ScoreGauge.tsx
// Gauge SVG arco 270° — Score 0-100 com cor graduada
// Server-safe (no 'use client')

export type ScoreVeredito =
  | 'SAUDAVEL'
  | 'REVISAR'
  | 'RENEGOCIAR'
  | 'SUBSTITUIR'
  | 'ALERTA_CREDITO'
  | 'SEM_DADOS';

export interface ScoreGaugeProps {
  score: number;
  veredito?: ScoreVeredito;
  fasTag?: string;
  dataAtualizacao?: string;
}

const VEREDITO_CONFIG: Record<ScoreVeredito, { cor: string; textCor: string; bg: string; border: string; label: string; frase: string }> = {
  SAUDAVEL: {
    cor: '#22C55E',
    textCor: '#16A34A',
    bg: '#F0FDF4',
    border: '#BBF7D0',
    label: 'SAUDÁVEL',
    frase: 'Cliente rentável, regular e dentro dos limites de risco.',
  },
  REVISAR: {
    cor: '#F59E0B',
    textCor: '#B45309',
    bg: '#FFFBEB',
    border: '#FDE68A',
    label: 'REVISAR',
    frase: 'Margem 5–15% — atenção em verba/devolução. Monitorar próximos 60 dias.',
  },
  RENEGOCIAR: {
    cor: '#F97316',
    textCor: '#C2410C',
    bg: '#FFF7ED',
    border: '#FED7AA',
    label: 'RENEGOCIAR',
    frase: 'Margem < 5% — abaixo do custo de capital. Renegociar condições comerciais.',
  },
  SUBSTITUIR: {
    cor: '#EF4444',
    textCor: '#B91C1C',
    bg: '#FEF2F2',
    border: '#FECACA',
    label: 'SUBSTITUIR',
    frase: 'Margem negativa — cliente destrói valor. Avaliação de substituição necessária.',
  },
  ALERTA_CREDITO: {
    cor: '#A855F7',
    textCor: '#7E22CE',
    bg: '#FAF5FF',
    border: '#E9D5FF',
    label: 'ALERTA CRÉDITO',
    frase: 'Margem OK mas crédito comprometido. Aging elevado — revisar limites.',
  },
  SEM_DADOS: {
    cor: '#9CA3AF',
    textCor: '#6B7280',
    bg: '#F9FAFB',
    border: '#E5E7EB',
    label: 'SEM DADOS',
    frase: 'Dados insuficientes para veredito automático. Integração DDE pendente.',
  },
};

function polarToXY(cx: number, cy: number, r: number, angleDeg: number) {
  const rad = ((angleDeg - 90) * Math.PI) / 180;
  return { x: cx + r * Math.cos(rad), y: cy + r * Math.sin(rad) };
}

function arcPath(cx: number, cy: number, r: number, startDeg: number, endDeg: number) {
  const start = polarToXY(cx, cy, r, startDeg);
  const end = polarToXY(cx, cy, r, endDeg);
  const large = endDeg - startDeg > 180 ? 1 : 0;
  return `M ${start.x.toFixed(3)} ${start.y.toFixed(3)} A ${r} ${r} 0 ${large} 1 ${end.x.toFixed(3)} ${end.y.toFixed(3)}`;
}

export function ScoreGauge({
  score,
  veredito = 'SEM_DADOS',
  fasTag,
  dataAtualizacao,
}: ScoreGaugeProps) {
  const config = VEREDITO_CONFIG[veredito] ?? VEREDITO_CONFIG.SEM_DADOS;
  const clamped = Math.max(0, Math.min(100, Math.round(score ?? 0)));

  const CX = 60;
  const CY = 60;
  const R = 44;
  const STROKE = 10;
  const ANGLE_START = 135;
  const ANGLE_RANGE = 270;
  const endAngle = ANGLE_START + (clamped / 100) * ANGLE_RANGE;

  return (
    <div
      className="rounded-xl p-5 border flex flex-col sm:flex-row items-start sm:items-center gap-5"
      style={{ backgroundColor: config.bg, borderColor: config.border }}
    >
      {/* SVG Gauge */}
      <div className="flex-shrink-0 flex flex-col items-center">
        <svg
          viewBox="0 0 120 100"
          className="w-28 h-24"
          aria-label={`Score ${clamped} de 100`}
          role="img"
        >
          {/* Trilho cinza */}
          <path
            d={arcPath(CX, CY, R, ANGLE_START, ANGLE_START + ANGLE_RANGE)}
            fill="none"
            stroke="#E5E7EB"
            strokeWidth={STROKE}
            strokeLinecap="round"
          />
          {/* Arco colorido */}
          {clamped > 0 && (
            <path
              d={arcPath(CX, CY, R, ANGLE_START, endAngle)}
              fill="none"
              stroke={config.cor}
              strokeWidth={STROKE}
              strokeLinecap="round"
            />
          )}
          {/* Score numérico */}
          <text
            x={CX}
            y={CY - 2}
            textAnchor="middle"
            dominantBaseline="middle"
            fontSize="20"
            fontWeight="700"
            fill="#111827"
          >
            {clamped}
          </text>
          <text
            x={CX}
            y={CY + 14}
            textAnchor="middle"
            dominantBaseline="middle"
            fontSize="8"
            fontWeight="500"
            fill="#9CA3AF"
          >
            /100
          </text>
        </svg>
      </div>

      {/* Veredito + Descrição */}
      <div className="flex-1 min-w-0">
        <div className="flex flex-wrap items-center gap-2 mb-1.5">
          <span
            className="inline-flex items-center px-3 py-1 rounded-full text-sm font-bold uppercase tracking-wide"
            style={{ backgroundColor: config.cor + '20', color: config.textCor, border: `1px solid ${config.cor}40` }}
          >
            {config.label}
          </span>
          {fasTag && (
            <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold text-gray-500 bg-white border border-gray-200">
              {fasTag}
            </span>
          )}
        </div>
        <p className="text-sm text-gray-700 leading-snug">{config.frase}</p>
        {dataAtualizacao && (
          <p className="text-xs text-gray-400 mt-2">Atualizado: {dataAtualizacao}</p>
        )}
      </div>
    </div>
  );
}
