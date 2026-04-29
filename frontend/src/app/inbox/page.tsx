'use client';

/**
 * CRM VITAO360 — Inbox Page (3-column WhatsApp-like layout)
 *
 * Layout (desktop):
 *   Conversas | Chat | Painel cliente Mercos
 *
 * Mobile: 1 coluna por vez via state mobileView (list | chat | painel).
 *
 * Auth: 'use client' com useAuth() — fetches só rodam após user resolver.
 * Empty UX: sem fallback DB; quando Deskrio offline mostra banner discreto.
 *
 * Regras: R5 (CNPJ string), R8 (zero fabricação), R9 (tema light + cores Vitão).
 */

import { useCallback, useEffect, useRef, useState } from 'react';

import { useAuth } from '@/contexts/AuthContext';
import { Badge } from '@/components/ui/Badge';
import {
  fetchInbox,
  fetchTicketMensagens,
  fetchWhatsAppStatus,
  fetchCliente,
  enviarWhatsApp,
  formatBRL,
  formatDateBR,
  type InboxTicket,
  type DeskrioMensagem,
  type WhatsAppStatus,
  type ClienteRegistro,
} from '@/lib/api';

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const POLL_INTERVAL_MS = 30_000;

type FilterTab = 'todos' | 'aguardando' | 'atendimento' | 'finalizados';
type MobileView = 'list' | 'chat' | 'painel';

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function getInitials(nome: string): string {
  return (nome || '?')
    .trim()
    .split(/\s+/)
    .slice(0, 2)
    .map((w) => w.charAt(0).toUpperCase())
    .join('');
}

function formatTime(dateStr: string | null | undefined): string {
  if (!dateStr) return '';
  try {
    const d = new Date(dateStr);
    if (Number.isNaN(d.getTime())) return '';
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
    if (Number.isNaN(d.getTime())) return '';
    return d.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' });
  } catch {
    return '';
  }
}

function formatCNPJ(cnpj: string | null | undefined): string {
  if (!cnpj) return '';
  const d = cnpj.replace(/\D/g, '').padStart(14, '0');
  if (d.length !== 14) return cnpj;
  return `${d.slice(0, 2)}.${d.slice(2, 5)}.${d.slice(5, 8)}/${d.slice(8, 12)}-${d.slice(12)}`;
}

function formatPhone(num: string | null | undefined): string {
  if (!num) return '';
  return num.replace(/^55/, '+55 ').replace(/(\d{2})(\d{5})(\d{4})/, '($1) $2-$3');
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
  return clean.length <= max ? clean : `${clean.slice(0, max)}...`;
}

// ---------------------------------------------------------------------------
// Media bubble (suporte a áudio/imagem/vídeo/documento)
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
        className={`flex items-center gap-2 px-3 py-2 rounded-xl text-xs font-medium underline ${
          enviado ? 'text-white/90' : 'text-vitao-darkgreen'
        }`}
      >
        <svg className="w-4 h-4 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z"
          />
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
          className="block focus:outline-none focus:ring-2 focus:ring-vitao-green rounded-xl overflow-hidden"
          aria-label="Ampliar imagem"
        >
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img
            src={url}
            alt="Imagem WhatsApp"
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
              className="absolute top-4 right-4 text-white bg-black/50 rounded-full p-2 hover:bg-black/70 transition-colors"
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
        <audio controls src={url} className="w-full rounded-lg" style={{ height: '36px', minWidth: '220px' }} />
      </div>
    );
  }

  if (mediaType === 'video') {
    return (
      <div style={{ maxWidth: '300px' }}>
        {/* eslint-disable-next-line jsx-a11y/media-has-caption */}
        <video controls src={url} className="rounded-xl object-cover" style={{ maxWidth: '300px', maxHeight: '220px', display: 'block' }} />
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
      className={`flex items-center gap-2.5 px-3 py-2.5 rounded-xl border text-xs font-medium transition-colors hover:opacity-80 ${
        enviado ? 'border-white/30 text-white bg-white/10' : 'border-gray-200 text-gray-700 bg-gray-50 hover:bg-gray-100'
      }`}
      style={{ maxWidth: '260px' }}
      download
    >
      <svg className="w-5 h-5 flex-shrink-0 text-vitao-green" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={1.5}
          d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z"
        />
      </svg>
      <span className="truncate">{fileName}</span>
    </a>
  );
}

// ---------------------------------------------------------------------------
// Avatar + status dot
// ---------------------------------------------------------------------------

interface AvatarProps {
  nome: string;
  size?: 'sm' | 'md' | 'lg';
}

function Avatar({ nome, size = 'md' }: AvatarProps) {
  const dim =
    size === 'sm'
      ? 'w-8 h-8 text-[10px]'
      : size === 'lg'
        ? 'w-12 h-12 text-sm'
        : 'w-10 h-10 text-xs';
  return (
    <div
      className={`${dim} rounded-full flex items-center justify-center flex-shrink-0 text-white font-bold bg-vitao-green`}
    >
      {getInitials(nome)}
    </div>
  );
}

