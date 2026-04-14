'use client';

// ---------------------------------------------------------------------------
// Skeleton — shimmer placeholders para estados de carregamento
// Variantes: text | card | table-row | chart | kpi
// Tailwind only, sem CSS customizado, tema LIGHT exclusivamente
// ---------------------------------------------------------------------------

interface SkeletonBaseProps {
  className?: string;
}

// ---------------------------------------------------------------------------
// Primitivo: bloco com shimmer pulse
// ---------------------------------------------------------------------------

interface SkeletonBlockProps extends SkeletonBaseProps {
  width?: string;
  height?: string;
  rounded?: string;
}

function SkeletonBlock({
  width = '100%',
  height = '1rem',
  rounded = 'rounded',
  className = '',
}: SkeletonBlockProps) {
  return (
    <div
      className={`bg-gray-200 animate-pulse ${rounded} ${className}`}
      style={{ width, height }}
      aria-hidden="true"
    />
  );
}

// ---------------------------------------------------------------------------
// Variante: text
// ---------------------------------------------------------------------------

interface SkeletonTextProps extends SkeletonBaseProps {
  width?: string;
  lines?: number;
}

function SkeletonText({ width = '100%', lines = 1, className = '' }: SkeletonTextProps) {
  if (lines === 1) {
    return <SkeletonBlock width={width} height="0.875rem" rounded="rounded" className={className} />;
  }
  return (
    <div className={`space-y-2 ${className}`} aria-hidden="true">
      {Array.from({ length: lines }).map((_, i) => (
        <SkeletonBlock
          key={i}
          width={i === lines - 1 ? '70%' : '100%'}
          height="0.875rem"
          rounded="rounded"
        />
      ))}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Variante: kpi — imita KpiCard
// ---------------------------------------------------------------------------

function SkeletonKpi({ className = '' }: SkeletonBaseProps) {
  return (
    <div
      className={`bg-white rounded-lg border border-gray-200 p-3 sm:p-4 flex flex-col gap-2 shadow-sm ${className}`}
      style={{ borderLeftWidth: '4px', borderLeftColor: '#e5e7eb' }}
      aria-hidden="true"
    >
      <SkeletonBlock width="60%" height="0.625rem" rounded="rounded" />
      <SkeletonBlock width="40%" height="1.75rem" rounded="rounded" />
      <SkeletonBlock width="50%" height="0.625rem" rounded="rounded" />
    </div>
  );
}

// ---------------------------------------------------------------------------
// Variante: card
// ---------------------------------------------------------------------------

function SkeletonCard({ className = '' }: SkeletonBaseProps) {
  return (
    <div
      className={`bg-white rounded-xl border border-gray-100 shadow-sm p-5 space-y-3 ${className}`}
      aria-hidden="true"
    >
      <SkeletonBlock width="40%" height="0.875rem" rounded="rounded" />
      <SkeletonBlock width="100%" height="0.75rem" rounded="rounded" />
      <SkeletonBlock width="85%" height="0.75rem" rounded="rounded" />
      <SkeletonBlock width="70%" height="0.75rem" rounded="rounded" />
    </div>
  );
}

// ---------------------------------------------------------------------------
// Variante: chart — imita área de gráfico Recharts
// ---------------------------------------------------------------------------

interface SkeletonChartProps extends SkeletonBaseProps {
  height?: string;
}

function SkeletonChart({ height = '224px', className = '' }: SkeletonChartProps) {
  return (
    <div className={`mt-4 ${className}`} aria-hidden="true">
      <div
        className="bg-gray-100 animate-pulse rounded-lg w-full"
        style={{ height }}
      />
    </div>
  );
}

// ---------------------------------------------------------------------------
// Variante: table-row — imita linha de tabela
// ---------------------------------------------------------------------------

interface SkeletonTableRowProps extends SkeletonBaseProps {
  columns?: number;
  rows?: number;
}

function SkeletonTableRow({ columns = 5, rows = 1, className = '' }: SkeletonTableRowProps) {
  const widths = [40, 120, 100, 80, 60, 60, 80, 50, 60];

  return (
    <>
      {Array.from({ length: rows }).map((_, rowIdx) => (
        <tr key={rowIdx} className={`border-b border-gray-100 ${className}`} aria-hidden="true">
          {Array.from({ length: columns }).map((_, colIdx) => {
            const w = widths[colIdx % widths.length];
            return (
              <td key={colIdx} className="px-4 py-3">
                <div
                  className="h-3 rounded animate-pulse bg-gray-100"
                  style={{ width: w }}
                />
              </td>
            );
          })}
        </tr>
      ))}
    </>
  );
}

// ---------------------------------------------------------------------------
// Variante: kanban-column — imita coluna do pipeline
// ---------------------------------------------------------------------------

interface SkeletonKanbanProps extends SkeletonBaseProps {
  columns?: number;
  cardsPerColumn?: number;
}

function SkeletonKanban({
  columns = 6,
  cardsPerColumn = 4,
  className = '',
}: SkeletonKanbanProps) {
  return (
    <div className={`flex gap-3 overflow-x-auto pb-3 ${className}`} aria-hidden="true">
      {Array.from({ length: columns }).map((_, colIdx) => (
        <div
          key={colIdx}
          className="flex-shrink-0 rounded-lg border border-gray-200 bg-white animate-pulse"
          style={{ width: 220 }}
        >
          <div className="h-14 bg-gray-100 rounded-t-lg" />
          <div className="p-2 space-y-2">
            {Array.from({ length: cardsPerColumn }).map((_, cardIdx) => (
              <div
                key={cardIdx}
                className="h-20 bg-gray-50 rounded-lg border border-gray-100"
              />
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Variante: agenda-list — imita cards de agenda
// ---------------------------------------------------------------------------

interface SkeletonAgendaProps extends SkeletonBaseProps {
  rows?: number;
}

function SkeletonAgenda({ rows = 6, className = '' }: SkeletonAgendaProps) {
  return (
    <div className={`space-y-3 p-4 ${className}`} aria-hidden="true">
      {Array.from({ length: rows }).map((_, i) => (
        <div
          key={i}
          className="h-28 bg-gray-100 animate-pulse rounded-lg"
          style={{ animationDelay: `${i * 80}ms` }}
        />
      ))}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Export principal com sub-componentes nomeados
// ---------------------------------------------------------------------------

const Skeleton = {
  Block: SkeletonBlock,
  Text: SkeletonText,
  Kpi: SkeletonKpi,
  Card: SkeletonCard,
  Chart: SkeletonChart,
  TableRow: SkeletonTableRow,
  Kanban: SkeletonKanban,
  Agenda: SkeletonAgenda,
};

export default Skeleton;

// Named exports para uso direto sem namespace
export {
  SkeletonBlock,
  SkeletonText,
  SkeletonKpi,
  SkeletonCard,
  SkeletonChart,
  SkeletonTableRow,
  SkeletonKanban,
  SkeletonAgenda,
};
