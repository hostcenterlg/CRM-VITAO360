'use client';

/**
 * CRM VITAO360 — RequireRole
 *
 * Componente de guard declarativo: renderiza children apenas se o usuario
 * autenticado tiver nivel de role >= minRole. Caso contrario, renderiza
 * o fallback (ou nada se fallback nao for fornecido).
 *
 * Uso tipico:
 *
 *   // Esconde silenciosamente para quem nao tem acesso
 *   <RequireRole minRole="GERENTE">
 *     <BotaoRedistribuir />
 *   </RequireRole>
 *
 *   // Mostra mensagem de acesso negado
 *   <RequireRole minRole="ADMIN" fallback={<AcessoNegado />}>
 *     <PainelAdmin />
 *   </RequireRole>
 *
 * Wave 2: aplicar nas paginas /gestao, /dashboard, /admin, etc.
 */

import type { ReactNode } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import type { UserRole } from '@/lib/permissions';

// ---------------------------------------------------------------------------
// Props
// ---------------------------------------------------------------------------

interface RequireRoleProps {
  /** Nivel minimo de role exigido para renderizar children. */
  minRole: UserRole;
  /**
   * O que renderizar quando o usuario nao tem permissao.
   * - undefined (padrao): nao renderiza nada (null)
   * - ReactNode: renderiza o fallback fornecido
   */
  fallback?: ReactNode;
  children: ReactNode;
}

// ---------------------------------------------------------------------------
// Componente
// ---------------------------------------------------------------------------

export function RequireRole({
  minRole,
  fallback = null,
  children,
}: RequireRoleProps): ReactNode {
  const { hasRole, loading } = useAuth();

  // Durante carregamento do contexto de autenticacao, nao renderiza nada
  // para evitar flash de conteudo protegido antes da verificacao de role.
  if (loading) return null;

  if (!hasRole(minRole)) {
    return fallback;
  }

  return children;
}
