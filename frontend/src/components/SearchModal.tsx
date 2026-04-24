'use client';

import { useEffect, useMemo, useRef, useState } from 'react';
import { useRouter } from 'next/navigation';
import { fetchClientes, fetchProdutos, fetchVendasPorStatus, ClienteRegistro, ProdutoItem, VendaPedidoItem, formatBRL } from '@/lib/api';

// ---------------------------------------------------------------------------
// SearchModal — busca global Ctrl+K / Cmd+K
// Busca paralela em clientes, produtos e pedidos (quando query parece numero)
// ---------------------------------------------------------------------------

interface SearchResult {
  type: 'cliente' | 'produto' | 'pedido';
  id: string;
  title: string;
  subtitle: string;
  href: string;
}

function debounce<T extends (...args: Parameters<T>) => void>(
  fn: T,
  delay: number
): (...args: Parameters<T>) => void {
  let timer: ReturnType<typeof setTimeout>;
  return (...args: Parameters<T>) => {
    clearTimeout(timer);
    timer = setTimeout(() => fn(...args), delay);
  };
}

// ---------------------------------------------------------------------------
// Result item icon by type
// ---------------------------------------------------------------------------

function ResultIcon({ type }: { type: SearchResult['type'] }) {
  if (type === 'cliente') {
    return (
      <div className="flex-shrink-0 w-8 h-8 rounded-full bg-blue-100 flex items-center justify-center">
        <svg className="w-4 h-4 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
            d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-2 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
        </svg>
      </div>
    );
  }
  if (type === 'produto') {
    return (
      <div className="flex-shrink-0 w-8 h-8 rounded-full bg-green-100 flex items-center justify-center">
        <svg className="w-4 h-4 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
            d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10" />
        </svg>
      </div>
    );
  }
  return (
    <div className="flex-shrink-0 w-8 h-8 rounded-full bg-purple-100 flex items-center justify-center">
      <svg className="w-4 h-4 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
          d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
      </svg>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Group label
// ---------------------------------------------------------------------------

const GROUP_LABELS: Record<SearchResult['type'], string> = {
  cliente: 'Clientes',
  produto: 'Produtos',
  pedido: 'Pedidos',
};

// ---------------------------------------------------------------------------
// SearchModal component
// ---------------------------------------------------------------------------

interface SearchModalProps {
  open: boolean;
  onClose: () => void;
}

export default function SearchModal({ open, onClose }: SearchModalProps) {
  const router = useRouter();
  const inputRef = useRef<HTMLInputElement>(null);
  const listRef = useRef<HTMLDivElement>(null);

  const [query, setQuery] = useState('');
  const [results, setResults] = useState<SearchResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [activeIndex, setActiveIndex] = useState(0);

  // Reset state when modal opens/closes
  useEffect(() => {
    if (open) {
      setQuery('');
      setResults([]);
      setActiveIndex(0);
      // Autofocus after paint
      requestAnimationFrame(() => {
        inputRef.current?.focus();
      });
    }
  }, [open]);

  // Close on Escape — handled separately so the pipeline page Escape doesn't conflict
  useEffect(() => {
    if (!open) return;
    function onKey(e: KeyboardEvent) {
      if (e.key === 'Escape') {
        e.stopPropagation();
        onClose();
      }
    }
    window.addEventListener('keydown', onKey, true);
    return () => window.removeEventListener('keydown', onKey, true);
  }, [open, onClose]);

  // ---------------------------------------------------------------------------
  // Search — debounced, parallel fetch
  // ---------------------------------------------------------------------------

  // eslint-disable-next-line react-hooks/exhaustive-deps
  const buscar = useMemo(
    () =>
      debounce(async (q: string) => {
        if (q.trim().length < 2) {
          setResults([]);
          setLoading(false);
          return;
        }

        setLoading(true);

        const pareceNumero = /\d{4,}/.test(q);

        const promises: Promise<SearchResult[]>[] = [
          // Clientes
          fetchClientes({ busca: q, limit: 5 })
            .then((res): SearchResult[] =>
              res.registros.map((c: ClienteRegistro) => ({
                type: 'cliente',
                id: c.cnpj,
                title: c.nome_fantasia,
                subtitle: `${c.consultor ?? '—'} · ${c.situacao ?? '—'} · CNPJ ${c.cnpj.slice(-4)}`,
                href: `/carteira?cnpj=${c.cnpj}`,
              }))
            )
            .catch(() => []),

          // Produtos
          fetchProdutos({ busca: q, limit: 3 })
            .then((res): SearchResult[] =>
              res.itens.map((p: ProdutoItem) => ({
                type: 'produto',
                id: String(p.id),
                title: p.nome,
                subtitle: `${p.categoria ?? '—'} · ${p.codigo} · ${formatBRL(p.preco_tabela)}`,
                href: `/produtos?id=${p.id}`,
              }))
            )
            .catch(() => []),
        ];

        // Busca por pedido se query parece ser numero de pedido
        if (pareceNumero) {
          promises.push(
            fetchVendasPorStatus({ busca: q, limit: 3 })
              .then((res): SearchResult[] =>
                (res?.items ?? []).map((v: VendaPedidoItem) => ({
                  type: 'pedido',
                  id: String(v.id),
                  title: `Pedido ${v.numero_pedido ?? v.id}`,
                  subtitle: `${v.nome_fantasia ?? v.cnpj} · ${formatBRL(v.valor_pedido)} · ${v.status_pedido}`,
                  href: `/pedidos?numero=${v.numero_pedido ?? v.id}`,
                }))
              )
              .catch(() => [])
          );
        }

        const all = await Promise.all(promises);
        const flat = all.flat();

        setResults(flat);
        setActiveIndex(0);
        setLoading(false);
      }, 300),
    []
  );

  useEffect(() => {
    if (query.length >= 2) {
      setLoading(true);
      buscar(query);
    } else {
      setResults([]);
      setLoading(false);
    }
  }, [query, buscar]);

  // ---------------------------------------------------------------------------
  // Keyboard navigation in results
  // ---------------------------------------------------------------------------

  function handleKeyDown(e: React.KeyboardEvent<HTMLInputElement>) {
    if (e.key === 'ArrowDown') {
      e.preventDefault();
      setActiveIndex((i) => Math.min(i + 1, results.length - 1));
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      setActiveIndex((i) => Math.max(i - 1, 0));
    } else if (e.key === 'Enter' && results[activeIndex]) {
      e.preventDefault();
      navigate(results[activeIndex]);
    }
  }

  function navigate(result: SearchResult) {
    router.push(result.href);
    onClose();
  }

  // Auto-scroll active item into view
  useEffect(() => {
    const activeEl = listRef.current?.querySelector(`[data-idx="${activeIndex}"]`);
    activeEl?.scrollIntoView({ block: 'nearest' });
  }, [activeIndex]);

  if (!open) return null;

  // Group results by type
  const groups: SearchResult['type'][] = ['cliente', 'produto', 'pedido'];
  const grouped = groups
    .map((type) => ({
      type,
      items: results.filter((r) => r.type === type),
    }))
    .filter((g) => g.items.length > 0);

  // Build flat index map for keyboard navigation
  const flatResults = grouped.flatMap((g) => g.items);

  return (
    <>
      {/* Overlay */}
      <div
        className="fixed inset-0 bg-black/40 z-[60] backdrop-blur-sm"
        onClick={onClose}
        aria-hidden="true"
      />

      {/* Modal */}
      <div
        className="fixed top-[10vh] left-1/2 -translate-x-1/2 w-full max-w-xl z-[70] flex flex-col"
        role="dialog"
        aria-label="Busca global"
        aria-modal="true"
      >
        <div className="bg-white rounded-xl shadow-2xl border border-gray-200 overflow-hidden flex flex-col max-h-[70vh]">
          {/* Search input */}
          <div className="flex items-center gap-3 px-4 py-3 border-b border-gray-100">
            {loading ? (
              <div className="w-4 h-4 border-2 border-green-500 border-t-transparent rounded-full animate-spin flex-shrink-0" />
            ) : (
              <svg className="w-4 h-4 text-gray-400 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                  d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
            )}
            <input
              ref={inputRef}
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Buscar cliente, pedido ou produto..."
              className="flex-1 text-sm text-gray-900 placeholder-gray-400 bg-transparent outline-none"
              autoComplete="off"
              spellCheck={false}
            />
            {query && (
              <button
                type="button"
                onClick={() => setQuery('')}
                className="flex-shrink-0 text-gray-400 hover:text-gray-600 transition-colors"
                aria-label="Limpar busca"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            )}
            <kbd className="flex-shrink-0 hidden sm:inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[10px] font-mono bg-gray-100 text-gray-500 border border-gray-200">
              Esc
            </kbd>
          </div>

          {/* Results */}
          <div ref={listRef} className="overflow-y-auto flex-1 py-1">
            {query.length < 2 && (
              <div className="flex flex-col items-center justify-center py-10 text-gray-400">
                <svg className="w-8 h-8 mb-2 opacity-40" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
                    d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                </svg>
                <p className="text-sm">Digite pelo menos 2 caracteres</p>
              </div>
            )}

            {query.length >= 2 && !loading && results.length === 0 && (
              <div className="flex flex-col items-center justify-center py-10 text-gray-400">
                <svg className="w-8 h-8 mb-2 opacity-40" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
                    d="M9.172 16.172a4 4 0 015.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <p className="text-sm">Nenhum resultado para <strong className="text-gray-600">&ldquo;{query}&rdquo;</strong></p>
              </div>
            )}

            {grouped.map(({ type, items }) => (
              <div key={type}>
                {/* Group header */}
                <div className="px-4 py-1.5 flex items-center gap-2">
                  <span className="text-[10px] font-bold uppercase tracking-wider text-gray-400">
                    {GROUP_LABELS[type]}
                  </span>
                  <span className="text-[10px] text-gray-300">{items.length}</span>
                </div>

                {/* Items */}
                {items.map((result) => {
                  const flatIdx = flatResults.findIndex((r) => r.id === result.id && r.type === result.type);
                  const isActive = flatIdx === activeIndex;

                  return (
                    <button
                      key={`${result.type}-${result.id}`}
                      type="button"
                      data-idx={flatIdx}
                      onClick={() => navigate(result)}
                      onMouseEnter={() => setActiveIndex(flatIdx)}
                      className={`w-full flex items-center gap-3 px-4 py-2.5 text-left transition-colors ${
                        isActive ? 'bg-gray-50' : 'hover:bg-gray-50'
                      }`}
                    >
                      <ResultIcon type={result.type} />
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium text-gray-900 truncate">{result.title}</p>
                        <p className="text-xs text-gray-500 truncate">{result.subtitle}</p>
                      </div>
                      {isActive && (
                        <svg className="w-4 h-4 text-gray-300 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                        </svg>
                      )}
                    </button>
                  );
                })}
              </div>
            ))}
          </div>

          {/* Footer hints */}
          {results.length > 0 && (
            <div className="flex-shrink-0 flex items-center gap-4 px-4 py-2 border-t border-gray-100 bg-gray-50">
              <span className="flex items-center gap-1 text-[10px] text-gray-400">
                <kbd className="px-1 py-0.5 rounded bg-white border border-gray-200 font-mono text-[9px]">Enter</kbd>
                Abrir
              </span>
              <span className="flex items-center gap-1 text-[10px] text-gray-400">
                <kbd className="px-1 py-0.5 rounded bg-white border border-gray-200 font-mono text-[9px]">↑↓</kbd>
                Navegar
              </span>
              <span className="flex items-center gap-1 text-[10px] text-gray-400">
                <kbd className="px-1 py-0.5 rounded bg-white border border-gray-200 font-mono text-[9px]">Esc</kbd>
                Fechar
              </span>
            </div>
          )}
        </div>
      </div>
    </>
  );
}
