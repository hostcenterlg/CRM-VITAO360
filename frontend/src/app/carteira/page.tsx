'use client';

import { Suspense, useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import {
  fetchClientes,
  ClienteRegistro,
  ClientesResponse,
} from '@/lib/api';
import { exportToCSV } from '@/lib/export';
import { useAuth } from '@/contexts/AuthContext';
import ClienteTable, { SortState } from '@/components/ClienteTable';
import ClienteDetalhe from '@/components/ClienteDetalhe';

// ---------------------------------------------------------------------------
// Carteira de Clientes — filtros cumulativos, URL params, ordenação, paginação
// Multi-select chips para situacao, abc, temperatura (client-side)
// Export CSV via helper exportToCSV
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
// Cores dos chips (alinhado ao Blueprint v2 do projeto)
// ---------------------------------------------------------------------------

const SITUACAO_CHIP_COLORS: Record<string, { bg: string; text: string; border: string }> = {
  'ATIVO':    { bg: '#f0fdf4', text: '#15803d', border: '#00B050' },
  'INAT.REC': { bg: '#fffbeb', text: '#92400e', border: '#FFC000' },
  'INAT.ANT': { bg: '#fef2f2', text: '#991b1b', border: '#FF0000' },
  'PROSPECT': { bg: '#faf5ff', text: '#6b21a8', border: '#7030A0' },
  'EM RISCO': { bg: '#fff7ed', text: '#c2410c', border: '#FF8C00' },
  'LEAD':     { bg: '#eff6ff', text: '#1d4ed8', border: '#2563eb' },
  'NOVO':     { bg: '#f0fdfa', text: '#0f766e', border: '#0891b2' },
};

const ABC_CHIP_COLORS: Record<string, { bg: string; text: string; border: string }> = {
  'A': { bg: '#f0fdf4', text: '#15803d', border: '#00B050' },
  'B': { bg: '#fffbeb', text: '#92400e', border: '#FFC000' },
  'C': { bg: '#fff7ed', text: '#c2410c', border: '#FF8C00' },
};

const TEMPERATURA_CHIP_COLORS: Record<string, { bg: string; text: string; border: string }> = {
  'QUENTE':  { bg: '#fef2f2', text: '#991b1b', border: '#FF0000' },
  'MORNO':   { bg: '#fffbeb', text: '#92400e', border: '#FFC000' },
  'FRIO':    { bg: '#eff6ff', text: '#1d4ed8', border: '#2563eb' },
  'CRITICO': { bg: '#fdf4ff', text: '#7e22ce', border: '#7030A0' },
};

const PAGE_SIZE = 50;
const DEFAULT_SORT: SortState = { by: 'score', dir: 'desc' };
const DEBOUNCE_MS = 300;

// ---------------------------------------------------------------------------
// Interfaces de filtros
// Filtros servidor: consultor, sinaleiro, prioridade, uf, busca
// Filtros client-side multi-select: situacoes[], abcs[], temperaturas[]
// ---------------------------------------------------------------------------

interface FiltrosServidor {
  consultor: string;
  sinaleiro: string;
  prioridade: string;
  uf: string;
  busca: string;
}

interface FiltrosCliente {
  situacoes: string[];   // multi-select
  abcs: string[];        // multi-select
  temperaturas: string[]; // multi-select
}

const FILTROS_SERVIDOR_INICIAIS: FiltrosServidor = {
  consultor: '',
  sinaleiro: '',
  prioridade: '',
  uf: '',
  busca: '',
};

const FILTROS_CLIENTE_INICIAIS: FiltrosCliente = {
  situacoes: [],
  abcs: [],
  temperaturas: [],
};

function filtrosServidorFromParams(params: URLSearchParams): FiltrosServidor {
  return {
    consultor:  params.get('consultor')  ?? '',
    sinaleiro:  params.get('sinaleiro')  ?? '',
    prioridade: params.get('prioridade') ?? '',
    uf:         params.get('uf')         ?? '',
    busca:      params.get('busca')      ?? '',
  };
}

function filtrosClienteFromParams(params: URLSearchParams): FiltrosCliente {
  return {
    situacoes:   params.get('situacoes')?.split(',').filter(Boolean)   ?? [],
    abcs:        params.get('abcs')?.split(',').filter(Boolean)        ?? [],
    temperaturas: params.get('temperaturas')?.split(',').filter(Boolean) ?? [],
  };
}

function temFiltroServidor(f: FiltrosServidor): boolean {
  return Object.values(f).some((v) => v !== '');
}

function temFiltroCliente(f: FiltrosCliente): boolean {
  return f.situacoes.length > 0 || f.abcs.length > 0 || f.temperaturas.length > 0;
}

function temFiltroAtivo(fs: FiltrosServidor, fc: FiltrosCliente): boolean {
  return temFiltroServidor(fs) || temFiltroCliente(fc);
}

// ---------------------------------------------------------------------------
// Filtro client-side — aplica multi-selects sobre registros ja carregados
// ---------------------------------------------------------------------------

function aplicarFiltrosCliente(
  registros: ClienteRegistro[],
  fc: FiltrosCliente
): ClienteRegistro[] {
  return registros.filter((r) => {
    if (fc.situacoes.length > 0 && !fc.situacoes.includes(r.situacao ?? '')) return false;
    if (fc.abcs.length > 0 && !fc.abcs.includes(r.curva_abc ?? '')) return false;
    if (fc.temperaturas.length > 0 && !fc.temperaturas.includes(r.temperatura ?? '')) return false;
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
  const isExternoJulio = user?.role === 'consultor_externo';

  // Filtros servidor (sincrono com URL)
  const [filtrosS, setFiltrosS] = useState<FiltrosServidor>(
    () => filtrosServidorFromParams(searchParams)
  );
  // Filtros client-side multi-select (sincrono com URL via params separados)
  const [filtrosC, setFiltrosC] = useState<FiltrosCliente>(
    () => filtrosClienteFromParams(searchParams)
  );

  // Busca tem debounce separado
  const [buscaInput, setBuscaInput] = useState(() => searchParams.get('busca') ?? '');

  // Ordenação
  const [sort, setSort] = useState<SortState>(DEFAULT_SORT);

  // Paginação (server-side, aplicado antes do filtro client)
  const [offset, setOffset] = useState(0);

  // Dados brutos do servidor
  const [response, setResponse] = useState<ClientesResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

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

  // Filtros colapsados em mobile
  const [filtrosExpanded, setFiltrosExpanded] = useState(false);

  // Debounce da busca
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  // ---------------------------------------------------------------------------
  // Sincronizar filtros -> URL
  // ---------------------------------------------------------------------------

  const pushUrl = useCallback(
    (fs: FiltrosServidor, fc: FiltrosCliente, novoOffset: number, novoSort: SortState) => {
      const params = new URLSearchParams();
      Object.entries(fs).forEach(([k, v]) => { if (v) params.set(k, v); });
      if (fc.situacoes.length > 0) params.set('situacoes', fc.situacoes.join(','));
      if (fc.abcs.length > 0) params.set('abcs', fc.abcs.join(','));
      if (fc.temperaturas.length > 0) params.set('temperaturas', fc.temperaturas.join(','));
      if (novoOffset > 0) params.set('offset', String(novoOffset));
      if (novoSort.by !== DEFAULT_SORT.by || novoSort.dir !== DEFAULT_SORT.dir) {
        params.set('sort_by', novoSort.by);
        params.set('sort_dir', novoSort.dir);
      }
      const query = params.toString();
      router.replace(query ? `/carteira?${query}` : '/carteira', { scroll: false });
    },
    [router]
  );

  // ---------------------------------------------------------------------------
  // Carregar dados do servidor (sem filtros client-side — esses aplicam localmente)
  // ---------------------------------------------------------------------------

  const load = useCallback(() => {
    setLoading(true);
    fetchClientes({
      ...filtrosS,
      sort_by: sort.by,
      sort_dir: sort.dir,
      limit: PAGE_SIZE,
      offset,
    })
      .then(setResponse)
      .catch((e: Error) => setError(e.message))
      .finally(() => setLoading(false));
  }, [filtrosS, sort, offset]);

  useEffect(() => {
    load();
  }, [load]);

  // ---------------------------------------------------------------------------
  // Registros apos filtros client-side (memoizado)
  // ---------------------------------------------------------------------------

  const registrosFiltrados = useMemo(
    () => aplicarFiltrosCliente(response?.registros ?? [], filtrosC),
    [response, filtrosC]
  );

  // ---------------------------------------------------------------------------
  // Export CSV — gera com filtros ativos (server + client)
  // ---------------------------------------------------------------------------

  async function handleExportCsv() {
    setExporting(true);
    try {
      const data = await fetchClientes({
        ...filtrosS,
        sort_by: sort.by,
        sort_dir: sort.dir,
        limit: 10000,
        offset: 0,
      });

      const todosRegistros = aplicarFiltrosCliente(data.registros, filtrosC);
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
  // Handlers — filtros servidor
  // ---------------------------------------------------------------------------

  function handleServidorChange(campo: keyof FiltrosServidor, valor: string) {
    const novos = { ...filtrosS, [campo]: valor };
    setFiltrosS(novos);
    setOffset(0);
    pushUrl(novos, filtrosC, 0, sort);
  }

  function handleBuscaChange(e: React.ChangeEvent<HTMLInputElement>) {
    const valor = e.target.value;
    setBuscaInput(valor);
    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => {
      const novos = { ...filtrosS, busca: valor };
      setFiltrosS(novos);
      setOffset(0);
      pushUrl(novos, filtrosC, 0, sort);
    }, DEBOUNCE_MS);
  }

  function handleBuscaClear() {
    setBuscaInput('');
    const novos = { ...filtrosS, busca: '' };
    setFiltrosS(novos);
    setOffset(0);
    pushUrl(novos, filtrosC, 0, sort);
  }

  // ---------------------------------------------------------------------------
  // Handlers — filtros client-side multi-select
  // ---------------------------------------------------------------------------

  function toggleChip<K extends keyof FiltrosCliente>(
    campo: K,
    valor: string
  ) {
    const lista = filtrosC[campo] as string[];
    const novaLista = lista.includes(valor)
      ? lista.filter((v) => v !== valor)
      : [...lista, valor];
    const novos: FiltrosCliente = { ...filtrosC, [campo]: novaLista };
    setFiltrosC(novos);
    pushUrl(filtrosS, novos, offset, sort);
  }

  function removerChipAtivo(campo: keyof FiltrosCliente, valor: string) {
    toggleChip(campo, valor);
  }

  // ---------------------------------------------------------------------------
  // Handlers — sort, limpar, paginação
  // ---------------------------------------------------------------------------

  function handleSort(col: string) {
    const novoSort: SortState =
      sort.by === col
        ? { by: col, dir: sort.dir === 'asc' ? 'desc' : 'asc' }
        : { by: col, dir: 'desc' };
    setSort(novoSort);
    setOffset(0);
    pushUrl(filtrosS, filtrosC, 0, novoSort);
  }

  function handleLimpar() {
    setFiltrosS(FILTROS_SERVIDOR_INICIAIS);
    setFiltrosC(FILTROS_CLIENTE_INICIAIS);
    setBuscaInput('');
    setOffset(0);
    setSort(DEFAULT_SORT);
    pushUrl(FILTROS_SERVIDOR_INICIAIS, FILTROS_CLIENTE_INICIAIS, 0, DEFAULT_SORT);
  }

  function handleRowClick(c: ClienteRegistro) {
    setSelectedCnpj(c.cnpj);
  }

  // ---------------------------------------------------------------------------
  // Paginação — aplica sobre total servidor (filtros client-side afetam exibicao)
  // ---------------------------------------------------------------------------

  const totalServidor = response?.total ?? 0;
  const totalFiltrado = temFiltroCliente(filtrosC) ? registrosFiltrados.length : totalServidor;
  const totalPages = Math.ceil(totalServidor / PAGE_SIZE);
  const currentPage = Math.floor(offset / PAGE_SIZE) + 1;
  const mostrando = response
    ? `${offset + 1}–${Math.min(offset + PAGE_SIZE, totalServidor)}`
    : '—';

  const ativo = temFiltroAtivo(filtrosS, filtrosC);
  const countFiltrosAtivos =
    Object.values(filtrosS).filter(Boolean).length +
    filtrosC.situacoes.length +
    filtrosC.abcs.length +
    filtrosC.temperaturas.length;

  return (
    <div className="space-y-3">
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
              ? temFiltroCliente(filtrosC)
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

      {/* ------------------------------------------------------------------ */}
      {/* Barra de filtros                                                     */}
      {/* ------------------------------------------------------------------ */}
      <div className="bg-white rounded-xl border border-gray-200 p-3 shadow-sm space-y-3">

        {/* Linha 1: Busca + toggle mobile */}
        <div className="flex items-center gap-2">
          <div className="flex flex-col gap-1 flex-1 min-w-0">
            <label className="text-[10px] font-semibold text-gray-500 uppercase tracking-wide hidden sm:block">
              Busca
            </label>
            <div className="relative">
              <svg
                className="absolute left-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-gray-400 pointer-events-none"
                fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true"
              >
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                  d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
              <input
                type="text"
                value={buscaInput}
                onChange={handleBuscaChange}
                placeholder="Nome ou CNPJ..."
                aria-label="Buscar por nome ou CNPJ"
                className={`w-full pl-8 pr-7 py-2 sm:py-1.5 text-sm border rounded focus:outline-none focus:ring-2 focus:ring-green-200 focus:border-green-400 ${
                  filtrosS.busca ? 'border-green-400 bg-green-50' : 'border-gray-200 bg-white'
                }`}
              />
              {buscaInput && (
                <button
                  type="button"
                  onClick={handleBuscaClear}
                  aria-label="Limpar busca"
                  className="absolute right-2 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
                >
                  <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              )}
            </div>
          </div>

          {/* Botao "Filtros" visivel apenas em mobile */}
          <button
            type="button"
            onClick={() => setFiltrosExpanded((v) => !v)}
            aria-expanded={filtrosExpanded}
            className={`sm:hidden flex items-center gap-1.5 min-h-11 px-3 py-2 text-sm font-medium rounded-md border transition-colors flex-shrink-0 ${
              ativo
                ? 'border-green-400 bg-green-50 text-green-800'
                : 'border-gray-200 bg-white text-gray-600'
            }`}
          >
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round"
                d="M3 4a1 1 0 011-1h16a1 1 0 011 1v2a1 1 0 01-.293.707L13 13.414V19a1 1 0 01-.553.894l-4 2A1 1 0 017 21v-7.586L3.293 6.707A1 1 0 013 6V4z" />
            </svg>
            Filtros
            {ativo && (
              <span className="inline-flex items-center justify-center w-4 h-4 rounded-full bg-green-600 text-white text-[9px] font-bold">
                {countFiltrosAtivos}
              </span>
            )}
          </button>
        </div>

        {/* Linha 2: Dropdowns servidor (colapsavel em mobile) */}
        <div className={`${filtrosExpanded ? 'flex' : 'hidden'} sm:flex flex-wrap gap-2 items-end`}>
          <FilterSelect
            label="Consultor"
            value={filtrosS.consultor}
            onChange={(v) => handleServidorChange('consultor', v)}
            options={CONSULTORES}
          />
          <FilterSelect
            label="Sinaleiro"
            value={filtrosS.sinaleiro}
            onChange={(v) => handleServidorChange('sinaleiro', v)}
            options={SINALEIROS}
          />
          <FilterSelect
            label="Prioridade"
            value={filtrosS.prioridade}
            onChange={(v) => handleServidorChange('prioridade', v)}
            options={PRIORIDADES}
          />
          <FilterSelect
            label="UF"
            value={filtrosS.uf}
            onChange={(v) => handleServidorChange('uf', v)}
            options={UFS}
          />
          {ativo && (
            <button
              type="button"
              onClick={handleLimpar}
              className="self-end text-xs text-gray-500 hover:text-gray-800 underline hover:no-underline pb-0.5"
            >
              Limpar todos
            </button>
          )}
        </div>

        {/* Linha 3: Chips multi-select Situacao (sempre visivel em desktop) */}
        <div className={`${filtrosExpanded ? 'block' : 'hidden'} sm:block`}>
          <ChipGroup
            label="Situacao"
            opcoes={SITUACOES}
            selecionados={filtrosC.situacoes}
            cores={SITUACAO_CHIP_COLORS}
            onToggle={(v) => toggleChip('situacoes', v)}
          />
        </div>

        {/* Linha 4: Chips ABC + Temperatura lado a lado */}
        <div className={`${filtrosExpanded ? 'flex' : 'hidden'} sm:flex flex-wrap gap-4`}>
          <ChipGroup
            label="Curva ABC"
            opcoes={ABCS}
            selecionados={filtrosC.abcs}
            cores={ABC_CHIP_COLORS}
            onToggle={(v) => toggleChip('abcs', v)}
          />
          <ChipGroup
            label="Temperatura"
            opcoes={TEMPERATURAS}
            selecionados={filtrosC.temperaturas}
            cores={TEMPERATURA_CHIP_COLORS}
            onToggle={(v) => toggleChip('temperaturas', v)}
          />
        </div>

        {/* Barra de filtros ativos */}
        {ativo && (
          <div className="flex flex-wrap gap-1.5 pt-2 border-t border-gray-100">
            {/* Filtros servidor */}
            {Object.entries(filtrosS).map(([key, val]) => {
              if (!val) return null;
              const rotulo = key === 'busca' ? 'Busca' : key.charAt(0).toUpperCase() + key.slice(1);
              return (
                <ChipAtivo
                  key={`s-${key}`}
                  rotulo={rotulo}
                  valor={val}
                  onRemover={() => {
                    if (key === 'busca') { setBuscaInput(''); }
                    handleServidorChange(key as keyof FiltrosServidor, '');
                  }}
                />
              );
            })}
            {/* Multi-selects cliente */}
            {filtrosC.situacoes.map((s) => (
              <ChipAtivo
                key={`sit-${s}`}
                rotulo="Situacao"
                valor={s}
                onRemover={() => removerChipAtivo('situacoes', s)}
                cor={SITUACAO_CHIP_COLORS[s]}
              />
            ))}
            {filtrosC.abcs.map((a) => (
              <ChipAtivo
                key={`abc-${a}`}
                rotulo="ABC"
                valor={a}
                onRemover={() => removerChipAtivo('abcs', a)}
                cor={ABC_CHIP_COLORS[a]}
              />
            ))}
            {filtrosC.temperaturas.map((t) => (
              <ChipAtivo
                key={`tmp-${t}`}
                rotulo="Temp."
                valor={t}
                onRemover={() => removerChipAtivo('temperaturas', t)}
                cor={TEMPERATURA_CHIP_COLORS[t]}
              />
            ))}
            {/* Limpar todos */}
            <button
              type="button"
              onClick={handleLimpar}
              className="text-[11px] text-red-500 hover:text-red-700 font-medium border border-red-200 rounded px-2 py-0.5 hover:bg-red-50 transition-colors"
            >
              Limpar todos
            </button>
          </div>
        )}
      </div>

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
              {temFiltroCliente(filtrosC) && (
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
                  pushUrl(filtrosS, filtrosC, novo, sort);
                }}
              />
              <PaginationButton
                label="Proxima"
                disabled={offset + PAGE_SIZE >= totalServidor}
                onClick={() => {
                  const novo = offset + PAGE_SIZE;
                  setOffset(novo);
                  pushUrl(filtrosS, filtrosC, novo, sort);
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

interface ChipGroupProps {
  label: string;
  opcoes: string[];
  selecionados: string[];
  cores: Record<string, { bg: string; text: string; border: string }>;
  onToggle: (valor: string) => void;
}

function ChipGroup({ label, opcoes, selecionados, cores, onToggle }: ChipGroupProps) {
  return (
    <div className="flex flex-wrap items-center gap-1.5">
      <span className="text-[10px] font-semibold text-gray-500 uppercase tracking-wide mr-1 flex-shrink-0">
        {label}
      </span>
      {opcoes.map((opcao) => {
        const ativo = selecionados.includes(opcao);
        const cor = cores[opcao] ?? { bg: '#f9fafb', text: '#374151', border: '#d1d5db' };
        return (
          <button
            key={opcao}
            type="button"
            onClick={() => onToggle(opcao)}
            aria-pressed={ativo}
            className="inline-flex items-center px-2.5 py-1 text-[11px] font-semibold rounded-full border cursor-pointer transition-all select-none"
            style={
              ativo
                ? { backgroundColor: cor.bg, color: cor.text, borderColor: cor.border, boxShadow: `0 0 0 2px ${cor.border}40` }
                : { backgroundColor: '#f9fafb', color: '#9ca3af', borderColor: '#e5e7eb' }
            }
          >
            {opcao}
            {ativo && (
              <svg className="w-3 h-3 ml-1 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
              </svg>
            )}
          </button>
        );
      })}
    </div>
  );
}

interface ChipAtivoProps {
  rotulo: string;
  valor: string;
  onRemover: () => void;
  cor?: { bg: string; text: string; border: string };
}

function ChipAtivo({ rotulo, valor, onRemover, cor }: ChipAtivoProps) {
  return (
    <span
      className="inline-flex items-center gap-1 text-[11px] rounded px-2 py-0.5 border font-medium"
      style={
        cor
          ? { backgroundColor: cor.bg, color: cor.text, borderColor: cor.border }
          : { backgroundColor: '#f0fdf4', color: '#15803d', borderColor: '#bbf7d0' }
      }
    >
      <span className="opacity-70 text-[10px]">{rotulo}:</span>
      <span>{valor}</span>
      <button
        type="button"
        onClick={onRemover}
        aria-label={`Remover filtro ${rotulo} ${valor}`}
        className="ml-0.5 opacity-60 hover:opacity-100 transition-opacity"
      >
        <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
        </svg>
      </button>
    </span>
  );
}

interface FilterSelectProps {
  label: string;
  value: string;
  onChange: (v: string) => void;
  options: string[];
}

function FilterSelect({ label, value, onChange, options }: FilterSelectProps) {
  const id = `filter-${label.toLowerCase().replace(/\s/g, '-')}`;
  const isActive = value !== '';
  return (
    <div className="flex flex-col gap-1 min-w-[110px]">
      <label
        htmlFor={id}
        className="text-[10px] font-semibold text-gray-500 uppercase tracking-wide"
      >
        {label}
      </label>
      <select
        id={id}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        aria-label={`Filtrar por ${label}`}
        className={`border rounded px-2 py-1.5 text-xs text-gray-700 bg-white focus:outline-none focus:ring-2 focus:ring-green-200 focus:border-green-400 transition-colors ${
          isActive
            ? 'border-green-400 bg-green-50 text-green-800 font-medium'
            : 'border-gray-200'
        }`}
      >
        <option value="">Todos</option>
        {options.map((opt) => (
          <option key={opt} value={opt}>
            {opt}
          </option>
        ))}
      </select>
    </div>
  );
}

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
          ? 'border-gray-200 text-gray-300 cursor-not-allowed'
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
