'use client';

import { Suspense, useCallback, useEffect, useRef, useState } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import {
  fetchVendasPorStatus,
  VendaPedidoItem,
  VendasPorStatusResponse,
  formatBRL,
} from '@/lib/api';
import { exportToCSV } from '@/lib/export';
import { useAuth } from '@/contexts/AuthContext';

// ---------------------------------------------------------------------------
// Pedidos — gestao de pedidos agrupados por data com transição de status
// ---------------------------------------------------------------------------

type StatusPedido = 'DIGITADO' | 'LIBERADO' | 'FATURADO' | 'ENTREGUE' | 'CANCELADO';

const CONSULTORES = ['MANU', 'LARISSA', 'DAIANE', 'JULIO', 'OUTROS'];

const DEBOUNCE_MS = 300;

// ---------------------------------------------------------------------------
// Config de status
// ---------------------------------------------------------------------------

// Status config — cores alinhadas com R9 (ATIVO=#00B050, INAT.ANT=#FF0000)
// Evita hardcoded inline; Tailwind tokens usados para garantir design system consistente.
const STATUS_BG_CLASSES: Record<StatusPedido, string> = {
  DIGITADO:  'bg-gray-500',
  LIBERADO:  'bg-vitao-blue',
  FATURADO:  'bg-vitao-verde',
  ENTREGUE:  'bg-vitao-darkgreen',
  CANCELADO: 'bg-vitao-vermelho',
};

const STATUS_CONFIG: Record<StatusPedido, { label: string; bg: string; text: string }> = {
  DIGITADO:  { label: 'DIGITADO',  bg: '', text: '#fff' },
  LIBERADO:  { label: 'LIBERADO',  bg: '', text: '#fff' },
  FATURADO:  { label: 'FATURADO',  bg: '', text: '#fff' },
  ENTREGUE:  { label: 'ENTREGUE',  bg: '', text: '#fff' },
  CANCELADO: { label: 'CANCELADO', bg: '', text: '#fff' },
};

const STATUS_LIST: StatusPedido[] = ['DIGITADO', 'LIBERADO', 'FATURADO', 'ENTREGUE', 'CANCELADO'];

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function formatarData(iso: string | null | undefined): string {
  if (!iso) return '—';
  try {
    const d = new Date(iso);
    return d.toLocaleDateString('pt-BR', { day: '2-digit', month: '2-digit', year: 'numeric' });
  } catch {
    return String(iso);
  }
}

function labelData(iso: string | null | undefined): string {
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
    return String(iso);
  }
}

