'use client';

import { useCallback, useEffect, useMemo, useState } from 'react';
import { fetchAgenda, AgendaItem } from '@/lib/api';
import StatusBadge from '@/components/StatusBadge';
import AtendimentoModal from '@/components/AtendimentoModal';

// ---------------------------------------------------------------------------
// Constantes de dominio
// ---------------------------------------------------------------------------

const CONSULTORES = ['LARISSA', 'MANU', 'JULIO', 'DAIANE'] as const;
type Consultor = (typeof CONSULTORES)[number];

// Prioridades que "pulam fila" — aparecem na secao PRIORITARIOS
const PRIORIDADES_URGENTES = new Set(['P0', 'P1', 'P3']);

// ---------------------------------------------------------------------------
// Helpers visuais
// ---------------------------------------------------------------------------

function formatDate(date: Date): string {
  const dias = ['Domingo', 'Segunda', 'Terca', 'Quarta', 'Quinta', 'Sexta', 'Sabado'];
  const meses = [
    'Janeiro', 'Fevereiro', 'Marco', 'Abril', 'Maio', 'Junho',
    'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro',
  ];
  return `${dias[date.getDay()]}, ${date.getDate()} de ${meses[date.getMonth()]} de ${date.getFullYear()}`;
}

// ---------------------------------------------------------------------------
// Sub-componentes
// ---------------------------------------------------------------------------

function SinaleiroDot({ value, size = 10 }: { value?: string; size?: number }) {
  const colorMap: Record<string, string> = {
    VERDE: '#00B050',
    AMARELO: '#FFC000',
    VERMELHO: '#FF0000',
    ROXO: '#7030A0',
    LARANJA: '#FF8C00',
  };
  const color = colorMap[(value ?? '').toUpperCase()] ?? '#D1D5DB';
  return (
    <span
      aria-label={`Sinaleiro: ${value ?? 'desconhecido'}`}
      style={{
        backgroundColor: color,
        width: size,
        height: size,
        borderRadius: '50%',
        display: 'inline-block',
        flexShrink: 0,
      }}
    />
  );
}

function ScoreBar({ score }: { score: number }) {
  const clamped = Math.min(100, Math.max(0, score));
  const color = clamped >= 70 ? '#00B050' : clamped >= 40 ? '#FFC000' : '#FF0000';
  return (
    <div className="flex items-center gap-1.5">
      <div className="w-14 bg-gray-100 rounded-full h-1.5 overflow-hidden">
        <div
          className="h-full rounded-full transition-all duration-500"
          style={{ width: `${clamped}%`, backgroundColor: color }}
        />
      </div>
      <span className="text-xs font-bold" style={{ color }}>{score}</span>
    </div>
  );
}

function FollowUpBadge({ followUp }: { followUp?: string }) {
  if (!followUp) return null;

  const upper = followUp.toUpperCase();
  if (upper.includes('HOJE') || upper.includes('VENCID')) {
    return (
      <span
        className="inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-bold text-white"
        style={{
          backgroundColor: '#FF0000',
          animation: upper.includes('HOJE') ? 'pulse 1.5s ease-in-out infinite' : undefined,
        }}
      >
        {followUp}
      </span>
    );
  }
  if (upper.includes('AMANHA')) {
    return (
      <span className="inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-bold text-gray-800 bg-yellow-100">
        {followUp}
      </span>
    );
  }
  return <span className="text-[11px] text-gray-500">{followUp}</span>;
}

