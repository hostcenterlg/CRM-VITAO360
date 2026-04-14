'use client';

import { Suspense, useCallback, useEffect, useRef, useState } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import {
  fetchVendasPorStatus,
  transicionarStatusVenda,
  VendaPedidoItem,
  VendasPorStatusResponse,
  formatBRL,
} from '@/lib/api';
import { useAuth } from '@/contexts/AuthContext';

// ---------------------------------------------------------------------------
// Pedidos — gestao de pedidos agrupados por data com transição de status
// ---------------------------------------------------------------------------

type StatusPedido = 'DIGITADO' | 'LIBERADO' | 'FATURADO' | 'ENTREGUE' | 'CANCELADO';

const CONSULTORES = ['LARISSA', 'MANU', 'DAIANE', 'JULIO'];

const DEBOUNCE_MS = 300;

// ---------------------------------------------------------------------------
// Config de status
// ---------------------------------------------------------------------------

const STATUS_CONFIG: Record<StatusPedido, { label: string; bg: string; text: string }> = {
  DIGITADO:  { label: 'DIGITADO',  bg: '#6B7280', text: '#fff' },
  LIBERADO:  { label: 'LIBERADO',  bg: '#3B82F6', text: '#fff' },
  FATURADO:  { label: 'FATURADO',  bg: '#00B050', text: '#fff' },
  ENTREGUE:  { label: 'ENTREGUE',  bg: '#166534', text: '#fff' },
  CANCELADO: { label: 'CANCELADO', bg: '#FF0000', text: '#fff' },
};

const STATUS_LIST: StatusPedido[] = ['DIGITADO', 'LIBERADO', 'FATURADO', 'ENTREGUE', 'CANCELADO'];

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function formatarData(iso: string): string {
  if (!iso) return '—';
  try {
    const d = new Date(iso);
    return d.toLocaleDateString('pt-BR', { day: '2-digit', month: '2-digit', year: 'numeric' });
  } catch {
    return iso;
  }
}

function labelData(iso: string): string {
  if (!iso) return 'Sem data';
  try {
    const hoje = new Date();
    const d = new Date(iso);
    const diff = Math.floor(
      (new Date(hoje.toDateString()).getTime() - new Date(d.toDateString()).getTime()) / 86400000
    );
    if (diff === 0) return 'HOJE';
    if (diff === 1) return 'ONTEM';
    return d.toLocaleDateString('pt-BR', { weekday: 'long', day: '2-digit', month: 'long' });
  } catch {
    return iso;
  }
}

/** Agrupa itens por data_pedido (YYYY-MM-DD) */
function agruparPorData(itens: VendaPedidoItem[]): { label: string; data: string; pedidos: VendaPedidoItem[] }[] {
  const map = new Map<string, VendaPedidoItem[]>();
  for (const pedido of itens) {
    const chave = pedido.data_pedido?.slice(0, 10) ?? 'sem-data';
    const lista = map.get(chave) ?? [];
    lista.push(pedido);
    map.set(chave, lista);
  }
  // Ordenar datas decrescentes
  return Array.from(map.entries())
    .sort(([a], [b]) => b.localeCompare(a))
    .map(([data, pedidos]) => ({
      data,
      label: labelData(data),
      pedidos,
    }));
}

// ---------------------------------------------------------------------------
// StatusBadge
// ---------------------------------------------------------------------------

function StatusBadge({ status }: { status: StatusPedido }) {
  const cfg = STATUS_CONFIG[status] ?? STATUS_CONFIG.DIGITADO;
  return (
    <span
      className="inline-flex items-center px-2 py-0.5 text-[10px] font-semibold rounded uppercase"
      style={{ backgroundColor: cfg.bg, color: cfg.text }}
    >
      {cfg.label}
    </span>
  );
}

// ---------------------------------------------------------------------------
// Modal de detalhe do pedido
// ---------------------------------------------------------------------------

interface ModalPedidoProps {
  pedido: VendaPedidoItem;
  onClose: () => void;
  onTransicionar: (id: number, novoStatus: string) => Promise<void>;
  isAdmin: boolean;
}

