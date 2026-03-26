'use client';

import { Suspense, useCallback, useEffect, useRef, useState } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import {
  fetchClientes,
  ClienteRegistro,
  ClientesResponse,
} from '@/lib/api';
import { useAuth } from '@/contexts/AuthContext';
import ClienteTable, { SortState } from '@/components/ClienteTable';
import ClienteDetalhe from '@/components/ClienteDetalhe';

// ---------------------------------------------------------------------------
// Carteira de Clientes — filtros cumulativos, URL params, ordenação, paginação
// ---------------------------------------------------------------------------

const CONSULTORES = ['LARISSA', 'MANU', 'JULIO', 'DAIANE'];
const SITUACOES   = ['ATIVO', 'INAT.REC', 'INAT.ANT', 'PROSPECT'];
const SINALEIROS  = ['VERDE', 'AMARELO', 'LARANJA', 'VERMELHO', 'ROXO'];
const ABCS        = ['A', 'B', 'C'];
const TEMPERATURAS = ['QUENTE', 'MORNO', 'FRIO', 'CRITICO', 'PERDIDO'];
const PRIORIDADES  = ['P0', 'P1', 'P2', 'P3', 'P4', 'P5'];
const UFS = [
  'AC','AL','AM','AP','BA','CE','DF','ES','GO','MA','MG','MS','MT',
  'PA','PB','PE','PI','PR','RJ','RN','RO','RR','RS','SC','SE','SP','TO',
];

const PAGE_SIZE = 50;
const DEFAULT_SORT: SortState = { by: 'score', dir: 'desc' };
const DEBOUNCE_MS = 300;

// ---------------------------------------------------------------------------
// Hook: lê/escreve filtros na URL
// ---------------------------------------------------------------------------

interface Filtros {
  consultor: string;
  situacao: string;
  sinaleiro: string;
  abc: string;
  temperatura: string;
  prioridade: string;
  uf: string;
  busca: string;
}

const FILTROS_INICIAIS: Filtros = {
  consultor: '',
  situacao: '',
  sinaleiro: '',
  abc: '',
  temperatura: '',
  prioridade: '',
  uf: '',
  busca: '',
};

function filtrosFromParams(params: URLSearchParams): Filtros {
  return {
    consultor:   params.get('consultor')   ?? '',
    situacao:    params.get('situacao')    ?? '',
    sinaleiro:   params.get('sinaleiro')   ?? '',
    abc:         params.get('abc')         ?? '',
    temperatura: params.get('temperatura') ?? '',
    prioridade:  params.get('prioridade')  ?? '',
    uf:          params.get('uf')          ?? '',
    busca:       params.get('busca')       ?? '',
  };
}

function temFiltroAtivo(f: Filtros): boolean {
  return Object.values(f).some((v) => v !== '');
}

// ---------------------------------------------------------------------------
// Page inner — precisa de Suspense porque usa useSearchParams
// ---------------------------------------------------------------------------