/** Agrupa items por data_pedido (YYYY-MM-DD) */
function agruparPorData(items: VendaPedidoItem[]): { label: string; data: string; pedidos: VendaPedidoItem[] }[] {
  const map = new Map<string, VendaPedidoItem[]>();
  for (const pedido of items) {
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
  const bgClass = STATUS_BG_CLASSES[status] ?? 'bg-gray-500';
  return (
    <span
      className={`inline-flex items-center px-2 py-0.5 text-xs font-semibold rounded uppercase text-white ${bgClass}`}
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
}

// Read-only modal — CRM has no authority to approve or transition orders.
// Status transitions are handled exclusively by SAP/financeiro.
function ModalPedido({ pedido, onClose }: ModalPedidoProps) {
  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      if (e.key === 'Escape') onClose();
    }
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [onClose]);

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm"
      role="dialog"
      aria-modal="true"
      aria-labelledby="modal-pedido-titulo"
    >
      <div className="relative bg-white rounded-xl shadow-xl w-full max-w-lg mx-4">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200">
          <div>
            <h2 id="modal-pedido-titulo" className="text-sm font-bold text-gray-900">
              Pedido #{pedido.numero_pedido}
            </h2>
            <p className="text-xs text-gray-500 mt-0.5">{formatarData(pedido.data_pedido)}</p>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="text-gray-500 hover:text-gray-600 p-1 rounded focus:outline-none focus:ring-2 focus:ring-green-500"
            aria-label="Fechar modal"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Body */}
        <div className="px-6 py-5 space-y-4">
          {/* Info grid */}
          <div className="grid grid-cols-2 gap-3">
            <div>
              <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-1">Cliente</p>
              <p className="text-xs font-medium text-gray-900">{pedido.nome_fantasia ?? '—'}</p>
              <p className="text-xs text-gray-500 font-mono mt-0.5">{pedido.cnpj}</p>
            </div>
            <div>
              <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-1">Consultor</p>
              <p className="text-xs font-medium text-gray-900">{pedido.consultor ?? '—'}</p>
            </div>
            <div>
              <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-1">Valor Total</p>
              <p className="text-sm font-bold text-gray-900 tabular-nums">{formatBRL(pedido.valor_pedido)}</p>
            </div>
            <div>
              <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-1">Cond. Pagamento</p>
              <p className="text-xs font-medium text-gray-900">{pedido.condicao_pagamento ?? '—'}</p>
            </div>
            <div>
              <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-1">Status Atual</p>
              <StatusBadge status={pedido.status_pedido} />
            </div>
            {pedido.fonte && (
              <div>
                <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-1">Fonte</p>
                <p className="text-xs font-medium text-gray-900">{pedido.fonte}</p>
              </div>
            )}
            {pedido.observacao && (
              <div className="col-span-2">
                <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-1">Observação</p>
                <p className="text-xs text-gray-700">{pedido.observacao}</p>
              </div>
            )}
          </div>

          {/* Aviso de governanca + botao fechar */}
          <div className="pt-3 border-t border-gray-100">
            <p className="text-xs text-gray-500 italic mb-3">
              Aprovacoes e transicoes de status sao realizadas pelo SAP/financeiro.
            </p>
            <button
              type="button"
              onClick={onClose}
              className="w-full min-h-[44px] px-4 py-2 text-xs font-semibold text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-lg transition-colors"
            >
              Fechar
            </button>
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
      aria-label={`Pedido ${pedido.numero_pedido ?? pedido.id} — ${pedido.nome_fantasia ?? pedido.cnpj}`}
    >
      <div className="flex items-start justify-between gap-2">
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2 flex-wrap">
            <span className="text-xs font-mono text-gray-500">#{pedido.numero_pedido ?? pedido.id}</span>
            <span className="text-xs font-semibold text-gray-600">{pedido.consultor ?? '—'}</span>
          </div>
          <p className="text-sm font-semibold text-gray-900 mt-0.5 truncate">{pedido.nome_fantasia ?? '—'}</p>
          <p className="text-xs text-gray-500 font-mono mt-0.5">{pedido.cnpj}</p>
        </div>
        <div className="flex-shrink-0 flex flex-col items-end gap-1.5">
          <StatusBadge status={pedido.status_pedido} />
          <span className="text-sm font-bold text-gray-900 tabular-nums">
            {formatBRL(pedido.valor_pedido)}
          </span>
        </div>
      </div>
      <div className="flex items-center gap-3 mt-2 pt-2 border-t border-gray-100">
        <span className="text-xs text-gray-500">{pedido.condicao_pagamento ?? '—'}</span>
        {pedido.fonte && (
          <span className="text-xs text-gray-500">{pedido.fonte}</span>
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
            <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mt-0.5">
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
  useAuth(); // mantido para session context; isAdmin removido — CRM nao tem alcada de aprovacao

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
  const [exporting, setExporting] = useState(false);

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

  const items = response?.items ?? [];
  const grupos = agruparPorData(items);
  const temFiltro = !!(filtroStatus || filtroConsultor || filtroDataInicio || filtroDataFim || busca);
  const totalPedidos = response?.total ?? 0;
  // Backend não retorna resumo agregado — calcular do payload atual.
  const resumoStatus = items.reduce<Record<string, number>>((acc, v) => {
    const key = v.status_pedido || 'DIGITADO';
    acc[key] = (acc[key] ?? 0) + 1;
    return acc;
  }, {});

  async function handleExportCsv() {
    setExporting(true);
    try {
      const hoje = new Date().toISOString().slice(0, 10);
      const itensFiltrados = response?.items ?? [];
      exportToCSV(
        itensFiltrados,
        [
          { label: 'Numero Pedido', value: (p) => p.numero_pedido ?? '' },
          { label: 'Data',         value: (p) => p.data_pedido?.slice(0, 10) ?? '' },
          { label: 'Cliente',      value: (p) => p.nome_fantasia ?? '' },
          { label: 'CNPJ',         value: (p) => p.cnpj ?? '', forceText: true },
          { label: 'Consultor',    value: (p) => p.consultor ?? '' },
          { label: 'Status',       value: (p) => p.status_pedido ?? '' },
          { label: 'Valor Total',  value: (p) => p.valor_pedido != null ? p.valor_pedido.toFixed(2) : '' },
          { label: 'Cond. Pagamento', value: (p) => p.condicao_pagamento ?? '' },
          { label: 'Fonte',        value: (p) => p.fonte ?? '' },
        ],
        `pedidos_vitao360_${hoje}`
      );
    } catch {
      // silencioso — erro improvavel em export client-side
    } finally {
      setExporting(false);
    }
  }

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
        <div className="flex items-center gap-2 flex-shrink-0">
          {/* Botao Exportar CSV */}
          <button
            type="button"
            onClick={handleExportCsv}
            disabled={exporting || loading || !response?.items?.length}
            aria-label="Exportar pedidos filtrados como CSV"
            className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold text-green-700 border border-green-300 rounded-lg bg-white hover:bg-green-50 hover:border-green-400 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {exporting ? (
              <svg className="w-3.5 h-3.5 animate-spin" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
              </svg>
            ) : (
              <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
              </svg>
            )}
            CSV
          </button>

          {/* Botao atualizar */}
          <button
            type="button"
            onClick={load}
            disabled={loading}
            aria-label="Atualizar lista de pedidos"
            className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold text-gray-600 border border-gray-200 rounded-lg bg-white hover:bg-gray-50 transition-colors disabled:opacity-50"
          >
            <svg className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
            Atualizar
          </button>
        </div>
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
            <label htmlFor="pedidos-busca" className="text-xs font-semibold text-gray-500 uppercase tracking-wide hidden sm:block">
              Busca
            </label>
            <div className="relative">
              <svg className="absolute left-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-gray-500 pointer-events-none" fill="none" viewBox="0 0 24 24" stroke="currentColor">
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
                }} aria-label="Limpar busca" className="absolute right-2 top-1/2 -translate-y-1/2 text-gray-500 hover:text-gray-600">
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
        <div className={`${filtrosExpanded ? 'grid grid-cols-1 xs:grid-cols-2 gap-2' : 'hidden'} sm:flex sm:flex-wrap sm:gap-2 sm:items-end mt-2`}>
          {/* Status */}
          <div className="flex flex-col gap-1">
            <label htmlFor="pedidos-status" className="text-xs font-semibold text-gray-500 uppercase tracking-wide">Status</label>
            <select
              id="pedidos-status"
              value={filtroStatus}
              onChange={(e) => {
                setFiltroStatus(e.target.value);
                pushUrl(e.target.value, filtroConsultor, filtroDataInicio, filtroDataFim, busca);
              }}
              aria-label="Filtrar por status"
              className={`w-full sm:w-auto min-h-[44px] sm:min-h-0 sm:h-8 px-2.5 text-xs border rounded focus:outline-none focus:ring-2 focus:ring-green-200 bg-white ${filtroStatus ? 'border-green-400 bg-green-50 text-green-800' : 'border-gray-200 text-gray-700'}`}
            >
              <option value="">Todos</option>
              {STATUS_LIST.map((s) => (
                <option key={s} value={s}>{STATUS_CONFIG[s].label}</option>
              ))}
            </select>
          </div>

          {/* Consultor */}
          <div className="flex flex-col gap-1">
            <label htmlFor="pedidos-consultor" className="text-xs font-semibold text-gray-500 uppercase tracking-wide">Consultor</label>
            <select
              id="pedidos-consultor"
              value={filtroConsultor}
              onChange={(e) => {
                setFiltroConsultor(e.target.value);
                pushUrl(filtroStatus, e.target.value, filtroDataInicio, filtroDataFim, busca);
              }}
              aria-label="Filtrar por consultor"
              className={`w-full sm:w-auto min-h-[44px] sm:min-h-0 sm:h-8 px-2.5 text-xs border rounded focus:outline-none focus:ring-2 focus:ring-green-200 bg-white ${filtroConsultor ? 'border-green-400 bg-green-50 text-green-800' : 'border-gray-200 text-gray-700'}`}
            >
              <option value="">Todos</option>
              {CONSULTORES.map((c) => (
                <option key={c} value={c}>{c}</option>
              ))}
            </select>
          </div>

          {/* Data inicio */}
          <div className="flex flex-col gap-1">
            <label htmlFor="pedidos-data-inicio" className="text-xs font-semibold text-gray-500 uppercase tracking-wide">De</label>
            <input
              id="pedidos-data-inicio"
              type="date"
              value={filtroDataInicio}
              onChange={(e) => {
                setFiltroDataInicio(e.target.value);
                pushUrl(filtroStatus, filtroConsultor, e.target.value, filtroDataFim, busca);
              }}
              className={`w-full sm:w-auto min-h-[44px] sm:min-h-0 sm:h-8 px-2.5 text-xs border rounded focus:outline-none focus:ring-2 focus:ring-green-200 bg-white ${filtroDataInicio ? 'border-green-400 bg-green-50' : 'border-gray-200'}`}
            />
          </div>

          {/* Data fim */}
          <div className="flex flex-col gap-1">
            <label htmlFor="pedidos-data-fim" className="text-xs font-semibold text-gray-500 uppercase tracking-wide">Ate</label>
            <input
              id="pedidos-data-fim"
              type="date"
              value={filtroDataFim}
              onChange={(e) => {
                setFiltroDataFim(e.target.value);
                pushUrl(filtroStatus, filtroConsultor, filtroDataInicio, e.target.value, busca);
              }}
              className={`w-full sm:w-auto min-h-[44px] sm:min-h-0 sm:h-8 px-2.5 text-xs border rounded focus:outline-none focus:ring-2 focus:ring-green-200 bg-white ${filtroDataFim ? 'border-green-400 bg-green-50' : 'border-gray-200'}`}
            />
          </div>

          {temFiltro && (
            <button
              type="button"
              onClick={handleLimpar}
              className="col-span-2 sm:col-span-1 sm:self-end min-h-[44px] sm:min-h-0 px-3 text-xs text-gray-500 hover:text-gray-800 border border-gray-200 rounded-lg sm:border-transparent sm:underline sm:hover:no-underline transition-colors"
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
          <svg className="w-10 h-10 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
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
                <span className="text-xs text-gray-500">{formatarData(grupo.data)}</span>
                <span className="text-xs text-gray-500">
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

      {/* Modal detalhe — read-only, sem acoes de transicao */}
      {selectedPedido && (
        <ModalPedido
          pedido={selectedPedido}
          onClose={() => setSelectedPedido(null)}
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
