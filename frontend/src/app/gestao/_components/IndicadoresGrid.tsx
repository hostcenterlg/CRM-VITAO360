'use client';

// IndicadoresGrid — grid 3x3 dos 9 indicadores DDE
// R8: valor null → "—". Nunca inferir ou fabricar valor.
// Hover mostra descrição do indicador.

import type { IndicadoresDDE } from '@/lib/api';

interface IndicadoresGridProps {
  indicadores: IndicadoresDDE;
}

interface IndicadorConfig {
  key: keyof IndicadoresDDE;
  label: string;
  descricao: string;
  unidade: 'pct' | 'dias' | 'score';
  /** Acima deste valor é negativo (quanto menor melhor) */
  limiteAlerta?: number;
  /** Acima deste valor é positivo (quanto maior melhor) */
  limiteBom?: number;
  invertido?: boolean; // true = menor é melhor (ex: devolução, inadimplência)
}

const INDICADORES: IndicadorConfig[] = [
  { key: 'I1', label: 'Margem Bruta',        descricao: 'Receita Líquida menos CMV. Fase B — aguarda dados SAP de custo de produtos.', unidade: 'pct', limiteBom: 30, limiteAlerta: 15 },
  { key: 'I2', label: 'Margem Contribuição',  descricao: 'Receita Líquida menos todas as despesas variáveis do cliente. Principal indicador de rentabilidade.', unidade: 'pct', limiteBom: 15, limiteAlerta: 5 },
  { key: 'I3', label: 'Comissão %',           descricao: 'Comissão do representante como percentual da Receita Líquida. Acima de 8% é alerta.', unidade: 'pct', limiteAlerta: 8, invertido: true },
  { key: 'I4', label: 'Frete %',              descricao: 'Custo de frete CT-e sobre a Receita Líquida. Acima de 5% comprime margem.', unidade: 'pct', limiteAlerta: 5, invertido: true },
  { key: 'I5', label: 'Verba %',              descricao: 'Verbas negociadas (promoção, promotor, rebate) como % da Receita Líquida.', unidade: 'pct', limiteAlerta: 6, invertido: true },
  { key: 'I6', label: 'Inadimplência %',      descricao: 'Valor em débito provisionado como perda sobre o faturamento total do período.', unidade: 'pct', limiteAlerta: 3, invertido: true },
  { key: 'I7', label: 'Devolução %',          descricao: 'Valor de devoluções sobre o faturamento bruto. Acima de 3% é sinal de problema de qualidade ou sell-out.', unidade: 'pct', limiteAlerta: 3, invertido: true },
  { key: 'I8', label: 'Aging (dias)',         descricao: 'Prazo médio de recebimento ponderado pelos débitos em aberto. Acima de 45 dias é alerta de crédito.', unidade: 'dias', limiteAlerta: 45, invertido: true },
  { key: 'I9', label: 'Score Saúde',          descricao: 'Score composto 0-100 calculado a partir de I1–I8. Sintetiza a saúde financeira do relacionamento comercial.', unidade: 'score', limiteBom: 70, limiteAlerta: 30 },
];

function formatValor(val: number | null, unidade: 'pct' | 'dias' | 'score'): string {
  if (val == null) return '—';
  if (unidade === 'pct') return `${val.toFixed(1)}%`;
  if (unidade === 'dias') return `${Math.round(val)}d`;
  return String(Math.round(val));
}

function getColorClass(
  val: number | null,
  cfg: IndicadorConfig
): { text: string; bg: string } {
  if (val == null) return { text: 'text-gray-500', bg: 'bg-gray-50' };

  if (cfg.invertido) {
    if (cfg.limiteAlerta != null && val > cfg.limiteAlerta) return { text: 'text-red-700', bg: 'bg-red-50' };
    if (cfg.limiteAlerta != null && val > cfg.limiteAlerta * 0.7) return { text: 'text-amber-700', bg: 'bg-amber-50' };
    return { text: 'text-green-700', bg: 'bg-green-50' };
  }

  if (cfg.limiteBom != null && val >= cfg.limiteBom) return { text: 'text-green-700', bg: 'bg-green-50' };
  if (cfg.limiteAlerta != null && val >= cfg.limiteAlerta) return { text: 'text-amber-700', bg: 'bg-amber-50' };
  return { text: 'text-red-700', bg: 'bg-red-50' };
}

export function IndicadoresGrid({ indicadores }: IndicadoresGridProps) {
  return (
    <div className="grid grid-cols-3 gap-3" role="list" aria-label="Indicadores DDE">
      {INDICADORES.map((cfg) => {
        const val = indicadores[cfg.key];
        const { text, bg } = getColorClass(val, cfg);
        const formatted = formatValor(val, cfg.unidade);

        return (
          <div
            key={cfg.key}
            className={`rounded-lg border border-gray-200 p-3 ${bg} cursor-default group relative`}
            role="listitem"
            aria-label={`${cfg.label}: ${formatted}`}
          >
            {/* Tooltip */}
            <div className="absolute z-10 hidden group-hover:block bottom-full left-1/2 -translate-x-1/2 mb-2 w-56 bg-gray-900 text-white text-xs rounded-lg px-3 py-2 shadow-lg pointer-events-none">
              <p className="font-semibold mb-1">{cfg.label}</p>
              <p className="leading-relaxed opacity-90">{cfg.descricao}</p>
              <div className="absolute top-full left-1/2 -translate-x-1/2 w-0 h-0 border-l-4 border-r-4 border-t-4 border-transparent border-t-gray-900" />
            </div>

            <div className="flex items-start justify-between gap-1 mb-1">
              <span className="text-xs font-mono text-gray-400">{cfg.key}</span>
              <span className={`text-lg font-extrabold tabular-nums leading-none ${text}`}>
                {formatted}
              </span>
            </div>
            <p className="text-xs text-gray-600 leading-snug">{cfg.label}</p>
          </div>
        );
      })}
    </div>
  );
}
