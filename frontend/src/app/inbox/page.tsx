'use client';

import { useCallback, useEffect, useRef, useState } from 'react';
import {
  fetchInbox,
  fetchTicketMensagens,
  fetchWhatsAppStatus,
  fetchAtendimentosInbox,
  type InboxTicket,
  type DeskrioMensagem,
  type WhatsAppStatus,
  type AtendimentoInboxItem,
} from '@/lib/api';
import { getToken } from '@/lib/auth';

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? '';
const POLL_INTERVAL_MS = 30_000;

type FilterTab = 'todos' | 'aguardando' | 'atendimento' | 'finalizados';

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function getInitials(nome: string): string {
  return nome
    .trim()
    .split(/\s+/)
    .slice(0, 2)
    .map((w) => w.charAt(0).toUpperCase())
    .join('');
}

function formatTime(dateStr: string | null): string {
  if (!dateStr) return '';
  try {
    const d = new Date(dateStr);
    const now = new Date();
    const diffMs = now.getTime() - d.getTime();
    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));
    if (diffDays === 0) {
      return d.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' });
    }
    if (diffDays === 1) return 'Ontem';
    if (diffDays < 7) return `${diffDays}d`;
    return d.toLocaleDateString('pt-BR', { day: '2-digit', month: '2-digit' });
  } catch {
    return '';
  }
}

function formatMsgTime(dateStr: string): string {
  try {
    const d = new Date(dateStr);
    return d.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' });
  } catch {
    return '';
  }
}

function formatSecondsAgo(last: Date | null): string {
  if (!last) return '';
  const secs = Math.floor((Date.now() - last.getTime()) / 1000);
  if (secs < 5) return 'Atualizado agora';
  if (secs < 60) return `Atualizado ha ${secs}s`;
  const mins = Math.floor(secs / 60);
  return `Atualizado ha ${mins}min`;
}

function stripMarkdown(text: string): string {
  return text
    .replace(/\*([^*]+)\*:/g, '$1:')
    .replace(/\*([^*]+)\*/g, '$1')
    .replace(/_([^_]+)_/g, '$1')
    .trim();
}

function truncatePreview(text: string, max = 52): string {
  const clean = stripMarkdown(text);
  if (clean.length <= max) return clean;
  return clean.slice(0, max) + '...';
}

// ---------------------------------------------------------------------------
// Fallback histórico — agrupa LOG do banco por CNPJ (uma entrada por cliente)
// Usado quando Deskrio offline (waConnecting) e tickets ao vivo zerados.
// ---------------------------------------------------------------------------

interface HistoricoFallbackGrupo {
  cnpj: string;
  nome_fantasia: string;
  count: number;
  ultimaMensagem: string;
  dataUltima: string;
}

