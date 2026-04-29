'use client';

import { CurvaABCBar, formatBRL } from '@/lib/api';

// ---------------------------------------------------------------------------
// CurvaABCBars — exibe as 3 barras de progresso da Curva ABC
// Cores: A=#00B050 (vitao-green), B=vitao-blue, C=gray-400
// Extraído de page.tsx (hero section) para reutilização em /carteira
// ---------------------------------------------------------------------------

interface CurvaABCBarsProps {
  data?: Record<string, CurvaABCBar>;
  loading: boolean;
}

export default function CurvaABCBars({ data, loading }: CurvaABCBarsProps) {
  if (loading) {
    return (
      <div className="space-y-3">
        {[1, 2, 3].map((i) => (
          <div key={i} className="h-16 bg-gray-50 animate-pulse rounded" />
        ))}
      </div>
    );
  }
  if (!data) return <p className="text-sm text-gray-500">Sem dados</p>;

  const rows: Array<{ key: string; label: string; pctClientes: string; barColor: string }> = [
    { key: 'A', label: 'Curva A', pctClientes: '20%', barColor: 'bg-vitao-green' },
    { key: 'B', label: 'Curva B', pctClientes: '30%', barColor: 'bg-vitao-blue' },
    { key: 'C', label: 'Curva C', pctClientes: '50%', barColor: 'bg-gray-400' },
  ];

  return (
    <div className="space-y-3">
      {rows.map((r) => {
        const item = data[r.key];
        if (!item) return null;
        const pct = item.pct_faturamento ?? 0;
        return (
          <div key={r.key}>
            <div className="flex items-center justify-between text-xs mb-1">
              <span className="font-semibold text-gray-700">
                {r.label} ({r.pctClientes})
              </span>
              <span className="text-gray-500">
                {(item.clientes ?? 0).toLocaleString('pt-BR')} clientes
              </span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-4 relative overflow-hidden">
              <div
                className={`${r.barColor} h-full rounded-full flex items-center justify-end pr-2 transition-all`}
                style={{ width: `${Math.max(pct, 4)}%` }}
              >
                <span className="text-white text-[10px] font-bold">{pct.toFixed(0)}%</span>
              </div>
            </div>
            <div className="text-xs text-gray-500 mt-1">
              {pct.toFixed(0)}% do faturamento • {formatBRL(item.valor ?? 0)}
            </div>
          </div>
        );
      })}
    </div>
  );
}