function StatusDot({ ticket }: { ticket: InboxTicket }) {
  if (ticket.status === 'closed' || ticket.status === 'resolved') {
    return (
      <span title="Finalizado">
        <span className="w-2 h-2 rounded-full bg-gray-400 inline-block ring-2 ring-white" />
      </span>
    );
  }
  if (ticket.aguardando_resposta) {
    return (
      <span title="Aguardando resposta">
        <span className="w-2 h-2 rounded-full bg-vitao-orange inline-block ring-2 ring-white" />
      </span>
    );
  }
  return (
    <span title="Em atendimento">
      <span className="w-2 h-2 rounded-full bg-vitao-green inline-block ring-2 ring-white" />
    </span>
  );
}

function StatusBadge({ ticket }: { ticket: InboxTicket }) {
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
        <span className="w-1.5 h-1.5 rounded-full bg-vitao-orange animate-pulse" />
        <span className="text-[10px] font-medium text-orange-700">Aguardando</span>
      </span>
    );
  }
  return (
    <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-vitao-lightgreen border border-green-200">
      <span className="w-1.5 h-1.5 rounded-full bg-vitao-green" />
      <span className="text-[10px] font-medium text-vitao-darkgreen">Em atendimento</span>
    </span>
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
// Coluna 1 — Lista de conversas
// ---------------------------------------------------------------------------

interface ColunaListaProps {
  tickets: InboxTicket[];
  loading: boolean;
  selectedId: number | null;
  busca: string;
  setBusca: (v: string) => void;
  filterTab: FilterTab;
  setFilterTab: (t: FilterTab) => void;
  waStatus: WhatsAppStatus | null;
  onSelect: (t: InboxTicket) => void;
  onRefresh: () => void;
  refreshing: boolean;
}

function ColunaLista({
  tickets,
  loading,
  selectedId,
  busca,
  setBusca,
  filterTab,
  setFilterTab,
  waStatus,
  onSelect,
  onRefresh,
  refreshing,
}: ColunaListaProps) {
  const tabs: { key: FilterTab; label: string }[] = [
    { key: 'todos', label: 'Todos' },
    { key: 'aguardando', label: 'Aguard.' },
    { key: 'atendimento', label: 'Em Atend.' },
    { key: 'finalizados', label: 'Finaliz.' },
  ];

  const filtered = tickets.filter((t) => {
    const matchBusca =
      !busca.trim() ||
      (t.contato_nome ?? '').toLowerCase().includes(busca.toLowerCase()) ||
      (t.contato_numero ?? '').includes(busca);
    if (!matchBusca) return false;
    if (filterTab === 'aguardando') return t.aguardando_resposta && t.status === 'open';
    if (filterTab === 'atendimento') return !t.aguardando_resposta && t.status === 'open';
    if (filterTab === 'finalizados') return t.status === 'closed' || t.status === 'resolved';
    return true;
  });

  const countAguardando = tickets.filter((t) => t.aguardando_resposta && t.status === 'open').length;

  const waOnline = waStatus !== null && waStatus.configurado && waStatus.alguma_conectada;
  const waConnecting = waStatus !== null && waStatus.configurado && !waStatus.alguma_conectada;
  const waOffline = waStatus !== null && !waStatus.configurado;

  return (
    <>
      {/* Header */}
      <div className="px-4 pt-3 pb-2 border-b border-gray-100 flex-shrink-0">
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center gap-2">
            <svg className="w-4 h-4" viewBox="0 0 24 24" fill="#00A859" aria-hidden="true">
              <path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413z" />
            </svg>
            <h2 className="text-sm font-bold text-gray-900">Conversas</h2>
            <span
              className={`text-[10px] font-bold px-1.5 py-0.5 rounded-full ${
                tickets.length > 0 ? 'bg-vitao-lightgreen text-vitao-darkgreen' : 'bg-gray-100 text-gray-500'
              }`}
            >
              {tickets.length}
            </span>
          </div>
          <div className="flex items-center gap-2">
            {waOnline && (() => {
              const ativas = waStatus!.conexoes.filter((c) => c.status === 'CONNECTED');
              const tooltip = ativas.length > 0
                ? `${ativas.length} de ${waStatus!.total_conexoes} conexões ativas: ${ativas.map((c) => c.nome).join(', ')}`
                : 'WhatsApp conectado';
              return (
                <Badge variant="success" size="xs" dot title={tooltip}>
                  WhatsApp conectado
                </Badge>
              );
            })()}
            {waConnecting && (
              <Badge variant="warning" size="xs" dot title="WhatsApp configurado mas sem conexões ativas. Reconecte no Deskrio.">
                Sem conexão ativa
              </Badge>
            )}
            {waOffline && (
              <Badge variant="neutral" size="xs" dot title="WhatsApp não configurado no Deskrio">
                Offline
              </Badge>
            )}
            <button
              type="button"
              onClick={onRefresh}
              disabled={refreshing}
              aria-label="Atualizar"
              className="p-1 rounded-md text-gray-400 hover:text-gray-600 hover:bg-gray-100 transition-colors disabled:opacity-40"
            >
              <svg
                className={`w-3.5 h-3.5 ${refreshing ? 'animate-spin' : ''}`}
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
                />
              </svg>
            </button>
          </div>
        </div>

        {/* Busca */}
        <div className="relative mb-2">
          <svg
            className="absolute left-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-gray-400 pointer-events-none"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
          </svg>
          <input
            type="search"
            value={busca}
            onChange={(e) => setBusca(e.target.value)}
            placeholder="Buscar conversa..."
            aria-label="Buscar conversa"
            className="w-full pl-8 pr-3 py-2 text-xs border border-gray-200 rounded-lg bg-gray-50 focus:outline-none focus:ring-2 focus:ring-vitao-green/40 focus:border-vitao-green placeholder:text-gray-400"
          />
        </div>

        {/* Tabs */}
        <div className="flex gap-0.5 bg-gray-100 rounded-lg p-0.5">
          {tabs.map((tab) => (
            <button
              key={tab.key}
              type="button"
              onClick={() => setFilterTab(tab.key)}
              className={`flex-1 flex items-center justify-center gap-1 py-1 rounded-md text-[10px] font-semibold transition-colors focus:outline-none ${
                filterTab === tab.key ? 'bg-vitao-green text-white shadow-sm' : 'text-gray-600 hover:text-gray-800'
              }`}
            >
              {tab.label}
              {tab.key === 'aguardando' && countAguardando > 0 && (
                <span
                  className={`text-[8px] font-bold px-1 py-0.5 rounded-full leading-none min-w-[14px] text-center ${
                    filterTab === tab.key ? 'bg-white text-vitao-darkgreen' : 'bg-vitao-orange text-white'
                  }`}
                >
                  {countAguardando}
                </span>
              )}
            </button>
          ))}
        </div>
      </div>

      {/* Banner WhatsApp offline (discreto) */}
      {(waConnecting || waOffline) && (
        <div className="px-3 py-2 bg-amber-50 border-b border-amber-200 flex items-start gap-2 flex-shrink-0">
          <svg className="w-3.5 h-3.5 text-amber-600 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
            />
          </svg>
          <div className="flex-1 min-w-0">
            <p className="text-[11px] font-semibold text-amber-900">
              {waConnecting ? 'Nenhuma conexão WhatsApp ativa. Verifique no Deskrio.' : 'WhatsApp não configurado'}
            </p>
            {waConnecting && (
              <a
                href="https://web.deskrio.com.br"
                target="_blank"
                rel="noopener noreferrer"
                className="text-[10px] text-amber-700 underline hover:text-amber-900"
              >
                Reconectar →
              </a>
            )}
          </div>
        </div>
      )}

      {/* Lista */}
      <div className="flex-1 overflow-y-auto" style={{ scrollbarWidth: 'thin' }}>
        {loading && (
          <div>
            {[...Array(8)].map((_, i) => (
              <SkeletonRow key={i} />
            ))}
          </div>
        )}

        {!loading && filtered.length === 0 && (
          <div className="flex flex-col items-center justify-center py-16 px-6 text-center">
            <svg className="w-12 h-12 text-gray-300 mb-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={1.5}
                d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z"
              />
            </svg>
            <p className="text-sm font-medium text-gray-500">Nenhuma conversa</p>
            <p className="text-xs text-gray-400 mt-1">
              {busca
                ? 'Tente outro termo de busca'
                : filterTab !== 'todos'
                  ? 'Tente outro filtro'
                  : 'Nenhuma conversa nos últimos 6 dias.'}
            </p>
          </div>
        )}

        {!loading &&
          filtered.map((t) => (
            <ItemConversa key={t.ticket_id} ticket={t} selected={selectedId === t.ticket_id} onClick={() => onSelect(t)} />
          ))}
      </div>
    </>
  );
}

// ---------------------------------------------------------------------------
// Item de conversa
// ---------------------------------------------------------------------------

interface ItemConversaProps {
  ticket: InboxTicket;
  selected: boolean;
  onClick: () => void;
}

function ItemConversa({ ticket, selected, onClick }: ItemConversaProps) {
  const isAguardando = ticket.aguardando_resposta && ticket.status === 'open';
  const naoLidas = ticket.mensagens_nao_lidas ?? 0;

  return (
    <button
      type="button"
      onClick={onClick}
      aria-pressed={selected}
      className={`w-full flex items-start gap-3 px-3 py-3 text-left border-b border-gray-50 transition-colors hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-inset focus:ring-vitao-green/40 relative ${
        selected ? 'bg-vitao-lightgreen' : ''
      } ${
        isAguardando
          ? 'border-l-2 border-l-vitao-orange'
          : selected
            ? 'border-l-2 border-l-vitao-green'
            : 'border-l-2 border-l-transparent'
      }`}
    >
      <div className="relative flex-shrink-0 mt-0.5">
        <Avatar nome={ticket.contato_nome} size="md" />
        <span className="absolute -bottom-0.5 -right-0.5">
          <StatusDot ticket={ticket} />
        </span>
      </div>

      <div className="flex-1 min-w-0">
        <div className="flex items-start justify-between gap-1 mb-0.5">
          <p className={`text-xs text-gray-900 truncate leading-tight ${naoLidas > 0 ? 'font-bold' : 'font-semibold'}`}>
            {ticket.contato_nome || '(sem nome)'}
          </p>
          <div className="flex items-center gap-1 flex-shrink-0">
            {naoLidas > 0 && (
              <span className="bg-vitao-green text-white text-[9px] font-bold w-4 h-4 rounded-full flex items-center justify-center">
                {naoLidas > 9 ? '9+' : naoLidas}
              </span>
            )}
            <span className="text-[10px] text-gray-400">{formatTime(ticket.ultima_mensagem_data ?? ticket.ultima_msg_cliente_data)}</span>
          </div>
        </div>

        <p className={`text-[11px] truncate leading-tight mb-1 ${naoLidas > 0 ? 'text-gray-800 font-medium' : 'text-gray-500'}`}>
          {ticket.ultima_mensagem ? truncatePreview(ticket.ultima_mensagem) : ' '}
        </p>

        <div className="flex items-center gap-1.5">
          {ticket.atendente_nome && (
            <span className="text-[9px] text-gray-400 truncate">
              {ticket.atendente_nome.replace(/-\s*Vitao/i, '').trim()}
            </span>
          )}
          {ticket.atendente_nome && ticket.origem && <span className="text-[9px] text-gray-300">·</span>}
          {ticket.origem && <span className="text-[9px] text-gray-400">{ticket.origem}</span>}
        </div>
      </div>
    </button>
  );
}

// ---------------------------------------------------------------------------
// Coluna 2 — Chat
// ---------------------------------------------------------------------------

interface ColunaChatProps {
  ticket: InboxTicket | null;
  mensagens: DeskrioMensagem[];
  loading: boolean;
  refreshing: boolean;
  inputTexto: string;
  setInputTexto: (v: string) => void;
  sending: boolean;
  onEnviar: () => void;
  onVoltarMobile: () => void;
  onVerPainelMobile: () => void;
  onRefresh: () => void;
  showMobileBack: boolean;
}

function ColunaChat({
  ticket,
  mensagens,
  loading,
  refreshing,
  inputTexto,
  setInputTexto,
  sending,
  onEnviar,
  onVoltarMobile,
  onVerPainelMobile,
  onRefresh,
  showMobileBack,
}: ColunaChatProps) {
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [mensagens]);

  function handleKeyDown(e: React.KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      if (!sending && inputTexto.trim()) onEnviar();
    }
  }

  const quickPills = [
    { label: '📋 Catálogo', msg: 'Olá! Posso te enviar o catálogo de produtos atualizado?' },
    { label: '💰 Tabela', msg: 'Vou enviar nossa tabela de preços. Tem alguma linha de interesse?' },
    { label: '🚚 Prazo Entrega', msg: 'Nosso prazo de entrega é de 5 a 7 dias úteis após confirmação do pagamento.' },
  ];

  if (!ticket) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center bg-gray-50 px-6">
        <div className="w-16 h-16 rounded-full flex items-center justify-center mb-4 bg-vitao-lightgreen">
          <svg className="w-8 h-8 text-vitao-green" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={1.5}
              d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z"
            />
          </svg>
        </div>
        <h3 className="text-sm font-semibold text-gray-700">Selecione uma conversa</h3>
        <p className="text-xs text-gray-400 mt-1 text-center">Escolha um ticket na lista ao lado para ver o histórico</p>
      </div>
    );
  }

  const isClosed = ticket.status === 'closed' || ticket.status === 'resolved';
  const semCnpj = !ticket.cnpj;

  return (
    <>
      {/* Header */}
      <div className="flex items-center gap-3 px-4 py-3 bg-white border-b border-gray-200 flex-shrink-0">
        {showMobileBack && (
          <button
            type="button"
            onClick={onVoltarMobile}
            aria-label="Voltar"
            className="p-1.5 rounded-lg text-gray-500 hover:bg-gray-100 transition-colors lg:hidden"
          >
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
            </svg>
          </button>
        )}

        <Avatar nome={ticket.contato_nome} size="md" />

        <div className="flex-1 min-w-0">
          <p className="text-sm font-semibold text-gray-900 truncate leading-tight">{ticket.contato_nome || '(sem nome)'}</p>
          <div className="flex items-center gap-1.5">
            <span className="w-1.5 h-1.5 rounded-full bg-vitao-green animate-pulse inline-block" />
            <span className="text-[11px] text-vitao-darkgreen">Online agora</span>
            <span className="text-[10px] text-gray-300">·</span>
            <span className="text-[10px] text-gray-400 truncate">{formatPhone(ticket.contato_numero)}</span>
          </div>
        </div>

        <div className="flex items-center gap-2 flex-shrink-0">
          <StatusBadge ticket={ticket} />
          <button
            type="button"
            onClick={onVerPainelMobile}
            aria-label="Ver painel cliente"
            className="lg:hidden p-1.5 rounded-lg text-gray-500 hover:bg-gray-100 transition-colors"
          >
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
              />
            </svg>
          </button>
          {refreshing && <div className="w-3.5 h-3.5 border-2 border-gray-200 border-t-vitao-green rounded-full animate-spin" />}
          <button
            type="button"
            onClick={onRefresh}
            disabled={loading || refreshing}
            aria-label="Atualizar mensagens"
            className="hidden md:inline-flex p-1.5 rounded-lg text-gray-400 hover:text-gray-600 hover:bg-gray-100 transition-colors disabled:opacity-40"
          >
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
              />
            </svg>
          </button>
          <span className="text-[9px] text-gray-300 hidden lg:inline" title="ID do ticket Deskrio">
            #{ticket.ticket_id}
          </span>
        </div>
      </div>

      {/* Mensagens */}
      <div className="flex-1 overflow-y-auto px-4 py-4 space-y-3 bg-gray-50" style={{ scrollbarWidth: 'thin' }}>
        {loading && (
          <div className="flex justify-center py-8">
            <div className="w-5 h-5 border-2 border-gray-200 border-t-vitao-green rounded-full animate-spin" />
          </div>
        )}

        {!loading && mensagens.length === 0 && (
          <div className="flex flex-col items-center justify-center h-32 text-center">
            <svg className="w-8 h-8 text-gray-200 mb-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={1.5}
                d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z"
              />
            </svg>
            <p className="text-xs font-medium text-gray-500">Sem mensagens ainda</p>
          </div>
        )}

        {!loading &&
          mensagens.map((m) => (
            <BolhaMensagem key={m.id} msg={m} contatoNome={ticket.contato_nome} />
          ))}

        <div ref={messagesEndRef} />
      </div>

      {/* Closed notice */}
      {isClosed && (
        <div className="flex items-center justify-center gap-2 px-4 py-2 bg-gray-100 border-t border-gray-200 flex-shrink-0">
          <svg className="w-3.5 h-3.5 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"
            />
          </svg>
          <span className="text-[11px] text-gray-500">Ticket finalizado — envio desabilitado</span>
        </div>
      )}

      {!isClosed && semCnpj && (
        <div className="flex items-center justify-center gap-2 px-4 py-2 bg-amber-50 border-t border-amber-200 flex-shrink-0">
          <svg className="w-3.5 h-3.5 text-amber-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
            />
          </svg>
          <span className="text-[11px] text-amber-800">
            Contato sem CNPJ vinculado — envio desabilitado. Cadastre o telefone do cliente em Carteira.
          </span>
        </div>
      )}

      {/* Quick pills */}
      {!isClosed && !semCnpj && (
        <div className="flex items-center gap-2 px-4 pb-2 pt-2 bg-white border-t border-gray-100 flex-shrink-0 overflow-x-auto">
          {quickPills.map((pill) => (
            <button
              key={pill.label}
              type="button"
              onClick={() => setInputTexto(pill.msg)}
              className="flex items-center gap-1 px-3 py-1 text-[11px] font-medium text-gray-700 bg-gray-100 border border-gray-200 rounded-full hover:bg-vitao-lightgreen hover:border-vitao-green hover:text-vitao-darkgreen transition-colors whitespace-nowrap flex-shrink-0"
            >
              {pill.label}
            </button>
          ))}
        </div>
      )}

      {/* Input */}
      {!isClosed && !semCnpj && (
        <div
          className="px-4 bg-white border-t border-gray-100 flex-shrink-0"
          style={{ paddingTop: '0.5rem', paddingBottom: 'max(1rem, env(safe-area-inset-bottom))' }}
        >
          <div className="flex items-end gap-2 bg-gray-50 border border-gray-200 rounded-2xl shadow-sm px-3 py-2 focus-within:border-vitao-green focus-within:ring-2 focus-within:ring-vitao-green/20 transition-all">
            <textarea
              ref={inputRef}
              value={inputTexto}
              onChange={(e) => setInputTexto(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Digite uma mensagem... (Enter para enviar)"
              aria-label="Mensagem"
              rows={1}
              disabled={sending}
              className="flex-1 resize-none text-xs text-gray-900 placeholder:text-gray-400 bg-transparent focus:outline-none leading-relaxed max-h-32 disabled:opacity-50"
              style={{ minHeight: '20px' }}
            />
            <button
              type="button"
              onClick={onEnviar}
              disabled={sending || !inputTexto.trim()}
              aria-label="Enviar mensagem"
              className="flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center bg-vitao-green hover:bg-vitao-darkgreen transition-all disabled:opacity-40 disabled:cursor-not-allowed"
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
    </>
  );
}

// ---------------------------------------------------------------------------
// Bolha de mensagem
// ---------------------------------------------------------------------------

function BolhaMensagem({ msg, contatoNome }: { msg: DeskrioMensagem; contatoNome: string }) {
  const enviado = !msg.de_cliente;
  const mediaType = msg.media_url ? getMediaType(msg.media_url) : null;

  return (
    <div className={`flex ${enviado ? 'justify-end' : 'justify-start'}`}>
      {!enviado && (
        <div className="w-6 h-6 rounded-full flex items-center justify-center flex-shrink-0 text-white text-[9px] font-bold mr-2 mt-auto mb-0.5 bg-gray-400">
          {getInitials(msg.nome_contato ?? contatoNome)}
        </div>
      )}

      <div className="max-w-xs lg:max-w-sm xl:max-w-md">
        {enviado && msg.nome_contato && (
          <p className="text-[9px] text-gray-400 text-right mb-0.5 mr-1 truncate max-w-[200px] ml-auto">
            {msg.nome_contato.replace(/-\s*Vitao/i, '').trim()}
          </p>
        )}
        <div
          className={`px-3 py-2 text-xs leading-relaxed shadow-sm ${
            enviado ? 'bg-vitao-green text-white' : 'bg-white text-gray-800 border border-gray-200'
          }`}
          style={{ borderRadius: enviado ? '16px 16px 4px 16px' : '16px 16px 16px 4px' }}
        >
          {msg.media_url && (
            <div className={`mb-1.5 ${mediaType === 'audio' ? 'w-full' : ''}`}>
              <MediaBubble url={msg.media_url} enviado={enviado} />
            </div>
          )}
          {msg.texto && <span className="whitespace-pre-wrap break-words">{msg.texto}</span>}
        </div>
        <div className={`flex items-center gap-1 mt-0.5 ${enviado ? 'justify-end' : 'justify-start'}`}>
          <span className="text-[9px] text-gray-400">{formatMsgTime(msg.timestamp)}</span>
          {enviado && (
            <svg className="w-3 h-3 text-vitao-green/70" fill="currentColor" viewBox="0 0 24 24">
              <path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z" />
            </svg>
          )}
        </div>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Coluna 3 — Painel cliente (Mercos)
// ---------------------------------------------------------------------------

interface ColunaPainelProps {
  ticket: InboxTicket | null;
  cliente: ClienteRegistro | null;
  loadingCliente: boolean;
  onVoltarMobile: () => void;
}

function ColunaPainel({ ticket, cliente, loadingCliente, onVoltarMobile }: ColunaPainelProps) {
  const cnpjFormatado = cliente?.cnpj ? formatCNPJ(cliente.cnpj) : ticket?.cnpj ? formatCNPJ(ticket.cnpj) : '—';
  const nomeExibir = cliente?.nome_fantasia ?? ticket?.contato_nome ?? 'Cliente';

  const ticketMedio = cliente?.ticket_medio;
  // ciclo_medio_dias pode chegar dentro do indexador [k:string]:unknown
  const cicloMedioRaw = (cliente as Record<string, unknown> | null | undefined)?.['ciclo_medio_dias'];
  const cicloMedio = typeof cicloMedioRaw === 'number' ? cicloMedioRaw : cliente?.ciclo_medio;
  const ultimaCompra = cliente?.ultima_compra;
  const curvaABC = cliente?.curva_abc;
  const consultor = cliente?.consultor;
  const fatTotal = cliente?.faturamento_total;
  const sinaleiro = cliente?.sinaleiro;
  const temperatura = cliente?.temperatura;
  const diasSemCompra = cliente?.dias_sem_compra;

  return (
    <>
      {/* Header mobile */}
      <div className="lg:hidden p-3 border-b border-gray-200 bg-white flex items-center gap-2 flex-shrink-0">
        <button
          type="button"
          onClick={onVoltarMobile}
          aria-label="Voltar para chat"
          className="p-1.5 rounded-lg text-gray-500 hover:bg-gray-100 transition-colors"
        >
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
          </svg>
        </button>
        <span className="text-sm font-semibold text-gray-900">Detalhes do cliente</span>
      </div>

      {!ticket ? (
        <div className="p-4 flex-1 flex flex-col items-center justify-center text-center text-gray-400">
          <svg className="w-10 h-10 text-gray-200 mb-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={1.5}
              d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"
            />
          </svg>
          <p className="text-xs">Selecione uma conversa para ver os dados do cliente</p>
        </div>
      ) : (
        <div className="p-4 space-y-4 overflow-y-auto" style={{ scrollbarWidth: 'thin' }}>
          {/* Header cliente */}
          <div className="flex items-center gap-3 pb-3 border-b border-gray-100">
            <Avatar nome={nomeExibir} size="lg" />
            <div className="flex-1 min-w-0">
              <h3 className="text-sm font-bold text-gray-900 truncate">{nomeExibir}</h3>
              <p className="text-[11px] text-gray-500 truncate">{cnpjFormatado}</p>
              {consultor && (
                <p className="text-[10px] text-vitao-darkgreen font-medium truncate">Consultor: {consultor}</p>
              )}
            </div>
          </div>

          {!ticket.cnpj && (
            <div className="p-3 bg-amber-50 border border-amber-200 rounded-lg">
              <p className="text-[11px] text-amber-800">
                Este contato ainda não está vinculado a nenhum cliente cadastrado em Carteira. Para enriquecer com dados Mercos, cadastre o telefone na ficha do cliente.
              </p>
            </div>
          )}

          {ticket.cnpj && loadingCliente && (
            <div className="flex justify-center py-6">
              <div className="w-5 h-5 border-2 border-gray-200 border-t-vitao-green rounded-full animate-spin" />
            </div>
          )}

          {ticket.cnpj && !loadingCliente && !cliente && (
            <div className="p-3 bg-gray-50 border border-gray-200 rounded-lg">
              <p className="text-[11px] text-gray-600">
                Cliente não encontrado em Carteira. Pode ser um prospect novo ou estar fora do seu canal.
              </p>
            </div>
          )}

          {ticket.cnpj && !loadingCliente && cliente && (
            <>
              {/* Dados Mercos */}
              <div>
                <h4 className="text-[11px] font-semibold text-gray-700 uppercase tracking-wider mb-2">📊 Dados Mercos</h4>
                <div className="space-y-2">
                  <DadoRow
                    label="Ticket Médio"
                    value={ticketMedio != null && Number.isFinite(ticketMedio) ? formatBRL(ticketMedio) : '—'}
                    bg="bg-blue-50"
                    textColor="text-vitao-blue"
                  />
                  <DadoRow
                    label="Ciclo de Compra"
                    value={cicloMedio != null && Number.isFinite(cicloMedio) ? `${cicloMedio} dias` : '—'}
                    bg="bg-purple-50"
                    textColor="text-vitao-purple"
                  />
                  <DadoRow
                    label="Última Compra"
                    value={ultimaCompra ? formatDateBR(ultimaCompra) : '—'}
                    bg="bg-orange-50"
                    textColor="text-vitao-orange"
                  />
                  {diasSemCompra != null && (
                    <DadoRow
                      label="Dias sem comprar"
                      value={`${diasSemCompra}`}
                      bg="bg-gray-50"
                      textColor="text-gray-700"
                    />
                  )}
                  <DadoRow
                    label="Faturamento Total"
                    value={fatTotal != null && Number.isFinite(fatTotal) ? formatBRL(fatTotal) : '—'}
                    bg="bg-vitao-lightgreen"
                    textColor="text-vitao-darkgreen"
                  />
                  <DadoRow
                    label="Curva ABC"
                    value={curvaABC ?? '—'}
                    bg="bg-vitao-lightgreen"
                    textColor="text-vitao-darkgreen"
                    badge
                  />
                </div>
              </div>

              {/* Status comercial */}
              {(sinaleiro || temperatura) && (
                <div>
                  <h4 className="text-[11px] font-semibold text-gray-700 uppercase tracking-wider mb-2">🚦 Status Comercial</h4>
                  <div className="space-y-2">
                    {sinaleiro && <DadoRow label="Sinaleiro" value={sinaleiro} bg="bg-gray-50" textColor="text-gray-700" />}
                    {temperatura && <DadoRow label="Temperatura" value={temperatura} bg="bg-gray-50" textColor="text-gray-700" />}
                  </div>
                </div>
              )}

              {/* Atalhos */}
              <div>
                <h4 className="text-[11px] font-semibold text-gray-700 uppercase tracking-wider mb-2">🔗 Atalhos</h4>
                <div className="grid grid-cols-2 gap-2">
                  <a
                    href={`/carteira?busca=${encodeURIComponent(cliente.cnpj)}`}
                    className="px-3 py-2 bg-vitao-lightgreen text-vitao-darkgreen text-[11px] font-medium rounded-lg text-center hover:bg-green-100 transition-colors"
                  >
                    Ver na Carteira
                  </a>
                  <a
                    href={`/clientes/${cliente.cnpj}`}
                    className="px-3 py-2 bg-blue-50 text-vitao-blue text-[11px] font-medium rounded-lg text-center hover:bg-blue-100 transition-colors"
                  >
                    Ficha 360
                  </a>
                </div>
              </div>
            </>
          )}
        </div>
      )}
    </>
  );
}

interface DadoRowProps {
  label: string;
  value: string;
  bg: string;
  textColor: string;
  badge?: boolean;
}

function DadoRow({ label, value, bg, textColor, badge }: DadoRowProps) {
  return (
    <div className={`${bg} px-3 py-2 rounded-lg flex items-center justify-between`}>
      <span className="text-[11px] text-gray-700">{label}</span>
      {badge ? (
        <span className="text-[10px] font-bold rounded-full px-2 py-0.5 bg-vitao-green text-white">{value}</span>
      ) : (
        <span className={`text-xs font-semibold ${textColor}`}>{value}</span>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Página principal
// ---------------------------------------------------------------------------

export default function InboxPage() {
  const { user, loading: authLoading } = useAuth();

  const [tickets, setTickets] = useState<InboxTicket[]>([]);
  const [loadingTickets, setLoadingTickets] = useState(true);
  const [refreshingTickets, setRefreshingTickets] = useState(false);

  const [selectedTicket, setSelectedTicket] = useState<InboxTicket | null>(null);
  const [mensagens, setMensagens] = useState<DeskrioMensagem[]>([]);
  const [loadingMensagens, setLoadingMensagens] = useState(false);
  const [refreshingMensagens, setRefreshingMensagens] = useState(false);

  const [cliente, setCliente] = useState<ClienteRegistro | null>(null);
  const [loadingCliente, setLoadingCliente] = useState(false);

  const [waStatus, setWaStatus] = useState<WhatsAppStatus | null>(null);

  const [busca, setBusca] = useState('');
  const [filterTab, setFilterTab] = useState<FilterTab>('todos');
  const [mobileView, setMobileView] = useState<MobileView>('list');

  const [inputTexto, setInputTexto] = useState('');
  const [sending, setSending] = useState(false);

  const selectedTicketRef = useRef<InboxTicket | null>(null);
  selectedTicketRef.current = selectedTicket;

  // -----------------------------------------------------------------------
  // Loaders
  // -----------------------------------------------------------------------

  const loadInbox = useCallback(async (silent = false) => {
    if (!silent) setLoadingTickets(true);
    else setRefreshingTickets(true);
    try {
      const data = await fetchInbox(6);
      const sorted = [...(data.tickets ?? [])].sort((a, b) => {
        const da = a.ultima_mensagem_data ?? a.ultima_msg_cliente_data ?? '';
        const db = b.ultima_mensagem_data ?? b.ultima_msg_cliente_data ?? '';
        return db.localeCompare(da);
      });
      setTickets(sorted);
    } catch {
      setTickets([]);
    } finally {
      if (!silent) setLoadingTickets(false);
      else setRefreshingTickets(false);
    }
  }, []);

  const loadMensagens = useCallback(async (ticketId: number, silent = false) => {
    if (!silent) setLoadingMensagens(true);
    else setRefreshingMensagens(true);
    try {
      const data = await fetchTicketMensagens(ticketId, 1);
      setMensagens(data.messages ?? []);
    } catch {
      if (!silent) setMensagens([]);
    } finally {
      if (!silent) setLoadingMensagens(false);
      else setRefreshingMensagens(false);
    }
  }, []);

  const loadCliente = useCallback(async (cnpj: string) => {
    setLoadingCliente(true);
    try {
      const c = await fetchCliente(cnpj);
      setCliente(c);
    } catch {
      setCliente(null);
    } finally {
      setLoadingCliente(false);
    }
  }, []);

  // -----------------------------------------------------------------------
  // Inicialização (após auth resolver)
  // -----------------------------------------------------------------------

  useEffect(() => {
    if (authLoading || !user) return;
    fetchWhatsAppStatus()
      .then(setWaStatus)
      .catch(() => setWaStatus(null));
    void loadInbox(false);
  }, [authLoading, user, loadInbox]);

  function handleSelectTicket(t: InboxTicket) {
    setSelectedTicket(t);
    setMobileView('chat');
    setMensagens([]);
    setInputTexto('');
    setCliente(null);
    void loadMensagens(t.ticket_id, false);
    if (t.cnpj) void loadCliente(t.cnpj);
  }

  // Polling 30s (visibility-aware)
  useEffect(() => {
    if (authLoading || !user) return;
    const interval = setInterval(() => {
      if (document.hidden) return;
      void loadInbox(true);
      const t = selectedTicketRef.current;
      if (t) void loadMensagens(t.ticket_id, true);
    }, POLL_INTERVAL_MS);
    return () => clearInterval(interval);
  }, [authLoading, user, loadInbox, loadMensagens]);

  async function handleEnviar() {
    const texto = inputTexto.trim();
    if (!texto || !selectedTicket?.cnpj || sending) return;

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
      const res = await enviarWhatsApp(selectedTicket.cnpj, texto);
      if (!res.enviado) {
        setMensagens((prev) => prev.filter((m) => m.id !== tempMsg.id));
        setInputTexto(texto);
      } else {
        await loadMensagens(selectedTicket.ticket_id, true);
      }
    } catch {
      setMensagens((prev) => prev.filter((m) => m.id !== tempMsg.id));
      setInputTexto(texto);
    } finally {
      setSending(false);
    }
  }

  if (authLoading || !user) {
    return (
      <div className="flex items-center justify-center" style={{ height: 'calc(100vh - 49px)' }}>
        <div className="w-8 h-8 border-2 border-gray-300 border-t-vitao-green rounded-full animate-spin" />
      </div>
    );
  }

  return (
    /*
     * Quebra do padding do AppShell (max-w-screen-2xl p-3 lg:p-6) para
     * preencher toda a área. Altura: 100vh menos header AppShell (~49px).
     */
    <div className="-m-3 lg:-m-6 flex" style={{ height: 'calc(100vh - 49px)' }}>
      {/* Coluna 1 — Lista */}
      <aside
        className={`${mobileView === 'list' ? 'flex' : 'hidden'} lg:flex flex-col w-full lg:w-80 flex-shrink-0 border-r border-gray-200 bg-white`}
      >
        <ColunaLista
          tickets={tickets}
          loading={loadingTickets}
          selectedId={selectedTicket?.ticket_id ?? null}
          busca={busca}
          setBusca={setBusca}
          filterTab={filterTab}
          setFilterTab={setFilterTab}
          waStatus={waStatus}
          onSelect={handleSelectTicket}
          onRefresh={() => void loadInbox(true)}
          refreshing={refreshingTickets}
        />
      </aside>

      {/* Coluna 2 — Chat */}
      <section className={`${mobileView === 'chat' ? 'flex' : 'hidden'} lg:flex flex-1 min-w-0 flex-col bg-gray-50`}>
        <ColunaChat
          ticket={selectedTicket}
          mensagens={mensagens}
          loading={loadingMensagens}
          refreshing={refreshingMensagens}
          inputTexto={inputTexto}
          setInputTexto={setInputTexto}
          sending={sending}
          onEnviar={handleEnviar}
          onVoltarMobile={() => setMobileView('list')}
          onVerPainelMobile={() => setMobileView('painel')}
          onRefresh={() => {
            const t = selectedTicketRef.current;
            if (t) void loadMensagens(t.ticket_id, true);
          }}
          showMobileBack={mobileView === 'chat'}
        />
      </section>

      {/* Coluna 3 — Painel cliente */}
      <aside
        className={`${mobileView === 'painel' ? 'flex' : 'hidden'} lg:flex w-full lg:w-96 flex-shrink-0 border-l border-gray-200 bg-white flex-col`}
      >
        <ColunaPainel
          ticket={selectedTicket}
          cliente={cliente}
          loadingCliente={loadingCliente}
          onVoltarMobile={() => setMobileView('chat')}
        />
      </aside>
    </div>
  );
}
