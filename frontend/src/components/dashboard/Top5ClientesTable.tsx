'use client';

import { Top5Cliente, formatBRL } from '@/lib/api';

// ---------------------------------------------------------------------------
// Top5ClientesTable — tabela compacta com top 5 clientes do mês
// Extraído de page.tsx (hero section) para reutilização em /carteira
// ---------------------------------------------------------------------------

interface Top5ClientesTableProps {
  rows: Top5Cliente[];
  loading: boolean;
}

export default function Top5ClientesTable({ rows, loading }: Top5ClientesTableProps) {
  if (loading) {
    return (
      <div className="space-y-2">
        {[1, 2, 3, 4, 5].map((i) => (
          <div key={i} className="h-8 bg-gray-50 animate-pulse rounded" />
        ))}
      </div>
    );
  }
  if (rows.length === 0) {
    return <p className="text-sm text-gray-500">Sem vendas no mes ainda</p>;
  }

  const curvaBg: Record<string, string> = {
    A: 'bg-vitao-green text-white',
    B: 'bg-vitao-blue text-white',
    C: 'bg-gray-400 text-white',
  };

  return (
    <ul className="divide-y divide-gray-100">
      {rows.map((r, i) => (
        <li key={r.cnpj} className="flex items-center gap-3 py-2 text-xs">
          <span className="text-gray-400 font-bold w-4">{i + 1}</span>
          <span className="flex-1 min-w-0 truncate font-medium text-gray-900">
            {r.nome_fantasia}
          </span>
          {r.curva_abc && (
            <span
              className={`text-[9px] font-bold rounded-full px-2 py-0.5 ${
                curvaBg[r.curva_abc] ?? 'bg-gray-200 text-gray-600'
              }`}
            >
              {r.curva_abc}
            </span>
          )}
          <span className="font-mono font-semibold text-gray-900">
            {formatBRL(r.faturamento_mes)}
          </span>
          <span className="text-gray-500 w-16 text-right">{r.pedidos_mes ?? 0} ped.</span>
        </li>
      ))}
    </ul>
  );
}
