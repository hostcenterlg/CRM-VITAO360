'use client';

import { useEffect, useRef, useState } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { useCanal } from '@/contexts/CanalContext';
import type { Canal } from '@/lib/api';

// ---------------------------------------------------------------------------
// CanalSelector — dropdown compacto para o header
//
// Comportamento:
//  - admin: lista 'Todos' + cada canal cadastrado (canalId = null|id)
//  - nao-admin com 1 canal: NAO RENDERIZA (canal eh fixo)
//  - nao-admin com 2+ canais: dropdown com seus canais permitidos
//  - badge colorido por status:
//      ATIVO       -> #00B050 (verde)
//      EM_BREVE    -> #FFC000 (amarelo)
//      ADMIN_ONLY  -> #6B7280 (cinza)
//
// Persistencia: via CanalContext -> localStorage('crm_canal_id').
// ---------------------------------------------------------------------------

const STATUS_COLORS: Record<string, { bg: string; fg: string; label: string }> = {
  ATIVO:       { bg: '#00B050', fg: '#FFFFFF', label: 'Ativo'      },
  EM_BREVE:    { bg: '#FFC000', fg: '#1F2937', label: 'Em breve'   },
  ADMIN_ONLY:  { bg: '#6B7280', fg: '#FFFFFF', label: 'Restrito'   },
};

function StatusDot({ status }: { status: string }) {
  const cfg = STATUS_COLORS[status] ?? STATUS_COLORS.ATIVO!;
  return (
    <span
      aria-hidden="true"
      className="inline-block w-2 h-2 rounded-full flex-shrink-0"
      style={{ backgroundColor: cfg.bg }}
    />
  );
}

function StatusBadge({ status }: { status: string }) {
  const cfg = STATUS_COLORS[status] ?? STATUS_COLORS.ATIVO!;
  return (
    <span
      className="text-[9px] font-bold px-1.5 py-0.5 rounded uppercase tracking-wide"
      style={{ backgroundColor: cfg.bg, color: cfg.fg }}
    >
      {cfg.label}
    </span>
  );
}

interface OpcaoBaseProps {
  selecionado: boolean;
  onClick: () => void;
}

function OpcaoTodos({ selecionado, onClick }: OpcaoBaseProps) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={`flex items-center justify-between w-full px-3 py-2 text-xs text-left transition-colors ${
        selecionado ? 'bg-green-50 text-green-700' : 'text-gray-700 hover:bg-gray-50'
      }`}
    >
      <span className="flex items-center gap-2">
        <span aria-hidden="true" className="inline-block w-2 h-2 rounded-full bg-purple-500 flex-shrink-0" />
        <span className="font-semibold">Todos os canais</span>
      </span>
      {selecionado && (
        <svg className="w-3.5 h-3.5 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M5 13l4 4L19 7" />
        </svg>
      )}
    </button>
  );
}

interface OpcaoCanalProps extends OpcaoBaseProps {
  canal: Canal;
}

function OpcaoCanal({ canal, selecionado, onClick }: OpcaoCanalProps) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={`flex items-center justify-between w-full px-3 py-2 text-xs text-left transition-colors ${
        selecionado ? 'bg-green-50 text-green-700' : 'text-gray-700 hover:bg-gray-50'
      }`}
    >
      <span className="flex items-center gap-2 min-w-0">
        <StatusDot status={canal.status} />
        <span className="truncate font-medium">{canal.nome}</span>
        <StatusBadge status={canal.status} />
      </span>
      {selecionado && (
        <svg className="w-3.5 h-3.5 text-green-600 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M5 13l4 4L19 7" />
        </svg>
      )}
    </button>
  );
}

