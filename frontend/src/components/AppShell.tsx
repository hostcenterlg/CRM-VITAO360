'use client';

import { useState, useEffect, useRef, useCallback } from 'react';
import { useRouter, usePathname } from 'next/navigation';
import Sidebar, { HamburgerButton } from './Sidebar';
import { useAuth } from '@/contexts/AuthContext';
import { fetchNotificacoes, Alerta } from '@/lib/api';
import SearchModal from './SearchModal';
import Onboarding from './Onboarding';
import { useKeyboardShortcuts } from '@/hooks/useKeyboardShortcuts';

// ---------------------------------------------------------------------------
// AppShell — sidebar + header com info do usuario + main content
// Client component pois gerencia estado de sidebar e auth
// ---------------------------------------------------------------------------

// ---------------------------------------------------------------------------
// Cores e icones por tipo de alerta
// ---------------------------------------------------------------------------

const ALERTA_CONFIG: Record<Alerta['tipo'], { cor: string; rotulo: string }> = {
  CHURN:             { cor: '#EF4444', rotulo: 'Churn' },
  FOLLOWUP_VENCIDO:  { cor: '#F59E0B', rotulo: 'Follow-up' },
  SINALEIRO_VERMELHO:{ cor: '#DC2626', rotulo: 'Sinaleiro' },
  META_RISCO:        { cor: '#EAB308', rotulo: 'Meta' },
};

// ---------------------------------------------------------------------------
// SinoBell — dropdown de notificacoes
// ---------------------------------------------------------------------------