function AgendaSkeleton() {
  return (
    <div className="space-y-3 p-4">
      {Array.from({ length: 6 }).map((_, i) => (
        <div
          key={i}
          className="h-28 bg-gray-100 rounded-lg"
          style={{ animation: 'pulse 1.5s ease-in-out infinite', animationDelay: `${i * 80}ms` }}
        />
      ))}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Card de item de agenda
// ---------------------------------------------------------------------------

interface AgendaCardProps {
  item: AgendaItem;
  concluido: boolean;
  onRegistrar: (item: AgendaItem) => void;
}

function AgendaCard({ item, concluido, onRegistrar }: AgendaCardProps) {
  const prio = (item.prioridade ?? '').toUpperCase();
  const sinal = (item.sinaleiro ?? '').toUpperCase();
  const isUrgente = PRIORIDADES_URGENTES.has(prio);

  // Cor da borda esquerda (por prioridade)
  const borderColorMap: Record<string, string> = {
    P0: '#FF0000',
    P1: '#FF6600',
    P2: '#FFC000',
    P3: '#FFFF00',
    P4: '#9CA3AF',
    P5: '#D1D5DB',
    P6: '#E5E7EB',
    P7: '#F3F4F6',
  };
  const borderColor = borderColorMap[prio] ?? '#E5E7EB';

  // Cor e background do bloco de acao (por sinaleiro)
  const acaoStyle: Record<string, { bg: string; border: string }> = {
    VERMELHO: { bg: '#FEF2F2', border: '#FF0000' },
    AMARELO:  { bg: '#FFFBEB', border: '#FFC000' },
    ROXO:     { bg: '#F5F3FF', border: '#7030A0' },
    VERDE:    { bg: '#F0FDF4', border: '#00B050' },
    LARANJA:  { bg: '#FFF7ED', border: '#FF8C00' },
  };
  const acao = acaoStyle[sinal] ?? { bg: '#F9FAFB', border: '#D1D5DB' };

  return (
    <article
      aria-label={`Item ${item.posicao}: ${item.nome_fantasia}`}
      className="relative rounded-lg border overflow-hidden transition-all duration-150"
      style={{
        borderColor: concluido ? '#E5E7EB' : (isUrgente ? borderColor : '#E5E7EB'),
        borderWidth: isUrgente && !concluido ? '2px' : '1px',
        borderLeftWidth: '4px',
        borderLeftColor: borderColor,
        backgroundColor: concluido ? '#F9FAFB' : '#FFFFFF',
        opacity: concluido ? 0.6 : 1,
        boxShadow: concluido ? 'none' : '0 1px 3px rgba(0,0,0,0.06)',
      }}
    >
      {/* Tag PRIORITARIO para P0/P1/P3 */}
      {isUrgente && !concluido && (
        <div
          className="absolute top-0 right-0 px-2 py-0.5 text-[9px] font-bold text-white rounded-bl-md"
          style={{ backgroundColor: borderColor }}
        >
          PRIORITARIO
        </div>
      )}

      <div className="p-3 pr-4">
        {/* Linha 1: posicao + nome + sinaleiro */}
        <div className="flex items-start justify-between gap-2 mb-1.5">
          <div className="flex items-center gap-2 min-w-0">
            {/* Numero da posicao */}
            <span className="flex-shrink-0 inline-flex items-center justify-center w-6 h-6 rounded-full bg-gray-100 text-gray-600 text-[11px] font-bold">
              {item.posicao}
            </span>

            {/* Badge de prioridade */}
            <StatusBadge value={item.prioridade} variant="prioridade" small />

            {/* Nome do cliente */}
            <h3 className="text-sm font-bold text-gray-900 truncate leading-tight">
              {item.nome_fantasia}
            </h3>
          </div>

          {/* Sinaleiro (dot + label) */}
          <div className="flex-shrink-0 flex items-center gap-1.5">
            <SinaleiroDot value={item.sinaleiro} />
            <span className="text-[11px] font-semibold" style={{ color: acaoStyle[sinal]?.border ?? '#6B7280' }}>
              {item.sinaleiro ?? '—'}
            </span>
          </div>
        </div>

        {/* Linha 2: metadados */}
        <div className="flex flex-wrap items-center gap-x-3 gap-y-0.5 mb-2 text-[11px] text-gray-500">
          {item.uf && <span className="font-medium text-gray-700">{item.uf}</span>}
          {item.situacao && <StatusBadge value={item.situacao} variant="situacao" small />}
          {item.temperatura && <StatusBadge value={item.temperatura} variant="situacao" small />}
          {item.dias_sem_compra !== undefined && (
            <span>{item.dias_sem_compra}d sem compra</span>
          )}
          {item.ciclo_medio !== undefined && (
            <span>Ciclo {item.ciclo_medio}d</span>
          )}
          {item.curva_abc && <StatusBadge value={item.curva_abc} variant="abc" small />}
        </div>

        {/* Bloco de ACAO SUGERIDA (destaque principal) */}
        {item.acao && (
          <div
            className="mb-2.5 px-3 py-2 rounded-r-md"
            style={{
              backgroundColor: acao.bg,
              borderLeft: `3px solid ${acao.border}`,
            }}
          >
            <p className="text-[10px] font-semibold text-gray-500 uppercase tracking-wide mb-0.5">
              Acao Prescrita
            </p>
            <p className="text-sm font-semibold text-gray-900 leading-snug">{item.acao}</p>
          </div>
        )}

        {/* Linha 3: tentativa + follow-up + score + botao */}
        <div className="flex items-center justify-between gap-2 flex-wrap">
          <div className="flex items-center gap-3 flex-wrap">
            {item.tentativa && (
              <span className="text-[11px] text-gray-600">
                <span className="font-semibold">Tentativa {item.tentativa}</span>
              </span>
            )}
            {item.follow_up && (
              <span className="flex items-center gap-1 text-[11px] text-gray-600">
                <span>FU:</span>
                <FollowUpBadge followUp={item.follow_up} />
              </span>
            )}
            <ScoreBar score={item.score} />
          </div>

          {/* Botao de acao ou checkmark de concluido */}
          {concluido ? (
            <span className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-md bg-green-50 text-green-700 text-xs font-semibold border border-green-200">
              <svg aria-hidden="true" className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
              </svg>
              Concluido
            </span>
          ) : (
            <button
              type="button"
              onClick={() => onRegistrar(item)}
              aria-label={`Registrar atendimento de ${item.nome_fantasia}`}
              className="flex-shrink-0 px-3 py-1.5 bg-green-600 hover:bg-green-700 text-white text-xs font-semibold rounded-md transition-all duration-150 hover:shadow-md hover:-translate-y-px focus:outline-none focus:ring-2 focus:ring-green-500 focus:ring-offset-1"
            >
              Registrar Atendimento
            </button>
          )}
        </div>
      </div>
    </article>
  );
}

// ---------------------------------------------------------------------------
// Barra de progresso do dia
// ---------------------------------------------------------------------------

interface ProgressBarProps {
  total: number;
  concluidos: number;
  consultor: string;
}

function ProgressBar({ total, concluidos, consultor }: ProgressBarProps) {
  const pct = total > 0 ? Math.round((concluidos / total) * 100) : 0;
  const progressColor =
    pct >= 80 ? '#00B050' :
    pct >= 50 ? '#FFC000' :
    pct >= 20 ? '#FF8C00' : '#E5E7EB';

  return (
    <div className="bg-white rounded-lg border border-gray-200 px-5 py-4 shadow-sm">
      <div className="flex items-center justify-between mb-2">
        <p className="text-sm font-medium text-gray-700">
          <span className="font-bold text-gray-900">{concluidos}</span> de{' '}
          <span className="font-bold text-gray-900">{total}</span> atendimentos concluidos hoje
          {pct > 0 && (
            <span className="ml-2 text-xs text-gray-500">
              ({pct}%)
            </span>
          )}
        </p>
        <p className="text-xs text-gray-500">{consultor}</p>
      </div>
      <div className="w-full h-2 bg-gray-100 rounded-full overflow-hidden">
        <div
          className="h-full rounded-full transition-all duration-500 ease-out"
          style={{ width: `${pct}%`, backgroundColor: progressColor }}
          role="progressbar"
          aria-valuenow={pct}
          aria-valuemin={0}
          aria-valuemax={100}
          aria-label={`${pct}% da agenda concluida`}
        />
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Pagina principal
// ---------------------------------------------------------------------------

export default function AgendaPage() {
  const [activeTab, setActiveTab] = useState<Consultor>('LARISSA');
  const [agendaByConsultor, setAgendaByConsultor] = useState<
    Partial<Record<Consultor, AgendaItem[]>>
  >({});
  const [loadingTabs, setLoadingTabs] = useState<Partial<Record<Consultor, boolean>>>({});
  const [errorTabs, setErrorTabs] = useState<Partial<Record<Consultor, string>>>({});

  // CNPJ de itens concluidos por consultor (Two-Base: so LOG, sem R$)
  const [concluidosByConsultor, setConcluidosByConsultor] = useState<
    Partial<Record<Consultor, Set<string>>>
  >({});

  // Modal de atendimento
  const [modalItem, setModalItem] = useState<AgendaItem | null>(null);

  // Filtros locais
  const [filtroPrioridade, setFiltroPrioridade] = useState<string>('');
  const [filtroSinaleiro, setFiltroSinaleiro] = useState<string>('');
  const [filtroBusca, setFiltroBusca] = useState<string>('');

  // ---------------------------------------------------------------------------
  // Carregamento de dados
  // ---------------------------------------------------------------------------

  const loadConsultor = useCallback((consultor: Consultor) => {
    if (agendaByConsultor[consultor] !== undefined) return;
    if (loadingTabs[consultor]) return;

    setLoadingTabs((prev) => ({ ...prev, [consultor]: true }));
    fetchAgenda(consultor)
      .then((data) =>
        setAgendaByConsultor((prev) => ({ ...prev, [consultor]: data }))
      )
      .catch((e: unknown) =>
        setErrorTabs((prev) => ({
          ...prev,
          [consultor]: e instanceof Error ? e.message : 'Erro desconhecido',
        }))
      )
      .finally(() =>
        setLoadingTabs((prev) => ({ ...prev, [consultor]: false }))
      );
  }, [agendaByConsultor, loadingTabs]);

  useEffect(() => {
    loadConsultor('LARISSA');
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const handleTabChange = (consultor: Consultor) => {
    setActiveTab(consultor);
    loadConsultor(consultor);
    // Limpa filtros ao trocar de aba
    setFiltroPrioridade('');
    setFiltroSinaleiro('');
    setFiltroBusca('');
  };

  // ---------------------------------------------------------------------------
  // Dados derivados
  // ---------------------------------------------------------------------------

  const todosItems = useMemo(
    () => agendaByConsultor[activeTab] ?? [],
    [agendaByConsultor, activeTab]
  );

  const isLoading = loadingTabs[activeTab] ?? false;
  const errorMsg = errorTabs[activeTab];

  const concluidosSet = useMemo(
    () => concluidosByConsultor[activeTab] ?? new Set<string>(),
    [concluidosByConsultor, activeTab]
  );

  // Aplicar filtros
  const itemsFiltrados = useMemo(() => {
    return todosItems.filter((item) => {
      if (filtroPrioridade && (item.prioridade ?? '').toUpperCase() !== filtroPrioridade) return false;
      if (filtroSinaleiro && (item.sinaleiro ?? '').toUpperCase() !== filtroSinaleiro) return false;
      if (filtroBusca) {
        const q = filtroBusca.toLowerCase();
        const cnpjNorm = item.cnpj.replace(/\D/g, '');
        if (!item.nome_fantasia.toLowerCase().includes(q) && !cnpjNorm.includes(q)) return false;
      }
      return true;
    });
  }, [todosItems, filtroPrioridade, filtroSinaleiro, filtroBusca]);

  // Separar prioritarios e regulares
  const prioritarios = useMemo(
    () => itemsFiltrados.filter((i) => PRIORIDADES_URGENTES.has((i.prioridade ?? '').toUpperCase())),
    [itemsFiltrados]
  );
  const regulares = useMemo(
    () => itemsFiltrados.filter((i) => !PRIORIDADES_URGENTES.has((i.prioridade ?? '').toUpperCase())),
    [itemsFiltrados]
  );

  // Contagem de concluidos
  const totalConcluidos = useMemo(
    () => todosItems.filter((i) => concluidosSet.has(i.cnpj)).length,
    [todosItems, concluidosSet]
  );

  // Avisos P0/P1
  const urgentesNaoPendentes = useMemo(
    () => itemsFiltrados.filter((i) => {
      const p = (i.prioridade ?? '').toUpperCase();
      return (p === 'P0' || p === 'P1') && !concluidosSet.has(i.cnpj);
    }),
    [itemsFiltrados, concluidosSet]
  );

  // ---------------------------------------------------------------------------
  // Handlers
  // ---------------------------------------------------------------------------

  const handleRegistrar = (item: AgendaItem) => {
    setModalItem(item);
  };

  const handleModalSaved = (cnpj: string) => {
    setConcluidosByConsultor((prev) => {
      const currentSet = prev[activeTab] ? new Set(prev[activeTab]) : new Set<string>();
      currentSet.add(cnpj);
      return { ...prev, [activeTab]: currentSet };
    });
  };

  const handleModalClose = () => {
    setModalItem(null);
  };

  const temFiltrosAtivos = !!(filtroPrioridade || filtroSinaleiro || filtroBusca);

  // ---------------------------------------------------------------------------
  // Render
  // ---------------------------------------------------------------------------

  const hoje = formatDate(new Date());

  return (
    <>
      <div className="space-y-4 max-w-4xl">
        {/* Cabecalho da pagina */}
        <div className="flex items-start justify-between gap-4">
          <div>
            <h1 className="text-lg font-bold text-gray-900">Agenda Comercial</h1>
            <p className="text-xs text-gray-500 mt-0.5">{hoje}</p>
          </div>
          {todosItems.length > 0 && (
            <div className="text-right flex-shrink-0">
              <p className="text-xs text-gray-500">Total na agenda</p>
              <p className="text-xl font-bold text-gray-900">{todosItems.length}</p>
            </div>
          )}
        </div>

        {/* Barra de progresso */}
        {todosItems.length > 0 && (
          <ProgressBar
            total={todosItems.length}
            concluidos={totalConcluidos}
            consultor={activeTab}
          />
        )}

        {/* Tabs de consultor */}
        <div className="bg-white rounded-lg border border-gray-200 shadow-sm overflow-hidden">
          {/* Tab bar */}
          <div className="flex border-b border-gray-200 overflow-x-auto">
            {CONSULTORES.map((c) => {
              const count = agendaByConsultor[c]?.length;
              const pendentes = count !== undefined
                ? count - ((concluidosByConsultor[c]?.size) ?? 0)
                : undefined;

              return (
                <button
                  key={c}
                  type="button"
                  onClick={() => handleTabChange(c)}
                  className={`
                    flex-shrink-0 px-5 py-3 text-sm font-medium border-b-2 transition-colors focus:outline-none focus:ring-2 focus:ring-inset focus:ring-green-500
                    ${activeTab === c
                      ? 'border-green-500 text-green-700 bg-green-50/50'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:bg-gray-50'
                    }
                  `}
                >
                  {c}
                  {pendentes !== undefined && (
                    <span
                      className={`ml-2 inline-flex items-center justify-center min-w-[20px] h-5 px-1.5 rounded-full text-[10px] font-bold ${
                        pendentes > 0
                          ? 'bg-gray-200 text-gray-700'
                          : 'bg-green-100 text-green-700'
                      }`}
                    >
                      {pendentes > 0 ? pendentes : '✓'}
                    </span>
                  )}
                </button>
              );
            })}
          </div>

          {/* Filtros */}
          <div className="flex flex-wrap items-center gap-2 px-4 py-3 bg-gray-50 border-b border-gray-100">
            {/* Busca */}
            <div className="relative flex-1 min-w-[180px]">
              <svg
                aria-hidden="true"
                className="absolute left-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-gray-400"
                fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}
              >
                <path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-4.35-4.35M17 11A6 6 0 1 1 5 11a6 6 0 0 1 12 0z" />
              </svg>
              <input
                type="search"
                placeholder="Buscar por nome ou CNPJ..."
                value={filtroBusca}
                onChange={(e) => setFiltroBusca(e.target.value)}
                aria-label="Buscar por nome ou CNPJ"
                className="w-full h-8 pl-8 pr-3 text-xs border border-gray-300 rounded-md bg-white text-gray-900 placeholder:text-gray-400 focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-green-500"
              />
            </div>

            {/* Filtro prioridade */}
            <select
              value={filtroPrioridade}
              onChange={(e) => setFiltroPrioridade(e.target.value)}
              aria-label="Filtrar por prioridade"
              className={`h-8 px-2 text-xs border rounded-md bg-white text-gray-900 focus:outline-none focus:ring-2 focus:ring-green-500 transition-colors ${
                filtroPrioridade ? 'border-green-500 bg-green-50' : 'border-gray-300'
              }`}
            >
              <option value="">Prioridade</option>
              {['P0', 'P1', 'P2', 'P3', 'P4', 'P5', 'P6', 'P7'].map((p) => (
                <option key={p} value={p}>{p}</option>
              ))}
            </select>

            {/* Filtro sinaleiro */}
            <select
              value={filtroSinaleiro}
              onChange={(e) => setFiltroSinaleiro(e.target.value)}
              aria-label="Filtrar por sinaleiro"
              className={`h-8 px-2 text-xs border rounded-md bg-white text-gray-900 focus:outline-none focus:ring-2 focus:ring-green-500 transition-colors ${
                filtroSinaleiro ? 'border-green-500 bg-green-50' : 'border-gray-300'
              }`}
            >
              <option value="">Sinaleiro</option>
              {['VERDE', 'AMARELO', 'LARANJA', 'VERMELHO', 'ROXO'].map((s) => (
                <option key={s} value={s}>{s}</option>
              ))}
            </select>

            {/* Limpar filtros */}
            {temFiltrosAtivos && (
              <button
                type="button"
                onClick={() => { setFiltroPrioridade(''); setFiltroSinaleiro(''); setFiltroBusca(''); }}
                className="h-8 px-3 text-xs text-gray-500 hover:text-gray-900 transition-colors focus:outline-none focus:ring-2 focus:ring-gray-400 rounded-md"
              >
                Limpar
              </button>
            )}
          </div>

          {/* Conteudo da aba */}
          <div className="p-4">
            {/* Aviso de urgentes */}
            {urgentesNaoPendentes.length > 0 && !isLoading && (
              <div className="mb-4 flex items-center gap-2.5 px-3.5 py-2.5 rounded-md border border-orange-200 bg-orange-50 text-sm">
                <svg aria-hidden="true" className="w-4 h-4 text-orange-500 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v2m0 4h.01M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z" />
                </svg>
                <p className="font-medium text-orange-800">
                  {urgentesNaoPendentes.length} cliente{urgentesNaoPendentes.length > 1 ? 's' : ''} P0/P1 aguardam. Prioridade maxima.
                </p>
              </div>
            )}

            {/* Erro */}
            {errorMsg && (
              <div role="alert" className="mb-4 px-4 py-3 bg-red-50 border border-red-200 rounded-md text-sm text-red-700">
                Erro ao carregar agenda de {activeTab}: {errorMsg}
              </div>
            )}

            {/* Loading */}
            {isLoading ? (
              <AgendaSkeleton />
            ) : itemsFiltrados.length === 0 && !errorMsg ? (
              <div className="py-14 text-center text-gray-400">
                <svg aria-hidden="true" className="w-10 h-10 mx-auto mb-3 text-gray-200" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
                </svg>
                <p className="text-sm font-medium">
                  {temFiltrosAtivos ? 'Nenhum item com esses filtros' : `Nenhum item na agenda de ${activeTab}`}
                </p>
                {temFiltrosAtivos && (
                  <button
                    type="button"
                    onClick={() => { setFiltroPrioridade(''); setFiltroSinaleiro(''); setFiltroBusca(''); }}
                    className="mt-2 text-sm text-green-600 hover:text-green-800 underline"
                  >
                    Limpar filtros
                  </button>
                )}
              </div>
            ) : (
              <div className="space-y-4">

                {/* Secao PRIORITARIOS */}
                {prioritarios.length > 0 && (
                  <section aria-label="Clientes prioritarios">
                    <div className="flex items-center gap-3 mb-3">
                      <div className="h-px flex-1 bg-red-200" />
                      <span className="flex-shrink-0 text-[11px] font-bold text-red-600 uppercase tracking-wider px-2 py-0.5 rounded border border-red-200 bg-red-50">
                        Prioritarios (pula fila)
                      </span>
                      <div className="h-px flex-1 bg-red-200" />
                    </div>

                    <div className="space-y-2">
                      {prioritarios.map((item) => (
                        <AgendaCard
                          key={item.cnpj}
                          item={item}
                          concluido={concluidosSet.has(item.cnpj)}
                          onRegistrar={handleRegistrar}
                        />
                      ))}
                    </div>
                  </section>
                )}

                {/* Secao REGULAR */}
                {regulares.length > 0 && (
                  <section aria-label="Clientes regulares">
                    {prioritarios.length > 0 && (
                      <div className="flex items-center gap-3 mb-3 mt-5">
                        <div className="h-px flex-1 bg-gray-200" />
                        <span className="flex-shrink-0 text-[11px] font-semibold text-gray-500 uppercase tracking-wider px-2 py-0.5 rounded border border-gray-200 bg-gray-50">
                          Regular
                        </span>
                        <div className="h-px flex-1 bg-gray-200" />
                      </div>
                    )}

                    <div className="space-y-2">
                      {regulares.map((item) => (
                        <AgendaCard
                          key={item.cnpj}
                          item={item}
                          concluido={concluidosSet.has(item.cnpj)}
                          onRegistrar={handleRegistrar}
                        />
                      ))}
                    </div>
                  </section>
                )}

                {/* Rodape com contagem */}
                {itemsFiltrados.length > 0 && (
                  <p className="text-center text-xs text-gray-400 pt-2">
                    {itemsFiltrados.length} cliente{itemsFiltrados.length > 1 ? 's' : ''} na agenda
                    {temFiltrosAtivos && ` (filtrado${itemsFiltrados.length > 1 ? 's' : ''})`}
                  </p>
                )}
              </div>
            )}
          </div>
        </div>

        {/* Legenda de prioridades */}
        <div className="bg-white rounded-lg border border-gray-200 p-4 shadow-sm">
          <h2 className="text-[10px] font-semibold text-gray-500 uppercase tracking-wide mb-3">
            Legenda de Prioridade
          </h2>
          <div className="flex flex-wrap gap-3">
            {[
              { code: 'P0', label: 'Critico — contato hoje',      bg: '#FF0000', text: '#fff' },
              { code: 'P1', label: 'Urgente — namoro novo',       bg: '#FF6600', text: '#fff' },
              { code: 'P2', label: 'Negociacao ativa',            bg: '#FFC000', text: '#1a1a1a' },
              { code: 'P3', label: 'Problema / suporte aberto',   bg: '#FFFF00', text: '#1a1a1a' },
              { code: 'P4', label: 'Medio',                       bg: '#9ca3af', text: '#fff' },
              { code: 'P5', label: 'Media-baixo',                 bg: '#d1d5db', text: '#374151' },
              { code: 'P7', label: 'Nutricao',                    bg: '#f3f4f6', text: '#9ca3af' },
            ].map((p) => (
              <div key={p.code} className="flex items-center gap-1.5">
                <span
                  className="inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-bold"
                  style={{ backgroundColor: p.bg, color: p.text }}
                >
                  {p.code}
                </span>
                <span className="text-[11px] text-gray-500">{p.label}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Modal de atendimento (fora do flow normal para overlay correto) */}
      {modalItem && (
        <AtendimentoModal
          item={modalItem}
          onClose={handleModalClose}
          onSaved={handleModalSaved}
        />
      )}
    </>
  );
}
