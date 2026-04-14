'use client';

import { useCallback, useEffect, useRef, useState } from 'react';
import { fetchClientes, fetchCliente, atualizarEstagioCliente, ClienteRegistro, formatBRL, formatDateBR } from '@/lib/api';
import { useAuth } from '@/contexts/AuthContext';

// ---------------------------------------------------------------------------
// Pipeline Kanban — CRM VITAO360
// Horizontal scrollable board with 14 funnel stages, HTML5 drag-and-drop,
// swimlane grouping (PRE-VENDA / VENDA / POS-VENDA) and mobile fallback.
// ---------------------------------------------------------------------------

// ---------------------------------------------------------------------------
// Stage definitions — 14 estagios do Motor de Regras
// ---------------------------------------------------------------------------

type StageGroup = 'pre-venda' | 'venda' | 'pos-venda';

interface StageConfig {
  id: string;
  label: string;
  group: StageGroup;
  borderColor: string;
  bgColor: string;
  textColor: string;
  headerBg: string;
}

const STAGE_CONFIGS: StageConfig[] = [
  // Pre-venda
  { id: 'INÍCIO CONTATO',  label: 'Inicio Contato',  group: 'pre-venda', borderColor: '#64748b', bgColor: '#f8fafc', textColor: '#475569', headerBg: '#f1f5f9' },
  { id: 'TENTATIVA',       label: 'Tentativa',        group: 'pre-venda', borderColor: '#94a3b8', bgColor: '#f8fafc', textColor: '#475569', headerBg: '#f1f5f9' },
  { id: 'PROSPECÇÃO',      label: 'Prospeccao',       group: 'pre-venda', borderColor: '#64748b', bgColor: '#f8fafc', textColor: '#475569', headerBg: '#f1f5f9' },
  // Venda
  { id: 'EM ATENDIMENTO',  label: 'Em Atendimento',   group: 'venda',     borderColor: '#2563eb', bgColor: '#eff6ff', textColor: '#1d4ed8', headerBg: '#dbeafe' },
  { id: 'CADASTRO',        label: 'Cadastro',          group: 'venda',     borderColor: '#3b82f6', bgColor: '#eff6ff', textColor: '#1d4ed8', headerBg: '#dbeafe' },
  { id: 'ORÇAMENTO',       label: 'Orcamento',         group: 'venda',     borderColor: '#2563eb', bgColor: '#eff6ff', textColor: '#1d4ed8', headerBg: '#dbeafe' },
  { id: 'PEDIDO',          label: 'Pedido',            group: 'venda',     borderColor: '#1d4ed8', bgColor: '#eff6ff', textColor: '#1d4ed8', headerBg: '#dbeafe' },
  // Pos-venda
  { id: 'ACOMP POS-VENDA', label: 'Acomp Pos-Venda',  group: 'pos-venda', borderColor: '#00B050', bgColor: '#f0fdf4', textColor: '#166534', headerBg: '#dcfce7' },
  { id: 'POS-VENDA',       label: 'Pos-Venda',         group: 'pos-venda', borderColor: '#16a34a', bgColor: '#f0fdf4', textColor: '#166534', headerBg: '#dcfce7' },
  { id: 'CS',              label: 'CS',                group: 'pos-venda', borderColor: '#00B050', bgColor: '#f0fdf4', textColor: '#166534', headerBg: '#dcfce7' },
  { id: 'FOLLOW-UP',       label: 'Follow-Up',         group: 'pos-venda', borderColor: '#d97706', bgColor: '#fffbeb', textColor: '#92400e', headerBg: '#fef3c7' },
  { id: 'SUPORTE',         label: 'Suporte',            group: 'pos-venda', borderColor: '#dc2626', bgColor: '#fff1f2', textColor: '#9f1239', headerBg: '#ffe4e6' },
  { id: 'RELACIONAMENTO',  label: 'Relacionamento',     group: 'pos-venda', borderColor: '#e11d48', bgColor: '#fff1f2', textColor: '#9f1239', headerBg: '#ffe4e6' },
  { id: 'NUTRIÇÃO',        label: 'Nutricao',           group: 'pos-venda', borderColor: '#f43f5e', bgColor: '#fff1f2', textColor: '#9f1239', headerBg: '#ffe4e6' },
];

// Swimlane configuration
interface SwimlaneConfig {
  id: StageGroup;
  label: string;
  bg: string;
  border: string;
  text: string;
}

const SWIMLANES: SwimlaneConfig[] = [
  { id: 'pre-venda', label: 'PRE-VENDA',  bg: '#DBEAFE', border: '#93c5fd', text: '#1d4ed8' },
  { id: 'venda',     label: 'VENDA',      bg: '#DCFCE7', border: '#86efac', text: '#166534' },
  { id: 'pos-venda', label: 'POS-VENDA',  bg: '#FEF3C7', border: '#fcd34d', text: '#92400e' },
];

// Normalise variant spellings from the backend to canonical stage IDs
const STAGE_ALIASES: Record<string, string> = {
  'INICIO CONTATO':     'INÍCIO CONTATO',
  'INÍCIO CONTATO':     'INÍCIO CONTATO',
  'ACOMP PÓS-VENDA':   'ACOMP POS-VENDA',
  'ACOMP POS-VENDA':   'ACOMP POS-VENDA',
  'PÓS-VENDA':         'POS-VENDA',
  'POS-VENDA':         'POS-VENDA',
  'PROSPEÇÃO':         'PROSPECÇÃO',
  'PROSPECÇÃO':        'PROSPECÇÃO',
  'PROSPECCAO':        'PROSPECÇÃO',
  'ORÇAMENTO':         'ORÇAMENTO',
  'ORCAMENTO':         'ORÇAMENTO',
  'FOLLOW-UP':         'FOLLOW-UP',
  'FOLLOWUP':          'FOLLOW-UP',
  'NUTRIÇÃO':          'NUTRIÇÃO',
  'NUTRICAO':          'NUTRIÇÃO',
};

