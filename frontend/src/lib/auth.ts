'use client';

// ---------------------------------------------------------------------------
// Auth token utilities — localStorage, SSR-safe
// Chaves privadas ao modulo, nao exportadas
// ---------------------------------------------------------------------------

const TOKEN_KEY = 'vitao360_access_token';
const REFRESH_KEY = 'vitao360_refresh_token';

export function getToken(): string | null {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem(TOKEN_KEY);
}

export function setTokens(access: string, refresh: string): void {
  localStorage.setItem(TOKEN_KEY, access);
  localStorage.setItem(REFRESH_KEY, refresh);
}

export function clearTokens(): void {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(REFRESH_KEY);
}

export function getRefreshToken(): string | null {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem(REFRESH_KEY);
}
