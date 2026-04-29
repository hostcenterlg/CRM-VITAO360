'use client';

import { useCallback, useEffect, useMemo, useRef, useState, TouchEvent } from 'react';
import {
  fetchAgenda,
  gerarAgenda,
  getResumoSemanal,
  enviarWhatsApp,
  fetchWhatsAppStatus,
  AgendaItem,
  ResumoSemanalResponse,
  WhatsAppStatus,
  WhatsAppEnviarResponse,
} from '@/lib/api';
import AtendimentoModal from '@/components/AtendimentoModal';
import { StatusPill } from '@/components/ui/StatusPill';
import { CurvaPill } from '@/components/ui/CurvaPill';
import { PriorityPill } from '@/components/ui/PriorityPill';
import { ScoreBar } from '@/components/ui/ScoreBar';
import { ProgressBar } from '@/components/ui/ProgressBar';
import { Tabs } from '@/components/ui/Tabs';
import { Sinaleiro } from '@/components/ui/Sinaleiro';
import TarefasPanel from '@/components/TarefasPanel';

// Tipo para a tab de nivel superior da pagina Agenda
type AgendaPageTab = 'compromissos' | 'tarefas';

// ---------------------------------------------------------------------------
// Constantes de dominio
// ---------------------------------------------------------------------------

const CONSULTORES = ['MANU', 'LARISSA', 'DAIANE', 'JULIO', 'OUTROS'] as const;
type Consultor = (typeof CONSULTORES)[number];

// Prioridades que "pulam fila" — aparecem na secao PRIORITARIOS
// P2 = NEGOCIACAO ATIVA: incluso como urgente
const PRIORIDADES_URGENTES = new Set(['P0', 'P1', 'P2', 'P3']);

// ---------------------------------------------------------------------------
// Helpers visuais
// ---------------------------------------------------------------------------

function formatDate(date: Date): string {
  const dias = ['Domingo', 'Segunda-feira', 'Terca-feira', 'Quarta-feira', 'Quinta-feira', 'Sexta-feira', 'Sabado'];
  const meses = [
    'Janeiro', 'Fevereiro', 'Marco', 'Abril', 'Maio', 'Junho',
    'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro',
  ];
  return `${dias[date.getDay()]}, ${date.getDate()} de ${meses[date.getMonth()]} de ${date.getFullYear()}`;
}

/** Retorna descrição textual do sinaleiro para exibir ao lado do dot */
function getSinaleiroDescricao(cor?: string): string {
  const key = (cor ?? '').toLowerCase();
  switch (key) {
    case 'verde':    return 'Cliente saudável';
    case 'amarelo':  return 'Atenção, frequência caindo';
    case 'laranja':  return 'Risco, ciclo vencendo';
    case 'vermelho': return 'Crítico, possível perda';
    case 'roxo':     return 'Cliente especial';
    default:         return 'Sem dados';
  }
}

// ---------------------------------------------------------------------------
// Sub-componentes auxiliares
// ---------------------------------------------------------------------------

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

// ---------------------------------------------------------------------------
// Modal rapido de envio WhatsApp a partir da agenda
// ---------------------------------------------------------------------------

interface WhatsAppAgendaModalProps {
  item: AgendaItem;
  waStatus: WhatsAppStatus | null;
  onClose: () => void;
}

