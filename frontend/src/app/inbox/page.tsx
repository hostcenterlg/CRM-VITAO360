'use client';

import { useCallback, useEffect, useRef, useState } from 'react';
import { getToken } from '@/lib/auth';

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface Cliente {
  cnpj: string;
  nome_fantasia: string;
  razao_social?: string;
  consultor?: string;
  situacao?: string;
  temperatura?: string;
  sinaleiro?: string;
  curva_abc?: string;
  score?: number;
  faturamento_total?: number;
  ticket_medio?: number;
  ciclo_medio?: number;
  ultima_compra?: string;
  dias_sem_compra?: number;
  telefone?: string;
  cidade?: string;
  uf?: string;
  prioridade?: string;
}

interface Atendimento {
  id: number;
  cnpj: string;
  tipo: string;
  descricao: string;
  data_atendimento: string;
  consultor?: string;
  resultado?: string;
  valor?: number;
}

interface Mensagem {
  id: string;
  texto: string;
  enviado: boolean; // true = sent by us (green right), false = received (white left)
  timestamp: string;
  tipo: 'texto' | 'atendimento';
  media_url?: string;
}

interface ClienteScore {
  cnpj: string;
  score?: number;
  temperatura?: string;
  prioridade?: string;
  sinaleiro?: string;
  curva_abc?: string;
  ticket_medio?: number;
  ciclo_medio?: number;
  ultima_compra?: string;
  dias_sem_compra?: number;
  faturamento_total?: number;
  sugestao_ia?: string;
  produtos_foco?: string[];
  tarefas_pendentes?: string[];
}

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? '';
const POLL_INTERVAL_MS = 30_000;

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function getInitials(nome: string): string {
  return nome
    .split(' ')
    .slice(0, 2)
    .map((w) => w.charAt(0).toUpperCase())
    .join('');
}

