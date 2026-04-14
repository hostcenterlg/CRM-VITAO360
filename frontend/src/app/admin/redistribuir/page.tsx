'use client';

import { useState, useEffect, useCallback } from 'react';
import Skeleton from '@/components/Skeleton';
import {
  fetchConsultorResumo,
  fetchClientes,
  redistribuirCarteira,
  formatBRL,
  ConsultorResumo,
  ClienteRegistro,
} from '@/lib/api';

// ---------------------------------------------------------------------------
// Admin — Redistribuicao de Carteira (FR-022)
// Operacao L3: aprovada por Leandro — licenca maternidade Manu Q2 2026.
// Acesso exclusivo: role=admin (protegido via RouteGuard + require_admin backend).
// LIGHT theme. Portugues Brasileiro. CNPJ: string 14 digitos.
// ---------------------------------------------------------------------------

const CONSULTORES = ['MANU', 'LARISSA', 'DAIANE', 'JULIO'] as const;
type Consultor = (typeof CONSULTORES)[number];

// Cores por consultor para os cards de resumo
const CONSULTOR_CORES: Record<Consultor, { bg: string; border: string; text: string }> = {
  MANU:    { bg: '#EFF6FF', border: '#BFDBFE', text: '#1D4ED8' },
  LARISSA: { bg: '#F0FDF4', border: '#BBF7D0', text: '#15803D' },
  DAIANE:  { bg: '#FFF7ED', border: '#FED7AA', text: '#C2410C' },
  JULIO:   { bg: '#FAF5FF', border: '#E9D5FF', text: '#7C3AED' },
};

// ---------------------------------------------------------------------------
// Componentes auxiliares
// ---------------------------------------------------------------------------

function CardConsultor({ resumo }: { resumo: ConsultorResumo }) {
  const cores = CONSULTOR_CORES[resumo.consultor as Consultor] ?? {
    bg: '#F9FAFB',
    border: '#E5E7EB',
    text: '#374151',
  };
  return (
    <div
      className="rounded-lg border p-4 flex flex-col gap-1"
      style={{ backgroundColor: cores.bg, borderColor: cores.border }}
    >
      <p className="text-[11px] font-bold uppercase tracking-wider" style={{ color: cores.text }}>
        {resumo.consultor}
      </p>
      <p className="text-xl font-bold text-gray-900">{resumo.total}</p>
      <p className="text-[10px] text-gray-500">clientes</p>
      <p className="text-xs font-semibold text-gray-700 mt-1">{formatBRL(resumo.faturamento)}</p>
      <p className="text-[10px] text-gray-400">faturamento acumulado</p>
    </div>
  );
}

interface ModalConfirmacaoProps {
  qtd: number;
  origem: string;
  destino: string;
  onConfirmar: () => void;
  onCancelar: () => void;
  loading: boolean;
}

function ModalConfirmacao({
  qtd,
  origem,
  destino,
  onConfirmar,
  onCancelar,
  loading,
}: ModalConfirmacaoProps) {
  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      if (e.key === 'Escape') onCancelar();
    }
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [onCancelar]);

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center"
      style={{ backgroundColor: 'rgba(0,0,0,0.5)' }}
      role="dialog"
      aria-modal="true"
      aria-labelledby="modal-confirm-titulo"
    >
      <div className="bg-white rounded-lg shadow-xl w-full max-w-sm mx-4">
        <div className="px-6 py-5">
          {/* Icone de aviso */}
          <div className="flex items-center justify-center w-12 h-12 rounded-full bg-amber-100 mx-auto mb-4">
            <svg className="w-6 h-6 text-amber-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
          </div>

          <h2
            id="modal-confirm-titulo"
            className="text-sm font-bold text-gray-900 text-center mb-2"
          >
            Confirmar Redistribuicao
          </h2>
          <p className="text-xs text-gray-600 text-center leading-relaxed">
            Voce esta prestes a transferir{' '}
            <span className="font-bold text-gray-900">{qtd} cliente{qtd !== 1 ? 's' : ''}</span>{' '}
            de <span className="font-bold">{origem}</span> para{' '}
            <span className="font-bold">{destino}</span>.
          </p>
          <p className="text-[10px] text-gray-400 text-center mt-2">
            Esta operacao sera registrada em auditoria e nao pode ser desfeita automaticamente.
          </p>
        </div>

        <div className="flex gap-3 px-6 pb-5">
          <button
            type="button"
            onClick={onCancelar}
            disabled={loading}
            className="flex-1 px-4 py-2 text-xs font-medium text-gray-600 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors disabled:opacity-50"
          >
            Cancelar
          </button>
          <button
            type="button"
            onClick={onConfirmar}
            disabled={loading}
            className="flex-1 px-4 py-2 text-xs font-semibold text-white rounded-lg transition-colors disabled:opacity-60"
            style={{ backgroundColor: loading ? '#9CA3AF' : '#00B050' }}
          >
            {loading ? 'Redistribuindo...' : 'Confirmar'}
          </button>
        </div>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Pagina principal
