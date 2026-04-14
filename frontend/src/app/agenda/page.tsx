'use client';

import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
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
import StatusBadge from '@/components/StatusBadge';
import AtendimentoModal from '@/components/AtendimentoModal';

// ---------------------------------------------------------------------------
// Constantes de dominio
// ---------------------------------------------------------------------------

const CONSULTORES = ['LARISSA', 'MANU', 'JULIO', 'DAIANE'] as const;
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
// Card de item de agenda
// ---------------------------------------------------------------------------

interface AgendaCardProps {
  item: AgendaItem;
  concluido: boolean;
  onRegistrar: (item: AgendaItem) => void;
  onWhatsApp?: (item: AgendaItem) => void;
}

function AgendaCard({ item, concluido, onRegistrar, onWhatsApp }: AgendaCardProps) {
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
            <StatusBadge value={item.prioridade} variant="prioridade" large />

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

        {/* Bloco de ACAO SUGERIDA (destaque principal — elemento mais visivel do card) */}
        {item.acao && (
          <div
            className="mb-2.5 px-3 py-2.5 rounded-r-md"
            style={{
              backgroundColor: concluido ? '#F9FAFB' : acao.bg,
              borderLeft: `4px solid ${acao.border}`,
            }}
          >
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

          {/* Botoes de acao ou checkmark de concluido */}
          {concluido ? (
            <span className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-md bg-green-50 text-green-700 text-xs font-semibold border border-green-200">
              <svg aria-hidden="true" className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
              </svg>
              Concluido
            </span>
          ) : (
            <div className="flex items-center gap-1.5 flex-shrink-0">
              {/* Botao WhatsApp rapido */}
              {onWhatsApp && (
                <button
                  type="button"
                  onClick={() => onWhatsApp(item)}
                  aria-label={`Enviar WhatsApp para ${item.nome_fantasia}`}
                  title="Enviar mensagem WhatsApp"
                  className="min-h-11 sm:min-h-0 p-2 sm:py-1.5 rounded-md border border-gray-200 text-gray-500 hover:text-green-700 hover:border-green-300 hover:bg-green-50 transition-all duration-150 focus:outline-none focus:ring-2 focus:ring-green-500 focus:ring-offset-1"
                >
                  <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                    <path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347z" />
                    <path d="M12 0C5.373 0 0 5.373 0 12c0 2.139.558 4.144 1.535 5.879L.057 23.55a.5.5 0 00.608.608l5.693-1.479A11.952 11.952 0 0012 24c6.627 0 12-5.373 12-12S18.627 0 12 0zm0 22c-1.96 0-3.799-.56-5.354-1.527l-.383-.231-3.979 1.034 1.054-3.867-.252-.4A9.956 9.956 0 012 12C2 6.477 6.477 2 12 2s10 4.477 10 10-4.477 10-10 10z" />
                  </svg>
                </button>
              )}
              <button
                type="button"
                onClick={() => onRegistrar(item)}
                aria-label={`Registrar atendimento de ${item.nome_fantasia}`}
                className="flex-shrink-0 min-h-11 sm:min-h-0 px-3 py-2 sm:py-1.5 bg-green-600 hover:bg-green-700 text-white text-xs font-semibold rounded-md transition-all duration-150 hover:shadow-md hover:-translate-y-px focus:outline-none focus:ring-2 focus:ring-green-500 focus:ring-offset-1"
              >
                Registrar Atendimento
              </button>
            </div>
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
    <div className="bg-white rounded-xl border border-gray-200 px-4 py-3 shadow-sm">
      <div className="flex items-center justify-between mb-2 gap-2">
        {/* Mobile: so mostra pct e consultor | Desktop: texto completo */}
        <p className="text-sm font-medium text-gray-700 min-w-0">
          <span className="hidden sm:inline">
            <span className="font-bold text-gray-900">{concluidos}</span> de{' '}
            <span className="font-bold text-gray-900">{total}</span> atendimentos concluidos hoje
          </span>
          <span className="sm:hidden font-bold text-gray-900">
            {concluidos}/{total}
          </span>
          <span className="ml-2 text-xs font-semibold" style={{ color: progressColor }}>
            {pct}%
          </span>
        </p>
        <p className="text-xs text-gray-500 flex-shrink-0">{consultor}</p>
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
          <span className="text-[11px] font-semibold text-gray-600 uppercase tracking-wider">
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

  return (
    <>
      <div className="space-y-3 sm:space-y-4 max-w-4xl">
        {/* Cabecalho da pagina */}
        <div className="flex items-start justify-between gap-3">
          <div className="min-w-0">
            <h1 className="text-lg sm:text-xl font-bold text-gray-900">Agenda Comercial</h1>
            <p className="text-xs text-gray-500 mt-0.5 truncate">{hoje}</p>
          </div>
          <div className="flex items-center gap-2 sm:gap-3 flex-shrink-0">
            {todosItems.length > 0 && (
              <div className="hidden sm:block text-right">
                <p className="text-xs text-gray-500">Total na agenda</p>
                <p className="text-xl font-bold text-gray-900">{todosItems.length}</p>
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

        {/* Resumo Semanal IA */}
        <ResumoSemanalIA consultorAtivo={activeTab} />

        {/* Barra de progresso */}
        {todosItems.length > 0 && (
          <ProgressBar
            total={todosItems.length}
            concluidos={totalConcluidos}
            consultor={activeTab}
          />
        )}

        {/* Seletor de Consultor — botoes grandes */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
          {CONSULTORES.map((c) => {
            const count = agendaByConsultor[c]?.length;
            const pendentes = count !== undefined
              ? count - ((concluidosByConsultor[c]?.size) ?? 0)
              : undefined;
            const isActive = activeTab === c;

            return (
              <button
                key={c}
                type="button"
                onClick={() => handleTabChange(c)}
                className="flex flex-col items-center justify-center gap-1 px-4 py-3 rounded-xl border-2 font-semibold text-sm transition-all focus:outline-none focus:ring-2 focus:ring-green-500 focus:ring-offset-1"
                style={{
                  backgroundColor: isActive ? '#00B050' : '#ffffff',
                  borderColor: isActive ? '#00B050' : '#E5E7EB',
                  color: isActive ? '#ffffff' : '#374151',
                  boxShadow: isActive ? '0 2px 8px rgba(0,176,80,0.25)' : '0 1px 3px rgba(0,0,0,0.06)',
                }}
              >
                <span>{c}</span>
                {pendentes !== undefined && (
                  <span
                    className="inline-flex items-center justify-center min-w-[20px] h-5 px-1.5 rounded-full text-[10px] font-bold"
                    style={{
                      backgroundColor: isActive ? 'rgba(255,255,255,0.25)' : (pendentes > 0 ? '#F3F4F6' : '#DCFCE7'),
                      color: isActive ? '#fff' : (pendentes > 0 ? '#374151' : '#15803D'),
                    }}
                  >
                    {pendentes > 0 ? pendentes : '✓'}
                  </span>
                )}
              </button>
            );
          })}
        </div>

        {/* Agenda do consultor selecionado */}
        <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
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

                    <div className="space-y-2">
                      {prioritarios.map((item) => (
                        <AgendaCard
                          key={item.cnpj}
                          item={item}
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

                    <div className="space-y-2">
                      {regulares.map((item) => (
                        <AgendaCard
                          key={item.cnpj}
                          item={item}
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
