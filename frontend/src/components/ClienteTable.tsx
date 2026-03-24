'use client';

import { ClienteRegistro, formatBRL } from '@/lib/api';
import StatusBadge from './StatusBadge';

// ---------------------------------------------------------------------------
// ClienteTable — reusable data table for clientes
// ---------------------------------------------------------------------------

interface ClienteTableProps {
  registros: ClienteRegistro[];
  loading?: boolean;
  onRowClick?: (cliente: ClienteRegistro) => void;
}

const SKELETON_ROWS = 8;

export default function ClienteTable({
  registros,
  loading = false,
  onRowClick,
}: ClienteTableProps) {
  if (loading) {
    return (
      <div className="overflow-x-auto scrollbar-thin">
        <table className="w-full text-sm">
          <thead>
            <TableHead />
          </thead>
          <tbody>
            {Array.from({ length: SKELETON_ROWS }).map((_, i) => (
              <tr key={i} className="border-t border-gray-100">
                {Array.from({ length: 10 }).map((__, j) => (
                  <td key={j} className="px-3 py-2.5">
                    <div className="h-3.5 bg-gray-100 animate-pulse rounded" style={{ width: `${60 + Math.random() * 40}%` }} />
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    );
  }

  if (registros.length === 0) {
    return (
      <div className="py-16 text-center text-gray-400 text-sm">
        Nenhum cliente encontrado com os filtros selecionados.
      </div>
    );
  }

  return (
    <div className="overflow-x-auto scrollbar-thin">
      <table className="w-full text-sm">
        <thead>
          <TableHead />
        </thead>
        <tbody>
          {registros.map((c) => (
            <tr
              key={c.cnpj}
              className={`border-t border-gray-100 hoverable ${
                onRowClick ? 'cursor-pointer' : ''
              }`}
              onClick={() => onRowClick?.(c)}
            >
              <td className="px-3 py-2.5 font-mono text-xs text-gray-500 whitespace-nowrap">
                {formatCnpj(c.cnpj)}
              </td>
              <td className="px-3 py-2.5 max-w-[200px]">
                <p className="font-medium text-gray-900 truncate">{c.nome_fantasia ?? '—'}</p>
                {c.razao_social && c.razao_social !== c.nome_fantasia && (
                  <p className="text-[11px] text-gray-400 truncate">{c.razao_social}</p>
                )}
              </td>
              <td className="px-3 py-2.5 whitespace-nowrap">
                <StatusBadge value={c.situacao} variant="situacao" />
              </td>
              <td className="px-3 py-2.5 text-gray-700 whitespace-nowrap">{c.consultor ?? '—'}</td>
              <td className="px-3 py-2.5 whitespace-nowrap">
                <StatusBadge value={c.sinaleiro} variant="sinaleiro" />
              </td>
              <td className="px-3 py-2.5 whitespace-nowrap">
                <StatusBadge value={c.prioridade} variant="prioridade" />
              </td>
              <td className="px-3 py-2.5 whitespace-nowrap">
                {c.curva_abc ? (
                  <StatusBadge value={c.curva_abc} variant="abc" />
                ) : (
                  <span className="text-gray-300">—</span>
                )}
              </td>
              <td className="px-3 py-2.5 text-right whitespace-nowrap font-mono text-gray-800">
                {c.faturamento_total != null ? formatBRL(c.faturamento_total) : '—'}
              </td>
              <td className="px-3 py-2.5 text-right whitespace-nowrap text-gray-700">
                {c.score != null ? c.score.toFixed(1) : '—'}
              </td>
              <td className="px-3 py-2.5 text-gray-500 whitespace-nowrap text-xs">
                {c.cidade && c.uf ? `${c.cidade}/${c.uf}` : (c.uf ?? '—')}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function TableHead() {
  return (
    <tr className="bg-gray-50 text-left">
      {[
        'CNPJ',
        'Cliente',
        'Situacao',
        'Consultor',
        'Sinaleiro',
        'Prioridade',
        'ABC',
        'Faturamento',
        'Score',
        'Localidade',
      ].map((h) => (
        <th
          key={h}
          className="px-3 py-2 text-[11px] font-semibold text-gray-500 uppercase tracking-wide whitespace-nowrap"
        >
          {h}
        </th>
      ))}
    </tr>
  );
}

function formatCnpj(cnpj: string): string {
  const digits = cnpj.replace(/\D/g, '').padStart(14, '0');
  if (digits.length !== 14) return cnpj;
  return `${digits.slice(0, 2)}.${digits.slice(2, 5)}.${digits.slice(5, 8)}/${digits.slice(8, 12)}-${digits.slice(12)}`;
}
