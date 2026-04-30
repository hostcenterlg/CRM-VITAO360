'use client';

// ScoreGauge — arco SVG 270° mostrando score DDE (0-100)
// Cores: 0-30 vermelho, 30-50 âmbar, 50-70 amarelo, 70-100 verde
// null → "—" + "Aguardando dados"

interface ScoreGaugeProps {
  score: number | null;
  size?: number; // diâmetro em px (padrão 160)
}

function getScoreColor(score: number): string {
  if (score >= 70) return '#00A859'; // verde vitao
  if (score >= 50) return '#EAB308'; // amarelo
  if (score >= 30) return '#F59E0B'; // âmbar
  return '#EF4444'; // vermelho
}

export function ScoreGauge({ score, size = 160 }: ScoreGaugeProps) {
  const cx = size / 2;
  const cy = size / 2;
  const r = (size / 2) - 14;
  const strokeW = size * 0.075;

  // Arco 270°: começa em 135° e termina em 405° (135°+270°)
  const startAngle = 135;
  const totalAngle = 270;

  function polarToXY(angle: number, radius: number) {
    const rad = ((angle - 90) * Math.PI) / 180;
    return {
      x: cx + radius * Math.cos(rad),
      y: cy + radius * Math.sin(rad),
    };
  }

  function describeArc(startDeg: number, endDeg: number, radius: number): string {
    const start = polarToXY(startDeg, radius);
    const end = polarToXY(endDeg, radius);
    const largeArc = endDeg - startDeg > 180 ? 1 : 0;
    return `M ${start.x} ${start.y} A ${radius} ${radius} 0 ${largeArc} 1 ${end.x} ${end.y}`;
  }

  const bgPath = describeArc(startAngle, startAngle + totalAngle, r);

  const fillAngle = score != null
    ? startAngle + (score / 100) * totalAngle
    : startAngle;

  const fillPath = score != null && score > 0
    ? describeArc(startAngle, Math.min(fillAngle, startAngle + totalAngle), r)
    : null;

  const scoreColor = score != null ? getScoreColor(score) : '#9CA3AF';

  return (
    <div
      className="inline-flex flex-col items-center gap-1"
      role="img"
      aria-label={score != null ? `Score DDE: ${score} de 100` : 'Score DDE: aguardando dados'}
    >
      <svg width={size} height={size * 0.82} viewBox={`0 0 ${size} ${size * 0.82}`} aria-hidden="true">
        {/* Trilha de fundo */}
        <path
          d={bgPath}
          fill="none"
          stroke="#E5E7EB"
          strokeWidth={strokeW}
          strokeLinecap="round"
        />
        {/* Arco preenchido */}
        {fillPath && (
          <path
            d={fillPath}
            fill="none"
            stroke={scoreColor}
            strokeWidth={strokeW}
            strokeLinecap="round"
            style={{ transition: 'stroke-dasharray 0.5s ease' }}
          />
        )}
        {/* Score central */}
        <text
          x={cx}
          y={cy + (size * 0.04)}
          textAnchor="middle"
          dominantBaseline="middle"
          className="font-bold"
          style={{ fontSize: size * 0.22, fill: score != null ? scoreColor : '#9CA3AF', fontFamily: 'Inter, sans-serif' }}
        >
          {score != null ? Math.round(score) : '—'}
        </text>
        {/* Label inferior */}
        <text
          x={cx}
          y={cy + (size * 0.21)}
          textAnchor="middle"
          style={{ fontSize: size * 0.09, fill: '#6B7280', fontFamily: 'Inter, sans-serif' }}
        >
          Score DDE
        </text>
      </svg>
      {score == null && (
        <span className="text-xs text-gray-500 italic">Aguardando dados</span>
      )}
    </div>
  );
}