function normalizeStage(raw: string | undefined | null): string {
  if (!raw) return '';
  const upper = raw.trim().toUpperCase();
  return STAGE_ALIASES[upper] ?? upper;
}

const STAGE_IDS = STAGE_CONFIGS.map((s) => s.id);
const CONSULTORES = ['LARISSA', 'MANU', 'JULIO', 'DAIANE'];

// ---------------------------------------------------------------------------
// Score badge helpers
// ---------------------------------------------------------------------------

function scoreBadgeColor(score: number | undefined): { bg: string; text: string } {
  if (score == null) return { bg: '#e5e7eb', text: '#6b7280' };
  if (score >= 70)   return { bg: '#dcfce7', text: '#166534' };
  if (score >= 40)   return { bg: '#fef9c3', text: '#854d0e' };
  return              { bg: '#fee2e2', text: '#991b1b' };
}

// ---------------------------------------------------------------------------
// Temperature dot helper
// ---------------------------------------------------------------------------

function tempDotColor(temp: string | undefined): string {
  if (!temp) return '#d1d5db';
  switch (temp.toUpperCase()) {
    case 'QUENTE':  return '#ef4444';
    case 'MORNO':   return '#f97316';
    case 'FRIO':    return '#3b82f6';
    case 'CRITICO': return '#7c3aed';
    case 'PERDIDO': return '#6b7280';
    default:        return '#d1d5db';
  }
}

// ---------------------------------------------------------------------------
// Format helpers
// ---------------------------------------------------------------------------

function formatCnpj(cnpj: string): string {
  const d = cnpj.replace(/\D/g, '').padStart(14, '0');
  if (d.length !== 14) return cnpj;
  return `${d.slice(0, 2)}.${d.slice(2, 5)}.${d.slice(5, 8)}/${d.slice(8, 12)}-${d.slice(12)}`;
}

// formatDate: alias para formatDateBR centralizado em api.ts
const formatDate = formatDateBR;

function truncate(s: string, max: number): string {
  return s.length <= max ? s : s.slice(0, max - 1) + '…';
}

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface KanbanColumns {
  [stage: string]: ClienteRegistro[];
}

// ---------------------------------------------------------------------------
// ClienteDetailPanel — slide-over with full client info
// ---------------------------------------------------------------------------

interface ClienteDetailPanelProps {
  cnpj: string | null;
  onClose: () => void;
}

function ClienteDetailPanel({ cnpj, onClose }: ClienteDetailPanelProps) {
  const [cliente, setCliente] = useState<ClienteRegistro | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const { user } = useAuth();
  const isExterno = user?.role === 'consultor_externo';

  useEffect(() => {
    if (!cnpj) {
      setCliente(null);
      return;
    }
    setLoading(true);
    setError(null);
    fetchCliente(cnpj)
      .then(setCliente)
      .catch((e: Error) => setError(e.message))
      .finally(() => setLoading(false));
  }, [cnpj]);

  // Close on Escape
  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      if (e.key === 'Escape') onClose();
    }
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [onClose]);

  if (!cnpj) return null;

  const cfg = cliente ? STAGE_CONFIGS.find((s) => s.id === normalizeStage(cliente.estagio_funil)) : null;
  const sc = scoreBadgeColor(cliente?.score);

  return (
    <>
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black/20 z-40"
        onClick={onClose}
        aria-hidden="true"
      />

      {/* Panel */}
      <aside
        className="fixed top-0 right-0 h-full w-full sm:w-[420px] bg-white border-l border-gray-200 z-50 flex flex-col shadow-2xl"
        role="dialog"
        aria-label="Detalhe do cliente"
      >
        {/* Header */}
        <div className="flex-shrink-0 flex items-center justify-between px-5 py-4 border-b border-gray-100">
          <div className="min-w-0">
            {loading ? (
              <div className="h-5 bg-gray-100 animate-pulse rounded w-40" />
            ) : cliente ? (
              <>
                <h2 className="text-sm font-bold text-gray-900 truncate">
                  {cliente.nome_fantasia}
                </h2>
                <p className="text-xs text-gray-400 mt-0.5">{formatCnpj(cliente.cnpj)}</p>
              </>
            ) : (
              <h2 className="text-sm font-bold text-gray-900">Carregando...</h2>
            )}
          </div>
          <button
            type="button"
            onClick={onClose}
            className="flex-shrink-0 ml-3 p-1.5 rounded text-gray-400 hover:text-gray-700 hover:bg-gray-100 transition-colors"
            aria-label="Fechar painel"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto scrollbar-thin px-5 py-4 space-y-5">
          {loading && (
            <div className="space-y-3">
              {[...Array(6)].map((_, i) => (
                <div key={i} className="h-4 bg-gray-100 animate-pulse rounded" style={{ width: `${70 + (i % 3) * 15}%` }} />
              ))}
            </div>
          )}

          {error && (
            <div className="flex items-start gap-2 p-3 bg-red-50 border border-red-200 rounded-lg">
              <svg className="w-4 h-4 text-red-500 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
              </svg>
              <p className="text-xs text-red-700">{error}</p>
            </div>
          )}

          {!loading && cliente && (
            <>
              {/* Stage badge */}
              {cfg && (
                <div
                  className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-semibold border"
                  style={{ backgroundColor: cfg.bgColor, color: cfg.textColor, borderColor: cfg.borderColor }}
                >
                  {cfg.label}
                </div>
              )}

              {/* Score + temperatura row */}
              <div className="flex items-center gap-3">
                <div className="flex items-center gap-1.5">
                  <span
                    className="inline-flex items-center justify-center w-8 h-8 rounded-full text-xs font-bold"
                    style={{ backgroundColor: sc.bg, color: sc.text }}
                    title={`Score: ${cliente.score?.toFixed(1) ?? '—'}`}
                  >
                    {cliente.score != null ? Math.round(cliente.score) : '—'}
                  </span>
                  <span className="text-xs text-gray-500">Score</span>
                </div>
                {cliente.temperatura && (
                  <div className="flex items-center gap-1.5">
                    <span
                      className="w-3 h-3 rounded-full flex-shrink-0"
                      style={{ backgroundColor: tempDotColor(cliente.temperatura) }}
                    />
                    <span className="text-xs text-gray-500">{cliente.temperatura}</span>
                  </div>
                )}
                {cliente.prioridade && (
                  <span className="text-xs font-mono bg-gray-100 text-gray-600 px-1.5 py-0.5 rounded">
                    {cliente.prioridade}
                  </span>
                )}
              </div>

              {/* Identidade */}
              <section>
                <h3 className="text-[10px] font-semibold text-gray-400 uppercase tracking-wider mb-2">
                  Identidade
                </h3>
                <dl className="space-y-1.5">
                  <DetailRow label="Razao Social" value={cliente.razao_social} />
                  <DetailRow label="Consultor"    value={cliente.consultor} />
                  <DetailRow label="Situacao"     value={cliente.situacao} />
                  <DetailRow label="Cidade"       value={cliente.cidade && cliente.uf ? `${cliente.cidade} / ${cliente.uf}` : (cliente.cidade ?? cliente.uf)} />
                  <DetailRow label="Segmento"     value={cliente.segmento} />
                  <DetailRow label="Rede / Grupo" value={cliente.rede_grupo} />
                  <DetailRow label="Telefone"     value={cliente.telefone} />
                  <DetailRow label="Email"        value={cliente.email} />
                  <DetailRow label="Cadastro"     value={formatDate(cliente.data_cadastro)} />
                </dl>
              </section>

              {/* Status comercial */}
              <section>
                <h3 className="text-[10px] font-semibold text-gray-400 uppercase tracking-wider mb-2">
                  Status Comercial
                </h3>
                <dl className="space-y-1.5">
                  <DetailRow label="Sinaleiro"        value={cliente.sinaleiro} />
                  <DetailRow label="Curva ABC"         value={cliente.curva_abc} />
                  <DetailRow label="Fase"              value={cliente.fase} />
                  <DetailRow label="Ultima Compra"     value={formatDate(cliente.ultima_compra)} />
                  <DetailRow label="Dias sem Compra"   value={cliente.dias_sem_compra != null ? `${cliente.dias_sem_compra} dias` : undefined} />
                  <DetailRow label="Ciclo Medio"       value={cliente.ciclo_medio != null ? `${cliente.ciclo_medio} dias` : undefined} />
                </dl>
              </section>

              {/* Financeiro — oculto para consultor externo */}
              {!isExterno && (
                <section>
                  <h3 className="text-[10px] font-semibold text-gray-400 uppercase tracking-wider mb-2">
                    Financeiro
                  </h3>
                  <dl className="space-y-1.5">
                    <DetailRow label="Ult. Pedido"       value={cliente.valor_ultimo_pedido != null ? formatBRL(cliente.valor_ultimo_pedido) : undefined} />
                    <DetailRow label="Fat. Acumulado"    value={cliente.faturamento_total != null ? formatBRL(cliente.faturamento_total) : undefined} />
                    <DetailRow label="Meta Anual"        value={cliente.meta_anual != null ? formatBRL(cliente.meta_anual) : undefined} />
                    <DetailRow label="Meta Mensal"       value={cliente.meta_anual != null ? formatBRL(cliente.meta_anual / 12) : undefined} />
                  </dl>
                </section>
              )}
            </>
          )}
        </div>
      </aside>
    </>
  );
}

