'use client';

import { useCallback, useEffect, useRef, useState } from 'react';
import {
  AtendimentoHistoricoItem,
  BriefingResponse,
  ClienteRegistro,
  ClienteScoreResponse,
  MensagemWhatsAppResponse,
  ScoreBreakdown,
  VendaMensal,
  fetchAtendimentosHistorico,
  fetchCliente,
  fetchClienteScore,
  formatBRL,
  getBriefing,
  gerarMensagemWhatsApp,
} from '@/lib/api';
import { useAuth } from '@/contexts/AuthContext';
import StatusBadge from './StatusBadge';
import AtendimentoForm from './AtendimentoForm';

// ---------------------------------------------------------------------------
// ClienteDetalhe — drawer lateral com ficha completa do cliente
// 4 blocos colapsáveis: Identidade, Status, Financeiro, Histórico
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
  // Aceita ISO "2026-03-25" ou "2026-03-25T..."
  const [datePart] = value.split('T');
  const parts = datePart.split('-');
  if (parts.length !== 3) return value;
  return `${parts[2]}/${parts[1]}/${parts[0]}`;
}

// ---------------------------------------------------------------------------
// Bloco colapsável
// ---------------------------------------------------------------------------

interface BlocoProps {
  title: string;
  open: boolean;
  onToggle: () => void;
  children: React.ReactNode;
}

