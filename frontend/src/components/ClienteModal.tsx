'use client';

import { useEffect, useState } from 'react';
import { ClienteRegistro, fetchCliente, formatBRL } from '@/lib/api';
import StatusBadge from './StatusBadge';

// ---------------------------------------------------------------------------
// ClienteModal — slide-in panel showing full client detail
// ---------------------------------------------------------------------------

interface ClienteModalProps {
  cnpj: string | null;
  onClose: () => void;
}

function formatCnpj(cnpj: string): string {
  const d = cnpj.replace(/\D/g, '').padStart(14, '0');
  if (d.length !== 14) return cnpj;
  return `${d.slice(0, 2)}.${d.slice(2, 5)}.${d.slice(5, 8)}/${d.slice(8, 12)}-${d.slice(12)}`;
}

interface FieldRowProps {
  label: string;
  value?: unknown;
  money?: boolean;
}

function FieldRow({ label, value, money }: FieldRowProps) {
  if (value == null || value === '') return null;
  const display = money && typeof value === 'number' ? formatBRL(value) : String(value);
  return (
    <div className="flex justify-between gap-4 py-1.5 border-b border-gray-50 text-sm">
      <span className="text-gray-500 flex-shrink-0">{label}</span>
      <span className="text-gray-900 text-right font-medium">{display}</span>
    </div>
  );
}

export default function ClienteModal({ cnpj, onClose }: ClienteModalProps) {
  const [cliente, setCliente] = useState<ClienteRegistro | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!cnpj) {
      setCliente(null);
      return;
    }

    setLoading(true);
    setError(null);

    fetchCliente(cnpj)
      .then(setCliente)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [cnpj]);

  if (!cnpj) return null;

  return (
    <>
      {/* Overlay */}
      <div
        className="fixed inset-0 bg-black/30 z-40"
        onClick={onClose}
        aria-hidden="true"
      />

      {/* Panel */}
      <aside className="fixed top-0 right-0 h-full w-full max-w-md bg-white z-50 shadow-xl flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between px-5 py-4 border-b border-gray-200">
          <div>
            <p className="font-semibold text-gray-900 text-base">
              {loading ? 'Carregando...' : (cliente?.nome_fantasia ?? cnpj)}
            </p>
            <p className="text-xs text-gray-400 font-mono">{formatCnpj(cnpj)}</p>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="p-2 rounded hover:bg-gray-100 text-gray-500"
            aria-label="Fechar"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Body */}
        <div className="flex-1 overflow-y-auto scrollbar-thin px-5 py-4">
          {loading && (
            <div className="space-y-3">
              {Array.from({ length: 12 }).map((_, i) => (
                <div key={i} className="h-4 bg-gray-100 animate-pulse rounded" style={{ width: `${50 + i * 3}%` }} />
              ))}
            </div>
          )}

          {error && (
            <div className="p-4 bg-red-50 border border-red-200 rounded text-sm text-red-700">
              Erro ao carregar cliente: {error}
            </div>
          )}

          {cliente && !loading && (
            <div className="space-y-4">
              {/* Status badges row */}
              <div className="flex flex-wrap gap-2 pb-3 border-b border-gray-100">
                <StatusBadge value={cliente.situacao} variant="situacao" />
                <StatusBadge value={cliente.sinaleiro} variant="sinaleiro" />
                {cliente.prioridade && <StatusBadge value={cliente.prioridade} variant="prioridade" />}
                {cliente.curva_abc && <StatusBadge value={cliente.curva_abc} variant="abc" />}
              </div>

              {/* Identification */}
              <section>
                <h3 className="text-[11px] font-semibold text-gray-400 uppercase tracking-wider mb-2">
                  Identificacao
                </h3>
                <FieldRow label="Razao Social" value={cliente.razao_social} />
                <FieldRow label="Nome Fantasia" value={cliente.nome_fantasia} />
                <FieldRow label="CNPJ" value={formatCnpj(cliente.cnpj)} />
                <FieldRow label="Cidade/UF" value={cliente.cidade && cliente.uf ? `${cliente.cidade}/${cliente.uf}` : (cliente.uf ?? undefined)} />
                <FieldRow label="Segmento" value={cliente.segmento} />
              </section>

              {/* Commercial */}
              <section>
                <h3 className="text-[11px] font-semibold text-gray-400 uppercase tracking-wider mb-2">
                  Comercial
                </h3>
                <FieldRow label="Consultor" value={cliente.consultor} />
                <FieldRow label="Faturamento Total" value={cliente.faturamento_total} money />
                <FieldRow label="Ticket Medio" value={cliente.ticket_medio} money />
                <FieldRow label="Meta Mensal" value={cliente.meta_mensal} money />
                <FieldRow label="Score" value={cliente.score != null ? cliente.score.toFixed(2) : undefined} />
                <FieldRow label="Ultima Compra" value={cliente.ultima_compra} />
                <FieldRow label="Dias Sem Compra" value={cliente.dias_sem_compra} />
              </section>

              {/* Extra fields from API */}
              {Object.entries(cliente)
                .filter(([k]) =>
                  ![
                    'cnpj', 'nome_fantasia', 'razao_social', 'consultor',
                    'situacao', 'sinaleiro', 'prioridade', 'curva_abc',
                    'score', 'faturamento_total', 'ticket_medio', 'meta_mensal',
                    'cidade', 'uf', 'segmento', 'ultima_compra', 'dias_sem_compra',
                  ].includes(k)
                )
                .filter(([, v]) => v != null && v !== '' && typeof v !== 'object')
                .length > 0 && (
                  <section>
                    <h3 className="text-[11px] font-semibold text-gray-400 uppercase tracking-wider mb-2">
                      Dados Adicionais
                    </h3>
                    {Object.entries(cliente)
                      .filter(([k]) =>
                        ![
                          'cnpj', 'nome_fantasia', 'razao_social', 'consultor',
                          'situacao', 'sinaleiro', 'prioridade', 'curva_abc',
                          'score', 'faturamento_total', 'ticket_medio', 'meta_mensal',
                          'cidade', 'uf', 'segmento', 'ultima_compra', 'dias_sem_compra',
                        ].includes(k)
                      )
                      .filter(([, v]) => v != null && v !== '' && typeof v !== 'object')
                      .map(([k, v]) => (
                        <FieldRow
                          key={k}
                          label={k.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase())}
                          value={v as string | number}
                        />
                      ))}
                  </section>
                )}
            </div>
          )}
        </div>
      </aside>
    </>
  );
}
