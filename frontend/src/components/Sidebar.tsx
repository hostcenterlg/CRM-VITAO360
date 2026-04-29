'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useEffect, useState } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { fetchJson } from '@/lib/api';
import { MetaWidget } from '@/components/ui';

// ---------------------------------------------------------------------------
// Sidebar — navegacao CRM VITAO360, light theme only
// Briefing 29-Abr-2026: 7 itens principais (Inbox, IA, Agenda, Pedidos,
//   Clientes, Produtos, --- divider ---, Manual)
// Suporta: colapso em desktop (so icones) + mobile drawer
// Pipeline e RNC continuam existindo como rotas, mas saem da navegacao.
// ---------------------------------------------------------------------------

interface NavItem {
  href: string;
  label: string;
  icon: React.ReactNode;
  showInboxBadge?: boolean;
  showAgendaBadge?: boolean;
  isDividerBefore?: boolean;
  previewBadge?: 'em_construcao' | 'bloqueado';
}

interface NavGroup {
  label: string;
  items: NavItem[];
  adminOnly?: boolean;
  gerenteOuAdmin?: boolean;
}

// ---------------------------------------------------------------------------
// InboxBadge — conta tickets nao lidos (status aguardando)
// ---------------------------------------------------------------------------

interface InboxCountResponse {
  tickets?: Array<{ status?: string }>;
  total?: number;
  nao_lidas?: number;
}

function InboxBadge({ active, collapsed }: { active: boolean; collapsed: boolean }) {
  const [count, setCount] = useState<number | null>(null);

  useEffect(() => {
    let cancelled = false;
    async function load() {
      try {
        const res = await fetchJson<InboxCountResponse>('/api/inbox?status=aguardando&limit=1');
        if (!cancelled) {
          const n = res.nao_lidas ?? res.total ?? 0;
          if (n > 0) setCount(n);
        }
      } catch {
        // Non-critical
      }
    }
    void load();
    return () => { cancelled = true; };
  }, []);

  if (!count || count === 0) return null;

  if (collapsed) {
    return (
      <span
        className="absolute -top-0.5 -right-0.5 flex items-center justify-center
                   min-w-[14px] h-3.5 px-0.5 rounded-full text-white text-[8px] font-bold leading-none"
        style={{ backgroundColor: '#ef4444' }}
        aria-label={`${count} mensagens nao lidas`}
      >
        {count > 9 ? '9+' : count}
      </span>
    );
  }

  return (
    <span
      className="inline-flex items-center justify-center min-w-[18px] h-[18px]
                 px-1 rounded-full text-white text-[9px] font-bold leading-none ml-auto"
      style={{ backgroundColor: active ? 'rgba(255,255,255,0.35)' : '#ef4444' }}
      aria-label={`${count} mensagens nao lidas`}
    >
      {count > 99 ? '99+' : count}
    </span>
  );
}

// ---------------------------------------------------------------------------
// AgendaBadge — conta compromissos de hoje + tarefas pendentes de hoje
// ---------------------------------------------------------------------------

interface AgendaConsultorResponse {
  itens?: Array<unknown>;
}

function AgendaBadge({ active, collapsed }: { active: boolean; collapsed: boolean }) {
  const [count, setCount] = useState<number | null>(null);

  useEffect(() => {
    let cancelled = false;
    async function load() {
      try {
        // Busca agenda do consultor LARISSA (mais representativo) como proxy
        const res = await fetchJson<AgendaConsultorResponse>('/api/agenda/LARISSA');
        if (!cancelled) {
          const n = res.itens?.length ?? 0;
          if (n > 0) setCount(n);
        }
      } catch {
        // Non-critical
      }
    }
    void load();
    return () => { cancelled = true; };
  }, []);

  if (!count || count === 0) return null;

  if (collapsed) {
    return (
      <span
        className="absolute -top-0.5 -right-0.5 flex items-center justify-center
                   min-w-[14px] h-3.5 px-0.5 rounded-full text-white text-[8px] font-bold leading-none"
        style={{ backgroundColor: '#FFC000', color: '#1a1a1a' }}
        aria-label={`${count} itens na agenda hoje`}
      >
        {count > 9 ? '9+' : count}
      </span>
    );
  }

  return (
    <span
      className="inline-flex items-center justify-center min-w-[18px] h-[18px]
                 px-1 rounded-full text-[9px] font-bold leading-none ml-auto"
      style={{
        backgroundColor: active ? 'rgba(255,255,255,0.35)' : '#FFC000',
        color: active ? '#fff' : '#1a1a1a',
      }}
      aria-label={`${count} itens na agenda hoje`}
    >
      {count > 99 ? '99+' : count}
    </span>
  );
}

