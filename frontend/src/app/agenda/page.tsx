'use client';

import { useEffect, useState } from 'react';
import { fetchAgenda, AgendaItem } from '@/lib/api';
import StatusBadge from '@/components/StatusBadge';

// ---------------------------------------------------------------------------
// Agenda page — daily call agenda per consultant (4 tabs)
// ---------------------------------------------------------------------------

const CONSULTORES = ['LARISSA', 'MANU', 'JULIO', 'DAIANE'] as const;
type Consultor = (typeof CONSULTORES)[number];

const prioridadeRowColor: Record<string, string> = {
  P0: 'bg-red-50 border-l-4 border-red-400',
  P1: 'bg-orange-50 border-l-4 border-orange-300',
  P2: 'bg-yellow-50 border-l-4 border-yellow-300',
  P3: 'bg-yellow-50/40',
  P4: '',
  P5: '',
};

export default function AgendaPage() {
  const [activeTab, setActiveTab] = useState<Consultor>('LARISSA');
  const [agendaByConsultor, setAgendaByConsultor] = useState<
    Partial<Record<Consultor, AgendaItem[]>>
  >({});
  const [loadingTabs, setLoadingTabs] = useState<Partial<Record<Consultor, boolean>>>({});
  const [errorTabs, setErrorTabs] = useState<Partial<Record<Consultor, string>>>({});

  // Load agenda for a consultant (lazy — only when tab is first opened)
  const loadConsultor = (consultor: Consultor) => {
    if (agendaByConsultor[consultor] !== undefined) return; // already loaded
    if (loadingTabs[consultor]) return; // in flight

    setLoadingTabs((prev) => ({ ...prev, [consultor]: true }));
    fetchAgenda(consultor)
      .then((data) =>
        setAgendaByConsultor((prev) => ({ ...prev, [consultor]: data }))
      )
      .catch((e) =>
        setErrorTabs((prev) => ({ ...prev, [consultor]: e.message }))
      )
      .finally(() =>
        setLoadingTabs((prev) => ({ ...prev, [consultor]: false }))
      );
  };

  // Load the first tab on mount
  useEffect(() => {
    loadConsultor('LARISSA');
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const handleTabChange = (consultor: Consultor) => {
    setActiveTab(consultor);
    loadConsultor(consultor);
  };

  const items = agendaByConsultor[activeTab] ?? [];
  const isLoading = loadingTabs[activeTab] ?? false;
  const errorMsg = errorTabs[activeTab];

  return (
    <div className="space-y-4">
      {/* Page heading */}
      <div>
        <h1 className="text-xl font-bold text-gray-900">Agenda Diaria</h1>
        <p className="text-sm text-gray-500 mt-0.5">
          Fila de atendimento prioritario por consultor
        </p>
      </div>

      {/* Tabs */}
      <div className="bg-white rounded-lg border border-gray-200 shadow-sm overflow-hidden">
        {/* Tab bar */}
        <div className="flex border-b border-gray-200 overflow-x-auto">
          {CONSULTORES.map((c) => (
            <button
              key={c}
              type="button"
              onClick={() => handleTabChange(c)}
              className={`
                flex-shrink-0 px-5 py-3 text-sm font-medium border-b-2 transition-colors
                ${
                  activeTab === c
                    ? 'border-green-500 text-green-700 bg-green-50/50'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:bg-gray-50'
                }
              `}
            >
              {c}
              {agendaByConsultor[c] !== undefined && (
                <span className="ml-2 text-xs text-gray-400">
                  ({agendaByConsultor[c]!.length})
                </span>
              )}
            </button>
          ))}
        </div>

        {/* Tab content */}
        <div>
          {errorMsg && (
            <div className="p-4 text-sm text-red-700 bg-red-50 border-b border-red-200">
              Erro ao carregar agenda de {activeTab}: {errorMsg}
            </div>
          )}

          {isLoading ? (
            <AgendaSkeleton />
          ) : items.length === 0 && !errorMsg ? (
            <div className="py-16 text-center text-gray-400 text-sm">
              Nenhum item na agenda de {activeTab}
            </div>
          ) : (
            <div className="overflow-x-auto scrollbar-thin">
              <table className="w-full text-sm">
                <thead>
                  <tr className="bg-gray-50 text-left">
                    {['Pos', 'Cliente', 'Score', 'Prioridade', 'Acao Recomendada'].map((h) => (
                      <th
                        key={h}
                        className="px-4 py-2.5 text-[11px] font-semibold text-gray-500 uppercase tracking-wide whitespace-nowrap"
                      >
                        {h}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {items.map((item) => (
                    <tr
                      key={item.cnpj}
                      className={`border-t border-gray-50 ${
                        prioridadeRowColor[item.prioridade?.toUpperCase()] ?? ''
                      }`}
                    >
                      {/* Posicao */}
                      <td className="px-4 py-3 w-12">
                        <span className="inline-flex items-center justify-center w-7 h-7 rounded-full bg-gray-100 text-gray-600 text-xs font-bold">
                          {item.posicao}
                        </span>
                      </td>

                      {/* Cliente */}
                      <td className="px-4 py-3">
                        <p className="font-medium text-gray-900">{item.nome_fantasia}</p>
                        <p className="text-[11px] text-gray-400 font-mono">{formatCnpj(item.cnpj)}</p>
                      </td>

                      {/* Score */}
                      <td className="px-4 py-3 whitespace-nowrap">
                        <ScoreBar score={item.score} />
                      </td>

                      {/* Prioridade */}
                      <td className="px-4 py-3 whitespace-nowrap">
                        <StatusBadge value={item.prioridade} variant="prioridade" />
                      </td>

                      {/* Acao */}
                      <td className="px-4 py-3 text-gray-700 max-w-xs">
                        {item.acao ?? '—'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>

      {/* Legend */}
      <div className="bg-white rounded-lg border border-gray-200 p-4 shadow-sm">
        <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-3">
          Legenda de Prioridade
        </h3>
        <div className="flex flex-wrap gap-3">
          {[
            { code: 'P0', label: 'Critico — contato hoje', bg: '#FF0000', text: '#fff' },
            { code: 'P1', label: 'Alto — contato urgente', bg: '#FF6600', text: '#fff' },
            { code: 'P2', label: 'Medio — contato esta semana', bg: '#FFC000', text: '#1a1a1a' },
            { code: 'P3', label: 'Normal — contato planejado', bg: '#FFFF00', text: '#1a1a1a' },
            { code: 'P4', label: 'Baixo', bg: '#9ca3af', text: '#fff' },
          ].map((p) => (
            <div key={p.code} className="flex items-center gap-2">
              <span
                className="inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold"
                style={{ backgroundColor: p.bg, color: p.text }}
              >
                {p.code}
              </span>
              <span className="text-xs text-gray-500">{p.label}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Sub-components
// ---------------------------------------------------------------------------

function ScoreBar({ score }: { score: number }) {
  const clamped = Math.min(100, Math.max(0, score));
  const color =
    clamped >= 70 ? '#00B050' : clamped >= 40 ? '#FFC000' : '#FF0000';

  return (
    <div className="flex items-center gap-2">
      <div className="w-20 bg-gray-100 rounded-full h-2 overflow-hidden">
        <div
          className="h-full rounded-full"
          style={{ width: `${clamped}%`, backgroundColor: color }}
        />
      </div>
      <span className="text-xs text-gray-600 w-8">{score.toFixed(0)}</span>
    </div>
  );
}

function AgendaSkeleton() {
  return (
    <div className="p-4 space-y-3">
      {Array.from({ length: 8 }).map((_, i) => (
        <div key={i} className="flex gap-4 items-center">
          <div className="w-7 h-7 bg-gray-100 animate-pulse rounded-full" />
          <div className="flex-1 h-4 bg-gray-100 animate-pulse rounded" />
          <div className="w-24 h-4 bg-gray-100 animate-pulse rounded" />
          <div className="w-12 h-4 bg-gray-100 animate-pulse rounded" />
        </div>
      ))}
    </div>
  );
}

function formatCnpj(cnpj: string): string {
  const d = cnpj.replace(/\D/g, '').padStart(14, '0');
  if (d.length !== 14) return cnpj;
  return `${d.slice(0, 2)}.${d.slice(2, 5)}.${d.slice(5, 8)}/${d.slice(8, 12)}-${d.slice(12)}`;
}