function ModalPedido({ pedido, onClose, onTransicionar, isAdmin }: ModalPedidoProps) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [formDirty, setFormDirty] = useState(false);
  const [confirmDescarte, setConfirmDescarte] = useState(false);

  function tentarFechar() {
    if (formDirty) {
      setConfirmDescarte(true);
    } else {
      onClose();
    }
  }

  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      if (e.key === 'Escape') {
        if (confirmDescarte) {
          setConfirmDescarte(false);
        } else {
          tentarFechar();
        }
      }
    }
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [formDirty, confirmDescarte]);

  async function handleAcao(novoStatus: string) {
    setFormDirty(true);
    setLoading(true);
    setError(null);
    try {
      await onTransicionar(pedido.id, novoStatus);
      setFormDirty(false);
      onClose();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Erro ao atualizar status');
    } finally {
      setLoading(false);
    }
  }

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm"
      role="dialog"
      aria-modal="true"
      aria-labelledby="modal-pedido-titulo"
    >
      <div className="relative bg-white rounded-xl shadow-xl w-full max-w-lg mx-4">
        {/* Mini-confirmacao de descarte */}
        {confirmDescarte && (
          <div className="absolute inset-0 z-10 flex items-center justify-center bg-black/30 rounded-lg">
            <div className="bg-white rounded-lg shadow-xl mx-6 p-5 w-full max-w-xs text-center">
              <p className="text-sm font-semibold text-gray-900 mb-1">Descartar alteracoes?</p>
              <p className="text-xs text-gray-500 mb-4">As mudancas nao salvas serao perdidas.</p>
              <div className="flex gap-3 justify-center">
                <button
                  type="button"
                  onClick={() => setConfirmDescarte(false)}
                  className="px-4 py-2 text-xs font-medium text-gray-700 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors"
                >
                  Continuar editando
                </button>
                <button
                  type="button"
                  onClick={onClose}
                  className="px-4 py-2 text-xs font-semibold text-white rounded-lg transition-colors"
                  style={{ backgroundColor: '#FF0000' }}
                >
                  Descartar
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200">
          <div>
            <h2 id="modal-pedido-titulo" className="text-sm font-bold text-gray-900">
              Pedido #{pedido.numero_pedido}
            </h2>
            <p className="text-[11px] text-gray-500 mt-0.5">{formatarData(pedido.data_pedido)}</p>
          </div>
          <button
            type="button"
            onClick={tentarFechar}
            className="text-gray-400 hover:text-gray-600 p-1 rounded focus:outline-none focus:ring-2 focus:ring-green-500"
            aria-label="Fechar modal"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Body */}
        <div className="px-6 py-5 space-y-4">
          {error && (
            <div role="alert" className="px-3 py-2 bg-red-50 border border-red-200 rounded text-xs text-red-700">
              {error}
            </div>
          )}

          {/* Info grid */}
          <div className="grid grid-cols-2 gap-3">
            <div>
              <p className="text-[10px] font-semibold text-gray-500 uppercase tracking-wide mb-1">Cliente</p>
              <p className="text-xs font-medium text-gray-900">{pedido.cliente_nome}</p>
              <p className="text-[10px] text-gray-400 font-mono mt-0.5">{pedido.cliente_cnpj}</p>
            </div>
            <div>
              <p className="text-[10px] font-semibold text-gray-500 uppercase tracking-wide mb-1">Consultor</p>
              <p className="text-xs font-medium text-gray-900">{pedido.consultor}</p>
            </div>
            <div>
              <p className="text-[10px] font-semibold text-gray-500 uppercase tracking-wide mb-1">Valor Total</p>
              <p className="text-sm font-bold text-gray-900 tabular-nums">{formatBRL(pedido.valor_total)}</p>
            </div>
            <div>
              <p className="text-[10px] font-semibold text-gray-500 uppercase tracking-wide mb-1">Cond. Pagamento</p>
              <p className="text-xs font-medium text-gray-900">{pedido.condicao_pagamento}</p>
            </div>
            <div>
              <p className="text-[10px] font-semibold text-gray-500 uppercase tracking-wide mb-1">Status Atual</p>
              <StatusBadge status={pedido.status} />
            </div>
            {pedido.itens_qtd != null && (
              <div>
                <p className="text-[10px] font-semibold text-gray-500 uppercase tracking-wide mb-1">Itens</p>
                <p className="text-xs font-medium text-gray-900">{pedido.itens_qtd} produto{pedido.itens_qtd !== 1 ? 's' : ''}</p>
              </div>
            )}
          </div>

          {/* Botoes de transicao */}
          <div className="pt-3 border-t border-gray-100 space-y-2">
            <p className="text-[10px] font-semibold text-gray-500 uppercase tracking-wide mb-2">Acoes</p>
            <div className="flex flex-wrap gap-2">
              {pedido.status === 'DIGITADO' && (
                <button
                  type="button"
                  disabled={loading}
                  onClick={() => void handleAcao('LIBERADO')}
                  className="px-4 py-2 text-xs font-semibold text-white rounded-lg transition-colors disabled:opacity-60"
                  style={{ backgroundColor: '#3B82F6' }}
                >
                  Liberar Pedido
                </button>
              )}
              {pedido.status === 'LIBERADO' && (
                <button
                  type="button"
                  disabled={loading}
                  onClick={() => void handleAcao('FATURADO')}
                  className="px-4 py-2 text-xs font-semibold text-white rounded-lg transition-colors disabled:opacity-60"
                  style={{ backgroundColor: '#00B050' }}
                >
                  Faturar Pedido
                </button>
              )}
              {pedido.status === 'FATURADO' && (
                <button
                  type="button"
                  disabled={loading}
                  onClick={() => void handleAcao('ENTREGUE')}
                  className="px-4 py-2 text-xs font-semibold text-white rounded-lg transition-colors disabled:opacity-60"
                  style={{ backgroundColor: '#166534' }}
                >
                  Marcar Entregue
                </button>
              )}
              {pedido.status !== 'CANCELADO' && pedido.status !== 'ENTREGUE' && isAdmin && (
                <button
                  type="button"
                  disabled={loading}
                  onClick={() => void handleAcao('CANCELADO')}
                  className="px-4 py-2 text-xs font-semibold text-white rounded-lg transition-colors disabled:opacity-60"
                  style={{ backgroundColor: '#FF0000' }}
                >
                  Cancelar
                </button>
              )}
              {(pedido.status === 'CANCELADO' || pedido.status === 'ENTREGUE') && (
                <p className="text-xs text-gray-400 italic">Nenhuma acao disponivel para este status</p>
              )}
            </div>
            {loading && (
              <div className="flex items-center gap-2 text-xs text-gray-500">
                <div className="w-3.5 h-3.5 border-2 border-gray-300 border-t-green-600 rounded-full animate-spin" />
                Processando...
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Card de pedido individual
// ---------------------------------------------------------------------------

interface CardPedidoProps {
  pedido: VendaPedidoItem;
  onClick: () => void;
}

function CardPedido({ pedido, onClick }: CardPedidoProps) {
  return (
    <button
      type="button"
      onClick={onClick}
      className="w-full text-left bg-white rounded-lg border border-gray-200 p-3 hover:border-green-300 hover:shadow-sm transition-all focus:outline-none focus:ring-2 focus:ring-green-500"
      aria-label={`Pedido ${pedido.numero_pedido} — ${pedido.cliente_nome}`}
    >
      <div className="flex items-start justify-between gap-2">
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2 flex-wrap">
            <span className="text-[11px] font-mono text-gray-400">#{pedido.numero_pedido}</span>
            <span className="text-[11px] font-semibold text-gray-600">{pedido.consultor}</span>
          </div>
          <p className="text-sm font-semibold text-gray-900 mt-0.5 truncate">{pedido.cliente_nome}</p>
          <p className="text-[10px] text-gray-400 font-mono mt-0.5">{pedido.cliente_cnpj}</p>
        </div>
        <div className="flex-shrink-0 flex flex-col items-end gap-1.5">
          <StatusBadge status={pedido.status} />
          <span className="text-sm font-bold text-gray-900 tabular-nums">
            {formatBRL(pedido.valor_total)}
          </span>
        </div>
      </div>
      <div className="flex items-center gap-3 mt-2 pt-2 border-t border-gray-100">
        <span className="text-[11px] text-gray-500">{pedido.condicao_pagamento}</span>
        {pedido.itens_qtd != null && (
          <span className="text-[11px] text-gray-400">{pedido.itens_qtd} item{pedido.itens_qtd !== 1 ? 's' : ''}</span>
        )}
      </div>
    </button>
  );
}

// ---------------------------------------------------------------------------
// Resumo de status (cards no topo)
// ---------------------------------------------------------------------------

function ResumoStatus({ resumo }: { resumo: Record<string, number> }) {
  const ordem: StatusPedido[] = ['DIGITADO', 'LIBERADO', 'FATURADO', 'ENTREGUE', 'CANCELADO'];
  return (
    <div className="grid grid-cols-3 sm:grid-cols-5 gap-2">
      {ordem.map((status) => {
        const cfg = STATUS_CONFIG[status];
        const qtd = resumo[status] ?? 0;
        return (
          <div key={status} className="bg-white rounded-xl border border-gray-200 p-3 text-center shadow-sm"
            style={{ borderLeftColor: cfg.bg, borderLeftWidth: '3px' }}>
            <p
              className="text-lg font-bold tabular-nums"
              style={{ color: cfg.bg }}
            >
              {qtd}
            </p>
            <p className="text-[10px] font-semibold text-gray-500 uppercase tracking-wide mt-0.5">
              {cfg.label}
            </p>
          </div>
        );
      })}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Inner — usa useSearchParams
// ---------------------------------------------------------------------------

function PedidosInner() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const { isAdmin } = useAuth();

  const [busca, setBusca] = useState(() => searchParams.get('busca') ?? '');
  const [buscaInput, setBuscaInput] = useState(() => searchParams.get('busca') ?? '');
  const [filtroStatus, setFiltroStatus] = useState(() => searchParams.get('status') ?? '');
  const [filtroConsultor, setFiltroConsultor] = useState(() => {
    // Se usuario e consultor, pré-filtrar pela carteira dele
    return searchParams.get('consultor') ?? '';
  });
  const [filtroDataInicio, setFiltroDataInicio] = useState(() => searchParams.get('data_inicio') ?? '');
  const [filtroDataFim, setFiltroDataFim] = useState(() => searchParams.get('data_fim') ?? '');

  const [response, setResponse] = useState<VendasPorStatusResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [apiError, setApiError] = useState<string | null>(null);

  const [selectedPedido, setSelectedPedido] = useState<VendaPedidoItem | null>(null);
  const [filtrosExpanded, setFiltrosExpanded] = useState(false);

  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const pushUrl = useCallback(
    (st: string, cons: string, di: string, df: string, b: string) => {
      const params = new URLSearchParams();
      if (st) params.set('status', st);
      if (cons) params.set('consultor', cons);
      if (di) params.set('data_inicio', di);
      if (df) params.set('data_fim', df);
      if (b) params.set('busca', b);
      const q = params.toString();
      router.replace(q ? `/pedidos?${q}` : '/pedidos', { scroll: false });
    },
    [router]
  );

  const load = useCallback(() => {
    setLoading(true);
    setError(null);
    fetchVendasPorStatus({
      status: filtroStatus || undefined,
      consultor: filtroConsultor || undefined,
      data_inicio: filtroDataInicio || undefined,
      data_fim: filtroDataFim || undefined,
      busca: busca || undefined,
      limit: 200,
    })
      .then(setResponse)
      .catch((e: Error) => setError(e.message))
      .finally(() => setLoading(false));
  }, [filtroStatus, filtroConsultor, filtroDataInicio, filtroDataFim, busca]);

  useEffect(() => {
    load();
  }, [load]);

  function handleBuscaChange(e: React.ChangeEvent<HTMLInputElement>) {
    const v = e.target.value;
    setBuscaInput(v);
    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => {
      setBusca(v);
      pushUrl(filtroStatus, filtroConsultor, filtroDataInicio, filtroDataFim, v);
    }, DEBOUNCE_MS);
  }

  function handleLimpar() {
    setBusca('');
    setBuscaInput('');
    setFiltroStatus('');
    setFiltroConsultor('');
    setFiltroDataInicio('');
    setFiltroDataFim('');
    router.replace('/pedidos', { scroll: false });
  }

  async function handleTransicionar(id: number, novoStatus: string) {
    await transicionarStatusVenda(id, novoStatus);
    await load();
  }

  const grupos = agruparPorData(response?.itens ?? []);
  const temFiltro = !!(filtroStatus || filtroConsultor || filtroDataInicio || filtroDataFim || busca);
  const totalPedidos = response?.total ?? 0;
  const resumoStatus = response?.resumo_status ?? {};

  return (
    <div className="space-y-4">
      {/* Cabecalho */}
      <div className="flex items-start justify-between gap-3">
        <div>
          <h1 className="text-lg sm:text-xl font-bold text-gray-900">Pedidos</h1>
          <p className="text-xs text-gray-500 mt-0.5">
            {loading
              ? 'Carregando...'
              : `${totalPedidos.toLocaleString('pt-BR')} pedido${totalPedidos !== 1 ? 's' : ''}`}
          </p>
        </div>
        {/* Botao atualizar */}
        <button
          type="button"
          onClick={load}
          disabled={loading}
          aria-label="Atualizar lista de pedidos"
          className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold text-gray-600 border border-gray-200 rounded-lg bg-white hover:bg-gray-50 transition-colors disabled:opacity-50 flex-shrink-0"
        >
          <svg className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
              d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
          </svg>
          Atualizar
        </button>
      </div>

      {/* Resumo de status */}
      {!loading && response && <ResumoStatus resumo={resumoStatus} />}
      {loading && (
        <div className="grid grid-cols-3 sm:grid-cols-5 gap-2">
          {[1,2,3,4,5].map((i) => (
            <div key={i} className="h-16 bg-gray-100 animate-pulse rounded-lg" />
          ))}
        </div>
      )}

      {/* Erro */}
      {error && (
        <div role="alert" className="flex items-start gap-3 p-4 bg-red-50 border border-red-200 rounded-lg">
          <svg className="w-5 h-5 text-red-500 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
              d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
          </svg>
          <div className="flex-1">
            <p className="text-sm font-semibold text-red-800">Erro ao carregar pedidos</p>
            <p className="text-xs text-red-600 mt-0.5">{error}</p>
          </div>
          <button type="button" onClick={load} className="flex-shrink-0 px-3 py-1.5 text-xs font-semibold text-red-700 border border-red-300 rounded-lg hover:bg-red-100 transition-colors">
            Tentar novamente
          </button>
        </div>
      )}

      {/* Erro de acao */}
      {apiError && (
        <div role="alert" className="p-3 bg-red-50 border border-red-200 rounded-lg text-xs text-red-700">
          {apiError}
          <button type="button" onClick={() => setApiError(null)} className="ml-2 text-red-500 hover:text-red-700">
            <svg className="w-3.5 h-3.5 inline" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
      )}

      {/* Filtros */}
      <div className="bg-white rounded-xl border border-gray-200 p-3 shadow-sm">
        <div className="flex items-center gap-2 mb-2 sm:mb-0">
          {/* Busca — sempre visivel */}
          <div className="flex flex-col gap-1 flex-1 min-w-0">
            <label htmlFor="pedidos-busca" className="text-[10px] font-semibold text-gray-500 uppercase tracking-wide hidden sm:block">
              Busca
            </label>
            <div className="relative">
              <svg className="absolute left-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-gray-400 pointer-events-none" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
              <input
                id="pedidos-busca"
                type="text"
                value={buscaInput}
                onChange={handleBuscaChange}
                placeholder="Cliente, CNPJ ou numero..."
                aria-label="Buscar pedido"
                className={`w-full pl-8 pr-7 py-2 sm:py-1.5 text-sm border rounded focus:outline-none focus:ring-2 focus:ring-green-200 focus:border-green-400 ${
                  busca ? 'border-green-400 bg-green-50' : 'border-gray-200 bg-white'
                }`}
              />
              {buscaInput && (
                <button type="button" onClick={() => {
                  setBuscaInput(''); setBusca('');
                  pushUrl(filtroStatus, filtroConsultor, filtroDataInicio, filtroDataFim, '');
                }} aria-label="Limpar busca" className="absolute right-2 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600">
                  <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              )}
            </div>
          </div>

          {/* Toggle filtros mobile */}
          <button
            type="button"
            onClick={() => setFiltrosExpanded((v) => !v)}
            aria-expanded={filtrosExpanded}
            className={`sm:hidden flex items-center gap-1.5 min-h-11 px-3 py-2 text-sm font-medium rounded-md border transition-colors flex-shrink-0 ${
              temFiltro ? 'border-green-400 bg-green-50 text-green-800' : 'border-gray-200 bg-white text-gray-600'
            }`}
          >
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M3 4a1 1 0 011-1h16a1 1 0 011 1v2a1 1 0 01-.293.707L13 13.414V19a1 1 0 01-.553.894l-4 2A1 1 0 017 21v-7.586L3.293 6.707A1 1 0 013 6V4z" />
            </svg>
            Filtros
          </button>
        </div>

        {/* Filtros expandidos */}
        <div className={`${filtrosExpanded ? 'flex' : 'hidden'} sm:flex flex-wrap gap-2 items-end mt-2`}>
          {/* Status */}
          <div className="flex flex-col gap-1 min-w-[130px]">
            <label htmlFor="pedidos-status" className="text-[10px] font-semibold text-gray-500 uppercase tracking-wide">Status</label>
            <select
              id="pedidos-status"
              value={filtroStatus}
              onChange={(e) => {
                setFiltroStatus(e.target.value);
                pushUrl(e.target.value, filtroConsultor, filtroDataInicio, filtroDataFim, busca);
              }}
              aria-label="Filtrar por status"
              className={`h-8 px-2.5 text-xs border rounded focus:outline-none focus:ring-2 focus:ring-green-200 bg-white ${filtroStatus ? 'border-green-400 bg-green-50 text-green-800' : 'border-gray-200 text-gray-700'}`}
            >
              <option value="">Todos</option>
              {STATUS_LIST.map((s) => (
                <option key={s} value={s}>{STATUS_CONFIG[s].label}</option>
              ))}
            </select>
          </div>

          {/* Consultor */}
          <div className="flex flex-col gap-1 min-w-[120px]">
            <label htmlFor="pedidos-consultor" className="text-[10px] font-semibold text-gray-500 uppercase tracking-wide">Consultor</label>
            <select
              id="pedidos-consultor"
              value={filtroConsultor}
              onChange={(e) => {
                setFiltroConsultor(e.target.value);
                pushUrl(filtroStatus, e.target.value, filtroDataInicio, filtroDataFim, busca);
              }}
              aria-label="Filtrar por consultor"
              className={`h-8 px-2.5 text-xs border rounded focus:outline-none focus:ring-2 focus:ring-green-200 bg-white ${filtroConsultor ? 'border-green-400 bg-green-50 text-green-800' : 'border-gray-200 text-gray-700'}`}
            >
              <option value="">Todos</option>
              {CONSULTORES.map((c) => (
                <option key={c} value={c}>{c}</option>
              ))}
            </select>
          </div>

          {/* Data inicio */}
          <div className="flex flex-col gap-1">
            <label htmlFor="pedidos-data-inicio" className="text-[10px] font-semibold text-gray-500 uppercase tracking-wide">De</label>
            <input
              id="pedidos-data-inicio"
              type="date"
              value={filtroDataInicio}
              onChange={(e) => {
                setFiltroDataInicio(e.target.value);
                pushUrl(filtroStatus, filtroConsultor, e.target.value, filtroDataFim, busca);
              }}
              className={`h-8 px-2.5 text-xs border rounded focus:outline-none focus:ring-2 focus:ring-green-200 bg-white ${filtroDataInicio ? 'border-green-400 bg-green-50' : 'border-gray-200'}`}
            />
          </div>

          {/* Data fim */}
          <div className="flex flex-col gap-1">
            <label htmlFor="pedidos-data-fim" className="text-[10px] font-semibold text-gray-500 uppercase tracking-wide">Ate</label>
            <input
              id="pedidos-data-fim"
              type="date"
              value={filtroDataFim}
              onChange={(e) => {
                setFiltroDataFim(e.target.value);
                pushUrl(filtroStatus, filtroConsultor, filtroDataInicio, e.target.value, busca);
              }}
              className={`h-8 px-2.5 text-xs border rounded focus:outline-none focus:ring-2 focus:ring-green-200 bg-white ${filtroDataFim ? 'border-green-400 bg-green-50' : 'border-gray-200'}`}
            />
          </div>

          {temFiltro && (
            <button
              type="button"
              onClick={handleLimpar}
              className="self-end text-xs text-gray-500 hover:text-gray-800 underline hover:no-underline pb-0.5"
            >
              Limpar
            </button>
          )}
        </div>
      </div>

      {/* Lista agrupada */}
      {loading ? (
        <div className="space-y-4">
          {[1, 2].map((g) => (
            <div key={g} className="space-y-2">
              <div className="h-5 w-24 bg-gray-100 animate-pulse rounded" />
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                {[1, 2, 3, 4].map((i) => (
                  <div key={i} className="h-24 bg-gray-100 animate-pulse rounded-lg" />
                ))}
              </div>
            </div>
          ))}
        </div>
      ) : grupos.length === 0 ? (
        <div className="bg-white rounded-xl border border-gray-200 py-16 flex flex-col items-center gap-3 shadow-sm">
          <svg className="w-10 h-10 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
              d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
          </svg>
          <p className="text-sm font-medium text-gray-500">Nenhum pedido encontrado</p>
          {temFiltro && (
            <button type="button" onClick={handleLimpar} className="text-xs text-green-600 hover:underline">
              Limpar filtros
            </button>
          )}
        </div>
      ) : (
        <div className="space-y-5">
          {grupos.map((grupo) => (
            <div key={grupo.data}>
              {/* Label do grupo */}
              <div className="flex items-center gap-3 mb-2">
                <span className="text-xs font-bold text-gray-700 uppercase tracking-wide">
                  {grupo.label}
                </span>
                <span className="text-[11px] text-gray-400">{formatarData(grupo.data)}</span>
                <span className="text-[11px] text-gray-400">
                  ({grupo.pedidos.length} pedido{grupo.pedidos.length !== 1 ? 's' : ''})
                </span>
                <div className="flex-1 h-px bg-gray-200" />
              </div>

              {/* Grid de cards */}
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
                {grupo.pedidos.map((pedido) => (
                  <CardPedido
                    key={pedido.id}
                    pedido={pedido}
                    onClick={() => setSelectedPedido(pedido)}
                  />
                ))}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Modal detalhe */}
      {selectedPedido && (
        <ModalPedido
          pedido={selectedPedido}
          onClose={() => setSelectedPedido(null)}
          onTransicionar={handleTransicionar}
          isAdmin={isAdmin}
        />
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Export com Suspense
// ---------------------------------------------------------------------------

export default function PedidosPage() {
  return (
    <Suspense
      fallback={
        <div className="space-y-4">
          <div className="h-8 bg-gray-100 animate-pulse rounded w-40" />
          <div className="grid grid-cols-5 gap-2">
            {[1,2,3,4,5].map((i) => <div key={i} className="h-16 bg-gray-100 animate-pulse rounded-lg" />)}
          </div>
          <div className="h-96 bg-gray-100 animate-pulse rounded" />
        </div>
      }
    >
      <PedidosInner />
    </Suspense>
  );
}