/** Remove prefixo "[Ticket#XXX|...|...]" da descrição vinda do log_interacoes. */
function limparDescricao(desc: string): string {
  return desc.replace(/^\[Ticket#[^\]]+\]\s*/, '').trim();
}

/** Filtra apenas atendimentos provenientes do canal WhatsApp.
 * Heurística (o backend não aceita filtro tipo_contato no GET /api/atendimentos):
 *   - descricao com prefixo "[Ticket#...]" = log do Deskrio (WhatsApp)
 *   - fase começando com "ATENDIMENTO_WA" também marca canal WhatsApp
 */
function filtrarWhatsApp(itens: AtendimentoInboxItem[]): AtendimentoInboxItem[] {
  return itens.filter((it) => {
    const desc = it.descricao ?? '';
    const fase = it.fase ?? '';
    return desc.startsWith('[Ticket#') || fase.toUpperCase().startsWith('ATENDIMENTO_WA');
  });
}

/** Agrupa por CNPJ: 1 linha por cliente com a última interação + count. */
function agruparPorCnpj(itens: AtendimentoInboxItem[]): HistoricoFallbackGrupo[] {
  const map = new Map<string, HistoricoFallbackGrupo>();
  for (const item of itens) {
    const cnpj = item.cnpj;
    const dataAtual = item.data_interacao;
    const ex = map.get(cnpj);
    if (!ex) {
      map.set(cnpj, {
        cnpj,
        nome_fantasia: item.nome_fantasia ?? '(sem nome)',
        count: 1,
        ultimaMensagem: limparDescricao(item.descricao ?? ''),
        dataUltima: dataAtual,
      });
    } else {
      ex.count += 1;
      // Atualiza última mensagem se este item for mais recente
      if (new Date(dataAtual).getTime() > new Date(ex.dataUltima).getTime()) {
        ex.dataUltima = dataAtual;
        ex.ultimaMensagem = limparDescricao(item.descricao ?? '');
      }
    }
  }
  return Array.from(map.values()).sort(
    (a, b) => new Date(b.dataUltima).getTime() - new Date(a.dataUltima).getTime()
  );
}

/** Formata data ISO -> dd/mm HH:MM (curto, p/ lista compacta). */
function formatDataCurta(dateStr: string): string {
  try {
    const d = new Date(dateStr);
    const dia = String(d.getDate()).padStart(2, '0');
    const mes = String(d.getMonth() + 1).padStart(2, '0');
    const hora = String(d.getHours()).padStart(2, '0');
    const min = String(d.getMinutes()).padStart(2, '0');
    return `${dia}/${mes} ${hora}:${min}`;
  } catch {
    return '';
  }
}

// ---------------------------------------------------------------------------
// Media helpers (preserved from original)
// ---------------------------------------------------------------------------

type MediaType = 'image' | 'audio' | 'video' | 'document';

function getMediaType(url: string): MediaType | null {
  if (!url) return null;
  const cleanUrl = url.split('?')[0] ?? '';
  const ext = (cleanUrl.split('.').pop() ?? '').toLowerCase();
  if (['jpg', 'jpeg', 'png', 'gif', 'webp'].includes(ext)) return 'image';
  if (['mp3', 'ogg', 'wav', 'opus', 'm4a'].includes(ext)) return 'audio';
  if (['mp4', 'webm'].includes(ext)) return 'video';
  if (['pdf', 'doc', 'docx', 'xls', 'xlsx'].includes(ext)) return 'document';
  if (/\/(image|img|photo|foto)\//i.test(url)) return 'image';
  if (/\/(audio|voice|ptt)\//i.test(url)) return 'audio';
  if (/\/(video|vid)\//i.test(url)) return 'video';
  if (/\/(document|doc|file)\//i.test(url)) return 'document';
  return null;
}

function getDocumentIcon(): string {
  return 'M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z';
}

interface MediaBubbleProps {
  url: string;
  enviado: boolean;
}

function MediaBubble({ url, enviado }: MediaBubbleProps) {
  const mediaType = getMediaType(url);
  const [imgExpanded, setImgExpanded] = useState(false);

  if (!mediaType) {
    return (
      <a
        href={url}
        target="_blank"
        rel="noopener noreferrer"
        className={`flex items-center gap-2 px-3 py-2 rounded-xl text-xs font-medium underline
          ${enviado ? 'text-white/90' : 'text-green-700'}`}
      >
        <svg className="w-4 h-4 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d={getDocumentIcon()} />
        </svg>
        Arquivo anexo
      </a>
    );
  }

  if (mediaType === 'image') {
    return (
      <>
        <button
          type="button"
          onClick={() => setImgExpanded(true)}
          className="block focus:outline-none focus:ring-2 focus:ring-green-400 rounded-xl overflow-hidden"
          aria-label="Ampliar imagem"
        >
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img
            src={url}
            alt="Imagem recebida via WhatsApp"
            className="rounded-xl object-cover"
            style={{ maxWidth: '300px', maxHeight: '220px', display: 'block' }}
            loading="lazy"
            onError={(e) => {
              (e.currentTarget as HTMLImageElement).style.display = 'none';
            }}
          />
        </button>
        {imgExpanded && (
          <div
            className="fixed inset-0 z-50 flex items-center justify-center bg-black/80"
            onClick={() => setImgExpanded(false)}
            role="dialog"
            aria-modal="true"
            aria-label="Imagem ampliada"
          >
            <button
              type="button"
              onClick={() => setImgExpanded(false)}
              className="absolute top-4 right-4 text-white bg-black/50 rounded-full p-2
                         hover:bg-black/70 transition-colors"
              aria-label="Fechar"
            >
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img
              src={url}
              alt="Imagem ampliada"
              className="max-w-[90vw] max-h-[90vh] rounded-xl shadow-2xl object-contain"
              onClick={(e) => e.stopPropagation()}
            />
          </div>
        )}
      </>
    );
  }

  if (mediaType === 'audio') {
    return (
      <div className="w-full" style={{ maxWidth: '300px' }}>
        {/* eslint-disable-next-line jsx-a11y/media-has-caption */}
        <audio
          controls
          src={url}
          className="w-full rounded-lg"
          style={{ height: '36px', minWidth: '220px' }}
        />
      </div>
    );
  }

  if (mediaType === 'video') {
    return (
      <div style={{ maxWidth: '300px' }}>
        {/* eslint-disable-next-line jsx-a11y/media-has-caption */}
        <video
          controls
          src={url}
          className="rounded-xl object-cover"
          style={{ maxWidth: '300px', maxHeight: '220px', display: 'block' }}
        />
      </div>
    );
  }

  // document
  const fileName = url.split('/').pop()?.split('?')[0] ?? 'Documento';
  return (
    <a
      href={url}
      target="_blank"
      rel="noopener noreferrer"
      className={`flex items-center gap-2.5 px-3 py-2.5 rounded-xl border text-xs font-medium
        transition-colors hover:opacity-80
        ${enviado
          ? 'border-white/30 text-white bg-white/10'
          : 'border-gray-200 text-gray-700 bg-gray-50 hover:bg-gray-100'}`}
      style={{ maxWidth: '260px' }}
      download
    >
      <svg className="w-5 h-5 flex-shrink-0 text-green-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d={getDocumentIcon()} />
      </svg>
      <span className="truncate">{fileName}</span>
      <svg className="w-3.5 h-3.5 flex-shrink-0 opacity-60" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
          d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
      </svg>
    </a>
  );
}

// ---------------------------------------------------------------------------
// Status dot
// ---------------------------------------------------------------------------

interface StatusDotProps {
  ticket: InboxTicket;
}

function StatusDot({ ticket }: StatusDotProps) {
  if (ticket.status === 'closed' || ticket.status === 'resolved') {
    return (
      <span title="Finalizado">
        <span className="w-2 h-2 rounded-full bg-gray-400 inline-block" />
      </span>
    );
  }
  if (ticket.aguardando_resposta) {
    return (
      <span title="Aguardando resposta">
        <span className="w-2 h-2 rounded-full bg-orange-400 inline-block" />
      </span>
    );
  }
  return (
    <span title="Em atendimento">
      <span className="w-2 h-2 rounded-full bg-green-500 inline-block" />
    </span>
  );
}

// ---------------------------------------------------------------------------
// Status badge (for chat header)
// ---------------------------------------------------------------------------

function StatusBadge({ ticket }: StatusDotProps) {
  if (ticket.status === 'closed' || ticket.status === 'resolved') {
    return (
      <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-gray-100 border border-gray-200">
        <span className="w-1.5 h-1.5 rounded-full bg-gray-400" />
        <span className="text-[10px] font-medium text-gray-600">Finalizado</span>
      </span>
    );
  }
  if (ticket.aguardando_resposta) {
    return (
      <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-orange-50 border border-orange-200">
        <span className="w-1.5 h-1.5 rounded-full bg-orange-400 animate-pulse" />
        <span className="text-[10px] font-medium text-orange-700">Aguardando resposta</span>
      </span>
    );
  }
  return (
    <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-green-50 border border-green-200">
      <span className="w-1.5 h-1.5 rounded-full bg-green-500" />
      <span className="text-[10px] font-medium text-green-700">Em atendimento</span>
    </span>
  );
}

// ---------------------------------------------------------------------------
// Avatar
// ---------------------------------------------------------------------------

interface AvatarProps {
  nome: string;
  size?: 'sm' | 'md';
}

function Avatar({ nome, size = 'md' }: AvatarProps) {
  const dim = size === 'sm' ? 'w-8 h-8 text-[10px]' : 'w-10 h-10 text-xs';
  return (
    <div
      className={`${dim} rounded-full flex items-center justify-center flex-shrink-0 text-white font-bold`}
      style={{ backgroundColor: '#00B050' }}
    >
      {getInitials(nome)}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Skeleton row
// ---------------------------------------------------------------------------

function SkeletonRow() {
  return (
    <div className="flex items-center gap-3 px-3 py-3 border-b border-gray-50">
      <div className="w-10 h-10 rounded-full bg-gray-100 animate-pulse flex-shrink-0" />
      <div className="flex-1 space-y-1.5">
        <div className="h-3 bg-gray-100 animate-pulse rounded w-3/4" />
        <div className="h-2.5 bg-gray-100 animate-pulse rounded w-1/2" />
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Left panel — Conversation list
// ---------------------------------------------------------------------------

interface ConversationListProps {
  tickets: InboxTicket[];
  loading: boolean;
  error: string | null;
  selectedId: number | null;
  busca: string;
  filterTab: FilterTab;
  lastRefreshed: Date | null;
  refreshing: boolean;
  waStatus: WhatsAppStatus | null;
  historicoFallback: AtendimentoInboxItem[] | null;
  onBuscaChange: (v: string) => void;
  onFilterTab: (t: FilterTab) => void;
  onSelect: (t: InboxTicket) => void;
  onRefresh: () => void;
}

function ConversationList({
  tickets,
  loading,
  error,
  selectedId,
  busca,
  filterTab,
  lastRefreshed,
  refreshing,
  waStatus,
  historicoFallback,
  onBuscaChange,
  onFilterTab,
  onSelect,
  onRefresh,
}: ConversationListProps) {
  const tabs: { key: FilterTab; label: string }[] = [
    { key: 'todos', label: 'Todos' },
    { key: 'aguardando', label: 'Aguardando' },
    { key: 'atendimento', label: 'Em atend.' },
    { key: 'finalizados', label: 'Finaliz.' },
  ];

  // Filter by tab
  const filtered = tickets.filter((t) => {
    const matchBusca = !busca.trim() ||
      t.contato_nome.toLowerCase().includes(busca.toLowerCase()) ||
      t.contato_numero.includes(busca);
    if (!matchBusca) return false;
    if (filterTab === 'aguardando') return t.aguardando_resposta && t.status === 'open';
    if (filterTab === 'atendimento') return !t.aguardando_resposta && t.status === 'open';
    if (filterTab === 'finalizados') return t.status === 'closed' || t.status === 'resolved';
    return true;
  });

  // Count badges
  const countAguardando = tickets.filter((t) => t.aguardando_resposta && t.status === 'open').length;

  // Derive WA connection state from status
  const waOnline = waStatus !== null && waStatus.configurado && waStatus.alguma_conectada;
  const waConnecting = waStatus !== null && waStatus.configurado && !waStatus.alguma_conectada;
  const waOffline = waStatus === null || !waStatus.configurado;

  // Histórico fallback (banco) — usado quando Deskrio offline e tickets vazios.
  // Agrupa por CNPJ; cada grupo é uma linha clicável read-only.
  const fallbackGruposBase: HistoricoFallbackGrupo[] = (() => {
    if (!waConnecting) return [];
    if (historicoFallback === null || historicoFallback.length === 0) return [];
    return agruparPorCnpj(filtrarWhatsApp(historicoFallback));
  })();
  const fallbackGrupos: HistoricoFallbackGrupo[] = busca.trim()
    ? fallbackGruposBase.filter((g) => {
        const termo = busca.toLowerCase();
        return (
          g.nome_fantasia.toLowerCase().includes(termo) ||
          g.cnpj.includes(busca.replace(/\D/g, ''))
        );
      })
    : fallbackGruposBase;
  const showFallback =
    waConnecting && tickets.length === 0 && historicoFallback !== null;
  const fallbackLoading =
    waConnecting && tickets.length === 0 && historicoFallback === null;

  return (
    <div className="w-full flex-shrink-0 border-r border-gray-200 bg-white flex flex-col h-full">
      {/* Offline banner */}
      {waOffline && (
        <div className="flex items-center gap-2 px-3 py-2 bg-amber-50 border-b border-amber-200 flex-shrink-0">
          <svg className="w-3.5 h-3.5 text-amber-500 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
              d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
          </svg>
          <p className="text-[10px] text-amber-700 font-medium">
            WhatsApp desconectado — mostrando ultimos dados disponiveis
          </p>
        </div>
      )}
      {waConnecting && (
        <div className="bg-amber-50 border-l-4 border-amber-500 rounded-lg p-4 flex items-start gap-3 shadow-sm mx-3 mt-3 flex-shrink-0">
          <svg
            className="w-5 h-5 text-amber-600 flex-shrink-0 mt-0.5"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
            aria-hidden="true"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
            />
          </svg>
          <div className="flex-1 min-w-0">
            <p className="text-sm font-semibold text-amber-900">
              Conexões WhatsApp do Deskrio offline
            </p>
            <p className="text-xs text-amber-800 mt-0.5">
              Novas mensagens não chegam até reconectar uma das conexões WhatsApp no painel Deskrio.
              O histórico abaixo (se houver) é dos últimos dados sincronizados.
            </p>
            <a
              href="https://web.deskrio.com.br"
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1.5 mt-2 px-3 py-1.5 text-xs font-semibold text-white bg-amber-600 hover:bg-amber-700 rounded-md transition-colors focus:outline-none focus:ring-2 focus:ring-amber-500 focus:ring-offset-1"
            >
              <span>Abrir painel Deskrio</span>
              <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14 5l7 7m0 0l-7 7m7-7H3" />
              </svg>
            </a>
          </div>
        </div>
      )}

      {/* Header */}
      <div className="px-4 pt-3 pb-2 border-b border-gray-100 flex-shrink-0">
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center gap-2">
            {/* WhatsApp icon */}
            <svg className="w-4 h-4" viewBox="0 0 24 24" fill="#00B050">
              <path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413z" />
            </svg>
            <h2 className="text-sm font-bold text-gray-900">WhatsApp Inbox</h2>
          </div>
          <div className="flex items-center gap-2">
            {/* Dynamic WA status indicator */}
            <div className="flex items-center gap-1">
              {waOnline && (
                <>
                  <div className="w-1.5 h-1.5 rounded-full bg-green-500 animate-pulse" />
                  <span className="text-[9px] text-green-700 font-medium">Online</span>
                </>
              )}
              {waConnecting && (
                <>
                  <div className="w-1.5 h-1.5 rounded-full bg-yellow-400 animate-pulse" />
                  <span className="text-[9px] text-yellow-700 font-medium">Conectando</span>
                </>
              )}
              {waOffline && (
                <>
                  <div className="w-1.5 h-1.5 rounded-full bg-gray-400" />
                  <span className="text-[9px] text-gray-500 font-medium">Offline</span>
                </>
              )}
            </div>
            <button
              type="button"
              onClick={onRefresh}
              disabled={refreshing}
              aria-label="Atualizar"
              className="p-1 rounded-md text-gray-400 hover:text-gray-600 hover:bg-gray-100
                         transition-colors disabled:opacity-40"
            >
              <svg
                className={`w-3.5 h-3.5 ${refreshing ? 'animate-spin' : ''}`}
                fill="none" viewBox="0 0 24 24" stroke="currentColor"
              >
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                  d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
            </button>
          </div>
        </div>

        {lastRefreshed && (
          <p className="text-[9px] text-gray-400 mb-2 leading-none">
            {formatSecondsAgo(lastRefreshed)}
          </p>
        )}

        {/* Search */}
        <div className="relative mb-2">
          <svg
            className="absolute left-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-gray-400 pointer-events-none"
            fill="none" viewBox="0 0 24 24" stroke="currentColor"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
              d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
          </svg>
          <input
            type="text"
            value={busca}
            onChange={(e) => onBuscaChange(e.target.value)}
            placeholder="Buscar contato..."
            aria-label="Buscar contato"
            className="w-full pl-8 pr-3 py-2 text-xs border border-gray-200 rounded-lg bg-gray-50
                       focus:outline-none focus:ring-2 focus:ring-green-200 focus:border-green-400
                       placeholder:text-gray-400"
          />
        </div>

        {/* Filter tabs */}
        <div className="flex gap-0.5 bg-gray-100 rounded-lg p-0.5">
          {tabs.map((tab) => (
            <button
              key={tab.key}
              type="button"
              onClick={() => onFilterTab(tab.key)}
              className={`flex-1 flex items-center justify-center gap-1 py-1 rounded-md text-[10px] font-semibold
                         transition-colors focus:outline-none
                         ${filterTab === tab.key
                           ? 'bg-white text-gray-900 shadow-sm'
                           : 'text-gray-500 hover:text-gray-700'}`}
            >
              {tab.label}
              {tab.key === 'aguardando' && countAguardando > 0 && (
                <span className="bg-orange-400 text-white text-[8px] font-bold px-1 py-0.5 rounded-full leading-none min-w-[14px] text-center">
                  {countAguardando}
                </span>
              )}
            </button>
          ))}
        </div>
      </div>

      {/* List */}
      <div className="flex-1 overflow-y-auto" style={{ scrollbarWidth: 'thin' }}>
        {loading && (
          <div>
            {[...Array(8)].map((_, i) => <SkeletonRow key={i} />)}
          </div>
        )}

        {!loading && error && (
          <div className="flex flex-col items-center justify-center h-48 text-center px-6">
            <svg className="w-8 h-8 text-amber-300 mb-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
                d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
            <p className="text-xs font-medium text-gray-600 mb-1">Erro ao carregar</p>
            <p className="text-[11px] text-gray-400">{error}</p>
          </div>
        )}

        {!loading && !error && filtered.length === 0 && !showFallback && (
          <div className="flex flex-col items-center justify-center py-16 px-6 text-center">
            <svg className="w-12 h-12 text-gray-300 mb-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
                d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
            </svg>
            <p className="text-sm font-medium text-gray-500">Nenhuma conversa encontrada</p>
            <p className="text-xs text-gray-400 mt-1">
              {busca
                ? 'Tente outro termo de busca'
                : filterTab !== 'todos'
                  ? 'Tente outro filtro'
                  : 'Nenhum ticket nos ultimos 7 dias'}
            </p>
          </div>
        )}

        {/* Fallback do banco — Deskrio offline + zero tickets */}
        {!loading && !error && fallbackLoading && (
          <div>
            <div className="px-3 py-2 bg-blue-50 border-b border-blue-100">
              <p className="text-[11px] text-blue-800">Carregando historico do banco...</p>
            </div>
            {[...Array(6)].map((_, i) => <SkeletonRow key={`fb-skel-${i}`} />)}
          </div>
        )}

        {!loading && !error && showFallback && historicoFallback !== null && fallbackGrupos.length === 0 && (
          <div className="flex flex-col items-center justify-center py-16 px-6 text-center">
            <svg className="w-12 h-12 text-gray-300 mb-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
                d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
            </svg>
            <p className="text-sm font-medium text-gray-700">Aguardando reconexão WhatsApp</p>
            <p className="text-xs text-gray-500 mt-1 max-w-sm">
              {busca
                ? 'Nenhum historico bate com a busca. Reconecte uma das conexões WhatsApp no painel Deskrio para receber mensagens novas.'
                : 'Sem historico WhatsApp no banco. Reconecte uma das conexões WhatsApp no painel Deskrio para receber mensagens novas.'}
            </p>
          </div>
        )}

        {!loading && !error && showFallback && fallbackGrupos.length > 0 && (
          <div>
            <div className="px-3 py-2 bg-blue-50 border-b border-blue-100 flex items-center gap-2">
              <svg className="w-3.5 h-3.5 text-blue-600 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <p className="text-[11px] text-blue-800">
                Histórico do banco — {fallbackGrupos.length} {fallbackGrupos.length === 1 ? 'cliente' : 'clientes'}.
                Reconecte para receber mensagens novas.
              </p>
            </div>
            {fallbackGrupos.map((g) => (
              <div
                key={g.cnpj}
                className="w-full flex items-start gap-3 px-3 py-3 border-b border-gray-50 border-l-2 border-l-transparent"
                title="Histórico do banco — read-only enquanto WhatsApp esta offline"
              >
                <div className="relative flex-shrink-0 mt-0.5">
                  <Avatar nome={g.nome_fantasia} size="md" />
                  <span className="absolute -bottom-0.5 -right-0.5" title="Histórico (read-only)">
                    <span className="w-2 h-2 rounded-full bg-gray-400 inline-block ring-2 ring-white" />
                  </span>
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-start justify-between gap-1 mb-0.5">
                    <p className="text-xs font-semibold text-gray-900 truncate leading-tight">
                      {g.nome_fantasia}
                    </p>
                    <div className="flex items-center gap-1 flex-shrink-0">
                      <span className="text-[9px] font-semibold text-gray-500 bg-gray-100 px-1.5 py-0.5 rounded">
                        histórico
                      </span>
                      <span className="text-[10px] text-gray-400 tabular-nums">
                        {formatDataCurta(g.dataUltima)}
                      </span>
                    </div>
                  </div>
                  <p className="text-[11px] text-gray-500 truncate leading-tight mb-1">
                    {g.ultimaMensagem ? truncatePreview(g.ultimaMensagem) : ' '}
                  </p>
                  {g.count > 1 && (
                    <span className="text-[9px] text-gray-400">
                      {g.count} interações
                    </span>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}

        {!loading && !error && filtered.map((t) => {
          const isSelected = selectedId === t.ticket_id;
          const isAguardando = t.aguardando_resposta && t.status === 'open';
          return (
            <button
              key={t.ticket_id}
              type="button"
              onClick={() => onSelect(t)}
              aria-pressed={isSelected}
              className={`w-full flex items-start gap-3 px-3 py-3 text-left border-b border-gray-50
                          transition-colors hover:bg-gray-50 focus:outline-none focus:ring-2
                          focus:ring-inset focus:ring-green-300 relative
                          ${isSelected ? 'bg-green-50' : ''}
                          ${isAguardando ? 'border-l-2 border-l-orange-400' : isSelected ? 'border-l-2 border-l-green-500' : 'border-l-2 border-l-transparent'}`}
            >
              {/* Avatar */}
              <div className="relative flex-shrink-0 mt-0.5">
                <Avatar nome={t.contato_nome} size="md" />
                <span className="absolute -bottom-0.5 -right-0.5">
                  <StatusDot ticket={t} />
                </span>
              </div>

              {/* Content */}
              <div className="flex-1 min-w-0">
                <div className="flex items-start justify-between gap-1 mb-0.5">
                  <p className={`text-xs font-semibold text-gray-900 truncate leading-tight
                    ${t.mensagens_nao_lidas > 0 ? 'font-bold' : ''}`}>
                    {t.contato_nome}
                  </p>
                  <div className="flex items-center gap-1 flex-shrink-0">
                    {t.mensagens_nao_lidas > 0 && (
                      <span className="bg-green-500 text-white text-[9px] font-bold
                                       w-4 h-4 rounded-full flex items-center justify-center">
                        {t.mensagens_nao_lidas > 9 ? '9+' : t.mensagens_nao_lidas}
                      </span>
                    )}
                    <span className="text-[10px] text-gray-400">
                      {formatTime(t.ultima_mensagem_data ?? t.ultima_msg_cliente_data)}
                    </span>
                  </div>
                </div>

                <p className={`text-[11px] truncate leading-tight mb-1
                  ${t.mensagens_nao_lidas > 0 ? 'text-gray-800 font-medium' : 'text-gray-500'}`}>
                  {t.ultima_mensagem ? truncatePreview(t.ultima_mensagem) : '\u00a0'}
                </p>

                <div className="flex items-center gap-1.5">
                  {t.atendente_nome && (
                    <span className="text-[9px] text-gray-400 truncate">
                      {t.atendente_nome.replace('- Vitao', '').replace('- vitao', '').trim()}
                    </span>
                  )}
                  {t.origem && (
                    <span className="text-[9px] text-gray-300">·</span>
                  )}
                  {t.origem && (
                    <span className="text-[9px] text-gray-400">{t.origem}</span>
                  )}
                </div>
              </div>
            </button>
          );
        })}
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Chat panel
// ---------------------------------------------------------------------------

interface ChatPanelProps {
  ticket: InboxTicket | null;
  mensagens: DeskrioMensagem[];
  loading: boolean;
  refreshing: boolean;
  inputTexto: string;
  sending: boolean;
  lastRefreshed: Date | null;
  onInputChange: (v: string) => void;
  onSend: () => void;
  onBack: () => void;
  showBack: boolean;
  onRefresh: () => void;
}

function ChatPanel({
  ticket,
  mensagens,
  loading,
  refreshing,
  inputTexto,
  sending,
  lastRefreshed,
  onInputChange,
  onSend,
  onBack,
  showBack,
  onRefresh,
}: ChatPanelProps) {
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [mensagens]);

  function handleKeyDown(e: React.KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      onSend();
    }
  }

  const quickPills = [
    { label: 'Catalogo', msg: 'Segue o catalogo de produtos VITAO: [link]' },
    { label: 'Tabela de Precos', msg: 'Segue a tabela de precos atualizada: [link]' },
    { label: 'Prazo de Entrega', msg: 'O prazo de entrega para sua regiao e de 3 a 5 dias uteis.' },
  ];

  // Empty state — no ticket selected
  if (!ticket) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center bg-gray-50">
        <div
          className="w-16 h-16 rounded-full flex items-center justify-center mb-4"
          style={{ backgroundColor: '#00B05015' }}
        >
          <svg className="w-8 h-8" fill="none" viewBox="0 0 24 24" stroke="currentColor" style={{ color: '#00B050' }}>
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
              d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
          </svg>
        </div>
        <h3 className="text-sm font-semibold text-gray-700">Selecione uma conversa</h3>
        <p className="text-xs text-gray-400 mt-1 text-center px-8">
          Escolha um ticket na lista ao lado para ver o historico
        </p>
      </div>
    );
  }

  const isClosed = ticket.status === 'closed' || ticket.status === 'resolved';

  return (
    <div className="flex-1 flex flex-col bg-gray-50 min-w-0">
      {/* Chat header */}
      <div className="flex items-center gap-3 px-4 py-3 bg-white border-b border-gray-200 flex-shrink-0">
        {showBack && (
          <button
            type="button"
            onClick={onBack}
            aria-label="Voltar"
            className="p-1.5 rounded-lg text-gray-500 hover:bg-gray-100 transition-colors"
          >
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
            </svg>
          </button>
        )}

        <Avatar nome={ticket.contato_nome} size="sm" />

        <div className="flex-1 min-w-0">
          <p className="text-sm font-semibold text-gray-900 truncate leading-tight">
            {ticket.contato_nome}
          </p>
          <div className="flex items-center gap-2 flex-wrap">
            <span className="text-[10px] text-gray-400">
              {ticket.contato_numero
                ? ticket.contato_numero.replace(/^55/, '+55 ').replace(/(\d{2})(\d{5})(\d{4})/, '($1) $2-$3')
                : ''}
            </span>
            {ticket.atendente_nome && (
              <span className="text-[10px] text-gray-400">
                · {ticket.atendente_nome.replace('- Vitao', '').replace('- vitao', '').trim()}
              </span>
            )}
          </div>
        </div>

        <div className="flex items-center gap-2 flex-shrink-0">
          <StatusBadge ticket={ticket} />
          {refreshing && (
            <div className="w-3.5 h-3.5 border-2 border-gray-200 border-t-green-500 rounded-full animate-spin" />
          )}
          <button
            type="button"
            onClick={onRefresh}
            disabled={loading || refreshing}
            aria-label="Atualizar mensagens"
            title={lastRefreshed ? formatSecondsAgo(lastRefreshed) : 'Atualizar'}
            className="p-1.5 rounded-lg text-gray-400 hover:text-gray-600 hover:bg-gray-100
                       transition-colors disabled:opacity-40"
          >
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
          </button>
          <span
            className="text-[9px] text-gray-400 hidden lg:inline"
            title="ID do ticket Deskrio"
          >
            #{ticket.ticket_id}
          </span>
        </div>
      </div>

      {/* Last-refreshed bar */}
      {lastRefreshed && (
        <div className="flex items-center justify-center px-4 py-1 bg-white border-b border-gray-100 flex-shrink-0">
          <span className="text-[9px] text-gray-400">{formatSecondsAgo(lastRefreshed)}</span>
        </div>
      )}

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-4 py-4 space-y-3" style={{ scrollbarWidth: 'thin' }}>
        {loading && (
          <div className="flex justify-center py-8">
            <div className="w-5 h-5 border-2 border-gray-200 border-t-green-500 rounded-full animate-spin" />
          </div>
        )}

        {!loading && mensagens.length === 0 && (
          <div className="flex flex-col items-center justify-center h-32 text-center">
            <svg className="w-8 h-8 text-gray-200 mb-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
                d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
            </svg>
            <p className="text-xs font-medium text-gray-500">Sem mensagens ainda</p>
            <p className="text-[11px] text-gray-400 mt-1">O historico aparecera aqui</p>
          </div>
        )}

        {!loading && mensagens.map((m) => {
          const enviado = !m.de_cliente;
          const mediaType = m.media_url ? getMediaType(m.media_url) : null;

          return (
            <div key={m.id} className={`flex ${enviado ? 'justify-end' : 'justify-start'}`}>
              {/* Avatar for incoming */}
              {!enviado && (
                <div
                  className="w-6 h-6 rounded-full flex items-center justify-center flex-shrink-0
                             text-white text-[9px] font-bold mr-2 mt-auto mb-0.5 bg-gray-400"
                >
                  {getInitials(m.nome_contato ?? ticket.contato_nome)}
                </div>
              )}

              <div className="max-w-xs lg:max-w-sm xl:max-w-md">
                {/* Sender name for outgoing */}
                {enviado && m.nome_contato && (
                  <p className="text-[9px] text-gray-400 text-right mb-0.5 mr-1 truncate max-w-[200px] ml-auto">
                    {m.nome_contato.replace('- Vitao', '').replace('- vitao', '').trim()}
                  </p>
                )}
                <div
                  className={`px-3 py-2 text-xs leading-relaxed shadow-sm
                    ${enviado ? 'text-white' : 'bg-white text-gray-800 border border-gray-200'}`}
                  style={{
                    borderRadius: enviado ? '16px 16px 4px 16px' : '16px 16px 16px 4px',
                    backgroundColor: enviado ? '#00B050' : undefined,
                  }}
                >
                  {m.media_url && (
                    <div className={`mb-1.5 ${mediaType === 'audio' ? 'w-full' : ''}`}>
                      <MediaBubble url={m.media_url} enviado={enviado} />
                    </div>
                  )}
                  {m.texto && (
                    <span className="whitespace-pre-wrap break-words">{m.texto}</span>
                  )}
                </div>
                <div className={`flex items-center gap-1 mt-0.5 ${enviado ? 'justify-end' : 'justify-start'}`}>
                  <span className="text-[9px] text-gray-400">{formatMsgTime(m.timestamp)}</span>
                  {enviado && (
                    <svg className="w-3 h-3 text-green-300" fill="currentColor" viewBox="0 0 24 24">
                      <path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z" />
                    </svg>
                  )}
                </div>
              </div>
            </div>
          );
        })}

        <div ref={messagesEndRef} />
      </div>

      {/* Closed notice */}
      {isClosed && (
        <div className="flex items-center justify-center gap-2 px-4 py-2 bg-gray-100 border-t border-gray-200 flex-shrink-0">
          <svg className="w-3.5 h-3.5 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
              d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
          </svg>
          <span className="text-[11px] text-gray-500">Ticket finalizado — envio desabilitado</span>
        </div>
      )}

      {/* Quick pills */}
      {!isClosed && (
        <div className="flex items-center gap-2 px-4 pb-2 pt-1 bg-gray-50 flex-shrink-0 overflow-x-auto">
          {quickPills.map((pill) => (
            <button
              key={pill.label}
              type="button"
              onClick={() => onInputChange(pill.msg)}
              className="flex items-center gap-1 px-2.5 py-1 text-[10px] font-medium text-gray-600
                         bg-white border border-gray-200 rounded-full hover:border-green-300
                         hover:text-green-700 transition-colors whitespace-nowrap flex-shrink-0"
            >
              {pill.label}
            </button>
          ))}
        </div>
      )}

      {/* Input bar */}
      {!isClosed && (
        <div
          className="px-4 bg-gray-50 flex-shrink-0"
          style={{ paddingBottom: 'max(1rem, env(safe-area-inset-bottom))' }}
        >
          <div className="flex items-end gap-2 bg-white border border-gray-200 rounded-2xl
                          shadow-sm px-3 py-2 focus-within:border-green-400 focus-within:ring-2
                          focus-within:ring-green-100 transition-all">
            <textarea
              ref={inputRef}
              value={inputTexto}
              onChange={(e) => onInputChange(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Digite uma mensagem... (Enter para enviar)"
              aria-label="Mensagem"
              rows={1}
              className="flex-1 resize-none text-xs text-gray-900 placeholder:text-gray-400
                         bg-transparent focus:outline-none leading-relaxed max-h-32"
              style={{ minHeight: '20px' }}
            />
            <button
              type="button"
              onClick={onSend}
              disabled={sending || !inputTexto.trim()}
              aria-label="Enviar mensagem"
              className="flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center
                         transition-all disabled:opacity-40 disabled:cursor-not-allowed"
              style={{ backgroundColor: '#00B050' }}
            >
              {sending ? (
                <div className="w-4 h-4 border-2 border-white/40 border-t-white rounded-full animate-spin" />
              ) : (
                <svg className="w-4 h-4 text-white translate-x-0.5" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z" />
                </svg>
              )}
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Main page component
// ---------------------------------------------------------------------------

export default function InboxPage() {
  // Inbox list
  const [tickets, setTickets] = useState<InboxTicket[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastRefreshedList, setLastRefreshedList] = useState<Date | null>(null);
  const [refreshingList, setRefreshingList] = useState(false);

  // Selection
  const [selectedTicket, setSelectedTicket] = useState<InboxTicket | null>(null);

  // Messages
  const [mensagens, setMensagens] = useState<DeskrioMensagem[]>([]);
  const [loadingMensagens, setLoadingMensagens] = useState(false);
  const [refreshingMensagens, setRefreshingMensagens] = useState(false);
  const [lastRefreshedMensagens, setLastRefreshedMensagens] = useState<Date | null>(null);

  // Input
  const [inputTexto, setInputTexto] = useState('');
  const [sending, setSending] = useState(false);

  // UI
  const [busca, setBusca] = useState('');
  const [filterTab, setFilterTab] = useState<FilterTab>('todos');
  const [mobileView, setMobileView] = useState<'list' | 'chat'>('list');

  // WhatsApp connection status
  const [waStatus, setWaStatus] = useState<WhatsAppStatus | null>(null);

  // Histórico do banco — fallback quando Deskrio offline (waConnecting)
  const [historicoFallback, setHistoricoFallback] = useState<AtendimentoInboxItem[] | null>(null);

  // Stable refs to avoid stale closures in intervals
  const selectedTicketRef = useRef<InboxTicket | null>(null);
  selectedTicketRef.current = selectedTicket;

  // Ticker to force "Atualizado ha Xs" re-renders
  const [, setTick] = useState(0);

  // ---------------------------------------------------------------------------
  // Load inbox
  // ---------------------------------------------------------------------------

  const loadInbox = useCallback(async (silent = false) => {
    if (!silent) setLoading(true);
    else setRefreshingList(true);
    setError(null);
    try {
      const data = await fetchInbox(7);
      // Sort: most recent first
      const sorted = [...data.tickets].sort((a, b) => {
        const da = a.ultima_mensagem_data ?? a.ultima_msg_cliente_data ?? '';
        const db = b.ultima_mensagem_data ?? b.ultima_msg_cliente_data ?? '';
        return db.localeCompare(da);
      });
      setTickets(sorted);
      setLastRefreshedList(new Date());
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Erro ao carregar inbox');
    } finally {
      if (!silent) setLoading(false);
      else setRefreshingList(false);
    }
  }, []);

  useEffect(() => {
    loadInbox(false);
  }, [loadInbox]);

  // Fetch WA status once on mount (fire-and-forget — does not block inbox)
  useEffect(() => {
    fetchWhatsAppStatus()
      .then(setWaStatus)
      .catch(() => setWaStatus(null));
  }, []);

  // Derive WA connection state once (used by fallback effect)
  const waConnectingDerived =
    waStatus !== null && waStatus.configurado && !waStatus.alguma_conectada;
  const waOnlineDerived =
    waStatus !== null && waStatus.configurado && waStatus.alguma_conectada;

  // Fallback histórico — carrega quando Deskrio offline (zero conexões WhatsApp).
  // Online: limpa fallback (live data manda).
  // waStatus ainda nao chegou (null): nao faz nada.
  useEffect(() => {
    if (waOnlineDerived) {
      setHistoricoFallback(null);
      return;
    }
    if (!waConnectingDerived) {
      // Status nao carregou ou backend offline: nao popula fallback.
      return;
    }
    let cancelled = false;
    fetchAtendimentosInbox({ page_size: 100 })
      .then((res) => {
        if (!cancelled) setHistoricoFallback(res.itens);
      })
      .catch(() => {
        if (!cancelled) setHistoricoFallback([]);
      });
    return () => {
      cancelled = true;
    };
  }, [waConnectingDerived, waOnlineDerived]);

  // ---------------------------------------------------------------------------
  // Load messages for selected ticket
  // ---------------------------------------------------------------------------

  const loadMensagens = useCallback(async (ticketId: number, silent = false) => {
    if (!silent) setLoadingMensagens(true);
    else setRefreshingMensagens(true);

    try {
      const data = await fetchTicketMensagens(ticketId, 1);
      setMensagens(data.messages ?? []);
      setLastRefreshedMensagens(new Date());
    } catch {
      // keep existing messages on silent refresh failure
      if (!silent) setMensagens([]);
    } finally {
      if (!silent) setLoadingMensagens(false);
      else setRefreshingMensagens(false);
    }
  }, []);

  // ---------------------------------------------------------------------------
  // Select ticket
  // ---------------------------------------------------------------------------

  async function handleSelectTicket(t: InboxTicket) {
    setSelectedTicket(t);
    setMobileView('chat');
    setMensagens([]);
    setInputTexto('');
    setLastRefreshedMensagens(null);
    await loadMensagens(t.ticket_id, false);
  }

  // ---------------------------------------------------------------------------
  // Manual refresh handlers
  // ---------------------------------------------------------------------------

  async function handleRefreshList() {
    await loadInbox(true);
  }

  async function handleRefreshMensagens() {
    const t = selectedTicketRef.current;
    if (!t) return;
    await loadMensagens(t.ticket_id, true);
  }

  // ---------------------------------------------------------------------------
  // Auto-polling — 30s
  // ---------------------------------------------------------------------------

  useEffect(() => {
    const interval = setInterval(() => {
      if (document.hidden) return;
      // Always refresh the list
      loadInbox(true);
      // If a ticket is selected, refresh its messages too
      const t = selectedTicketRef.current;
      if (t) loadMensagens(t.ticket_id, true);
    }, POLL_INTERVAL_MS);
    return () => clearInterval(interval);
  }, [loadInbox, loadMensagens]);

  // Ticker: re-render "Atualizado ha Xs" every 10s
  useEffect(() => {
    const ticker = setInterval(() => setTick((n) => n + 1), 10_000);
    return () => clearInterval(ticker);
  }, []);

  // ---------------------------------------------------------------------------
  // Send message
  // ---------------------------------------------------------------------------

  async function handleSend() {
    const texto = inputTexto.trim();
    if (!texto || !selectedTicket || sending) return;

    // Optimistic: add a temp message immediately
    const tempMsg: DeskrioMensagem = {
      id: -Date.now(),
      texto,
      de_cliente: false,
      timestamp: new Date().toISOString(),
      tipo: 'chat',
    };
    setMensagens((prev) => [...prev, tempMsg]);
    setInputTexto('');
    setSending(true);

    try {
      const token = getToken();
      const res = await fetch(`${BASE_URL}/api/whatsapp/enviar`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: JSON.stringify({
          ticket_id: selectedTicket.ticket_id,
          mensagem: texto,
        }),
      });
      if (!res.ok) throw new Error('Erro ao enviar');
    } catch {
      // Revert optimistic on error
      setMensagens((prev) => prev.filter((m) => m.id !== tempMsg.id));
      setInputTexto(texto);
    } finally {
      setSending(false);
    }
  }

  // ---------------------------------------------------------------------------
  // Render
  // ---------------------------------------------------------------------------

  return (
    /*
     * Break out of the AppShell padding (max-w-screen-2xl p-3 lg:p-6)
     * to fill the full content area edge-to-edge.
     * Height = 100vh minus the AppShell header (~49px).
     */
    <div
      className="-m-3 lg:-m-6 flex"
      style={{ height: 'calc(100vh - 49px)' }}
    >
      {/* LEFT — conversation list */}
      <div
        className={`${mobileView === 'chat' ? 'hidden md:flex' : 'flex'} md:flex flex-col flex-shrink-0 w-full md:w-80`}
      >
        <ConversationList
          tickets={tickets}
          loading={loading}
          error={error}
          selectedId={selectedTicket?.ticket_id ?? null}
          busca={busca}
          filterTab={filterTab}
          lastRefreshed={lastRefreshedList}
          refreshing={refreshingList}
          waStatus={waStatus}
          historicoFallback={historicoFallback}
          onBuscaChange={setBusca}
          onFilterTab={setFilterTab}
          onSelect={handleSelectTicket}
          onRefresh={handleRefreshList}
        />
      </div>

      {/* RIGHT — chat */}
      <div
        className={`${mobileView === 'list' ? 'hidden md:flex' : 'flex'} md:flex flex-1 min-w-0`}
      >
        <ChatPanel
          ticket={selectedTicket}
          mensagens={mensagens}
          loading={loadingMensagens}
          refreshing={refreshingMensagens}
          inputTexto={inputTexto}
          sending={sending}
          lastRefreshed={lastRefreshedMensagens}
          onInputChange={setInputTexto}
          onSend={handleSend}
          onBack={() => setMobileView('list')}
          showBack={mobileView === 'chat'}
          onRefresh={handleRefreshMensagens}
        />
      </div>
    </div>
  );
}
