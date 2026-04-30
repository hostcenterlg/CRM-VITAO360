// gestao/_components/AcoesPriorizadasList.tsx
// Lista top 5 ações priorizadas com impacto R$ e status
// Server-safe (no 'use client')

export type AcaoStatus = 'ABERTO' | 'EM_ANDAMENTO' | 'CONCLUIDO';

export interface AcaoItem {
  posicao: number;
  titulo: string;
  descricao?: string;
  impacto: string;
  status: AcaoStatus;
  prazo?: string;
}

const STATUS_CONFIG: Record<AcaoStatus, { label: string; bg: string; text: string; border: string }> = {
  ABERTO:       { label: 'Aberto',       bg: '#F9FAFB', text: '#6B7280', border: '#E5E7EB' },
  EM_ANDAMENTO: { label: 'Em andamento', bg: '#EFF6FF', text: '#1D4ED8', border: '#BFDBFE' },
  CONCLUIDO:    { label: 'Concluído',    bg: '#F0FDF4', text: '#15803D', border: '#BBF7D0' },
};

interface AcoesPriorizadasListProps {
  acoes: AcaoItem[];
}

export function AcoesPriorizadasList({ acoes }: AcoesPriorizadasListProps) {
  return (
    <div className="space-y-2">
      {acoes.map((acao) => {
        const sCfg = STATUS_CONFIG[acao.status] ?? STATUS_CONFIG.ABERTO;
        return (
          <div
            key={acao.posicao}
            className="flex items-start gap-3 bg-white border border-gray-100 rounded-xl px-4 py-3 shadow-sm hover:border-gray-200 transition-colors"
          >
            {/* Número */}
            <span
              className="flex-shrink-0 w-6 h-6 rounded-full flex items-center justify-center text-white font-bold text-xs mt-0.5"
              style={{ backgroundColor: '#00A859' }}
            >
              {acao.posicao}
            </span>

            {/* Conteúdo */}
            <div className="flex-1 min-w-0">
              <p className="text-sm font-semibold text-gray-900 leading-snug">{acao.titulo}</p>
              {acao.descricao && (
                <p className="text-xs text-gray-500 mt-0.5 leading-snug">{acao.descricao}</p>
              )}
              <div className="flex flex-wrap items-center gap-2 mt-1.5">
                {/* Impacto */}
                <span
                  className="text-xs font-semibold px-2 py-0.5 rounded"
                  style={{ backgroundColor: '#00A85915', color: '#00A859' }}
                >
                  {acao.impacto}
                </span>
                {/* Prazo */}
                {acao.prazo && (
                  <span className="text-xs text-gray-400">{acao.prazo}</span>
                )}
                {/* Status */}
                <span
                  className="text-[10px] font-bold uppercase tracking-wide px-1.5 py-0.5 rounded border"
                  style={{ backgroundColor: sCfg.bg, color: sCfg.text, borderColor: sCfg.border }}
                >
                  {sCfg.label}
                </span>
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
}