export default function CanalSelector() {
  const { user } = useAuth();
  const { canalId, setCanalId, canaisDisponiveis: canaisRaw, carregando, erro } = useCanal();
  // Defensivo: garante array mesmo se o context devolver null/undefined em race conditions
  const canaisDisponiveis = Array.isArray(canaisRaw) ? canaisRaw : [];
  const [aberto, setAberto] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);

  const ehAdmin = user?.role === 'admin';

  // Fechar ao clicar fora
  useEffect(() => {
    if (!aberto) return;
    function onClickFora(e: MouseEvent) {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setAberto(false);
      }
    }
    document.addEventListener('mousedown', onClickFora);
    return () => document.removeEventListener('mousedown', onClickFora);
  }, [aberto]);

  // Fechar com Escape
  useEffect(() => {
    if (!aberto) return;
    function onKey(e: KeyboardEvent) {
      if (e.key === 'Escape') setAberto(false);
    }
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [aberto]);

  // Sem usuario logado -> nada para mostrar
  if (!user) return null;

  // Loading discreto
  if (carregando) {
    return (
      <div className="flex items-center gap-1.5 px-2.5 py-1.5 text-xs text-gray-400">
        <div className="w-3 h-3 border-2 border-gray-300 border-t-green-500 rounded-full animate-spin" />
        <span className="hidden md:inline">Canais</span>
      </div>
    );
  }

  // Erro -> badge discreto, nao bloqueia o header
  if (erro) {
    return (
      <div
        title={erro}
        className="flex items-center gap-1.5 px-2.5 py-1.5 text-xs text-red-500 bg-red-50 border border-red-200 rounded-lg"
      >
        <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
            d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
        </svg>
        <span className="hidden md:inline">Canais offline</span>
      </div>
    );
  }

  // Nao-admin com 1 canal -> nao renderiza (canal eh fixo, regra explicita do bloco 4)
  if (!ehAdmin && canaisDisponiveis.length <= 1) {
    return null;
  }

  // Admin sem canais (banco vazio?) -> trava como vazio
  if (canaisDisponiveis.length === 0) {
    return null;
  }

  const canalAtual = canaisDisponiveis.find(c => c.id === canalId) ?? null;
  const labelBotao = canalAtual?.nome ?? (ehAdmin ? 'Todos' : 'Selecionar');
  const statusBotao = canalAtual?.status ?? 'ATIVO';

  return (
    <div ref={containerRef} className="relative">
      <button
        type="button"
        onClick={() => setAberto(v => !v)}
        aria-haspopup="listbox"
        aria-expanded={aberto}
        aria-label="Selecionar canal"
        className="flex items-center gap-1.5 md:gap-2 px-2 md:px-2.5 py-1.5 rounded-lg border border-gray-200
                   text-xs font-medium text-gray-700 bg-white hover:bg-gray-50 hover:border-gray-300
                   transition-colors focus:outline-none focus:ring-2 focus:ring-green-500 max-w-[180px]"
      >
        {canalAtual ? (
          <StatusDot status={statusBotao} />
        ) : (
          <span aria-hidden="true" className="inline-block w-2 h-2 rounded-full bg-purple-500 flex-shrink-0" />
        )}
        <span className="truncate">{labelBotao}</span>
        <svg
          className={`w-3 h-3 text-gray-400 transition-transform flex-shrink-0 ${aberto ? 'rotate-180' : ''}`}
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>

      {aberto && (
        <div
          role="listbox"
          aria-label="Canais disponiveis"
          className="absolute right-0 top-full mt-1 w-[min(260px,calc(100vw-1.5rem))] bg-white border border-gray-200
                     rounded-lg shadow-lg z-50 overflow-hidden"
        >
          <div className="px-3 py-1.5 border-b border-gray-100 bg-gray-50">
            <span className="text-[10px] font-semibold text-gray-500 uppercase tracking-wide">
              {ehAdmin ? 'Filtrar por canal' : 'Seus canais'}
            </span>
          </div>
          <div className="max-h-72 overflow-y-auto py-1">
            {ehAdmin && (
              <OpcaoTodos
                selecionado={canalId === null}
                onClick={() => {
                  setCanalId(null);
                  setAberto(false);
                }}
              />
            )}
            {canaisDisponiveis.map(canal => (
              <OpcaoCanal
                key={canal.id}
                canal={canal}
                selecionado={canalId === canal.id}
                onClick={() => {
                  setCanalId(canal.id);
                  setAberto(false);
                }}
              />
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