const navGroups: NavGroup[] = [
  {
    label: 'CRM',
    items: [
      {
        href: '/inbox',
        label: 'Inbox',
        showInboxBadge: true,
        icon: (
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
              d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
          </svg>
        ),
      },
      {
        href: '/ia',
        label: 'Inteligencia IA',
        icon: (
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
              d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
          </svg>
        ),
      },
      {
        href: '/agenda',
        label: 'Agenda',
        showAgendaBadge: true,
        icon: (
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
              d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4" />
          </svg>
        ),
      },
      {
        href: '/pedidos',
        label: 'Pedidos',
        icon: (
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
              d="M3 3h2l.4 2M7 13h10l4-8H5.4M7 13L5.4 5M7 13l-2.293 2.293c-.63.63-.184 1.707.707 1.707H17m0 0a2 2 0 100 4 2 2 0 000-4zm-8 2a2 2 0 11-4 0 2 2 0 014 0z" />
          </svg>
        ),
      },
      {
        href: '/clientes',
        label: 'Clientes',
        icon: (
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
              d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0z" />
          </svg>
        ),
      },
      {
        href: '/produtos',
        label: 'Produtos',
        icon: (
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
              d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" />
          </svg>
        ),
      },
      {
        href: '/manual',
        label: 'Manual',
        isDividerBefore: true,
        icon: (
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
              d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
          </svg>
        ),
      },
    ],
  },
  {
    label: 'Gestao',
    items: [
      {
        href: '/',
        label: 'Dashboard',
        icon: (
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
              d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" />
          </svg>
        ),
      },
      // Projecao removida da sidebar — vira tab interna do Dashboard (Wave 3)
      {
        href: '/redes',
        label: 'Redes',
        icon: (
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
              d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
          </svg>
        ),
      },
      {
        href: '/sinaleiro',
        label: 'Sinaleiro',
        icon: (
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
              d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
          </svg>
        ),
      },
      {
        href: '/relatorios',
        label: 'Relatorios',
        icon: (
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
              d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
        ),
      },
      {
        href: '/gestao/dde',
        label: 'DDE',
        previewBadge: 'em_construcao',
        icon: (
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
              d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
          </svg>
        ),
      },
      {
        href: '/gestao/analise-critica',
        label: 'Analise Critica',
        previewBadge: 'bloqueado',
        icon: (
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
              d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
          </svg>
        ),
      },
    ],
    gerenteOuAdmin: true,
  },
  {
    label: 'Admin',
    adminOnly: true,
    items: [
      {
        href: '/admin/motor',
        label: 'Motor',
        icon: (
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
              d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
              d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
          </svg>
        ),
      },
      {
        href: '/admin/usuarios',
        label: 'Usuarios',
        icon: (
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
              d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z" />
          </svg>
        ),
      },
      {
        href: '/admin/import',
        label: 'Import',
        icon: (
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
              d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" />
          </svg>
        ),
      },
      {
        href: '/admin/redistribuir',
        label: 'Redistribuir Carteira',
        icon: (
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
              d="M8 7h12m0 0l-4-4m4 4l-4 4m0 6H4m0 0l4 4m-4-4l4-4" />
          </svg>
        ),
      },
      {
        href: '/atualizacoes',
        label: 'Atualizacoes',
        icon: (
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
              d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-3 7h3m-3 4h3m-6-4h.01M9 16h.01" />
          </svg>
        ),
      },
    ],
  },
];

// ---------------------------------------------------------------------------
// NavItemCollapsed — ícone só com tooltip no hover
// ---------------------------------------------------------------------------

interface NavItemCollapsedProps {
  item: NavItem;
  active: boolean;
  onClose: () => void;
}

