'use client';

import { useState, useEffect, useCallback } from 'react';
import { fetchJson } from '@/lib/api-internal';

// ---------------------------------------------------------------------------
// Admin Usuarios — CRUD de usuarios do sistema
// Acesso exclusivo: role=admin (P1 Leandro)
// ---------------------------------------------------------------------------

type RoleUsuario = 'admin' | 'gerente' | 'consultor' | 'consultor_externo';

interface Usuario {
  id: number;
  nome: string;
  email: string;
  role: RoleUsuario;
  consultor_vinculado: string | null;
  ativo: boolean;
  ultimo_login: string | null;
}

interface UsuarioForm {
  nome: string;
  email: string;
  senha: string;
  role: RoleUsuario;
  consultor_vinculado: string;
  ativo: boolean;
}

// ---------------------------------------------------------------------------
// Mock data
// ---------------------------------------------------------------------------

const MOCK_USUARIOS: Usuario[] = [
  { id: 1, nome: 'Leandro Vitao',    email: 'leandro@vitao.com.br',  role: 'admin',              consultor_vinculado: null,      ativo: true,  ultimo_login: '2026-03-25T08:00:00' },
  { id: 2, nome: 'Manu Ditzel',      email: 'manu@vitao.com.br',     role: 'consultor',          consultor_vinculado: 'MANU',    ativo: true,  ultimo_login: '2026-03-25T07:45:00' },
  { id: 3, nome: 'Larissa Padilha',  email: 'larissa@vitao.com.br',  role: 'consultor',          consultor_vinculado: 'LARISSA', ativo: true,  ultimo_login: '2026-03-25T07:30:00' },
  { id: 4, nome: 'Daiane Stavicki',  email: 'daiane@vitao.com.br',   role: 'gerente',            consultor_vinculado: 'DAIANE',  ativo: true,  ultimo_login: '2026-03-24T18:00:00' },
  { id: 5, nome: 'Julio Gadret',     email: 'julio@vitao.com.br',    role: 'consultor_externo',  consultor_vinculado: 'JULIO',   ativo: true,  ultimo_login: '2026-03-23T14:00:00' },
];

// ---------------------------------------------------------------------------
// Constantes
// ---------------------------------------------------------------------------

const ROLE_CONFIG: Record<RoleUsuario, { label: string; bg: string; text: string }> = {
  admin:              { label: 'Admin',      bg: '#7C3AED', text: '#fff' },
  gerente:            { label: 'Gerente',    bg: '#2563EB', text: '#fff' },
  consultor:          { label: 'Consultor',  bg: '#00B050', text: '#fff' },
  consultor_externo:  { label: 'Ext.',       bg: '#6B7280', text: '#fff' },
};

const CONSULTORES = ['MANU', 'LARISSA', 'DAIANE', 'JULIO'];

// ---------------------------------------------------------------------------
// Componentes internos
// ---------------------------------------------------------------------------

function RoleBadgeAdmin({ role }: { role: RoleUsuario }) {
  const cfg = ROLE_CONFIG[role] ?? { label: role, bg: '#e5e7eb', text: '#374151' };
  return (
    <span className="inline-flex items-center px-2 py-0.5 text-[10px] font-semibold rounded uppercase"
      style={{ backgroundColor: cfg.bg, color: cfg.text }}>
      {cfg.label}
    </span>
  );
}

function AtivoToggle({ ativo, onChange }: { ativo: boolean; onChange: () => void }) {
  return (
    <button
      type="button"
      onClick={onChange}
      aria-label={ativo ? 'Desativar usuario' : 'Ativar usuario'}
      className={`relative inline-flex h-5 w-9 flex-shrink-0 items-center rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-green-500 focus:ring-offset-1 ${ativo ? 'bg-green-500' : 'bg-gray-300'}`}
    >
      <span className={`inline-block h-3.5 w-3.5 rounded-full bg-white shadow transition-transform ${ativo ? 'translate-x-4' : 'translate-x-1'}`} />
    </button>
  );
}

interface ModalUsuarioProps {
  usuario: Usuario | null;
  onClose: () => void;
  onSalvar: (form: UsuarioForm, id?: number) => Promise<void>;
}

