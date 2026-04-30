// gestao/_components/KPICards.tsx
// Grid 3x3 de KPIs I1-I9 com sinaleiro semafórico por indicador
// Server-safe (no 'use client')

export type KPIStatus = 'ok' | 'atencao' | 'critico' | 'pendente';

export interface KPIItem {
  codigo: string; // I1-I9
  label: string;
  valor: string | null;
  status: KPIStatus;
  detalhe?: string;
  variacao?: string; // ex: "▲ 2.1pp", "▼ 8d"
  faseBloqueio?: string; // ex: "Fase B"
}

const STATUS_CONFIG: Record<KPIStatus, { bg: string; border: string; text: string; dot: string; label: string }> = {
  ok:       { bg: '#F0FDF4', border: '#BBF7D0', text: '#15803D', dot: '#22C55E', label: 'Bom' },
  atencao:  { bg: '#FFFBEB', border: '#FDE68A', text: '#92400E', dot: '#F59E0B', label: 'Atenção' },
  critico:  { bg: '#FEF2F2', border: '#FECACA', text: '#991B1B', dot: '#EF4444', label: 'Crítico' },
  pendente: { bg: '#F9FAFB', border: '#E5E7EB', text: '#6B7280', dot: '#9CA3AF', label: 'Pendente' },
};

interface KPICardProps {
  kpi: KPIItem;
}

function KPICard({ kpi }: KPICardProps) {
  const cfg = STATUS_CONFIG[kpi.status] ?? STATUS_CONFIG.pendente;
  const bloqueado = !!kpi.faseBloqueio;

  return (
    <div
      className={`rounded-xl p-3 border ${bloqueado ? 'opacity-70' : ''}`}
      style={{ backgroundColor: cfg.bg, borderColor: cfg.border }}
    >
      <div className="flex items-start justify-between gap-1 mb-1">
        <p className="text-[10px] font-semibold uppercase tracking-wide text-gray-500 leading-tight">{kpi.label}</p>
        <span
          className="flex-shrink-0 w-2 h-2 rounded-full mt-0.5"
          style={{ backgroundColor: cfg.dot }}
          title={cfg.label}
          aria-label={cfg.label}
        />
      </div>

      {bloqueado ? (
        <div>
          <p className="text-[10px] text-gray-400 font-mono tracking-widest">░░░░</p>
          <span
            className="inline-block text-[10px] font-bold uppercase px-1.5 py-0 rounded mt-0.5"
            style={{ backgroundColor: '#E5E7EB', color: '#6B7280' }}
          >
            {kpi.faseBloqueio}
          </span>
        </div>
      ) : (
        <div>
          <p className="text-base font-bold tabular-nums leading-tight" style={{ color: cfg.text }}>
            {kpi.valor ?? '—'}
          </p>
          {kpi.variacao && (
            <p className="text-[10px] text-gray-500 mt-0.5">{kpi.variacao}</p>
          )}
          {kpi.detalhe && (
            <p className="text-[10px] text-gray-400 mt-0.5">{kpi.detalhe}</p>
          )}
        </div>
      )}
    </div>
  );
}

interface KPICardsProps {
  kpis: KPIItem[];
  colunas?: 2 | 3 | 4;
}

export function KPICards({ kpis, colunas = 3 }: KPICardsProps) {
  const gridClass = {
    2: 'grid-cols-2',
    3: 'grid-cols-2 sm:grid-cols-3',
    4: 'grid-cols-2 sm:grid-cols-4',
  }[colunas];

  return (
    <div className={`grid ${gridClass} gap-3`}>
      {kpis.map((kpi, i) => (
        <KPICard key={kpi.codigo || i} kpi={kpi} />
      ))}
    </div>
  );
}
