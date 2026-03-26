'use client';

import { useEffect, type ReactNode } from 'react';
import { usePathname, useRouter } from 'next/navigation';
import { useAuth } from '@/contexts/AuthContext';
import AppShell from '@/components/AppShell';

// ---------------------------------------------------------------------------
// RouteGuard — protege todas as rotas exceto /login
// Renderiza AppShell apenas em rotas autenticadas
// ---------------------------------------------------------------------------

const PUBLIC_PATHS = ['/login'];

interface RouteGuardProps {
  children: ReactNode;
}

export default function RouteGuard({ children }: RouteGuardProps) {
  const { user, loading } = useAuth();
  const router = useRouter();
  const pathname = usePathname();

  const isPublic = PUBLIC_PATHS.includes(pathname);

  useEffect(() => {
    if (loading) return;
    // Rota protegida e sem usuario: redireciona para login
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

  // Autenticado: renderiza com AppShell
  return <AppShell>{children}</AppShell>;
}
