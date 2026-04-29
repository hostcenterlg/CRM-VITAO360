'use client';

/**
 * CRM VITAO360 — Inbox Page — Demo-quality rebuild (Missao B10)
 *
 * Modo DEMO: quando API retorna 0 conversas (Deskrio offline / sem dados reais),
 * exibe mock data ilustrativo para apresentacao da diretoria.
 * Banner amarelo diferencia claramente o modo demo do modo producao.
 *
 * Modo PRODUCAO: quando API retorna >= 1 ticket, mock data e descartado
 * e o sistema opera normalmente com dados reais do Deskrio.
 *
 * Layout 3 colunas:
 *   [Lista Conversas w-80] | [Chat WhatsApp flex-1] | [Painel Cliente w-96]
 *
 * Mobile: 1 coluna por vez via state mobileView (list | chat | painel).
 *
 * Pendencias Fase 2a real:
 *   - Remover MOCK_CONVERSAS / MOCK_MENSAGENS / MOCK_DADOS_MERCOS
 *   - Migrar para SSR com cookies (padrao de Carteira/Agenda)
 *   - Endpoint GET /api/inbox/conversas com cruzamento Deskrio + banco
 *   - Endpoint GET /api/inbox/mensagens/{ticketId}
 *   - POST /api/inbox/enviar com logica real Deskrio
 *
 * Regras: R5 (CNPJ string), R8 (zero fabricacao real), R9 (tema light + cores Vitao).
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
  formatDateBR,
  type InboxTicket,
  type DeskrioMensagem,
  type WhatsAppStatus,
  type ClienteRegistro,
} from '@/lib/api';

import {
  MOCK_CONVERSAS,
  MOCK_MENSAGENS,
  MOCK_DADOS_MERCOS,
  MOCK_WA_STATUS,
  getTemperaturaBadge,
  getTemperaturaAvatarBg,
  type DadosMercosMock,
} from './_mockData';

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

function truncatePreview(text: string, max = 52): string {
  const clean = text.replace(/\*([^*]+)\*/g, '$1').replace(/_([^_]+)_/g, '$1').trim();
  return clean.length <= max ? clean : `${clean.slice(0, max)}...`;
}

function formatBRLLocal(val: number | null | undefined): string {
  if (val == null || !Number.isFinite(val)) return '—';
  return new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL', maximumFractionDigits: 0 }).format(val);
}

// ---------------------------------------------------------------------------
// Banner demo
// ---------------------------------------------------------------------------

