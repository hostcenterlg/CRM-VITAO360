'use client';

// Componente CustomTooltip reutilizavel para graficos Recharts
// Card branco com sombra, titulo, linhas de dados formatados
// Suporta modo BRL, modo positivacao e modo performance (meta vs realizado)

import { formatBRL, formatPercent } from '@/lib/api';

// ---------------------------------------------------------------------------
// Tipos internos — espelha o que Recharts injeta em `content`
// ---------------------------------------------------------------------------

export interface TooltipPayloadEntry {
  name: string;
  value: number;
  color?: string;
  dataKey?: string;
}

// ---------------------------------------------------------------------------
// Props do CustomTooltip
// ---------------------------------------------------------------------------

export interface CustomTooltipProps {
  // Injetados automaticamente pelo Recharts
  active?: boolean;
  payload?: TooltipPayloadEntry[];
  label?: string | number;

  // Modos de formatacao
  /** Formata valores como BRL (R$) */
  isBRL?: boolean;
  /**
   * Modo positivacao: payload deve ter `positivados` e `total` ou `objetivo`.
   * Exibe "X clientes de Y positivados (Z%)"
   */
  modoPositivacao?: boolean;
  /**
   * Modo performance: payload deve ter `faturamento` e `meta`.
   * Exibe "Realizado: R$ X / Meta: R$ Y (Z%)"
   */
  modoPerformance?: boolean;
  /**
   * Adiciona linha de delta percentual vs mes anterior quando dois valores
   * sao fornecidos (primeiro = atual, segundo = anterior).
   * Usado no grafico de Evolucao de Vendas.
   */
  mostrarDeltaMesAnterior?: boolean;
}

// ---------------------------------------------------------------------------
// Helpers de formatacao internos
// ---------------------------------------------------------------------------

function formatValor(value: number, isBRL: boolean): string {
  if (isBRL) {
    return formatBRL(value);
  }
  return value.toLocaleString('pt-BR');
}

function calcDelta(atual: number, anterior: number): string {
  if (anterior === 0) return '';
  const delta = ((atual - anterior) / anterior) * 100;
  const sinal = delta >= 0 ? '+' : '';
  return `${sinal}${formatPercent(delta)} vs mes anterior`;
}

// ---------------------------------------------------------------------------
// Componente principal
// ---------------------------------------------------------------------------

export default function CustomTooltip({
  active,
  payload,
  label,
  isBRL = false,
  modoPositivacao = false,
  modoPerformance = false,
  mostrarDeltaMesAnterior = false,
}: CustomTooltipProps) {
  if (!active || !payload || payload.length === 0) return null;

  // -------------------------------------------------------------------------
  // Modo Positivacao
  // -------------------------------------------------------------------------
  if (modoPositivacao) {
    const positivadosEntry = payload.find(
      (p) => p.dataKey === 'positivados' || p.name?.toLowerCase().includes('positiv')
    );
    const totalEntry = payload.find(
      (p) =>
        p.dataKey === 'total' ||
        p.dataKey === 'objetivo' ||
        p.name?.toLowerCase().includes('total') ||
        p.name?.toLowerCase().includes('objetivo')
    );

    const positivados = positivadosEntry?.value ?? 0;
    const total = totalEntry?.value ?? 0;
    const pct = total > 0 ? (positivados / total) * 100 : 0;

    return (
      <div className="bg-white border border-gray-200 rounded-lg shadow-lg p-3 text-xs min-w-[160px]">
        {label != null && (
          <p className="font-semibold text-gray-700 mb-2 border-b border-gray-100 pb-1">
            {label}
          </p>
        )}
        <p className="text-gray-800 font-medium">
          {positivados.toLocaleString('pt-BR')} clientes de{' '}
          {total.toLocaleString('pt-BR')} positivados
        </p>
        <p className="mt-1" style={{ color: pct >= 70 ? '#00B050' : pct >= 40 ? '#FFC000' : '#FF0000' }}>
          {formatPercent(pct)} de positivacao
        </p>
      </div>
    );
  }

  // -------------------------------------------------------------------------
  // Modo Performance (meta vs realizado)
  // -------------------------------------------------------------------------
  if (modoPerformance) {
    const realizadoEntry = payload.find(
      (p) =>
        p.dataKey === 'faturamento' ||
        p.dataKey === 'realizado' ||
        p.name?.toLowerCase().includes('realizado')
    );
    const metaEntry = payload.find(
      (p) => p.dataKey === 'meta' || p.name?.toLowerCase().includes('meta')
    );

    const realizado = realizadoEntry?.value ?? 0;
    const meta = metaEntry?.value ?? 0;
    const pct = meta > 0 ? (realizado / meta) * 100 : 0;

    return (
      <div className="bg-white border border-gray-200 rounded-lg shadow-lg p-3 text-xs min-w-[190px]">
        {label != null && (
          <p className="font-semibold text-gray-700 mb-2 border-b border-gray-100 pb-1">
            {label}
          </p>
        )}
        <div className="space-y-1">
          <p className="text-gray-800">
            <span className="font-medium" style={{ color: realizadoEntry?.color ?? '#00B050' }}>
              Realizado:{' '}
            </span>
            {formatBRL(realizado)}
          </p>
          {meta > 0 && (
            <p className="text-gray-800">
              <span className="font-medium" style={{ color: metaEntry?.color ?? '#2563eb' }}>
                Meta:{' '}
              </span>
              {formatBRL(meta)}
            </p>
          )}
          {meta > 0 && (
            <p
              className="font-semibold mt-1 pt-1 border-t border-gray-100"
              style={{ color: pct >= 80 ? '#00B050' : pct >= 50 ? '#FFC000' : '#FF0000' }}
            >
              {formatPercent(pct)} atingido
            </p>
          )}
        </div>
      </div>
    );
  }

  // -------------------------------------------------------------------------
  // Modo padrao (generico)
  // -------------------------------------------------------------------------
  const linhas = payload.filter((p) => p.value != null);

  // Delta vs mes anterior: requer ao menos 2 linhas onde [0]=atual, [1]=anterior
  const deltaMesAnterior =
    mostrarDeltaMesAnterior && linhas.length >= 2
      ? calcDelta(linhas[0]?.value ?? 0, linhas[1]?.value ?? 0)
      : null;

  return (
    <div className="bg-white border border-gray-200 rounded-lg shadow-lg p-3 text-xs min-w-[150px]">
      {label != null && (
        <p className="font-semibold text-gray-700 mb-2 border-b border-gray-100 pb-1">
          {label}
        </p>
      )}
      <div className="space-y-1">
        {linhas.map((p, i) => (
          <p key={i} className="text-gray-700">
            <span className="font-medium" style={{ color: p.color ?? '#374151' }}>
              {p.name}:{' '}
            </span>
            {formatValor(p.value, isBRL)}
          </p>
        ))}
        {deltaMesAnterior && (
          <p
            className="mt-1 pt-1 border-t border-gray-100 font-medium"
            style={{
              color:
                linhas[0] && linhas[1] && linhas[0].value >= linhas[1].value
                  ? '#00B050'
                  : '#FF0000',
            }}
          >
            {deltaMesAnterior}
          </p>
        )}
      </div>
    </div>
  );
}