function DetailRow({ label, value }: { label: string; value?: string | null }) {
  if (!value) return null;
  return (
    <div className="flex items-baseline gap-2 text-xs">
      <dt className="text-gray-400 flex-shrink-0 w-32">{label}</dt>
      <dd className="text-gray-800 font-medium min-w-0 break-words">{value}</dd>
    </div>
  );
}

// ---------------------------------------------------------------------------
// MobileMoveModal — selecao de estagio no mobile (sem drag-and-drop)
// ---------------------------------------------------------------------------

interface MobileMoveModalProps {
  cliente: ClienteRegistro;
  currentStage: string;
  onMove: (cnpj: string, toStage: string) => void;
  onClose: () => void;
}

function MobileMoveModal({ cliente, currentStage, onMove, onClose }: MobileMoveModalProps) {
  return (
    <>
      <div
        className="fixed inset-0 bg-black/40 z-50"
        onClick={onClose}
        aria-hidden="true"
      />
      <div
        className="fixed bottom-0 left-0 right-0 bg-white rounded-t-2xl z-50 shadow-2xl max-h-[80vh] overflow-y-auto"
        role="dialog"
        aria-label="Mover cliente de estagio"
      >
        <div className="px-4 py-3 border-b border-gray-100 flex items-center justify-between">
          <div>
            <p className="text-sm font-semibold text-gray-900 truncate">{cliente.nome_fantasia}</p>
            <p className="text-xs text-gray-500 mt-0.5">Selecionar novo estagio</p>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="p-1.5 rounded text-gray-400 hover:text-gray-700 hover:bg-gray-100 transition-colors"
            aria-label="Fechar"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <div className="p-3 space-y-1">
          {SWIMLANES.map((swimlane) => {
            const stages = STAGE_CONFIGS.filter((s) => s.group === swimlane.id);
            return (
              <div key={swimlane.id} className="mb-3">
                <p
                  className="text-[10px] font-bold uppercase tracking-wider px-2 py-1 rounded mb-1"
                  style={{ backgroundColor: swimlane.bg, color: swimlane.text }}
                >
                  {swimlane.label}
                </p>
                {stages.map((cfg) => (
                  <button
                    key={cfg.id}
                    type="button"
                    disabled={cfg.id === currentStage}
                    onClick={() => {
                      onMove(cliente.cnpj, cfg.id);
                      onClose();
                    }}
                    className={`w-full text-left px-3 py-2.5 rounded-lg text-xs font-medium transition-colors flex items-center gap-2
                      ${cfg.id === currentStage
                        ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
                        : 'hover:bg-gray-50 text-gray-700 active:bg-gray-100'
                      }`}
                  >
                    <span
                      className="w-2.5 h-2.5 rounded-sm flex-shrink-0"
                      style={{ backgroundColor: cfg.borderColor }}
                    />
                    {cfg.label}
                    {cfg.id === currentStage && (
                      <span className="ml-auto text-[10px] text-gray-400">atual</span>
                    )}
                  </button>
                ))}
              </div>
            );
          })}
        </div>
      </div>
    </>
  );
}

