'use client';

/**
 * CRM VITAO360 — RoleGuard
 *
 * HOC e hook para verificacao condicional de role em logica de componente.
 *
 * Duas formas de uso:
 *
 * 1. Hook useRoleGuard — retorna boolean, util para condicionais dentro do componente:
 *
 *    const canSeeDashboard = useRoleGuard('GERENTE');
 *    return (
 *      <nav>
 *        {canSeeDashboard && <Link href="/dashboard">Dashboard</Link>}
 *      </nav>
 *    );
 *
 * 2. Componente RoleGuard — wrapper declarativo equivalente a RequireRole sem fallback:
 *
 *    <RoleGuard minRole="GERENTE">
 *      <MenuItemGestao />
 *    </RoleGuard>
 *
 * Diferenca de RequireRole: RoleGuard e focado em condicionais leves e wrappers
 * de navegacao. RequireRole e mais rico (suporta fallback, loading state explicito).
 */

import type { ReactNode } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import type { UserRole } from '@/lib/permissions';

// ---------------------------------------------------------------------------
// Hook
// ---------------------------------------------------------------------------

/**
 * Retorna true se o usuario autenticado tem nivel >= minRole.
 *
 * Retorna false enquanto o contexto de autenticacao ainda esta carregando,
 * para evitar renderizacao prematura de conteudo protegido.
 */
export function useRoleGuard(minRole: UserRole): boolean {
  const { hasRole, loading } = useAuth();
  if (loading) return false;
  return hasRole(minRole);
}

// ---------------------------------------------------------------------------
// Componente
// ---------------------------------------------------------------------------

interface RoleGuardProps {
  minRole: UserRole;
  children: ReactNode;
}

/**
 * Wrapper de guard sem fallback — nao renderiza children se role insuficiente.
 *
 * Para fallback, use RequireRole.
 */
export function RoleGuard({ minRole, children }: RoleGuardProps): ReactNode {
  const allowed = useRoleGuard(minRole);
  if (!allowed) return null;
  return children;
}
