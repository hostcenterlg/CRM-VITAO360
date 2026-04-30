// gestao/_components/AnomaliasList.tsx
// Lista de anomalias detectadas pelo motor de regras
// Server-safe (no 'use client')

export type AnomaliaSeveridade = 'CRITICO' | 'ALTA' | 'MEDIA' | 'REVISAR';

export interface AnomaliaItem {
  codigo: string;
  titulo: string;
  descricao: string;
  valorObservado?: string;
  limite?: string;
  severidade: AnomaliaSeveridade;
}

const SEVERIDADE_CONFIG: Record<AnomaliaSeveridade, {
  bg: string; border: string; textBadge: string; bgBadge: string; label: string; iconColor: string;
}> = {
  CRITICO: {
    bg: '#FEF2F2', border: '#FECACA',
    textBadge: '#991B1B', bgBadge: '#FEE2E2',
    label: 'CRÍTICA', iconColor: '#EF4444',
  },
  ALTA: {
    bg: '#FFF7ED', border: '#FED7AA',
    textBadge: '#9A3412', bgBadge: '#FFEDD5',
    label: 'ALTA', iconColor: '#F97316',
  },
  MEDIA: {
    bg: '#FFFBEB', border: '#FDE68A',
    textBadge: '#92400E', bgBadge: '#FEF3C7',
    label: 'MÉDIA', iconColor: '#F59E0B',
  },
  REVISAR: {
    bg: '#EFF6FF', border: '#BFDBFE',
    textBadge: '#1E40AF', bgBadge: '#DBEAFE',
    label: 'REVISAR', iconColor: '#3B82F6',
  },
};

function IconTriangle({ color }: { color: string }) {
  return (
    <svg className="w-4 h-4 flex-shrink-0 mt-0.5" fill="none" stroke={color} viewBox="0 0 24 24" aria-hidden="true">
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth={2}
        d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
      />
    </svg>
  );
}

interface AnomaliasListProps {
  anomalias: AnomaliaItem[];
}

export function AnomaliasList({ anomalias }: AnomaliasListProps) {
  if (anomalias.length === 0) {
    return (
      <div className="flex items-center gap-3 bg-green-50 border border-green-200 rounded-xl px-4 py-3">
        <svg className="w-4 h-4 text-green-500 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
        </svg>
        <p className="text-sm font-semibold text-green-700">Nenhuma anomalia detectada neste período.</p>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {anomalias.map((anomalia, i) => {
        const cfg = SEVERIDADE_CONFIG[anomalia.severidade] ?? SEVERIDADE_CONFIG.REVISAR;
        return (
          <div
            key={`${anomalia.codigo}-${i}`}
            className="rounded-xl px-4 py-3 border"
            style={{ backgroundColor: cfg.bg, borderColor: cfg.border }}
          >
            <div className="flex items-start gap-3">
              <IconTriangle color={cfg.iconColor} />
              <div className="flex-1 min-w-0">
                <div className="flex flex-wrap items-center gap-2 mb-0.5">
                  <span
                    className="text-[10px] font-bold uppercase tracking-wide px-1.5 py-0 rounded"
                    style={{ color: cfg.textBadge, backgroundColor: cfg.bgBadge }}
                  >
                    {cfg.label}
                  </span>
                  <span className="text-xs font-semibold text-gray-700">{anomalia.codigo} · {anomalia.titulo}</span>
                </div>
                <p className="text-xs text-gray-600 leading-snug">{anomalia.descricao}</p>
                {(anomalia.valorObservado || anomalia.limite) && (
                  <div className="flex flex-wrap gap-3 mt-1.5">
                    {anomalia.valorObservado && (
                      <span className="text-[10px] text-gray-500">
                        Observado: <span className="font-semibold text-gray-700">{anomalia.valorObservado}</span>
                      </span>
                    )}
                    {anomalia.limite && (
                      <span className="text-[10px] text-gray-500">
                        Limite: <span className="font-semibold text-gray-700">{anomalia.limite}</span>
                      </span>
                    )}
                  </div>
                )}
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
}