function NavItemCollapsed({ item, active, onClose }: NavItemCollapsedProps) {
  return (
    <li className="relative group">
      <Link
        href={item.href}
        onClick={onClose}
        title={item.label}
        className={`
          relative flex items-center justify-center w-11 h-11 rounded-lg transition-colors mx-auto
          ${active
            ? 'text-green-700'
            : 'text-gray-500 hover:bg-gray-100 hover:text-gray-900'
          }
        `}
        style={active ? { backgroundColor: '#00B05018' } : undefined}
        aria-label={item.label}
        aria-current={active ? 'page' : undefined}
      >
        <span style={active ? { color: '#00B050' } : undefined}>
          {item.icon}
        </span>
        {item.showInboxBadge && (
          <InboxBadge active={active} collapsed />
        )}
        {item.showAgendaBadge && (
          <AgendaBadge active={active} collapsed />
        )}
        {item.previewBadge === 'em_construcao' && (
          <span
            className="absolute -top-0.5 -right-0.5 w-2.5 h-2.5 rounded-full border-2 border-white"
            style={{ backgroundColor: '#F97316' }}
            aria-label="Em construcao"
          />
        )}
        {item.previewBadge === 'bloqueado' && (
          <span
            className="absolute -top-0.5 -right-0.5 w-2.5 h-2.5 rounded-full border-2 border-white bg-gray-400"
            aria-label="Bloqueado"
          />
        )}
      </Link>

      {/* Tooltip — aparece no hover */}
      <div
        className="
          pointer-events-none absolute left-full top-1/2 -translate-y-1/2 ml-2 z-50
          bg-gray-900 text-white text-xs font-medium px-2 py-1 rounded whitespace-nowrap
          opacity-0 group-hover:opacity-100 transition-opacity duration-150
        "
        role="tooltip"
      >
        {item.label}
        <span className="absolute right-full top-1/2 -translate-y-1/2 border-4 border-transparent border-r-gray-900" />
      </div>
    </li>
  );
}

// ---------------------------------------------------------------------------
// Sidebar props
// ---------------------------------------------------------------------------

interface SidebarProps {
  mobileOpen: boolean;
  onClose: () => void;
  collapsed?: boolean;
  onToggleCollapse?: () => void;
}

