'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import Sidebar, { HamburgerButton } from './Sidebar';
import { useAuth } from '@/contexts/AuthContext';

// ---------------------------------------------------------------------------
// AppShell — sidebar + header com info do usuario + main content
// Client component pois gerencia estado de sidebar e auth
// ---------------------------------------------------------------------------

interface AppShellProps {
  children: React.ReactNode;
  pageTitle?: string;
}

// Badge de role — cores por tipo de acesso
function RoleBadge({ role }: { role: string }) {
  const styles: Record<string, string> = {
    admin:
      'bg-purple-100 text-purple-700 border border-purple-200',
    consultor:
      'bg-green-100 text-green-700 border border-green-200',
    viewer:
      'bg-gray-100 text-gray-600 border border-gray-200',
  };
  const label: Record<string, string> = {
    admin: 'Admin',
    consultor: 'Consultor',
    viewer: 'Visualizacao',
  };
  const cls = styles[role] ?? styles['viewer'];
  return (
    <span className={`text-[10px] font-semibold px-1.5 py-0.5 rounded ${cls}`}>
      {label[role] ?? role}
    </span>
  );
}

export default function AppShell({ children, pageTitle }: AppShellProps) {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const { user, logout } = useAuth();
  const router = useRouter();

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

          {/* Titulo da pagina (opcional) */}
          {pageTitle && (
            <h1 className="text-base font-semibold text-gray-900">{pageTitle}</h1>
          )}

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
          <div className="max-w-screen-2xl mx-auto p-4 lg:p-6">
            {children}
          </div>
        </main>
      </div>
    </div>
  );
}
