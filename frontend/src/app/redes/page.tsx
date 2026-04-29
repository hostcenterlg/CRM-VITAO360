'use client';

import { useState, useEffect, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { fetchJson } from '@/lib/api-internal';
import { formatBRL } from '@/lib/api';

// ---------------------------------------------------------------------------
// Tela Redes — sinaleiro por rede/franquia com accordion drill-down
// Acesso: admin + gerente
// ---------------------------------------------------------------------------

interface LojaRede {
  cnpj: string;
  nome: string;
  cidade: string;
  uf: string;
  fat_real: number;
  meta: number;
  pct_ating: number;
  cor: string;
}

interface RedeItem {
  nome: string;
  consultor: string;
  total_lojas: number;
  fat_real: number;
  meta: number;
  pct_ating: number;
  gap: number;
  cor: string;
  distribuicao: { VERDE: number; AMARELO: number; LARANJA: number; VERMELHO: number; ROXO: number };
  lojas: LojaRede[];
}

interface RedesResponse {
  total_redes: number;
  total_lojas: number;
  redes: RedeItem[];
}

// Mock data removido — R8: NUNCA exibir dados fabricados

// ---------------------------------------------------------------------------
// Helpers visuais
// ---------------------------------------------------------------------------

const COR_COLORS: Record<string, { bg: string; text: string; sigla: string }> = {
  VERDE:    { bg: '#00B050', text: '#fff',    sigla: 'V' },
  AMARELO:  { bg: '#FFC000', text: '#1a1a1a', sigla: 'A' },
  LARANJA:  { bg: '#FF8C00', text: '#fff',    sigla: 'La' },
  VERMELHO: { bg: '#FF0000', text: '#fff',    sigla: 'Vm' },
  ROXO:     { bg: '#7030A0', text: '#fff',    sigla: 'Rx' },
};

function CorBadge({ cor }: { cor: string }) {
  const cfg = COR_COLORS[cor] ?? { bg: '#e5e7eb', text: '#374151', sigla: '?' };
  return (
    <span className="inline-flex items-center px-2 py-0.5 text-xs font-semibold rounded uppercase"
      style={{ backgroundColor: cfg.bg, color: cfg.text }}>
      {cor}
    </span>
  );
}

// Cor de penetracao: ROXO <1%, VERMELHO 1-40%, AMARELO 40-60%, VERDE >60%
function penetracaoColor(pct: number): string {
  if (pct < 1) return '#7030A0';
  if (pct < 40) return '#FF0000';
  if (pct <= 60) return '#FFC000';
  return '#00B050';
}

function ProgressBar({ pct }: { pct: number | null | undefined }) {
  // Defensivo: backend pode retornar null em pct_ating (rede sem meta definida)
  const safePct = pct == null || !Number.isFinite(pct) ? 0 : pct;
  const color = penetracaoColor(safePct);
  return (
    <div className="flex items-center gap-2">
      <div className="flex-1 h-1.5 bg-gray-200 rounded-full overflow-hidden">
        <div
          className="h-full rounded-full transition-all"
          style={{ width: `${Math.min(safePct, 100)}%`, backgroundColor: color }}
        />
      </div>
      <span className="text-xs font-semibold tabular-nums" style={{ color }}>
        {safePct.toFixed(1)}%
      </span>
    </div>
  );
}

function DistribuicaoMini({ dist }: { dist: RedeItem['distribuicao'] }) {
  return (
    <div className="flex items-center gap-1.5 flex-wrap">
      {Object.entries(dist).map(([cor, qtd]) => {
        if (qtd === 0) return null;
        const cfg = COR_COLORS[cor];
        if (!cfg) return null;
        return (
          <span key={cor} className="flex items-center gap-0.5">
            <span className="inline-block w-2 h-2 rounded-full" style={{ backgroundColor: cfg.bg }} />
            <span className="text-xs text-gray-600">{qtd}{cfg.sigla}</span>
          </span>
        );
      })}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Pagina
// ---------------------------------------------------------------------------

export default function RedesPage() {
  const router = useRouter();
  const [data, setData] = useState<RedesResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [expandida, setExpandida] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetchJson<RedesResponse>('/api/redes');
      setData(res);
    } catch {
      setError('Erro ao carregar redes. Tente novamente.');
      setData(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { void load(); }, [load]);

  function toggleRede(nome: string) {
    setExpandida(prev => prev === nome ? null : nome);
  }

  const redes = data?.redes ?? [];
  const criticas = redes.filter(r => r.pct_ating < 40);

  // Media de penetracao
  const mediaPenetracao = redes.length > 0
    ? redes.reduce((acc, r) => acc + r.pct_ating, 0) / redes.length
    : 0;

  return (
    <div className="space-y-5 px-3 md:px-4 lg:px-6">
      {/* Titulo */}
      <div>
        <h1 className="text-lg font-bold text-gray-900">Redes e Franquias</h1>
        <p className="text-xs text-gray-500 mt-0.5">
          Monitoramento de penetracao e faturamento por rede/franquia
        </p>
      </div>

      {/* Cards de resumo */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
        <div className="bg-white rounded-xl border border-gray-200 p-4 shadow-sm flex flex-col gap-1"
          style={{ borderLeftColor: '#00B050', borderLeftWidth: '4px' }}>
          <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide">Total Redes</p>
          <p className="text-2xl font-bold text-gray-900">{loading ? '—' : (data?.total_redes ?? 0)}</p>
          <p className="text-xs text-gray-500">redes cadastradas</p>
        </div>
        <div className="bg-white rounded-xl border border-gray-200 p-4 shadow-sm flex flex-col gap-1"
          style={{ borderLeftColor: '#2563eb', borderLeftWidth: '4px' }}>
          <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide">Total Lojas</p>
          <p className="text-2xl font-bold text-gray-900">{loading ? '—' : (data?.total_lojas ?? 0)}</p>
          <p className="text-xs text-gray-500">unidades monitoradas</p>
        </div>
        <div className="bg-white rounded-xl border border-gray-200 p-4 shadow-sm flex flex-col gap-1"
          style={{ borderLeftColor: penetracaoColor(mediaPenetracao), borderLeftWidth: '4px' }}>
          <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide">Penetracao Media</p>
          <p className="text-2xl font-bold" style={{ color: penetracaoColor(mediaPenetracao) }}>
            {loading ? '—' : `${mediaPenetracao.toFixed(1)}%`}
          </p>
          <p className="text-xs text-gray-500">media das redes</p>
        </div>
      </div>

      {/* Erro */}
      {error && (
        <div className="px-4 py-3 bg-red-50 border border-red-200 rounded-lg flex items-center justify-between">
          <p className="text-sm text-red-700">{error}</p>
          <button onClick={() => void load()} className="text-xs font-semibold text-red-600 hover:text-red-800 underline">
            Tentar novamente
          </button>
        </div>
      )}

      {/* Alerta redes criticas */}
      {criticas.length > 0 && (
        <div className="flex items-start gap-3 p-3 bg-red-50 border border-red-200 rounded-lg">
          <svg className="w-4 h-4 text-red-600 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
              d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
          </svg>
          <p className="text-xs font-semibold text-red-800">
            {criticas.length} rede{criticas.length > 1 ? 's' : ''} critica{criticas.length > 1 ? 's' : ''} (abaixo de 40%):
            {' '}{criticas.map(r => r.nome).join(', ')}
          </p>
        </div>
      )}

      {/* Tabela principal */}
      <div className="bg-white rounded-xl border border-gray-200 overflow-hidden shadow-sm">
        {loading ? (
          <div className="flex items-center justify-center py-16">
            <div className="w-5 h-5 border-2 border-gray-300 border-t-green-600 rounded-full animate-spin" />
          </div>
        ) : redes.length === 0 ? (
          <div className="flex items-center justify-center py-16">
            <p className="text-xs text-gray-500">Nenhuma rede cadastrada.</p>
          </div>
        ) : (
          <div className="overflow-x-auto -mx-0">
            <div style={{ minWidth: 640 }}>
            {/* Header tabela */}
            <div className="border-b border-gray-200 bg-gray-50 px-4 py-2.5 grid grid-cols-9 gap-3 text-xs font-semibold text-gray-500 uppercase tracking-wide">
              <span className="col-span-2">Rede</span>
              <span>Consultor</span>
              <span className="text-right">Lojas</span>
              <span className="text-right">Fat Real</span>
              <span className="text-right">Meta</span>
              <span className="col-span-2">% Ating</span>
              <span className="text-right">Gap</span>
            </div>

            {redes.map(rede => {
              const isExpanded = expandida === rede.nome;
              const isCritica = rede.pct_ating < 40;

              return (
                <div key={rede.nome}>
                  {/* Linha da rede */}
                  <button
                    type="button"
                    onClick={() => toggleRede(rede.nome)}
                    className="w-full px-4 py-3 grid grid-cols-9 gap-3 items-center hover:bg-gray-50 transition-colors text-left focus:outline-none focus:ring-2 focus:ring-green-500 focus:ring-inset min-h-[44px]"
                    style={{ backgroundColor: isCritica ? '#FEF2F2' : undefined }}
                    aria-expanded={isExpanded}
                    aria-controls={`rede-lojas-${rede.nome}`}
                  >
                    {/* Nome + chevron */}
                    <div className="col-span-2 flex items-center gap-2">
                      <svg
                        className="w-3.5 h-3.5 text-gray-500 flex-shrink-0 transition-transform"
                        style={{ transform: isExpanded ? 'rotate(90deg)' : 'rotate(0deg)' }}
                        fill="none" stroke="currentColor" viewBox="0 0 24 24"
                      >
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                      </svg>
                      <div>
                        <span className="text-xs font-semibold text-gray-900">{rede.nome}</span>
                        {isCritica && (
                          <span className="ml-1.5 text-xs font-bold text-red-600">CRITICA</span>
                        )}
                      </div>
                    </div>

                    <span className="text-xs text-gray-600">{rede.consultor}</span>
                    <span className="text-xs text-gray-700 text-right tabular-nums">{rede.total_lojas}</span>
                    <span className="text-xs text-gray-900 font-medium text-right tabular-nums">{formatBRL(rede.fat_real)}</span>
                    <span className="text-xs text-gray-600 text-right tabular-nums">{formatBRL(rede.meta)}</span>

                    {/* Barra progresso */}
                    <div className="col-span-2">
                      <ProgressBar pct={rede.pct_ating} />
                    </div>

                    {/* Gap */}
                    <span
                      className="text-xs text-right tabular-nums font-medium"
                      style={{ color: rede.gap >= 0 ? '#00B050' : '#DC2626' }}
                    >
                      {rede.gap >= 0 ? '+' : ''}{formatBRL(rede.gap)}
                    </span>
                  </button>

                  {/* Distribuicao por cor (mini-barras) */}
                  <div className="px-4 pb-2 flex items-center gap-2">
                    <span className="text-xs text-gray-500">Distribuicao:</span>
                    <DistribuicaoMini dist={rede.distribuicao} />
                    <div className="ml-auto">
                      <CorBadge cor={rede.cor} />
                    </div>
                  </div>

                  {/* Accordion — lista de lojas */}
                  {isExpanded && (
                    <div
                      id={`rede-lojas-${rede.nome}`}
                      className="border-t border-gray-100 bg-gray-50"
                    >
                      {/* Header lojas */}
                      <div className="px-10 py-2 grid grid-cols-8 gap-3 text-xs font-semibold text-gray-500 uppercase tracking-wide">
                        <span className="col-span-2">CNPJ</span>
                        <span className="col-span-2">Nome Loja</span>
                        <span>Cidade</span>
                        <span className="text-right">Fat Real</span>
                        <span className="text-right">Meta</span>
                        <span>% / Cor</span>
                      </div>

                      {rede.lojas.map(loja => (
                        <button
                          key={loja.cnpj}
                          type="button"
                          onClick={() => router.push(`/carteira?busca=${loja.cnpj}`)}
                          className="w-full px-10 py-2 grid grid-cols-8 gap-3 items-center hover:bg-white transition-colors text-left focus:outline-none focus:ring-1 focus:ring-green-500 focus:ring-inset cursor-pointer min-h-[44px]"
                        >
                          <span className="col-span-2 text-xs font-mono text-gray-500">{loja.cnpj}</span>
                          <span className="col-span-2 text-xs text-gray-800">{loja.nome}</span>
                          <span className="text-xs text-gray-600">{loja.cidade}/{loja.uf}</span>
                          <span className="text-xs text-gray-900 text-right tabular-nums">{formatBRL(loja.fat_real)}</span>
                          <span className="text-xs text-gray-500 text-right tabular-nums">{formatBRL(loja.meta)}</span>
                          <div className="flex items-center gap-2">
                            <span
                              className="text-xs font-semibold tabular-nums"
                              style={{ color: penetracaoColor(loja.pct_ating) }}
                            >
                              {loja.pct_ating}%
                            </span>
                            <CorBadge cor={loja.cor} />
                          </div>
                        </button>
                      ))}

                      {/* Rodape distribuicao */}
                      <div className="px-10 py-2 border-t border-gray-100 flex items-center gap-2">
                        <span className="text-xs text-gray-500">Total lojas: {rede.total_lojas}</span>
                        <span className="text-xs text-gray-500">|</span>
                        <DistribuicaoMini dist={rede.distribuicao} />
                      </div>
                    </div>
                  )}

                  <div className="border-b border-gray-100" />
                </div>
              );
            })}
            </div>
          </div>
        )}
      </div>

      <p className="text-xs text-gray-500">
        Click numa rede para expandir a lista de lojas. Click numa loja para abrir a ficha do cliente.
        Redes com % atingimento abaixo de 40% sao destacadas como CRITICAS.
      </p>
    </div>
  );
}
