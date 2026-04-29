/**
 * CRM VITAO360 — Permissoes e hierarquia de roles (frontend).
 *
 * Espelha a logica de RBAC do backend (security.py).
 * Os valores de UserRole batem com os strings armazenados no banco de dados.
 *
 * Roles (do maior para o menor nivel):
 *   ADMIN             — superusuario, acesso total (Leandro)
 *   GERENTE           — dashboard, redistribuir, gestao (Daiane)
 *   CONSULTOR         — propria carteira, Inbox, Agenda, Pedidos (Manu, Larissa)
 *   VENDEDOR          — propria carteira + Agenda + tarefas apenas (Julio)
 *
 * Nota sobre VENDEDOR: o valor armazenado no banco e "consultor_externo".
 * O frontend aceita ambas as formas via normalize().
 */

// ---------------------------------------------------------------------------
// Tipos
// ---------------------------------------------------------------------------

/** Valores que chegam do backend via /api/auth/me */
export type UserRoleRaw =
  | 'admin'
  | 'gerente'
  | 'consultor'
  | 'consultor_externo'
  | 'ADMIN'
  | 'GERENTE'
  | 'CONSULTOR'
  | 'VENDEDOR';

/** Forma canonizada usada internamente no frontend */
export type UserRole = 'ADMIN' | 'GERENTE' | 'CONSULTOR' | 'VENDEDOR';

// ---------------------------------------------------------------------------
// Hierarquia numerica
// ---------------------------------------------------------------------------

/**
 * Quanto maior o numero, mais permissoes.
 * Espelha ROLE_HIERARCHY do backend (security.py).
 */
export const ROLE_HIERARCHY: Record<UserRole, number> = {
  ADMIN: 4,
  GERENTE: 3,
  CONSULTOR: 2,
  VENDEDOR: 1,
};

// ---------------------------------------------------------------------------
// Normalizacao
// ---------------------------------------------------------------------------

/**
 * Converte qualquer forma de role (lowercase do banco ou uppercase do frontend)
 * para a forma canonizada UserRole.
 *
 * - "admin"             -> "ADMIN"
 * - "gerente"           -> "GERENTE"
 * - "consultor"         -> "CONSULTOR"
 * - "consultor_externo" -> "VENDEDOR"
 * - "VENDEDOR"          -> "VENDEDOR"
 * - null / undefined    -> null
 */
export function normalizeRole(raw: string | null | undefined): UserRole | null {
  if (!raw) return null;
  const map: Record<string, UserRole> = {
    admin: 'ADMIN',
    ADMIN: 'ADMIN',
    gerente: 'GERENTE',
    GERENTE: 'GERENTE',
    consultor: 'CONSULTOR',
    CONSULTOR: 'CONSULTOR',
    consultor_externo: 'VENDEDOR',
    VENDEDOR: 'VENDEDOR',
  };
  return map[raw] ?? null;
}

// ---------------------------------------------------------------------------
// Verificacao de permissao
// ---------------------------------------------------------------------------

/**
 * Retorna true se o usuario tem nivel de role >= minRole.
 *
 * Aceita tanto a forma raw (do banco) quanto a forma canonizada.
 *
 * Exemplos:
 *   hasRole('admin', 'GERENTE')       -> true
 *   hasRole('gerente', 'ADMIN')       -> false
 *   hasRole('consultor_externo', 'VENDEDOR') -> true
 *   hasRole(null, 'VENDEDOR')         -> false
 */
export function hasRole(
  userRole: string | null | undefined,
  minRole: UserRole,
): boolean {
  const normalized = normalizeRole(userRole);
  if (!normalized) return false;
  return ROLE_HIERARCHY[normalized] >= ROLE_HIERARCHY[minRole];
}

// ---------------------------------------------------------------------------
// Helpers especializados
// ---------------------------------------------------------------------------

/** Usuario e administrador? */
export function isAdmin(userRole: string | null | undefined): boolean {
  return normalizeRole(userRole) === 'ADMIN';
}

/** Usuario e gerente ou superior? */
export function isGerenteOrAbove(userRole: string | null | undefined): boolean {
  return hasRole(userRole, 'GERENTE');
}

/** Usuario e consultor ou superior? (exclui VENDEDOR/consultor_externo) */
export function isConsultorOrAbove(userRole: string | null | undefined): boolean {
  return hasRole(userRole, 'CONSULTOR');
}

/** Usuario e vendedor externo (Julio)? */
export function isVendedor(userRole: string | null | undefined): boolean {
  return normalizeRole(userRole) === 'VENDEDOR';
}

// ---------------------------------------------------------------------------
// Permissoes de pagina (mapa declarativo)
// ---------------------------------------------------------------------------

/**
 * Mapeamento de paginas/funcionalidades para o nivel minimo de role.
 *
 * Usado por RequireRole e RoleGuard para centralizar regras de acesso.
 * Wave 2 aplica esses guards nas paginas concretas.
 */
export const PAGE_PERMISSIONS: Record<string, UserRole> = {
  // Gestao (Daiane e acima)
  '/gestao': 'GERENTE',
  '/relatorios': 'GERENTE',
  '/sinaleiro': 'GERENTE',
  '/analise-critica': 'GERENTE',
  '/redistribuir': 'GERENTE',

  // Dashboard agregado (Gerente e acima)
  '/dashboard': 'GERENTE',

  // RBAC / configuracao (Admin apenas)
  '/admin': 'ADMIN',
  '/admin/usuarios': 'ADMIN',
  '/admin/rbac': 'ADMIN',

  // Uso geral (Consultor e acima)
  '/carteira': 'CONSULTOR',
  '/inbox': 'CONSULTOR',
  '/pedidos': 'CONSULTOR',
  '/produtos': 'CONSULTOR',
  '/manual': 'CONSULTOR',

  // Agenda e tarefas (todos, inclusive Vendedor)
  '/agenda': 'VENDEDOR',
  '/tarefas': 'VENDEDOR',
};
