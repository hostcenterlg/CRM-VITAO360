'use client';

// CascataPL — tabela de 21 linhas da cascata DDE P&L
// Colunas: Código | Conta | Valor (BRL) | % Receita | Tier | Fonte
// R8: valor null → "—", pct null → "—". NUNCA inferir valor de PENDENTE/NULL.
// Linhas com sinal="=" destacadas (negrito + bg-gray-50).

import { TierPill } from './TierPill';
import type { LinhaDRE } from '@/lib/api';
import { formatBRL } from '@/lib/api';

interface CascataPLProps {
  linhas: LinhaDRE[];
}

// Labels de fonte para chips compactos
const FONTE_CHIP: Record<string, string> = {
  SH: 'Sales Hunter',
  SAP: 'SAP',
  LOG: 'LOG',
  CALC: 'Calculado',
  DB: 'Banco',
};

function FonteChip({ fonte }: { fonte: string }) {
  // Extrai sigla da fonte para chip (primeiras 4 letras ou sigla mapeada)
  const sigla = (Object.keys(FONTE_CHIP).find((k) => fonte.toUpperCase().includes(k)) ?? fonte.slice(0, 4)).toUpperCase();
  const label = FONTE_CHIP[sigla] ?? fonte;
  return (
    <span
      className="inline-flex items-center px-1.5 py-0.5 rounded bg-gray-100 text-gray-600 text-xs font-mono border border-gray-200 whitespace-nowrap"
      title={label}
      aria-label={`Fonte: ${label}`}
    >
      {sigla}
    </span>
  );
}

function formatPct(val: number | null): string {
  if (val == null) return '—';
  return `${val.toFixed(1)}%`;
}

export function CascataPL({ linhas }: CascataPLProps) {
  if (!linhas || linhas.length === 0) {
    return (
      <div className="flex items-center justify-center py-12 text-sm text-gray-500">
        Cascata P&L indisponível — nenhuma linha retornada pela API.
      </div>
    );
  }

  return (
    <div className="overflow-x-auto rounded-lg border border-gray-200 shadow-sm" role="region" aria-label="Cascata P&L DDE">
      <table className="min-w-full text-xs" aria-label="Linhas da cascata DDE">
        <thead>
          <tr className="bg-gray-50 border-b border-gray-200">
            <th scope="col" className="px-3 py-2 text-left font-semibold text-gray-600 w-14">Cód.</th>
            <th scope="col" className="px-3 py-2 text-left font-semibold text-gray-600">Conta</th>
            <th scope="col" className="px-3 py-2 text-right font-semibold text-gray-600 w-32 tabular-nums">Valor</th>
            <th scope="col" className="px-3 py-2 text-right font-semibold text-gray-600 w-20 tabular-nums">% Rec.</th>
            <th scope="col" className="px-3 py-2 text-center font-semibold text-gray-600 w-24">Tier</th>
            <th scope="col" className="px-3 py-2 text-center font-semibold text-gray-600 w-16">Fonte</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-100">
          {linhas.map((linha) => {
            const isTotal = linha.sinal === '=';
            const isPendente = linha.classificacao === 'PENDENTE' || linha.classificacao === 'NULL';
            return (
              <tr
                key={linha.codigo}
                className={`${isTotal ? 'bg-gray-50' : 'bg-white hover:bg-gray-50'} transition-colors`}
              >
                <td className="px-3 py-2 font-mono text-gray-500 align-top">
                  <div className="flex items-center gap-1">
                    {linha.sinal === '+' && <span className="text-green-600 font-bold w-3">+</span>}
                    {linha.sinal === '-' && <span className="text-red-500 font-bold w-3">−</span>}
                    {linha.sinal === '=' && <span className="text-gray-400 w-3">=</span>}
                    <span className={`${isTotal ? 'font-semibold text-gray-700' : 'text-gray-500'}`}>
                      {linha.codigo}
                    </span>
                  </div>
                </td>
                <td className="px-3 py-2 align-top">
                  <span className={`leading-snug ${isTotal ? 'font-semibold text-gray-800' : 'text-gray-700'}`}>
                    {linha.conta}
                  </span>
                </td>
                <td className={`px-3 py-2 text-right tabular-nums align-top ${isPendente ? 'text-gray-400 italic' : isTotal ? 'font-semibold text-gray-800' : 'text-gray-700'}`}>
                  {linha.valor != null ? formatBRL(linha.valor) : '—'}
                </td>
                <td className={`px-3 py-2 text-right tabular-nums align-top ${isPendente ? 'text-gray-400 italic' : 'text-gray-600'}`}>
                  {formatPct(linha.pct_receita)}
                </td>
                <td className="px-3 py-2 text-center align-top">
                  <TierPill
                    tier={linha.classificacao}
                    title={linha.observacao || undefined}
                  />
                </td>
                <td className="px-3 py-2 text-center align-top">
                  <FonteChip fonte={linha.fonte} />
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