function SinoBell() {
  const router = useRouter();
  const [aberto, setAberto] = useState(false);
  const [alertas, setAlertas] = useState<Alerta[]>([]);
  const [total, setTotal] = useState(0);
  const [carregando, setCarregando] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  // Fechar ao clicar fora
  useEffect(() => {
    function handleClickFora(e: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
        setAberto(false);
      }
    }
    if (aberto) {
      document.addEventListener('mousedown', handleClickFora);
    }
    return () => document.removeEventListener('mousedown', handleClickFora);
  }, [aberto]);

  // Buscar notificacoes + auto-refresh a cada 5 minutos
  useEffect(() => {
    let mounted = true;

    async function buscar() {
      try {
        const data = await fetchNotificacoes();
        if (mounted) {
          setTotal(data.total);
          setAlertas(data.alertas.slice(0, 10));
        }
      } catch {
        // silencioso — sino fica sem badge em caso de erro
      }
    }

    buscar();
    const intervalo = setInterval(buscar, 5 * 60 * 1000);
    return () => {
      mounted = false;
      clearInterval(intervalo);
    };
  }, []);

  function handleVer(alerta: Alerta) {
    setAberto(false);
    if (alerta.tipo === 'CHURN') {
      router.push(`/ia?cnpj=${alerta.cnpj}`);
    } else {
      router.push(`/carteira?cnpj=${alerta.cnpj}`);
    }
  }

  async function handleAbrirDropdown() {
    const novoEstado = !aberto;
    setAberto(novoEstado);
    if (novoEstado && alertas.length === 0) {
      setCarregando(true);
      try {
        const data = await fetchNotificacoes();
        setTotal(data.total);
        setAlertas(data.alertas.slice(0, 10));
      } catch {
        // silencioso
      } finally {
        setCarregando(false);
      }
    }
  }

  return (
    <div ref={dropdownRef} className="relative">
      {/* Botao sino */}
      <button
        type="button"
        onClick={handleAbrirDropdown}
        aria-label="Notificacoes"
        className="relative flex items-center justify-center w-8 h-8 rounded-lg
                   text-gray-500 hover:text-gray-800 hover:bg-gray-100
                   transition-colors focus:outline-none focus:ring-2 focus:ring-green-500"
      >
        {/* Icone sino */}
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.8}
            d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
        </svg>
        {/* Badge contador */}
        {total > 0 && (
          <span
            className="absolute -top-0.5 -right-0.5 flex items-center justify-center
                       min-w-[16px] h-4 px-1 rounded-full text-[10px] font-bold text-white leading-none"
            style={{ backgroundColor: '#EF4444' }}
          >
            {total > 99 ? '99+' : total}
          </span>
        )}
      </button>

      {/* Dropdown */}
      {aberto && (
        <div
          className="absolute right-0 top-full mt-2 w-80 bg-white border border-gray-200
                     rounded-xl shadow-lg z-50 overflow-hidden"
        >
          {/* Cabecalho dropdown */}
          <div className="flex items-center justify-between px-4 py-2.5 border-b border-gray-100 bg-gray-50">
            <span className="text-sm font-semibold text-gray-800">Alertas</span>
            {total > 0 && (
              <span className="text-xs text-gray-500">{total} pendente{total !== 1 ? 's' : ''}</span>
            )}
          </div>

          {/* Lista */}
          <div className="overflow-y-auto max-h-80">
            {carregando ? (
              <div className="flex items-center justify-center py-8">
                <div className="w-5 h-5 border-2 border-green-500 border-t-transparent rounded-full animate-spin" />
              </div>
            ) : alertas.length === 0 ? (
              <div className="flex flex-col items-center justify-center py-8 gap-2 text-gray-400">
                <svg className="w-8 h-8 opacity-40" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
                    d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <span className="text-sm">Sem alertas no momento</span>
              </div>
            ) : (
              alertas.map((alerta, idx) => {
                const cfg = ALERTA_CONFIG[alerta.tipo];
                return (
                  <div
                    key={`${alerta.cnpj}-${idx}`}
                    className="flex items-start gap-3 px-4 py-3 border-b border-gray-50
                               hover:bg-gray-50 transition-colors"
                  >
                    {/* Ponto colorido por tipo */}
                    <span
                      className="flex-shrink-0 w-2 h-2 rounded-full mt-1.5"
                      style={{ backgroundColor: cfg.cor }}
                    />
                    {/* Conteudo */}
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-0.5">
                        <span
                          className="text-[10px] font-semibold px-1.5 py-0.5 rounded uppercase"
                          style={{ backgroundColor: `${cfg.cor}18`, color: cfg.cor }}
                        >
                          {cfg.rotulo}
                        </span>
                        <span className="text-xs text-gray-500 truncate">{alerta.nome}</span>
                      </div>
                      <p className="text-xs text-gray-700 line-clamp-2 leading-relaxed">
                        {alerta.mensagem}
                      </p>
                    </div>
                    {/* Botao Ver */}
                    <button
                      type="button"
                      onClick={() => handleVer(alerta)}
                      className="flex-shrink-0 text-xs font-medium text-green-600
                                 hover:text-green-800 hover:underline transition-colors"
                    >
                      Ver
                    </button>
                  </div>
                );
              })
            )}
          </div>
        </div>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Map pathname -> page title for automatic header label
const PAGE_TITLES: Record<string, string> = {
  '/':              'Dashboard CEO',
  '/inbox':         'WhatsApp Inbox',
  '/agenda':        'Agenda Comercial',
  '/carteira':      'Carteira de Clientes',
  '/pipeline':      'Pipeline Kanban',
  '/sinaleiro':     'Sinaleiro de Carteira',
  '/projecao':      'Projecao Comercial',
  '/redes':         'Redes e Franquias',
  '/rnc':           'RNC',
  '/pedidos':       'Pedidos',
  '/produtos':      'Catalogo de Produtos',
  '/relatorios':    'Central de Relatorios',
  '/admin/motor':    'Motor de IA',
  '/admin/usuarios': 'Usuarios',
  '/admin/pipeline': 'Pipeline de Dados',
  '/atualizacoes':   'Atualizacoes & Pendencias',
  '/docs':           'Manual do CRM VITAO360',
};

// Map pathname -> breadcrumb segments [{ label, href? }]
const BREADCRUMBS: Record<string, Array<{ label: string; href?: string }>> = {
  '/':              [{ label: 'Dashboard' }],
  '/inbox':         [{ label: 'Dashboard', href: '/' }, { label: 'Inbox' }],
  '/agenda':        [{ label: 'Dashboard', href: '/' }, { label: 'Agenda' }],
  '/carteira':      [{ label: 'Dashboard', href: '/' }, { label: 'Carteira' }],
  '/pipeline':      [{ label: 'Dashboard', href: '/' }, { label: 'Pipeline' }],
  '/sinaleiro':     [{ label: 'Dashboard', href: '/' }, { label: 'Sinaleiro' }],
  '/projecao':      [{ label: 'Dashboard', href: '/' }, { label: 'Projecao' }],
  '/redes':         [{ label: 'Dashboard', href: '/' }, { label: 'Redes' }],
  '/rnc':           [{ label: 'Dashboard', href: '/' }, { label: 'RNC' }],
  '/pedidos':       [{ label: 'Dashboard', href: '/' }, { label: 'Pedidos' }],
  '/produtos':      [{ label: 'Gestao', href: '/' }, { label: 'Produtos' }],
  '/relatorios':    [{ label: 'Gestao', href: '/' }, { label: 'Relatorios' }],
  '/admin/motor':    [{ label: 'Admin', href: '/' }, { label: 'Motor' }],
  '/atualizacoes':   [{ label: 'Admin', href: '/' }, { label: 'Atualizacoes' }],
  '/admin/usuarios': [{ label: 'Admin', href: '/' }, { label: 'Usuarios' }],
  '/admin/pipeline': [{ label: 'Admin', href: '/' }, { label: 'Pipeline' }],
  '/docs':           [{ label: 'Dashboard', href: '/' }, { label: 'Manual' }],
};

interface AppShellProps {
  children: React.ReactNode;
  pageTitle?: string;
}

// Badge de role — 4 roles: admin (roxo), gerente (azul), consultor (verde), consultor_externo (cinza)
function RoleBadge({ role }: { role: string }) {
  const map: Record<string, { cls: string; label: string }> = {
    admin:             { cls: 'bg-purple-100 text-purple-700 border border-purple-200', label: 'Admin' },
    gerente:           { cls: 'bg-blue-100 text-blue-700 border border-blue-200',       label: 'Gerente' },
    consultor:         { cls: 'bg-green-100 text-green-700 border border-green-200',    label: 'Consultor' },
    consultor_externo: { cls: 'bg-gray-100 text-gray-600 border border-gray-200',       label: 'Ext.' },
    // legado — manter compatibilidade
    viewer:            { cls: 'bg-gray-100 text-gray-600 border border-gray-200',       label: 'Visualizacao' },
  };
  const entry = map[role] ?? map['viewer'];
  return (
    <span className={`text-[10px] font-semibold px-1.5 py-0.5 rounded ${entry.cls}`}>
      {entry.label}
    </span>
  );
}

const SIDEBAR_COLLAPSED_KEY = 'crm_sidebar_collapsed';

export default function AppShell({ children, pageTitle }: AppShellProps) {
  // Mobile drawer state (hidden by default)
  const [sidebarOpen, setSidebarOpen] = useState(false);

  // Desktop collapsed state — persisted in localStorage
  const [sidebarCollapsed, setSidebarCollapsed] = useState<boolean>(() => {
    if (typeof window === 'undefined') return false;
    try {
      return localStorage.getItem(SIDEBAR_COLLAPSED_KEY) === 'true';
    } catch {
      return false;
    }
  });

  // Busca global
  const [searchOpen, setSearchOpen] = useState(false);
  const handleOpenSearch = useCallback(() => setSearchOpen(true), []);
  const handleCloseSearch = useCallback(() => setSearchOpen(false), []);

  const { user, logout } = useAuth();
  const router = useRouter();
  const pathname = usePathname();

  // Auto-detect page title if not explicitly passed
  const resolvedTitle = pageTitle ?? PAGE_TITLES[pathname] ?? undefined;
  const breadcrumbs = BREADCRUMBS[pathname] ?? null;

  // Atalhos de teclado globais
  useKeyboardShortcuts({ onOpenSearch: handleOpenSearch });

  function handleLogout() {
    logout();
    router.replace('/login');
  }

  function handleToggleCollapse() {
    setSidebarCollapsed((prev) => {
      const next = !prev;
      try {
        localStorage.setItem(SIDEBAR_COLLAPSED_KEY, String(next));
      } catch {
        // fallback silencioso
      }
      return next;
    });
  }

  // Fechar sidebar mobile quando rota muda
  useEffect(() => {
    setSidebarOpen(false);
  }, [pathname]);

  return (
    <div className="flex h-screen overflow-hidden bg-gray-50">
      {/* Sidebar */}
      <Sidebar
        mobileOpen={sidebarOpen}
        onClose={() => setSidebarOpen(false)}
        collapsed={sidebarCollapsed}
        onToggleCollapse={handleToggleCollapse}
      />

      {/* Overlay escuro para mobile quando sidebar aberta */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 bg-black/40 z-20 md:hidden"
          onClick={() => setSidebarOpen(false)}
          aria-hidden="true"
        />
      )}

      {/* Coluna principal */}
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        {/* Header compacto em mobile, completo em desktop */}
        <header className="flex-shrink-0 bg-white border-b border-gray-200 px-3 md:px-4 py-2.5 flex items-center gap-2 md:gap-3 shadow-sm">
          {/* Hamburger mobile */}
          <HamburgerButton onClick={() => setSidebarOpen(true)} />

          {/* Titulo da pagina */}
          <div className="flex items-center gap-1 min-w-0">
            {/* Desktop: breadcrumbs quando disponivel */}
            {breadcrumbs && breadcrumbs.length > 1 ? (
              <div className="hidden sm:flex items-center gap-1">
                {breadcrumbs.map((crumb, idx) => (
                  <span key={idx} className="flex items-center gap-1">
                    {idx > 0 && (
                      <svg className="w-3.5 h-3.5 text-gray-300 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                      </svg>
                    )}
                    {crumb.href && idx < breadcrumbs.length - 1 ? (
                      <button
                        type="button"
                        onClick={() => router.push(crumb.href!)}
                        className="text-xs text-gray-400 hover:text-gray-700 transition-colors whitespace-nowrap"
                      >
                        {crumb.label}
                      </button>
                    ) : (
                      <span className={idx === breadcrumbs.length - 1
                        ? 'text-sm font-semibold text-gray-900 whitespace-nowrap'
                        : 'text-xs text-gray-400 whitespace-nowrap'
                      }>
                        {crumb.label}
                      </span>
                    )}
                  </span>
                ))}
              </div>
            ) : null}

            {/* Mobile: apenas titulo da pagina, sem breadcrumbs */}
            {resolvedTitle && (
              <h1 className={`text-sm font-semibold text-gray-900 truncate ${breadcrumbs && breadcrumbs.length > 1 ? 'sm:hidden' : ''}`}>
                {resolvedTitle}
              </h1>
            )}
          </div>

          {/* Spacer */}
          <div className="flex-1" />

          {/* Busca global — desktop: hint Ctrl+K; mobile: icone lupa */}
          <button
            type="button"
            onClick={handleOpenSearch}
            aria-label="Busca global (Ctrl+K)"
            className="flex items-center gap-2 px-2.5 py-1.5 rounded-lg border border-gray-200 text-gray-400
                       hover:text-gray-700 hover:border-gray-300 hover:bg-gray-50 transition-colors
                       focus:outline-none focus:ring-2 focus:ring-green-500"
          >
            <svg className="w-4 h-4 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
            <span className="hidden md:flex items-center gap-1.5 text-xs text-gray-400">
              Buscar
              <kbd className="px-1 py-0.5 rounded bg-gray-100 border border-gray-200 font-mono text-[9px] leading-none">
                Ctrl+K
              </kbd>
            </span>
          </button>

          {/* Sino de notificacoes */}
          <SinoBell />

          {/* Info do usuario autenticado */}
          {user && (
            <div className="flex items-center gap-2 md:gap-3">
              {/* Nome + role — oculto em mobile */}
              <div className="hidden sm:flex flex-col items-end gap-0.5">
                <div className="flex items-center gap-1.5">
                  <span className="w-2 h-2 rounded-full bg-green-500 animate-pulse-dot flex-shrink-0" />
                  <span className="text-sm font-medium text-gray-800 leading-tight">
                    {user.consultor_nome ?? user.nome}
                  </span>
                </div>
                <RoleBadge role={user.role} />
              </div>

              {/* Avatar inicial */}
              <div
                className="w-7 h-7 rounded-full flex items-center justify-center flex-shrink-0 text-white text-xs font-bold"
                style={{ backgroundColor: '#00B050' }}
                title={user.nome}
              >
                {user.nome.charAt(0).toUpperCase()}
              </div>

              {/* Botao Sair */}
              <button
                type="button"
                onClick={handleLogout}
                title="Sair"
                className="flex items-center gap-1.5 px-2 md:px-2.5 py-1.5 text-xs font-medium text-gray-600
                           border border-gray-200 rounded-lg hover:bg-gray-50 hover:text-gray-900
                           transition-colors focus:outline-none focus:ring-2 focus:ring-green-500"
              >
                <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                    d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
                </svg>
                <span className="hidden sm:inline">Sair</span>
              </button>
            </div>
          )}
        </header>

        {/* Conteudo da pagina — scrollavel */}
        <main className="flex-1 overflow-y-auto scrollbar-thin">
          <div className="max-w-screen-2xl mx-auto p-3 md:p-4 lg:p-6">
            {children}
          </div>
        </main>
      </div>

      {/* Busca global modal */}
      <SearchModal open={searchOpen} onClose={handleCloseSearch} />

      {/* Tour de boas-vindas (primeiro login) */}
      <Onboarding />
    </div>
  );
}