// ---------------------------------------------------------------------------
// KanbanCard — individual client card
// ---------------------------------------------------------------------------

interface KanbanCardProps {
  cliente: ClienteRegistro;
  currentStage: string;
  onDragStart: (e: React.DragEvent, cnpj: string, fromStage: string) => void;
  onClick: (cnpj: string) => void;
  onMobileMove: (cliente: ClienteRegistro, currentStage: string) => void;
  isDragging: boolean;
  isMobile: boolean;
}

function KanbanCard({ cliente, currentStage, onDragStart, onClick, onMobileMove, isDragging, isMobile }: KanbanCardProps) {
  const sc = scoreBadgeColor(cliente.score);
  const { user } = useAuth();
  const isExterno = user?.role === 'consultor_externo';

  return (
    <div
      draggable={!isMobile}
      onDragStart={(e) => !isMobile && onDragStart(e, cliente.cnpj, currentStage)}
      onClick={() => onClick(cliente.cnpj)}
      aria-label={`Cliente ${cliente.nome_fantasia}, score ${cliente.score?.toFixed(1) ?? 'N/A'}`}
      role="button"
      tabIndex={0}
      onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') onClick(cliente.cnpj); }}
      className={`
        bg-white rounded-lg border border-gray-200 p-2.5 cursor-pointer select-none
        transition-all duration-150
        hover:shadow-md hover:-translate-y-0.5 hover:border-gray-300
        focus:outline-none focus:ring-2 focus:ring-offset-1
        ${isDragging ? 'opacity-50 shadow-lg' : 'shadow-sm'}
      `}
      style={{ '--tw-ring-color': '#00B050' } as React.CSSProperties}
    >
      {/* Top row: temperature dot + name */}
      <div className="flex items-start gap-2 mb-1.5">
        <span
          className="mt-1 w-2 h-2 rounded-full flex-shrink-0"
          style={{ backgroundColor: tempDotColor(cliente.temperatura) }}
          title={cliente.temperatura ?? 'Temperatura desconhecida'}
        />
        <p className="text-xs font-semibold text-gray-900 leading-snug min-w-0 line-clamp-2 flex-1">
          {truncate(cliente.nome_fantasia, 40)}
        </p>
      </div>

      {/* Bottom row: score badge + value + consultor */}
      <div className="flex items-center gap-1.5 flex-wrap">
        <span
          className="inline-flex items-center justify-center w-6 h-6 rounded-full text-[10px] font-bold flex-shrink-0"
          style={{ backgroundColor: sc.bg, color: sc.text }}
          title={`Score: ${cliente.score?.toFixed(1) ?? '—'}`}
        >
          {cliente.score != null ? Math.round(cliente.score) : '—'}
        </span>

        {!isExterno && (cliente.valor_ultimo_pedido ?? 0) > 0 && (
          <span className="text-[10px] text-gray-500 font-medium" title="Valor do ultimo pedido">
            {formatBRL(cliente.valor_ultimo_pedido!)}
          </span>
        )}

        {cliente.consultor && (
          <span className="ml-auto text-[10px] text-gray-400 font-medium uppercase tracking-wide flex-shrink-0">
            {cliente.consultor.slice(0, 4)}
          </span>
        )}
      </div>

      {/* Prioridade chip — only when P0/P1 */}
      {(cliente.prioridade === 'P0' || cliente.prioridade === 'P1') && (
        <div className="mt-1.5">
          <span className={`inline-block text-[9px] font-bold px-1 py-0.5 rounded ${
            cliente.prioridade === 'P0'
              ? 'bg-red-100 text-red-700'
              : 'bg-orange-100 text-orange-700'
          }`}>
            {cliente.prioridade}
          </span>
        </div>
      )}

      {/* Mobile move button */}
      {isMobile && (
        <button
          type="button"
          onClick={(e) => {
            e.stopPropagation();
            onMobileMove(cliente, currentStage);
          }}
          className="mt-1.5 w-full flex items-center justify-center gap-1 py-1 text-[10px] font-medium text-blue-600 border border-blue-200 rounded bg-blue-50 hover:bg-blue-100 transition-colors"
          aria-label="Mover para outro estagio"
        >
          <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 8l4 4m0 0l-4 4m4-4H3" />
          </svg>
          Mover para
        </button>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// KanbanColumn
// ---------------------------------------------------------------------------

interface KanbanColumnProps {
  config: StageConfig;
  cards: ClienteRegistro[];
  onDragStart: (e: React.DragEvent, cnpj: string, fromStage: string) => void;
  onDragOver: (e: React.DragEvent, toStage: string) => void;
  onDrop: (e: React.DragEvent, toStage: string) => void;
  onDragLeave: () => void;
  isDragTarget: boolean;
  draggingCnpj: string | null;
  onCardClick: (cnpj: string) => void;
  onMobileMove: (cliente: ClienteRegistro, currentStage: string) => void;
  isMobile: boolean;
}

function KanbanColumn({
  config,
  cards,
  onDragStart,
  onDragOver,
  onDrop,
  onDragLeave,
  isDragTarget,
  draggingCnpj,
  onCardClick,
  onMobileMove,
  isMobile,
}: KanbanColumnProps) {
  const totalUltimoPedido = cards.reduce((acc, c) => acc + (c.valor_ultimo_pedido ?? 0), 0);

  return (
    <div
      className="flex-shrink-0 flex flex-col rounded-lg border-t-4 bg-white"
      style={{
        width: 220,
        borderTopColor: config.borderColor,
        borderLeft: '1px solid #e5e7eb',
        borderRight: '1px solid #e5e7eb',
        borderBottom: '1px solid #e5e7eb',
      }}
    >
      {/* Column Header */}
      <div
        className="px-3 py-2.5 border-b border-gray-100"
        style={{ backgroundColor: config.headerBg }}
      >
        <div className="flex items-center justify-between gap-1 mb-0.5">
          <h2
            className="text-xs font-bold uppercase tracking-wide truncate"
            style={{ color: config.textColor }}
          >
            {config.label}
          </h2>
          <span
            className="flex-shrink-0 inline-flex items-center justify-center min-w-[20px] h-5 rounded-full text-[10px] font-bold px-1"
            style={{ backgroundColor: config.borderColor, color: '#fff' }}
          >
            {cards.length}
          </span>
        </div>
        {totalUltimoPedido > 0 && (
          <p className="text-[10px] text-gray-400 font-medium" title="Soma do ultimo pedido de cada cliente neste estagio">
            {formatBRL(totalUltimoPedido)}
            <span className="text-gray-300 ml-1">ult.ped</span>
          </p>
        )}
      </div>

      {/* Drop zone */}
      <div
        onDragOver={(e) => onDragOver(e, config.id)}
        onDrop={(e) => onDrop(e, config.id)}
        onDragLeave={onDragLeave}
        className={`
          flex-1 p-2 space-y-2 overflow-y-auto scrollbar-thin min-h-[120px] transition-colors duration-150
          ${isDragTarget ? 'bg-blue-50 ring-2 ring-inset ring-blue-300' : ''}
        `}
        style={{ maxHeight: 'calc(100vh - 320px)' }}
      >
        {cards.length === 0 ? (
          <div className="h-full flex items-center justify-center min-h-[100px]">
            <div className="text-center border-2 border-dashed border-gray-200 rounded-lg p-4 w-full">
              <p className="text-[10px] text-gray-400">Nenhum cliente</p>
              <p className="text-[10px] text-gray-300">neste estagio</p>
            </div>
          </div>
        ) : (
          cards.map((c) => (
            <KanbanCard
              key={c.cnpj}
              cliente={c}
              currentStage={config.id}
              onDragStart={onDragStart}
              onClick={onCardClick}
              onMobileMove={onMobileMove}
              isDragging={draggingCnpj === c.cnpj}
              isMobile={isMobile}
            />
          ))
        )}
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// SummaryBar
// ---------------------------------------------------------------------------

interface SummaryBarProps {
  totalOportunidades: number;
  totalUltPedido: number;
  totalFatAcumulado: number;
  totalClientes: number;
  filtroConsultor: string;
  onFiltroConsultor: (v: string) => void;
  loading: boolean;
  pendingMoves: number;
}

function SummaryBar({
  totalOportunidades,
  totalUltPedido,
  totalFatAcumulado,
  totalClientes,
  filtroConsultor,
  onFiltroConsultor,
  loading,
  pendingMoves,
}: SummaryBarProps) {
  const conversionRate =
    totalClientes > 0 ? ((totalOportunidades / totalClientes) * 100).toFixed(1) : '0.0';

  return (
    <div className="flex-shrink-0 bg-white border border-gray-200 rounded-lg shadow-sm px-4 py-3">
      <div className="flex items-center flex-wrap gap-4">
        {/* KPIs */}
        <div className="flex items-center gap-4 flex-wrap flex-1">
          <div className="flex flex-col">
            <span className="text-[10px] font-semibold text-gray-400 uppercase tracking-wide">
              Oportunidades
            </span>
            {loading ? (
              <div className="h-6 w-10 bg-gray-100 animate-pulse rounded" />
            ) : (
              <span className="text-xl font-bold text-gray-900">
                {totalOportunidades.toLocaleString('pt-BR')}
              </span>
            )}
          </div>

          <div className="w-px h-8 bg-gray-200 flex-shrink-0" />

          <div className="flex flex-col">
            <span className="text-[10px] font-semibold text-gray-400 uppercase tracking-wide">
              Ult. Pedidos
            </span>
            {loading ? (
              <div className="h-6 w-28 bg-gray-100 animate-pulse rounded" />
            ) : (
              <span className="text-xl font-bold" style={{ color: '#00B050' }}>
                {formatBRL(totalUltPedido)}
              </span>
            )}
          </div>

          <div className="w-px h-8 bg-gray-200 flex-shrink-0" />

          <div className="flex flex-col">
            <span className="text-[10px] font-semibold text-gray-400 uppercase tracking-wide">
              Fat. Acumulado
            </span>
            {loading ? (
              <div className="h-6 w-28 bg-gray-100 animate-pulse rounded" />
            ) : (
              <span className="text-lg font-bold text-gray-600">
                {formatBRL(totalFatAcumulado)}
              </span>
            )}
          </div>

          <div className="w-px h-8 bg-gray-200 flex-shrink-0" />

          <div className="flex flex-col">
            <span className="text-[10px] font-semibold text-gray-400 uppercase tracking-wide">
              Engajamento
            </span>
            {loading ? (
              <div className="h-6 w-14 bg-gray-100 animate-pulse rounded" />
            ) : (
              <span className="text-xl font-bold text-gray-900">
                {conversionRate}%
              </span>
            )}
          </div>

          {/* Pending API saves indicator */}
          {pendingMoves > 0 && (
            <>
              <div className="w-px h-8 bg-gray-200 flex-shrink-0" />
              <div className="flex items-center gap-1.5">
                <div className="w-3.5 h-3.5 border-2 border-blue-500 border-t-transparent rounded-full animate-spin flex-shrink-0" />
                <span className="text-[10px] text-blue-600 font-medium">
                  Salvando {pendingMoves} movimentacao{pendingMoves !== 1 ? 'oes' : ''}...
                </span>
              </div>
            </>
          )}
        </div>

        {/* Consultor filter */}
        <div className="flex flex-col gap-1 flex-shrink-0">
          <label className="text-[10px] font-semibold text-gray-400 uppercase tracking-wide">
            Consultor
          </label>
          <select
            value={filtroConsultor}
            onChange={(e) => onFiltroConsultor(e.target.value)}
            aria-label="Filtrar por consultor"
            className={`border rounded px-2 py-1.5 text-xs text-gray-700 bg-white focus:outline-none focus:ring-2 focus:ring-offset-0 transition-colors ${
              filtroConsultor
                ? 'border-green-400 bg-green-50 text-green-800 font-medium'
                : 'border-gray-200'
            }`}
            style={{ '--tw-ring-color': '#00B050' } as React.CSSProperties}
          >
            <option value="">Todos</option>
            {CONSULTORES.map((c) => (
              <option key={c} value={c}>{c}</option>
            ))}
          </select>
        </div>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// SwimlaneGroup — wrapper that renders a labeled group of columns
// ---------------------------------------------------------------------------

interface SwimlaneGroupProps {
  swimlane: SwimlaneConfig;
  stages: StageConfig[];
  columns: KanbanColumns;
  onDragStart: (e: React.DragEvent, cnpj: string, fromStage: string) => void;
  onDragOver: (e: React.DragEvent, toStage: string) => void;
  onDrop: (e: React.DragEvent, toStage: string) => void;
  onDragLeave: () => void;
  dragTargetStage: string | null;
  draggingCnpj: string | null;
  onCardClick: (cnpj: string) => void;
  onMobileMove: (cliente: ClienteRegistro, currentStage: string) => void;
  isMobile: boolean;
}

function SwimlaneGroup({
  swimlane,
  stages,
  columns,
  onDragStart,
  onDragOver,
  onDrop,
  onDragLeave,
  dragTargetStage,
  draggingCnpj,
  onCardClick,
  onMobileMove,
  isMobile,
}: SwimlaneGroupProps) {
  const totalCards = stages.reduce((acc, s) => acc + (columns[s.id]?.length ?? 0), 0);

  return (
    <div className="flex-shrink-0 flex flex-col gap-2">
      {/* Swimlane header label */}
      <div
        className="flex items-center gap-2 px-3 py-1.5 rounded-lg border"
        style={{ backgroundColor: swimlane.bg, borderColor: swimlane.border }}
      >
        <span
          className="text-[10px] font-black uppercase tracking-widest"
          style={{ color: swimlane.text }}
        >
          {swimlane.label}
        </span>
        <span
          className="text-[10px] font-bold px-1.5 py-0.5 rounded-full"
          style={{ backgroundColor: swimlane.border, color: swimlane.text }}
        >
          {totalCards}
        </span>
      </div>

      {/* Columns in this swimlane */}
      <div className="flex gap-3">
        {stages.map((cfg) => (
          <KanbanColumn
            key={cfg.id}
            config={cfg}
            cards={columns[cfg.id] ?? []}
            onDragStart={onDragStart}
            onDragOver={onDragOver}
            onDrop={onDrop}
            onDragLeave={onDragLeave}
            isDragTarget={dragTargetStage === cfg.id}
            draggingCnpj={draggingCnpj}
            onCardClick={onCardClick}
            onMobileMove={onMobileMove}
            isMobile={isMobile}
          />
        ))}
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// PipelinePage — main board
// ---------------------------------------------------------------------------

export default function PipelinePage() {
  const { user } = useAuth();

  const [allClientes, setAllClientes] = useState<ClienteRegistro[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Filter
  const [filtroConsultor, setFiltroConsultor] = useState<string>('');

  // Drag state
  const [draggingCnpj, setDraggingCnpj] = useState<string | null>(null);
  const [draggingFromStage, setDraggingFromStage] = useState<string | null>(null);
  const [dragTargetStage, setDragTargetStage] = useState<string | null>(null);

  // Local overrides for stage (applied immediately, API call fires in background)
  const [stageOverrides, setStageOverrides] = useState<Record<string, string>>({});

  // Pending API saves counter (for UX indicator)
  const [pendingMoves, setPendingMoves] = useState(0);

  // Detail panel
  const [selectedCnpj, setSelectedCnpj] = useState<string | null>(null);

  // Mobile detection
  const [isMobile, setIsMobile] = useState(false);

  // Mobile move modal
  const [mobileMoving, setMobileMoving] = useState<{ cliente: ClienteRegistro; currentStage: string } | null>(null);

  // Scroll ref for horizontal board
  const boardRef = useRef<HTMLDivElement>(null);

  // Detect mobile on mount + resize
  useEffect(() => {
    function check() {
      setIsMobile(window.innerWidth < 768);
    }
    check();
    window.addEventListener('resize', check);
    return () => window.removeEventListener('resize', check);
  }, []);

  // Apply consultant filter from user role automatically
  useEffect(() => {
    if (user?.role === 'consultor' && user.consultor_nome) {
      setFiltroConsultor(user.consultor_nome);
    }
  }, [user]);

  // ---------------------------------------------------------------------------
  // Load data
  // ---------------------------------------------------------------------------

  const loadClientes = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const resp = await fetchClientes({
        limit: 500,
        sort_by: 'score',
        sort_dir: 'desc',
        ...(filtroConsultor ? { consultor: filtroConsultor } : {}),
      });
      setAllClientes(resp.registros);
      // Clear overrides on fresh reload
      setStageOverrides({});
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Erro ao carregar clientes');
    } finally {
      setLoading(false);
    }
  }, [filtroConsultor]);

  useEffect(() => {
    void loadClientes();
  }, [loadClientes]);

  // ---------------------------------------------------------------------------
  // Build kanban columns
  // ---------------------------------------------------------------------------

  const columns: KanbanColumns = {};
  STAGE_IDS.forEach((id) => { columns[id] = []; });

  allClientes.forEach((c) => {
    const stageRaw = stageOverrides[c.cnpj] ?? c.estagio_funil;
    const stage = normalizeStage(stageRaw);
    if (stage && columns[stage] !== undefined) {
      columns[stage].push(c);
    }
  });

  // Only show stages that have cards OR are "core" stages we always want visible
  const ALWAYS_SHOW_STAGES = new Set([
    'EM ATENDIMENTO', 'PEDIDO', 'POS-VENDA', 'FOLLOW-UP',
  ]);

  // ---------------------------------------------------------------------------
  // Summary stats
  // ---------------------------------------------------------------------------

  const totalOportunidades = allClientes.filter((c) => {
    const stage = normalizeStage(stageOverrides[c.cnpj] ?? c.estagio_funil);
    return stage !== '' && STAGE_IDS.includes(stage);
  }).length;

  const totalUltPedido = allClientes.reduce((acc, c) => acc + (c.valor_ultimo_pedido ?? 0), 0);
  const totalFatAcumulado = allClientes.reduce((acc, c) => acc + (c.faturamento_total ?? 0), 0);

  // ---------------------------------------------------------------------------
  // Move handler — optimistic UI + async API call
  // ---------------------------------------------------------------------------

  const handleMoveCliente = useCallback(async (cnpj: string, fromStage: string, toStage: string) => {
    if (!cnpj || !fromStage || fromStage === toStage) return;

    // Optimistic update
    setStageOverrides((prev) => ({ ...prev, [cnpj]: toStage }));
    setPendingMoves((n) => n + 1);

    try {
      await atualizarEstagioCliente(cnpj, toStage);
    } catch (e) {
      // Revert on failure
      setStageOverrides((prev) => {
        const next = { ...prev };
        delete next[cnpj];
        return next;
      });
      console.error('Falha ao atualizar estagio:', e);
    } finally {
      setPendingMoves((n) => Math.max(0, n - 1));
    }
  }, []);

  // ---------------------------------------------------------------------------
  // Drag-and-drop handlers (desktop only)
  // ---------------------------------------------------------------------------

  function handleDragStart(e: React.DragEvent, cnpj: string, fromStage: string) {
    setDraggingCnpj(cnpj);
    setDraggingFromStage(fromStage);
    e.dataTransfer.effectAllowed = 'move';
    e.dataTransfer.setData('cnpj', cnpj);
    e.dataTransfer.setData('fromStage', fromStage);
  }

  function handleDragOver(e: React.DragEvent, toStage: string) {
    e.preventDefault();
    e.dataTransfer.dropEffect = 'move';
    if (dragTargetStage !== toStage) {
      setDragTargetStage(toStage);
    }
  }

  function handleDrop(e: React.DragEvent, toStage: string) {
    e.preventDefault();
    const cnpj = e.dataTransfer.getData('cnpj');
    const fromStage = e.dataTransfer.getData('fromStage') || draggingFromStage;

    setDraggingCnpj(null);
    setDraggingFromStage(null);
    setDragTargetStage(null);

    if (!cnpj || !fromStage || fromStage === toStage) return;

    void handleMoveCliente(cnpj, fromStage, toStage);
  }

  function handleDragLeave() {
    setDragTargetStage(null);
  }

  function handleDragEnd() {
    setDraggingCnpj(null);
    setDraggingFromStage(null);
    setDragTargetStage(null);
  }

  // ---------------------------------------------------------------------------
  // Mobile move handler
  // ---------------------------------------------------------------------------

  function handleMobileOpenMove(cliente: ClienteRegistro, currentStage: string) {
    setMobileMoving({ cliente, currentStage });
  }

  function handleMobileMoveConfirm(cnpj: string, toStage: string) {
    const fromStage = mobileMoving?.currentStage ?? '';
    void handleMoveCliente(cnpj, fromStage, toStage);
    setMobileMoving(null);
  }

  // ---------------------------------------------------------------------------
  // Build swimlane data — filter visible stages per swimlane
  // ---------------------------------------------------------------------------

  const swimlaneData = SWIMLANES.map((swimlane) => {
    const stages = STAGE_CONFIGS.filter(
      (s) =>
        s.group === swimlane.id &&
        (columns[s.id].length > 0 || ALWAYS_SHOW_STAGES.has(s.id))
    );
    return { swimlane, stages };
  }).filter((entry) => entry.stages.length > 0);

  // ---------------------------------------------------------------------------
  // Mobile list view — single flat list grouped by stage
  // ---------------------------------------------------------------------------

  if (isMobile) {
    return (
      <div className="flex flex-col gap-3">
        {/* Page header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-lg font-bold text-gray-900">Pipeline</h1>
            <p className="text-xs text-gray-500 mt-0.5">
              {loading ? 'Carregando...' : `${allClientes.length.toLocaleString('pt-BR')} clientes`}
            </p>
          </div>
          <button
            type="button"
            onClick={loadClientes}
            disabled={loading}
            className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold text-green-700 border border-green-300 rounded-lg bg-white hover:bg-green-50 transition-colors disabled:opacity-50"
          >
            <svg className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
            Atualizar
          </button>
        </div>

        {/* Filter */}
        <div className="flex items-center gap-2">
          <label className="text-xs text-gray-500 font-medium flex-shrink-0">Consultor:</label>
          <select
            value={filtroConsultor}
            onChange={(e) => setFiltroConsultor(e.target.value)}
            className="flex-1 border border-gray-200 rounded px-2 py-1.5 text-xs bg-white"
          >
            <option value="">Todos</option>
            {CONSULTORES.map((c) => <option key={c} value={c}>{c}</option>)}
          </select>
        </div>

        {error && (
          <div className="p-3 bg-red-50 border border-red-200 rounded-lg text-xs text-red-700">{error}</div>
        )}

        {loading ? (
          <div className="space-y-2">
            {[...Array(5)].map((_, i) => (
              <div key={i} className="h-20 bg-gray-100 animate-pulse rounded-lg" />
            ))}
          </div>
        ) : (
          STAGE_CONFIGS.map((cfg) => {
            const cards = columns[cfg.id] ?? [];
            if (cards.length === 0) return null;
            return (
              <div key={cfg.id}>
                <div
                  className="flex items-center gap-2 px-3 py-1.5 rounded-t-lg border-t-4"
                  style={{ borderTopColor: cfg.borderColor, backgroundColor: cfg.headerBg }}
                >
                  <span className="text-xs font-bold uppercase" style={{ color: cfg.textColor }}>
                    {cfg.label}
                  </span>
                  <span
                    className="text-[10px] font-bold px-1.5 py-0.5 rounded-full text-white"
                    style={{ backgroundColor: cfg.borderColor }}
                  >
                    {cards.length}
                  </span>
                </div>
                <div className="space-y-2 p-2 bg-white border border-t-0 border-gray-200 rounded-b-lg">
                  {cards.map((c) => (
                    <KanbanCard
                      key={c.cnpj}
                      cliente={c}
                      currentStage={cfg.id}
                      onDragStart={() => {}}
                      onClick={setSelectedCnpj}
                      onMobileMove={handleMobileOpenMove}
                      isDragging={false}
                      isMobile={true}
                    />
                  ))}
                </div>
              </div>
            );
          })
        )}

        {/* Mobile move modal */}
        {mobileMoving && (
          <MobileMoveModal
            cliente={mobileMoving.cliente}
            currentStage={mobileMoving.currentStage}
            onMove={handleMobileMoveConfirm}
            onClose={() => setMobileMoving(null)}
          />
        )}

        {/* Detail panel */}
        <ClienteDetailPanel
          cnpj={selectedCnpj}
          onClose={() => setSelectedCnpj(null)}
        />
      </div>
    );
  }

  // ---------------------------------------------------------------------------
  // Desktop Kanban board with swimlane grouping
  // ---------------------------------------------------------------------------

  return (
    <div className="flex flex-col gap-3 h-full" onDragEnd={handleDragEnd}>
      {/* Page header */}
      <div className="flex-shrink-0 flex items-center justify-between">
        <div>
          <h1 className="text-lg font-bold text-gray-900">Pipeline Kanban</h1>
          <p className="text-xs text-gray-500 mt-0.5">
            {loading
              ? 'Carregando clientes...'
              : `${allClientes.length.toLocaleString('pt-BR')} clientes no pipeline`}
          </p>
        </div>
        <button
          type="button"
          onClick={loadClientes}
          disabled={loading}
          className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold text-green-700 border border-green-300 rounded-lg bg-white hover:bg-green-50 hover:border-green-400 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          aria-label="Atualizar pipeline"
        >
          <svg
            className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`}
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
            />
          </svg>
          Atualizar
        </button>
      </div>

      {/* Summary bar */}
      <SummaryBar
        totalOportunidades={totalOportunidades}
        totalUltPedido={totalUltPedido}
        totalFatAcumulado={totalFatAcumulado}
        totalClientes={allClientes.length}
        filtroConsultor={filtroConsultor}
        onFiltroConsultor={setFiltroConsultor}
        loading={loading}
        pendingMoves={pendingMoves}
      />

      {/* Error state */}
      {error && (
        <div className="flex-shrink-0 flex items-start gap-3 p-4 bg-red-50 border border-red-200 rounded-lg">
          <svg
            className="w-5 h-5 text-red-500 flex-shrink-0 mt-0.5"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
            />
          </svg>
          <div className="flex-1">
            <p className="text-sm font-semibold text-red-800">Erro ao carregar pipeline</p>
            <p className="text-xs text-red-600 mt-0.5">{error}</p>
          </div>
          <button
            type="button"
            onClick={loadClientes}
            className="flex-shrink-0 px-3 py-1.5 text-xs font-semibold text-red-700 border border-red-300 rounded-lg hover:bg-red-100 transition-colors"
          >
            Tentar novamente
          </button>
        </div>
      )}

      {/* Loading skeleton */}
      {loading && !error && (
        <div className="flex gap-6 overflow-x-auto pb-3 scrollbar-thin">
          {SWIMLANES.map((sw) => (
            <div key={sw.id} className="flex-shrink-0 flex flex-col gap-2">
              <div
                className="h-8 rounded-lg w-48 animate-pulse"
                style={{ backgroundColor: sw.bg }}
              />
              <div className="flex gap-3">
                {[...Array(sw.id === 'pos-venda' ? 4 : sw.id === 'venda' ? 4 : 3)].map((_, i) => (
                  <div
                    key={i}
                    className="flex-shrink-0 rounded-lg border border-gray-200 bg-white animate-pulse"
                    style={{ width: 220, height: 360 }}
                  >
                    <div className="h-14 bg-gray-100 rounded-t-lg" />
                    <div className="p-2 space-y-2">
                      {[...Array(4)].map((_, j) => (
                        <div key={j} className="h-16 bg-gray-50 rounded-lg border border-gray-100" />
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Kanban board — swimlane groups side by side, horizontally scrollable */}
      {!loading && (
        <div
          ref={boardRef}
          className="flex gap-6 overflow-x-auto pb-4 scrollbar-thin flex-1"
          style={{ minHeight: 0 }}
        >
          {swimlaneData.map(({ swimlane, stages }) => (
            <SwimlaneGroup
              key={swimlane.id}
              swimlane={swimlane}
              stages={stages}
              columns={columns}
              onDragStart={handleDragStart}
              onDragOver={handleDragOver}
              onDrop={handleDrop}
              onDragLeave={handleDragLeave}
              dragTargetStage={dragTargetStage}
              draggingCnpj={draggingCnpj}
              onCardClick={setSelectedCnpj}
              onMobileMove={handleMobileOpenMove}
              isMobile={false}
            />
          ))}

          {swimlaneData.length === 0 && !loading && (
            <div className="flex-1 flex items-center justify-center min-h-[200px]">
              <div className="text-center">
                <p className="text-sm font-medium text-gray-500">Nenhum cliente no pipeline</p>
                <p className="text-xs text-gray-400 mt-1">
                  Verifique os filtros ou aguarde a atualizacao dos dados
                </p>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Client detail panel */}
      <ClienteDetailPanel
        cnpj={selectedCnpj}
        onClose={() => setSelectedCnpj(null)}
      />
    </div>
  );
}