function BannerDemo({ onDismiss }: { onDismiss: () => void }) {
  return (
    <div className="flex items-center justify-between gap-2 bg-vitao-lightgreen border-b border-vitao-green/30 text-vitao-darkgreen text-xs px-4 py-2 flex-shrink-0">
      <div className="flex items-center gap-2">
        <svg className="w-4 h-4 flex-shrink-0 text-vitao-green" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 10l4.553-2.069A1 1 0 0121 8.87V15.13a1 1 0 01-1.447.9L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
        </svg>
        <span>
          <strong>Preview do novo Inbox</strong> — dados ilustrativos para apresentacao.
          Integracao com Deskrio em desenvolvimento (Fase 2 do roadmap).
        </span>
      </div>
      <button
        type="button"
        onClick={onDismiss}
        aria-label="Fechar banner"
        className="flex-shrink-0 text-vitao-darkgreen/60 hover:text-vitao-darkgreen transition-colors"
      >
        <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
        </svg>
      </button>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Avatar
// ---------------------------------------------------------------------------

interface AvatarProps {
  nome: string;
  size?: 'sm' | 'md' | 'lg';
  bgClass?: string;
}

function Avatar({ nome, size = 'md', bgClass = 'bg-vitao-green' }: AvatarProps) {
  const dim =
    size === 'sm'
      ? 'w-8 h-8 text-xs'
      : size === 'lg'
        ? 'w-12 h-12 text-sm'
        : 'w-10 h-10 text-xs';
  return (
    <div
      className={`${dim} rounded-full flex items-center justify-center flex-shrink-0 text-white font-bold ${bgClass}`}
    >
      {getInitials(nome)}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Status dot e badge
// ---------------------------------------------------------------------------

function StatusDot({ ticket }: { ticket: InboxTicket }) {
  if (ticket.status === 'closed' || ticket.status === 'resolved') {
    return <span className="w-2 h-2 rounded-full bg-gray-400 inline-block ring-2 ring-white" />;
  }
  if (ticket.aguardando_resposta) {
    return <span className="w-2 h-2 rounded-full bg-vitao-orange animate-pulse inline-block ring-2 ring-white" />;
  }
  return <span className="w-2 h-2 rounded-full bg-vitao-green inline-block ring-2 ring-white" />;
}

function StatusBadge({ ticket }: { ticket: InboxTicket }) {
  if (ticket.status === 'closed' || ticket.status === 'resolved') {
    return (
      <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-gray-100 border border-gray-200">
        <span className="w-1.5 h-1.5 rounded-full bg-gray-400" />
        <span className="text-xs font-medium text-gray-600">Finalizado</span>
      </span>
    );
  }
  if (ticket.aguardando_resposta) {
    return (
      <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-orange-50 border border-orange-200">
        <span className="w-1.5 h-1.5 rounded-full bg-vitao-orange animate-pulse" />
        <span className="text-xs font-medium text-orange-700">Aguardando</span>
      </span>
    );
  }
  return (
    <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-vitao-lightgreen border border-green-200">
      <span className="w-1.5 h-1.5 rounded-full bg-vitao-green" />
      <span className="text-xs font-medium text-vitao-darkgreen">Em atendimento</span>
    </span>
  );
}

// ---------------------------------------------------------------------------
// Skeleton
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
  isDemo: boolean;
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
  isDemo,
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

  return (
    <>
      {/* Header */}
      <div className="px-4 pt-3 pb-2 border-b border-gray-100 flex-shrink-0">
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center gap-2">
            <svg className="w-4 h-4" viewBox="0 0 24 24" fill="#00A859" aria-hidden="true">
              <path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413z" />
            </svg>
            <h2 className="text-sm font-bold text-gray-900">Conversas Ativas</h2>
            <span className="text-xs font-bold px-1.5 py-0.5 rounded-full bg-vitao-green text-white">
              {tickets.filter(t => t.status === 'open').length}
            </span>
          </div>
          <div className="flex items-center gap-2">
            {waOnline && (
              <Badge variant="success" size="xs" dot>
                WhatsApp conectado
              </Badge>
            )}
            {!waOnline && isDemo && (
              <Badge variant="success" size="xs" dot>
                WhatsApp conectado
              </Badge>
            )}
            <button
              type="button"
              onClick={onRefresh}
              disabled={refreshing}
              aria-label="Atualizar"
              className="p-1 rounded-md text-gray-500 hover:text-gray-600 hover:bg-gray-100 transition-colors disabled:opacity-40"
            >
              <svg
                className={`w-3.5 h-3.5 ${refreshing ? 'animate-spin' : ''}`}
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
            </button>
          </div>
        </div>

        {/* Busca */}
        <div className="relative mb-2">
          <svg className="absolute left-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-gray-500 pointer-events-none" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
          </svg>
          <input
            type="search"
            value={busca}
            onChange={(e) => setBusca(e.target.value)}
            placeholder="Buscar cliente, conversa..."
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
              className={`flex-1 flex items-center justify-center gap-1 py-1 rounded-md text-xs font-semibold transition-colors focus:outline-none ${
                filterTab === tab.key ? 'bg-vitao-green text-white shadow-sm' : 'text-gray-600 hover:text-gray-800'
              }`}
            >
              {tab.label}
              {tab.key === 'aguardando' && countAguardando > 0 && (
                <span className={`text-xs font-bold px-1 py-0.5 rounded-full leading-none min-w-[14px] text-center ${
                  filterTab === tab.key ? 'bg-white text-vitao-darkgreen' : 'bg-vitao-orange text-white'
                }`}>
                  {countAguardando}
                </span>
              )}
            </button>
          ))}
        </div>
      </div>

      {/* Lista */}
      <div className="flex-1 overflow-y-auto" style={{ scrollbarWidth: 'thin' }}>
        {loading && (
          <div>{[...Array(8)].map((_, i) => <SkeletonRow key={i} />)}</div>
        )}

        {!loading && filtered.length === 0 && (
          <div className="flex flex-col items-center justify-center py-16 px-6 text-center">
            <svg className="w-12 h-12 text-gray-500 mb-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
            </svg>
            <p className="text-sm font-medium text-gray-500">Nenhuma conversa</p>
            <p className="text-xs text-gray-500 mt-1">
              {busca ? 'Tente outro termo de busca' : filterTab !== 'todos' ? 'Tente outro filtro' : 'Sem conversas no período'}
            </p>
          </div>
        )}

        {!loading && filtered.map((t) => (
          <ItemConversa
            key={t.ticket_id}
            ticket={t}
            selected={selectedId === t.ticket_id}
            onClick={() => onSelect(t)}
          />
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

  // Temperatura do mock (se ticket vier do mock, atendente_nome nao e null)
  const tempMap: Record<string, string> = { 'Larissa - Vitao': 'Quente', 'Manu - Vitao': 'Quente', 'Daiane - Vitao': 'Morno' };
  const tempGuess = ticket.atendente_nome ? (tempMap[ticket.atendente_nome] ?? 'Morno') : 'Morno';
  const tempBadge = getTemperaturaBadge(isAguardando ? 'quente' : tempGuess);
  const avatarBg = getTemperaturaAvatarBg(isAguardando ? 'quente' : tempGuess);

  return (
    <button
      type="button"
      onClick={onClick}
      aria-pressed={selected}
      className={`w-full flex items-start gap-3 px-3 py-3 text-left border-b border-gray-50 transition-colors hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-inset focus:ring-vitao-green/40 relative ${
        selected ? 'bg-vitao-lightgreen' : ''
      } ${
        isAguardando
          ? 'border-l-4 border-l-vitao-orange'
          : selected
            ? 'border-l-4 border-l-vitao-green'
            : 'border-l-4 border-l-transparent'
      }`}
    >
      <div className="relative flex-shrink-0 mt-0.5">
        <div className={`w-12 h-12 rounded-full flex items-center justify-center text-white font-bold text-sm ${avatarBg}`}>
          {getInitials(ticket.contato_nome)}
        </div>
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
              <span className="bg-vitao-blue text-white text-xs font-bold w-4 h-4 rounded-full flex items-center justify-center">
                {naoLidas > 9 ? '9+' : naoLidas}
              </span>
            )}
            <span className="text-xs text-gray-500">{formatTime(ticket.ultima_mensagem_data ?? ticket.ultima_msg_cliente_data)}</span>
          </div>
        </div>

        <p className={`text-xs truncate leading-tight mb-1 ${naoLidas > 0 ? 'text-gray-800 font-medium' : 'text-gray-500'}`}>
          {ticket.ultima_mensagem ? truncatePreview(ticket.ultima_mensagem) : ' '}
        </p>

        <div className="flex items-center gap-1.5">
          <span className={`text-xs font-semibold px-1.5 py-0.5 rounded-full ${tempBadge.classes}`}>
            {isAguardando ? 'Quente' : tempBadge.label}
          </span>
          {ticket.atendente_nome && (
            <span className="text-xs text-gray-500 truncate">
              {ticket.atendente_nome.replace(/-\s*Vitao/i, '').trim()}
            </span>
          )}
        </div>
      </div>
    </button>
  );
}

// ---------------------------------------------------------------------------
// Typing indicator
// ---------------------------------------------------------------------------

function TypingIndicator() {
  return (
    <div className="flex justify-start">
      <div className="bg-white rounded-2xl px-4 py-3 border border-gray-200 shadow-sm">
        <div className="flex space-x-1">
          <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
          <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
          <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
        </div>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Bolha de mensagem
// ---------------------------------------------------------------------------

function BolhaMensagem({ msg, contatoNome }: { msg: DeskrioMensagem; contatoNome: string }) {
  const enviado = !msg.de_cliente;

  return (
    <div className={`flex ${enviado ? 'justify-end' : 'justify-start'}`}>
      {!enviado && (
        <div className="w-6 h-6 rounded-full flex items-center justify-center flex-shrink-0 text-white text-xs font-bold mr-2 mt-auto mb-0.5 bg-gray-400">
          {getInitials(msg.nome_contato ?? contatoNome)}
        </div>
      )}
      <div className="max-w-xs lg:max-w-sm xl:max-w-md">
        {enviado && msg.nome_contato && (
          <p className="text-xs text-gray-500 text-right mb-0.5 mr-1 truncate max-w-[200px] ml-auto">
            {msg.nome_contato.replace(/-\s*Vitao/i, '').trim()}
          </p>
        )}
        <div
          className={`px-3 py-2 text-xs leading-relaxed shadow-sm ${
            enviado ? 'bg-vitao-green text-white' : 'bg-white text-gray-800 border border-gray-200'
          }`}
          style={{ borderRadius: enviado ? '16px 16px 4px 16px' : '16px 16px 16px 4px' }}
        >
          <span className="whitespace-pre-wrap break-words">{msg.texto}</span>
        </div>
        <div className={`flex items-center gap-1 mt-0.5 ${enviado ? 'justify-end' : 'justify-start'}`}>
          <span className="text-xs text-gray-500">{formatMsgTime(msg.timestamp)}</span>
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
// Coluna 2 — Chat WhatsApp-like
// ---------------------------------------------------------------------------

interface ColunaChatProps {
  ticket: InboxTicket | null;
  mensagens: DeskrioMensagem[];
  loading: boolean;
  inputTexto: string;
  setInputTexto: (v: string) => void;
  sending: boolean;
  onEnviar: () => void;
  onVoltarMobile: () => void;
  onVerPainelMobile: () => void;
  showMobileBack: boolean;
  isDemo: boolean;
  showTyping: boolean;
}

function ColunaChat({
  ticket,
  mensagens,
  loading,
  inputTexto,
  setInputTexto,
  sending,
  onEnviar,
  onVoltarMobile,
  onVerPainelMobile,
  showMobileBack,
  showTyping,
}: ColunaChatProps) {
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [mensagens, showTyping]);

  function handleKeyDown(e: React.KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      if (!sending && inputTexto.trim()) onEnviar();
    }
  }

  const quickPills = [
    { label: 'Catalogo', msg: 'Ola! Posso te enviar o catalogo de produtos atualizado?' },
    { label: 'Tabela', msg: 'Vou enviar nossa tabela de precos. Tem alguma linha de interesse?' },
    { label: 'Prazo Entrega', msg: 'Nosso prazo de entrega e de 5 a 7 dias uteis apos confirmacao do pagamento.' },
  ];

  if (!ticket) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center bg-gray-50 px-6">
        <div className="w-16 h-16 rounded-full flex items-center justify-center mb-4 bg-vitao-lightgreen">
          <svg className="w-8 h-8 text-vitao-green" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
          </svg>
        </div>
        <h3 className="text-sm font-semibold text-gray-700">Selecione uma conversa</h3>
        <p className="text-xs text-gray-500 mt-1 text-center">Escolha um cliente na lista ao lado para ver o historico</p>
      </div>
    );
  }

  const isClosed = ticket.status === 'closed' || ticket.status === 'resolved';

  return (
    <>
      {/* Header */}
      <div className="flex items-center gap-3 px-4 py-3 bg-white border-b border-gray-200 flex-shrink-0">
        {showMobileBack && (
          <button
            type="button"
            onClick={onVoltarMobile}
            aria-label="Voltar"
            className="p-1.5 rounded-lg text-gray-500 hover:bg-gray-100 transition-colors lg:hidden min-h-[44px] min-w-[44px] flex items-center justify-center"
          >
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
            </svg>
          </button>
        )}

        <Avatar nome={ticket.contato_nome} size="md" bgClass="bg-vitao-green" />

        <div className="flex-1 min-w-0">
          <p className="text-sm font-semibold text-gray-900 truncate leading-tight">{ticket.contato_nome || '(sem nome)'}</p>
          <div className="flex items-center gap-1.5">
            <span className="w-1.5 h-1.5 rounded-full bg-vitao-green animate-pulse inline-block" />
            <span className="text-xs text-vitao-darkgreen">Online agora</span>
          </div>
        </div>

        <div className="flex items-center gap-2 flex-shrink-0">
          <StatusBadge ticket={ticket} />
          <button
            type="button"
            aria-label="Ligar"
            className="hidden sm:flex items-center gap-1.5 px-3 py-1.5 bg-vitao-blue text-white text-xs font-medium rounded-lg hover:bg-vitao-blue/90 transition-colors min-h-[36px]"
            onClick={() => alert('Em breve: chamada integrada')}
          >
            <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 5a2 2 0 012-2h3.28a1 1 0 01.948.684l1.498 4.493a1 1 0 01-.502 1.21l-2.257 1.13a11.042 11.042 0 005.516 5.516l1.13-2.257a1 1 0 011.21-.502l4.493 1.498a1 1 0 01.684.949V19a2 2 0 01-2 2h-1C9.716 21 3 14.284 3 6V5z" />
            </svg>
            Ligar
          </button>
          <button
            type="button"
            aria-label="Ver pedidos"
            className="hidden sm:flex items-center gap-1.5 px-3 py-1.5 bg-vitao-green text-white text-xs font-medium rounded-lg hover:bg-vitao-darkgreen transition-colors min-h-[36px]"
            onClick={() => alert('Em breve: historico de pedidos')}
          >
            <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
            </svg>
            Ver Pedidos
          </button>
          <button
            type="button"
            onClick={onVerPainelMobile}
            aria-label="Ver painel cliente"
            className="lg:hidden p-1.5 rounded-lg text-gray-500 hover:bg-gray-100 transition-colors min-h-[44px] min-w-[44px] flex items-center justify-center"
          >
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </button>
        </div>
      </div>

      {/* Mensagens */}
      <div className="flex-1 overflow-y-auto px-4 py-4 space-y-3 bg-gray-50" style={{ scrollbarWidth: 'thin' }}>
        {loading && (
          <div className="flex justify-center py-8">
            <div className="w-5 h-5 border-2 border-gray-200 border-t-vitao-green rounded-full animate-spin" />
          </div>
        )}

        {!loading && mensagens.map((m) => (
          <BolhaMensagem key={m.id} msg={m} contatoNome={ticket.contato_nome} />
        ))}

        {!loading && showTyping && <TypingIndicator />}

        <div ref={messagesEndRef} />
      </div>

      {/* Closed notice */}
      {isClosed && (
        <div className="flex items-center justify-center gap-2 px-4 py-2 bg-gray-100 border-t border-gray-200 flex-shrink-0">
          <svg className="w-3.5 h-3.5 text-gray-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
          </svg>
          <span className="text-xs text-gray-500">Ticket finalizado</span>
        </div>
      )}

      {/* Quick pills */}
      {!isClosed && (
        <div className="flex items-center gap-2 px-4 pb-2 pt-2 bg-white border-t border-gray-100 flex-shrink-0 overflow-x-auto">
          {quickPills.map((pill) => (
            <button
              key={pill.label}
              type="button"
              onClick={() => setInputTexto(pill.msg)}
              className="flex items-center gap-1 px-3 py-1 text-xs font-medium text-gray-700 bg-gray-100 border border-gray-200 rounded-full hover:bg-vitao-lightgreen hover:border-vitao-green hover:text-vitao-darkgreen transition-colors whitespace-nowrap flex-shrink-0 min-h-[36px]"
            >
              {pill.label}
            </button>
          ))}
        </div>
      )}

      {/* Input */}
      {!isClosed && (
        <div
          className="px-4 bg-white border-t border-gray-100 flex-shrink-0"
          style={{ paddingTop: '0.5rem', paddingBottom: 'max(1rem, env(safe-area-inset-bottom))' }}
        >
          <div className="flex items-end gap-2 bg-gray-50 border border-gray-200 rounded-2xl shadow-sm px-3 py-2 focus-within:border-vitao-green focus-within:ring-2 focus-within:ring-vitao-green/20 transition-all">
            {/* Paperclip */}
            <button
              type="button"
              aria-label="Anexar arquivo"
              className="p-1.5 text-gray-500 hover:text-gray-600 transition-colors flex-shrink-0 min-h-[36px] flex items-center"
              onClick={() => alert('Em breve: envio de arquivos')}
            >
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.172 7l-6.586 6.586a2 2 0 102.828 2.828l6.414-6.586a4 4 0 00-5.656-5.656l-6.415 6.585a6 6 0 108.486 8.486L20.5 13" />
              </svg>
            </button>
            <textarea
              ref={inputRef}
              value={inputTexto}
              onChange={(e) => setInputTexto(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Digite sua mensagem..."
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
              className="flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center bg-gradient-to-r from-vitao-green to-vitao-darkgreen hover:opacity-90 transition-all disabled:opacity-40 disabled:cursor-not-allowed"
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
// Coluna 3 — Painel cliente
// ---------------------------------------------------------------------------

interface ColunaPainelProps {
  ticket: InboxTicket | null;
  cliente: ClienteRegistro | null;
  mockDados: DadosMercosMock | null;
  loadingCliente: boolean;
  onVoltarMobile: () => void;
  isDemo: boolean;
}

function DadoRow({ label, value, bg, textColor, badge }: { label: string; value: string; bg: string; textColor: string; badge?: boolean }) {
  return (
    <div className={`${bg} px-3 py-2 rounded-lg flex items-center justify-between`}>
      <span className="text-xs text-gray-700">{label}</span>
      {badge ? (
        <span className="text-xs font-bold rounded-full px-2 py-0.5 bg-vitao-green text-white">{value}</span>
      ) : (
        <span className={`text-xs font-semibold ${textColor}`}>{value}</span>
      )}
    </div>
  );
}

function ColunaPainel({ ticket, cliente, mockDados, loadingCliente, onVoltarMobile, isDemo }: ColunaPainelProps) {
  const dados = isDemo && mockDados ? mockDados : null;
  const nomeExibir = dados?.nome_fantasia ?? cliente?.nome_fantasia ?? ticket?.contato_nome ?? 'Cliente';

  const ticketMedio = dados?.ticket_medio ?? cliente?.ticket_medio;
  const cicloMedio = dados?.ciclo_medio_dias ?? (cliente as Record<string, unknown> | null)?.['ciclo_medio_dias'] as number | undefined;
  const ultimaCompra = dados?.ultima_compra ?? cliente?.ultima_compra;
  const curvaABC = dados?.curva_abc ?? cliente?.curva_abc;
  const consultor = dados?.consultor ?? cliente?.consultor;
  const cnpjRaw = dados?.cnpj ?? ticket?.cnpj;

  return (
    <>
      {/* Header mobile */}
      <div className="lg:hidden p-3 border-b border-gray-200 bg-white flex items-center gap-2 flex-shrink-0">
        <button
          type="button"
          onClick={onVoltarMobile}
          aria-label="Voltar para chat"
          className="p-1.5 rounded-lg text-gray-500 hover:bg-gray-100 transition-colors min-h-[44px] min-w-[44px] flex items-center justify-center"
        >
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
          </svg>
        </button>
        <span className="text-sm font-semibold text-gray-900">Detalhes do cliente</span>
      </div>

      {!ticket ? (
        <div className="p-4 flex-1 flex flex-col items-center justify-center text-center text-gray-500">
          <svg className="w-10 h-10 text-gray-200 mb-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
          </svg>
          <p className="text-xs">Selecione uma conversa para ver os dados do cliente</p>
        </div>
      ) : (
        <div className="p-4 space-y-4 overflow-y-auto flex-1" style={{ scrollbarWidth: 'thin' }}>
          {/* Header cliente */}
          <div className="flex items-center gap-3 pb-3 border-b border-gray-100">
            <Avatar nome={nomeExibir} size="lg" bgClass="bg-vitao-green" />
            <div className="flex-1 min-w-0">
              <h3 className="text-sm font-bold text-gray-900 truncate">{nomeExibir}</h3>
              <p className="text-xs text-gray-500 truncate">{cnpjRaw ? formatCNPJ(cnpjRaw) : '—'}</p>
              {consultor && <p className="text-xs text-vitao-darkgreen font-medium truncate">Consultor: {consultor}</p>}
            </div>
          </div>

          {/* IA placeholder */}
          <div className="bg-gray-100 rounded-xl p-5 text-gray-500 text-center text-sm">
            <svg className="w-8 h-8 text-gray-500 mx-auto mb-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M5 3v4M3 5h4M6 17v4m-2-2h4m5-16l2.286 6.857L21 12l-5.714 2.143L13 21l-2.286-6.857L5 12l5.714-2.143L13 3z" />
            </svg>
            <p className="font-semibold text-gray-600 text-[13px] mb-1">Inteligencia (Em breve)</p>
            <p className="text-xs text-gray-500">Sugestoes de IA para este cliente aparecerão aqui em breve.</p>
            <p className="text-xs text-gray-500 mt-1">Dados do cliente abaixo</p>
          </div>

          {/* Loading */}
          {loadingCliente && !isDemo && (
            <div className="flex justify-center py-6">
              <div className="w-5 h-5 border-2 border-gray-200 border-t-vitao-green rounded-full animate-spin" />
            </div>
          )}

          {/* Dados Mercos */}
          {(dados || cliente) && (
            <div>
              <h4 className="text-xs font-semibold text-gray-700 uppercase tracking-wider mb-2">Dados do Cliente (Mercos)</h4>
              <div className="space-y-2">
                <DadoRow
                  label="Ticket Medio"
                  value={ticketMedio != null ? formatBRLLocal(ticketMedio) : '—'}
                  bg="bg-blue-50"
                  textColor="text-vitao-blue"
                />
                <DadoRow
                  label="Ciclo de Compra"
                  value={cicloMedio != null ? `${cicloMedio} dias` : '—'}
                  bg="bg-purple-50"
                  textColor="text-vitao-purple"
                />
                <DadoRow
                  label="Ultima Compra"
                  value={ultimaCompra ? (isDemo ? `${dados?.dias_sem_compra ?? '?'} dias atras` : formatDateBR(ultimaCompra)) : '—'}
                  bg="bg-orange-50"
                  textColor="text-vitao-orange"
                />
                <DadoRow
                  label="Curva ABC"
                  value={curvaABC ?? '—'}
                  bg="bg-green-50"
                  textColor="text-vitao-darkgreen"
                  badge
                />
              </div>
            </div>
          )}

          {/* Produtos de foco (demo) */}
          {isDemo && dados?.produtos_foco && dados.produtos_foco.length > 0 && (
            <div>
              <h4 className="text-xs font-semibold text-gray-700 uppercase tracking-wider mb-2">Produtos de Foco</h4>
              <div className="space-y-2">
                {dados.produtos_foco.map((p, idx) => (
                  <div key={idx} className="bg-gray-50 border border-gray-200 rounded-lg p-3">
                    <div className="flex items-start justify-between gap-1 mb-1">
                      <p className="text-xs font-semibold text-gray-800 truncate flex-1">{p.nome}</p>
                      {p.recompra_proxima && (
                        <span className="flex-shrink-0 text-xs font-semibold bg-vitao-orange/10 text-vitao-orange px-1.5 py-0.5 rounded-full whitespace-nowrap">
                          Recompra proxima
                        </span>
                      )}
                    </div>
                    <p className="text-xs text-gray-500">{p.caixas_mes} cx/mes · Ultima: {p.ultima_compra_label}</p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Tarefas do cliente (demo) */}
          {isDemo && dados?.tarefas && dados.tarefas.length > 0 && (
            <div>
              <h4 className="text-xs font-semibold text-gray-700 uppercase tracking-wider mb-2">Tarefas</h4>
              <div className="space-y-2">
                {dados.tarefas.map((t) => (
                  <div key={t.id} className={`flex items-start gap-2 p-2 rounded-lg border ${t.atrasada ? 'bg-red-50 border-red-200' : 'bg-gray-50 border-gray-200'}`}>
                    <svg className={`w-4 h-4 flex-shrink-0 mt-0.5 ${t.atrasada ? 'text-vitao-red' : 'text-gray-500'}`} fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
                    </svg>
                    <div className="flex-1 min-w-0">
                      <p className={`text-xs font-medium truncate ${t.atrasada ? 'text-vitao-red' : 'text-gray-800'}`}>{t.titulo}</p>
                      <p className={`text-xs ${t.atrasada ? 'text-red-500 font-semibold' : 'text-gray-500'}`}>{t.prazo_label}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Atalhos (producao) */}
          {!isDemo && cliente && (
            <div>
              <h4 className="text-xs font-semibold text-gray-700 uppercase tracking-wider mb-2">Atalhos</h4>
              <div className="grid grid-cols-2 gap-2">
                <a href={`/carteira?busca=${encodeURIComponent(cliente.cnpj)}`} className="px-3 py-2 bg-vitao-lightgreen text-vitao-darkgreen text-xs font-medium rounded-lg text-center hover:bg-green-100 transition-colors">
                  Ver na Carteira
                </a>
                <a href={`/clientes/${cliente.cnpj}`} className="px-3 py-2 bg-blue-50 text-vitao-blue text-xs font-medium rounded-lg text-center hover:bg-blue-100 transition-colors">
                  Ficha 360
                </a>
              </div>
            </div>
          )}
        </div>
      )}
    </>
  );
}

// ---------------------------------------------------------------------------
// Pagina principal
// ---------------------------------------------------------------------------

export default function InboxPage() {
  const { user, loading: authLoading } = useAuth();

  // Modo demo: ativo quando API retorna 0 tickets
  const [isDemo, setIsDemo] = useState(false);
  const [demoBannerVisible, setDemoBannerVisible] = useState(true);

  const [tickets, setTickets] = useState<InboxTicket[]>([]);
  const [loadingTickets, setLoadingTickets] = useState(true);
  const [refreshingTickets, setRefreshingTickets] = useState(false);

  const [selectedTicket, setSelectedTicket] = useState<InboxTicket | null>(null);
  const [mensagens, setMensagens] = useState<DeskrioMensagem[]>([]);
  const [loadingMensagens, setLoadingMensagens] = useState(false);

  const [cliente, setCliente] = useState<ClienteRegistro | null>(null);
  const [mockDadosAtual, setMockDadosAtual] = useState<DadosMercosMock | null>(null);
  const [loadingCliente, setLoadingCliente] = useState(false);

  const [waStatus, setWaStatus] = useState<WhatsAppStatus | null>(null);

  const [busca, setBusca] = useState('');
  const [filterTab, setFilterTab] = useState<FilterTab>('todos');
  const [mobileView, setMobileView] = useState<MobileView>('list');

  const [inputTexto, setInputTexto] = useState('');
  const [sending, setSending] = useState(false);

  // Typing indicator: visivel por 2.5s apos selecionar conversa demo
  const [showTyping, setShowTyping] = useState(false);

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

      if (sorted.length === 0) {
        // Modo demo: usar mock data
        setIsDemo(true);
        setTickets(MOCK_CONVERSAS);
        // Selecionar primeira conversa automaticamente
        if (!silent && !selectedTicketRef.current) {
          const primeira = MOCK_CONVERSAS[0];
          if (primeira) {
            setSelectedTicket(primeira);
            setMensagens(MOCK_MENSAGENS[primeira.ticket_id] ?? []);
            setMockDadosAtual(MOCK_DADOS_MERCOS[primeira.ticket_id] ?? null);
          }
        }
      } else {
        setIsDemo(false);
        setTickets(sorted);
      }
    } catch {
      // Em caso de erro de rede, tambem ativa modo demo
      setIsDemo(true);
      setTickets(MOCK_CONVERSAS);
      if (!silent && !selectedTicketRef.current) {
        const primeira = MOCK_CONVERSAS[0];
        if (primeira) {
          setSelectedTicket(primeira);
          setMensagens(MOCK_MENSAGENS[primeira.ticket_id] ?? []);
          setMockDadosAtual(MOCK_DADOS_MERCOS[primeira.ticket_id] ?? null);
        }
      }
    } finally {
      if (!silent) setLoadingTickets(false);
      else setRefreshingTickets(false);
    }
  }, []);

  const loadMensagens = useCallback(async (ticketId: number, silent = false) => {
    if (!silent) setLoadingMensagens(true);
    try {
      const data = await fetchTicketMensagens(ticketId, 1);
      setMensagens(data.messages ?? []);
    } catch {
      if (!silent) setMensagens([]);
    } finally {
      if (!silent) setLoadingMensagens(false);
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
  // Inicializacao (apos auth resolver)
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
    setShowTyping(false);

    if (isDemo) {
      setMensagens(MOCK_MENSAGENS[t.ticket_id] ?? []);
      setMockDadosAtual(MOCK_DADOS_MERCOS[t.ticket_id] ?? null);
      // Typing indicator por 2.5s se conversa esta aguardando resposta
      if (t.aguardando_resposta) {
        setTimeout(() => setShowTyping(true), 500);
        setTimeout(() => setShowTyping(false), 3000);
      }
    } else {
      setMockDadosAtual(null);
      void loadMensagens(t.ticket_id, false);
      if (t.cnpj) void loadCliente(t.cnpj);
    }
  }

  // Polling 30s (apenas modo producao, visibility-aware)
  useEffect(() => {
    if (authLoading || !user || isDemo) return;
    const interval = setInterval(() => {
      if (document.hidden) return;
      void loadInbox(true);
      const t = selectedTicketRef.current;
      if (t) void loadMensagens(t.ticket_id, true);
    }, POLL_INTERVAL_MS);
    return () => clearInterval(interval);
  }, [authLoading, user, isDemo, loadInbox, loadMensagens]);

  function handleEnviar() {
    const texto = inputTexto.trim();
    if (!texto || sending) return;

    if (isDemo) {
      // Demo: simula envio
      const novaMsgId = Date.now();
      const novaMsg: DeskrioMensagem = {
        id: novaMsgId,
        texto,
        de_cliente: false,
        timestamp: new Date().toISOString(),
        tipo: 'chat',
        nome_contato: user?.email?.split('@')[0] ?? 'Voce',
      };
      setMensagens((prev) => [...prev, novaMsg]);
      setInputTexto('');
      // Typing indicator simulando resposta apos 2s
      setTimeout(() => setShowTyping(true), 2000);
      setTimeout(() => setShowTyping(false), 4500);
      return;
    }

    // Producao: requer ticket com CNPJ
    if (!selectedTicket?.cnpj) return;
    void (async () => {
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
        const res = await enviarWhatsApp(selectedTicket.cnpj!, texto);
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
    })();
  }

  const waStatusEfetivo = isDemo ? MOCK_WA_STATUS as WhatsAppStatus : waStatus;

  if (authLoading || !user) {
    return (
      <div className="flex items-center justify-center" style={{ height: 'calc(100vh - 49px)' }}>
        <div className="w-8 h-8 border-2 border-gray-300 border-t-vitao-green rounded-full animate-spin" />
      </div>
    );
  }

  return (
    <div className="-m-3 lg:-m-6 flex flex-col" style={{ height: 'calc(100vh - 49px)' }}>
      {/* Banner demo (dismissivel) */}
      {isDemo && demoBannerVisible && (
        <BannerDemo onDismiss={() => setDemoBannerVisible(false)} />
      )}

      <div className="flex flex-1 min-h-0">
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
            waStatus={waStatusEfetivo}
            onSelect={handleSelectTicket}
            onRefresh={() => void loadInbox(true)}
            refreshing={refreshingTickets}
            isDemo={isDemo}
          />
        </aside>

        {/* Coluna 2 — Chat */}
        <section className={`${mobileView === 'chat' ? 'flex' : 'hidden'} lg:flex flex-1 min-w-0 flex-col bg-gray-50`}>
          <ColunaChat
            ticket={selectedTicket}
            mensagens={mensagens}
            loading={loadingMensagens}
            inputTexto={inputTexto}
            setInputTexto={setInputTexto}
            sending={sending}
            onEnviar={handleEnviar}
            onVoltarMobile={() => setMobileView('list')}
            onVerPainelMobile={() => setMobileView('painel')}
            showMobileBack={mobileView === 'chat'}
            isDemo={isDemo}
            showTyping={showTyping}
          />
        </section>

        {/* Coluna 3 — Painel cliente */}
        <aside
          className={`${mobileView === 'painel' ? 'flex' : 'hidden'} lg:flex w-full lg:w-96 flex-shrink-0 border-l border-gray-200 bg-white flex-col`}
        >
          <ColunaPainel
            ticket={selectedTicket}
            cliente={cliente}
            mockDados={mockDadosAtual}
            loadingCliente={loadingCliente}
            onVoltarMobile={() => setMobileView('chat')}
            isDemo={isDemo}
          />
        </aside>
      </div>
    </div>
  );
}
