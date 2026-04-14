'use client';

import { useCallback, useEffect, useRef, useState } from 'react';
import {
  BriefingIAResponse,
  ChurnRiskResponse,
  ClienteRegistro,
  MensagemWAResponse,
  ResumoSemanalIAResponse,
  SugestaoProdutoResponse,
  enviarWhatsApp,
  fetchBriefingIA,
  fetchChurnRisk,
  fetchClientes,
  fetchMensagemWA,
  fetchResumoSemanalIA,
  fetchSugestaoProduto,
  formatBRL,
} from '@/lib/api';

// ---------------------------------------------------------------------------
// Central de IA — 5 agentes de inteligencia comercial
// ---------------------------------------------------------------------------

const CONSULTORES = ['LARISSA', 'MANU', 'DAIANE', 'JULIO'] as const;
type Consultor = (typeof CONSULTORES)[number];

const CHURN_NIVEL_COLORS: Record<string, string> = {
  BAIXO:   '#00B050',
  MEDIO:   '#FFC000',
  ALTO:    '#FF6600',
  CRITICO: '#FF0000',
};

// ---------------------------------------------------------------------------
// Skeleton shimmer
// ---------------------------------------------------------------------------

function SkeletonLine({ w = 'w-full' }: { w?: string }) {
  return <div className={`h-3 bg-gray-100 animate-pulse rounded ${w}`} />;
}

function CardSkeleton() {
  return (
    <div className="space-y-2 py-2">
      <SkeletonLine w="w-3/4" />
      <SkeletonLine w="w-full" />
      <SkeletonLine w="w-5/6" />
      <SkeletonLine w="w-2/3" />
    </div>
  );
}

// ---------------------------------------------------------------------------
// ClienteAutocomplete — busca por nome/CNPJ
// ---------------------------------------------------------------------------

interface ClienteAutocompleteProps {
  onSelect: (cliente: ClienteRegistro) => void;
}

