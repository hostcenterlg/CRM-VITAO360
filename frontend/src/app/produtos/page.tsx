'use client';

import { Suspense, useCallback, useEffect, useRef, useState } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import {
  fetchProdutos,
  fetchProdutoCategorias,
  fetchProdutosMaisVendidos,
  fetchProduto,
  ProdutoItem,
  ProdutosResponse,
  formatBRL,
} from '@/lib/api';

// ---------------------------------------------------------------------------
// Produtos — catálogo com filtros, ordenação, detalhe e mais vendidos
// ---------------------------------------------------------------------------

const PAGE_SIZE = 50;
const DEBOUNCE_MS = 300;

type SortCol = 'codigo' | 'nome' | 'categoria' | 'preco_tabela' | 'comissao_pct';
type SortDir = 'asc' | 'desc';

interface SortState {
  col: SortCol;
  dir: SortDir;
}

const DEFAULT_SORT: SortState = { col: 'nome', dir: 'asc' };

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function formatPercent(n: number): string {
  return `${n.toFixed(1)}%`;
}

// ---------------------------------------------------------------------------
// Badge Ativo/Inativo
// ---------------------------------------------------------------------------

function BadgeAtivo({ ativo }: { ativo: boolean }) {
  return (
    <span
      className="inline-flex items-center px-2 py-0.5 text-[10px] font-semibold rounded uppercase"
      style={ativo
        ? { backgroundColor: '#00B050', color: '#fff' }
        : { backgroundColor: '#FF0000', color: '#fff' }
      }
    >
      {ativo ? 'Ativo' : 'Inativo'}
    </span>
  );
}

// ---------------------------------------------------------------------------
// Skeleton de linha de tabela
// ---------------------------------------------------------------------------

function SkeletonRow() {
  return (
    <tr className="border-b border-gray-100">
      {[40, 120, 100, 60, 60, 80, 50, 60].map((w, i) => (
        <td key={i} className="px-4 py-3">
          <div className="h-3 rounded animate-pulse bg-gray-100" style={{ width: w }} />
        </td>
      ))}
    </tr>
  );
}

// ---------------------------------------------------------------------------
// Modal de detalhe de produto
// ---------------------------------------------------------------------------

interface ModalProdutoProps {
  produtoId: number;
  onClose: () => void;
}

