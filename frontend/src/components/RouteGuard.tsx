'use client';

import { useEffect, type ReactNode } from 'react';
import { usePathname, useRouter } from 'next/navigation';
import { useAuth } from '@/contexts/AuthContext';
import AppShell from '@/components/AppShell';

// ---------------------------------------------------------------------------
// RouteGuard — protege rotas por autenticacao e por role
//
// Regras de acesso:
//   /login            — publico
//   /admin/*          — somente role=admin
//   /redes            — role=admin ou gerente
//   todo o resto      — qualquer usuario autenticado
// ---------------------------------------------------------------------------

const PUBLIC_PATHS = ['/login'];

interface RouteGuardProps {
  children: ReactNode;
}

function AccessDenied({ reason }: { reason: string }) {
  const router = useRouter();
  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center">
      <div className="bg-white rounded-lg border border-gray-200 p-8 max-w-sm w-full text-center">
        <div className="w-12 h-12 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
          <svg className="w-6 h-6 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
              d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
          </svg>
        </div>
        <h2 className="text-sm font-bold text-gray-900 mb-2">Acesso Negado</h2>
        <p className="text-xs text-gray-500 mb-6">{reason}</p>
        <button
          type="button"
          onClick={() => router.replace('/')}
          className="px-4 py-2 text-xs font-semibold text-white rounded"
          style={{ backgroundColor: '#00B050' }}
        >
          Voltar ao inicio
        </button>
      </div>
    </div>
  );
}

export default function RouteGuard({ children }: RouteGuardProps) {
  const { user, loading } = useAuth();
  const router = useRouter();
  const pathname = usePathname();

  const isPublic = PUBLIC_PATHS.includes(pathname);
  const isAdminRoute = pathname.startsWith('/admin');
  const isRedesRoute = pathname === '/redes';

  useEffect(() => {
    if (loading) return;
    if (!isPublic && !user) {
      router.replace('/login');
    }
  }, [loading, user, isPublic, router]);

  // Enquanto valida auth: spinner minimo
  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="w-5 h-5 border-2 border-gray-300 border-t-green-600 rounded-full animate-spin" />
      </div>
    );
  }

  // Pagina publica (login): sem AppShell
  if (isPublic) {
    return <>{children}</>;
  }

  // Rota protegida sem usuario: nao renderiza (redirect em andamento)
  if (!user) {
    return null;
  }

  // /admin/* — somente admin
  if (isAdminRoute && user.role !== 'admin') {
    return (
      <AppShell>
        <AccessDenied reason="Esta pagina e restrita a administradores. Solicite acesso a Leandro." />
      </AppShell>
    );
  }

  // /redes — admin ou gerente
  if (isRedesRoute && user.role !== 'admin' && user.role !== 'gerente') {
    return (
      <AppShell>
        <AccessDenied reason="Esta pagina e restrita a administradores e gerentes." />
      </AppShell>
    );
  }

  // Autenticado com permissao: renderiza com AppShell
  return <AppShell>{children}</AppShell>;
}