function WhatsAppAgendaModal({ item, waStatus, onClose }: WhatsAppAgendaModalProps) {
  const [mensagem, setMensagem] = useState(item.acao ?? '');
  const [enviando, setEnviando] = useState(false);
  const [resultado, setResultado] = useState<WhatsAppEnviarResponse | null>(null);
  const [erro, setErro] = useState<string | null>(null);

  const podeSendEscrever = waStatus?.configurado && waStatus.alguma_conectada;

  const handleEnviar = async () => {
    if (!mensagem.trim()) return;
    setEnviando(true);
    setErro(null);
    setResultado(null);
    try {
      const res = await enviarWhatsApp(item.cnpj, mensagem.trim());
      setResultado(res);
      if (!res.enviado && res.erro) {
        setErro(res.erro);
      }
    } catch (e: unknown) {
      setErro(e instanceof Error ? e.message : 'Erro ao enviar mensagem');
    } finally {
      setEnviando(false);
    }
  };

  // Fechar com ESC
  useEffect(() => {
    const handler = (e: KeyboardEvent) => { if (e.key === 'Escape') onClose(); };
    document.addEventListener('keydown', handler);
    return () => document.removeEventListener('keydown', handler);
  }, [onClose]);

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4"
      role="dialog"
      aria-modal="true"
      aria-label={`Enviar WhatsApp para ${item.nome_fantasia}`}
    >
      {/* Overlay */}
      <div
        className="absolute inset-0 bg-black/40"
        onClick={onClose}
        aria-hidden="true"
      />

      {/* Modal */}
      <div className="relative w-full max-w-md bg-white rounded-xl shadow-xl overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between px-4 py-3 border-b border-gray-100 bg-gray-50">
          <div className="flex items-center gap-2 min-w-0">
            <div className="flex-shrink-0 w-8 h-8 rounded-full bg-green-100 flex items-center justify-center">
              <svg className="w-4 h-4 text-green-700" fill="currentColor" viewBox="0 0 24 24">
                <path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347z" />
                <path d="M12 0C5.373 0 0 5.373 0 12c0 2.139.558 4.144 1.535 5.879L.057 23.55a.5.5 0 00.608.608l5.693-1.479A11.952 11.952 0 0012 24c6.627 0 12-5.373 12-12S18.627 0 12 0zm0 22c-1.96 0-3.799-.56-5.354-1.527l-.383-.231-3.979 1.034 1.054-3.867-.252-.4A9.956 9.956 0 012 12C2 6.477 6.477 2 12 2s10 4.477 10 10-4.477 10-10 10z" />
              </svg>
            </div>
            <div className="min-w-0">
              <p className="text-sm font-bold text-gray-900 truncate">{item.nome_fantasia}</p>
              <p className="text-[10px] text-gray-400 font-mono">{item.cnpj}</p>
            </div>
          </div>
          <button
            type="button"
            onClick={onClose}
            aria-label="Fechar modal"
            className="flex-shrink-0 p-1.5 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-md transition-colors"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Corpo */}
        <div className="p-4 space-y-3">
          {/* Status WA */}
          {waStatus && (
            <div className={`flex items-center gap-1.5 text-[11px] font-medium px-2 py-1.5 rounded-md ${
              waStatus.alguma_conectada
                ? 'bg-green-50 text-green-700'
                : 'bg-gray-50 text-gray-500'
            }`}>
              <span
                className="w-2 h-2 rounded-full flex-shrink-0"
                style={{ backgroundColor: waStatus.alguma_conectada ? '#00A651' : '#9CA3AF' }}
              />
              {waStatus.configurado
                ? (waStatus.alguma_conectada ? 'WhatsApp conectado — pronto para envio' : 'WhatsApp desconectado')
                : 'WhatsApp nao configurado'}
            </div>
          )}

          {/* Acao prescrita como contexto */}
          {item.acao && (
            <div className="px-3 py-2 bg-gray-50 rounded-md border border-gray-100">
              <p className="text-[10px] text-gray-400 uppercase font-semibold tracking-wide mb-0.5">Acao prescrita</p>
              <p className="text-xs text-gray-700">{item.acao}</p>
            </div>
          )}

          {/* Campo de mensagem */}
          <div className="space-y-1">
            <label className="text-xs font-medium text-gray-700" htmlFor="wa-mensagem-agenda">
              Mensagem WhatsApp
            </label>
            <textarea
              id="wa-mensagem-agenda"
              rows={4}
              value={mensagem}
              onChange={(e) => setMensagem(e.target.value)}
              placeholder="Digite ou edite a mensagem para enviar..."
              disabled={resultado?.enviado}
              className="w-full p-3 text-xs border border-gray-200 rounded-lg bg-white text-gray-800 resize-none focus:outline-none focus:ring-2 focus:ring-green-500 leading-relaxed disabled:bg-gray-50 disabled:text-gray-500"
            />
            <p className="text-[10px] text-gray-400 text-right">{mensagem.length}/4096</p>
          </div>

          {/* Feedback */}
          {erro && (
            <p className="text-xs text-red-600 bg-red-50 border border-red-200 rounded-md px-3 py-2">
              {erro}
            </p>
          )}
          {resultado?.enviado && (
            <p className="text-xs text-green-700 bg-green-50 border border-green-200 rounded-md px-3 py-2">
              Mensagem enviada com sucesso via WhatsApp
              {resultado.numero ? ` para ${resultado.numero}` : ''}.
            </p>
          )}
        </div>

        {/* Footer */}
        <div className="px-4 py-3 border-t border-gray-100 flex items-center justify-end gap-2">
          <button
            type="button"
            onClick={onClose}
            className="px-3 py-1.5 text-xs font-medium text-gray-600 hover:text-gray-900 hover:bg-gray-50 rounded-md transition-colors focus:outline-none focus:ring-2 focus:ring-gray-400"
          >
            {resultado?.enviado ? 'Fechar' : 'Cancelar'}
          </button>
          {!resultado?.enviado && (
            <button
              type="button"
              onClick={handleEnviar}
              disabled={enviando || !mensagem.trim() || !podeSendEscrever}
              className="inline-flex items-center gap-1.5 px-4 py-1.5 text-xs font-semibold text-white rounded-md transition-all hover:opacity-90 focus:outline-none focus:ring-2 focus:ring-green-500 focus:ring-offset-1 disabled:opacity-50"
              style={{ backgroundColor: '#00A651' }}
            >
              {enviando ? (
                <>
                  <span className="w-3 h-3 border-2 border-white/40 border-t-white rounded-full animate-spin" />
                  Enviando...
                </>
              ) : (
                'Enviar WhatsApp'
              )}
            </button>
          )}
        </div>
      </div>
    </div>
  );
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
// Card de item de agenda — layout reformulado (ETAPA 4)
// ---------------------------------------------------------------------------

// Threshold em px para considerar um swipe esquerda valido
const SWIPE_THRESHOLD = 100;

interface AgendaCardProps {
  item: AgendaItem;
  idx: number;
  concluido: boolean;
  onRegistrar: (item: AgendaItem) => void;
  onWhatsApp?: (item: AgendaItem) => void;
}

