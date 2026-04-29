'use client';

import { useCallback, useEffect, useRef, useState } from 'react';
import {
  AtendimentoHistoricoItem,
  BriefingIAResponse,
  BriefingResponse,
  ChurnRiskResponse,
  ClienteRegistro,
  ClienteScoreResponse,
  MensagemWhatsAppResponse,
  ScoreBreakdown,
  VendaMensal,
  VendaPedidoItem,
  WhatsAppConversaResponse,
  WhatsAppEnviarResponse,
  WhatsAppMensagem,
  WhatsAppStatus,
  enviarWhatsApp,
  fetchAtendimentosHistorico,
  fetchBriefingIA,
  fetchChurnRisk,
  fetchCliente,
  fetchClienteScore,
  fetchVendasCliente,
  fetchWhatsAppConversa,
  fetchWhatsAppStatus,
  formatBRL,
  getBriefing,
  gerarMensagemWhatsApp,
} from '@/lib/api';
import { useAuth } from '@/contexts/AuthContext';
import StatusBadge from './StatusBadge';
import AtendimentoForm from './AtendimentoForm';
import { LineChart, Line, ResponsiveContainer, Tooltip } from 'recharts';

// ---------------------------------------------------------------------------
// ClienteDetalhe — drawer lateral com ficha completa do cliente
// Blocos colapsáveis: Identidade, Status, Financeiro, Timeline, Compras, Score, Histórico, IA
// Bloco Financeiro oculto para consultor_externo (Julio)
// ---------------------------------------------------------------------------

