'use client';

import { Suspense, useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import {
  fetchClientes,
  fetchDashboardHero,
  ClienteRegistro,
  ClientesResponse,
  KPIsHeroResponse,
} from '@/lib/api';
import { exportToCSV } from '@/lib/export';
import { useAuth } from '@/contexts/AuthContext';
import { useCanal } from '@/contexts/CanalContext';
import ClienteTable, { SortState } from '@/components/ClienteTable';
import ClienteDetalhe from '@/components/ClienteDetalhe';
import { FilterGroup, FilterField, FilterState } from '@/components/ui';
import CurvaABCBars from '@/components/dashboard/CurvaABCBars';
import Top5ClientesTable from '@/components/dashboard/Top5ClientesTable';

// ---------------------------------------------------------------------------
// Carteira de Clientes — filtros cumulativos, URL params, ordenação, paginação
// Wave 2B: FilterGroup 3 níveis, sem label BUSCA, CLIENTE primeira coluna
// ---------------------------------------------------------------------------

const CONSULTORES = ['MANU', 'LARISSA', 'DAIANE', 'JULIO', 'OUTROS'];
const SITUACOES   = ['ATIVO', 'INAT.REC', 'INAT.ANT', 'PROSPECT', 'EM RISCO', 'LEAD', 'NOVO'];
const SINALEIROS  = ['VERDE', 'AMARELO', 'LARANJA', 'VERMELHO', 'ROXO'];
const ABCS        = ['A', 'B', 'C'];
const TEMPERATURAS = ['QUENTE', 'MORNO', 'FRIO', 'CRITICO'];
const PRIORIDADES  = ['P0', 'P1', 'P2', 'P3', 'P4', 'P5', 'P6', 'P7'];
const UFS = [
  'AC','AL','AM','AP','BA','CE','DF','ES','GO','MA','MG','MS','MT',
  'PA','PB','PE','PI','PR','RJ','RN','RO','RR','RS','SC','SE','SP','TO',
];

// ---------------------------------------------------------------------------
// FilterGroup field schema — 3 níveis hierárquicos
// Nível 1 (sempre visível): busca + consultor
// Nível 2 (pills): situação
// Nível 3 (colapsável): curva ABC, temperatura, sinaleiro, prioridade, UF
// ---------------------------------------------------------------------------

const FILTER_FIELDS: FilterField[] = [
  // Nível 1
  {
    id: 'busca',
    label: 'Nome ou CNPJ',
    level: 1,
    type: 'search',
    placeholder: 'Nome ou CNPJ...',
    className: 'flex-1 min-w-[200px]',
  },
  {
    id: 'consultor',
    label: 'Consultor',
    level: 1,
    type: 'select',
    placeholder: 'Todos consultores',
    options: CONSULTORES.map((c) => ({ value: c, label: c })),
  },

  // Nível 2 — pills situação
  {
    id: 'situacoes',
    label: 'Situação',
    level: 2,
    type: 'pill-toggle',
    multi: true,
    options: SITUACOES.map((s) => ({ value: s, label: s })),
  },

  // Nível 3 — colapsável
  {
    id: 'abcs',
    label: 'Curva ABC',
    level: 3,
    type: 'pill-toggle',
    multi: true,
    options: ABCS.map((a) => ({ value: a, label: `Curva ${a}` })),
  },
  {
    id: 'temperaturas',
    label: 'Temperatura',
    level: 3,
    type: 'pill-toggle',
    multi: true,
    options: TEMPERATURAS.map((t) => ({ value: t, label: t })),
  },
  {
    id: 'sinaleiro',
    label: 'Sinaleiro',
    level: 3,
    type: 'select',
    placeholder: 'Todos',
    options: SINALEIROS.map((s) => ({ value: s, label: s })),
  },
  {
    id: 'prioridade',
    label: 'Prioridade',
    level: 3,
    type: 'select',
    placeholder: 'Todas',
    options: PRIORIDADES.map((p) => ({ value: p, label: p })),
  },
  {
    id: 'uf',
    label: 'UF',
    level: 3,
    type: 'select',
    placeholder: 'Todas',
    options: UFS.map((u) => ({ value: u, label: u })),
  },
];

const PAGE_SIZE = 50;
const DEFAULT_SORT: SortState = { by: 'score', dir: 'desc' };

// ---------------------------------------------------------------------------
// FilterState helpers
// ---------------------------------------------------------------------------

const FILTER_STATE_INICIAL: FilterState = {
  busca: '',
  consultor: '',
  situacoes: [],
  abcs: [],
  temperaturas: [],
  sinaleiro: '',
  prioridade: '',
  uf: '',
};

function filterStateFromParams(params: URLSearchParams): FilterState {
  return {
    busca:       params.get('busca')       ?? '',
    consultor:   params.get('consultor')   ?? '',
    situacoes:   params.get('situacoes')?.split(',').filter(Boolean)    ?? [],
    abcs:        params.get('abcs')?.split(',').filter(Boolean)         ?? [],
    temperaturas: params.get('temperaturas')?.split(',').filter(Boolean) ?? [],
    sinaleiro:   params.get('sinaleiro')   ?? '',
    prioridade:  params.get('prioridade')  ?? '',
    uf:          params.get('uf')          ?? '',
  };
}

function temFiltroAtivo(s: FilterState): boolean {
  return (
    !!s.busca ||
    !!s.consultor ||
    (s.situacoes as string[]).length > 0 ||
    (s.abcs as string[]).length > 0 ||
    (s.temperaturas as string[]).length > 0 ||
    !!s.sinaleiro ||
    !!s.prioridade ||
    !!s.uf
  );
}

// ---------------------------------------------------------------------------
// Filtro client-side para multi-selects situacao/abc/temperatura
// ---------------------------------------------------------------------------

function aplicarFiltrosCliente(
  registros: ClienteRegistro[],
  fs: FilterState
): ClienteRegistro[] {
  const situacoes = fs.situacoes as string[];
  const abcs      = fs.abcs      as string[];
  const temps     = fs.temperaturas as string[];

  return (registros ?? []).filter((r) => {
    if (situacoes.length > 0 && !situacoes.includes(r.situacao ?? '')) return false;
    if (abcs.length      > 0 && !abcs.includes(r.curva_abc ?? ''))     return false;
    if (temps.length     > 0 && !temps.includes(r.temperatura ?? ''))  return false;
    return true;
  });
}

// ---------------------------------------------------------------------------
// Page inner — precisa de Suspense porque usa useSearchParams
// ---------------------------------------------------------------------------

function CarteiraInner() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const { user } = useAuth();
  const { canalId } = useCanal();
  const isExternoJulio = user?.role === 'consultor_externo';

  const [filterState, setFilterState] = useState<FilterState>(
    () => filterStateFromParams(searchParams)
  );

  // Ordenação
  const [sort, setSort] = useState<SortState>(DEFAULT_SORT);

  // Paginação (server-side)
  const [offset, setOffset] = useState(0);

  // Dados brutos do servidor
  const [response, setResponse] = useState<ClientesResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Hero — Curva ABC + Top 5 clientes (graceful degrade)
  const [hero, setHero] = useState<KPIsHeroResponse | null>(null);
  const [heroLoading, setHeroLoading] = useState(true);

  useEffect(() => {
    setHeroLoading(true);
    fetchDashboardHero()
      .then(setHero)
      .catch(() => setHero(null))
      .finally(() => setHeroLoading(false));
  }, []);

  // Detalhe cliente
  const [selectedCnpj, setSelectedCnpj] = useState<string | null>(null);

  // Export CSV
  const [exporting, setExporting] = useState(false);

  // Toast inline
  const [toastMsg, setToastMsg] = useState<{ texto: string; tipo: 'erro' | 'sucesso' } | null>(null);
  const toastTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  function showToast(texto: string, tipo: 'erro' | 'sucesso' = 'erro') {
    if (toastTimerRef.current) clearTimeout(toastTimerRef.current);
    setToastMsg({ texto, tipo });
    toastTimerRef.current = setTimeout(() => setToastMsg(null), 5000);
  }

  // ---------------------------------------------------------------------------
  // Sincronizar filtros -> URL
  // ---------------------------------------------------------------------------

  const pushUrl = useCallback(
    (fs: FilterState, novoOffset: number, novoSort: SortState) => {
      const params = new URLSearchParams();
      if (fs.busca)      params.set('busca',       fs.busca as string);
      if (fs.consultor)  params.set('consultor',   fs.consultor as string);
      if (fs.sinaleiro)  params.set('sinaleiro',   fs.sinaleiro as string);
      if (fs.prioridade) params.set('prioridade',  fs.prioridade as string);
      if (fs.uf)         params.set('uf',          fs.uf as string);
      const sits = fs.situacoes as string[];
      const abcs = fs.abcs as string[];
      const temps = fs.temperaturas as string[];
      if (sits.length  > 0) params.set('situacoes',    sits.join(','));
      if (abcs.length  > 0) params.set('abcs',         abcs.join(','));
      if (temps.length > 0) params.set('temperaturas', temps.join(','));
      if (novoOffset > 0) params.set('offset', String(novoOffset));
      if (novoSort.by !== DEFAULT_SORT.by || novoSort.dir !== DEFAULT_SORT.dir) {
        params.set('sort_by',  novoSort.by);
        params.set('sort_dir', novoSort.dir);
      }
      const query = params.toString();
      router.replace(query ? `/carteira?${query}` : '/carteira', { scroll: false });
    },
    [router]
  );

  // ---------------------------------------------------------------------------
  // Carregar dados do servidor — filtros que vão ao backend:
  //   busca, consultor, sinaleiro, prioridade, uf (os restantes = client-side)
  // ---------------------------------------------------------------------------

  const load = useCallback(() => {
    setLoading(true);
    fetchClientes({
      busca:      filterState.busca as string,
      consultor:  filterState.consultor as string,
      sinaleiro:  filterState.sinaleiro as string,
      prioridade: filterState.prioridade as string,
      uf:         filterState.uf as string,
      sort_by:    sort.by,
      sort_dir:   sort.dir,
      limit:      PAGE_SIZE,
      offset,
      canal_id:   canalId,
    })
      .then(setResponse)
      .catch((e: Error) => setError(e.message))
      .finally(() => setLoading(false));
  }, [filterState, sort, offset, canalId]);

  useEffect(() => {
    load();
  }, [load]);

  // ---------------------------------------------------------------------------
  // Registros apos filtros client-side (memoizado)
  // ---------------------------------------------------------------------------

  const registrosFiltrados = useMemo(
    () => aplicarFiltrosCliente(response?.registros ?? [], filterState),
    [response, filterState]
  );

  // ---------------------------------------------------------------------------
  // Export CSV
  // ---------------------------------------------------------------------------

  async function handleExportCsv() {
    setExporting(true);
    try {
      const data = await fetchClientes({
        busca:      filterState.busca as string,
        consultor:  filterState.consultor as string,
        sinaleiro:  filterState.sinaleiro as string,
        prioridade: filterState.prioridade as string,
        uf:         filterState.uf as string,
        sort_by:    sort.by,
        sort_dir:   sort.dir,
        limit:      10000,
        offset:     0,
        canal_id:   canalId,
      });

      const todosRegistros = aplicarFiltrosCliente(data.registros ?? [], filterState);
      const hoje = new Date().toISOString().slice(0, 10);

      exportToCSV(
        todosRegistros,
        [
          { label: 'CNPJ',           value: (r) => r.cnpj,             forceText: true },
          { label: 'Nome Fantasia',   value: (r) => r.nome_fantasia ?? '' },
          { label: 'UF',             value: (r) => r.uf ?? '' },
          { label: 'Consultor',      value: (r) => r.consultor ?? '' },
          { label: 'Situacao',       value: (r) => r.situacao ?? '' },
          { label: 'Temperatura',    value: (r) => r.temperatura ?? '' },
          { label: 'Score',          value: (r) => r.score != null ? r.score.toFixed(1) : '' },
          { label: 'Prioridade',     value: (r) => r.prioridade ?? '' },
          { label: 'Sinaleiro',      value: (r) => r.sinaleiro ?? '' },
          { label: 'Curva ABC',      value: (r) => r.curva_abc ?? '' },
          { label: 'Faturamento',    value: (r) => r.faturamento_total != null ? r.faturamento_total.toFixed(2) : '' },
        ],
        `carteira_vitao360_${hoje}`
      );

      showToast(`CSV exportado com sucesso — ${todosRegistros.length} clientes.`, 'sucesso');
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Erro ao exportar';
      showToast(`Erro ao exportar CSV: ${msg}`, 'erro');
    } finally {
      setExporting(false);
    }
  }

  // ---------------------------------------------------------------------------
  // Handler unificado para FilterGroup
  // ---------------------------------------------------------------------------

  function handleFilterChange(next: FilterState) {
    setFilterState(next);
    setOffset(0);
    pushUrl(next, 0, sort);
  }

  function handleLimpar() {
    setFilterState(FILTER_STATE_INICIAL);
    setOffset(0);
    setSort(DEFAULT_SORT);
    pushUrl(FILTER_STATE_INICIAL, 0, DEFAULT_SORT);
  }

  // ---------------------------------------------------------------------------
  // Handlers — sort, paginação
  // ---------------------------------------------------------------------------

  function handleSort(col: string) {
    const novoSort: SortState =
      sort.by === col
        ? { by: col, dir: sort.dir === 'asc' ? 'desc' : 'asc' }
        : { by: col, dir: 'desc' };
    setSort(novoSort);
    setOffset(0);
    pushUrl(filterState, 0, novoSort);
  }

  function handleRowClick(c: ClienteRegistro) {
    setSelectedCnpj(c.cnpj);
  }

  // ---------------------------------------------------------------------------
  // Paginação
  // ---------------------------------------------------------------------------

  const totalServidor = response?.total ?? 0;
  const situacoes = filterState.situacoes as string[];
  const abcs      = filterState.abcs      as string[];
  const temps     = filterState.temperaturas as string[];
  const hasClientFilters = situacoes.length > 0 || abcs.length > 0 || temps.length > 0;
  const totalFiltrado = hasClientFilters ? (registrosFiltrados?.length ?? 0) : totalServidor;
  const totalPages = Math.ceil(totalServidor / PAGE_SIZE);
  const currentPage = Math.floor(offset / PAGE_SIZE) + 1;
  const mostrando = response
    ? `${offset + 1}–${Math.min(offset + PAGE_SIZE, totalServidor)}`
    : '—';

  const ativo = temFiltroAtivo(filterState);

  return (
    <div className="space-y-3">
      {/* Curva ABC + Top 5 Clientes — bloco de inteligencia de clientes */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 mb-6">
        <div className="lg:col-span-2 bg-white rounded-xl shadow-sm border border-gray-100 p-5">
          <h2 className="text-sm font-bold text-gray-900 mb-4">Curva ABC</h2>
          <CurvaABCBars data={hero?.curva_abc} loading={heroLoading} />
        </div>
        <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-5">
          <h2 className="text-sm font-bold text-gray-900 mb-4">Top 5 Clientes (Mes)</h2>
          <Top5ClientesTable rows={hero?.top_5 ?? []} loading={heroLoading} />
        </div>
      </div>

      {/* Toast inline */}
      {toastMsg && (
        <div
          role="alert"
          className={`flex items-center justify-between gap-3 px-4 py-3 rounded-lg border text-sm font-medium
            ${toastMsg.tipo === 'erro'
              ? 'bg-red-50 border-red-200 text-red-700'
              : 'bg-green-50 border-green-200 text-green-700'}`}
        >
          <span>{toastMsg.texto}</span>
          <button
            type="button"
            onClick={() => setToastMsg(null)}
            aria-label="Fechar"
            className="flex-shrink-0 opacity-60 hover:opacity-100 transition-opacity"
          >
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
      )}

      {/* Cabeçalho */}
      <div className="flex items-start justify-between gap-3">
        <div>
          <h1 className="text-lg sm:text-xl font-bold text-gray-900">Carteira de Clientes</h1>
          <p className="text-xs text-gray-500 mt-0.5">
            {response
              ? hasClientFilters
                ? `Mostrando ${totalFiltrado.toLocaleString('pt-BR')} de ${totalServidor.toLocaleString('pt-BR')} clientes (filtro local aplicado)`
                : `Mostrando ${mostrando} de ${totalServidor.toLocaleString('pt-BR')} clientes`
              : 'Carregando...'}
          </p>
        </div>

        {/* Botao Exportar CSV */}
        <button
          type="button"
          onClick={handleExportCsv}
          disabled={exporting || loading}
          aria-label="Exportar carteira filtrada como CSV"
          className="flex items-center gap-1.5 min-h-11 sm:min-h-0 px-3 py-1.5 text-xs font-semibold text-green-700 border border-green-300 rounded-lg bg-white hover:bg-green-50 hover:border-green-400 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex-shrink-0"
        >
          {exporting ? (
            <>
              <svg className="w-3.5 h-3.5 animate-spin" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
              </svg>
              Exportando...
            </>
          ) : (
            <>
              <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2} aria-hidden="true">
                <path strokeLinecap="round" strokeLinejoin="round" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
              </svg>
              Exportar CSV
            </>
          )}
        </button>
      </div>

      {/* Erro */}
      {error && (
        <div className="flex items-start gap-3 p-4 bg-red-50 border border-red-200 rounded-lg">
          <svg className="w-5 h-5 text-red-500 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
              d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
          </svg>
          <div className="flex-1">
            <p className="text-sm font-semibold text-red-800">Erro ao carregar clientes</p>
            <p className="text-xs text-red-600 mt-0.5">{error}</p>
          </div>
          <button
            type="button"
            onClick={load}
            className="flex-shrink-0 px-3 py-1.5 text-xs font-semibold text-red-700 border border-red-300 rounded-lg hover:bg-red-100 transition-colors"
          >
            Tentar novamente
          </button>
        </div>
      )}

      {/* FilterGroup — 3 níveis */}
      <FilterGroup
        fields={FILTER_FIELDS}
        state={filterState}
        onChange={handleFilterChange}
        onReset={ativo ? handleLimpar : undefined}
        resultsCount={response ? totalFiltrado : undefined}
      />

      {/* Tabela */}
      <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
        <ClienteTable
          registros={registrosFiltrados}
          loading={loading}
          onRowClick={handleRowClick}
          sort={sort}
          onSort={handleSort}
          showFaturamento={!isExternoJulio}
          hasActiveFilters={ativo}
          onResetFilters={handleLimpar}
        />

        {/* Paginação */}
        {response && totalServidor > PAGE_SIZE && (
          <div className="flex items-center justify-between px-3 sm:px-4 py-2.5 border-t border-gray-100 bg-gray-50 gap-3">
            <p className="text-xs text-gray-500 min-w-0">
              <span className="hidden sm:inline">
                Mostrando {mostrando} de {totalServidor.toLocaleString('pt-BR')} clientes —{' '}
              </span>
              <span className="sm:hidden">{mostrando} de {totalServidor.toLocaleString('pt-BR')} — </span>
              Pag. {currentPage}/{totalPages}
              {hasClientFilters && (
                <span className="text-orange-600 font-medium"> | {totalFiltrado.toLocaleString('pt-BR')} apos filtro local</span>
              )}
            </p>
            <div className="flex gap-2 flex-shrink-0">
              <PaginationButton
                label="Anterior"
                disabled={offset === 0}
                onClick={() => {
                  const novo = Math.max(0, offset - PAGE_SIZE);
                  setOffset(novo);
                  pushUrl(filterState, novo, sort);
                }}
              />
              <PaginationButton
                label="Proxima"
                disabled={offset + PAGE_SIZE >= totalServidor}
                onClick={() => {
                  const novo = offset + PAGE_SIZE;
                  setOffset(novo);
                  pushUrl(filterState, novo, sort);
                }}
              />
            </div>
          </div>
        )}
      </div>

      {/* Detalhe do cliente */}
      <ClienteDetalhe
        cnpj={selectedCnpj}
        onClose={() => setSelectedCnpj(null)}
      />
    </div>
  );
}