export default function Sidebar({ mobileOpen, onClose, collapsed = false, onToggleCollapse }: SidebarProps) {
  const pathname = usePathname();
  const { user, isAdmin } = useAuth();

  const isGerenteOuAdmin = isAdmin || user?.role === 'gerente';

  const isActive = (href: string) => {
    if (href === '/') return pathname === '/';
    // /clientes redireciona para /carteira — ambos sao equivalentes na nav
    if (href === '/clientes') return pathname.startsWith('/clientes') || pathname.startsWith('/carteira');
    return pathname.startsWith(href);
  };

  function shouldShowGroup(group: NavGroup): boolean {
    if (group.adminOnly) return isAdmin;
    if (group.gerenteOuAdmin) return isGerenteOuAdmin;
    return true;
  }

  return (
    <>
      {/* Mobile overlay */}
      {mobileOpen && (
        <div
          className="fixed inset-0 bg-black/30 z-20 md:hidden"
          onClick={onClose}
          aria-hidden="true"
        />
      )}

      {/* Sidebar panel */}
      <aside
        className={`
          fixed top-0 left-0 h-full z-30
          bg-white border-r border-gray-200
          flex flex-col
          transition-all duration-200
          md:static md:translate-x-0
          ${mobileOpen ? 'translate-x-0' : '-translate-x-full md:translate-x-0'}
          ${collapsed ? 'w-14' : 'w-56 max-w-[80vw]'}
        `}
        role="navigation"
        aria-label="Menu principal"
      >
        {/* Brand */}
        <div className={`flex items-center border-b border-gray-100 gradient-vitao flex-shrink-0 ${collapsed ? 'justify-center px-2 py-4' : 'gap-3 px-4 py-4'}`}>
          <div className="w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0 bg-white/20">
            <span className="text-white font-bold text-sm">V</span>
          </div>
          {!collapsed && (
            <div className="min-w-0 flex-1">
              <p className="font-bold text-white text-sm leading-tight">CRM VITAO360</p>
              <p className="text-[10px] text-white/70 leading-tight">Inteligencia Comercial</p>
            </div>
          )}
        </div>

        {/* Nav por grupos */}
        <nav className={`flex-1 py-3 overflow-y-auto space-y-1 ${collapsed ? 'px-1' : 'px-2'}`}>
          {navGroups.map((group) => {
            if (!shouldShowGroup(group)) return null;
            return (
              <div key={group.label}>
                {!collapsed && (
                  <p className="px-3 mb-1 text-[10px] font-semibold text-gray-400 uppercase tracking-wider">
                    {group.label}
                  </p>
                )}
                {collapsed && (
                  <div className="h-px bg-gray-100 my-1.5 mx-1" aria-hidden="true" />
                )}
                <ul className="space-y-0.5">
                  {group.items.map((item) => {
                    const active = isActive(item.href);

                    if (collapsed) {
                      return (
                        <NavItemCollapsed
                          key={item.href}
                          item={item}
                          active={active}
                          onClose={onClose}
                        />
                      );
                    }

                    return (
                      <li key={item.href}>
                        {/* Divider antes do ultimo item (Manual) */}
                        {item.isDividerBefore && (
                          <div className="h-px bg-gray-100 my-1.5 mx-1" aria-hidden="true" />
                        )}
                        <Link
                          href={item.href}
                          onClick={onClose}
                          className={`
                            flex items-center gap-3 py-2.5 px-4 min-h-[44px] rounded text-sm font-medium transition-colors
                            ${active
                              ? 'bg-green-50 border-l-4 border-vitao-green text-vitao-green font-semibold pl-3'
                              : 'text-gray-700 hover:bg-gray-50 hover:text-gray-900'
                            }
                          `}
                          aria-current={active ? 'page' : undefined}
                        >
                          <span
                            className={active ? 'text-vitao-green' : 'text-gray-400'}
                          >
                            {item.icon}
                          </span>
                          <span className="flex-1 leading-tight">{item.label}</span>
                          {item.showInboxBadge && (
                            <InboxBadge active={active} collapsed={false} />
                          )}
                          {item.showAgendaBadge && (
                            <AgendaBadge active={active} collapsed={false} />
                          )}
                          {item.previewBadge === 'em_construcao' && (
                            <span className="inline-flex items-center px-1.5 py-0.5 rounded text-[9px] font-semibold uppercase tracking-wide bg-orange-100 text-orange-700 border border-orange-200 animate-pulse ml-auto flex-shrink-0">
                              EM CONST.
                            </span>
                          )}
                          {item.previewBadge === 'bloqueado' && (
                            <span className="inline-flex items-center gap-0.5 px-1.5 py-0.5 rounded text-[9px] font-semibold uppercase tracking-wide bg-gray-200 text-gray-600 border border-gray-300 ml-auto flex-shrink-0">
                              <svg className="w-2.5 h-2.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5}
                                  d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                              </svg>
                              BLOQUEADO
                            </span>
                          )}
                        </Link>
                      </li>
                    );
                  })}
                </ul>
              </div>
            );
          })}
        </nav>

        {/* MetaWidget — meta mensal fixada no bottom da sidebar */}
        {/* TODO Wave 3: conectar com /api/metas/atual — hardcoded values removed (R8) */}
        {false && (
        <div className={`flex-shrink-0 ${collapsed ? 'px-1 py-2' : 'px-3 py-3'}`}>
          <MetaWidget
            meta={250000}
            realizado={187000}
            mes="Abril 2026"
            collapsed={collapsed}
          />
        </div>
        )}

        {/* Collapse toggle (desktop only) + Footer */}
        <div className={`border-t border-gray-100 flex-shrink-0 ${collapsed ? 'px-1 py-2' : 'px-4 py-3'}`}>
          {/* Botao colapsar — desktop only */}
          {onToggleCollapse && (
            <button
              type="button"
              onClick={onToggleCollapse}
              title={collapsed ? 'Expandir menu' : 'Recolher menu'}
              aria-label={collapsed ? 'Expandir menu' : 'Recolher menu'}
              className={`
                hidden md:flex items-center justify-center rounded-lg transition-colors
                text-gray-400 hover:text-gray-700 hover:bg-gray-100
                ${collapsed ? 'w-9 h-9 mx-auto' : 'w-full h-8 gap-2 text-xs font-medium mb-2'}
              `}
            >
              <svg
                className={`w-4 h-4 transition-transform duration-200 ${collapsed ? 'rotate-180' : ''}`}
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                  d="M11 19l-7-7 7-7m8 14l-7-7 7-7" />
              </svg>
              {!collapsed && <span>Recolher</span>}
            </button>
          )}

          {!collapsed && (
            <>
              <p className="text-[10px] text-gray-400">VITAO Alimentos B2B</p>
              <p className="text-[10px] text-gray-300">v1.0 — 2026</p>
            </>
          )}
        </div>
      </aside>
    </>
  );
}

// ---------------------------------------------------------------------------
// Mobile hamburger button — exportado separadamente para o Header
// ---------------------------------------------------------------------------

export function HamburgerButton({ onClick }: { onClick: () => void }) {
  return (
    <button
      type="button"
      onClick={onClick}
      className="md:hidden p-2 rounded text-gray-500 hover:text-gray-900 hover:bg-gray-100 transition-colors"
      aria-label="Abrir menu"
    >
      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
          d="M4 6h16M4 12h16M4 18h16" />
      </svg>
    </button>
  );
}
