'use client';

import {
  createContext,
  useContext,
  useEffect,
  useState,
  type ReactNode,
} from 'react';
import { getToken, setTokens, clearTokens } from '@/lib/auth';
import {
  type UserRole,
  type UserRoleRaw,
  normalizeRole,
  hasRole,
  isAdmin as checkIsAdmin,
  isGerenteOrAbove,
  isConsultorOrAbove,
} from '@/lib/permissions';

// ---------------------------------------------------------------------------
// Tipos
// ---------------------------------------------------------------------------

export interface User {
  id: number;
  email: string;
  nome: string;
  /** Role raw como retornado pelo backend (ex.: "admin", "consultor_externo") */
  role: UserRoleRaw;
  consultor_nome: string | null;
}

interface AuthContextType {
  user: User | null;
  loading: boolean;
  login: (email: string, senha: string) => Promise<void>;
  logout: () => void;
  /** Role canonizado do usuario (ADMIN | GERENTE | CONSULTOR | VENDEDOR | null) */
  role: UserRole | null;
  /** true se role === ADMIN */
  isAdmin: boolean;
  /** true se role >= GERENTE */
  isGerente: boolean;
  /** true se role >= CONSULTOR */
  isConsultor: boolean;
  /** Verifica se o usuario tem nivel de acesso suficiente para minRole */
  hasRole: (minRole: UserRole) => boolean;
}

// ---------------------------------------------------------------------------
// Contexto
// ---------------------------------------------------------------------------

const AuthContext = createContext<AuthContextType | null>(null);

const BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? '';

// ---------------------------------------------------------------------------
// Provider
// ---------------------------------------------------------------------------

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  // Ao montar: tenta revalidar token existente
  useEffect(() => {
    const token = getToken();
    if (token) {
      fetchMe(token)
        .then(setUser)
        .catch(() => clearTokens())
        .finally(() => setLoading(false));
    } else {
      setLoading(false);
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function fetchMe(token: string): Promise<User> {
    const res = await fetch(`${BASE_URL}/api/auth/me`, {
      cache: 'no-store',
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!res.ok) throw new Error('Token invalido');
    return res.json() as Promise<User>;
  }

  async function login(email: string, senha: string): Promise<void> {
    const res = await fetch(`${BASE_URL}/api/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, senha }),
    });
    if (!res.ok) {
      const body = await res.json().catch(() => ({})) as Record<string, unknown>;
      throw new Error((body.detail as string) || 'Erro no login');
    }
    const data = await res.json() as { access_token: string; refresh_token: string };
    setTokens(data.access_token, data.refresh_token);
    const me = await fetchMe(data.access_token);
    setUser(me);
  }

  function logout(): void {
    clearTokens();
    setUser(null);
  }

  const canonicalRole = normalizeRole(user?.role ?? null);

  return (
    <AuthContext.Provider
      value={{
        user,
        loading,
        login,
        logout,
        role: canonicalRole,
        isAdmin: checkIsAdmin(user?.role),
        isGerente: isGerenteOrAbove(user?.role),
        isConsultor: isConsultorOrAbove(user?.role),
        hasRole: (minRole: UserRole) => hasRole(user?.role, minRole),
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

// ---------------------------------------------------------------------------
// Hook
// ---------------------------------------------------------------------------

export function useAuth(): AuthContextType {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth deve ser usado dentro de AuthProvider');
  return ctx;
}
