'use client';

import { useEffect, useState, useCallback, useMemo } from 'react';
import {
  fetchSinaleiro,
  fetchRedes,
  SinaleiroResponse,
  SinaleiroItem,
  SinaleiroResumo,
  RedeItem,
  RedesResponse,
  formatBRL,
  formatPercent,
} from '@/lib/api';
import ClienteDetalhe from '@/components/ClienteDetalhe';

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const TICKET_BENCHMARK = 525; // R$/loja/mês — benchmark de penetração de rede
const MESES_BENCHMARK = 11;   // período de apuração (mar/25–jan/26)

const COR_HEX: Record<string, string> = {
  VERDE: '#00B050',
  AMARELO: '#FFC000',
  VERMELHO: '#FF0000',
  ROXO: '#7030A0',
  LARANJA: '#FF8C00',
};

const COR_TEXT: Record<string, string> = {
  VERDE: '#fff',
  AMARELO: '#1a1a1a',
  VERMELHO: '#fff',
  ROXO: '#fff',
  LARANJA: '#fff',
};

const COR_BG_LIGHT: Record<string, string> = {
  VERDE: '#E8F5E9',
  AMARELO: '#FFF8E1',
  VERMELHO: '#FFEBEE',
  ROXO: '#F3E5F5',
  LARANJA: '#FFF3E0',
};

const COR_ORDER = ['VERDE', 'AMARELO', 'VERMELHO', 'ROXO'] as const;

// Sinaleiro color from penetration %
function sinaleiroCorFromPct(pct: number): 'VERDE' | 'AMARELO' | 'VERMELHO' | 'ROXO' {
  if (pct >= 60) return 'VERDE';
  if (pct >= 40) return 'AMARELO';
  if (pct >= 1) return 'VERMELHO';
  return 'ROXO';
}

function formatCnpj(cnpj: string): string {
  const d = cnpj.replace(/\D/g, '').padStart(14, '0');
  if (d.length !== 14) return cnpj;
  return `${d.slice(0, 2)}.${d.slice(2, 5)}.${d.slice(5, 8)}/${d.slice(8, 12)}-${d.slice(12)}`;
}

// ---------------------------------------------------------------------------
// Types for rede enriched
// ---------------------------------------------------------------------------

interface RedeEnriquecida extends RedeItem {
  fatPotencial: number;
  sinaleiroPct: number;
  gap_potencial: number;
  penetracaoLojas: number;
  sinCor: 'VERDE' | 'AMARELO' | 'VERMELHO' | 'ROXO';
  maturidade: string;
}

function enriquecerRede(r: RedeItem): RedeEnriquecida {
  const fatPotencial = r.total_lojas * TICKET_BENCHMARK * MESES_BENCHMARK;
  const sinaleiroPct = fatPotencial > 0 ? (r.fat_real / fatPotencial) * 100 : 0;
  const gap_potencial = fatPotencial - r.fat_real;
  // penetracao de lojas = clientes com venda / total lojas — approximate via distribuicao
  const comVenda = (r.distribuicao?.VERDE ?? 0) + (r.distribuicao?.AMARELO ?? 0) + (r.distribuicao?.LARANJA ?? 0);
  const penetracaoLojas = r.total_lojas > 0 ? (comVenda / r.total_lojas) * 100 : 0;
  const sinCor = sinaleiroCorFromPct(sinaleiroPct);

  let maturidade: string;
  if (sinaleiroPct >= 60) maturidade = 'JBP';
  else if (sinaleiroPct >= 40) maturidade = 'SELL OUT';
  else if (sinaleiroPct >= 10) maturidade = 'POSITIVAÇÃO';
  else if (r.fat_real > 0) maturidade = 'ATIVAÇÃO';
  else maturidade = 'PROSPECÇÃO';

  return { ...r, fatPotencial, sinaleiroPct, gap_potencial, penetracaoLojas, sinCor, maturidade };
}

// ---------------------------------------------------------------------------
// Acoes plan by color
// ---------------------------------------------------------------------------

const PLANO_ACAO: Record<string, { titulo: string; frequencia: string; canal: string; acoes: string[] }> = {
  VERDE: {
    titulo: 'Manutenção',
    frequencia: 'Mensal',
    canal: 'Reunião + BI',
    acoes: [
      'Reunião mensal de revisão de resultados',
      'Joint Business Plan (JBP) trimestral',
      'Acompanhamento de Sell Out e giro de estoque',
      'Proposta de expansão de mix e novas categorias',
    ],
  },
  AMARELO: {
    titulo: 'Atenção',
    frequencia: '1x/semana',
    canal: 'WhatsApp + Oferta',
    acoes: [
      'Contato semanal com oferta direcionada',
      'Análise de mix com oportunidade de cross-sell',
      'Ajuste de frequência de pedidos',
      'Apresentar comparativo com clientes VERDE da mesma rede',
    ],
  },
  VERMELHO: {
    titulo: 'Urgente',
    frequencia: '2x/semana',
    canal: 'Ligação + Visita',
    acoes: [
      'Ligar ou visitar 2x/semana até reativar',
      'Campanha de retorno com condição especial',
      'Identificar barreira de compra (mix, prazo, preço)',
      'Benchmark: apresentar case de clientes similares que compraram',
    ],
  },
  ROXO: {
    titulo: 'Prospecção',
    frequencia: '1x/semana',
    canal: 'WhatsApp + Ligação',
    acoes: [
      'WhatsApp + ligação 1x/semana para prospectar',
      'Mapear decisor de compras da loja',
      'Proposta de mix de entrada com kit reduzido',
      'Registrar touchpoints no CRM para histórico',
    ],
  },
};