// ---------------------------------------------------------------------------

export default function RedistribuirCarteiraPage() {
  // Dados de resumo
  const [resumos, setResumos] = useState<ConsultorResumo[]>([]);
  const [loadingResumos, setLoadingResumos] = useState(true);

  // Filtros de selecao
  const [consultorOrigem, setConsultorOrigem] = useState<string>('MANU');
  const [consultorDestino, setConsultorDestino] = useState<string>('');
  const [filtroUF, setFiltroUF] = useState<string>('');

  // Lista de clientes do consultor de origem
  const [clientes, setClientes] = useState<ClienteRegistro[]>([]);
  const [loadingClientes, setLoadingClientes] = useState(false);

  // Selecao de checkboxes
  const [selecionados, setSelecionados] = useState<Set<string>>(new Set());

  // Modal e resultado
  const [mostrarModal, setMostrarModal] = useState(false);
  const [loadingRedistribuir, setLoadingRedistribuir] = useState(false);
  const [resultado, setResultado] = useState<{
    total_processados: number;
    total_atualizados: number;
    erros: string[];
  } | null>(null);

  // Erros globais
  const [erroGlobal, setErroGlobal] = useState<string | null>(null);

  // Carrega resumos de distribuicao
  const carregarResumos = useCallback(async () => {
    setLoadingResumos(true);
    try {
      const data = await fetchConsultorResumo();
      setResumos(data);
    } catch (err: unknown) {
      setErroGlobal(err instanceof Error ? err.message : 'Erro ao carregar distribuicao');
    } finally {
      setLoadingResumos(false);
    }
  }, []);

  useEffect(() => {
    void carregarResumos();
  }, [carregarResumos]);

  // Carrega clientes do consultor de origem com filtro opcional de UF
  const carregarClientes = useCallback(async () => {
    if (!consultorOrigem) return;
    setLoadingClientes(true);
    setSelecionados(new Set());
    try {
      // Busca ate 500 clientes para exibicao na tabela
      const data = await fetchClientes({
        consultor: consultorOrigem,
        uf: filtroUF || undefined,
        limit: 500,
        offset: 0,
      });
      setClientes(data.registros);
    } catch (err: unknown) {
      setErroGlobal(err instanceof Error ? err.message : 'Erro ao carregar clientes');
    } finally {
      setLoadingClientes(false);
    }
  }, [consultorOrigem, filtroUF]);

  useEffect(() => {
    void carregarClientes();
  }, [carregarClientes]);

  // Selecionar / desmarcar todos
  function toggleTodos() {
    if (selecionados.size === clientes.length && clientes.length > 0) {
      setSelecionados(new Set());
    } else {
      setSelecionados(new Set(clientes.map((c) => c.cnpj)));
    }
  }

  function toggleCliente(cnpj: string) {
    setSelecionados((prev) => {
      const next = new Set(prev);
      if (next.has(cnpj)) {
        next.delete(cnpj);
      } else {
        next.add(cnpj);
      }
      return next;
    });
  }

  // UFs unicas disponıveis para filtro
  const ufsDisponiveis = Array.from(
    new Set(clientes.map((c) => c.uf).filter(Boolean) as string[])
  ).sort();

  // Validacao do botao de redistribuir
  const podeRedistribuir =
    selecionados.size > 0 &&
    consultorDestino !== '' &&
    consultorDestino !== consultorOrigem;

  // Executar redistribuicao apos confirmacao
  async function executarRedistribuicao() {
    setLoadingRedistribuir(true);
    try {
      const res = await redistribuirCarteira(Array.from(selecionados), consultorDestino);
      setResultado(res);
      setMostrarModal(false);
      setSelecionados(new Set());
      // Recarregar dados atualizados
      await Promise.all([carregarResumos(), carregarClientes()]);
    } catch (err: unknown) {
      setErroGlobal(err instanceof Error ? err.message : 'Erro ao redistribuir carteira');
      setMostrarModal(false);
    } finally {
      setLoadingRedistribuir(false);
    }
  }

  // Curva ABC — badge colorido
  function CurvaABCBadge({ curva }: { curva?: string }) {
    const cores: Record<string, { bg: string; text: string }> = {
      A: { bg: '#00B050', text: '#fff' },
      B: { bg: '#FFFF00', text: '#374151' },
      C: { bg: '#FFC000', text: '#1a1a1a' },
    };
    if (!curva) return <span className="text-gray-300 text-[10px]">—</span>;
    const cfg = cores[curva] ?? { bg: '#E5E7EB', text: '#374151' };
    return (
      <span
        className="inline-flex items-center justify-center w-5 h-5 rounded text-[9px] font-bold"
        style={{ backgroundColor: cfg.bg, color: cfg.text }}
      >
        {curva}
      </span>
    );
  }

  const todosSelecionados = clientes.length > 0 && selecionados.size === clientes.length;

  return (
    <div className="space-y-5">
      {/* Cabecalho */}
      <div>
        <h1 className="text-lg font-bold text-gray-900">Redistribuicao de Carteira</h1>
        <p className="text-xs text-gray-500 mt-0.5">
          FR-022 — Transferencia de clientes entre consultores. Operacao auditada.
        </p>
      </div>

      {/* Erro global */}
      {erroGlobal && (
        <div
          role="alert"
          className="p-3 bg-red-50 border border-red-200 rounded-lg text-xs text-red-700 flex items-center justify-between"
        >
          <span>{erroGlobal}</span>
          <button
            type="button"
            onClick={() => setErroGlobal(null)}
            className="ml-2 text-red-500 hover:text-red-700"
            aria-label="Fechar aviso de erro"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
      )}

      {/* Resultado de redistribuicao bem-sucedida */}
      {resultado && (
        <div className="p-4 bg-green-50 border border-green-200 rounded-lg">
          <div className="flex items-center justify-between mb-2">
            <p className="text-xs font-bold text-green-800 uppercase tracking-wide">
              Redistribuicao concluida
            </p>
            <button
              type="button"
              onClick={() => setResultado(null)}
              className="text-green-600 hover:text-green-800"
              aria-label="Fechar resultado"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
          <div className="flex gap-6 text-xs text-green-800">
            <span>Processados: <strong>{resultado.total_processados}</strong></span>
            <span>Atualizados: <strong>{resultado.total_atualizados}</strong></span>
            {resultado.erros.length > 0 && (
              <span className="text-amber-700">Erros: <strong>{resultado.erros.length}</strong></span>
            )}
          </div>
          {resultado.erros.length > 0 && (
            <ul className="mt-2 space-y-0.5">
              {resultado.erros.map((e, i) => (
                <li key={i} className="text-[10px] text-amber-700">
                  {e}
                </li>
              ))}
            </ul>
          )}
        </div>
      )}

      {/* Cards de distribuicao atual */}
      <div>
        <p className="text-xs font-semibold text-gray-600 uppercase tracking-wider mb-3">
          Distribuicao Atual
        </p>
        {loadingResumos ? (
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            {Array.from({ length: 4 }).map((_, i) => (
              <Skeleton.Kpi key={i} />
            ))}
          </div>
        ) : (
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            {resumos.map((r) => (
              <CardConsultor key={r.consultor} resumo={r} />
            ))}
            {resumos.length === 0 && (
              <p className="col-span-4 text-xs text-gray-400">Nenhum dado de distribuicao.</p>
            )}
          </div>
        )}
      </div>

      {/* Selecao de origem e destino */}
      <div className="bg-white rounded-lg border border-gray-200 p-4">
        <p className="text-xs font-semibold text-gray-700 uppercase tracking-wider mb-4">
          Configurar Transferencia
        </p>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          {/* Origem */}
          <div>
            <label className="block text-[10px] font-semibold text-gray-500 uppercase tracking-wide mb-1">
              Consultor de Origem
            </label>
            <select
              value={consultorOrigem}
              onChange={(e) => {
                setConsultorOrigem(e.target.value);
                setConsultorDestino('');
              }}
              className="w-full h-9 px-3 text-xs border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-green-500 bg-white"
            >
              {CONSULTORES.map((c) => (
                <option key={c} value={c}>{c}</option>
              ))}
            </select>
          </div>

          {/* Destino */}
          <div>
            <label className="block text-[10px] font-semibold text-gray-500 uppercase tracking-wide mb-1">
              Consultor Destino
            </label>
            <select
              value={consultorDestino}
              onChange={(e) => setConsultorDestino(e.target.value)}
              className="w-full h-9 px-3 text-xs border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-green-500 bg-white"
            >
              <option value="">Selecionar destino...</option>
              {CONSULTORES.filter((c) => c !== consultorOrigem).map((c) => (
                <option key={c} value={c}>{c}</option>
              ))}
            </select>
          </div>

          {/* Filtro UF */}
          <div>
            <label className="block text-[10px] font-semibold text-gray-500 uppercase tracking-wide mb-1">
              Filtrar por UF (opcional)
            </label>
            <select
              value={filtroUF}
              onChange={(e) => setFiltroUF(e.target.value)}
              className="w-full h-9 px-3 text-xs border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-green-500 bg-white"
            >
              <option value="">Todas as UFs</option>
              {ufsDisponiveis.map((uf) => (
                <option key={uf} value={uf}>{uf}</option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {/* Tabela de clientes */}
      <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
        {/* Cabecalho da tabela com acoes */}
        <div className="flex items-center justify-between px-4 py-3 border-b border-gray-100 bg-gray-50">
          <div className="flex items-center gap-3">
            <input
              type="checkbox"
              id="selecionar-todos"
              checked={todosSelecionados}
              onChange={toggleTodos}
              disabled={clientes.length === 0}
              className="w-4 h-4 accent-green-600 cursor-pointer disabled:cursor-default"
              aria-label="Selecionar todos os clientes"
            />
            <label htmlFor="selecionar-todos" className="text-xs text-gray-600 cursor-pointer">
              {todosSelecionados
                ? `${clientes.length} selecionados`
                : selecionados.size > 0
                ? `${selecionados.size} de ${clientes.length} selecionados`
                : `${clientes.length} clientes de ${consultorOrigem}`}
            </label>
          </div>

          {/* Botao de redistribuir */}
          <button
            type="button"
            disabled={!podeRedistribuir || loadingRedistribuir}
            onClick={() => setMostrarModal(true)}
            className="flex items-center gap-2 px-4 py-2 text-xs font-semibold text-white rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            style={{ backgroundColor: podeRedistribuir ? '#00B050' : '#9CA3AF' }}
          >
            <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                d="M8 7h12m0 0l-4-4m4 4l-4 4m0 6H4m0 0l4 4m-4-4l4-4" />
            </svg>
            {selecionados.size > 0 && consultorDestino
              ? `Redistribuir ${selecionados.size} para ${consultorDestino}`
              : 'Redistribuir Selecionados'}
          </button>
        </div>

        {/* Conteudo da tabela */}
        {loadingClientes ? (
          <div className="flex items-center justify-center py-16">
            <div className="w-5 h-5 border-2 border-gray-300 border-t-green-600 rounded-full animate-spin" />
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full" role="table">
              <thead>
                <tr className="border-b border-gray-100">
                  <th scope="col" className="w-10 px-4 py-2.5" aria-label="Selecao" />
                  <th scope="col" className="px-4 py-2.5 text-left text-[10px] font-semibold text-gray-500 uppercase tracking-wide">
                    CNPJ
                  </th>
                  <th scope="col" className="px-4 py-2.5 text-left text-[10px] font-semibold text-gray-500 uppercase tracking-wide">
                    Nome
                  </th>
                  <th scope="col" className="px-4 py-2.5 text-left text-[10px] font-semibold text-gray-500 uppercase tracking-wide">
                    UF
                  </th>
                  <th scope="col" className="px-4 py-2.5 text-right text-[10px] font-semibold text-gray-500 uppercase tracking-wide">
                    Faturamento
                  </th>
                  <th scope="col" className="px-4 py-2.5 text-center text-[10px] font-semibold text-gray-500 uppercase tracking-wide">
                    ABC
                  </th>
                  <th scope="col" className="px-4 py-2.5 text-left text-[10px] font-semibold text-gray-500 uppercase tracking-wide">
                    Situacao
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-50">
                {clientes.length === 0 ? (
                  <tr>
                    <td colSpan={7} className="px-4 py-10 text-center text-xs text-gray-400">
                      Nenhum cliente encontrado para {consultorOrigem}
                      {filtroUF ? ` / UF ${filtroUF}` : ''}.
                    </td>
                  </tr>
                ) : (
                  clientes.map((c) => {
                    const isSelecionado = selecionados.has(c.cnpj);
                    return (
                      <tr
                        key={c.cnpj}
                        onClick={() => toggleCliente(c.cnpj)}
                        className="hover:bg-gray-50 cursor-pointer transition-colors"
                        style={{ backgroundColor: isSelecionado ? '#F0FDF4' : undefined }}
                      >
                        <td className="px-4 py-2.5" onClick={(e) => e.stopPropagation()}>
                          <input
                            type="checkbox"
                            checked={isSelecionado}
                            onChange={() => toggleCliente(c.cnpj)}
                            className="w-4 h-4 accent-green-600 cursor-pointer"
                            aria-label={`Selecionar ${c.nome_fantasia ?? c.cnpj}`}
                          />
                        </td>
                        <td className="px-4 py-2.5 font-mono text-[10px] text-gray-500">
                          {c.cnpj}
                        </td>
                        <td className="px-4 py-2.5 text-xs font-medium text-gray-900 max-w-[200px] truncate">
                          {c.nome_fantasia ?? <span className="text-gray-400">—</span>}
                        </td>
                        <td className="px-4 py-2.5 text-xs text-gray-600">
                          {c.uf ?? <span className="text-gray-300">—</span>}
                        </td>
                        <td className="px-4 py-2.5 text-right text-xs text-gray-700 tabular-nums">
                          {c.faturamento_total != null
                            ? formatBRL(c.faturamento_total)
                            : <span className="text-gray-300">—</span>}
                        </td>
                        <td className="px-4 py-2.5 text-center">
                          <CurvaABCBadge curva={c.curva_abc} />
                        </td>
                        <td className="px-4 py-2.5 text-[10px] text-gray-500 uppercase">
                          {c.situacao ?? <span className="text-gray-300">—</span>}
                        </td>
                      </tr>
                    );
                  })
                )}
              </tbody>
            </table>
            {clientes.length > 0 && (
              <div className="px-4 py-3 border-t border-gray-100 text-[10px] text-gray-400">
                {clientes.length} cliente{clientes.length !== 1 ? 's' : ''} carregados
                {filtroUF ? ` — UF: ${filtroUF}` : ''}
                {selecionados.size > 0 ? ` — ${selecionados.size} selecionado${selecionados.size !== 1 ? 's' : ''}` : ''}
              </div>
            )}
          </div>
        )}
      </div>

      {/* Modal de confirmacao */}
      {mostrarModal && (
        <ModalConfirmacao
          qtd={selecionados.size}
          origem={consultorOrigem}
          destino={consultorDestino}
          onConfirmar={() => void executarRedistribuicao()}
          onCancelar={() => setMostrarModal(false)}
          loading={loadingRedistribuir}
        />
      )}
    </div>
  );
}