function CarteiraInner() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const { user } = useAuth();
  const isExternoJulio = user?.role === 'consultor_externo';

  // Filtros
  const [filtros, setFiltros] = useState<Filtros>(() => filtrosFromParams(searchParams));
  // Busca tem debounce separado
  const [buscaInput, setBuscaInput] = useState(() => searchParams.get('busca') ?? '');

  // Ordenação
  const [sort, setSort] = useState<SortState>(DEFAULT_SORT);

  // Paginação
  const [offset, setOffset] = useState(0);

  // Dados
  const [response, setResponse] = useState<ClientesResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Detalhe cliente
  const [selectedCnpj, setSelectedCnpj] = useState<string | null>(null);

  // Export CSV
  const [exporting, setExporting] = useState(false);

  // Filtros colapsados em mobile
  const [filtrosExpanded, setFiltrosExpanded] = useState(false);

  // Debounce da busca
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  // ---------------------------------------------------------------------------
  // Sincronizar filtros -> URL
  // ---------------------------------------------------------------------------

  const pushUrl = useCallback(
    (novosFiltros: Filtros, novoOffset: number, novoSort: SortState) => {
      const params = new URLSearchParams();
      Object.entries(novosFiltros).forEach(([k, v]) => {
        if (v) params.set(k, v);
      });
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
  // Carregar dados
  // ---------------------------------------------------------------------------

  const load = useCallback(() => {
    setLoading(true);
    fetchClientes({
      ...filtros,
      sort_by: sort.by,
      sort_dir: sort.dir,
      limit: PAGE_SIZE,
      offset,
    })
      .then(setResponse)
      .catch((e: Error) => setError(e.message))
      .finally(() => setLoading(false));
  }, [filtros, sort, offset]);

  useEffect(() => {
    load();
  }, [load]);

  // ---------------------------------------------------------------------------
  // Export CSV — gera client-side com os filtros ativos, encoding UTF-8 BOM
  // ---------------------------------------------------------------------------

  async function handleExportCsv() {
    setExporting(true);
    try {
      const data = await fetchClientes({
        ...filtros,
        sort_by: sort.by,
        sort_dir: sort.dir,
        limit: 10000,
        offset: 0,
      });

      const hoje = new Date().toISOString().slice(0, 10); // YYYY-MM-DD
      const cabecalho = [
        'CNPJ',
        'Nome Fantasia',
        'UF',
        'Consultor',
        'Situacao',
        'Temperatura',
        'Score',
        'Prioridade',
        'Sinaleiro',
        'ABC',
        'Faturamento',
      ];

      const linhas = data.registros.map((c) => [
        // CNPJ como texto: ="04067573000193" — Excel nao converte para numero
        `="${c.cnpj}"`,
        `"${(c.nome_fantasia ?? '').replace(/"/g, '""')}"`,
        c.uf ?? '',
        c.consultor ?? '',
        c.situacao ?? '',
        c.temperatura ?? '',
        c.score != null ? c.score.toFixed(1) : '',
        c.prioridade ?? '',
        c.sinaleiro ?? '',
        c.curva_abc ?? '',
        c.faturamento_total != null ? c.faturamento_total.toFixed(2) : '',
      ]);

      const csvContent = [
        cabecalho.join(';'),
        ...linhas.map((l) => l.join(';')),
      ].join('\r\n');

      // UTF-8 BOM para Excel BR abrir corretamente com acentos
      const BOM = '\uFEFF';
      const blob = new Blob([BOM + csvContent], { type: 'text/csv;charset=utf-8;' });
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `carteira_vitao360_${hoje}.csv`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(url);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Erro ao exportar';
      alert(`Erro ao exportar CSV: ${msg}`);
    } finally {
      setExporting(false);
    }
  }

  // ---------------------------------------------------------------------------
  // Handlers
  // ---------------------------------------------------------------------------

  function handleFilterChange(campo: keyof Filtros, valor: string) {
    const novos = { ...filtros, [campo]: valor };
    setFiltros(novos);
    setOffset(0);
    pushUrl(novos, 0, sort);
  }

  function handleBuscaChange(e: React.ChangeEvent<HTMLInputElement>) {
    const valor = e.target.value;
    setBuscaInput(valor);
    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => {
      const novos = { ...filtros, busca: valor };
      setFiltros(novos);
      setOffset(0);
      pushUrl(novos, 0, sort);
    }, DEBOUNCE_MS);
  }

  function handleBuscaClear() {
    setBuscaInput('');
    const novos = { ...filtros, busca: '' };
    setFiltros(novos);
    setOffset(0);
    pushUrl(novos, 0, sort);
  }

  function handleSort(col: string) {
    const novoSort: SortState =
      sort.by === col
        ? { by: col, dir: sort.dir === 'asc' ? 'desc' : 'asc' }
        : { by: col, dir: 'desc' };
    setSort(novoSort);
    setOffset(0);
    pushUrl(filtros, 0, novoSort);
  }

  function handleLimpar() {
    setFiltros(FILTROS_INICIAIS);
    setBuscaInput('');
    setOffset(0);
    setSort(DEFAULT_SORT);
    pushUrl(FILTROS_INICIAIS, 0, DEFAULT_SORT);
  }

  function handleRowClick(c: ClienteRegistro) {
    setSelectedCnpj(c.cnpj);
  }

  // ---------------------------------------------------------------------------
  // Paginação
  // ---------------------------------------------------------------------------

  const totalPages = response ? Math.ceil(response.total / PAGE_SIZE) : 0;
  const currentPage = Math.floor(offset / PAGE_SIZE) + 1;
  const mostrando = response
    ? `${offset + 1}–${Math.min(offset + PAGE_SIZE, response.total)}`
    : '—';

  const ativo = temFiltroAtivo(filtros);

  return (
    <div className="space-y-3">
      {/* Cabeçalho */}
      <div className="flex items-start justify-between gap-3">
        <div>
          <h1 className="text-lg sm:text-xl font-bold text-gray-900">Carteira de Clientes</h1>
          <p className="text-xs text-gray-500 mt-0.5">
            {response
              ? `${mostrando} de ${response.total.toLocaleString('pt-BR')} clientes`
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

      {/* Barra de filtros */}
      <div className="bg-white rounded-lg border border-gray-200 p-3 shadow-sm">
        {/* Header da barra de filtros — com botao toggle em mobile */}
        <div className="flex items-center gap-2 mb-2 sm:mb-0">
          {/* Busca sempre visivel */}
          <div className="flex flex-col gap-1 flex-1 min-w-0">
            <label className="text-[10px] font-semibold text-gray-500 uppercase tracking-wide hidden sm:block">
              Busca
            </label>
            <div className="relative">
              <svg
                className="absolute left-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-gray-400 pointer-events-none"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
                aria-hidden="true"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
                />
              </svg>
              <input
                type="text"
                value={buscaInput}
                onChange={handleBuscaChange}
                placeholder="Nome ou CNPJ..."
                aria-label="Buscar por nome ou CNPJ"
                className={`w-full pl-8 pr-7 py-2 sm:py-1.5 text-sm border rounded focus:outline-none focus:ring-2 focus:ring-green-200 focus:border-green-400 ${
                  filtros.busca
                    ? 'border-green-400 bg-green-50'
                    : 'border-gray-200 bg-white'
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
                {Object.values(filtros).filter(Boolean).length}
              </span>
            )}
          </button>
        </div>

        {/* Dropdowns de filtro — sempre visiveis em desktop, colapsaveis em mobile */}
        <div className={`${filtrosExpanded ? 'flex' : 'hidden'} sm:flex flex-wrap gap-2 items-end mt-2`}>
          <FilterSelect
            label="Consultor"
            value={filtros.consultor}
            onChange={(v) => handleFilterChange('consultor', v)}
            options={CONSULTORES}
          />
          <FilterSelect
            label="Situacao"
            value={filtros.situacao}
            onChange={(v) => handleFilterChange('situacao', v)}
            options={SITUACOES}
          />
          <FilterSelect
            label="Sinaleiro"
            value={filtros.sinaleiro}
            onChange={(v) => handleFilterChange('sinaleiro', v)}
            options={SINALEIROS}
          />
          <FilterSelect
            label="ABC"
            value={filtros.abc}
            onChange={(v) => handleFilterChange('abc', v)}
            options={ABCS}
          />
          <FilterSelect
            label="Temperatura"
            value={filtros.temperatura}
            onChange={(v) => handleFilterChange('temperatura', v)}
            options={TEMPERATURAS}
          />
          <FilterSelect
            label="Prioridade"
            value={filtros.prioridade}
            onChange={(v) => handleFilterChange('prioridade', v)}
            options={PRIORIDADES}
          />
          <FilterSelect
            label="UF"
            value={filtros.uf}
            onChange={(v) => handleFilterChange('uf', v)}
            options={UFS}
          />

          {/* Botão limpar */}
          {ativo && (
            <button
              type="button"
              onClick={handleLimpar}
              className="self-end text-xs text-gray-500 hover:text-gray-800 underline hover:no-underline pb-0.5"
            >
              Limpar filtros
            </button>
          )}
        </div>

        {/* Chips de filtros ativos */}
        {ativo && (
          <div className="flex flex-wrap gap-1.5 mt-2 pt-2 border-t border-gray-100">
            {Object.entries(filtros).map(([key, val]) => {
              if (!val) return null;
              return (
                <span
                  key={key}
                  className="inline-flex items-center gap-1 text-[11px] bg-green-50 text-green-800 border border-green-200 rounded px-2 py-0.5"
                >
                  <span className="font-medium">{key}:</span> {val}
                  <button
                    type="button"
                    onClick={() => handleFilterChange(key as keyof Filtros, '')}
                    aria-label={`Remover filtro ${key}`}
                    className="text-green-600 hover:text-green-900 ml-0.5"
                  >
                    <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                    </svg>
                  </button>
                </span>
              );
            })}
          </div>
        )}
      </div>

      {/* Tabela */}
      <div className="bg-white rounded-lg border border-gray-200 shadow-sm overflow-hidden">
        <ClienteTable
          registros={response?.registros ?? []}
          loading={loading}
          onRowClick={handleRowClick}
          sort={sort}
          onSort={handleSort}
          showFaturamento={!isExternoJulio}
        />

        {/* Paginação */}
        {response && response.total > PAGE_SIZE && (
          <div className="flex items-center justify-between px-3 sm:px-4 py-2.5 border-t border-gray-100 bg-gray-50 gap-3">
            <p className="text-xs text-gray-500 min-w-0">
              <span className="hidden sm:inline">{mostrando} de {response.total.toLocaleString('pt-BR')} clientes — </span>
              <span className="sm:hidden">{mostrando} — </span>
              Pag. {currentPage}/{totalPages}
            </p>
            <div className="flex gap-2 flex-shrink-0">
              <PaginationButton
                label="Anterior"
                disabled={offset === 0}
                onClick={() => {
                  const novo = Math.max(0, offset - PAGE_SIZE);
                  setOffset(novo);
                  pushUrl(filtros, novo, sort);
                }}
              />
              <PaginationButton
                label="Proxima"
                disabled={offset + PAGE_SIZE >= response.total}
                onClick={() => {
                  const novo = offset + PAGE_SIZE;
                  setOffset(novo);
                  pushUrl(filtros, novo, sort);
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