function formatTime(dateStr: string): string {
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

function formatBRL(v: number): string {
  return new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(v);
}

/** Returns a canonical seconds-ago label for the last-refreshed indicator. */
function formatSecondsAgo(lastRefreshed: Date | null): string {
  if (!lastRefreshed) return '';
  const seconds = Math.floor((Date.now() - lastRefreshed.getTime()) / 1000);
  if (seconds < 5) return 'Atualizado agora';
  if (seconds < 60) return `Atualizado há ${seconds}s`;
  const minutes = Math.floor(seconds / 60);
  return `Atualizado há ${minutes}min`;
}

// ---------------------------------------------------------------------------
// Media helpers
// ---------------------------------------------------------------------------

type MediaType = 'image' | 'audio' | 'video' | 'document';

function getMediaType(url: string): MediaType | null {
  if (!url) return null;
  // Try to extract extension from path before query string
  const cleanUrl = url.split('?')[0] ?? '';
  const ext = (cleanUrl.split('.').pop() ?? '').toLowerCase();
  if (['jpg', 'jpeg', 'png', 'gif', 'webp'].includes(ext)) return 'image';
  if (['mp3', 'ogg', 'wav', 'opus', 'm4a'].includes(ext)) return 'audio';
  if (['mp4', 'webm'].includes(ext)) return 'video';
  if (['pdf', 'doc', 'docx', 'xls', 'xlsx'].includes(ext)) return 'document';
  // Fallback: inspect path segments for content-type hints (Deskrio URLs may lack extensions)
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
    // Unknown type — show as a generic download link
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

        {/* Lightbox overlay */}
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

interface TempBadgeProps {
  temperatura?: string;
  size?: 'sm' | 'xs';
}

function TempBadge({ temperatura, size = 'sm' }: TempBadgeProps) {
  if (!temperatura) return null;
  const map: Record<string, { label: string; cls: string; icon: string }> = {
    QUENTE:  { label: 'Quente',  cls: 'bg-green-100 text-green-800 border border-green-200',   icon: 'F' },
    MORNO:   { label: 'Morno',   cls: 'bg-yellow-100 text-yellow-800 border border-yellow-200', icon: 'A' },
    FRIO:    { label: 'Frio',    cls: 'bg-gray-100 text-gray-600 border border-gray-200',       icon: 'F' },
    CRITICO: { label: 'Critico', cls: 'bg-red-100 text-red-800 border border-red-200',         icon: '!' },
    PERDIDO: { label: 'Perdido', cls: 'bg-red-50 text-red-600 border border-red-200',          icon: 'X' },
  };
  const entry = map[temperatura.toUpperCase()] ?? { label: temperatura, cls: 'bg-gray-100 text-gray-600 border border-gray-200', icon: '?' };
  const textSize = size === 'xs' ? 'text-[9px]' : 'text-[10px]';
  const tempIcons: Record<string, string> = {
    QUENTE: '🔥', MORNO: '⚠️', FRIO: '❄️', CRITICO: '🚨', PERDIDO: '✖',
  };
  const icon = tempIcons[temperatura.toUpperCase()] ?? '';
  return (
    <span className={`inline-flex items-center gap-0.5 px-1.5 py-0.5 rounded font-semibold ${textSize} ${entry.cls}`}>
      <span>{icon}</span>
      <span>{entry.label}</span>
    </span>
  );
}

// ---------------------------------------------------------------------------
// Fetch helpers
// ---------------------------------------------------------------------------

async function apiFetch<T>(path: string, options?: RequestInit): Promise<T> {
  const token = getToken();
  const res = await fetch(`${BASE_URL}${path}`, {
    cache: 'no-store',
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...(options?.headers as Record<string, string> | undefined),
    },
  });
  if (res.status === 401) {
    if (typeof window !== 'undefined') window.location.href = '/login';
    throw new Error('Sessao expirada');
  }
  if (!res.ok) {
    const body = await res.json().catch(() => ({})) as Record<string, unknown>;
    throw new Error((body.detail as string) || `API error ${res.status}`);
  }
  return res.json() as Promise<T>;
}

// ---------------------------------------------------------------------------
// Left panel — Conversation list
// ---------------------------------------------------------------------------

interface ConversationListProps {
  clientes: Cliente[];
  loading: boolean;
  error: string | null;
  selectedCnpj: string | null;
  busca: string;
  onBuscaChange: (v: string) => void;
  onSelect: (c: Cliente) => void;
  atendimentoMap: Record<string, Atendimento | undefined>;
  lastRefreshed: Date | null;
  onRefresh: () => void;
  refreshing: boolean;
}

function ConversationList({
  clientes,
  loading,
  error,
  selectedCnpj,
  busca,
  onBuscaChange,
  onSelect,
  atendimentoMap,
  lastRefreshed,
  onRefresh,
  refreshing,
}: ConversationListProps) {
  return (
    <div className="w-80 flex-shrink-0 border-r border-gray-200 bg-white flex flex-col h-full">
      {/* Header */}
      <div className="px-4 py-3 border-b border-gray-100 flex-shrink-0">
        <div className="flex items-center justify-between mb-2">
          <h2 className="text-sm font-bold text-gray-900">WhatsApp Inbox</h2>
          <div className="flex items-center gap-2">
            <div className="flex items-center gap-1.5">
              <div className="w-2 h-2 rounded-full bg-green-500 animate-pulse" />
              <span className="text-[10px] text-green-700 font-medium">Online</span>
            </div>
            {/* Manual refresh button */}
            <button
              type="button"
              onClick={onRefresh}
              disabled={refreshing}
              aria-label="Atualizar conversas"
              title="Atualizar conversas"
              className="p-1 rounded-md text-gray-400 hover:text-gray-600 hover:bg-gray-100
                         transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
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

        {/* Last-refreshed indicator */}
        {lastRefreshed && (
          <p className="text-[9px] text-gray-400 mb-2 leading-none">
            {formatSecondsAgo(lastRefreshed)}
          </p>
        )}

        {/* Search */}
        <div className="relative">
          <svg
            className="absolute left-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-gray-400 pointer-events-none"
            fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
              d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
          </svg>
          <input
            type="text"
            value={busca}
            onChange={(e) => onBuscaChange(e.target.value)}
            placeholder="Buscar cliente..."
            aria-label="Buscar cliente"
            className="w-full pl-8 pr-3 py-2 text-xs border border-gray-200 rounded-lg bg-gray-50
                       focus:outline-none focus:ring-2 focus:ring-green-200 focus:border-green-400
                       placeholder:text-gray-400"
          />
        </div>
      </div>

      {/* List */}
      <div className="flex-1 overflow-y-auto scrollbar-thin">
        {loading && (
          <div className="flex flex-col gap-2 p-3">
            {[...Array(8)].map((_, i) => (
              <div key={i} className="flex items-center gap-3 p-2">
                <div className="w-10 h-10 rounded-full bg-gray-100 animate-pulse flex-shrink-0" />
                <div className="flex-1 space-y-1.5">
                  <div className="h-3 bg-gray-100 animate-pulse rounded w-3/4" />
                  <div className="h-2.5 bg-gray-100 animate-pulse rounded w-1/2" />
                </div>
              </div>
            ))}
          </div>
        )}

        {!loading && error && (
          <div className="p-5 text-center">
            <svg className="w-8 h-8 text-amber-300 mx-auto mb-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
                d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
            <p className="text-xs font-medium text-gray-600 mb-1">
              WhatsApp temporariamente indisponivel
            </p>
            <p className="text-[11px] text-gray-400">
              Mostrando atendimentos do CRM
            </p>
          </div>
        )}

        {!loading && !error && clientes.length === 0 && (
          <div className="flex flex-col items-center justify-center h-48 text-center px-6">
            <svg className="w-10 h-10 text-gray-300 mb-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
                d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
            </svg>
            <p className="text-xs font-medium text-gray-500">Nenhum cliente encontrado</p>
            <p className="text-[11px] text-gray-400 mt-1">Tente outro termo de busca</p>
          </div>
        )}

        {!loading && !error && clientes.map((c) => {
          const lastAtt = atendimentoMap[c.cnpj];
          const isSelected = selectedCnpj === c.cnpj;
          return (
            <button
              key={c.cnpj}
              type="button"
              onClick={() => onSelect(c)}
              aria-pressed={isSelected}
              className={`w-full flex items-start gap-3 px-3 py-3 text-left border-b border-gray-50
                          transition-colors hover:bg-gray-50 focus:outline-none focus:ring-2
                          focus:ring-inset focus:ring-green-300
                          ${isSelected ? 'bg-green-50 border-l-2 border-l-green-500' : ''}`}
            >
              {/* Avatar */}
              <div
                className="w-10 h-10 rounded-full flex items-center justify-center flex-shrink-0
                           text-white text-xs font-bold"
                style={{ backgroundColor: '#00B050' }}
              >
                {getInitials(c.nome_fantasia)}
              </div>

              {/* Info */}
              <div className="flex-1 min-w-0">
                <div className="flex items-center justify-between gap-1 mb-0.5">
                  <p className="text-xs font-semibold text-gray-900 truncate">{c.nome_fantasia}</p>
                  {lastAtt && (
                    <span className="text-[10px] text-gray-400 flex-shrink-0">
                      {formatTime(lastAtt.data_atendimento)}
                    </span>
                  )}
                </div>

                <p className="text-[11px] text-gray-500 truncate mb-1">
                  {lastAtt
                    ? lastAtt.descricao.slice(0, 48) + (lastAtt.descricao.length > 48 ? '...' : '')
                    : `${c.uf ?? ''} · ${c.consultor ?? ''}`}
                </p>

                <div className="flex items-center justify-between gap-1">
                  <TempBadge temperatura={c.temperatura} size="xs" />
                  {c.curva_abc && (
                    <span className={`text-[9px] font-bold px-1 py-0.5 rounded
                      ${c.curva_abc === 'A' ? 'bg-green-100 text-green-700'
                        : c.curva_abc === 'B' ? 'bg-yellow-100 text-yellow-700'
                        : 'bg-orange-100 text-orange-700'}`}>
                      {c.curva_abc}
                    </span>
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
// Center panel — Chat area
// ---------------------------------------------------------------------------

interface ChatPanelProps {
  cliente: Cliente | null;
  mensagens: Mensagem[];
  loadingMensagens: boolean;
  inputTexto: string;
  onInputChange: (v: string) => void;
  onSend: () => void;
  sending: boolean;
  onBack: () => void;
  showBack: boolean;
  lastRefreshed: Date | null;
  onRefresh: () => void;
  refreshingMensagens: boolean;
}

function ChatPanel({
  cliente,
  mensagens,
  loadingMensagens,
  inputTexto,
  onInputChange,
  onSend,
  sending,
  onBack,
  showBack,
  lastRefreshed,
  onRefresh,
  refreshingMensagens,
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
    { label: 'Catalogo', icon: 'C', msg: 'Segue o catalogo de produtos VITAO: [link]' },
    { label: 'Tabela de Precos', icon: 'R$', msg: 'Segue a tabela de precos atualizada: [link]' },
    { label: 'Prazo de Entrega', icon: 'D', msg: 'O prazo de entrega para sua regiao e de 3 a 5 dias uteis.' },
  ];

  if (!cliente) {
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
        <h3 className="text-sm font-semibold text-gray-700">Selecione um cliente</h3>
        <p className="text-xs text-gray-400 mt-1 text-center px-8">
          Escolha uma conversa na lista ao lado para comecar
        </p>
      </div>
    );
  }

  return (
    <div className="flex-1 flex flex-col bg-gray-50 min-w-0">
      {/* Chat header */}
      <div className="flex items-center gap-3 px-4 py-3 bg-white border-b border-gray-200 flex-shrink-0">
        {showBack && (
          <button
            type="button"
            onClick={onBack}
            aria-label="Voltar a lista"
            className="mr-1 p-1.5 rounded-lg text-gray-500 hover:bg-gray-100 transition-colors"
          >
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
            </svg>
          </button>
        )}

        <div
          className="w-9 h-9 rounded-full flex items-center justify-center flex-shrink-0 text-white text-xs font-bold"
          style={{ backgroundColor: '#00B050' }}
        >
          {getInitials(cliente.nome_fantasia)}
        </div>

        <div className="flex-1 min-w-0">
          <p className="text-sm font-semibold text-gray-900 truncate">{cliente.nome_fantasia}</p>
          <div className="flex items-center gap-2">
            <span className="text-[10px] text-gray-400">
              {cliente.cidade && cliente.uf ? `${cliente.cidade}, ${cliente.uf}` : cliente.uf ?? ''}
            </span>
            {cliente.temperatura && (
              <TempBadge temperatura={cliente.temperatura} size="xs" />
            )}
          </div>
        </div>

        {/* Action buttons */}
        <div className="flex items-center gap-2 flex-shrink-0">
          {/* Manual refresh for messages */}
          <button
            type="button"
            onClick={onRefresh}
            disabled={refreshingMensagens || loadingMensagens}
            aria-label="Atualizar mensagens"
            title={lastRefreshed ? formatSecondsAgo(lastRefreshed) : 'Atualizar mensagens'}
            className="p-1.5 rounded-lg text-gray-400 hover:text-gray-600 hover:bg-gray-100
                       transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
          >
            <svg
              className={`w-4 h-4 ${refreshingMensagens ? 'animate-spin' : ''}`}
              fill="none" viewBox="0 0 24 24" stroke="currentColor"
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
          </button>

          <button
            type="button"
            title="Ligar para o cliente"
            className="flex items-center gap-1.5 px-2.5 py-1.5 text-xs font-medium text-gray-600
                       border border-gray-200 rounded-lg hover:bg-gray-50 hover:border-gray-300
                       transition-colors"
          >
            <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                d="M3 5a2 2 0 012-2h3.28a1 1 0 01.948.684l1.498 4.493a1 1 0 01-.502 1.21l-2.257 1.13a11.042 11.042 0 005.516 5.516l1.13-2.257a1 1 0 011.21-.502l4.493 1.498a1 1 0 01.684.949V19a2 2 0 01-2 2h-1C9.716 21 3 14.284 3 6V5z" />
            </svg>
            <span className="hidden sm:inline">Ligar</span>
          </button>
          <a
            href={`/carteira?busca=${encodeURIComponent(cliente.cnpj)}`}
            title="Ver ficha completa do cliente"
            className="flex items-center gap-1.5 px-2.5 py-1.5 text-xs font-medium text-white
                       rounded-lg transition-colors"
            style={{ backgroundColor: '#00B050' }}
          >
            <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
            </svg>
            <span className="hidden sm:inline">Ver Pedidos</span>
          </a>
        </div>
      </div>

      {/* Last-refreshed indicator bar */}
      {lastRefreshed && (
        <div className="flex items-center justify-center px-4 py-1 bg-gray-50 border-b border-gray-100 flex-shrink-0">
          <span className="text-[10px] text-gray-400">{formatSecondsAgo(lastRefreshed)}</span>
        </div>
      )}

      {/* Messages area */}
      <div className="flex-1 overflow-y-auto scrollbar-thin px-4 py-4 space-y-3">
        {loadingMensagens && (
          <div className="flex justify-center py-8">
            <div className="w-5 h-5 border-2 border-gray-300 border-t-green-500 rounded-full animate-spin" />
          </div>
        )}

        {!loadingMensagens && mensagens.length === 0 && (
          <div className="flex flex-col items-center justify-center h-32 text-center">
            <svg className="w-8 h-8 text-amber-300 mb-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
                d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
            <p className="text-xs font-medium text-gray-600 mb-1">
              WhatsApp temporariamente indisponivel
            </p>
            <p className="text-[11px] text-gray-400">
              Mostrando atendimentos do CRM
            </p>
          </div>
        )}

        {!loadingMensagens && mensagens.map((m) => {
          const isAtendimento = m.tipo === 'atendimento';
          const mediaType = m.media_url ? getMediaType(m.media_url) : null;
          return (
            <div
              key={m.id}
              className={`flex ${m.enviado ? 'justify-end' : 'justify-start'}`}
            >
              {!m.enviado && (
                <div
                  className="w-6 h-6 rounded-full flex items-center justify-center flex-shrink-0
                             text-white text-[9px] font-bold mr-2 mt-auto mb-0.5"
                  style={{ backgroundColor: isAtendimento ? '#6366F1' : '#6B7280' }}
                  title={isAtendimento ? 'Atendimento CRM' : 'WhatsApp'}
                >
                  {isAtendimento ? 'A' : 'W'}
                </div>
              )}
              <div className="max-w-xs lg:max-w-sm xl:max-w-md">
                {isAtendimento && (
                  <span className="block text-[9px] font-semibold text-indigo-400 mb-0.5 uppercase tracking-wide ml-1">
                    Registro CRM
                  </span>
                )}
                <div
                  className={`px-3 py-2 text-xs leading-relaxed shadow-sm
                    ${m.enviado
                      ? 'text-white'
                      : isAtendimento
                        ? 'bg-indigo-50 text-gray-800 border border-indigo-200'
                        : 'bg-white text-gray-800 border border-gray-200'
                    }`}
                  style={{
                    borderRadius: m.enviado
                      ? '16px 16px 4px 16px'
                      : '16px 16px 16px 4px',
                    backgroundColor: m.enviado ? '#00B050' : undefined,
                  }}
                >
                  {/* Media content — rendered above text */}
                  {m.media_url && (
                    <div className={`mb-1.5 ${mediaType === 'audio' ? 'w-full' : ''}`}>
                      <MediaBubble url={m.media_url} enviado={m.enviado} />
                    </div>
                  )}
                  {/* Text content — only shown when present */}
                  {m.texto && (
                    <span>{m.texto}</span>
                  )}
                </div>
                <div className={`flex items-center gap-1.5 mt-0.5 ${m.enviado ? 'justify-end' : 'justify-start'}`}>
                  {!isAtendimento && !m.enviado && (
                    <span className="text-[8px] text-green-500 font-medium">WA</span>
                  )}
                  <span className="text-[9px] text-gray-400">
                    {formatTime(m.timestamp)}
                  </span>
                  {m.enviado && (
                    <svg className="w-3 h-3 text-green-200" fill="currentColor" viewBox="0 0 24 24">
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

      {/* Quick action pills */}
      <div className="flex items-center gap-2 px-4 pb-2 pt-1 bg-gray-50 flex-shrink-0">
        {quickPills.map((pill) => (
          <button
            key={pill.label}
            type="button"
            onClick={() => onInputChange(pill.msg)}
            className="flex items-center gap-1 px-2.5 py-1 text-[10px] font-medium text-gray-600
                       bg-white border border-gray-200 rounded-full hover:border-green-300
                       hover:text-green-700 transition-colors whitespace-nowrap"
          >
            <span className="text-[9px] font-bold">{pill.icon}</span>
            {pill.label}
          </button>
        ))}
      </div>

      {/* Input bar */}
      <div className="px-4 pb-4 bg-gray-50 flex-shrink-0">
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
    </div>
  );
}

// ---------------------------------------------------------------------------
// Right panel — Client Intelligence
// ---------------------------------------------------------------------------

interface IntelligencePanelProps {
  cliente: Cliente | null;
  score: ClienteScore | null;
  loadingScore: boolean;
}

function IntelligencePanel({ cliente, score, loadingScore }: IntelligencePanelProps) {
  if (!cliente) {
    return (
      <div className="w-96 flex-shrink-0 border-l border-gray-200 bg-white hidden xl:flex
                      flex-col items-center justify-center">
        <svg className="w-10 h-10 text-gray-200 mb-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
            d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
        </svg>
        <p className="text-xs text-gray-400">Selecione um cliente</p>
      </div>
    );
  }

  const produtosFoco = score?.produtos_foco ?? [
    'Graos e Cereais',
    'Linha Sem Gluten',
    'Proteinas Vegetais',
  ];

  const tarefas = score?.tarefas_pendentes ?? [];

  return (
    <div className="w-96 flex-shrink-0 border-l border-gray-200 bg-white hidden xl:flex flex-col h-full">
      <div className="flex-1 overflow-y-auto scrollbar-thin p-4 space-y-4">

        {/* IA Suggestion card */}
        <div
          className="rounded-xl p-4 text-white"
          style={{ background: 'linear-gradient(135deg, #7C3AED 0%, #5B21B6 100%)' }}
        >
          <div className="flex items-center gap-2 mb-2">
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
            </svg>
            <span className="text-xs font-bold uppercase tracking-wide">Sugestao IA</span>
          </div>

          {loadingScore ? (
            <div className="space-y-1.5">
              <div className="h-3 bg-white/20 animate-pulse rounded w-full" />
              <div className="h-3 bg-white/20 animate-pulse rounded w-4/5" />
              <div className="h-3 bg-white/20 animate-pulse rounded w-3/5" />
            </div>
          ) : (
            <p className="text-xs leading-relaxed text-purple-100">
              {score?.sugestao_ia ??
                `Cliente ${cliente.temperatura?.toLowerCase() ?? 'sem classificacao'}. ${
                  (score?.dias_sem_compra ?? 0) > 30
                    ? `Sem compra ha ${score?.dias_sem_compra} dias — momento ideal para reativar.`
                    : 'Perfil ativo. Oferta cruzada pode aumentar ticket medio.'
                }`}
            </p>
          )}
        </div>

        {/* Mercos Data card */}
        <div className="bg-white rounded-xl border border-gray-200 p-4">
          <div className="flex items-center gap-2 mb-3">
            <div className="w-6 h-6 rounded flex items-center justify-center" style={{ backgroundColor: '#00B05015' }}>
              <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" style={{ color: '#00B050' }}>
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                  d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
              </svg>
            </div>
            <span className="text-xs font-bold text-gray-800">Dados Mercos</span>
          </div>

          {loadingScore ? (
            <div className="space-y-2">
              {[...Array(4)].map((_, i) => (
                <div key={i} className="flex justify-between">
                  <div className="h-3 bg-gray-100 animate-pulse rounded w-1/3" />
                  <div className="h-3 bg-gray-100 animate-pulse rounded w-1/4" />
                </div>
              ))}
            </div>
          ) : (
            <div className="space-y-2.5">
              <DataRow
                label="Ticket Medio"
                value={score?.ticket_medio != null ? formatBRL(score.ticket_medio) : (cliente.ticket_medio != null ? formatBRL(cliente.ticket_medio) : '—')}
                highlight
              />
              <DataRow
                label="Ciclo de Compra"
                value={score?.ciclo_medio != null ? `${score.ciclo_medio} dias` : (cliente.ciclo_medio != null ? `${cliente.ciclo_medio} dias` : '—')}
              />
              <DataRow
                label="Ultima Compra"
                value={score?.ultima_compra ?? cliente.ultima_compra ?? '—'}
              />
              <DataRow
                label="Curva ABC"
                value={cliente.curva_abc ?? '—'}
              />
              <DataRow
                label="Faturamento"
                value={score?.faturamento_total != null
                  ? formatBRL(score.faturamento_total)
                  : (cliente.faturamento_total != null ? formatBRL(cliente.faturamento_total) : '—')}
              />
              <DataRow
                label="Score"
                value={score?.score != null ? `${score.score.toFixed(1)} pts` : (cliente.score != null ? `${cliente.score.toFixed(1)} pts` : '—')}
              />
            </div>
          )}
        </div>

        {/* Products focus */}
        <div className="bg-white rounded-xl border border-gray-200 p-4">
          <div className="flex items-center gap-2 mb-3">
            <div className="w-6 h-6 rounded flex items-center justify-center bg-orange-50">
              <svg className="w-3.5 h-3.5 text-orange-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                  d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" />
              </svg>
            </div>
            <span className="text-xs font-bold text-gray-800">Foco de Produtos</span>
          </div>
          <div className="flex flex-wrap gap-1.5">
            {produtosFoco.map((p) => (
              <span
                key={p}
                className="inline-flex items-center px-2.5 py-1 text-[11px] font-medium
                           bg-orange-50 text-orange-700 border border-orange-200 rounded-full"
              >
                {p}
              </span>
            ))}
          </div>
        </div>

        {/* Pending tasks */}
        {tarefas.length > 0 && (
          <div className="bg-white rounded-xl border border-gray-200 p-4">
            <div className="flex items-center gap-2 mb-3">
              <div className="w-6 h-6 rounded flex items-center justify-center bg-blue-50">
                <svg className="w-3.5 h-3.5 text-blue-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                    d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4" />
                </svg>
              </div>
              <span className="text-xs font-bold text-gray-800">Tarefas Pendentes</span>
              <span className="text-[10px] bg-blue-100 text-blue-700 px-1.5 py-0.5 rounded font-semibold">
                {tarefas.length}
              </span>
            </div>
            <ul className="space-y-2">
              {tarefas.map((t, i) => (
                <li key={i} className="flex items-start gap-2">
                  <div className="w-4 h-4 rounded border-2 border-gray-300 flex-shrink-0 mt-0.5" />
                  <span className="text-[11px] text-gray-600 leading-relaxed">{t}</span>
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </div>
  );
}

interface DataRowProps {
  label: string;
  value: string;
  highlight?: boolean;
}

function DataRow({ label, value, highlight = false }: DataRowProps) {
  return (
    <div className="flex items-center justify-between gap-2">
      <span className="text-[11px] text-gray-500">{label}</span>
      <span className={`text-[11px] font-semibold ${highlight ? 'text-green-700' : 'text-gray-800'}`}>
        {value}
      </span>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Main page component
// ---------------------------------------------------------------------------

export default function InboxPage() {
  // Clients list state
  const [clientes, setClientes] = useState<Cliente[]>([]);
  const [loadingClientes, setLoadingClientes] = useState(true);
  const [errorClientes, setErrorClientes] = useState<string | null>(null);
  const [busca, setBusca] = useState('');
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  // Selected client
  const [selectedCliente, setSelectedCliente] = useState<Cliente | null>(null);

  // Atendimentos
  const [mensagens, setMensagens] = useState<Mensagem[]>([]);
  const [loadingMensagens, setLoadingMensagens] = useState(false);
  const [refreshingMensagens, setRefreshingMensagens] = useState(false);

  // Latest atendimento per client (for preview in list)
  const [atendimentoMap, setAtendimentoMap] = useState<Record<string, Atendimento | undefined>>({});

  // Client score / intelligence
  const [score, setScore] = useState<ClienteScore | null>(null);
  const [loadingScore, setLoadingScore] = useState(false);

  // Message input
  const [inputTexto, setInputTexto] = useState('');
  const [sending, setSending] = useState(false);

  // Mobile view: 'list' or 'chat'
  const [mobileView, setMobileView] = useState<'list' | 'chat'>('list');

  // Auto-polling state
  const [lastRefreshed, setLastRefreshed] = useState<Date | null>(null);
  const [refreshingList, setRefreshingList] = useState(false);
  // Ticker that forces the "Atualizado há X segundos" label to re-render every 10s
  const [, setTickCount] = useState(0);

  // Stable ref to avoid stale-closure issues in the polling interval
  const selectedClienteRef = useRef<Cliente | null>(null);
  selectedClienteRef.current = selectedCliente;

  // ---------------------------------------------------------------------------
  // Load clients
  // ---------------------------------------------------------------------------

  const loadClientes = useCallback(async (searchTerm: string) => {
    setLoadingClientes(true);
    setErrorClientes(null);
    try {
      const params = new URLSearchParams({ limit: '50' });
      if (searchTerm.trim()) params.set('busca', searchTerm.trim());
      const data = await apiFetch<{ registros: Cliente[]; total: number }>(
        `/api/clientes?${params.toString()}`
      );
      setClientes(data.registros ?? []);
    } catch (e: unknown) {
      setErrorClientes(e instanceof Error ? e.message : 'Erro ao carregar clientes');
    } finally {
      setLoadingClientes(false);
    }
  }, []);

  useEffect(() => {
    loadClientes('');
  }, [loadClientes]);

  // Debounced search
  function handleBuscaChange(v: string) {
    setBusca(v);
    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => {
      loadClientes(v);
    }, 350);
  }

  // ---------------------------------------------------------------------------
  // Load latest atendimento for list preview (top 20 shown)
  // ---------------------------------------------------------------------------

  useEffect(() => {
    if (clientes.length === 0) return;
    const topClientes = clientes.slice(0, 20);

    async function loadPreviews() {
      const results: Record<string, Atendimento | undefined> = {};
      await Promise.allSettled(
        topClientes.map(async (c) => {
          try {
            const data = await apiFetch<{ atendimentos: Atendimento[] }>(
              `/api/atendimentos?cnpj=${c.cnpj}&limit=1`
            );
            if (data.atendimentos?.length > 0) {
              results[c.cnpj] = data.atendimentos[0];
            }
          } catch {
            // silently skip individual failures
          }
        })
      );
      setAtendimentoMap((prev) => ({ ...prev, ...results }));
    }

    loadPreviews();
  }, [clientes]);

  // ---------------------------------------------------------------------------
  // Core message loader — used both on select and on poll refresh
  // ---------------------------------------------------------------------------

  const loadMensagens = useCallback(async (c: Cliente, silent = false) => {
    if (!silent) setLoadingMensagens(true);
    else setRefreshingMensagens(true);

    try {
      const [conversaResult, atendResult] = await Promise.allSettled([
        apiFetch<{
          configurado: boolean;
          contato: { id: number; nome: string; numero: string } | null;
          ticket: { id: number; status: string; criado_em: string; atualizado_em: string; ultima_mensagem: string } | null;
          mensagens: Array<{ id: string | number; texto: string; de_cliente: boolean; timestamp: string; tipo: string; media_url?: string; nome_contato?: string }>;
          total: number;
        }>(`/api/whatsapp/conversa/${c.cnpj}`),
        apiFetch<{ atendimentos: Atendimento[] }>(`/api/atendimentos?cnpj=${c.cnpj}&limit=20`),
      ]);

      const msgs: Mensagem[] = [];

      // 1. Real WhatsApp messages from Deskrio (priority)
      if (conversaResult.status === 'fulfilled' && conversaResult.value.mensagens.length > 0) {
        for (const m of conversaResult.value.mensagens) {
          msgs.push({
            id: String(m.id ?? `wa-${msgs.length}`),
            texto: m.texto || (m.tipo !== 'chat' ? `[${m.tipo}]` : ''),
            enviado: !m.de_cliente,
            timestamp: m.timestamp,
            tipo: 'texto',
            media_url: m.media_url ?? undefined,
          });
        }
      }

      // 2. CRM atendimentos as fallback / supplement
      if (atendResult.status === 'fulfilled') {
        const atts = atendResult.value.atendimentos ?? [];

        const waTimestamps = new Set(msgs.map((m) => m.timestamp.slice(0, 10)));
        const attsToShow = msgs.length > 0
          ? atts.filter((a) => !waTimestamps.has(a.data_atendimento?.slice(0, 10)))
          : atts;

        for (const a of attsToShow.slice().reverse()) {
          msgs.push({
            id: `crm-${a.id}`,
            texto: a.descricao,
            enviado: false,
            timestamp: a.data_atendimento,
            tipo: 'atendimento',
          });
        }

        if (atts.length > 0) {
          setAtendimentoMap((prev) => ({ ...prev, [c.cnpj]: atts[0] }));
        }
      }

      msgs.sort((a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime());

      setMensagens(msgs);
      setLastRefreshed(new Date());
    } catch {
      // show empty state with fallback messaging — do not throw
    } finally {
      if (!silent) setLoadingMensagens(false);
      else setRefreshingMensagens(false);
    }
  }, []);

  // ---------------------------------------------------------------------------
  // Select client
  // ---------------------------------------------------------------------------

  async function handleSelectCliente(c: Cliente) {
    setSelectedCliente(c);
    setMobileView('chat');
    setMensagens([]);
    setScore(null);
    setInputTexto('');
    setLastRefreshed(null);

    await loadMensagens(c, false);

    // Load score / intelligence
    setLoadingScore(true);
    try {
      const scoreData = await apiFetch<ClienteScore>(`/api/clientes/${c.cnpj}/score`);
      setScore(scoreData);
    } catch {
      // score panel will show defaults
    } finally {
      setLoadingScore(false);
    }
  }

  // ---------------------------------------------------------------------------
  // Manual refresh handlers
  // ---------------------------------------------------------------------------

  async function handleRefreshList() {
    setRefreshingList(true);
    try {
      await loadClientes(busca);
    } finally {
      setRefreshingList(false);
    }
  }

  async function handleRefreshMensagens() {
    const c = selectedClienteRef.current;
    if (!c) return;
    await loadMensagens(c, true);
  }

  // ---------------------------------------------------------------------------
  // Auto-polling — 30s interval, only when tab is visible
  // ---------------------------------------------------------------------------

  useEffect(() => {
    const interval = setInterval(() => {
      if (document.hidden) return;
      const c = selectedClienteRef.current;
      if (c) {
        // Silently refresh messages for the selected conversation
        loadMensagens(c, true);
      }
    }, POLL_INTERVAL_MS);

    return () => clearInterval(interval);
  }, [loadMensagens]);

  // Ticker: re-render the "Atualizado há Xs" label every 10 seconds
  useEffect(() => {
    const ticker = setInterval(() => {
      setTickCount((n) => n + 1);
    }, 10_000);
    return () => clearInterval(ticker);
  }, []);

  // ---------------------------------------------------------------------------
  // Send message
  // ---------------------------------------------------------------------------

  async function handleSend() {
    const texto = inputTexto.trim();
    if (!texto || !selectedCliente || sending) return;

    // Optimistic update
    const tempId = `tmp-${Date.now()}`;
    const now = new Date().toISOString();
    const novaMensagem: Mensagem = {
      id: tempId,
      texto,
      enviado: true,
      timestamp: now,
      tipo: 'texto',
    };
    setMensagens((prev) => [...prev, novaMensagem]);
    setInputTexto('');
    setSending(true);

    try {
      // Send via Deskrio WhatsApp (backend resolves CNPJ -> phone number)
      await apiFetch<{ enviado: boolean; erro?: string }>('/api/whatsapp/enviar', {
        method: 'POST',
        body: JSON.stringify({ cnpj: selectedCliente.cnpj, mensagem: texto }),
      });
    } catch {
      // Revert optimistic on hard error
      setMensagens((prev) => prev.filter((m) => m.id !== tempId));
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
     * The AppShell wraps this page with max-w-screen-2xl p-3 lg:p-6.
     * We use -m-3 lg:-m-6 to break out of that padding and fill the
     * available content area edge-to-edge, giving the true 3-panel feel.
     * Height is calculated as viewport minus the AppShell header (~49px).
     */
    <div
      className="-m-3 lg:-m-6 flex"
      style={{ height: 'calc(100vh - 49px)' }}
    >
      {/* LEFT panel — conversations list */}
      <div className={`${mobileView === 'chat' ? 'hidden md:flex' : 'flex'} md:flex flex-col flex-shrink-0`}
        style={{ width: '320px' }}>
        <ConversationList
          clientes={clientes}
          loading={loadingClientes}
          error={errorClientes}
          selectedCnpj={selectedCliente?.cnpj ?? null}
          busca={busca}
          onBuscaChange={handleBuscaChange}
          onSelect={handleSelectCliente}
          atendimentoMap={atendimentoMap}
          lastRefreshed={lastRefreshed}
          onRefresh={handleRefreshList}
          refreshing={refreshingList}
        />
      </div>

      {/* CENTER panel — chat */}
      <div
        className={`${mobileView === 'list' ? 'hidden md:flex' : 'flex'} md:flex flex-1 min-w-0`}
      >
        <ChatPanel
          cliente={selectedCliente}
          mensagens={mensagens}
          loadingMensagens={loadingMensagens}
          inputTexto={inputTexto}
          onInputChange={setInputTexto}
          onSend={handleSend}
          sending={sending}
          onBack={() => setMobileView('list')}
          showBack={mobileView === 'chat'}
          lastRefreshed={lastRefreshed}
          onRefresh={handleRefreshMensagens}
          refreshingMensagens={refreshingMensagens}
        />
      </div>

      {/* RIGHT panel — intelligence (xl and above only) */}
      <IntelligencePanel
        cliente={selectedCliente}
        score={score}
        loadingScore={loadingScore}
      />
    </div>
  );
}
