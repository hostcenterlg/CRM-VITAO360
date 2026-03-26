'use client';

import { useState } from 'react';
import { useRouter, usePathname } from 'next/navigation';
import Sidebar, { HamburgerButton } from './Sidebar';
import { useAuth } from '@/contexts/AuthContext';

// ---------------------------------------------------------------------------
// AppShell — sidebar + header com info do usuario + main content
// Client component pois gerencia estado de sidebar e auth
// ---------------------------------------------------------------------------

// Map pathname -> page title for automatic header label
const PAGE_TITLES: Record<string, string> = {
  '/':              'Dashboard CEO',
  '/agenda':        'Agenda Comercial',
  '/carteira':      'Carteira de Clientes',
  '/sinaleiro':     'Sinaleiro de Carteira',
  '/projecao':      'Projecao Comercial',
  '/redes':         'Redes e Franquias',
  '/rnc':           'RNC',
  '/admin/motor':   'Motor de IA',
  '/admin/usuarios':'Usuarios',
};

// Map pathname -> breadcrumb segments [{ label, href? }]
const BREADCRUMBS: Record<string, Array<{ label: string; href?: string }>> = {
  '/':              [{ label: 'Dashboard' }],
  '/agenda':        [{ label: 'Dashboard', href: '/' }, { label: 'Agenda' }],
  '/carteira':      [{ label: 'Dashboard', href: '/' }, { label: 'Carteira' }],
  '/sinaleiro':     [{ label: 'Dashboard', href: '/' }, { label: 'Sinaleiro' }],
  '/projecao':      [{ label: 'Dashboard', href: '/' }, { label: 'Projecao' }],
  '/redes':         [{ label: 'Dashboard', href: '/' }, { label: 'Redes' }],
  '/rnc':           [{ label: 'Dashboard', href: '/' }, { label: 'RNC' }],
  '/admin/motor':   [{ label: 'Admin', href: '/' }, { label: 'Motor' }],
  '/admin/usuarios':[{ label: 'Admin', href: '/' }, { label: 'Usuarios' }],
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

export default function AppShell({ children, pageTitle }: AppShellProps) {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const { user, logout } = useAuth();
  const router = useRouter();
  const pathname = usePathname();

  // Auto-detect page title if not explicitly passed
  const resolvedTitle = pageTitle ?? PAGE_TITLES[pathname] ?? undefined;
  const breadcrumbs = BREADCRUMBS[pathname] ?? null;

  function handleLogout() {
    logout();
    router.replace('/login');
  }

  return (
    <div className="flex h-screen overflow-hidden bg-gray-50">
      {/* Sidebar */}
      <Sidebar
        mobileOpen={sidebarOpen}
        onClose={() => setSidebarOpen(false)}
      />

      {/* Coluna principal */}
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        {/* Header */}
        <header className="flex-shrink-0 bg-white border-b border-gray-200 px-4 py-2.5 flex items-center gap-3">
          {/* Hamburger mobile */}
          <HamburgerButton onClick={() => setSidebarOpen(true)} />

          {/* Breadcrumb + titulo */}
          <div className="flex items-center gap-1 min-w-0">
            {breadcrumbs && breadcrumbs.length > 1 ? (
              <>
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
              </>
            ) : resolvedTitle ? (
              <h1 className="text-base font-semibold text-gray-900">{resolvedTitle}</h1>
            ) : null}
          </div>

          {/* Spacer */}
          <div className="flex-1" />

          {/* Info do usuario autenticado */}
          {user && (
            <div className="flex items-center gap-3">
              {/* Nome + role */}
              <div className="hidden sm:flex flex-col items-end gap-0.5">
                <span className="text-sm font-medium text-gray-800 leading-tight">
                  {user.consultor_nome ?? user.nome}
                </span>
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
                className="flex items-center gap-1.5 px-2.5 py-1.5 text-xs font-medium text-gray-600
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
          <div className="max-w-screen-2xl mx-auto p-3 lg:p-6">
            {children}
          </div>
        </main>
      </div>
    </div>
  );
}