interface ClienteDetalheProps {
  cnpj: string | null;
  onClose: () => void;
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function formatCnpj(cnpj: string): string {
  const d = cnpj.replace(/\D/g, '').padStart(14, '0');
  if (d.length !== 14) return cnpj;
  return `${d.slice(0, 2)}.${d.slice(2, 5)}.${d.slice(5, 8)}/${d.slice(8, 12)}-${d.slice(12)}`;
}

function formatDate(value?: string): string {
  if (!value) return '—';
  const [datePart] = value.split('T');
  const parts = datePart.split('-');
  if (parts.length !== 3) return value;
  return `${parts[2]}/${parts[1]}/${parts[0]}`;
}

// ---------------------------------------------------------------------------
// Bloco colapsável genérico
// ---------------------------------------------------------------------------

interface BlocoProps {
  title: string;
  open: boolean;
  onToggle: () => void;
  children: React.ReactNode;
  badge?: React.ReactNode;
  id?: string;
}

function Bloco({ title, open, onToggle, children, badge, id }: BlocoProps) {
  // Gera ID estavel baseado no titulo para aria-labelledby
  const sectionId = id ?? `bloco-${title.toLowerCase().replace(/\s+/g, '-').replace(/[^a-z0-9-]/g, '')}`;
  const btnId = `${sectionId}-btn`;
  const panelId = `${sectionId}-panel`;

  return (
    <div className="border border-gray-200 rounded-lg overflow-hidden">
      <button
        id={btnId}
        type="button"
        onClick={onToggle}
        className="w-full flex items-center justify-between px-4 py-3 bg-gray-50 hover:bg-gray-100 transition-colors text-left"
        aria-expanded={open}
        aria-controls={panelId}
      >
        <div className="flex items-center gap-2">
          <span className="text-[11px] font-semibold text-gray-600 uppercase tracking-wider">
            {title}
          </span>
          {badge}
        </div>
        <svg
          className={`w-4 h-4 text-gray-400 flex-shrink-0 transition-transform duration-200 ${open ? 'rotate-180' : ''}`}
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
          aria-hidden="true"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>
      <div
        id={panelId}
        role="region"
        aria-labelledby={btnId}
        className={`transition-all duration-200 overflow-hidden ${open ? 'max-h-[2000px] opacity-100' : 'max-h-0 opacity-0'}`}
        aria-hidden={!open}
      >
        <div className="px-4 py-3 space-y-1.5">{children}</div>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// FieldRow
// ---------------------------------------------------------------------------

interface FieldRowProps {
  label: string;
  value?: unknown;
  money?: boolean;
  mono?: boolean;
  badge?: React.ReactNode;
}

function FieldRow({ label, value, money, mono, badge }: FieldRowProps) {
  if (badge == null && (value == null || value === '')) return null;
  const display = money && typeof value === 'number'
    ? formatBRL(value)
    : value != null ? String(value) : '';
  return (
    <div className="flex justify-between items-start gap-4 py-1 border-b border-gray-50 text-sm">
      <span className="text-gray-500 flex-shrink-0 text-xs">{label}</span>
      {badge ?? (
        <span className={`text-gray-900 text-right text-xs font-medium ${mono ? 'font-mono' : ''}`}>
          {display}
        </span>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Score Breakdown visual
// ---------------------------------------------------------------------------

interface ScoreBarProps {
  label: string;
  peso: string;
  valor: number;
  pontos: number;
}

const SCORE_FATOR_COLORS: Record<string, string> = {
  urgencia:  '#EF4444',
  valor:     '#7C3AED',
  follow_up: '#F59E0B',
  sinal:     '#2563EB',
  tentativa: '#10B981',
  situacao:  '#6B7280',
};

function ScoreBarRow({ label, peso, valor, pontos }: ScoreBarProps) {
  // Defensivo: campos do breakdown podem vir null do backend (sem dado)
  const safeValor  = valor  == null || !Number.isFinite(valor)  ? 0 : valor;
  const safePontos = pontos == null || !Number.isFinite(pontos) ? 0 : pontos;
  const pct = Math.min(100, Math.max(0, safeValor));
  const colorKey = label.toLowerCase().replace(/ /g, '_').replace(/[()%]/g, '');
  const color = SCORE_FATOR_COLORS[colorKey] ?? '#9CA3AF';

  return (
    <div className="flex items-center gap-2 py-0.5">
      <span className="text-[11px] text-gray-500 w-32 flex-shrink-0">
        {label} <span className="text-gray-400">({peso})</span>
      </span>
      <div className="flex-1 h-2 bg-gray-100 rounded-full overflow-hidden">
        <div
          className="h-full rounded-full"
          style={{ width: `${pct}%`, background: color, transition: 'width 400ms ease-out' }}
        />
      </div>
      <span className="text-[11px] font-semibold text-gray-700 w-8 text-right tabular-nums">
        {safeValor.toFixed(0)}
      </span>
      <span className="text-[11px] text-gray-400 w-10 text-right tabular-nums">
        {safePontos.toFixed(1)}pt
      </span>
    </div>
  );
}

function ScoreBreakdownDisplay({
  score,
  breakdown,
}: {
  score: number;
  breakdown?: ScoreBreakdown;
}) {
  const scoreColor = score >= 70 ? '#00B050' : score >= 40 ? '#FFC000' : '#FF0000';
  const scorePct = Math.min(100, Math.max(0, score));

  return (
    <div className="space-y-2 pt-1">
      {/* Barra principal do score */}
      <div className="flex items-center gap-2">
        <span className="text-xs text-gray-500 w-14 flex-shrink-0">Score</span>
        <div className="flex-1 h-3 bg-gray-100 rounded-full overflow-hidden">
          <div
            className="h-full rounded-full"
            style={{ width: `${scorePct}%`, background: scoreColor, transition: 'width 400ms ease-out' }}
          />
        </div>
        <span
          className="text-sm font-bold tabular-nums w-8 text-right"
          style={{ color: scoreColor }}
        >
          {score.toFixed(0)}
        </span>
      </div>

      {/* Breakdown por fator */}
      {breakdown && (
        <div className="mt-2 pl-2 border-l-2 border-gray-100 space-y-0.5">
          <ScoreBarRow
            label="urgencia"
            peso="30%"
            valor={breakdown.urgencia}
            pontos={breakdown.urgencia * 0.3}
          />
          <ScoreBarRow
            label="valor"
            peso="25%"
            valor={breakdown.valor}
            pontos={breakdown.valor * 0.25}
          />
          <ScoreBarRow
            label="follow_up"
            peso="20%"
            valor={breakdown.follow_up}
            pontos={breakdown.follow_up * 0.2}
          />
          <ScoreBarRow
            label="sinal"
            peso="15%"
            valor={breakdown.sinal}
            pontos={breakdown.sinal * 0.15}
          />
          <ScoreBarRow
            label="tentativa"
            peso="5%"
            valor={breakdown.tentativa}
            pontos={breakdown.tentativa * 0.05}
          />
          <ScoreBarRow
            label="situacao"
            peso="5%"
            valor={breakdown.situacao}
            pontos={breakdown.situacao * 0.05}
          />
          <div className="flex justify-between items-center pt-1 mt-1 border-t border-gray-100">
            <span className="text-[11px] font-semibold text-gray-600 uppercase tracking-wide">
              Score Total
            </span>
            <span className="text-sm font-bold tabular-nums" style={{ color: scoreColor }}>
              {score.toFixed(1)}
            </span>
          </div>
          <p className="text-[10px] text-gray-400 italic">
            Calculado automaticamente pelo Motor
          </p>
        </div>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Bloco Financeiro — mini bar chart vendas mensais
// ---------------------------------------------------------------------------

function VendasMiniChart({ vendas }: { vendas: VendaMensal[] }) {
  if (!vendas || vendas.length === 0) return null;
  const max = Math.max(...vendas.map((v) => v.valor), 1);

  return (
    <div className="pt-1">
      <p className="text-[11px] text-gray-500 mb-1.5 font-medium">Vendas mes a mes</p>
      <div className="flex items-end gap-0.5 h-12">
        {vendas.map((v) => {
          const pct = v.valor > 0 ? (v.valor / max) * 100 : 0;
          const barColor = v.valor > 0 ? '#00B050' : '#E5E7EB';
          return (
            <div
              key={v.mes}
              className="flex flex-col items-center gap-0.5 flex-1"
              title={v.valor > 0 ? formatBRL(v.valor) : '—'}
            >
              <div className="w-full flex items-end h-9">
                <div
                  className="w-full rounded-t"
                  style={{
                    height: pct > 0 ? `${Math.max(4, pct)}%` : 4,
                    background: barColor,
                    transition: 'height 400ms ease-out',
                  }}
                />
              </div>
              <span className="text-[9px] text-gray-400 leading-none">{v.mes}</span>
            </div>
          );
        })}
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Score Sparkline — mini gráfico Recharts (100x40)
// Usa vendas mensais como proxy de evolucao quando nao ha historico de score
// ---------------------------------------------------------------------------

interface ScoreSparklineProps {
  vendas: VendaMensal[];
  score: number;
}

function ScoreSparkline({ vendas, score }: ScoreSparklineProps) {
  if (!vendas || vendas.length < 2) return null;

  const scoreColor = score >= 70 ? '#00B050' : score >= 40 ? '#FFC000' : '#FF0000';

  // Normalizar valores para exibir evolucao relativa
  const data = vendas.map((v) => ({ mes: v.mes, valor: v.valor }));

  return (
    <div className="pt-1">
      <p className="text-[11px] text-gray-500 mb-1 font-medium">Evolucao faturamento</p>
      <div style={{ width: '100%', height: 40 }}>
        <ResponsiveContainer width="100%" height={40}>
          <LineChart data={data} margin={{ top: 2, right: 2, bottom: 2, left: 2 }}>
            <Line
              type="monotone"
              dataKey="valor"
              stroke={scoreColor}
              strokeWidth={1.5}
              dot={false}
              isAnimationActive={false}
            />
            <Tooltip
              contentStyle={{ fontSize: 10, padding: '2px 6px', borderRadius: 4 }}
              formatter={(value) => [formatBRL(Number(value ?? 0)), '']}
              labelFormatter={(label) => String(label ?? '')}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Ultimas Compras — tabela compacta com ultimos pedidos do cliente
// ---------------------------------------------------------------------------

interface UltimasComprasProps {
  cnpj: string;
}

const STATUS_VENDA_COLORS: Record<string, string> = {
  DIGITADO:  '#6B7280',
  LIBERADO:  '#2563EB',
  FATURADO:  '#7C3AED',
  ENTREGUE:  '#00B050',
  CANCELADO: '#EF4444',
};

function UltimasComprasBloco({ cnpj }: UltimasComprasProps) {
  const [vendas, setVendas] = useState<VendaPedidoItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setLoading(true);
    setError(null);
    fetchVendasCliente(cnpj, 5)
      .then(setVendas)
      .catch((e: Error) => setError(e.message))
      .finally(() => setLoading(false));
  }, [cnpj]);

  if (loading) {
    return (
      <div className="space-y-2 py-1">
        {Array.from({ length: 3 }).map((_, i) => (
          <div key={i} className="h-8 bg-gray-100 animate-pulse rounded" />
        ))}
      </div>
    );
  }

  if (error) {
    return (
      <p className="text-xs text-red-600 py-2">
        Erro ao carregar compras: {error}
      </p>
    );
  }

  if ((vendas ?? []).length === 0) {
    return (
      <p className="text-xs text-gray-400 py-2 italic">
        Nenhum pedido encontrado para este cliente.
      </p>
    );
  }

  return (
    <div className="overflow-x-auto -mx-1">
      <table className="w-full text-xs">
        <thead>
          <tr className="border-b border-gray-100">
            <th className="text-left text-[10px] font-semibold text-gray-500 uppercase py-1.5 px-1">Data</th>
            <th className="text-right text-[10px] font-semibold text-gray-500 uppercase py-1.5 px-1">Valor</th>
            <th className="text-right text-[10px] font-semibold text-gray-500 uppercase py-1.5 px-1">Status</th>
          </tr>
        </thead>
        <tbody>
          {(vendas ?? []).map((v) => {
            const cor = STATUS_VENDA_COLORS[v.status_pedido] ?? '#9CA3AF';
            return (
              <tr key={v.id} className="border-b border-gray-50 hover:bg-gray-50 transition-colors">
                <td className="py-1.5 px-1 text-gray-700 whitespace-nowrap">
                  {formatDate(v.data_pedido ?? '')}
                </td>
                <td className="py-1.5 px-1 text-right font-medium text-gray-900 tabular-nums whitespace-nowrap">
                  {formatBRL(v.valor_pedido)}
                </td>
                <td className="py-1.5 px-1 text-right whitespace-nowrap">
                  <span
                    className="inline-block text-[10px] font-semibold px-1.5 py-0.5 rounded"
                    style={{ backgroundColor: cor + '18', color: cor }}
                  >
                    {v.status_pedido}
                  </span>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Timeline Visual — ultimos 10 eventos em ordem cronologica
// ---------------------------------------------------------------------------

const TIMELINE_COLORS: Record<string, string> = {
  VENDA:    '#00B050',
  LIGACAO:  '#1D4ED8',
  LIGAÇÃO:  '#1D4ED8',
  WHATSAPP: '#25D366',
  EMAIL:    '#6B7280',
  VISITA:   '#7C3AED',
};

const TIMELINE_LABELS: Record<string, string> = {
  VENDA:    'Venda',
  LIGACAO:  'Ligacao',
  LIGAÇÃO:  'Ligacao',
  WHATSAPP: 'Whatsapp',
  EMAIL:    'Email',
  VISITA:   'Visita',
};

interface TimelineEventProps {
  item: AtendimentoHistoricoItem;
}

function TimelineEvent({ item }: TimelineEventProps) {
  const [expanded, setExpanded] = useState(false);

  const tipo = item.via_whatsapp ? 'WHATSAPP' : item.via_ligacao ? 'LIGACAO' : 'LIGACAO';
  const cor = TIMELINE_COLORS[tipo] ?? '#9CA3AF';
  const label = TIMELINE_LABELS[tipo] ?? 'Log';
  const maxLen = 70;
  const needsExpand = item.descricao.length > maxLen;

  return (
    <div className="flex gap-3 relative">
      {/* Linha vertical da timeline */}
      <div className="flex flex-col items-center flex-shrink-0">
        <div
          className="w-2.5 h-2.5 rounded-full ring-2 ring-white flex-shrink-0 mt-0.5 z-10 relative"
          style={{ backgroundColor: cor }}
          aria-hidden="true"
        />
        <div className="w-px flex-1 bg-gray-100 min-h-[16px]" aria-hidden="true" />
      </div>

      {/* Conteudo do evento */}
      <div className="flex-1 min-w-0 pb-3">
        <div className="flex items-start justify-between gap-2 flex-wrap">
          <div className="flex items-center gap-1.5 flex-wrap">
            <span
              className="text-[10px] font-bold px-1.5 py-0.5 rounded"
              style={{ backgroundColor: cor + '18', color: cor }}
            >
              {label}
            </span>
            <StatusBadge value={item.resultado} small />
          </div>
          <span className="text-[10px] text-gray-400 flex-shrink-0 tabular-nums">
            {formatDate(item.data_registro)}
          </span>
        </div>

        {item.consultor && (
          <p className="text-[11px] text-gray-500 mt-0.5">{item.consultor}</p>
        )}

        <button
          type="button"
          className="mt-0.5 text-left w-full"
          onClick={() => needsExpand && setExpanded((v) => !v)}
          aria-expanded={needsExpand ? expanded : undefined}
        >
          <p className={`text-[11px] text-gray-600 italic leading-relaxed ${needsExpand && !expanded ? 'line-clamp-2' : ''}`}>
            &quot;{item.descricao}&quot;
          </p>
        </button>

        {needsExpand && (
          <button
            type="button"
            onClick={() => setExpanded((v) => !v)}
            className="text-[10px] text-green-600 hover:underline mt-0.5"
          >
            {expanded ? 'Ver menos' : 'Ver mais'}
          </button>
        )}

        {item.acao_futura && (
          <p className="text-[11px] text-gray-500 mt-0.5">
            <span className="text-gray-400">Acao futura:</span> {item.acao_futura}
          </p>
        )}
      </div>
    </div>
  );
}

interface TimelineVisualProps {
  cnpj: string;
}

function TimelineVisual({ cnpj }: TimelineVisualProps) {
  const [itens, setItens] = useState<AtendimentoHistoricoItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [retryCount, setRetryCount] = useState(0);

  useEffect(() => {
    setLoading(true);
    setError(null);
    fetchAtendimentosHistorico(cnpj, 1, 10)
      .then((res) => setItens(res.itens ?? []))
      .catch((e: Error) => setError(e.message))
      .finally(() => setLoading(false));
  }, [cnpj, retryCount]);

  if (loading) {
    return (
      <div className="space-y-3 py-1">
        {Array.from({ length: 4 }).map((_, i) => (
          <div key={i} className="flex gap-3">
            <div className="w-2.5 h-2.5 rounded-full bg-gray-100 animate-pulse mt-0.5 flex-shrink-0" />
            <div className="flex-1 space-y-1">
              <div className="h-3 bg-gray-100 animate-pulse rounded w-2/3" />
              <div className="h-3 bg-gray-100 animate-pulse rounded w-full" />
            </div>
          </div>
        ))}
      </div>
    );
  }

  if (error) {
    return (
      <div className="py-2 space-y-2">
        <p className="text-xs text-red-600">Erro ao carregar timeline: {error}</p>
        <button
          type="button"
          onClick={() => setRetryCount((c) => c + 1)}
          className="px-3 py-1.5 text-xs font-semibold text-red-700 border border-red-300 rounded-lg bg-white hover:bg-red-50 transition-colors"
        >
          Tentar novamente
        </button>
      </div>
    );
  }

  if ((itens ?? []).length === 0) {
    return (
      <p className="text-xs text-gray-400 py-2 italic">
        Nenhum evento registrado.
      </p>
    );
  }

  return (
    <div className="pt-1">
      {(itens ?? []).map((item) => (
        <TimelineEvent key={item.id} item={item} />
      ))}
      <p className="text-[10px] text-gray-400 mt-1 text-right">
        Ultimos {(itens ?? []).length} eventos
      </p>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Bloco Histórico completo — timeline de atendimentos com paginacao
// ---------------------------------------------------------------------------

const TIPO_CONTATO_COLORS: Record<string, string> = {
  LIGACAO:   '#2563EB',
  WHATSAPP:  '#00A651',
  VISITA:    '#7C3AED',
  EMAIL:     '#F59E0B',
};

const TIPO_LABELS: Record<string, string> = {
  LIGACAO:  'Lig',
  WHATSAPP: 'Wpp',
  VISITA:   'Vis',
  EMAIL:    'Eml',
};

function inferTipo(item: AtendimentoHistoricoItem): string {
  if (item.via_whatsapp) return 'WHATSAPP';
  if (item.via_ligacao) return 'LIGACAO';
  return 'LIGACAO';
}

function TimelineItem({ item }: { item: AtendimentoHistoricoItem }) {
  const [expanded, setExpanded] = useState(false);
  const tipo = inferTipo(item);
  const tipoColor = TIPO_CONTATO_COLORS[tipo] ?? '#9CA3AF';
  const tipoLabel = TIPO_LABELS[tipo] ?? 'Lig';
  const maxLen = 80;
  const needsExpand = item.descricao.length > maxLen;

  return (
    <div className="flex gap-3 py-2 border-b border-gray-50 last:border-0">
      {/* Data + dot */}
      <div className="flex flex-col items-center flex-shrink-0 w-10">
        <span className="text-[10px] text-gray-400 leading-none text-right w-full">
          {formatDate(item.data_registro)}
        </span>
        <div
          className="w-2 h-2 rounded-full mt-1 ring-2 ring-white flex-shrink-0"
          style={{ background: tipoColor }}
          aria-hidden="true"
        />
      </div>

      {/* Conteudo */}
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-1.5 flex-wrap">
          <span
            className="text-[10px] font-bold px-1 py-0.5 rounded"
            style={{ background: tipoColor + '20', color: tipoColor }}
          >
            {tipoLabel}
          </span>
          {item.consultor && (
            <span className="text-[11px] font-semibold text-gray-700">{item.consultor}</span>
          )}
          <StatusBadge value={item.resultado} small />
        </div>

        <button
          type="button"
          className="mt-0.5 text-left"
          onClick={() => needsExpand && setExpanded(!expanded)}
        >
          <p className={`text-[11px] text-gray-600 italic ${needsExpand && !expanded ? 'line-clamp-2' : ''}`}>
            &quot;{item.descricao}&quot;
          </p>
        </button>

        {item.acao_futura && (
          <p className="text-[11px] text-gray-500 mt-0.5">
            <span className="text-gray-400">Acao futura:</span> {item.acao_futura}
          </p>
        )}
      </div>
    </div>
  );
}

function HistoricoBloco({ cnpj }: { cnpj: string }) {
  const [itens, setItens] = useState<AtendimentoHistoricoItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [loadingMore, setLoadingMore] = useState(false);
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [retryCount, setRetryCount] = useState(0);
  const PAGE_SIZE = 20;

  useEffect(() => {
    setLoading(true);
    setItens([]);
    setPage(1);
    setError(null);

    fetchAtendimentosHistorico(cnpj, 1, PAGE_SIZE)
      .then((res) => {
        setItens(res.itens ?? []);
        setTotal(res.total ?? 0);
      })
      .catch((e: Error) => setError(e.message))
      .finally(() => setLoading(false));
  }, [cnpj, retryCount]);

  const loadMore = useCallback(() => {
    const nextPage = page + 1;
    setLoadingMore(true);
    fetchAtendimentosHistorico(cnpj, nextPage, PAGE_SIZE)
      .then((res) => {
        setItens((prev) => [...prev, ...(res.itens ?? [])]);
        setPage(nextPage);
        setTotal(res.total ?? 0);
      })
      .catch((e: Error) => setError(e.message))
      .finally(() => setLoadingMore(false));
  }, [cnpj, page]);

  const hasMore = (itens ?? []).length < total;

  if (loading) {
    return (
      <div className="space-y-2 py-2">
        {Array.from({ length: 4 }).map((_, i) => (
          <div key={i} className="flex gap-3">
            <div className="w-10 h-8 bg-gray-100 animate-pulse rounded" />
            <div className="flex-1 space-y-1">
              <div className="h-3 bg-gray-100 animate-pulse rounded w-3/4" />
              <div className="h-3 bg-gray-100 animate-pulse rounded w-full" />
            </div>
          </div>
        ))}
      </div>
    );
  }

  if (error) {
    return (
      <div className="py-2 space-y-2">
        <p className="text-xs text-red-600">Erro ao carregar historico: {error}</p>
        <button
          type="button"
          onClick={() => setRetryCount((c) => c + 1)}
          className="px-3 py-1.5 text-xs font-semibold text-red-700 border border-red-300 rounded-lg bg-white hover:bg-red-50 transition-colors"
        >
          Tentar novamente
        </button>
      </div>
    );
  }

  if ((itens ?? []).length === 0) {
    return (
      <p className="text-xs text-gray-400 py-2 italic">
        Nenhum atendimento registrado.
      </p>
    );
  }

  return (
    <div>
      <div className="space-y-0">
        {(itens ?? []).map((item) => (
          <TimelineItem key={item.id} item={item} />
        ))}
      </div>

      {hasMore && (
        <button
          type="button"
          onClick={loadMore}
          disabled={loadingMore}
          className="mt-3 w-full py-2 text-xs font-medium text-green-700 border border-green-200 rounded-lg hover:bg-green-50 transition-colors disabled:opacity-50"
        >
          {loadingMore
            ? 'Carregando...'
            : `Mostrar mais ${Math.min(PAGE_SIZE, total - itens.length)} atendimentos`}
        </button>
      )}

      <p className="text-[10px] text-gray-400 mt-2 text-right">
        {itens.length} de {total} atendimentos
      </p>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Bloco IA — Briefing + Gerador de mensagem WhatsApp
// ---------------------------------------------------------------------------

function WhatsAppStatusDot({ status }: { status: WhatsAppStatus | null; loading: boolean }) {
  if (status === null) return null;
  if (!status.configurado) {
    return (
      <span
        className="inline-flex items-center gap-1 text-[10px] text-gray-400"
        title="WhatsApp nao configurado"
      >
        <span className="w-2 h-2 rounded-full bg-gray-300 flex-shrink-0" />
        WA nao configurado
      </span>
    );
  }
  const conectado = status.alguma_conectada;
  return (
    <span
      className="inline-flex items-center gap-1 text-[10px] font-medium"
      style={{ color: conectado ? '#00A651' : '#9CA3AF' }}
      title={conectado ? 'WhatsApp conectado' : 'WhatsApp desconectado'}
    >
      <span
        className="w-2 h-2 rounded-full flex-shrink-0"
        style={{ backgroundColor: conectado ? '#00A651' : '#9CA3AF' }}
      />
      WA {conectado ? 'conectado' : 'desconectado'}
    </span>
  );
}

function BlocoIA({ cnpj }: { cnpj: string }) {
  const [briefing, setBriefing] = useState<BriefingResponse | null>(null);
  const [loadingBriefing, setLoadingBriefing] = useState(false);
  const [erroBriefing, setErroBriefing] = useState<string | null>(null);

  const [objetivo, setObjetivo] = useState('');
  const [mensagem, setMensagem] = useState<MensagemWhatsAppResponse | null>(null);
  const [loadingMensagem, setLoadingMensagem] = useState(false);
  const [erroMensagem, setErroMensagem] = useState<string | null>(null);
  const [copiado, setCopiado] = useState(false);

  const [waStatus, setWaStatus] = useState<WhatsAppStatus | null>(null);
  const [loadingWaStatus, setLoadingWaStatus] = useState(false);
  const [enviando, setEnviando] = useState(false);
  const [resultadoEnvio, setResultadoEnvio] = useState<WhatsAppEnviarResponse | null>(null);
  const [erroEnvio, setErroEnvio] = useState<string | null>(null);

  useEffect(() => {
    setLoadingWaStatus(true);
    fetchWhatsAppStatus()
      .then(setWaStatus)
      .catch(() => setWaStatus(null))
      .finally(() => setLoadingWaStatus(false));
  }, []);

  const handleGerarBriefing = async () => {
    setLoadingBriefing(true);
    setErroBriefing(null);
    try {
      const data = await getBriefing(cnpj);
      setBriefing(data);
    } catch (e: unknown) {
      setErroBriefing(e instanceof Error ? e.message : 'Erro ao gerar briefing');
    } finally {
      setLoadingBriefing(false);
    }
  };

  const handleGerarMensagem = async () => {
    if (!objetivo.trim()) return;
    setLoadingMensagem(true);
    setErroMensagem(null);
    setCopiado(false);
    setResultadoEnvio(null);
    setErroEnvio(null);
    try {
      const data = await gerarMensagemWhatsApp(cnpj, objetivo.trim());
      setMensagem(data);
    } catch (e: unknown) {
      setErroMensagem(e instanceof Error ? e.message : 'Erro ao gerar mensagem');
    } finally {
      setLoadingMensagem(false);
    }
  };

  const handleCopiar = async () => {
    if (!mensagem?.mensagem) return;
    try {
      await navigator.clipboard.writeText(mensagem.mensagem);
      setCopiado(true);
      setTimeout(() => setCopiado(false), 2000);
    } catch {
      // fallback silencioso
    }
  };

  const handleEnviarViaWhatsApp = async () => {
    if (!mensagem?.mensagem) return;
    setEnviando(true);
    setErroEnvio(null);
    setResultadoEnvio(null);
    try {
      const resultado = await enviarWhatsApp(cnpj, mensagem.mensagem);
      setResultadoEnvio(resultado);
      if (!resultado.enviado && resultado.erro) {
        setErroEnvio(resultado.erro);
      }
    } catch (e: unknown) {
      setErroEnvio(e instanceof Error ? e.message : 'Erro ao enviar via WhatsApp');
    } finally {
      setEnviando(false);
    }
  };

  return (
    <div className="space-y-4">
      {/* Secao Briefing */}
      <div className="space-y-2">
        <div className="flex items-center justify-between gap-3">
          <p className="text-xs font-semibold text-gray-700">Briefing pre-chamada</p>
          <button
            type="button"
            onClick={handleGerarBriefing}
            disabled={loadingBriefing}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold text-white rounded-md transition-all hover:opacity-90 focus:outline-none focus:ring-2 focus:ring-green-500 focus:ring-offset-1 disabled:opacity-50"
            style={{ backgroundColor: '#00B050' }}
          >
            {loadingBriefing ? (
              <>
                <span className="w-3 h-3 border-2 border-white/40 border-t-white rounded-full animate-spin" />
                Gerando...
              </>
            ) : (
              'Gerar Briefing'
            )}
          </button>
        </div>

        {erroBriefing && (
          <p className="text-xs text-red-600 bg-red-50 border border-red-200 rounded-md px-3 py-2">
            {erroBriefing}
          </p>
        )}

        {briefing && (
          <div className="rounded-lg border border-green-100 bg-green-50 p-3 space-y-1.5">
            {!briefing.ia_configurada && (
              <p className="text-[10px] text-amber-600 bg-amber-50 border border-amber-200 rounded px-2 py-1 italic">
                IA nao configurada — briefing baseado em regras locais
              </p>
            )}
            <p className="text-xs text-gray-800 whitespace-pre-wrap leading-relaxed">
              {briefing.briefing}
            </p>
            {briefing.cached && (
              <p className="text-[10px] text-gray-400 italic">Resultado em cache</p>
            )}
          </div>
        )}
      </div>

      {/* Divisor */}
      <div className="border-t border-gray-100" />

      {/* Secao Mensagem WhatsApp */}
      <div className="space-y-2">
        <div className="flex items-center justify-between gap-2">
          <p className="text-xs font-semibold text-gray-700">Gerar mensagem WhatsApp</p>
          {!loadingWaStatus && (
            <WhatsAppStatusDot status={waStatus} loading={loadingWaStatus} />
          )}
        </div>

        <div className="flex gap-2">
          <input
            type="text"
            placeholder="Objetivo (ex: reativacao, pos-venda, cobranca)"
            value={objetivo}
            onChange={(e) => setObjetivo(e.target.value)}
            onKeyDown={(e) => { if (e.key === 'Enter') handleGerarMensagem(); }}
            aria-label="Objetivo da mensagem WhatsApp"
            className="flex-1 h-8 px-3 text-xs border border-gray-300 rounded-md bg-white text-gray-900 placeholder:text-gray-400 focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-green-500"
          />
          <button
            type="button"
            onClick={handleGerarMensagem}
            disabled={loadingMensagem || !objetivo.trim()}
            className="flex-shrink-0 inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold text-white rounded-md transition-all hover:opacity-90 focus:outline-none focus:ring-2 focus:ring-green-500 focus:ring-offset-1 disabled:opacity-50"
            style={{ backgroundColor: '#00A651' }}
          >
            {loadingMensagem ? (
              <>
                <span className="w-3 h-3 border-2 border-white/40 border-t-white rounded-full animate-spin" />
                Gerando...
              </>
            ) : (
              'Gerar Mensagem WA'
            )}
          </button>
        </div>

        {erroMensagem && (
          <p className="text-xs text-red-600 bg-red-50 border border-red-200 rounded-md px-3 py-2">
            {erroMensagem}
          </p>
        )}

        {mensagem && (
          <div className="space-y-1.5">
            {!mensagem.ia_configurada && (
              <p className="text-[10px] text-amber-600 bg-amber-50 border border-amber-200 rounded px-2 py-1 italic">
                IA nao configurada — mensagem baseada em regras locais
              </p>
            )}
            <div className="relative">
              <textarea
                readOnly
                value={mensagem.mensagem}
                rows={5}
                aria-label="Mensagem WhatsApp gerada"
                className="w-full p-3 text-xs border border-gray-200 rounded-lg bg-white text-gray-800 resize-none focus:outline-none focus:ring-2 focus:ring-green-500 leading-relaxed"
              />
              <button
                type="button"
                onClick={handleCopiar}
                aria-label="Copiar mensagem para area de transferencia"
                className="absolute top-2 right-2 inline-flex items-center gap-1 px-2 py-1 text-[10px] font-semibold rounded transition-all focus:outline-none focus:ring-2 focus:ring-green-500"
                style={copiado
                  ? { backgroundColor: '#00B050', color: '#fff' }
                  : { backgroundColor: '#F3F4F6', color: '#374151' }
                }
              >
                {copiado ? (
                  <>
                    <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M5 13l4 4L19 7" />
                    </svg>
                    Copiado!
                  </>
                ) : (
                  <>
                    <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                        d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                    </svg>
                    Copiar
                  </>
                )}
              </button>
            </div>

            <div className="flex items-center justify-between gap-2 pt-1">
              <button
                type="button"
                onClick={handleEnviarViaWhatsApp}
                disabled={enviando || !mensagem?.mensagem || resultadoEnvio?.enviado === true}
                className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold text-white rounded-md transition-all hover:opacity-90 focus:outline-none focus:ring-2 focus:ring-green-500 focus:ring-offset-1 disabled:opacity-50"
                style={{ backgroundColor: '#00A651' }}
                title={
                  !waStatus?.configurado
                    ? 'WhatsApp nao configurado'
                    : !waStatus?.alguma_conectada
                    ? 'Sem conexao WhatsApp ativa'
                    : 'Enviar mensagem via WhatsApp'
                }
              >
                {enviando ? (
                  <>
                    <span className="w-3 h-3 border-2 border-white/40 border-t-white rounded-full animate-spin" />
                    Enviando...
                  </>
                ) : resultadoEnvio?.enviado ? (
                  <>
                    <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M5 13l4 4L19 7" />
                    </svg>
                    Enviado!
                  </>
                ) : (
                  <>
                    <svg className="w-3.5 h-3.5" fill="currentColor" viewBox="0 0 24 24">
                      <path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347z" />
                      <path d="M12 0C5.373 0 0 5.373 0 12c0 2.139.558 4.144 1.535 5.879L.057 23.55a.5.5 0 00.608.608l5.693-1.479A11.952 11.952 0 0012 24c6.627 0 12-5.373 12-12S18.627 0 12 0zm0 22c-1.96 0-3.799-.56-5.354-1.527l-.383-.231-3.979 1.034 1.054-3.867-.252-.4A9.956 9.956 0 012 12C2 6.477 6.477 2 12 2s10 4.477 10 10-4.477 10-10 10z" />
                    </svg>
                    Enviar via WhatsApp
                  </>
                )}
              </button>

              {resultadoEnvio?.enviado && resultadoEnvio.numero && (
                <span className="text-[10px] text-gray-400">
                  Enviado para {resultadoEnvio.numero}
                </span>
              )}
            </div>

            {erroEnvio && (
              <p className="text-xs text-red-600 bg-red-50 border border-red-200 rounded-md px-3 py-2">
                {erroEnvio}
              </p>
            )}
            {resultadoEnvio?.enviado && (
              <p className="text-xs text-green-700 bg-green-50 border border-green-200 rounded-md px-3 py-2">
                Mensagem enviada via WhatsApp
                {resultadoEnvio.mensagem_id ? ` (ID: ${resultadoEnvio.mensagem_id})` : ''}.
              </p>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// BriefingLigacao — painel expandivel de preparacao de ligacao
// ---------------------------------------------------------------------------

const CHURN_NIVEL_COLORS: Record<string, string> = {
  BAIXO:   '#00B050',
  MEDIO:   '#FFC000',
  ALTO:    '#FF6600',
  CRITICO: '#FF0000',
};

function BriefingLigacaoPainel({ cnpj }: { cnpj: string }) {
  const [briefing, setBriefing] = useState<BriefingIAResponse | null>(null);
  const [churn, setChurn] = useState<ChurnRiskResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [copiado, setCopiado] = useState(false);

  useEffect(() => {
    setLoading(true);
    setError(null);
    Promise.all([
      fetchBriefingIA(cnpj),
      fetchChurnRisk(cnpj),
    ])
      .then(([b, c]) => {
        setBriefing(b);
        setChurn(c);
      })
      .catch((e: Error) => setError(e.message))
      .finally(() => setLoading(false));
  }, [cnpj]);

  const handleCopiarScript = async () => {
    if (!briefing?.script_venda) return;
    try {
      await navigator.clipboard.writeText(briefing.script_venda);
      setCopiado(true);
      setTimeout(() => setCopiado(false), 2000);
    } catch {
      // fallback silencioso
    }
  };

  if (loading) {
    return (
      <div className="mt-3 p-4 border border-blue-100 rounded-lg bg-blue-50 space-y-2">
        {Array.from({ length: 4 }).map((_, i) => (
          <div
            key={i}
            className="h-3 bg-blue-100 animate-pulse rounded"
            style={{ width: `${50 + (i * 15) % 40}%` }}
          />
        ))}
      </div>
    );
  }

  if (error) {
    return (
      <div className="mt-3 p-3 border border-red-200 rounded-lg bg-red-50 text-xs text-red-700">
        Erro ao preparar briefing: {error}
      </div>
    );
  }

  if (!briefing) return null;

  const churnColor = churn ? (CHURN_NIVEL_COLORS[churn.nivel] ?? '#9CA3AF') : '#9CA3AF';

  return (
    <div className="mt-3 border border-blue-200 rounded-lg bg-blue-50 overflow-hidden">
      <div className="px-4 py-2.5 bg-blue-100 border-b border-blue-200 flex items-center justify-between">
        <span className="text-xs font-semibold text-blue-800 uppercase tracking-wide">
          Briefing de Ligacao
        </span>
        {churn && (
          <span
            className="text-[10px] font-bold px-2 py-0.5 rounded-full text-white"
            style={{ backgroundColor: churnColor }}
          >
            Churn {churn.nivel} — {(churn.risco_pct ?? 0).toFixed(0)}%
          </span>
        )}
      </div>

      <div className="px-4 py-3 space-y-3">
        <div>
          <p className="text-[10px] font-semibold text-gray-500 uppercase tracking-wider mb-1">
            Abordagem sugerida
          </p>
          <p className="text-xs text-gray-800 leading-relaxed">{briefing.sugestao_abordagem}</p>
        </div>

        {briefing.ultimo_contato && (
          <div>
            <p className="text-[10px] font-semibold text-gray-500 uppercase tracking-wider mb-1">
              Ultimo contato
            </p>
            <p className="text-xs text-gray-700">
              {formatDate(briefing.ultimo_contato.data)} via {briefing.ultimo_contato.canal} —{' '}
              <span className="font-medium">{briefing.ultimo_contato.resultado}</span>
            </p>
          </div>
        )}

        <div>
          <div className="flex items-center justify-between mb-1">
            <p className="text-[10px] font-semibold text-gray-500 uppercase tracking-wider">
              Script de venda
            </p>
            <button
              type="button"
              onClick={handleCopiarScript}
              className="inline-flex items-center gap-1 px-2 py-0.5 text-[10px] font-semibold rounded transition-all focus:outline-none focus:ring-2 focus:ring-blue-500"
              style={copiado
                ? { backgroundColor: '#00B050', color: '#fff' }
                : { backgroundColor: '#DBEAFE', color: '#1D4ED8' }
              }
            >
              {copiado ? (
                <>
                  <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M5 13l4 4L19 7" />
                  </svg>
                  Copiado!
                </>
              ) : (
                <>
                  <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                      d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                  </svg>
                  Copiar Script
                </>
              )}
            </button>
          </div>
          <div className="p-2.5 bg-white border border-blue-100 rounded text-xs text-gray-800 leading-relaxed whitespace-pre-wrap">
            {briefing.script_venda}
          </div>
        </div>

        {churn && (churn.fatores?.length ?? 0) > 0 && (
          <div>
            <p className="text-[10px] font-semibold text-gray-500 uppercase tracking-wider mb-1">
              Fatores de risco
            </p>
            <ul className="space-y-0.5">
              {(churn.fatores ?? []).map((f, idx) => (
                <li key={idx} className="flex items-start gap-1.5 text-xs text-gray-700">
                  <span className="w-1.5 h-1.5 rounded-full flex-shrink-0 mt-1" style={{ backgroundColor: churnColor }} />
                  {f}
                </li>
              ))}
            </ul>
            {churn.recomendacao && (
              <p className="text-xs text-blue-800 font-medium mt-1.5 italic">
                Recomendacao: {churn.recomendacao}
              </p>
            )}
          </div>
        )}
      </div>
    </div>
  );
}


// ---------------------------------------------------------------------------
// Conversas WhatsApp — historico real de mensagens via Deskrio
// ---------------------------------------------------------------------------

function formatTimestampHHMM(ts: string): string {
  if (!ts) return '';
  try {
    const d = new Date(ts);
    if (isNaN(d.getTime())) return ts;
    return d.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' });
  } catch {
    return ts;
  }
}

function BolhaChat({ msg }: { msg: WhatsAppMensagem }) {
  const nosso = !msg.de_cliente;
  return (
    <div className={`flex w-full ${nosso ? 'justify-end' : 'justify-start'}`}>
      <div
        className={`max-w-[80%] px-3 py-2 rounded-lg space-y-0.5 ${
          nosso
            ? 'rounded-br-sm'
            : 'rounded-bl-sm bg-gray-100'
        }`}
        style={nosso ? { backgroundColor: '#00B050' } : undefined}
      >
        {msg.tipo === 'image' && msg.media_url ? (
          <a
            href={msg.media_url}
            target="_blank"
            rel="noopener noreferrer"
            className={`text-xs underline ${nosso ? 'text-white/80' : 'text-blue-600'}`}
          >
            [imagem]
          </a>
        ) : msg.tipo === 'audio' ? (
          <span className={`text-xs italic ${nosso ? 'text-white/80' : 'text-gray-500'}`}>
            [audio]
          </span>
        ) : (
          <p className={`text-xs leading-relaxed break-words ${nosso ? 'text-white' : 'text-gray-800'}`}>
            {msg.texto || '—'}
          </p>
        )}
        <p className={`text-[10px] text-right ${nosso ? 'text-white/60' : 'text-gray-400'}`}>
          {formatTimestampHHMM(msg.timestamp)}
        </p>
      </div>
    </div>
  );
}

function ChatSkeleton() {
  const sides = [false, true, false, false, true, true, false, true];
  return (
    <div className="space-y-2 py-1">
      {sides.map((right, i) => (
        <div key={i} className={`flex ${right ? 'justify-end' : 'justify-start'}`}>
          <div
            className="h-7 bg-gray-100 animate-pulse rounded-lg"
            style={{ width: `${40 + ((i * 13) % 35)}%` }}
          />
        </div>
      ))}
    </div>
  );
}

function ConversasWhatsAppBloco({ cnpj }: { cnpj: string }) {
  const [conversa, setConversa] = useState<WhatsAppConversaResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const chatRef = useRef<HTMLDivElement>(null);

  const carregar = () => {
    setLoading(true);
    setError(null);
    fetchWhatsAppConversa(cnpj)
      .then(setConversa)
      .catch((e: Error) => setError(e.message))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    carregar();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [cnpj]);

  // Scroll para o final das mensagens quando carregadas
  useEffect(() => {
    if (!loading && conversa?.mensagens?.length && chatRef.current) {
      chatRef.current.scrollTop = chatRef.current.scrollHeight;
    }
  }, [loading, conversa]);

  if (loading) return <ChatSkeleton />;

  if (error) {
    return (
      <div className="space-y-2 py-1">
        <p className="text-xs text-red-600">Erro ao carregar conversas: {error}</p>
        <button
          type="button"
          onClick={carregar}
          className="text-xs text-green-700 border border-green-200 px-3 py-1.5 rounded-lg hover:bg-green-50 transition-colors"
        >
          Tentar novamente
        </button>
      </div>
    );
  }

  if (!conversa || !conversa.encontrado) {
    return (
      <p className="text-xs text-gray-400 py-2 italic">
        Cliente nao encontrado no WhatsApp.
      </p>
    );
  }

  const mensagens = conversa.mensagens ?? [];

  if (mensagens.length === 0) {
    return (
      <p className="text-xs text-gray-400 py-2 italic">
        Nenhuma conversa encontrada.
      </p>
    );
  }

  const ultimas = mensagens.slice(-20);

  return (
    <div className="space-y-2">
      {/* Cabecalho com info do contato */}
      {conversa.contato && (
        <div className="flex items-center gap-2 pb-1.5 border-b border-gray-100">
          <div
            className="w-6 h-6 rounded-full flex-shrink-0 flex items-center justify-center text-[10px] font-bold text-white"
            style={{ backgroundColor: '#00B050' }}
            aria-hidden="true"
          >
            {conversa.contato.nome.charAt(0).toUpperCase()}
          </div>
          <div className="min-w-0">
            <p className="text-[11px] font-semibold text-gray-800 truncate">{conversa.contato.nome}</p>
            {conversa.contato.telefone && (
              <p className="text-[10px] text-gray-400 font-mono">{conversa.contato.telefone}</p>
            )}
          </div>
          {conversa.ticket_recente && (
            <span className="ml-auto text-[10px] text-gray-400 flex-shrink-0">
              Ticket #{conversa.ticket_recente.id} — {conversa.ticket_recente.status}
            </span>
          )}
        </div>
      )}

      {/* Baloes de chat */}
      <div
        ref={chatRef}
        className="max-h-[400px] overflow-y-auto space-y-1.5 py-1 pr-0.5"
        aria-label="Historico de mensagens WhatsApp"
      >
        {ultimas.map((msg) => (
          <BolhaChat key={msg.id} msg={msg} />
        ))}
      </div>

      <p className="text-[10px] text-gray-400 text-right">
        Ultimas {ultimas.length} mensagens
      </p>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Componente principal
// ---------------------------------------------------------------------------

type BlocoKey = 'identidade' | 'status' | 'financeiro' | 'timeline' | 'compras' | 'historico' | 'conversas' | 'ia';

const BLOCO_DEFAULTS: Record<BlocoKey, boolean> = {
  identidade: true,
  status:     true,
  financeiro: false,
  timeline:   true,
  compras:    false,
  historico:  false,
  conversas:  false,
  ia:         false,
};

export default function ClienteDetalhe({ cnpj, onClose }: ClienteDetalheProps) {
  const { user } = useAuth();
  const isExternoJulio = user?.role === 'consultor_externo';

  const [cliente, setCliente] = useState<ClienteRegistro | null>(null);
  const [scoreBreakdown, setScoreBreakdown] = useState<ScoreBreakdown | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [atendimentoAberto, setAtendimentoAberto] = useState(false);
  const [historicoKey, setHistoricoKey] = useState(0);
  const [briefingLigacaoAberto, setBriefingLigacaoAberto] = useState(false);
  const [retryCount, setRetryCount] = useState(0);

  // Estado dos blocos colapsáveis — persistido em sessionStorage
  const [open, setOpen] = useState<Record<BlocoKey, boolean>>(() => {
    if (typeof window === 'undefined') return BLOCO_DEFAULTS;
    try {
      const saved = sessionStorage.getItem('crm_detalhe_blocos_v2');
      if (saved) {
        const parsed = JSON.parse(saved) as Partial<Record<BlocoKey, boolean>>;
        return {
          identidade: parsed.identidade ?? BLOCO_DEFAULTS.identidade,
          status:     parsed.status     ?? BLOCO_DEFAULTS.status,
          financeiro: parsed.financeiro ?? BLOCO_DEFAULTS.financeiro,
          timeline:   parsed.timeline   ?? BLOCO_DEFAULTS.timeline,
          compras:    parsed.compras    ?? BLOCO_DEFAULTS.compras,
          historico:  parsed.historico  ?? BLOCO_DEFAULTS.historico,
          conversas:  parsed.conversas  ?? BLOCO_DEFAULTS.conversas,
          ia:         parsed.ia         ?? BLOCO_DEFAULTS.ia,
        };
      }
    } catch {
      // fallback silencioso
    }
    return BLOCO_DEFAULTS;
  });

  const drawerRef = useRef<HTMLElement>(null);

  // Foco no drawer ao abrir (acessibilidade)
  useEffect(() => {
    if (cnpj) {
      setTimeout(() => drawerRef.current?.focus(), 50);
    }
  }, [cnpj]);

  // Fechar com ESC
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    document.addEventListener('keydown', handler);
    return () => document.removeEventListener('keydown', handler);
  }, [onClose]);

  // Buscar dados do cliente + score breakdown em paralelo
  useEffect(() => {
    if (!cnpj) {
      setCliente(null);
      setScoreBreakdown(null);
      return;
    }
    setLoading(true);
    setError(null);
    setScoreBreakdown(null);

    Promise.all([
      fetchCliente(cnpj),
      fetchClienteScore(cnpj).catch((): ClienteScoreResponse | null => null),
    ])
      .then(([clienteData, scoreData]) => {
        setCliente(clienteData);
        if (scoreData?.fatores) {
          setScoreBreakdown({
            urgencia:  scoreData.fatores.urgencia.valor,
            valor:     scoreData.fatores.valor.valor,
            follow_up: scoreData.fatores.followup.valor,
            sinal:     scoreData.fatores.sinal.valor,
            tentativa: scoreData.fatores.tentativa.valor,
            situacao:  scoreData.fatores.situacao.valor,
          });
        } else if (clienteData.score_breakdown) {
          setScoreBreakdown(clienteData.score_breakdown);
        }
      })
      .catch((e: Error) => setError(e.message))
      .finally(() => setLoading(false));
  }, [cnpj, retryCount]);

  function toggleBloco(key: BlocoKey) {
    setOpen((prev) => {
      const next = { ...prev, [key]: !prev[key] };
      try {
        sessionStorage.setItem('crm_detalhe_blocos_v2', JSON.stringify(next));
      } catch {
        // fallback silencioso
      }
      return next;
    });
  }

  if (!cnpj) return null;

  return (
    <>
      {/* Overlay */}
      <div
        className="fixed inset-0 bg-black/40 z-40 backdrop-blur-[1px]"
        onClick={onClose}
        aria-hidden="true"
      />

      {/* Drawer lateral */}
      <aside
        ref={drawerRef}
        tabIndex={-1}
        role="dialog"
        aria-modal="true"
        aria-labelledby="detalhe-titulo"
        className="fixed top-0 right-0 h-full w-full md:max-w-2xl bg-white z-50 shadow-2xl flex flex-col outline-none"
      >
        {/* Cabeçalho fixo */}
        <div className="flex items-start justify-between px-4 md:px-5 py-3 md:py-4 border-b border-gray-200 bg-white flex-shrink-0">
          <div className="min-w-0 flex-1 pr-2">
            <h2
              id="detalhe-titulo"
              className="font-bold text-gray-900 text-base leading-tight truncate"
            >
              {loading ? 'Carregando...' : (cliente?.nome_fantasia ?? cnpj)}
            </h2>
            <p className="text-xs text-gray-400 font-mono mt-0.5">{formatCnpj(cnpj)}</p>
            {cliente && !loading && (
              <div className="flex flex-wrap gap-1.5 mt-1.5">
                <StatusBadge value={cliente.situacao} variant="situacao" small />
                {cliente.consultor && (
                  <span className="text-[11px] text-gray-500">{cliente.consultor}</span>
                )}
                {cliente.uf && (
                  <span className="text-[11px] text-gray-500">{cliente.uf}</span>
                )}
              </div>
            )}
          </div>
          <div className="flex items-center gap-1.5 flex-shrink-0">
            {/* Botao Preparar Ligacao */}
            {cliente && !loading && (
              <button
                type="button"
                onClick={() => setBriefingLigacaoAberto((v) => !v)}
                aria-label="Preparar briefing de ligacao com IA"
                aria-pressed={briefingLigacaoAberto}
                className="inline-flex items-center gap-1.5 min-h-[44px] sm:min-h-0 px-3 py-1.5 text-xs font-semibold rounded-md transition-all hover:opacity-90 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-1"
                style={briefingLigacaoAberto
                  ? { backgroundColor: '#1D4ED8', color: '#fff' }
                  : { backgroundColor: '#DBEAFE', color: '#1D4ED8' }
                }
              >
                <svg
                  aria-hidden="true"
                  className="w-3.5 h-3.5 flex-shrink-0"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                  strokeWidth={2}
                >
                  <path strokeLinecap="round" strokeLinejoin="round"
                    d="M3 5a2 2 0 012-2h3.28a1 1 0 01.948.684l1.498 4.493a1 1 0 01-.502 1.21l-2.257 1.13a11.042 11.042 0 005.516 5.516l1.13-2.257a1 1 0 011.21-.502l4.493 1.498a1 1 0 01.684.949V19a2 2 0 01-2 2h-1C9.716 21 3 14.284 3 6V5z" />
                </svg>
                <span className="hidden sm:inline">{briefingLigacaoAberto ? 'Fechar' : 'Ligar'}</span>
              </button>
            )}
            {/* Botao registrar atendimento */}
            {cliente && !loading && (
              <button
                type="button"
                onClick={() => setAtendimentoAberto(true)}
                aria-label={`Registrar atendimento de ${cliente.nome_fantasia}`}
                className="inline-flex items-center gap-1.5 min-h-[44px] sm:min-h-0 px-2.5 py-1.5 text-xs font-semibold text-white rounded-md transition-all hover:opacity-90 focus:outline-none focus:ring-2 focus:ring-green-500 focus:ring-offset-1"
                style={{ backgroundColor: '#00B050' }}
              >
                <svg
                  aria-hidden="true"
                  className="w-3.5 h-3.5 flex-shrink-0"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                  strokeWidth={2.5}
                >
                  <path strokeLinecap="round" strokeLinejoin="round" d="M12 4v16m8-8H4" />
                </svg>
                <span className="hidden sm:inline">Registrar</span>
              </button>
            )}
            <button
              type="button"
              onClick={onClose}
              className="p-2 rounded hover:bg-gray-100 text-gray-500 transition-colors"
              aria-label="Fechar ficha do cliente"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>

        {/* Painel de briefing de ligacao — expande sob o header */}
        {briefingLigacaoAberto && cnpj && (
          <div className="px-4 pb-3 border-b border-gray-200 bg-white flex-shrink-0">
            <BriefingLigacaoPainel cnpj={cnpj} />
          </div>
        )}

        {/* Corpo scrollável */}
        <div className="flex-1 overflow-y-auto py-3 px-3 md:px-4 space-y-3 pb-20 md:pb-4"
          style={{ WebkitOverflowScrolling: 'touch' }}
        >

          {/* Estado de loading */}
          {loading && (
            <div className="space-y-3 pt-2">
              {Array.from({ length: 10 }).map((_, i) => (
                <div
                  key={i}
                  className="h-4 bg-gray-100 animate-pulse rounded"
                  style={{ width: `${45 + (i * 17) % 45}%` }}
                />
              ))}
            </div>
          )}

          {/* Estado de erro */}
          {error && (
            <div className="p-4 bg-red-50 border border-red-200 rounded-lg text-xs text-red-700 space-y-2">
              <p>Erro ao carregar cliente: {error}</p>
              <button
                type="button"
                onClick={() => setRetryCount((c) => c + 1)}
                className="px-3 py-1.5 text-xs font-semibold text-red-700 border border-red-300 rounded-lg bg-white hover:bg-red-50 transition-colors"
              >
                Tentar novamente
              </button>
            </div>
          )}

          {/* Conteudo */}
          {cliente && !loading && (
            <>
              {/* BLOCO 1: IDENTIDADE */}
              <Bloco
                title="Identidade"
                open={open.identidade}
                onToggle={() => toggleBloco('identidade')}
              >
                <FieldRow
                  label="CNPJ"
                  value={formatCnpj(cliente.cnpj)}
                  mono
                />
                <FieldRow label="Nome Fantasia" value={cliente.nome_fantasia} />
                <FieldRow label="Razao Social" value={cliente.razao_social} />
                <FieldRow
                  label="UF / Cidade"
                  value={
                    cliente.cidade && cliente.uf
                      ? `${cliente.cidade} — ${cliente.uf}`
                      : (cliente.uf ?? undefined)
                  }
                />
                <FieldRow label="Email" value={cliente.email as string | undefined} />
                <FieldRow label="Telefone" value={cliente.telefone as string | undefined} />
                <FieldRow
                  label="Data Cadastro"
                  value={cliente.data_cadastro ? formatDate(cliente.data_cadastro) : undefined}
                />
                <FieldRow label="Rede / Grupo" value={cliente.rede_grupo as string | undefined} />
                <FieldRow label="Consultor" value={cliente.consultor} />
                <FieldRow label="Segmento" value={cliente.segmento} />
              </Bloco>

              {/* BLOCO 2: STATUS */}
              <Bloco
                title="Status e Motor"
                open={open.status}
                onToggle={() => toggleBloco('status')}
              >
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-x-4 gap-y-1.5 pb-2">
                  <FieldRow
                    label="Situacao"
                    badge={<StatusBadge value={cliente.situacao} variant="situacao" large />}
                  />
                  <FieldRow
                    label="Temperatura"
                    badge={
                      cliente.temperatura ? (
                        <StatusBadge value={cliente.temperatura} variant="temperatura" large />
                      ) : undefined
                    }
                  />
                  <FieldRow
                    label="Prioridade"
                    badge={
                      cliente.prioridade ? (
                        <div className="flex flex-col items-end gap-0.5">
                          <StatusBadge value={cliente.prioridade} variant="prioridade" large />
                          {cliente.fase && (
                            <span className="text-[10px] text-gray-500">{cliente.fase}</span>
                          )}
                        </div>
                      ) : undefined
                    }
                  />
                  <FieldRow
                    label="ABC"
                    badge={
                      cliente.curva_abc ? (
                        <StatusBadge value={cliente.curva_abc} variant="abc" large />
                      ) : undefined
                    }
                  />
                </div>

                {cliente.score != null && (
                  <div className="pt-1">
                    <ScoreBreakdownDisplay
                      score={cliente.score}
                      breakdown={scoreBreakdown ?? cliente.score_breakdown}
                    />
                  </div>
                )}

                <div className="pt-1.5 space-y-1.5 border-t border-gray-100 mt-1.5">
                  <FieldRow label="Estagio Funil" value={cliente.estagio_funil as string | undefined} />
                  <FieldRow label="Tipo Cliente" value={cliente.tipo_cliente as string | undefined} />
                  <FieldRow label="Fase" value={cliente.fase} />
                  <FieldRow label="Dias sem compra" value={cliente.dias_sem_compra} />
                  <FieldRow label="Ciclo medio (dias)" value={cliente.ciclo_medio} />
                  <FieldRow
                    label="Ultima compra"
                    value={cliente.ultima_compra ? formatDate(cliente.ultima_compra) : undefined}
                  />
                </div>
              </Bloco>

              {/* BLOCO 3: FINANCEIRO — oculto para consultor_externo */}
              {!isExternoJulio && (
                <Bloco
                  title="Financeiro"
                  open={open.financeiro}
                  onToggle={() => toggleBloco('financeiro')}
                >
                  <FieldRow label="Faturamento 2025" value={cliente.faturamento_total} money />
                  <FieldRow label="Faturamento 2026 (YTD)" value={cliente.faturamento_2026} money />
                  <FieldRow label="Meta Anual" value={cliente.meta_anual} money />

                  {cliente.meta_anual != null && cliente.faturamento_2026 != null && (() => {
                    const gap = cliente.faturamento_2026 - cliente.meta_anual;
                    const pct = cliente.meta_anual > 0
                      ? (cliente.faturamento_2026 / cliente.meta_anual) * 100
                      : 0;
                    const gapColor = gap >= 0 ? '#00B050' : '#DC2626';
                    const barColor = pct >= 100 ? '#00B050' : pct >= 80 ? '#FFC000' : pct >= 50 ? '#FF6600' : '#FF0000';

                    return (
                      <>
                        <div className="flex justify-between items-center py-1 border-b border-gray-50 text-xs">
                          <span className="text-gray-500">Gap (meta - realizado)</span>
                          <span className="font-medium tabular-nums" style={{ color: gapColor }}>
                            {gap >= 0 ? '+' : ''}{formatBRL(gap)}
                          </span>
                        </div>
                        <div className="flex justify-between items-center py-1 border-b border-gray-50 text-xs">
                          <span className="text-gray-500">% Alcancado</span>
                          <div className="flex items-center gap-2">
                            <div className="w-24 h-1.5 bg-gray-100 rounded-full overflow-hidden">
                              <div
                                className="h-full rounded-full"
                                style={{
                                  width: `${Math.min(100, pct)}%`,
                                  background: barColor,
                                  transition: 'width 400ms ease-out',
                                }}
                              />
                            </div>
                            <span className="font-medium tabular-nums" style={{ color: barColor }}>
                              {pct.toFixed(1)}%
                            </span>
                          </div>
                        </div>
                      </>
                    );
                  })()}

                  <FieldRow label="Ticket Medio" value={cliente.ticket_medio} money />
                  <FieldRow label="Meta Mensal" value={cliente.meta_mensal} money />
                  <FieldRow label="Dias sem compra" value={cliente.dias_sem_compra} />
                  <FieldRow label="Ciclo medio (dias)" value={cliente.ciclo_medio} />

                  {/* Mini bar chart vendas mensais */}
                  {cliente.vendas_mensais && cliente.vendas_mensais.length > 0 && (
                    <VendasMiniChart vendas={cliente.vendas_mensais} />
                  )}

                  {/* Score sparkline usando vendas mensais como proxy */}
                  {cliente.vendas_mensais && cliente.vendas_mensais.length >= 2 && cliente.score != null && (
                    <ScoreSparkline vendas={cliente.vendas_mensais} score={cliente.score} />
                  )}
                </Bloco>
              )}

              {/* BLOCO 4: TIMELINE VISUAL — ultimos 10 eventos */}
              <Bloco
                title="Timeline de Eventos"
                open={open.timeline}
                onToggle={() => toggleBloco('timeline')}
                badge={
                  <span className="text-[10px] font-medium text-gray-400">(ultimos 10)</span>
                }
              >
                <TimelineVisual cnpj={cnpj} />
              </Bloco>

              {/* BLOCO 5: ULTIMAS COMPRAS */}
              {!isExternoJulio && (
                <Bloco
                  title="Ultimas Compras"
                  open={open.compras}
                  onToggle={() => toggleBloco('compras')}
                  badge={
                    <span className="text-[10px] font-medium text-gray-400">(max 5)</span>
                  }
                >
                  <UltimasComprasBloco cnpj={cnpj} />
                </Bloco>
              )}

              {/* BLOCO 6: HISTÓRICO COMPLETO */}
              <Bloco
                title="Historico de Atendimentos"
                open={open.historico}
                onToggle={() => toggleBloco('historico')}
              >
                <HistoricoBloco key={historicoKey} cnpj={cnpj} />
              </Bloco>

              {/* BLOCO 6.5: CONVERSAS WHATSAPP */}
              <Bloco
                title="Conversas WhatsApp"
                open={open.conversas}
                onToggle={() => toggleBloco('conversas')}
                badge={
                  <span
                    className="inline-flex items-center gap-1 text-[10px] font-medium px-1.5 py-0.5 rounded"
                    style={{ backgroundColor: '#00B05018', color: '#00B050' }}
                  >
                    Deskrio
                  </span>
                }
              >
                <ConversasWhatsAppBloco cnpj={cnpj} />
              </Bloco>

              {/* BLOCO 7: INTELIGÊNCIA ARTIFICIAL */}
              <Bloco
                title="Inteligencia Artificial"
                open={open.ia}
                onToggle={() => toggleBloco('ia')}
              >
                <BlocoIA cnpj={cnpj} />
              </Bloco>
            </>
          )}
        </div>
      </aside>

      {/* Modal de atendimento — abre sobre o drawer */}
      {atendimentoAberto && cliente && (
        <AtendimentoForm
          cliente={{
            cnpj: cliente.cnpj,
            nome_fantasia: cliente.nome_fantasia,
            situacao: cliente.situacao,
            sinaleiro: cliente.sinaleiro,
            score: cliente.score,
            prioridade: cliente.prioridade,
            consultor: cliente.consultor,
            uf: cliente.uf,
          }}
          onClose={() => setAtendimentoAberto(false)}
          onSaved={() => {
            setHistoricoKey((k) => k + 1);
            setOpen((prev) => {
              const next = { ...prev, historico: true, timeline: true };
              try {
                sessionStorage.setItem('crm_detalhe_blocos_v2', JSON.stringify(next));
              } catch {
                // fallback silencioso
              }
              return next;
            });
          }}
          labelFechar="Fechar e voltar ao cliente"
        />
      )}
    </>
  );
}