function AgendaCard({ item, idx, concluido, onRegistrar, onWhatsApp }: AgendaCardProps) {
  const prio = (item.prioridade ?? '').toUpperCase();
  const sinalCor = (item.sinaleiro ?? '').toLowerCase();
  const isUrgente = PRIORIDADES_URGENTES.has(prio);

  // ---------------------------------------------------------------------------
  // Swipe state — touch events nativos, sem bibliotecas externas
  // ---------------------------------------------------------------------------
  const [swipeOffset, setSwipeOffset] = useState(0);
  const [swipeRevealed, setSwipeRevealed] = useState(false);
  const touchStartX = useRef<number>(0);
  const touchStartY = useRef<number>(0);
  const isDragging = useRef(false);

  function handleTouchStart(e: TouchEvent<HTMLDivElement>) {
    touchStartX.current = e.touches[0].clientX;
    touchStartY.current = e.touches[0].clientY;
    isDragging.current = false;
  }

  function handleTouchMove(e: TouchEvent<HTMLDivElement>) {
    const dx = e.touches[0].clientX - touchStartX.current;
    const dy = e.touches[0].clientY - touchStartY.current;

    // If vertical scroll is dominant, do not intercept
    if (!isDragging.current && Math.abs(dy) > Math.abs(dx)) return;

    if (Math.abs(dx) > 5) {
      isDragging.current = true;
    }

    if (!isDragging.current) return;

    // Allow left-swipe only (negative dx) unless already revealed (allow right to close)
    if (swipeRevealed) {
      const newOffset = Math.min(0, -SWIPE_THRESHOLD + dx);
      setSwipeOffset(newOffset);
    } else {
      const newOffset = Math.min(0, dx);
      setSwipeOffset(newOffset);
    }
  }

  function handleTouchEnd() {
    if (!isDragging.current) return;
    isDragging.current = false;

    if (swipeRevealed) {
      if (swipeOffset > -SWIPE_THRESHOLD / 2) {
        setSwipeOffset(0);
        setSwipeRevealed(false);
      } else {
        setSwipeOffset(-SWIPE_THRESHOLD);
        setSwipeRevealed(true);
      }
    } else {
      if (swipeOffset < -SWIPE_THRESHOLD / 2) {
        setSwipeOffset(-SWIPE_THRESHOLD);
        setSwipeRevealed(true);
      } else {
        setSwipeOffset(0);
        setSwipeRevealed(false);
      }
    }
  }

  function handleSwipeClose() {
    setSwipeOffset(0);
    setSwipeRevealed(false);
  }

  return (
    <div
      className="relative overflow-hidden rounded-lg"
      onTouchStart={concluido ? undefined : handleTouchStart}
      onTouchMove={concluido ? undefined : handleTouchMove}
      onTouchEnd={concluido ? undefined : handleTouchEnd}
    >
      {/* Swipe action buttons — revealed behind card on left swipe */}
      {!concluido && (
        <div
          className="absolute inset-y-0 right-0 flex items-stretch"
          aria-hidden={!swipeRevealed}
          style={{ width: SWIPE_THRESHOLD }}
        >
          {/* Adiar */}
          <button
            type="button"
            tabIndex={swipeRevealed ? 0 : -1}
            onClick={() => { handleSwipeClose(); onRegistrar(item); }}
            className="flex-1 flex flex-col items-center justify-center gap-0.5 bg-yellow-500 text-white text-[10px] font-bold"
            aria-label={`Adiar ${item.nome_fantasia}`}
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            Adiar
          </button>
          {/* Concluir */}
          <button
            type="button"
            tabIndex={swipeRevealed ? 0 : -1}
            onClick={() => { handleSwipeClose(); onRegistrar(item); }}
            className="flex-1 flex flex-col items-center justify-center gap-0.5 bg-green-600 text-white text-[10px] font-bold"
            aria-label={`Registrar atendimento de ${item.nome_fantasia}`}
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
            </svg>
            Feito
          </button>
        </div>
      )}

      {/* Card deslizavel */}
      <article
        aria-label={`Item ${idx + 1}: ${item.nome_fantasia}`}
        className="bg-white rounded-lg border border-gray-200 p-5 hover:shadow-sm transition-shadow"
        style={{
          transform: `translateX(${swipeOffset}px)`,
          transition: isDragging.current ? 'none' : 'transform 0.2s ease-out',
          opacity: concluido ? 0.6 : 1,
        }}
      >
        {/* Tag PRIORITARIO para P0/P1/P3 */}
        {isUrgente && !concluido && (
          <div
            className="absolute top-0 right-0 px-2 py-0.5 text-[9px] font-bold text-white rounded-bl-md"
            style={{ backgroundColor: prio === 'P0' ? '#FF0000' : prio === 'P1' ? '#FF6600' : prio === 'P2' ? '#FFC000' : '#FFFF00', color: prio === 'P3' ? '#1a1a1a' : '#fff' }}
          >
            PRIORITARIO
          </div>
        )}

        {/* Linha 1: número + nome + prioridade */}
        <div className="flex items-start justify-between mb-3">
          <div className="min-w-0 pr-2">
            <span className="text-xs font-medium text-gray-500">#{idx + 1}</span>
            <h3 className="text-base font-semibold text-gray-900 mt-1 leading-snug">
              {item.nome_fantasia}
            </h3>
          </div>
          <PriorityPill prioridade={item.prioridade ?? ''} />
        </div>

        {/* Linha 2: badges horizontais + score */}
        <div className="flex items-center gap-2 mb-3 flex-wrap">
          {item.situacao && <StatusPill status={item.situacao} />}
          {item.temperatura && <StatusPill status={item.temperatura} />}
          {item.curva_abc && <CurvaPill curva={item.curva_abc} />}
          <span className="text-sm text-gray-600 ml-auto flex items-center gap-1">
            Score:
            <ScoreBar score={item.score ?? 0} showLabel={false} className="w-20" />
            <span className="font-semibold text-gray-800">{(item.score ?? 0).toFixed(1)}</span>
          </span>
        </div>

        {/* Linha 3: sinaleiro com descrição */}
        <div className="text-sm text-gray-600 mb-3 flex items-center gap-2">
          <span className="text-gray-500">Sinaleiro:</span>
          <Sinaleiro cor={sinalCor} size="md" />
          <span className="text-gray-500 italic text-xs">{getSinaleiroDescricao(item.sinaleiro)}</span>
        </div>

        {/* Bloco de ACAO SUGERIDA */}
        {item.acao && (
          <div className="mb-3 px-3 py-2.5 rounded-r-md bg-gray-50 border-l-4 border-gray-300">
            <p className="text-[10px] font-bold text-gray-500 uppercase tracking-widest mb-1 flex items-center gap-1">
              <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5}
                  d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
              Acao Prescrita
            </p>
            <p className="text-sm font-semibold text-gray-900 leading-snug">{item.acao}</p>
          </div>
        )}

        {/* Metadados adicionais: follow-up + tentativa */}
        {(item.follow_up || item.tentativa) && (
          <div className="flex flex-wrap items-center gap-3 mb-3 text-[11px] text-gray-500">
            {item.tentativa && (
              <span>Tentativa <span className="font-semibold text-gray-700">{item.tentativa}</span></span>
            )}
            {item.follow_up && (
              <span className="flex items-center gap-1">
                FU: <FollowUpBadge followUp={item.follow_up} />
              </span>
            )}
          </div>
        )}

        {/* Linha 4: botões com ícones ou badge de concluído */}
        {concluido ? (
          <span className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-md bg-green-50 text-green-700 text-xs font-semibold border border-green-200">
            <svg aria-hidden="true" className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
            </svg>
            Concluido
          </span>
        ) : (
          <div className="flex gap-2">
            {onWhatsApp && (
              <button
                type="button"
                onClick={() => onWhatsApp(item)}
                aria-label={`Enviar WhatsApp para ${item.nome_fantasia}`}
                className="flex-1 inline-flex items-center justify-center gap-2 px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg font-medium text-sm transition-colors"
              >
                <span>📱</span> WhatsApp
              </button>
            )}
            <button
              type="button"
              onClick={() => onRegistrar(item)}
              aria-label={`Registrar atendimento de ${item.nome_fantasia}`}
              className="flex-1 inline-flex items-center justify-center gap-2 px-4 py-2 bg-vitao-green hover:bg-vitao-darkgreen text-white rounded-lg font-medium text-sm transition-colors"
            >
              <span>✅</span> Registrar Atendimento
            </button>
          </div>
        )}
      </article>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Resumo Semanal IA
// ---------------------------------------------------------------------------

const CONSULTORES_RESUMO = ['LARISSA', 'MANU', 'DAIANE', 'JULIO'] as const;

function ResumoSemanalIA({ consultorAtivo }: { consultorAtivo: string }) {
  const [aberto, setAberto] = useState(false);
  const [consultorSelecionado, setConsultorSelecionado] = useState(consultorAtivo);
  const [resumo, setResumo] = useState<ResumoSemanalResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [erro, setErro] = useState<string | null>(null);

  // Sincroniza consultor selecionado com a aba ativa (so se ainda nao foi alterado manualmente)
  const alteradoManualmente = useRef(false);
  useEffect(() => {
    if (!alteradoManualmente.current) {
      setConsultorSelecionado(consultorAtivo);
    }
  }, [consultorAtivo]);

  const handleGerar = async () => {
    setLoading(true);
    setErro(null);
    try {
      const data = await getResumoSemanal(consultorSelecionado);
      setResumo(data);
    } catch (e: unknown) {
      setErro(e instanceof Error ? e.message : 'Erro ao gerar resumo');
    } finally {
      setLoading(false);
    }
  };

  const metricaColor = (val: number, limiteAlerta: number) =>
    val >= limiteAlerta ? '#FF0000' : '#374151';

  // TODO Wave 5: implementar resumo IA quando endpoint pronto
  // Enquanto endpoint não tiver dados reais, o componente é exibido somente quando
  // o usuário clica em "Gerar Resumo" e recebe resposta com conteúdo.
  // Se não houver dados (resumo null e sem loading), não renderizar o accordion.
  if (!aberto && !resumo && !loading && !erro) {
    return (
      <button
        type="button"
        onClick={() => setAberto(true)}
        className="w-full flex items-center justify-between px-4 py-3 bg-white rounded-xl border border-gray-200 shadow-sm hover:bg-gray-50 transition-colors text-left"
      >
        <div className="flex items-center gap-2">
          <svg
            aria-hidden="true"
            className="w-4 h-4 flex-shrink-0"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
            strokeWidth={2}
            style={{ color: '#00B050' }}
          >
            <path strokeLinecap="round" strokeLinejoin="round"
              d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
          </svg>
          <span className="text-xs sm:text-sm font-semibold text-gray-600 uppercase tracking-wider">
            Resumo Semanal IA
          </span>
        </div>
        <svg
          className="w-4 h-4 text-gray-400 flex-shrink-0"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
          aria-hidden="true"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>
    );
  }

  return (
    <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
      {/* Header colapsavel */}
      <button
        type="button"
        onClick={() => setAberto((v) => !v)}
        className="w-full flex items-center justify-between px-4 py-3 bg-gray-50 hover:bg-gray-100 transition-colors text-left"
        aria-expanded={aberto}
      >
        <div className="flex items-center gap-2">
          <svg
            aria-hidden="true"
            className="w-4 h-4 flex-shrink-0"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
            strokeWidth={2}
            style={{ color: '#00B050' }}
          >
            <path strokeLinecap="round" strokeLinejoin="round"
              d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
          </svg>
          <span className="text-xs sm:text-sm font-semibold text-gray-600 uppercase tracking-wider">
            Resumo Semanal IA
          </span>
        </div>
        <svg
          className={`w-4 h-4 text-gray-400 flex-shrink-0 transition-transform duration-200 ${aberto ? 'rotate-180' : ''}`}
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
          aria-hidden="true"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>

      {/* Corpo colapsavel */}
      <div
        className={`transition-all duration-200 overflow-hidden ${aberto ? 'max-h-[2000px] opacity-100' : 'max-h-0 opacity-0'}`}
        aria-hidden={!aberto}
      >
        <div className="px-4 py-4 space-y-4">
          {/* Controles: dropdown consultor + botao gerar */}
          <div className="flex flex-wrap items-center gap-3">
            <div className="flex items-center gap-2">
              <label
                htmlFor="resumo-consultor-select"
                className="text-xs text-gray-600 font-medium flex-shrink-0"
              >
                Consultor:
              </label>
              <select
                id="resumo-consultor-select"
                value={consultorSelecionado}
                onChange={(e) => {
                  alteradoManualmente.current = true;
                  setConsultorSelecionado(e.target.value);
                  setResumo(null);
                  setErro(null);
                }}
                className="h-8 px-2 text-xs border border-gray-300 rounded-md bg-white text-gray-900 focus:outline-none focus:ring-2 focus:ring-green-500"
              >
                {CONSULTORES_RESUMO.map((c) => (
                  <option key={c} value={c}>{c}</option>
                ))}
              </select>
            </div>

            <button
              type="button"
              onClick={handleGerar}
              disabled={loading}
              className="inline-flex items-center gap-1.5 px-4 py-1.5 text-xs font-semibold text-white rounded-md transition-all hover:opacity-90 focus:outline-none focus:ring-2 focus:ring-green-500 focus:ring-offset-1 disabled:opacity-50"
              style={{ backgroundColor: '#00B050' }}
            >
              {loading ? (
                <>
                  <span className="w-3 h-3 border-2 border-white/40 border-t-white rounded-full animate-spin" />
                  Gerando...
                </>
              ) : (
                'Gerar Resumo'
              )}
            </button>
          </div>

          {/* Erro */}
          {erro && (
            <p className="text-xs text-red-600 bg-red-50 border border-red-200 rounded-md px-3 py-2">
              {erro}
            </p>
          )}

          {/* Resultado */}
          {resumo && (
            <div className="space-y-4">
              {!resumo.ia_configurada && (
                <p className="text-[10px] text-amber-600 bg-amber-50 border border-amber-200 rounded px-2 py-1 italic">
                  IA nao configurada — resumo baseado em regras locais
                </p>
              )}

              {/* Cards de metricas */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
                <div className="bg-gray-50 border border-gray-100 rounded-lg px-3 py-2 text-center">
                  <p className="text-[10px] text-gray-500 font-medium uppercase tracking-wide">Carteira</p>
                  <p className="text-xl font-bold text-gray-900 mt-0.5 tabular-nums">
                    {resumo.metricas.total_carteira}
                  </p>
                  <p className="text-[10px] text-gray-400">clientes</p>
                </div>

                <div className="bg-gray-50 border border-gray-100 rounded-lg px-3 py-2 text-center">
                  <p className="text-[10px] text-gray-500 font-medium uppercase tracking-wide">Vendas Semana</p>
                  <p
                    className="text-xl font-bold mt-0.5 tabular-nums"
                    style={{ color: '#00B050' }}
                  >
                    {resumo.metricas.vendas_semana_qtd}
                  </p>
                  <p className="text-[10px] text-gray-400">pedidos</p>
                </div>

                <div className="bg-gray-50 border border-gray-100 rounded-lg px-3 py-2 text-center">
                  <p className="text-[10px] text-gray-500 font-medium uppercase tracking-wide">Em Risco</p>
                  <p
                    className="text-xl font-bold mt-0.5 tabular-nums"
                    style={{ color: metricaColor(resumo.metricas.clientes_em_risco, 5) }}
                  >
                    {resumo.metricas.clientes_em_risco}
                  </p>
                  <p className="text-[10px] text-gray-400">clientes</p>
                </div>

                <div className="bg-gray-50 border border-gray-100 rounded-lg px-3 py-2 text-center">
                  <p className="text-[10px] text-gray-500 font-medium uppercase tracking-wide">FU Vencidos</p>
                  <p
                    className="text-xl font-bold mt-0.5 tabular-nums"
                    style={{ color: metricaColor(resumo.metricas.followups_vencidos, 3) }}
                  >
                    {resumo.metricas.followups_vencidos}
                  </p>
                  <p className="text-[10px] text-gray-400">follow-ups</p>
                </div>
              </div>

              {/* Texto do resumo IA */}
              <div className="bg-green-50 border border-green-100 rounded-lg p-3">
                <p className="text-[10px] font-semibold text-green-700 uppercase tracking-wide mb-1.5">
                  Analise IA — {resumo.consultor} — {resumo.periodo}
                </p>
                <p className="text-xs text-gray-800 whitespace-pre-wrap leading-relaxed">
                  {resumo.resumo}
                </p>
              </div>
            </div>
          )}

          {/* Estado vazio (ainda nao gerado) */}
          {!resumo && !loading && !erro && (
            <p className="text-xs text-gray-400 italic text-center py-2">
              Clique em &quot;Gerar Resumo&quot; para ver a analise da semana de {consultorSelecionado}.
            </p>
          )}
        </div>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Pagina principal
// ---------------------------------------------------------------------------

export default function AgendaPage() {
  // Tab de nivel superior: Compromissos (agenda) ou Tarefas
  // Abre na tab com mais itens pendentes para hoje — determinado apos carregamento inicial
  const [pageTab, setPageTab] = useState<AgendaPageTab>('compromissos');
  const [tarefasHojeCount, setTarefasHojeCount] = useState<number>(0);
  const pageTabSetByUser = useRef(false);

  const [activeTab, setActiveTab] = useState<Consultor>('LARISSA');
  const [agendaByConsultor, setAgendaByConsultor] = useState<
    Partial<Record<Consultor, AgendaItem[]>>
  >({});
  const [loadingTabs, setLoadingTabs] = useState<Partial<Record<Consultor, boolean>>>({});
  const [errorTabs, setErrorTabs] = useState<Partial<Record<Consultor, string>>>({});
  const [gerandoAgenda, setGerandoAgenda] = useState(false);

  // CNPJ de itens concluidos por consultor (Two-Base: so LOG, sem R$)
  const [concluidosByConsultor, setConcluidosByConsultor] = useState<
    Partial<Record<Consultor, Set<string>>>
  >({});

  // Modal de atendimento
  const [modalItem, setModalItem] = useState<AgendaItem | null>(null);

  // Modal WhatsApp rapido
  const [waModalItem, setWaModalItem] = useState<AgendaItem | null>(null);
  const [waStatus, setWaStatus] = useState<WhatsAppStatus | null>(null);

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
    // Carregar status WhatsApp uma vez ao montar
    fetchWhatsAppStatus()
      .then(setWaStatus)
      .catch(() => setWaStatus(null));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Selecionar automaticamente a tab com mais itens pendentes hoje
  // (so na primeira renderizacao — nao sobrescreve escolha manual do usuario)
  useEffect(() => {
    if (pageTabSetByUser.current) return;
    const compromissosLarissa = agendaByConsultor['LARISSA']?.length ?? 0;
    if (tarefasHojeCount > compromissosLarissa && tarefasHojeCount > 0) {
      setPageTab('tarefas');
    }
  }, [tarefasHojeCount, agendaByConsultor]);

  const handleTabChange = (consultor: string) => {
    const c = consultor as Consultor;
    setActiveTab(c);
    loadConsultor(c);
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
        const cnpjNorm = (item.cnpj ?? '').replace(/\D/g, '');
        if (!(item.nome_fantasia ?? '').toLowerCase().includes(q) && !cnpjNorm.includes(q)) return false;
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

  // Tabs para o componente Tabs global
  const tabsVendedores = useMemo(() =>
    CONSULTORES.map((c) => {
      const count = agendaByConsultor[c]?.length;
      const pendentes = count !== undefined
        ? count - ((concluidosByConsultor[c]?.size) ?? 0)
        : undefined;
      return {
        id: c,
        label: c.charAt(0) + c.slice(1).toLowerCase(),
        count: pendentes,
      };
    }),
    [agendaByConsultor, concluidosByConsultor]
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

  // Gerar nova agenda via backend
  const handleGerarAgenda = async () => {
    setGerandoAgenda(true);
    try {
      await gerarAgenda();
      // Recarregar agenda do consultor ativo
      setAgendaByConsultor((prev) => {
        const next = { ...prev };
        delete next[activeTab];
        return next;
      });
      setLoadingTabs((prev) => ({ ...prev, [activeTab]: false }));
      loadConsultor(activeTab);
    } catch {
      // Silently fail — user still sees current data
    } finally {
      setGerandoAgenda(false);
    }
  };

  const handleWhatsApp = (item: AgendaItem) => {
    setWaModalItem(item);
  };

  const handleWhatsAppClose = () => {
    setWaModalItem(null);
  };

  const temFiltrosAtivos = !!(filtroPrioridade || filtroSinaleiro || filtroBusca);

  // ---------------------------------------------------------------------------
  // Render
  // ---------------------------------------------------------------------------

  const hoje = formatDate(new Date());
  const pctConcluido = todosItems.length > 0
    ? Math.round((totalConcluidos / todosItems.length) * 100)
    : 0;

  // Contagem de compromissos hoje (para badge na tab e logica de tab ativa)
  const compromissosHoje = todosItems.length;

  return (
    <>
      <div className="space-y-3 sm:space-y-4 w-full px-0">
        {/* Cabecalho da pagina */}
        <div className="flex items-start justify-between gap-3">
          <div className="min-w-0">
            <h1 className="text-xl sm:text-2xl lg:text-3xl font-bold text-gray-900">Agenda</h1>
            <p className="text-sm sm:text-base text-gray-500 mt-0.5 truncate">
              {hoje}
              {(compromissosHoje > 0 || tarefasHojeCount > 0) && (
                <span className="ml-2 text-xs text-gray-400">
                  {compromissosHoje > 0 && `${compromissosHoje} compromisso${compromissosHoje !== 1 ? 's' : ''}`}
                  {compromissosHoje > 0 && tarefasHojeCount > 0 && ' · '}
                  {tarefasHojeCount > 0 && `${tarefasHojeCount} task${tarefasHojeCount !== 1 ? 's' : ''}`}
                </span>
              )}
            </p>
          </div>
          <div className="flex items-center gap-2 sm:gap-3 flex-shrink-0">
            {todosItems.length > 0 && (
              <div className="hidden sm:block text-right">
                <p className="text-xs sm:text-sm text-gray-500">Total na agenda</p>
                <p className="text-xl sm:text-2xl font-bold text-gray-900">{todosItems.length}</p>
              </div>
            )}
            <button
              type="button"
              onClick={handleGerarAgenda}
              disabled={gerandoAgenda}
              className="min-h-11 flex items-center gap-2 px-3 sm:px-4 py-2 text-sm font-semibold text-white rounded-lg
                         transition-all hover:opacity-90 active:scale-[0.98]
                         focus:outline-none focus:ring-2 focus:ring-green-500 focus:ring-offset-1
                         disabled:opacity-60 disabled:cursor-not-allowed"
              style={{ backgroundColor: '#00B050' }}
            >
              {gerandoAgenda ? (
                <>
                  <span className="w-4 h-4 border-2 border-white/40 border-t-white rounded-full animate-spin" />
                  Gerando...
                </>
              ) : (
                <>
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                      d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                  </svg>
                  Gerar Agenda
                </>
              )}
            </button>
          </div>
        </div>

        {/* Tabs de nivel superior: Compromissos | Tarefas */}
        <div className="flex gap-1 bg-white border border-gray-200 rounded-lg p-1 w-full sm:w-fit overflow-x-auto">
          <button
            type="button"
            onClick={() => { pageTabSetByUser.current = true; setPageTab('compromissos'); }}
            className={`
              flex items-center gap-1.5 px-4 py-2.5 sm:py-2 min-h-[44px] sm:min-h-0 rounded-md text-sm font-medium transition-all whitespace-nowrap
              ${pageTab === 'compromissos' ? 'text-white shadow-sm' : 'text-gray-500 hover:text-gray-800 hover:bg-gray-50'}
            `}
            style={pageTab === 'compromissos' ? { backgroundColor: '#00B050' } : {}}
          >
            <svg className="w-4 h-4 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
            </svg>
            Compromissos
            {compromissosHoje > 0 && (
              <span
                className="inline-flex items-center justify-center min-w-[18px] h-[18px] px-1 rounded-full text-[10px] font-bold"
                style={pageTab === 'compromissos'
                  ? { backgroundColor: 'rgba(255,255,255,0.3)', color: '#fff' }
                  : { backgroundColor: '#00B05018', color: '#00B050' }}
              >
                {compromissosHoje}
              </span>
            )}
          </button>
          <button
            type="button"
            onClick={() => { pageTabSetByUser.current = true; setPageTab('tarefas'); }}
            className={`
              flex items-center gap-1.5 px-4 py-2.5 sm:py-2 min-h-[44px] sm:min-h-0 rounded-md text-sm font-medium transition-all whitespace-nowrap
              ${pageTab === 'tarefas' ? 'text-white shadow-sm' : 'text-gray-500 hover:text-gray-800 hover:bg-gray-50'}
            `}
            style={pageTab === 'tarefas' ? { backgroundColor: '#00B050' } : {}}
          >
            <svg className="w-4 h-4 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4" />
            </svg>
            Tarefas
            {tarefasHojeCount > 0 && (
              <span
                className="inline-flex items-center justify-center min-w-[18px] h-[18px] px-1 rounded-full text-[10px] font-bold"
                style={pageTab === 'tarefas'
                  ? { backgroundColor: 'rgba(255,255,255,0.3)', color: '#fff' }
                  : { backgroundColor: '#FFC00020', color: '#b45309' }}
              >
                {tarefasHojeCount}
              </span>
            )}
          </button>
        </div>

        {/* Conteudo da tab Tarefas — renderizado independente do tab ativo
            para preservar estado ao trocar de tab */}
        <div className={pageTab === 'tarefas' ? 'block' : 'hidden'}>
          <TarefasPanel onCountReady={setTarefasHojeCount} />
        </div>

        {/* Conteudo da tab Compromissos */}
        <div className={pageTab === 'compromissos' ? 'block' : 'hidden'}>

        {/* Resumo Semanal IA — esconder se vazio (sem dados reais) */}
        <ResumoSemanalIA consultorAtivo={activeTab} />

        {/* Barra de progresso do dia — visível com fundo cinza */}
        {todosItems.length > 0 && (
          <div className="bg-gray-100 rounded-lg p-4 sm:p-5 lg:p-6">
            <div className="flex justify-between items-center mb-2">
              <span className="text-sm sm:text-base font-medium text-gray-700">Atendimentos hoje</span>
              <span className="text-sm sm:text-base font-semibold text-gray-900">
                {totalConcluidos} de {todosItems.length}
              </span>
            </div>
            <ProgressBar current={totalConcluidos} total={todosItems.length} showPercent={false} />
            <div className="text-right text-xs sm:text-sm text-gray-500 mt-1">
              {pctConcluido}% concluído
            </div>
          </div>
        )}

        {/* Seletor de Consultor — Tabs global (ativo verde, inativo cinza) */}
        <Tabs
          tabs={tabsVendedores}
          activeId={activeTab}
          onChange={handleTabChange}
          ariaLabel="Selecionar consultor"
        />

        {/* Agenda do consultor selecionado */}
        <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
          {/* Filtros */}
          <div className="px-3 md:px-4 py-3 bg-gray-50 border-b border-gray-100 space-y-2">
            {/* Busca — linha própria no mobile */}
            <div className="relative w-full">
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
                className="w-full h-9 pl-8 pr-3 text-xs border border-gray-300 rounded-md bg-white text-gray-900 placeholder:text-gray-400 focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-green-500"
              />
            </div>

            {/* Selects — 2-col grid no mobile, flex no desktop */}
            <div className="grid grid-cols-2 gap-2 sm:flex sm:flex-wrap sm:items-center">
              {/* Filtro prioridade */}
              <select
                value={filtroPrioridade}
                onChange={(e) => setFiltroPrioridade(e.target.value)}
                aria-label="Filtrar por prioridade"
                className={`w-full sm:w-auto min-h-[44px] sm:min-h-0 sm:h-8 px-2 text-xs border rounded-md bg-white text-gray-900 focus:outline-none focus:ring-2 focus:ring-green-500 transition-colors ${
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
                className={`w-full sm:w-auto min-h-[44px] sm:min-h-0 sm:h-8 px-2 text-xs border rounded-md bg-white text-gray-900 focus:outline-none focus:ring-2 focus:ring-green-500 transition-colors ${
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
                  className="col-span-2 sm:col-span-1 min-h-[44px] sm:min-h-0 sm:h-8 px-3 text-xs text-gray-500 hover:text-gray-900 transition-colors focus:outline-none focus:ring-2 focus:ring-gray-400 rounded-md border border-gray-200 sm:border-transparent"
                >
                  Limpar
                </button>
              )}
            </div>
          </div>

          {/* Conteudo da aba */}
          <div className="px-3 py-4 md:px-4">
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
                <p className="text-sm font-medium text-gray-600">
                  {temFiltrosAtivos
                    ? 'Nenhum item com esses filtros'
                    : 'Nenhum atendimento agendado para hoje.'}
                </p>
                {!temFiltrosAtivos && (
                  <p className="text-xs text-gray-400 mt-1 mb-3">
                    Clique em &quot;Gerar Agenda&quot; para criar a agenda do dia.
                  </p>
                )}
                {temFiltrosAtivos ? (
                  <button
                    type="button"
                    onClick={() => { setFiltroPrioridade(''); setFiltroSinaleiro(''); setFiltroBusca(''); }}
                    className="mt-2 text-sm text-green-600 hover:text-green-800 underline"
                  >
                    Limpar filtros
                  </button>
                ) : (
                  <button
                    type="button"
                    onClick={handleGerarAgenda}
                    disabled={gerandoAgenda}
                    className="inline-flex items-center gap-2 px-4 py-2 text-sm font-semibold text-white rounded-lg transition-all hover:opacity-90"
                    style={{ backgroundColor: '#00B050' }}
                  >
                    {gerandoAgenda ? (
                      <span className="w-4 h-4 border-2 border-white/40 border-t-white rounded-full animate-spin" />
                    ) : (
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                          d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                      </svg>
                    )}
                    Gerar Agenda
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
                        Prioritarios (P0-P3)
                      </span>
                      <div className="h-px flex-1 bg-red-200" />
                    </div>

                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-3">
                      {prioritarios.map((item, i) => (
                        <AgendaCard
                          key={item.cnpj}
                          item={item}
                          idx={i}
                          concluido={concluidosSet.has(item.cnpj)}
                          onRegistrar={handleRegistrar}
                          onWhatsApp={handleWhatsApp}
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
                          Outros Clientes (P4-P7)
                        </span>
                        <div className="h-px flex-1 bg-gray-200" />
                      </div>
                    )}

                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-3">
                      {regulares.map((item, i) => (
                        <AgendaCard
                          key={item.cnpj}
                          item={item}
                          idx={prioritarios.length + i}
                          concluido={concluidosSet.has(item.cnpj)}
                          onRegistrar={handleRegistrar}
                          onWhatsApp={handleWhatsApp}
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
        <div className="bg-white rounded-xl border border-gray-200 p-4 shadow-sm">
          <h2 className="text-xs sm:text-sm font-semibold text-gray-500 uppercase tracking-wide mb-3">
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
                  className="inline-flex items-center px-1.5 py-0.5 rounded text-xs font-bold"
                  style={{ backgroundColor: p.bg, color: p.text }}
                >
                  {p.code}
                </span>
                <span className="text-xs sm:text-sm text-gray-500">{p.label}</span>
              </div>
            ))}
          </div>
        </div>
        </div>{/* fim da tab Compromissos */}
      </div>

      {/* Modal de atendimento (fora do flow normal para overlay correto) */}
      {modalItem && (
        <AtendimentoModal
          item={modalItem}
          onClose={handleModalClose}
          onSaved={handleModalSaved}
        />
      )}

      {/* Modal WhatsApp rapido */}
      {waModalItem && (
        <WhatsAppAgendaModal
          item={waModalItem}
          waStatus={waStatus}
          onClose={handleWhatsAppClose}
        />
      )}
    </>
  );
}
