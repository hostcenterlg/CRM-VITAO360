'use client';

import { useState, useEffect, useCallback } from 'react';
import AppShell from '@/components/AppShell';
import {
  fetchPipelineStatus,
  fetchPipelineLogs,
  runPipeline,
  PipelineStatus,
  PipelineRunResult,
  PipelineLogEntry,
} from '@/lib/api';

// ---------------------------------------------------------------------------
// Helpers de formatacao
// ---------------------------------------------------------------------------

function formatarDataHora(iso: string | null): string {
  if (!iso) return '—';
  const d = new Date(iso);
  return d.toLocaleString('pt-BR', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  });
}

function formatarDuracao(ms: number | null): string {
  if (ms === null) return '—';
  if (ms < 1000) return `${ms}ms`;
  const s = (ms / 1000).toFixed(1);
  return `${s}s`;
}

// ---------------------------------------------------------------------------
// Badge de resultado do pipeline
// ---------------------------------------------------------------------------

function BadgeResultado({ resultado }: { resultado: string | null }) {
  if (!resultado) return <span className="text-gray-400 text-sm">—</span>;

  const map: Record<string, { bg: string; text: string }> = {
    SUCESSO:  { bg: '#D1FAE5', text: '#065F46' },
    ERRO:     { bg: '#FEE2E2', text: '#991B1B' },
    RODANDO:  { bg: '#DBEAFE', text: '#1E40AF' },
  };
  const cfg = map[resultado.toUpperCase()] ?? { bg: '#F3F4F6', text: '#374151' };

  return (
    <span
      className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-semibold"
      style={{ backgroundColor: cfg.bg, color: cfg.text }}
    >
      {resultado.toUpperCase() === 'RODANDO' && (
        <span className="w-2 h-2 rounded-full bg-blue-500 animate-pulse mr-1.5" />
      )}
      {resultado}
    </span>
  );
}

// ---------------------------------------------------------------------------
// Badge de nivel de log
// ---------------------------------------------------------------------------

function BadgeNivel({ nivel }: { nivel: string }) {
  const map: Record<string, { bg: string; text: string }> = {
    INFO:    { bg: '#DBEAFE', text: '#1E40AF' },
    WARNING: { bg: '#FEF3C7', text: '#92400E' },
    WARN:    { bg: '#FEF3C7', text: '#92400E' },
    ERROR:   { bg: '#FEE2E2', text: '#991B1B' },
    DEBUG:   { bg: '#F3F4F6', text: '#374151' },
  };
  const cfg = map[nivel.toUpperCase()] ?? { bg: '#F3F4F6', text: '#374151' };

  return (
    <span
      className="inline-flex items-center px-2 py-0.5 rounded text-[10px] font-semibold uppercase"
      style={{ backgroundColor: cfg.bg, color: cfg.text }}
    >
      {nivel}
    </span>
  );
}

// ---------------------------------------------------------------------------
// Icone por status de etapa
// ---------------------------------------------------------------------------

function IconeEtapa({ status }: { status: string }) {
  const s = status.toUpperCase();
  if (s === 'OK' || s === 'SUCESSO' || s === 'SUCCESS') {
    return (
      <svg className="w-4 h-4 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5}
          d="M5 13l4 4L19 7" style={{ stroke: '#059669' }} />
      </svg>
    );
  }
  if (s === 'ERRO' || s === 'ERROR' || s === 'FAIL') {
    return (
      <svg className="w-4 h-4 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5}
          d="M6 18L18 6M6 6l12 12" style={{ stroke: '#DC2626' }} />
      </svg>
    );
  }
  return (
    <span className="w-4 h-4 flex-shrink-0 rounded-full border-2 border-gray-300 inline-block" />
  );
}

// ---------------------------------------------------------------------------
// Skeleton
// ---------------------------------------------------------------------------