// ---------------------------------------------------------------------------
// Sub-componentes
// ---------------------------------------------------------------------------

interface PaginationButtonProps {
  label: string;
  disabled: boolean;
  onClick: () => void;
}

function PaginationButton({ label, disabled, onClick }: PaginationButtonProps) {
  return (
    <button
      type="button"
      disabled={disabled}
      onClick={onClick}
      className={`min-h-11 sm:min-h-0 px-3 py-2 sm:py-1.5 rounded text-xs font-medium border transition-colors ${
        disabled
          ? 'border-gray-200 text-gray-500 cursor-not-allowed'
          : 'border-gray-300 text-gray-600 hover:bg-gray-50 hover:border-gray-400'
      }`}
    >
      {label}
    </button>
  );
}

// ---------------------------------------------------------------------------
// Export default com Suspense (obrigatorio para useSearchParams no Next.js 14)
// ---------------------------------------------------------------------------

export default function CarteiraPage() {
  return (
    <Suspense
      fallback={
        <div className="space-y-3">
          <div className="h-8 bg-gray-100 animate-pulse rounded w-48" />
          <div className="h-16 bg-gray-100 animate-pulse rounded" />
          <div className="h-96 bg-gray-100 animate-pulse rounded" />
        </div>
      }
    >
      <CarteiraInner />
    </Suspense>
  );
}