function ModalProduto({ produtoId, onClose }: ModalProdutoProps) {
  const [produto, setProduto] = useState<ProdutoItem | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    fetchProduto(produtoId)
      .then((p) => { if (!cancelled) setProduto(p); })
      .catch((e: Error) => { if (!cancelled) setError(e.message); })
      .finally(() => { if (!cancelled) setLoading(false); });
    return () => { cancelled = true; };
  }, [produtoId]);

  useEffect(() => {
    function onKey(e: KeyboardEvent) { if (e.key === 'Escape') onClose(); }
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [onClose]);

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm"
      role="dialog"
      aria-modal="true"
      aria-labelledby="modal-produto-titulo"
    >
      <div className="bg-white rounded-xl shadow-xl w-full max-w-lg mx-4 max-h-[90vh] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200 flex-shrink-0">
          <h2 id="modal-produto-titulo" className="text-sm font-bold text-gray-900 uppercase tracking-wide">
            Detalhe do Produto
          </h2>
          <button
            type="button"
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 p-1 rounded focus:outline-none focus:ring-2 focus:ring-green-500"
            aria-label="Fechar modal"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Body */}
        <div className="overflow-y-auto flex-1 px-6 py-5">
          {loading && (
            <div className="flex items-center justify-center py-12">
              <div className="w-5 h-5 border-2 border-gray-300 border-t-green-600 rounded-full animate-spin" />
            </div>
          )}

          {error && (
            <div role="alert" className="p-3 bg-red-50 border border-red-200 rounded text-xs text-red-700">
              {error}
            </div>
          )}

          {produto && !loading && (
            <div className="space-y-4">
              {/* Cabecalho do produto */}
              <div className="flex items-start justify-between gap-3">
                <div>
                  <p className="text-xs font-mono text-gray-400">{produto.codigo}</p>
                  <h3 className="text-base font-bold text-gray-900 mt-0.5">{produto.nome}</h3>
                  <p className="text-xs text-gray-500 mt-0.5">{produto.categoria}</p>
                </div>
                <BadgeAtivo ativo={produto.ativo} />
              </div>

              {/* Descricao */}
              {produto.descricao && (
                <p className="text-xs text-gray-600 leading-relaxed">{produto.descricao}</p>
              )}

              {/* Grid de detalhes */}
              <div className="grid grid-cols-2 gap-3">
                <div className="bg-gray-50 rounded p-3">
                  <p className="text-[10px] font-semibold text-gray-500 uppercase tracking-wide mb-1">Unidade</p>
                  <p className="text-sm font-semibold text-gray-900">{produto.unidade}</p>
                </div>
                <div className="bg-gray-50 rounded p-3">
                  <p className="text-[10px] font-semibold text-gray-500 uppercase tracking-wide mb-1">Preco Tabela</p>
                  <p className="text-sm font-semibold text-gray-900">{formatBRL(produto.preco_tabela)}</p>
                </div>
                <div className="bg-gray-50 rounded p-3">
                  <p className="text-[10px] font-semibold text-gray-500 uppercase tracking-wide mb-1">Comissao</p>
                  <p className="text-sm font-semibold" style={{ color: '#00B050' }}>
                    {formatPercent(produto.comissao_pct)}
                  </p>
                </div>
                {produto.peso_liquido != null && (
                  <div className="bg-gray-50 rounded p-3">
                    <p className="text-[10px] font-semibold text-gray-500 uppercase tracking-wide mb-1">Peso Liquido</p>
                    <p className="text-sm font-semibold text-gray-900">{produto.peso_liquido} kg</p>
                  </div>
                )}
                {produto.validade_dias != null && (
                  <div className="bg-gray-50 rounded p-3">
                    <p className="text-[10px] font-semibold text-gray-500 uppercase tracking-wide mb-1">Validade</p>
                    <p className="text-sm font-semibold text-gray-900">{produto.validade_dias} dias</p>
                  </div>
                )}
              </div>

              {/* Precos regionais */}
              {produto.precos_regionais && produto.precos_regionais.length > 0 && (
                <div>
                  <p className="text-[10px] font-semibold text-gray-500 uppercase tracking-wide mb-2">
                    Precos Regionais
                  </p>
                  <div className="space-y-1.5">
                    {produto.precos_regionais.map((pr) => (
                      <div
                        key={pr.regiao}
                        className="flex items-center justify-between px-3 py-2 rounded bg-gray-50 text-xs"
                      >
                        <span className="text-gray-700 font-medium">{pr.regiao}</span>
                        <span className="text-gray-900 font-semibold tabular-nums">{formatBRL(pr.preco)}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Cabeçalho de coluna ordenável
// ---------------------------------------------------------------------------

interface ThSortProps {
  label: string;
  col: SortCol;
  sort: SortState;
  onSort: (col: SortCol) => void;
}

function ThSort({ label, col, sort, onSort }: ThSortProps) {
  const active = sort.col === col;
  return (
    <th
      scope="col"
      className="px-4 py-2.5 text-left text-[10px] font-semibold text-gray-500 uppercase tracking-wide cursor-pointer select-none hover:text-gray-700 whitespace-nowrap"
      onClick={() => onSort(col)}
      aria-sort={active ? (sort.dir === 'asc' ? 'ascending' : 'descending') : 'none'}
    >
      <span className="flex items-center gap-1">
        {label}
        <svg className={`w-3 h-3 flex-shrink-0 ${active ? 'text-green-600' : 'text-gray-300'}`} fill="none" viewBox="0 0 24 24" stroke="currentColor">
          {active && sort.dir === 'asc' ? (
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 15l7-7 7 7" />
          ) : active && sort.dir === 'desc' ? (
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
          ) : (
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 9l4-4 4 4M16 15l-4 4-4-4" />
          )}
        </svg>
      </span>
    </th>
  );
}

// ---------------------------------------------------------------------------
// Card "Mais Vendidos"
// ---------------------------------------------------------------------------

function MaisVendidosSection() {
  const [itens, setItens] = useState<ProdutoItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    fetchProdutosMaisVendidos({ limit: 5 })
      .then((data) => { if (!cancelled) setItens(data); })
      .catch(() => {/* silencioso: seção opcional */})
      .finally(() => { if (!cancelled) setLoading(false); });
    return () => { cancelled = true; };
  }, []);

  if (!loading && itens.length === 0) return null;

  return (
    <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-4">
      <div className="flex items-center gap-2 mb-3">
        <svg className="w-4 h-4 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24" style={{ color: '#FFC000' }}>
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
            d="M11.049 2.927c.3-.921 1.603-.921 1.902 0l1.519 4.674a1 1 0 00.95.69h4.915c.969 0 1.371 1.24.588 1.81l-3.976 2.888a1 1 0 00-.363 1.118l1.518 4.674c.3.922-.755 1.688-1.538 1.118l-3.976-2.888a1 1 0 00-1.176 0l-3.976 2.888c-.783.57-1.838-.197-1.538-1.118l1.518-4.674a1 1 0 00-.363-1.118l-3.976-2.888c-.784-.57-.38-1.81.588-1.81h4.914a1 1 0 00.951-.69l1.519-4.674z" />
        </svg>
        <h2 className="text-sm font-bold text-gray-900">Mais Vendidos</h2>
        <span className="text-[10px] text-gray-400">Top 5 produtos por volume</span>
      </div>

      {loading ? (
        <div className="flex gap-3 overflow-x-auto pb-1">
          {[1, 2, 3, 4, 5].map((i) => (
            <div key={i} className="flex-shrink-0 w-40 h-20 rounded-lg animate-pulse bg-gray-100" />
          ))}
        </div>
      ) : (
        <div className="flex gap-3 overflow-x-auto pb-1">
          {itens.map((item, idx) => (
            <div
              key={item.id}
              className="flex-shrink-0 w-44 rounded-lg border border-gray-200 p-3 bg-gray-50 hover:bg-white hover:border-green-300 transition-colors"
            >
              <div className="flex items-start justify-between mb-2">
                <span
                  className="inline-flex items-center justify-center w-5 h-5 rounded-full text-[10px] font-bold text-white flex-shrink-0"
                  style={{ backgroundColor: idx === 0 ? '#FFC000' : idx === 1 ? '#9CA3AF' : idx === 2 ? '#CD7F32' : '#00B050' }}
                >
                  {idx + 1}
                </span>
                <BadgeAtivo ativo={item.ativo} />
              </div>
              <p className="text-xs font-semibold text-gray-900 leading-snug line-clamp-2">{item.nome}</p>
              <p className="text-[10px] text-gray-500 mt-1">{item.categoria}</p>
              <p className="text-xs font-semibold mt-1.5 tabular-nums" style={{ color: '#00B050' }}>
                {formatBRL(item.preco_tabela)}
              </p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Inner da pagina (usa useSearchParams)
// ---------------------------------------------------------------------------

function ProdutosInner() {
  const searchParams = useSearchParams();
  const router = useRouter();

  const [busca, setBusca] = useState(() => searchParams.get('busca') ?? '');
  const [buscaInput, setBuscaInput] = useState(() => searchParams.get('busca') ?? '');
  const [categoria, setCategoria] = useState(() => searchParams.get('categoria') ?? '');
  const [apenasAtivos, setApenasAtivos] = useState(
    () => searchParams.get('ativo') !== 'false'
  );

  const [sort, setSort] = useState<SortState>(DEFAULT_SORT);
  const [offset, setOffset] = useState(0);

  const [response, setResponse] = useState<ProdutosResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [categorias, setCategorias] = useState<string[]>([]);

  const [selectedId, setSelectedId] = useState<number | null>(null);

  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  // Carregar categorias uma vez
  useEffect(() => {
    fetchProdutoCategorias()
      .then(setCategorias)
      .catch(() => {/* silencioso: lista cai para vazio */});
  }, []);

  // Sincronizar com URL
  const pushUrl = useCallback(
    (b: string, cat: string, ativo: boolean, off: number) => {
      const params = new URLSearchParams();
      if (b) params.set('busca', b);
      if (cat) params.set('categoria', cat);
      if (!ativo) params.set('ativo', 'false');
      if (off > 0) params.set('offset', String(off));
      const q = params.toString();
      router.replace(q ? `/produtos?${q}` : '/produtos', { scroll: false });
    },
    [router]
  );

  const load = useCallback(() => {
    setLoading(true);
    setError(null);
    fetchProdutos({
      busca: busca || undefined,
      categoria: categoria || undefined,
      ativo: apenasAtivos ? true : undefined,
      limit: PAGE_SIZE,
      offset,
    })
      .then(setResponse)
      .catch((e: Error) => setError(e.message))
      .finally(() => setLoading(false));
  }, [busca, categoria, apenasAtivos, offset]);

  useEffect(() => {
    load();
  }, [load]);

  function handleBuscaChange(e: React.ChangeEvent<HTMLInputElement>) {
    const v = e.target.value;
    setBuscaInput(v);
    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => {
      setBusca(v);
      setOffset(0);
      pushUrl(v, categoria, apenasAtivos, 0);
    }, DEBOUNCE_MS);
  }

  function handleCategoriaChange(v: string) {
    setCategoria(v);
    setOffset(0);
    pushUrl(busca, v, apenasAtivos, 0);
  }

  function handleAtivoToggle() {
    const novo = !apenasAtivos;
    setApenasAtivos(novo);
    setOffset(0);
    pushUrl(busca, categoria, novo, 0);
  }

  function handleSort(col: SortCol) {
    setSort((s) =>
      s.col === col
        ? { col, dir: s.dir === 'asc' ? 'desc' : 'asc' }
        : { col, dir: 'asc' }
    );
  }

  function handleLimpar() {
    setBusca('');
    setBuscaInput('');
    setCategoria('');
    setApenasAtivos(true);
    setOffset(0);
    setSort(DEFAULT_SORT);
    router.replace('/produtos', { scroll: false });
  }

  // Ordenacao client-side dos resultados carregados
  const itensOrdenados = [...(response?.itens ?? [])].sort((a, b) => {
    const dir = sort.dir === 'asc' ? 1 : -1;
    const va = a[sort.col];
    const vb = b[sort.col];
    if (typeof va === 'string' && typeof vb === 'string') {
      return va.localeCompare(vb, 'pt-BR') * dir;
    }
    if (typeof va === 'number' && typeof vb === 'number') {
      return (va - vb) * dir;
    }
    return 0;
  });

  const totalPages = response ? Math.ceil(response.total / PAGE_SIZE) : 0;
  const currentPage = Math.floor(offset / PAGE_SIZE) + 1;
  const temFiltro = !!(busca || categoria || !apenasAtivos);

  return (
    <div className="space-y-4">
      {/* Cabecalho */}
      <div>
        <h1 className="text-lg sm:text-xl font-bold text-gray-900">Catalogo de Produtos</h1>
        <p className="text-xs text-gray-500 mt-0.5">
          {response
            ? `${response.total.toLocaleString('pt-BR')} produto${response.total !== 1 ? 's' : ''} encontrado${response.total !== 1 ? 's' : ''}`
            : 'Carregando...'}
        </p>
      </div>

      {/* Mais Vendidos */}
      <MaisVendidosSection />

      {/* Erro */}
      {error && (
        <div role="alert" className="flex items-start gap-3 p-4 bg-red-50 border border-red-200 rounded-lg">
          <svg className="w-5 h-5 text-red-500 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
              d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
          </svg>
          <div className="flex-1">
            <p className="text-sm font-semibold text-red-800">Erro ao carregar produtos</p>
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
      <div className="bg-white rounded-xl border border-gray-200 p-3 shadow-sm">
        <div className="flex flex-wrap items-end gap-3">
          {/* Busca */}
          <div className="flex flex-col gap-1 flex-1 min-w-[160px]">
            <label htmlFor="produtos-busca" className="text-[10px] font-semibold text-gray-500 uppercase tracking-wide">
              Busca
            </label>
            <div className="relative">
              <svg
                className="absolute left-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-gray-400 pointer-events-none"
                fill="none" viewBox="0 0 24 24" stroke="currentColor"
              >
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                  d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
              <input
                id="produtos-busca"
                type="text"
                value={buscaInput}
                onChange={handleBuscaChange}
                placeholder="Nome ou codigo..."
                aria-label="Buscar produto por nome ou codigo"
                className={`w-full pl-8 pr-7 py-1.5 text-xs border rounded focus:outline-none focus:ring-2 focus:ring-green-200 focus:border-green-400 ${
                  busca ? 'border-green-400 bg-green-50' : 'border-gray-200 bg-white'
                }`}
              />
              {buscaInput && (
                <button
                  type="button"
                  onClick={() => {
                    setBuscaInput('');
                    setBusca('');
                    setOffset(0);
                    pushUrl('', categoria, apenasAtivos, 0);
                  }}
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

          {/* Categoria */}
          <div className="flex flex-col gap-1 min-w-[140px]">
            <label htmlFor="produtos-categoria" className="text-[10px] font-semibold text-gray-500 uppercase tracking-wide">
              Categoria
            </label>
            <select
              id="produtos-categoria"
              value={categoria}
              onChange={(e) => handleCategoriaChange(e.target.value)}
              aria-label="Filtrar por categoria"
              className={`h-8 px-2.5 text-xs border rounded focus:outline-none focus:ring-2 focus:ring-green-200 focus:border-green-400 bg-white ${
                categoria ? 'border-green-400 bg-green-50 text-green-800' : 'border-gray-200 text-gray-700'
              }`}
            >
              <option value="">Todas</option>
              {categorias.map((c) => (
                <option key={c} value={c}>{c}</option>
              ))}
            </select>
          </div>

          {/* Toggle apenas ativos */}
          <div className="flex flex-col gap-1">
            <span className="text-[10px] font-semibold text-gray-500 uppercase tracking-wide">
              Status
            </span>
            <button
              type="button"
              onClick={handleAtivoToggle}
              aria-pressed={apenasAtivos}
              className={`h-8 px-3 text-xs font-medium rounded border transition-colors ${
                apenasAtivos
                  ? 'border-green-400 bg-green-50 text-green-800'
                  : 'border-gray-200 bg-white text-gray-600 hover:bg-gray-50'
              }`}
            >
              {apenasAtivos ? 'Apenas ativos' : 'Todos'}
            </button>
          </div>

          {/* Limpar */}
          {temFiltro && (
            <button
              type="button"
              onClick={handleLimpar}
              className="self-end text-xs text-gray-500 hover:text-gray-800 underline hover:no-underline pb-0.5"
            >
              Limpar filtros
            </button>
          )}
        </div>
      </div>

      {/* Tabela */}
      <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full" role="table">
            <thead>
              <tr className="border-b border-gray-200 bg-gray-50">
                <ThSort label="Codigo"   col="codigo"       sort={sort} onSort={handleSort} />
                <ThSort label="Nome"     col="nome"         sort={sort} onSort={handleSort} />
                <ThSort label="Categoria" col="categoria"   sort={sort} onSort={handleSort} />
                <th scope="col" className="px-4 py-2.5 text-left text-[10px] font-semibold text-gray-500 uppercase tracking-wide">
                  Unidade
                </th>
                <ThSort label="Preco"    col="preco_tabela" sort={sort} onSort={handleSort} />
                <ThSort label="Comissao" col="comissao_pct" sort={sort} onSort={handleSort} />
                <th scope="col" className="px-4 py-2.5 text-left text-[10px] font-semibold text-gray-500 uppercase tracking-wide">
                  Status
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {loading ? (
                Array.from({ length: 8 }, (_, i) => <SkeletonRow key={i} />)
              ) : itensOrdenados.length === 0 ? (
                <tr>
                  <td colSpan={7} className="px-4 py-12 text-center">
                    <div className="flex flex-col items-center gap-2">
                      <svg className="w-8 h-8 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
                          d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" />
                      </svg>
                      <p className="text-sm text-gray-500">Nenhum produto encontrado</p>
                      {temFiltro && (
                        <button
                          type="button"
                          onClick={handleLimpar}
                          className="text-xs text-green-600 hover:underline"
                        >
                          Limpar filtros
                        </button>
                      )}
                    </div>
                  </td>
                </tr>
              ) : (
                itensOrdenados.map((item) => (
                  <tr
                    key={item.id}
                    className="hover:bg-gray-50 cursor-pointer transition-colors"
                    onClick={() => setSelectedId(item.id)}
                    role="button"
                    aria-label={`Ver detalhe de ${item.nome}`}
                    tabIndex={0}
                    onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') setSelectedId(item.id); }}
                  >
                    <td className="px-4 py-2.5 text-[11px] font-mono text-gray-500">{item.codigo}</td>
                    <td className="px-4 py-2.5 text-xs font-medium text-gray-900 max-w-[200px]">
                      <span className="block truncate">{item.nome}</span>
                    </td>
                    <td className="px-4 py-2.5 text-xs text-gray-600">{item.categoria}</td>
                    <td className="px-4 py-2.5 text-xs text-gray-600">{item.unidade}</td>
                    <td className="px-4 py-2.5 text-xs text-gray-900 tabular-nums font-medium">
                      {formatBRL(item.preco_tabela)}
                    </td>
                    <td className="px-4 py-2.5 text-xs font-semibold tabular-nums" style={{ color: '#00B050' }}>
                      {formatPercent(item.comissao_pct)}
                    </td>
                    <td className="px-4 py-2.5">
                      <BadgeAtivo ativo={item.ativo} />
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* Paginacao */}
        {response && response.total > PAGE_SIZE && (
          <div className="flex items-center justify-between px-4 py-2.5 border-t border-gray-100 bg-gray-50 gap-3">
            <p className="text-xs text-gray-500">
              {offset + 1}–{Math.min(offset + PAGE_SIZE, response.total)} de {response.total.toLocaleString('pt-BR')} — Pag. {currentPage}/{totalPages}
            </p>
            <div className="flex gap-2">
              <button
                type="button"
                disabled={offset === 0}
                onClick={() => {
                  const novo = Math.max(0, offset - PAGE_SIZE);
                  setOffset(novo);
                  pushUrl(busca, categoria, apenasAtivos, novo);
                }}
                className={`px-3 py-1.5 rounded text-xs font-medium border transition-colors ${
                  offset === 0
                    ? 'border-gray-200 text-gray-300 cursor-not-allowed'
                    : 'border-gray-300 text-gray-600 hover:bg-gray-50'
                }`}
              >
                Anterior
              </button>
              <button
                type="button"
                disabled={offset + PAGE_SIZE >= response.total}
                onClick={() => {
                  const novo = offset + PAGE_SIZE;
                  setOffset(novo);
                  pushUrl(busca, categoria, apenasAtivos, novo);
                }}
                className={`px-3 py-1.5 rounded text-xs font-medium border transition-colors ${
                  offset + PAGE_SIZE >= response.total
                    ? 'border-gray-200 text-gray-300 cursor-not-allowed'
                    : 'border-gray-300 text-gray-600 hover:bg-gray-50'
                }`}
              >
                Proxima
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Modal detalhe */}
      {selectedId !== null && (
        <ModalProduto
          produtoId={selectedId}
          onClose={() => setSelectedId(null)}
        />
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Export com Suspense obrigatorio para useSearchParams no Next.js 14
// ---------------------------------------------------------------------------

export default function ProdutosPage() {
  return (
    <Suspense
      fallback={
        <div className="space-y-4">
          <div className="h-8 bg-gray-100 animate-pulse rounded w-56" />
          <div className="h-24 bg-gray-100 animate-pulse rounded" />
          <div className="h-96 bg-gray-100 animate-pulse rounded" />
        </div>
      }
    >
      <ProdutosInner />
    </Suspense>
  );
}
