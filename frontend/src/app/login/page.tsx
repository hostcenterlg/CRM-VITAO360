'use client';

import { useState, useEffect, type FormEvent } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/contexts/AuthContext';

// ---------------------------------------------------------------------------
// Login page — LIGHT theme, verde #00B050, sem AppShell
// ---------------------------------------------------------------------------

export default function LoginPage() {
  const { login, user, loading } = useAuth();
  const router = useRouter();

  const [email, setEmail] = useState('');
  const [senha, setSenha] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [erro, setErro] = useState<string | null>(null);

  // Se ja autenticado, redireciona para dashboard
  useEffect(() => {
    if (!loading && user) {
      router.replace('/');
    }
  }, [loading, user, router]);

  async function handleSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setErro(null);
    setSubmitting(true);
    try {
      await login(email.trim(), senha);
      router.replace('/');
    } catch (err) {
      setErro(err instanceof Error ? err.message : 'Erro desconhecido');
    } finally {
      setSubmitting(false);
    }
  }

  // Enquanto carrega estado de auth, nao pisca o form
  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="w-5 h-5 border-2 border-gray-300 border-t-green-600 rounded-full animate-spin" />
      </div>
    );
  }

  return (
    <div className="min-h-screen flex items-center justify-center px-4" style={{ background: 'linear-gradient(160deg, #f0fdf4 0%, #f9fafb 50%, #ffffff 100%)' }}>
      <div className="w-full max-w-sm">
        {/* Logo / brand */}
        <div className="flex flex-col items-center mb-8">
          <div
            className="w-16 h-16 rounded-2xl flex items-center justify-center mb-4 shadow-md"
            style={{ backgroundColor: '#00B050' }}
          >
            <span className="text-white font-bold text-3xl tracking-tight">V</span>
          </div>
          <h1 className="text-3xl font-bold text-gray-900 tracking-tight">CRM VITAO360</h1>
          <p className="text-sm font-medium mt-2" style={{ color: '#00B050' }}>
            Sistema de Inteligencia Comercial
          </p>
          <p className="text-xs text-gray-400 mt-1">VITAO Alimentos — CRM B2B</p>
        </div>

        {/* Card de login */}
        <div className="bg-white rounded-xl border border-gray-200 shadow-lg p-6">
          <h2 className="text-base font-semibold text-gray-900 mb-5">
            Acesso ao sistema
          </h2>

          <form onSubmit={handleSubmit} noValidate className="space-y-4">
            {/* Email */}
            <div>
              <label
                htmlFor="email"
                className="block text-sm font-medium text-gray-700 mb-1"
              >
                E-mail
              </label>
              <input
                id="email"
                type="email"
                autoComplete="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                disabled={submitting}
                placeholder="seuemail@vitaoalimentos.com.br"
                className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg
                           bg-white text-gray-900 placeholder-gray-400
                           focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-green-500
                           disabled:bg-gray-50 disabled:text-gray-500"
              />
            </div>

            {/* Senha */}
            <div>
              <label
                htmlFor="senha"
                className="block text-sm font-medium text-gray-700 mb-1"
              >
                Senha
              </label>
              <input
                id="senha"
                type="password"
                autoComplete="current-password"
                required
                value={senha}
                onChange={(e) => setSenha(e.target.value)}
                disabled={submitting}
                placeholder="••••••••"
                className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg
                           bg-white text-gray-900 placeholder-gray-400
                           focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-green-500
                           disabled:bg-gray-50 disabled:text-gray-500"
              />
            </div>

            {/* Mensagem de erro */}
            {erro && (
              <div
                role="alert"
                className="flex items-start gap-2 px-3 py-2 bg-red-50 border border-red-200 rounded-lg"
              >
                <svg
                  className="w-4 h-4 text-red-500 mt-0.5 flex-shrink-0"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                  />
                </svg>
                <p className="text-sm text-red-700">{erro}</p>
              </div>
            )}

            {/* Botao entrar */}
            <button
              type="submit"
              disabled={submitting || !email || !senha}
              className="w-full min-h-[44px] py-2.5 px-4 text-sm font-semibold text-white rounded-lg gradient-vitao
                         transition-all focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500
                         disabled:opacity-50 disabled:cursor-not-allowed hover:opacity-90 active:scale-[0.99]"
            >
              {submitting ? (
                <span className="flex items-center justify-center gap-2">
                  <span className="w-4 h-4 border-2 border-white/40 border-t-white rounded-full animate-spin" />
                  Entrando...
                </span>
              ) : (
                <span className="flex items-center justify-center gap-2">
                  Entrar
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14 5l7 7m0 0l-7 7m7-7H3" />
                  </svg>
                </span>
              )}
            </button>
          </form>
        </div>

        <p className="text-center text-xs text-gray-400 mt-6">
          CRM VITAO360 v1.0 — Motor de Inteligencia Comercial
        </p>
      </div>
    </div>
  );
}
