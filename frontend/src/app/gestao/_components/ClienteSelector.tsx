'use client';

// ClienteSelector — autocomplete de CNPJ/razão social filtrado por canal elegível DDE
// Canais elegíveis: DIRETO, INDIRETO, FOOD SERVICE
// Onclick → navega para /gestao/dde/[cnpj]

import { useState, useCallback, useRef } from 'react';
import { useRouter } from 'next/navigation';
import { fetchClientes } from '@/lib/api';
import type { ClienteRegistro } from '@/lib/api';

// IDs dos canais elegíveis ao DDE (DIRETO=1, INDIRETO=2, FOOD SERVICE=3 — ajustar se necessário)
// O filtro real é por nome do canal no registro do cliente
const CANAIS_ELEGIVEIS_NOMES = ['DIRETO', 'INDIRETO', 'FOOD SERVICE', 'FOOD_SERVICE'];

interface ClienteSelectorProps {
  /** Rota de destino ao selecionar cliente. Usa /gestao/dde/[cnpj] por padrão. */
  destinoBase?: string;
  placeholder?: string;
  onSelect?: (cnpj: string) => void;
}

function isElegivel(cliente: ClienteRegistro): boolean {
  // Verifica elegibilidade pelo campo canal (se existir) ou aceita todos se não houver info
  const canal = (cliente as Record<string, unknown>)['canal'] as string | undefined;
  if (!canal) return true; // sem info de canal → inclui (melhor UX)
  return CANAIS_ELEGIVEIS_NOMES.some((c) => canal.toUpperCase().includes(c));
}

export function ClienteSelector({
  destinoBase = '/gestao/dde',
  placeholder = 'Buscar por CNPJ ou razão social…',
  onSelect,
}: ClienteSelectorProps) {
  const router = useRouter();
  const [query, setQuery] = useState('');
  const [resultados, setResultados] = useState<ClienteRegistro[]>([]);
  const [loading, setLoading] = useState(false);
  const [open, setOpen] = useState(false);
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const buscar = useCallback(async (q: string) => {
    if (q.trim().length < 2) {
      setResultados([]);
      setOpen(false);
      return;
    }
    setLoading(true);
    try {
      const res = await fetchClientes({ busca: q, limit: 10 });
      const filtrados = (res.registros ?? []).filter(isElegivel);
      setResultados(filtrados);
      setOpen(filtrados.length > 0);
    } catch {
      setResultados([]);
      setOpen(false);
    } finally {
      setLoading(false);
    }
  }, []);

  function handleChange(e: React.ChangeEvent<HTMLInputElement>) {
    const val = e.target.value;
    setQuery(val);
    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => buscar(val), 300);
  }

  function handleSelect(cliente: ClienteRegistro) {
    setOpen(false);
    setQuery(cliente.nome_fantasia ?? cliente.cnpj);
    if (onSelect) {
      onSelect(cliente.cnpj);
    } else {
      router.push(`${destinoBase}/${cliente.cnpj}`);
    }
  }

  function handleKeyDown(e: React.KeyboardEvent<HTMLInputElement>) {
    if (e.key === 'Escape') {
      setOpen(false);
    }
  }

  return (
    <div className="relative w-full max-w-lg" role="combobox" aria-expanded={open} aria-haspopup="listbox">
      <div className="relative">
        <input
          ref={inputRef}
          type="search"
          value={query}
          onChange={handleChange}
          onKeyDown={handleKeyDown}
          onFocus={() => resultados.length > 0 && setOpen(true)}
          onBlur={() => setTimeout(() => setOpen(false), 200)}
          placeholder={placeholder}
          className="w-full pl-10 pr-4 py-2.5 border border-gray-300 rounded-lg text-sm text-gray-800 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-green-500 bg-white"
          aria-label="Buscar cliente por CNPJ ou razão social"
          aria-autocomplete="list"
          aria-controls="cliente-selector-lista"
          autoComplete="off"
        />
        <span className="absolute left-3 top-1/2 -translate-y-1/2 pointer-events-none" aria-hidden="true">
          {loading ? (
            <svg className="w-4 h-4 text-gray-400 animate-spin" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
            </svg>
          ) : (
            <svg className="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
          )}
        </span>
      </div>

      {open && resultados.length > 0 && (
        <ul
          id="cliente-selector-lista"
          role="listbox"
          aria-label="Clientes encontrados"
          className="absolute z-20 left-0 right-0 mt-1 bg-white border border-gray-200 rounded-lg shadow-lg max-h-64 overflow-y-auto"
        >
          {resultados.map((cliente) => (
            <li
              key={cliente.cnpj}
              role="option"
              aria-selected={false}
              className="flex flex-col px-3 py-2.5 hover:bg-green-50 cursor-pointer border-b border-gray-50 last:border-0 min-h-[44px] justify-center"
              onMouseDown={() => handleSelect(cliente)}
            >
              <span className="text-sm font-semibold text-gray-800 truncate">
                {cliente.nome_fantasia ?? cliente.razao_social ?? '—'}
              </span>
              <span className="text-xs text-gray-500 font-mono">
                {cliente.cnpj} {cliente.consultor ? `· ${cliente.consultor}` : ''}
              </span>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