function ClienteAutocomplete({ onSelect }: ClienteAutocompleteProps) {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<ClienteRegistro[]>([]);
  const [loading, setLoading] = useState(false);
  const [open, setOpen] = useState(false);
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  const buscar = useCallback((q: string) => {
    if (!q.trim() || q.length < 2) {
      setResults([]);
      setOpen(false);
      return;
    }
    setLoading(true);
    fetchClientes({ busca: q, limit: 8 })
      .then((res) => {
        setResults(res.registros);
        setOpen(res.registros.length > 0);
      })
      .catch(() => setResults([]))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => buscar(query), 300);
    return () => {
      if (debounceRef.current) clearTimeout(debounceRef.current);
    };
  }, [query, buscar]);

  // Fechar dropdown ao clicar fora
  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setOpen(false);
      }
    };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, []);

  const handleSelect = (c: ClienteRegistro) => {
    setQuery(c.nome_fantasia);
    setOpen(false);
    onSelect(c);
  };

  return (
    <div ref={containerRef} className="relative w-full max-w-md">
      <div className="relative">
        <svg
          className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
            d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
        </svg>
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Buscar cliente por nome ou CNPJ..."
          aria-label="Buscar cliente"
          className="w-full h-10 pl-10 pr-10 text-sm border border-gray-300 rounded-lg bg-white text-gray-900 placeholder:text-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
        />
        {loading && (
          <span className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 border-2 border-blue-300 border-t-blue-600 rounded-full animate-spin" />
        )}
      </div>

      {open && results.length > 0 && (
        <ul
          role="listbox"
          className="absolute z-50 top-full left-0 right-0 mt-1 bg-white border border-gray-200 rounded-lg shadow-lg max-h-56 overflow-y-auto"
        >
          {results.map((c) => (
            <li key={c.cnpj}>
              <button
                type="button"
                role="option"
                aria-selected={false}
                onClick={() => handleSelect(c)}
                className="w-full flex items-center justify-between px-3 py-2 text-left hover:bg-blue-50 transition-colors"
              >
                <div className="min-w-0">
                  <p className="text-sm font-medium text-gray-900 truncate">{c.nome_fantasia}</p>
                  <p className="text-[11px] text-gray-500 font-mono">{c.cnpj}</p>
                </div>
                <div className="flex-shrink-0 text-right ml-3">
                  <span className="text-[11px] text-gray-400">{c.consultor}</span>
                  <p className="text-[11px] text-gray-400">{c.uf}</p>
                </div>
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Card wrapper padrao
// ---------------------------------------------------------------------------

interface AgentCardProps {
  title: string;
  subtitle?: string;
  accentColor: string;
  icon: React.ReactNode;
  children: React.ReactNode;
  disabled?: boolean;
}

function AgentCard({ title, subtitle, accentColor, icon, children, disabled }: AgentCardProps) {
  return (
    <div
      className={`bg-white rounded-xl border border-gray-200 shadow-sm hover:shadow-md transition-shadow overflow-hidden ${disabled ? 'opacity-60' : ''}`}
    >
      <div
        className="flex items-center gap-3 px-4 py-3 border-b border-gray-100"
        style={{ borderLeftWidth: 3, borderLeftColor: accentColor, borderLeftStyle: 'solid' }}
      >
        <span style={{ color: accentColor }}>{icon}</span>
        <div className="min-w-0">
          <p className="text-sm font-semibold text-gray-900 leading-tight">{title}</p>
          {subtitle && <p className="text-[11px] text-gray-500 leading-tight">{subtitle}</p>}
        </div>
      </div>
      <div className="px-4 py-3">{children}</div>
    </div>
  );
}

function EmptyState({ msg }: { msg: string }) {
  return <p className="text-xs text-gray-400 italic py-2">{msg}</p>;
}

function ErrorState({ msg }: { msg: string }) {
  return (
    <p className="text-xs text-red-600 bg-red-50 border border-red-200 rounded px-3 py-2">
      {msg}
    </p>
  );
}

// ---------------------------------------------------------------------------
// Card 1: Briefing Pre-Ligacao
// ---------------------------------------------------------------------------

function CardBriefing({ cnpj }: { cnpj: string | null }) {
  const [data, setData] = useState<BriefingIAResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [copiado, setCopiado] = useState(false);

  useEffect(() => {
    if (!cnpj) { setData(null); return; }
    setLoading(true);
    setError(null);
    fetchBriefingIA(cnpj)
      .then(setData)
      .catch((e: Error) => setError(e.message))
      .finally(() => setLoading(false));
  }, [cnpj]);

  const handleCopiar = async () => {
    if (!data?.script_venda) return;
    try {
      await navigator.clipboard.writeText(data.script_venda);
      setCopiado(true);
      setTimeout(() => setCopiado(false), 2000);
    } catch { /* fallback silencioso */ }
  };

  return (
    <AgentCard
      title="Briefing Pre-Ligacao"
      subtitle="Resumo estrategico antes de ligar"
      accentColor="#1D4ED8"
      disabled={!cnpj}
      icon={
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
            d="M3 5a2 2 0 012-2h3.28a1 1 0 01.948.684l1.498 4.493a1 1 0 01-.502 1.21l-2.257 1.13a11.042 11.042 0 005.516 5.516l1.13-2.257a1 1 0 011.21-.502l4.493 1.498a1 1 0 01.684.949V19a2 2 0 01-2 2h-1C9.716 21 3 14.284 3 6V5z" />
        </svg>
      }
    >
      {!cnpj && <EmptyState msg="Selecione um cliente para gerar o briefing." />}
      {cnpj && loading && <CardSkeleton />}
      {cnpj && error && <ErrorState msg={error} />}
      {cnpj && data && !loading && (
        <div className="space-y-3">
          <div className="flex flex-wrap gap-2">
            <span className="text-xs text-gray-600">
              Situacao: <strong className="text-gray-900">{data.situacao}</strong>
            </span>
            <span className="text-xs text-gray-600">
              Score: <strong className="text-gray-900">{data.score}</strong>
            </span>
            <span className="text-xs text-gray-600">
              Prioridade: <strong className="text-gray-900">{data.prioridade}</strong>
            </span>
            <span className="text-xs text-gray-600">
              Temperatura: <strong className="text-gray-900">{data.temperatura}</strong>
            </span>
          </div>

          <div>
            <p className="text-[10px] font-semibold text-gray-500 uppercase tracking-wider mb-1">
              Abordagem sugerida
            </p>
            <p className="text-xs text-gray-800 leading-relaxed">{data.sugestao_abordagem}</p>
          </div>

          <div>
            <div className="flex items-center justify-between mb-1">
              <p className="text-[10px] font-semibold text-gray-500 uppercase tracking-wider">
                Script de venda
              </p>
              <button
                type="button"
                onClick={handleCopiar}
                className="inline-flex items-center gap-1 px-2 py-0.5 text-[10px] font-semibold rounded transition-all focus:outline-none focus:ring-2 focus:ring-blue-500"
                style={copiado
                  ? { backgroundColor: '#00B050', color: '#fff' }
                  : { backgroundColor: '#DBEAFE', color: '#1D4ED8' }
                }
              >
                {copiado ? 'Copiado!' : 'Copiar script'}
              </button>
            </div>
            <div className="p-2.5 bg-gray-50 border border-gray-100 rounded text-xs text-gray-800 leading-relaxed whitespace-pre-wrap max-h-36 overflow-y-auto">
              {data.script_venda}
            </div>
          </div>

          {data.ultimas_compras.length > 0 && (
            <div>
              <p className="text-[10px] font-semibold text-gray-500 uppercase tracking-wider mb-1">
                Ultimas compras
              </p>
              <ul className="space-y-0.5">
                {data.ultimas_compras.slice(0, 3).map((c, i) => (
                  <li key={i} className="flex justify-between text-xs text-gray-700">
                    <span className="text-gray-500">{c.data}</span>
                    <span className="font-medium tabular-nums">{formatBRL(c.valor)}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </AgentCard>
  );
}

// ---------------------------------------------------------------------------
// Card 2: Mensagem WhatsApp
// ---------------------------------------------------------------------------

function CardMensagemWA({ cnpj, nomeCliente }: { cnpj: string | null; nomeCliente: string }) {
  const [data, setData] = useState<MensagemWAResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [copiado, setCopiado] = useState(false);
  const [enviando, setEnviando] = useState(false);
  const [enviado, setEnviado] = useState(false);
  const [erroEnvio, setErroEnvio] = useState<string | null>(null);

  useEffect(() => {
    if (!cnpj) { setData(null); return; }
    setLoading(true);
    setError(null);
    setEnviado(false);
    setErroEnvio(null);
    fetchMensagemWA(cnpj)
      .then(setData)
      .catch((e: Error) => setError(e.message))
      .finally(() => setLoading(false));
  }, [cnpj]);

  const handleCopiar = async () => {
    if (!data?.mensagem) return;
    try {
      await navigator.clipboard.writeText(data.mensagem);
      setCopiado(true);
      setTimeout(() => setCopiado(false), 2000);
    } catch { /* fallback silencioso */ }
  };

  const handleEnviar = async () => {
    if (!cnpj || !data?.mensagem) return;
    setEnviando(true);
    setErroEnvio(null);
    try {
      const res = await enviarWhatsApp(cnpj, data.mensagem);
      if (res.enviado) {
        setEnviado(true);
      } else {
        setErroEnvio(res.erro ?? 'Erro ao enviar');
      }
    } catch (e: unknown) {
      setErroEnvio(e instanceof Error ? e.message : 'Erro ao enviar');
    } finally {
      setEnviando(false);
    }
  };

  return (
    <AgentCard
      title="Mensagem WhatsApp"
      subtitle="Mensagem personalizada para o cliente"
      accentColor="#25D366"
      disabled={!cnpj}
      icon={
        <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
          <path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347z" />
          <path d="M12 0C5.373 0 0 5.373 0 12c0 2.139.558 4.144 1.535 5.879L.057 23.55a.5.5 0 00.608.608l5.693-1.479A11.952 11.952 0 0012 24c6.627 0 12-5.373 12-12S18.627 0 12 0zm0 22c-1.96 0-3.799-.56-5.354-1.527l-.383-.231-3.979 1.034 1.054-3.867-.252-.4A9.956 9.956 0 012 12C2 6.477 6.477 2 12 2s10 4.477 10 10-4.477 10-10 10z" />
        </svg>
      }
    >
      {!cnpj && <EmptyState msg="Selecione um cliente para gerar a mensagem." />}
      {cnpj && loading && <CardSkeleton />}
      {cnpj && error && <ErrorState msg={error} />}
      {cnpj && data && !loading && (
        <div className="space-y-2">
          <div className="flex flex-wrap gap-2 text-xs text-gray-600">
            <span>Tom: <strong className="text-gray-900">{data.tom}</strong></span>
            <span>Contexto: <strong className="text-gray-900">{data.contexto}</strong></span>
          </div>

          <div className="relative">
            <textarea
              readOnly
              value={data.mensagem}
              rows={5}
              aria-label={`Mensagem WhatsApp para ${nomeCliente}`}
              className="w-full p-3 text-xs border border-gray-200 rounded-lg bg-gray-50 text-gray-800 resize-none focus:outline-none leading-relaxed"
            />
          </div>

          <div className="flex gap-2">
            <button
              type="button"
              onClick={handleCopiar}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold rounded-md transition-all hover:opacity-90 focus:outline-none focus:ring-2 focus:ring-green-500"
              style={copiado
                ? { backgroundColor: '#00B050', color: '#fff' }
                : { backgroundColor: '#F0FDF4', color: '#15803D' }
              }
            >
              {copiado ? 'Copiado!' : 'Copiar'}
            </button>

            <button
              type="button"
              onClick={handleEnviar}
              disabled={enviando || enviado}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold text-white rounded-md transition-all hover:opacity-90 focus:outline-none focus:ring-2 focus:ring-green-500 disabled:opacity-50"
              style={{ backgroundColor: '#25D366' }}
            >
              {enviando ? 'Enviando...' : enviado ? 'Enviado!' : 'Enviar via WA'}
            </button>
          </div>

          {erroEnvio && <ErrorState msg={erroEnvio} />}
          {enviado && (
            <p className="text-xs text-green-700 bg-green-50 border border-green-200 rounded px-3 py-1.5">
              Mensagem enviada via WhatsApp.
            </p>
          )}
        </div>
      )}
    </AgentCard>
  );
}

// ---------------------------------------------------------------------------
// Card 3: Risco de Churn
// ---------------------------------------------------------------------------

function CardChurn({ cnpj }: { cnpj: string | null }) {
  const [data, setData] = useState<ChurnRiskResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!cnpj) { setData(null); return; }
    setLoading(true);
    setError(null);
    fetchChurnRisk(cnpj)
      .then(setData)
      .catch((e: Error) => setError(e.message))
      .finally(() => setLoading(false));
  }, [cnpj]);

  const nivelColor = data ? (CHURN_NIVEL_COLORS[data.nivel] ?? '#9CA3AF') : '#EF4444';

  return (
    <AgentCard
      title="Risco de Churn"
      subtitle="Probabilidade de perda do cliente"
      accentColor="#EF4444"
      disabled={!cnpj}
      icon={
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
            d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
        </svg>
      }
    >
      {!cnpj && <EmptyState msg="Selecione um cliente para analisar o risco." />}
      {cnpj && loading && <CardSkeleton />}
      {cnpj && error && <ErrorState msg={error} />}
      {cnpj && data && !loading && (
        <div className="space-y-3">
          {/* Badge nivel + barra de risco */}
          <div className="flex items-center gap-3">
            <span
              className="text-sm font-bold px-3 py-1 rounded-full text-white"
              style={{ backgroundColor: nivelColor }}
            >
              {data.nivel}
            </span>
            <div className="flex-1 h-2.5 bg-gray-100 rounded-full overflow-hidden">
              <div
                className="h-full rounded-full"
                style={{
                  width: `${Math.min(100, data.risco_pct)}%`,
                  backgroundColor: nivelColor,
                  transition: 'width 400ms ease-out',
                }}
              />
            </div>
            <span className="text-sm font-bold tabular-nums" style={{ color: nivelColor }}>
              {data.risco_pct.toFixed(0)}%
            </span>
          </div>

          {data.fatores.length > 0 && (
            <div>
              <p className="text-[10px] font-semibold text-gray-500 uppercase tracking-wider mb-1">
                Fatores de risco
              </p>
              <ul className="space-y-0.5">
                {data.fatores.map((f, i) => (
                  <li key={i} className="flex items-start gap-1.5 text-xs text-gray-700">
                    <span
                      className="w-1.5 h-1.5 rounded-full flex-shrink-0 mt-1"
                      style={{ backgroundColor: nivelColor }}
                    />
                    {f}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {data.recomendacao && (
            <div className="p-2.5 rounded-lg border text-xs text-gray-800 leading-relaxed"
              style={{ borderColor: nivelColor + '40', backgroundColor: nivelColor + '0A' }}>
              <strong>Recomendacao:</strong> {data.recomendacao}
            </div>
          )}
        </div>
      )}
    </AgentCard>
  );
}

// ---------------------------------------------------------------------------
// Card 4: Sugestao de Produto
// ---------------------------------------------------------------------------

function CardSugestaoProduto({ cnpj }: { cnpj: string | null }) {
  const [data, setData] = useState<SugestaoProdutoResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!cnpj) { setData(null); return; }
    setLoading(true);
    setError(null);
    fetchSugestaoProduto(cnpj)
      .then(setData)
      .catch((e: Error) => setError(e.message))
      .finally(() => setLoading(false));
  }, [cnpj]);

  return (
    <AgentCard
      title="Sugestao de Produto"
      subtitle="Produtos recomendados para este cliente"
      accentColor="#F59E0B"
      disabled={!cnpj}
      icon={
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
            d="M16 11V7a4 4 0 00-8 0v4M5 9h14l1 12H4L5 9z" />
        </svg>
      }
    >
      {!cnpj && <EmptyState msg="Selecione um cliente para ver sugestoes." />}
      {cnpj && loading && <CardSkeleton />}
      {cnpj && error && <ErrorState msg={error} />}
      {cnpj && data && !loading && (
        <div className="space-y-3">
          {data.estrategia && (
            <p className="text-xs text-gray-700 leading-relaxed italic border-l-2 border-amber-300 pl-3">
              {data.estrategia}
            </p>
          )}

          {data.produtos_sugeridos.length > 0 ? (
            <ul className="space-y-2">
              {data.produtos_sugeridos.map((p) => (
                <li key={p.id} className="flex items-start gap-2 p-2 bg-amber-50 rounded-lg border border-amber-100">
                  <div className="flex-1 min-w-0">
                    <p className="text-xs font-semibold text-gray-900 leading-tight">{p.nome}</p>
                    <p className="text-[11px] text-amber-700">{p.categoria}</p>
                    <p className="text-[11px] text-gray-600 mt-0.5">{p.motivo}</p>
                  </div>
                </li>
              ))}
            </ul>
          ) : (
            <EmptyState msg="Nenhum produto sugerido para este cliente." />
          )}
        </div>
      )}
    </AgentCard>
  );
}

// ---------------------------------------------------------------------------
// Card 5: Resumo Semanal
// ---------------------------------------------------------------------------

function CardResumoSemanal() {
  const [consultor, setConsultor] = useState<Consultor>('LARISSA');
  const [data, setData] = useState<ResumoSemanalIAResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const carregar = useCallback((c: string) => {
    setLoading(true);
    setError(null);
    fetchResumoSemanalIA(c)
      .then(setData)
      .catch((e: Error) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    carregar(consultor);
  }, [consultor, carregar]);

  return (
    <AgentCard
      title="Resumo Semanal"
      subtitle="Desempenho da semana por consultor"
      accentColor="#8B5CF6"
      icon={
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
            d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
        </svg>
      }
    >
      {/* Selector de consultor */}
      <div className="flex items-center gap-2 mb-3">
        <label className="text-[11px] font-medium text-gray-600 flex-shrink-0">Consultor:</label>
        <select
          value={consultor}
          onChange={(e) => setConsultor(e.target.value as Consultor)}
          className="text-xs border border-gray-300 rounded-md px-2 py-1 bg-white text-gray-900 focus:outline-none focus:ring-2 focus:ring-purple-500"
        >
          {CONSULTORES.map((c) => (
            <option key={c} value={c}>{c}</option>
          ))}
        </select>
      </div>

      {loading && <CardSkeleton />}
      {error && <ErrorState msg={error} />}
      {data && !loading && (
        <div className="space-y-3">
          <p className="text-[11px] text-gray-500">Periodo: {data.periodo}</p>

          {/* KPIs */}
          <div className="grid grid-cols-3 gap-2">
            <div className="text-center p-2 bg-purple-50 rounded-lg">
              <p className="text-[10px] text-gray-500 leading-tight">Contactados</p>
              <p className="text-lg font-bold text-purple-700 tabular-nums">{data.clientes_contactados}</p>
            </div>
            <div className="text-center p-2 bg-green-50 rounded-lg">
              <p className="text-[10px] text-gray-500 leading-tight">Vendas</p>
              <p className="text-lg font-bold text-green-700 tabular-nums">{data.vendas_fechadas}</p>
            </div>
            <div className="text-center p-2 bg-blue-50 rounded-lg">
              <p className="text-[10px] text-gray-500 leading-tight">Volume R$</p>
              <p className="text-sm font-bold text-blue-700 tabular-nums">{formatBRL(data.valor_vendas)}</p>
            </div>
          </div>

          {/* Pipeline */}
          {data.pipeline.length > 0 && (
            <div>
              <p className="text-[10px] font-semibold text-gray-500 uppercase tracking-wider mb-1">
                Pipeline
              </p>
              <div className="flex flex-wrap gap-1.5">
                {data.pipeline.map((p) => (
                  <span key={p.estagio}
                    className="text-[10px] font-medium px-2 py-0.5 rounded-full bg-purple-100 text-purple-800">
                    {p.estagio}: {p.qtd}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Top clientes */}
          {data.top_clientes.length > 0 && (
            <div>
              <p className="text-[10px] font-semibold text-gray-500 uppercase tracking-wider mb-1">
                Top clientes da semana
              </p>
              <ul className="space-y-1">
                {data.top_clientes.map((c) => (
                  <li key={c.cnpj} className="flex items-start justify-between gap-2 text-xs">
                    <div className="min-w-0">
                      <p className="font-medium text-gray-900 truncate leading-tight">{c.nome}</p>
                      <p className="text-[11px] text-gray-500 leading-tight">{c.motivo}</p>
                    </div>
                    <span className="font-bold tabular-nums flex-shrink-0" style={{ color: '#8B5CF6' }}>
                      {c.score}
                    </span>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </AgentCard>
  );
}

// ---------------------------------------------------------------------------
// Pagina principal /ia
// ---------------------------------------------------------------------------

export default function CentralIAPage() {
  const [clienteSelecionado, setClienteSelecionado] = useState<ClienteRegistro | null>(null);

  const cnpj = clienteSelecionado?.cnpj ?? null;
  const nomeCliente = clienteSelecionado?.nome_fantasia ?? '';

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header da pagina */}
      <div className="bg-white border-b border-gray-200">
        <div className="px-6 py-5">
          <div className="flex items-start gap-3">
            <div
              className="w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0"
              style={{ backgroundColor: '#EDE9FE' }}
            >
              <svg className="w-5 h-5" fill="none" stroke="#7C3AED" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                  d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
              </svg>
            </div>
            <div>
              <h1 className="text-xl font-bold text-gray-900">Central de IA</h1>
              <p className="text-sm text-gray-500 mt-0.5">
                Inteligencia comercial para vender mais
              </p>
            </div>
          </div>

          {/* Busca de cliente */}
          <div className="mt-4 flex flex-col sm:flex-row items-start sm:items-center gap-3">
            <ClienteAutocomplete onSelect={setClienteSelecionado} />
            {clienteSelecionado && (
              <div className="flex items-center gap-2 text-sm text-gray-700">
                <span className="font-medium text-gray-900">{clienteSelecionado.nome_fantasia}</span>
                <span className="text-gray-400">|</span>
                <span className="text-gray-500 font-mono text-xs">{clienteSelecionado.cnpj}</span>
                <button
                  type="button"
                  onClick={() => setClienteSelecionado(null)}
                  className="text-gray-400 hover:text-gray-700 transition-colors"
                  aria-label="Limpar selecao de cliente"
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Grid de cards */}
      <div className="px-6 py-6">
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
          {/* Row 1 */}
          <CardBriefing cnpj={cnpj} />
          <CardMensagemWA cnpj={cnpj} nomeCliente={nomeCliente} />
          <CardChurn cnpj={cnpj} />

          {/* Row 2 */}
          <CardSugestaoProduto cnpj={cnpj} />
          <div className="md:col-span-2 xl:col-span-2">
            <CardResumoSemanal />
          </div>
        </div>
      </div>
    </div>
  );
}