function ModalUsuario({ usuario, onClose, onSalvar }: ModalUsuarioProps) {
  const isEdicao = usuario !== null;
  const [form, setForm] = useState<UsuarioForm>({
    nome: usuario?.nome ?? '',
    email: usuario?.email ?? '',
    senha: '',
    role: usuario?.role ?? 'consultor',
    consultor_vinculado: usuario?.consultor_vinculado ?? '',
    ativo: usuario?.ativo ?? true,
  });
  const [loading, setLoading] = useState(false);
  const [errors, setErrors] = useState<Partial<Record<keyof UsuarioForm, string>>>({});

  function validate(): boolean {
    const e: Partial<Record<keyof UsuarioForm, string>> = {};
    if (!form.nome.trim()) e.nome = 'Nome obrigatorio';
    if (!form.email.trim() || !form.email.includes('@')) e.email = 'Email valido obrigatorio';
    if (!isEdicao && !form.senha.trim()) e.senha = 'Senha obrigatoria para novo usuario';
    setErrors(e);
    return Object.keys(e).length === 0;
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!validate()) return;
    setLoading(true);
    try {
      await onSalvar(form, usuario?.id);
      onClose();
    } catch {
      // erro tratado externamente
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    function onKey(e: KeyboardEvent) { if (e.key === 'Escape') onClose(); }
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [onClose]);

  const mostrarConsultor = form.role === 'consultor' || form.role === 'consultor_externo';

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center"
      style={{ backgroundColor: 'rgba(0,0,0,0.5)' }}
      role="dialog"
      aria-modal="true"
      aria-labelledby="modal-usuario-titulo"
    >
      <div className="bg-white rounded-lg shadow-xl w-full max-w-md mx-4">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200">
          <h2 id="modal-usuario-titulo" className="text-sm font-bold text-gray-900 uppercase tracking-wide">
            {isEdicao ? 'Editar Usuario' : 'Novo Usuario'}
          </h2>
          <button
            type="button"
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 p-1 rounded focus:outline-none focus:ring-2 focus:ring-green-500"
            aria-label="Fechar modal"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Body */}
        <form onSubmit={handleSubmit} className="px-6 py-5 space-y-4">
          {/* Nome */}
          <div>
            <label className="block text-xs font-semibold text-gray-700 mb-1 uppercase tracking-wide">
              Nome Completo *
            </label>
            <input
              type="text"
              value={form.nome}
              onChange={e => setForm(f => ({ ...f, nome: e.target.value }))}
              placeholder="Nome do usuario"
              className={`w-full h-9 px-3 text-xs border rounded focus:outline-none focus:ring-2 focus:ring-green-500 ${errors.nome ? 'border-red-500' : 'border-gray-300'}`}
            />
            {errors.nome && <p className="mt-1 text-[10px] text-red-600">{errors.nome}</p>}
          </div>

          {/* Email */}
          <div>
            <label className="block text-xs font-semibold text-gray-700 mb-1 uppercase tracking-wide">
              Email *
            </label>
            <input
              type="email"
              value={form.email}
              onChange={e => setForm(f => ({ ...f, email: e.target.value }))}
              placeholder="usuario@vitao.com.br"
              className={`w-full h-9 px-3 text-xs border rounded focus:outline-none focus:ring-2 focus:ring-green-500 ${errors.email ? 'border-red-500' : 'border-gray-300'}`}
            />
            {errors.email && <p className="mt-1 text-[10px] text-red-600">{errors.email}</p>}
          </div>

          {/* Role */}
          <div>
            <label className="block text-xs font-semibold text-gray-700 mb-1 uppercase tracking-wide">
              Role *
            </label>
            <select
              value={form.role}
              onChange={e => setForm(f => ({ ...f, role: e.target.value as RoleUsuario }))}
              className="w-full h-9 px-3 text-xs border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-green-500 bg-white"
            >
              <option value="admin">Admin — Acesso total</option>
              <option value="gerente">Gerente — Dashboard + Redes + Relatorios</option>
              <option value="consultor">Consultor — Agenda propria + Carteira + RNC</option>
              <option value="consultor_externo">Consultor Externo — Somente agenda propria</option>
            </select>
          </div>

          {/* Consultor vinculado (condicional) */}
          {mostrarConsultor && (
            <div>
              <label className="block text-xs font-semibold text-gray-700 mb-1 uppercase tracking-wide">
                Consultor Vinculado
              </label>
              <select
                value={form.consultor_vinculado}
                onChange={e => setForm(f => ({ ...f, consultor_vinculado: e.target.value }))}
                className="w-full h-9 px-3 text-xs border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-green-500 bg-white"
              >
                <option value="">Nenhum</option>
                {CONSULTORES.map(c => (
                  <option key={c} value={c}>{c}</option>
                ))}
              </select>
            </div>
          )}

          {/* Senha */}
          <div>
            <label className="block text-xs font-semibold text-gray-700 mb-1 uppercase tracking-wide">
              Senha Temporaria {isEdicao ? '(vazio = manter atual)' : '*'}
            </label>
            <input
              type="password"
              value={form.senha}
              onChange={e => setForm(f => ({ ...f, senha: e.target.value }))}
              placeholder={isEdicao ? 'Deixe vazio para nao alterar' : 'Senha inicial'}
              className={`w-full h-9 px-3 text-xs border rounded focus:outline-none focus:ring-2 focus:ring-green-500 ${errors.senha ? 'border-red-500' : 'border-gray-300'}`}
            />
            {errors.senha && <p className="mt-1 text-[10px] text-red-600">{errors.senha}</p>}
          </div>

          {/* Status */}
          <div className="flex items-center justify-between pt-1">
            <label className="text-xs font-semibold text-gray-700 uppercase tracking-wide">Status</label>
            <div className="flex items-center gap-2">
              <span className="text-xs text-gray-500">{form.ativo ? 'Ativo' : 'Inativo'}</span>
              <AtivoToggle ativo={form.ativo} onChange={() => setForm(f => ({ ...f, ativo: !f.ativo }))} />
            </div>
          </div>

          {/* Footer */}
          <div className="flex justify-between pt-2 border-t border-gray-100">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-xs font-medium text-gray-600 border border-gray-200 rounded hover:bg-gray-50 transition-colors"
            >
              Cancelar
            </button>
            <button
              type="submit"
              disabled={loading}
              className="px-5 py-2 text-xs font-semibold text-white rounded transition-colors disabled:opacity-60"
              style={{ backgroundColor: loading ? '#9CA3AF' : '#00B050' }}
            >
              {loading ? 'Salvando...' : 'Salvar'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Pagina principal
// ---------------------------------------------------------------------------

export default function AdminUsuariosPage() {
  const [usuarios, setUsuarios] = useState<Usuario[]>([]);
  const [loading, setLoading] = useState(true);
  const [modalUsuario, setModalUsuario] = useState<Usuario | null | 'novo'>(null);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const data = await fetchJson<Usuario[]>('/api/usuarios');
      setUsuarios(data);
    } catch {
      setUsuarios(MOCK_USUARIOS);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { void load(); }, [load]);

  async function handleSalvar(form: UsuarioForm, id?: number) {
    if (id) {
      await fetchJson(`/api/usuarios/${id}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(form),
      });
    } else {
      await fetchJson('/api/usuarios', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(form),
      });
    }
    await load();
  }

  async function handleToggleAtivo(usuario: Usuario) {
    try {
      await fetchJson(`/api/usuarios/${usuario.id}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ativo: !usuario.ativo }),
      });
      await load();
    } catch {
      // API indisponivel — atualizar localmente para demonstracao
      setUsuarios(prev =>
        prev.map(u => u.id === usuario.id ? { ...u, ativo: !u.ativo } : u)
      );
    }
  }

  function formatUltimoLogin(iso: string | null) {
    if (!iso) return 'Nunca';
    const d = new Date(iso);
    return d.toLocaleDateString('pt-BR', { day: '2-digit', month: '2-digit', year: '2-digit' })
      + ' ' + d.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' });
  }

  const usuarioParaModal = modalUsuario === 'novo' ? null : modalUsuario;
  const mostrarModal = modalUsuario !== null;

  return (
    <div className="space-y-5">
      {/* Titulo */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-lg font-bold text-gray-900">Gerenciamento de Usuarios</h1>
          <p className="text-xs text-gray-500 mt-0.5">{usuarios.length} usuarios cadastrados</p>
        </div>
        <button
          type="button"
          onClick={() => setModalUsuario('novo')}
          className="flex items-center gap-2 px-4 py-2 text-xs font-semibold text-white rounded-lg transition-colors"
          style={{ backgroundColor: '#00B050' }}
        >
          <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
          </svg>
          Novo Usuario
        </button>
      </div>

      {/* Tabela */}
      <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
        {loading ? (
          <div className="flex items-center justify-center py-16">
            <div className="w-5 h-5 border-2 border-gray-300 border-t-green-600 rounded-full animate-spin" />
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full" role="table">
              <thead>
                <tr className="border-b border-gray-200 bg-gray-50">
                  <th scope="col" className="px-4 py-2.5 text-left text-[10px] font-semibold text-gray-500 uppercase tracking-wide">Nome</th>
                  <th scope="col" className="px-4 py-2.5 text-left text-[10px] font-semibold text-gray-500 uppercase tracking-wide">Email</th>
                  <th scope="col" className="px-4 py-2.5 text-left text-[10px] font-semibold text-gray-500 uppercase tracking-wide">Role</th>
                  <th scope="col" className="px-4 py-2.5 text-left text-[10px] font-semibold text-gray-500 uppercase tracking-wide">Consultor</th>
                  <th scope="col" className="px-4 py-2.5 text-left text-[10px] font-semibold text-gray-500 uppercase tracking-wide">Status</th>
                  <th scope="col" className="px-4 py-2.5 text-left text-[10px] font-semibold text-gray-500 uppercase tracking-wide">Ultimo Login</th>
                  <th scope="col" className="px-4 py-2.5 text-left text-[10px] font-semibold text-gray-500 uppercase tracking-wide">Acoes</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {usuarios.length === 0 ? (
                  <tr>
                    <td colSpan={7} className="px-4 py-10 text-center text-xs text-gray-400">
                      Nenhum usuario cadastrado.
                    </td>
                  </tr>
                ) : (
                  usuarios.map(u => (
                    <tr
                      key={u.id}
                      className="hover:bg-gray-50 transition-colors"
                      style={{ opacity: u.ativo ? 1 : 0.6 }}
                    >
                      <td className="px-4 py-3">
                        <div className="flex items-center gap-2">
                          <div
                            className="w-6 h-6 rounded-full flex items-center justify-center text-white text-[10px] font-bold flex-shrink-0"
                            style={{ backgroundColor: '#00B050' }}
                          >
                            {u.nome.charAt(0).toUpperCase()}
                          </div>
                          <span className="text-xs font-medium text-gray-900">{u.nome}</span>
                        </div>
                      </td>
                      <td className="px-4 py-3 text-xs text-gray-600 font-mono">{u.email}</td>
                      <td className="px-4 py-3">
                        <RoleBadgeAdmin role={u.role} />
                      </td>
                      <td className="px-4 py-3 text-xs text-gray-600">
                        {u.consultor_vinculado ?? <span className="text-gray-300">—</span>}
                      </td>
                      <td className="px-4 py-3">
                        <AtivoToggle ativo={u.ativo} onChange={() => handleToggleAtivo(u)} />
                      </td>
                      <td className="px-4 py-3 text-xs text-gray-500">{formatUltimoLogin(u.ultimo_login)}</td>
                      <td className="px-4 py-3">
                        <button
                          type="button"
                          onClick={() => setModalUsuario(u)}
                          className="text-xs font-medium text-gray-600 hover:text-gray-900 underline focus:outline-none"
                        >
                          Editar
                        </button>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
            <div className="px-4 py-3 border-t border-gray-100 text-xs text-gray-500">
              {usuarios.length} usuarios cadastrados — {usuarios.filter(u => u.ativo).length} ativos
            </div>
          </div>
        )}
      </div>

      {/* Modal */}
      {mostrarModal && (
        <ModalUsuario
          usuario={usuarioParaModal}
          onClose={() => setModalUsuario(null)}
          onSalvar={handleSalvar}
        />
      )}
    </div>
  );
}