function SkeletonCard() {
  return (
    <div className="animate-pulse space-y-3">
      {[1, 2, 3, 4].map((i) => (
        <div key={i} className="flex items-center gap-3">
          <div className="h-4 w-28 bg-gray-200 rounded" />
          <div className="h-4 w-40 bg-gray-100 rounded" />
        </div>
      ))}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Pagina principal
// ---------------------------------------------------------------------------

export default function PipelinePage() {
  const [status, setStatus] = useState<PipelineStatus | null>(null);
  const [logs, setLogs] = useState<PipelineLogEntry[]>([]);
  const [carregandoStatus, setCarregandoStatus] = useState(true);
  const [carregandoLogs, setCarregandoLogs] = useState(true);
  const [erroStatus, setErroStatus] = useState<string | null>(null);
  const [erroLogs, setErroLogs] = useState<string | null>(null);

  // Estado de execucao do pipeline
  const [executando, setExecutando] = useState(false);
  const [resultado, setResultado] = useState<PipelineRunResult | null>(null);
  const [erroExecucao, setErroExecucao] = useState<string | null>(null);

  // Buscar status
  const buscarStatus = useCallback(async () => {
    try {
      const data = await fetchPipelineStatus();
      setStatus(data);
      setErroStatus(null);
    } catch (e) {
      setErroStatus(e instanceof Error ? e.message : 'Erro ao carregar status');
    } finally {
      setCarregandoStatus(false);
    }
  }, []);

  // Buscar logs
  const buscarLogs = useCallback(async () => {
    try {
      const data = await fetchPipelineLogs();
      setLogs(data.slice(0, 20));
      setErroLogs(null);
    } catch (e) {
      setErroLogs(e instanceof Error ? e.message : 'Erro ao carregar logs');
    } finally {
      setCarregandoLogs(false);
    }
  }, []);

  // Carga inicial
  useEffect(() => {
    buscarStatus();
    buscarLogs();
  }, [buscarStatus, buscarLogs]);

  // Auto-refresh de logs a cada 30s
  useEffect(() => {
    const intervalo = setInterval(() => {
      buscarLogs();
    }, 30_000);
    return () => clearInterval(intervalo);
  }, [buscarLogs]);

  // Executar pipeline
  async function handleExecutar() {
    setExecutando(true);
    setResultado(null);
    setErroExecucao(null);
    try {
      const res = await runPipeline();
      setResultado(res);
      // Atualizar status e logs apos execucao
      await Promise.all([buscarStatus(), buscarLogs()]);
    } catch (e) {
      setErroExecucao(e instanceof Error ? e.message : 'Erro ao executar pipeline');
    } finally {
      setExecutando(false);
    }
  }

  return (
    <AppShell>
      {/* Header da pagina */}
      <div className="mb-6">
        <h1 className="text-lg sm:text-xl font-bold text-gray-900">Pipeline de Dados</h1>
        <p className="text-sm text-gray-500 mt-0.5">
          Sincronizacao automatica Mercos / Deskrio
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Coluna esquerda — status + botao */}
        <div className="lg:col-span-1 space-y-4">
          {/* Card status */}
          <div className="bg-white border border-gray-200 rounded-xl p-5 shadow-sm">
            <h2 className="text-sm font-semibold text-gray-700 mb-4 flex items-center gap-2">
              <svg className="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                  d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
              </svg>
              Status do Pipeline
            </h2>

            {carregandoStatus ? (
              <SkeletonCard />
            ) : erroStatus ? (
              <div className="text-sm text-red-600 bg-red-50 rounded-lg p-3">{erroStatus}</div>
            ) : status ? (
              <dl className="space-y-3">
                <div>
                  <dt className="text-xs text-gray-400 uppercase tracking-wide mb-0.5">Ultimo run</dt>
                  <dd className="text-sm text-gray-800 font-medium">
                    {formatarDataHora(status.ultimo_run)}
                  </dd>
                </div>
                <div>
                  <dt className="text-xs text-gray-400 uppercase tracking-wide mb-0.5">Resultado</dt>
                  <dd><BadgeResultado resultado={status.resultado} /></dd>
                </div>
                <div>
                  <dt className="text-xs text-gray-400 uppercase tracking-wide mb-0.5">Duracao</dt>
                  <dd className="text-sm text-gray-800 font-medium">
                    {formatarDuracao(status.duracao_ms)}
                  </dd>
                </div>
                <div>
                  <dt className="text-xs text-gray-400 uppercase tracking-wide mb-0.5">Proximo agendado</dt>
                  <dd className="text-sm text-gray-800 font-medium">
                    {formatarDataHora(status.proximo_agendado)}
                  </dd>
                </div>
              </dl>
            ) : (
              <p className="text-sm text-gray-400">Nenhum dado disponivel</p>
            )}

            {/* Botao atualizar status */}
            <button
              type="button"
              onClick={buscarStatus}
              className="mt-4 w-full flex items-center justify-center gap-1.5 px-3 py-1.5
                         text-xs font-medium text-gray-600 border border-gray-200 rounded-lg
                         hover:bg-gray-50 transition-colors"
            >
              <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                  d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
              Atualizar status
            </button>
          </div>

          {/* Botao Executar Pipeline */}
          <div className="bg-white border border-gray-200 rounded-xl p-5 shadow-sm">
            <h2 className="text-sm font-semibold text-gray-700 mb-3">Execucao Manual</h2>
            <p className="text-xs text-gray-500 mb-4 leading-relaxed">
              Dispara o pipeline completo de sincronizacao: importacao Mercos, integracao Deskrio e recalculo de scores.
            </p>

            <button
              type="button"
              onClick={handleExecutar}
              disabled={executando}
              className="w-full flex items-center justify-center gap-2 px-4 py-3
                         text-sm font-semibold text-white rounded-xl transition-all
                         disabled:opacity-60 disabled:cursor-not-allowed
                         focus:outline-none focus:ring-2 focus:ring-green-500 focus:ring-offset-2"
              style={{ backgroundColor: executando ? '#6B7280' : '#00B050' }}
            >
              {executando ? (
                <>
                  <span className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                  Executando...
                </>
              ) : (
                <>
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                      d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" />
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                      d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  Executar Pipeline
                </>
              )}
            </button>
          </div>
        </div>

        {/* Coluna direita — resultado da execucao + logs */}
        <div className="lg:col-span-2 space-y-4">
          {/* Resultado da execucao */}
          {(resultado || erroExecucao) && (
            <div className={`border rounded-xl p-5 shadow-sm ${
              erroExecucao ? 'bg-red-50 border-red-200' : 'bg-white border-gray-200'
            }`}>
              <h2 className="text-sm font-semibold text-gray-700 mb-4 flex items-center gap-2">
                <svg className="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                    d="M13 10V3L4 14h7v7l9-11h-7z" />
                </svg>
                Resultado da Execucao
              </h2>

              {erroExecucao && (
                <div className="text-sm text-red-700 flex items-start gap-2">
                  <svg className="w-4 h-4 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                      d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  {erroExecucao}
                </div>
              )}

              {resultado && (
                <div className="space-y-4">
                  {/* Sumario */}
                  <div className="flex items-center gap-4 flex-wrap">
                    <div className="flex items-center gap-2">
                      <span className="text-xs text-gray-500">Status:</span>
                      <BadgeResultado resultado={resultado.status} />
                    </div>
                    <div className="flex items-center gap-2">
                      <span className="text-xs text-gray-500">Duracao total:</span>
                      <span className="text-sm font-medium text-gray-800">
                        {formatarDuracao(resultado.duracao_total_ms)}
                      </span>
                    </div>
                  </div>

                  {/* Etapas */}
                  {resultado.etapas.length > 0 && (
                    <div className="space-y-2">
                      <p className="text-xs font-medium text-gray-500 uppercase tracking-wide">
                        Etapas ({resultado.etapas.length})
                      </p>
                      <div className="space-y-1.5">
                        {resultado.etapas.map((etapa, idx) => (
                          <div
                            key={idx}
                            className="flex items-center gap-3 px-3 py-2 bg-gray-50 rounded-lg text-sm"
                          >
                            <IconeEtapa status={etapa.status} />
                            <span className="flex-1 font-medium text-gray-800">{etapa.nome}</span>
                            <span className="text-xs text-gray-400">{formatarDuracao(etapa.duracao_ms)}</span>
                            {etapa.detalhes && (
                              <span className="text-xs text-gray-500 italic truncate max-w-[160px]">
                                {etapa.detalhes}
                              </span>
                            )}
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>
          )}

          {/* Logs */}
          <div className="bg-white border border-gray-200 rounded-xl shadow-sm overflow-hidden">
            <div className="flex items-center justify-between px-5 py-3.5 border-b border-gray-100 bg-gray-50">
              <h2 className="text-sm font-semibold text-gray-700 flex items-center gap-2">
                <svg className="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                    d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
                </svg>
                Logs Recentes
              </h2>
              <div className="flex items-center gap-2">
                <span className="text-xs text-gray-400">Atualiza a cada 30s</span>
                <button
                  type="button"
                  onClick={buscarLogs}
                  title="Atualizar logs"
                  className="p-1 rounded text-gray-400 hover:text-gray-700 hover:bg-gray-100 transition-colors"
                >
                  <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                      d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                  </svg>
                </button>
              </div>
            </div>

            {carregandoLogs ? (
              <div className="p-5">
                <div className="animate-pulse space-y-2.5">
                  {[1, 2, 3, 4, 5].map((i) => (
                    <div key={i} className="flex items-center gap-3">
                      <div className="h-3.5 w-32 bg-gray-200 rounded" />
                      <div className="h-4 w-12 bg-gray-100 rounded" />
                      <div className="h-3.5 flex-1 bg-gray-100 rounded" />
                    </div>
                  ))}
                </div>
              </div>
            ) : erroLogs ? (
              <div className="p-5 text-sm text-red-600 bg-red-50">{erroLogs}</div>
            ) : logs.length === 0 ? (
              <div className="flex flex-col items-center justify-center py-10 text-gray-400">
                <svg className="w-8 h-8 opacity-40 mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
                    d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
                </svg>
                <span className="text-sm">Nenhum log disponivel</span>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-xs">
                  <thead>
                    <tr className="text-left">
                      <th className="px-4 py-2.5 text-gray-500 font-medium border-b border-gray-100 whitespace-nowrap">
                        Timestamp
                      </th>
                      <th className="px-4 py-2.5 text-gray-500 font-medium border-b border-gray-100">
                        Nivel
                      </th>
                      <th className="px-4 py-2.5 text-gray-500 font-medium border-b border-gray-100">
                        Mensagem
                      </th>
                    </tr>
                  </thead>
                  <tbody>
                    {logs.map((log, idx) => (
                      <tr
                        key={idx}
                        className={idx % 2 === 0 ? 'bg-white' : 'bg-gray-50/50'}
                      >
                        <td className="px-4 py-2 text-gray-400 font-mono whitespace-nowrap align-top">
                          {formatarDataHora(log.timestamp)}
                        </td>
                        <td className="px-4 py-2 align-top">
                          <BadgeNivel nivel={log.nivel} />
                        </td>
                        <td className="px-4 py-2 text-gray-700 align-top leading-relaxed">
                          {log.mensagem}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>
      </div>
    </AppShell>
  );
}