// ---------------------------------------------------------------------------
// Main page
// ---------------------------------------------------------------------------

type Tab = 'dashboard' | 'redes' | 'acoes';

export default function SinaleiroPage() {
  const [activeTab, setActiveTab] = useState<Tab>('dashboard');

  // Carteira data
  const [data, setData] = useState<SinaleiroResponse | null>(null);
  const [loadingCarteira, setLoadingCarteira] = useState(true);
  const [errorCarteira, setErrorCarteira] = useState<string | null>(null);

  // Redes data
  const [redesData, setRedesData] = useState<RedesResponse | null>(null);
  const [loadingRedes, setLoadingRedes] = useState(false);
  const [errorRedes, setErrorRedes] = useState<string | null>(null);

  // Drill-down
  const [selectedCnpj, setSelectedCnpj] = useState<string | null>(null);

  // Rede expand
  const [expandedRede, setExpandedRede] = useState<string | null>(null);

  // Sort redes
  const [sortBy, setSortBy] = useState<'gap' | 'sinaleiro' | 'penetracao' | 'lojas'>('gap');

  // Filters (Tab 1)
  const [filtroCor, setFiltroCor] = useState<string>('');
  const [filtroConsultor, setFiltroConsultor] = useState<string>('');

  // Load carteira
  const loadCarteira = useCallback(() => {
    setLoadingCarteira(true);
    fetchSinaleiro({ limit: 500 })
      .then(setData)
      .catch((e: Error) => setErrorCarteira(e.message))
      .finally(() => setLoadingCarteira(false));
  }, []);

  useEffect(() => {
    loadCarteira();
  }, [loadCarteira]);

  // Load redes when tab opens
  useEffect(() => {
    if (activeTab === 'redes' && !redesData && !loadingRedes) {
      setLoadingRedes(true);
      fetchRedes()
        .then(setRedesData)
        .catch((e: Error) => setErrorRedes(e.message))
        .finally(() => setLoadingRedes(false));
    }
  }, [activeTab, redesData, loadingRedes]);

  // Derived
  const resumo: SinaleiroResumo[] = useMemo(() => {
    return [...(data?.resumo ?? [])].sort((a, b) => {
      const ai = COR_ORDER.indexOf(a.cor.toUpperCase() as typeof COR_ORDER[number]);
      const bi = COR_ORDER.indexOf(b.cor.toUpperCase() as typeof COR_ORDER[number]);
      return (ai === -1 ? 99 : ai) - (bi === -1 ? 99 : bi);
    });
  }, [data]);

  const itens: SinaleiroItem[] = useMemo(() => {
    let list = data?.itens ?? [];
    if (filtroCor) list = list.filter((i) => i.cor.toUpperCase() === filtroCor);
    if (filtroConsultor) list = list.filter((i) => i.consultor === filtroConsultor);
    return list;
  }, [data, filtroCor, filtroConsultor]);

  const consultores = useMemo(
    () => Array.from(new Set((data?.itens ?? []).map((i) => i.consultor).filter(Boolean))).sort(),
    [data]
  );

  const redesEnriquecidas: RedeEnriquecida[] = useMemo(() => {
    return (redesData?.redes ?? []).map(enriquecerRede);
  }, [redesData]);

  const sortedRedes = useMemo(() => {
    const sorted = [...redesEnriquecidas];
    if (sortBy === 'gap') sorted.sort((a, b) => b.gap_potencial - a.gap_potencial);
    else if (sortBy === 'sinaleiro') sorted.sort((a, b) => b.sinaleiroPct - a.sinaleiroPct);
    else if (sortBy === 'penetracao') sorted.sort((a, b) => b.penetracaoLojas - a.penetracaoLojas);
    else if (sortBy === 'lojas') sorted.sort((a, b) => b.total_lojas - a.total_lojas);
    return sorted;
  }, [redesEnriquecidas, sortBy]);

  // Totais redes
  const totaisRedes = useMemo(() => {
    const t = redesEnriquecidas.reduce(
      (acc, r) => ({
        lojas: acc.lojas + r.total_lojas,
        fatReal: acc.fatReal + r.fat_real,
        fatPotencial: acc.fatPotencial + r.fatPotencial,
        gap: acc.gap + r.gap_potencial,
      }),
      { lojas: 0, fatReal: 0, fatPotencial: 0, gap: 0 }
    );
    return {
      ...t,
      sinaleiroPct: t.fatPotencial > 0 ? (t.fatReal / t.fatPotencial) * 100 : 0,
    };
  }, [redesEnriquecidas]);

  // Itens agrupados para Plano de Ação
  const itensPorCor = useMemo(() => {
    const grouped: Record<string, SinaleiroItem[]> = { VERDE: [], AMARELO: [], VERMELHO: [], ROXO: [] };
    (data?.itens ?? []).forEach((item) => {
      const c = item.cor.toUpperCase();
      if (c in grouped) grouped[c].push(item);
    });
    return grouped;
  }, [data]);

  const TABS: { id: Tab; label: string }[] = [
    { id: 'dashboard', label: 'Dashboard' },
    { id: 'redes', label: 'Por Rede' },
    { id: 'acoes', label: 'Plano de Acao' },
  ];

  return (
    <div className="space-y-5 animate-fadeIn">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-gray-900">Sinaleiro de Penetracao</h1>
          <p className="text-sm text-gray-500 mt-0.5">
            {data
              ? `${data.total.toLocaleString('pt-BR')} clientes | Formula: Fat.Real / Potencial x 100`
              : 'Saude da carteira por faixa de penetracao'}
          </p>
        </div>
        <span className="px-3 py-1 rounded-full text-xs font-bold text-white" style={{ background: '#00B050' }}>
          VITAO
        </span>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 border-b border-gray-200">
        {TABS.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className="px-4 py-2 text-sm font-medium transition-colors"
            style={
              activeTab === tab.id
                ? { color: '#00B050', borderBottom: '2px solid #00B050', marginBottom: -1 }
                : { color: '#6B7280', borderBottom: '2px solid transparent', marginBottom: -1 }
            }
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* ─── TAB: DASHBOARD ─── */}
      {activeTab === 'dashboard' && (
        <div className="space-y-5 animate-fadeIn">
          {errorCarteira && <ErrorBanner message={errorCarteira} onRetry={loadCarteira} />}

          {/* KPI strip — 4 cores */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            {loadingCarteira
              ? Array.from({ length: 4 }).map((_, i) => (
                  <div key={i} className="rounded-xl border border-gray-200 p-4 h-28 bg-gray-50 animate-pulse" />
                ))
              : COR_ORDER.map((cor) => {
                  const item = resumo.find((r) => r.cor.toUpperCase() === cor);
                  const hex = COR_HEX[cor];
                  const isActive = filtroCor === cor;
                  return (
                    <button
                      key={cor}
                      onClick={() => setFiltroCor(isActive ? '' : cor)}
                      className="rounded-xl text-left transition-all duration-150 hover:shadow-md focus:outline-none"
                      style={{
                        border: isActive ? `2px solid ${hex}` : '1px solid #E5E7EB',
                        background: isActive ? hex + '14' : '#fff',
                        padding: '16px',
                        boxShadow: '0 1px 3px rgba(0,0,0,0.04)',
                      }}
                      aria-pressed={isActive}
                    >
                      <div className="flex items-center gap-2 mb-2">
                        <span
                          className="w-3 h-3 rounded-full flex-shrink-0"
                          style={{ background: hex }}
                          aria-hidden="true"
                        />
                        <span
                          className="text-[10px] font-bold uppercase tracking-wider"
                          style={{ color: hex }}
                          aria-label={`Sinaleiro ${cor.toLowerCase()}`}
                        >
                          {cor}
                        </span>
                      </div>
                      <p className="text-3xl font-bold text-gray-900 leading-tight">
                        {item ? item.count.toLocaleString('pt-BR') : '—'}
                      </p>
                      <p className="text-xs text-gray-400 mt-0.5">
                        {item ? formatPercent(item.pct) : '0%'} da carteira
                      </p>
                      {item && item.faturamento > 0 && (
                        <p className="text-xs font-semibold mt-1 truncate" style={{ color: hex }}>
                          {formatBRL(item.faturamento)}
                        </p>
                      )}
                    </button>
                  );
                })}
          </div>

          {/* Sinaleiro bar — distribuicao horizontal */}
          {!loadingCarteira && resumo.length > 0 && (
            <div
              className="rounded-xl p-5"
              style={{ border: '1px solid #C8E6C9', background: '#fff', boxShadow: '0 1px 3px rgba(0,0,0,0.04)' }}
            >
              <div className="flex items-center justify-between mb-3">
                <div>
                  <p className="text-sm font-bold text-gray-800">DISTRIBUICAO DO SINALEIRO</p>
                  <p className="text-[11px] text-gray-500">Participacao de cada cor na carteira total</p>
                </div>
                <div
                  className="px-4 py-1.5 rounded-full text-xs font-bold text-white"
                  style={{
                    background: COR_HEX[
                      sinaleiroCorFromPct(
                        resumo.find((r) => r.cor.toUpperCase() === 'VERDE')?.pct ?? 0
                      )
                    ],
                  }}
                >
                  {data?.total.toLocaleString('pt-BR')} clientes
                </div>
              </div>

              {/* Stacked bar */}
              <div className="flex rounded-lg overflow-hidden h-9 mb-2">
                {COR_ORDER.map((cor) => {
                  const item = resumo.find((r) => r.cor.toUpperCase() === cor);
                  const pct = item?.pct ?? 0;
                  if (pct === 0) return null;
                  return (
                    <div
                      key={cor}
                      className="relative flex items-center justify-center transition-all"
                      style={{ width: `${pct}%`, background: COR_HEX[cor] }}
                      title={`${cor}: ${formatPercent(pct)}`}
                    >
                      {pct > 8 && (
                        <span className="text-[10px] font-bold" style={{ color: COR_TEXT[cor] }}>
                          {formatPercent(pct, 0)}
                        </span>
                      )}
                    </div>
                  );
                })}
              </div>

              <div className="flex justify-between text-[10px] text-gray-500">
                <span style={{ color: '#7030A0' }}>ROXO &lt;1%</span>
                <span style={{ color: '#FF0000' }}>VERMELHO 1-40%</span>
                <span style={{ color: '#B8860B' }}>AMARELO 40-60%</span>
                <span style={{ color: '#00B050' }}>VERDE 60%+</span>
              </div>
            </div>
          )}

          {/* Filters row */}
          <div className="flex flex-wrap items-end gap-3">
            <div className="flex flex-col gap-1">
              <label className="text-[10px] font-semibold text-gray-500 uppercase tracking-wide">Cor</label>
              <select
                value={filtroCor}
                onChange={(e) => setFiltroCor(e.target.value)}
                className="h-8 border border-gray-300 rounded-lg px-2 text-xs text-gray-700 bg-white focus:outline-none focus:border-green-600"
              >
                <option value="">Todas</option>
                {COR_ORDER.map((cor) => (
                  <option key={cor} value={cor}>{cor}</option>
                ))}
              </select>
            </div>
            <div className="flex flex-col gap-1">
              <label className="text-[10px] font-semibold text-gray-500 uppercase tracking-wide">Consultor</label>
              <select
                value={filtroConsultor}
                onChange={(e) => setFiltroConsultor(e.target.value)}
                className="h-8 border border-gray-300 rounded-lg px-2 text-xs text-gray-700 bg-white focus:outline-none focus:border-green-600"
              >
                <option value="">Todos</option>
                {consultores.map((c) => (
                  <option key={c} value={c}>{c}</option>
                ))}
              </select>
            </div>
            {(filtroCor || filtroConsultor) && (
              <button
                onClick={() => { setFiltroCor(''); setFiltroConsultor(''); }}
                className="h-8 px-3 text-xs text-gray-500 hover:text-gray-800 border border-gray-200 rounded-lg transition-colors"
              >
                Limpar filtros
              </button>
            )}
            {(filtroCor || filtroConsultor) && (
              <span className="text-xs text-gray-500">
                {itens.length.toLocaleString('pt-BR')} registros
              </span>
            )}
          </div>

          {/* Ranking table */}
          <div
            className="rounded-xl overflow-hidden"
            style={{ border: '1px solid #E5E7EB', boxShadow: '0 1px 3px rgba(0,0,0,0.04)' }}
          >
            <div className="px-4 py-3 bg-white border-b border-gray-100 flex items-center justify-between">
              <h2 className="text-sm font-semibold text-gray-700">Ranking de Clientes</h2>
              <span className="text-xs text-gray-400">
                {loadingCarteira ? 'carregando...' : `${itens.length.toLocaleString('pt-BR')} clientes`}
              </span>
            </div>
            <div className="overflow-x-auto scrollbar-thin">
              {loadingCarteira ? (
                <TableSkeleton cols={9} rows={8} />
              ) : itens.length === 0 ? (
                <div className="py-12 text-center text-gray-400 text-sm">
                  Nenhum cliente encontrado com os filtros selecionados
                </div>
              ) : (
                <RankingTable itens={itens} onRowClick={setSelectedCnpj} />
              )}
            </div>
          </div>

          {/* Legenda */}
          <div className="rounded-xl p-4 text-xs space-y-1" style={{ background: '#E8F5E9', border: '1px solid #C8E6C9' }}>
            <p className="font-bold text-green-800">Calculo do Sinaleiro</p>
            <p className="text-green-700">
              Formula: <strong>(Fat.Real / Potencial) x 100</strong> — Potencial = Total_Lojas x R$525/mes x 11 meses
            </p>
            <p className="text-green-700">
              VERDE &ge;60% | AMARELO 40-60% | VERMELHO 1-40% | ROXO &lt;1%
            </p>
          </div>
        </div>
      )}

      {/* ─── TAB: POR REDE ─── */}
      {activeTab === 'redes' && (
        <div className="space-y-4 animate-fadeIn">
          {errorRedes && <ErrorBanner message={errorRedes} onRetry={() => { setErrorRedes(null); setRedesData(null); }} />}

          {/* Totais redes */}
          {!loadingRedes && redesEnriquecidas.length > 0 && (
            <div className="grid grid-cols-2 sm:grid-cols-5 gap-3">
              {[
                { label: 'LOJAS', value: totaisRedes.lojas.toLocaleString('pt-BR'), sub: `${redesEnriquecidas.length} redes`, color: '#1B5E20' },
                { label: 'FAT. REAL', value: formatBRL(totaisRedes.fatReal), sub: 'realizado', color: '#2E7D32', small: true },
                { label: 'POTENCIAL', value: formatBRL(totaisRedes.fatPotencial), sub: 'calculado', color: '#1B5E20', small: true },
                { label: 'GAP', value: formatBRL(totaisRedes.gap), sub: 'a capturar', color: '#FF0000', small: true },
                {
                  label: 'SINALEIRO',
                  value: formatPercent(totaisRedes.sinaleiroPct),
                  sub: sinaleiroCorFromPct(totaisRedes.sinaleiroPct),
                  color: COR_HEX[sinaleiroCorFromPct(totaisRedes.sinaleiroPct)],
                },
              ].map((k, i) => (
                <div
                  key={i}
                  className="rounded-xl p-4"
                  style={{
                    background: '#fff',
                    borderLeft: `4px solid ${k.color}`,
                    border: '1px solid #E5E7EB',
                    borderLeftWidth: 4,
                    borderLeftColor: k.color,
                    boxShadow: '0 1px 3px rgba(0,0,0,0.04)',
                  }}
                >
                  <div className="text-[10px] font-semibold text-gray-400 tracking-wider mb-1">{k.label}</div>
                  <div
                    className="font-extrabold leading-tight"
                    style={{ fontSize: k.small ? 16 : 24, color: k.color }}
                  >
                    {k.value}
                  </div>
                  <div className="text-[10px] text-gray-400 mt-1">{k.sub}</div>
                </div>
              ))}
            </div>
          )}

          {/* Sort buttons */}
          <div className="flex items-center gap-2 flex-wrap">
            <span className="text-xs text-gray-500">Ordenar:</span>
            {([
              { id: 'gap', label: 'Maior GAP' },
              { id: 'sinaleiro', label: 'Sinaleiro' },
              { id: 'penetracao', label: 'Penetracao' },
              { id: 'lojas', label: 'No. Lojas' },
            ] as { id: typeof sortBy; label: string }[]).map((s) => (
              <button
                key={s.id}
                onClick={() => setSortBy(s.id)}
                className="px-3 py-1.5 rounded-lg text-xs font-medium transition-colors"
                style={
                  sortBy === s.id
                    ? { background: '#00B050', color: '#fff', border: '1px solid #00B050' }
                    : { background: '#fff', color: '#6B7280', border: '1px solid #E5E7EB' }
                }
              >
                {s.label}
              </button>
            ))}
          </div>

          {/* Rede cards */}
          {loadingRedes
            ? Array.from({ length: 4 }).map((_, i) => (
                <div key={i} className="rounded-xl border border-gray-200 p-5 h-24 animate-pulse bg-gray-50" />
              ))
            : sortedRedes.length === 0
            ? (
                <div className="py-12 text-center text-gray-400 text-sm rounded-xl border border-gray-200">
                  Nenhuma rede encontrada. Verifique a conexao com o backend.
                </div>
              )
            : sortedRedes.map((r) => (
                <RedeCard
                  key={r.nome}
                  rede={r}
                  expanded={expandedRede === r.nome}
                  onToggle={() => setExpandedRede(expandedRede === r.nome ? null : r.nome)}
                />
              ))}
        </div>
      )}

      {/* ─── TAB: PLANO DE ACAO ─── */}
      {activeTab === 'acoes' && (
        <div className="space-y-4 animate-fadeIn">
          {loadingCarteira ? (
            Array.from({ length: 4 }).map((_, i) => (
              <div key={i} className="rounded-xl border border-gray-200 p-5 h-36 animate-pulse bg-gray-50" />
            ))
          ) : (
            <>
              {/* Summary header */}
              <div
                className="rounded-xl p-5"
                style={{ background: '#fff', border: '1px solid #C8E6C9', borderTop: '3px solid #00B050', boxShadow: '0 1px 3px rgba(0,0,0,0.04)' }}
              >
                <p className="text-base font-bold text-green-900">PLANO DE ACAO POR PRIORIDADE</p>
                <p className="text-xs text-gray-500 mt-1">
                  Baseado no sinaleiro de cada cliente — acoes diferenciadas por faixa de penetracao
                </p>
              </div>

              {/* Action card per color */}
              {COR_ORDER.map((cor) => {
                const plano = PLANO_ACAO[cor];
                const clientes = itensPorCor[cor] ?? [];
                const hex = COR_HEX[cor];
                const bgLight = COR_BG_LIGHT[cor];
                if (!plano) return null;
                return (
                  <div
                    key={cor}
                    className="rounded-xl p-5"
                    style={{
                      background: '#fff',
                      borderLeft: `5px solid ${hex}`,
                      border: '1px solid #E5E7EB',
                      borderLeftWidth: 5,
                      borderLeftColor: hex,
                      boxShadow: '0 1px 3px rgba(0,0,0,0.04)',
                    }}
                  >
                    {/* Header */}
                    <div className="flex items-start justify-between mb-4">
                      <div>
                        <div className="flex items-center gap-2 mb-1">
                          <span
                            className="w-3 h-3 rounded-full"
                            style={{ background: hex }}
                          />
                          <span className="text-sm font-bold text-gray-900">{cor}</span>
                          <span
                            className="px-2 py-0.5 rounded-full text-[10px] font-bold"
                            style={{ background: bgLight, color: hex }}
                          >
                            {plano.titulo}
                          </span>
                        </div>
                        <p className="text-xs text-gray-500">
                          {clientes.length.toLocaleString('pt-BR')} clientes | {plano.frequencia} | {plano.canal}
                        </p>
                      </div>
                      <div
                        className="text-3xl font-extrabold"
                        style={{ color: hex }}
                      >
                        {clientes.length.toLocaleString('pt-BR')}
                      </div>
                    </div>

                    {/* Actions grid */}
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 mb-4">
                      {plano.acoes.map((acao, j) => (
                        <div
                          key={j}
                          className="flex gap-2 px-3 py-2 rounded-lg"
                          style={{ background: bgLight, border: `1px solid ${hex}20` }}
                        >
                          <span className="text-[10px] mt-0.5 font-bold" style={{ color: hex }}>◆</span>
                          <span className="text-xs text-gray-700 leading-relaxed">{acao}</span>
                        </div>
                      ))}
                    </div>

                    {/* Top 5 clientes desta cor */}
                    {clientes.length > 0 && (
                      <div>
                        <p className="text-[10px] font-semibold text-gray-500 uppercase tracking-wide mb-2">
                          Top clientes por realizado
                        </p>
                        <div className="space-y-1">
                          {clientes
                            .slice()
                            .sort((a, b) => b.realizado - a.realizado)
                            .slice(0, 5)
                            .map((c) => (
                              <button
                                key={c.cnpj}
                                onClick={() => setSelectedCnpj(c.cnpj)}
                                className="w-full flex items-center justify-between px-3 py-1.5 rounded-lg text-left hover:opacity-80 transition-opacity"
                                style={{ background: bgLight, border: `1px solid ${hex}15` }}
                              >
                                <div className="flex items-center gap-2 min-w-0">
                                  <span className="text-xs font-medium text-gray-800 truncate">
                                    {c.nome_fantasia}
                                  </span>
                                  <span className="text-[10px] text-gray-400 flex-shrink-0">{c.uf}</span>
                                </div>
                                <span className="text-xs font-semibold flex-shrink-0 ml-2" style={{ color: hex }}>
                                  {formatBRL(c.realizado)}
                                </span>
                              </button>
                            ))}
                        </div>
                      </div>
                    )}
                  </div>
                );
              })}
            </>
          )}
        </div>
      )}

      {/* Drill-down */}
      {selectedCnpj && (
        <ClienteDetalhe
          cnpj={selectedCnpj}
          onClose={() => setSelectedCnpj(null)}
        />
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// RedeCard
// ---------------------------------------------------------------------------

function RedeCard({ rede, expanded, onToggle }: { rede: RedeEnriquecida; expanded: boolean; onToggle: () => void }) {
  const hex = COR_HEX[rede.sinCor];
  const bgLight = COR_BG_LIGHT[rede.sinCor];
  const matCor = rede.maturidade === 'JBP' ? '#2E7D32' : rede.maturidade === 'SELL OUT' ? '#B8860B' : rede.maturidade === 'POSITIVAÇÃO' ? '#FF0000' : rede.maturidade === 'ATIVAÇÃO' ? '#E65100' : '#7030A0';

  const DIST_LABELS = ['VERDE', 'AMARELO', 'LARANJA', 'VERMELHO', 'ROXO'] as const;
  const distArr = DIST_LABELS.map((k) => ({
    label: k,
    value: rede.distribuicao?.[k] ?? 0,
    hex: COR_HEX[k] ?? '#9E9E9E',
  }));

  return (
    <div
      className="rounded-xl cursor-pointer transition-shadow hover:shadow-md"
      style={{
        background: '#fff',
        borderLeft: `5px solid ${hex}`,
        border: '1px solid #E5E7EB',
        borderLeftWidth: 5,
        borderLeftColor: hex,
        padding: 20,
        boxShadow: '0 1px 3px rgba(0,0,0,0.04)',
      }}
      onClick={onToggle}
    >
      {/* Top row */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div
            className="w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold text-white flex-shrink-0"
            style={{ background: hex }}
          >
            {rede.sinCor[0]}
          </div>
          <div>
            <p className="text-sm font-bold text-gray-900">{rede.nome}</p>
            <p className="text-[11px] text-gray-500">
              {rede.consultor} &bull; {rede.total_lojas} lojas
            </p>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <div className="text-right">
            <div className="text-xl font-extrabold" style={{ color: hex }}>
              {formatPercent(rede.sinaleiroPct)}
            </div>
            <div className="text-[10px] text-gray-400">sinaleiro</div>
          </div>
          <span
            className="px-2.5 py-1 rounded-full text-[10px] font-bold"
            style={{ background: matCor + '18', color: matCor }}
          >
            {rede.maturidade}
          </span>
          <span className="text-gray-400 text-xs ml-1">{expanded ? '▲' : '▼'}</span>
        </div>
      </div>

      {/* Metrics strip */}
      <div className="grid grid-cols-2 sm:grid-cols-5 gap-2 mt-4">
        {[
          { l: 'Penetracao', v: formatPercent(rede.penetracaoLojas), c: rede.penetracaoLojas > 30 ? '#00B050' : '#E65100' },
          { l: 'Fat. Real', v: formatBRL(rede.fat_real), c: '#2E7D32' },
          { l: 'Potencial', v: formatBRL(rede.fatPotencial), c: '#1B5E20' },
          { l: 'GAP', v: formatBRL(rede.gap_potencial), c: '#FF0000' },
          { l: '% Ating. Meta', v: formatPercent(rede.pct_ating), c: COR_HEX[sinaleiroCorFromPct(rede.pct_ating)] },
        ].map((s, i) => (
          <div
            key={i}
            className="rounded-lg p-2"
            style={{ background: '#FAFAFA', border: '1px solid #E5E7EB' }}
          >
            <div className="text-[9px] text-gray-400">{s.l}</div>
            <div className="text-xs font-bold mt-0.5" style={{ color: s.c }}>{s.v}</div>
          </div>
        ))}
      </div>

      {/* Expanded detail */}
      {expanded && (
        <div
          className="mt-4 pt-4"
          style={{ borderTop: '1px solid #E5E7EB' }}
          onClick={(e) => e.stopPropagation()}
        >
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {/* Distribuicao por cor */}
            <div>
              <p className="text-[11px] font-bold text-green-700 mb-2">COMPOSICAO DA CARTEIRA</p>
              {distArr.map((d) => (
                <div key={d.label} className="flex items-center gap-2 mb-1.5">
                  <div className="w-14 text-[10px] font-bold flex-shrink-0" style={{ color: d.hex }}>
                    {d.label}
                  </div>
                  <div className="flex-1 h-3.5 rounded bg-gray-100 overflow-hidden">
                    <div
                      className="h-full rounded transition-all"
                      style={{
                        width: `${rede.total_lojas > 0 ? Math.max((d.value / rede.total_lojas) * 100, 1) : 0}%`,
                        background: d.hex + '80',
                      }}
                    />
                  </div>
                  <div className="w-14 text-[10px] text-gray-500 text-right flex-shrink-0">
                    {d.value} ({rede.total_lojas > 0 ? formatPercent((d.value / rede.total_lojas) * 100, 0) : '0%'})
                  </div>
                </div>
              ))}
            </div>

            {/* Dados comerciais */}
            <div>
              <p className="text-[11px] font-bold text-green-700 mb-2">DADOS COMERCIAIS</p>
              {[
                { l: 'Total Lojas', v: rede.total_lojas },
                { l: 'Fat. Real', v: formatBRL(rede.fat_real) },
                { l: 'FAT. Potencial', v: formatBRL(rede.fatPotencial) },
                { l: 'GAP a Capturar', v: formatBRL(rede.gap_potencial) },
                { l: 'Meta Atingida', v: formatPercent(rede.pct_ating) },
              ].map((d, j) => (
                <div
                  key={j}
                  className="flex justify-between py-1.5"
                  style={{ borderBottom: '1px solid #F5F5F5' }}
                >
                  <span className="text-xs text-gray-500">{d.l}</span>
                  <span className="text-xs font-semibold text-gray-800">{d.v}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Acao recomendada */}
          <div
            className="mt-4 p-4 rounded-lg"
            style={{ background: bgLight, borderLeft: `3px solid ${hex}` }}
          >
            <p className="text-[11px] font-bold mb-1" style={{ color: hex }}>
              ACAO RECOMENDADA — {rede.maturidade}
            </p>
            <p className="text-xs text-gray-700 leading-relaxed">
              {rede.maturidade === 'PROSPECÇÃO' &&
                'Mapear decisores da rede, preparar apresentacao institucional, oferecer mix de entrada com condicoes especiais.'}
              {rede.maturidade === 'ATIVAÇÃO' &&
                'Reativar inativos com campanha direcionada. Prospectar novas lojas com benchmark das que ja compraram.'}
              {rede.maturidade === 'POSITIVAÇÃO' &&
                `Consolidar base de compradores. Aumentar frequencia de pedidos. Meta: subir penetracao para 30%.`}
              {rede.maturidade === 'SELL OUT' &&
                'Implementar plano de Sell Out com giro, ajuste de mix e promocoes. Objetivo: subir de AMARELO para VERDE.'}
              {rede.maturidade === 'JBP' &&
                'Joint Business Plan completo: BI integrado, plano de negocio, acompanhamento mensal.'}
            </p>
          </div>

          {/* Top lojas */}
          {rede.lojas && rede.lojas.length > 0 && (
            <div className="mt-4">
              <p className="text-[11px] font-bold text-green-700 mb-2">
                TOP LOJAS ({rede.lojas.length} total)
              </p>
              <div className="overflow-x-auto">
                <table className="w-full text-xs">
                  <thead>
                    <tr style={{ background: '#FAFAFA' }}>
                      {['Nome', 'Cidade/UF', 'Fat.Real', '% Ating.', 'Cor'].map((h) => (
                        <th key={h} scope="col" className="px-2 py-1.5 text-left text-[10px] font-semibold text-gray-500 uppercase tracking-wide whitespace-nowrap">
                          {h}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {rede.lojas
                      .slice()
                      .sort((a, b) => b.fat_real - a.fat_real)
                      .slice(0, 10)
                      .map((loja) => {
                        const lojaCor = loja.cor?.toUpperCase() ?? 'ROXO';
                        const lojaHex = COR_HEX[lojaCor] ?? '#9E9E9E';
                        return (
                          <tr
                            key={loja.cnpj}
                            className="border-t border-gray-50 hover:bg-gray-50/50"
                          >
                            <td className="px-2 py-1.5 font-medium text-gray-800 max-w-[150px] truncate">
                              {loja.nome}
                            </td>
                            <td className="px-2 py-1.5 text-gray-500 whitespace-nowrap">
                              {loja.cidade && loja.uf ? `${loja.cidade}/${loja.uf}` : (loja.uf || '—')}
                            </td>
                            <td className="px-2 py-1.5 font-semibold text-gray-800 whitespace-nowrap">
                              {loja.fat_real > 0 ? formatBRL(loja.fat_real) : '—'}
                            </td>
                            <td className="px-2 py-1.5 whitespace-nowrap">
                              {loja.pct_ating > 0 ? (
                                <span className="font-semibold" style={{ color: COR_HEX[sinaleiroCorFromPct(loja.pct_ating)] }}>
                                  {formatPercent(loja.pct_ating)}
                                </span>
                              ) : '—'}
                            </td>
                            <td className="px-2 py-1.5 whitespace-nowrap">
                              <span
                                className="inline-block px-2 py-0.5 rounded text-[10px] font-bold"
                                style={{ background: lojaHex, color: COR_TEXT[lojaCor] ?? '#fff' }}
                              >
                                {lojaCor}
                              </span>
                            </td>
                          </tr>
                        );
                      })}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// RankingTable
// ---------------------------------------------------------------------------

function RankingTable({ itens, onRowClick }: { itens: SinaleiroItem[]; onRowClick: (cnpj: string) => void }) {
  const sorted = useMemo(
    () => [...itens].sort((a, b) => b.realizado - a.realizado),
    [itens]
  );

  return (
    <table className="w-full text-sm" role="table">
      <thead>
        <tr style={{ background: '#FAFAFA' }}>
          {['#', 'Cliente', 'UF', 'Consultor', 'Realizado', 'Meta', '% Ating.', 'Gap', 'Cor'].map((h) => (
            <th
              key={h}
              scope="col"
              className="px-3 py-2.5 text-left text-[10px] font-semibold text-gray-500 uppercase tracking-wide whitespace-nowrap"
            >
              {h}
            </th>
          ))}
        </tr>
      </thead>
      <tbody>
        {sorted.map((item, idx) => {
          const cor = item.cor.toUpperCase();
          const hex = COR_HEX[cor] ?? '#9E9E9E';
          const isNegativeGap = item.gap < 0;

          return (
            <tr
              key={item.cnpj}
              className="border-t border-gray-50 cursor-pointer transition-colors hover:bg-green-50/60"
              style={{ borderLeft: `3px solid ${hex}` }}
              onClick={() => onRowClick(item.cnpj)}
              title="Clique para ver detalhes do cliente"
            >
              {/* # */}
              <td className="px-3 py-2 text-xs text-gray-400 w-8">
                {idx + 1}
              </td>
              {/* Nome */}
              <td className="px-3 py-2 max-w-[180px]">
                <p className="text-xs font-medium text-gray-900 truncate">{item.nome_fantasia}</p>
                <p className="text-[10px] font-mono text-gray-400">{formatCnpj(item.cnpj)}</p>
              </td>
              {/* UF */}
              <td className="px-3 py-2 text-xs text-gray-600 whitespace-nowrap">{item.uf || '—'}</td>
              {/* Consultor */}
              <td className="px-3 py-2 text-xs text-gray-700 whitespace-nowrap">{item.consultor || '—'}</td>
              {/* Realizado */}
              <td className="px-3 py-2 font-mono text-xs font-semibold text-gray-800 whitespace-nowrap">
                {formatBRL(item.realizado)}
              </td>
              {/* Meta */}
              <td className="px-3 py-2 font-mono text-xs text-gray-600 whitespace-nowrap">
                {item.meta_anual > 0 ? formatBRL(item.meta_anual) : '—'}
              </td>
              {/* % Ating */}
              <td className="px-3 py-2 whitespace-nowrap">
                {item.meta_anual > 0 ? (
                  <div className="flex items-center gap-1.5">
                    <div className="w-10 h-1.5 bg-gray-100 rounded-full overflow-hidden">
                      <div
                        className="h-full rounded-full"
                        style={{
                          width: `${Math.min(100, item.pct_atingimento)}%`,
                          background: COR_HEX[sinaleiroCorFromPct(item.pct_atingimento)] ?? '#9E9E9E',
                        }}
                      />
                    </div>
                    <span
                      className="text-xs font-semibold"
                      style={{ color: COR_HEX[sinaleiroCorFromPct(item.pct_atingimento)] ?? '#9E9E9E' }}
                    >
                      {formatPercent(item.pct_atingimento)}
                    </span>
                  </div>
                ) : (
                  <span className="text-gray-400 text-xs">—</span>
                )}
              </td>
              {/* Gap */}
              <td
                className="px-3 py-2 font-mono text-xs whitespace-nowrap font-medium"
                style={{ color: item.meta_anual > 0 ? (isNegativeGap ? '#DC2626' : '#00B050') : '#9CA3AF' }}
              >
                {item.meta_anual > 0
                  ? isNegativeGap
                    ? `(${formatBRL(Math.abs(item.gap))})`
                    : `+${formatBRL(item.gap)}`
                  : '—'}
              </td>
              {/* Cor badge */}
              <td className="px-3 py-2 whitespace-nowrap">
                <span
                  role="status"
                  className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-bold uppercase"
                  style={{ background: hex, color: COR_TEXT[cor] ?? '#fff' }}
                  aria-label={`Sinaleiro ${cor.toLowerCase()} — penetracao ${cor === 'VERDE' ? 'acima de 60%' : cor === 'AMARELO' ? 'entre 40% e 60%' : cor === 'VERMELHO' ? 'entre 1% e 40%' : 'abaixo de 1%'}`}
                >
                  {cor}
                </span>
              </td>
            </tr>
          );
        })}
      </tbody>
    </table>
  );
}

// ---------------------------------------------------------------------------
// ErrorBanner
// ---------------------------------------------------------------------------

function ErrorBanner({ message, onRetry }: { message: string; onRetry: () => void }) {
  return (
    <div className="flex items-start gap-3 p-4 rounded-xl" style={{ background: '#FFEBEE', border: '1px solid #FFCDD2' }}>
      <svg className="w-5 h-5 text-red-500 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
          d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
      </svg>
      <div className="flex-1">
        <p className="text-sm font-semibold text-red-800">Erro ao carregar dados</p>
        <p className="text-xs text-red-600 mt-0.5">{message}</p>
      </div>
      <button
        type="button"
        onClick={onRetry}
        className="flex-shrink-0 px-3 py-1.5 text-xs font-semibold text-red-700 border border-red-300 rounded-lg hover:bg-red-50 transition-colors"
      >
        Tentar novamente
      </button>
    </div>
  );
}

// ---------------------------------------------------------------------------
// TableSkeleton
// ---------------------------------------------------------------------------

function TableSkeleton({ cols, rows }: { cols: number; rows: number }) {
  return (
    <table className="w-full">
      <thead>
        <tr style={{ background: '#FAFAFA' }}>
          {Array.from({ length: cols }).map((_, i) => (
            <th key={i} scope="col" className="px-3 py-2.5">
              <div className="h-3 bg-gray-200 animate-pulse rounded" />
            </th>
          ))}
        </tr>
      </thead>
      <tbody>
        {Array.from({ length: rows }).map((_, r) => (
          <tr key={r} className="border-t border-gray-50">
            {Array.from({ length: cols }).map((_, c) => (
              <td key={c} className="px-3 py-2.5">
                <div
                  className="h-3 bg-gray-100 animate-pulse rounded"
                  style={{ width: `${50 + ((r + c) % 5) * 10}%` }}
                />
              </td>
            ))}
          </tr>
        ))}
      </tbody>
    </table>
  );
}