function Bloco({ title, open, onToggle, children }: BlocoProps) {
  return (
    <div className="border border-gray-200 rounded-lg overflow-hidden">
      <button
        type="button"
        onClick={onToggle}
        className="w-full flex items-center justify-between px-4 py-3 bg-gray-50 hover:bg-gray-100 transition-colors text-left"
        aria-expanded={open}
      >
        <span className="text-[11px] font-semibold text-gray-600 uppercase tracking-wider">
          {title}
        </span>
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
  const pct = Math.min(100, Math.max(0, valor));
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
        {valor.toFixed(0)}
      </span>
      <span className="text-[11px] text-gray-400 w-10 text-right tabular-nums">
        {pontos.toFixed(1)}pt
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
      <p className="text-[11px] text-gray-500 mb-1.5 font-medium">Vendas mês a mês</p>
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
// Bloco Histórico — timeline de atendimentos
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
  return 'LIGACAO'; // default
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
  const PAGE_SIZE = 20;

  useEffect(() => {
    setLoading(true);
    setItens([]);
    setPage(1);
    setError(null);

    fetchAtendimentosHistorico(cnpj, 1, PAGE_SIZE)
      .then((res) => {
        setItens(res.itens);
        setTotal(res.total);
      })
      .catch((e: Error) => setError(e.message))
      .finally(() => setLoading(false));
  }, [cnpj]);

  const loadMore = useCallback(() => {
    const nextPage = page + 1;
    setLoadingMore(true);
    fetchAtendimentosHistorico(cnpj, nextPage, PAGE_SIZE)
      .then((res) => {
        setItens((prev) => [...prev, ...res.itens]);
        setPage(nextPage);
        setTotal(res.total);
      })
      .catch((e: Error) => setError(e.message))
      .finally(() => setLoadingMore(false));
  }, [cnpj, page]);

  const hasMore = itens.length < total;

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
      <p className="text-xs text-red-600 py-2">
        Erro ao carregar historico: {error}
      </p>
    );
  }

  if (itens.length === 0) {
    return (
      <p className="text-xs text-gray-400 py-2 italic">
        Nenhum atendimento registrado.
      </p>
    );
  }

  return (
    <div>
      <div className="space-y-0">
        {itens.map((item) => (
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

function BlocoIA({ cnpj }: { cnpj: string }) {
  // Estado do briefing
  const [briefing, setBriefing] = useState<BriefingResponse | null>(null);
  const [loadingBriefing, setLoadingBriefing] = useState(false);
  const [erroBriefing, setErroBriefing] = useState<string | null>(null);

  // Estado do gerador de mensagem WA
  const [objetivo, setObjetivo] = useState('');
  const [mensagem, setMensagem] = useState<MensagemWhatsAppResponse | null>(null);
  const [loadingMensagem, setLoadingMensagem] = useState(false);
  const [erroMensagem, setErroMensagem] = useState<string | null>(null);
  const [copiado, setCopiado] = useState(false);

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
      // fallback: selecionar texto manualmente
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
        <p className="text-xs font-semibold text-gray-700">Gerar mensagem WhatsApp</p>

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
          </div>
        )}
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Componente principal
// ---------------------------------------------------------------------------

type BlocoKey = 'identidade' | 'status' | 'financeiro' | 'historico' | 'ia';

export default function ClienteDetalhe({ cnpj, onClose }: ClienteDetalheProps) {
  const { user } = useAuth();
  const isExternoJulio = user?.role === 'consultor_externo';

  const [cliente, setCliente] = useState<ClienteRegistro | null>(null);
  const [scoreBreakdown, setScoreBreakdown] = useState<ScoreBreakdown | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Estado do modal de atendimento
  const [atendimentoAberto, setAtendimentoAberto] = useState(false);
  // Chave para forcar re-render do HistoricoBloco apos salvar atendimento
  const [historicoKey, setHistoricoKey] = useState(0);

  // Estado dos blocos colapsáveis — persistido em sessionStorage
  const [open, setOpen] = useState<Record<BlocoKey, boolean>>(() => {
    if (typeof window === 'undefined') {
      return { identidade: true, status: true, financeiro: false, historico: false, ia: false };
    }
    try {
      const saved = sessionStorage.getItem('crm_detalhe_blocos');
      if (saved) {
        const parsed = JSON.parse(saved) as Record<BlocoKey, boolean>;
        // Garantir que 'ia' existe mesmo em estado salvo antes desta versao
        const merged: Record<BlocoKey, boolean> = {
          identidade: parsed.identidade ?? true,
          status: parsed.status ?? true,
          financeiro: parsed.financeiro ?? false,
          historico: parsed.historico ?? false,
          ia: parsed.ia ?? false,
        };
        return merged;
      }
    } catch {
      // fallback silencioso
    }
    return { identidade: true, status: true, financeiro: false, historico: false, ia: false };
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
        // Mapear estrutura do endpoint /score para ScoreBreakdown
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
  }, [cnpj]);

  function toggleBloco(key: BlocoKey) {
    setOpen((prev) => {
      const next = { ...prev, [key]: !prev[key] };
      try {
        sessionStorage.setItem('crm_detalhe_blocos', JSON.stringify(next));
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
        className="fixed top-0 right-0 h-full w-full max-w-lg bg-white z-50 shadow-2xl flex flex-col outline-none"
      >
        {/* Cabeçalho fixo */}
        <div className="flex items-start justify-between px-5 py-4 border-b border-gray-200 bg-white flex-shrink-0">
          <div className="min-w-0 flex-1 pr-3">
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
          <div className="flex items-center gap-2 flex-shrink-0">
            {/* Botao de registrar atendimento — disponivel assim que o cliente carrega */}
            {cliente && !loading && (
              <button
                type="button"
                onClick={() => setAtendimentoAberto(true)}
                aria-label={`Registrar atendimento de ${cliente.nome_fantasia}`}
                className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold text-white rounded-md transition-all hover:opacity-90 focus:outline-none focus:ring-2 focus:ring-green-500 focus:ring-offset-1"
                style={{ backgroundColor: '#00B050' }}
              >
                <svg
                  aria-hidden="true"
                  className="w-3.5 h-3.5"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                  strokeWidth={2.5}
                >
                  <path strokeLinecap="round" strokeLinejoin="round" d="M12 4v16m8-8H4" />
                </svg>
                Registrar
              </button>
            )}
            <button
              type="button"
              onClick={onClose}
              className="p-2 rounded hover:bg-gray-100 text-gray-500"
              aria-label="Fechar ficha do cliente"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>

        {/* Corpo scrollável */}
        <div className="flex-1 overflow-y-auto py-3 px-4 space-y-3">

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
            <div className="p-4 bg-red-50 border border-red-200 rounded-lg text-xs text-red-700">
              Erro ao carregar cliente: {error}
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
                {/* Badges de status em grade */}
                <div className="grid grid-cols-2 gap-x-4 gap-y-1.5 pb-2">
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

                {/* Score breakdown */}
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

                  {/* Gap e % alcancado */}
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
                </Bloco>
              )}

              {/* BLOCO 4: HISTÓRICO */}
              <Bloco
                title="Historico de Atendimentos"
                open={open.historico}
                onToggle={() => toggleBloco('historico')}
              >
                {/* historicoKey forca remontagem apos novo atendimento ser registrado */}
                <HistoricoBloco key={historicoKey} cnpj={cnpj} />
              </Bloco>

              {/* BLOCO 5: INTELIGÊNCIA ARTIFICIAL */}
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
            // Incrementar key forca HistoricoBloco a recarregar do backend
            setHistoricoKey((k) => k + 1);
            // Abrir bloco de historico se estiver fechado
            setOpen((prev) => {
              const next = { ...prev, historico: true };
              try {
                sessionStorage.setItem('crm_detalhe_blocos', JSON.stringify(next));
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
