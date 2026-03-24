'use client';

import { useCallback, useEffect, useState } from 'react';
import {
  fetchClientes,
  ClienteRegistro,
  ClientesResponse,
} from '@/lib/api';
import ClienteTable from '@/components/ClienteTable';
import ClienteModal from '@/components/ClienteModal';

// ---------------------------------------------------------------------------
// Carteira page — full client list with filters and pagination
// ---------------------------------------------------------------------------

const CONSULTORES = ['', 'LARISSA', 'MANU', 'JULIO', 'DAIANE'];
const SITUACOES = ['', 'ATIVO', 'INAT.REC', 'INAT.ANT', 'PROSPECT'];
const SINALEIROS = ['', 'VERDE', 'AMARELO', 'VERMELHO', 'ROXO'];
const PAGE_SIZE = 50;

export default function CarteiraPage() {
  const [response, setResponse] = useState<ClientesResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Filters
  const [consultor, setConsultor] = useState('');
  const [situacao, setSituacao] = useState('');
  const [sinaleiro, setSinaleiro] = useState('');
  const [offset, setOffset] = useState(0);

  // Detail modal
  const [selectedCnpj, setSelectedCnpj] = useState<string | null>(null);

  const load = useCallback(() => {
    setLoading(true);
    fetchClientes({ consultor, situacao, sinaleiro, limit: PAGE_SIZE, offset })
      .then(setResponse)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [consultor, situacao, sinaleiro, offset]);

  useEffect(() => {
    load();
  }, [load]);

  // Reset to page 0 when filters change
  const handleFilter = (setter: (v: string) => void) => (e: React.ChangeEvent<HTMLSelectElement>) => {
    setter(e.target.value);
    setOffset(0);
  };

  const totalPages = response ? Math.ceil(response.total / PAGE_SIZE) : 0;
  const currentPage = Math.floor(offset / PAGE_SIZE) + 1;

  return (
    <div className="space-y-4">
      {/* Page heading */}
      <div>
        <h1 className="text-xl font-bold text-gray-900">Carteira de Clientes</h1>
        <p className="text-sm text-gray-500 mt-0.5">
          {response
            ? `${response.total.toLocaleString('pt-BR')} clientes encontrados`
            : 'Carregando...'}
        </p>
      </div>

      {error && (
        <div className="p-4 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700">
          Erro ao carregar clientes: {error}
          <button
            type="button"
            onClick={load}
            className="ml-3 underline hover:no-underline"
          >
            Tentar novamente
          </button>
        </div>
      )}

      {/* Filters */}
      <div className="bg-white rounded-lg border border-gray-200 p-4 shadow-sm">
        <div className="flex flex-wrap gap-3 items-end">
          <FilterSelect
            label="Consultor"
            value={consultor}
            onChange={handleFilter(setConsultor)}
            options={CONSULTORES}
          />
          <FilterSelect
            label="Situacao"
            value={situacao}
            onChange={handleFilter(setSituacao)}
            options={SITUACOES}
          />
          <FilterSelect
            label="Sinaleiro"
            value={sinaleiro}
            onChange={handleFilter(setSinaleiro)}
            options={SINALEIROS}
          />
          {(consultor || situacao || sinaleiro) && (
            <button
              type="button"
              onClick={() => {
                setConsultor('');
                setSituacao('');
                setSinaleiro('');
                setOffset(0);
              }}
              className="text-sm text-red-600 hover:text-red-700 underline hover:no-underline self-end pb-0.5"
            >
              Limpar filtros
            </button>
          )}
        </div>
      </div>

      {/* Table */}
      <div className="bg-white rounded-lg border border-gray-200 shadow-sm overflow-hidden">
        <ClienteTable
          registros={response?.registros ?? []}
          loading={loading}
          onRowClick={(c: ClienteRegistro) => setSelectedCnpj(c.cnpj)}
        />

        {/* Pagination */}
        {response && response.total > PAGE_SIZE && (
          <div className="flex items-center justify-between px-4 py-3 border-t border-gray-100 bg-gray-50">
            <p className="text-xs text-gray-500">
              Pagina {currentPage} de {totalPages} —{' '}
              {response.total.toLocaleString('pt-BR')} registros
            </p>
            <div className="flex gap-2">
              <PaginationButton
                label="Anterior"
                disabled={offset === 0}
                onClick={() => setOffset(Math.max(0, offset - PAGE_SIZE))}
              />
              <PaginationButton
                label="Proximo"
                disabled={offset + PAGE_SIZE >= response.total}
                onClick={() => setOffset(offset + PAGE_SIZE)}
              />
            </div>
          </div>
        )}
      </div>

      {/* Client detail modal */}
      <ClienteModal
        cnpj={selectedCnpj}
        onClose={() => setSelectedCnpj(null)}
      />
    </div>
  );
}

// ---------------------------------------------------------------------------
// Sub-components
// ---------------------------------------------------------------------------

interface FilterSelectProps {
  label: string;
  value: string;
  onChange: (e: React.ChangeEvent<HTMLSelectElement>) => void;
  options: string[];
}

function FilterSelect({ label, value, onChange, options }: FilterSelectProps) {
  const id = `filter-${label.toLowerCase()}`;
  return (
    <div className="flex flex-col gap-1 min-w-[140px]">
      <label htmlFor={id} className="text-xs font-medium text-gray-500 uppercase tracking-wide">
        {label}
      </label>
      <select
        id={id}
        value={value}
        onChange={onChange}
        className="border border-gray-200 rounded px-2.5 py-1.5 text-sm text-gray-700 bg-white focus:outline-none focus:ring-2 focus:ring-green-200 focus:border-green-400"
      >
        {options.map((opt) => (
          <option key={opt} value={opt}>
            {opt === '' ? 'Todos' : opt}
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
      className={`px-3 py-1.5 rounded text-xs font-medium border transition-colors ${
        disabled
          ? 'border-gray-200 text-gray-300 cursor-not-allowed'
          : 'border-gray-300 text-gray-600 hover:bg-gray-50 hover:border-gray-400'
      }`}
    >
      {label}
    </button>
  );
}
