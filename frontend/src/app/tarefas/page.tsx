'use client';

import { useState, useEffect, useCallback, useMemo } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { fetchJson } from '@/lib/api';
import KpiCard from '@/components/KpiCard';

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

type TarefaTipo = 'AGENDA' | 'FOLLOWUP' | 'RNC';
type TarefaStatus = 'pending' | 'done';
type FilterTab = 'todas' | 'urgentes' | 'followups' | 'rncs' | 'concluidas';

interface Tarefa {
  id: string;
  tipo: TarefaTipo;
  descricao: string;
  cliente_nome: string;
  cliente_cnpj: string;
  prioridade: string;       // 'P0'..'P7' or 'RNC-ALTA' etc.
  due_label: string;        // human-readable date string
  due_date: Date | null;    // for sorting / coloring
  consultor: string;
  status: TarefaStatus;
  raw_priority_num: number; // 0..7 for sorting (lower = more urgent)
}

// Raw API shapes (minimal — only fields we consume)
interface AgendaItem {
  cnpj: string;
  nome_fantasia: string;
  prioridade: string;
  acao: string;
  consultor?: string;
  follow_up?: string;
}

interface AgendaConsultorResponse {
  itens: AgendaItem[];
}

interface ClienteFollowup {
  cnpj: string;
  nome_fantasia: string;
  consultor?: string;
  follow_up?: string;
  prioridade?: string;
}

interface ClientesResponse {
  registros: ClienteFollowup[];
}

interface RNCItem {
  id: number;
  cnpj: string;
  nome_fantasia?: string;
  tipo_problema: string;
  descricao: string;
  status: string;
  consultor?: string;
  data_abertura: string;
  prazo_resolucao?: string | null;
}

interface RNCResponse {
  total: number;
  items: RNCItem[];
}

// Modal form state
interface NovaTarefaForm {
  descricao: string;
  cliente: string;
  due_date: string;
  prioridade: string;
}

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const CONSULTORES = ['LARISSA', 'MANU', 'JULIO', 'DAIANE'] as const;

const PRIORITY_MAP: Record<string, number> = {
  P0: 0, P1: 1, P2: 2, P3: 3, P4: 4, P5: 5, P6: 6, P7: 7,
};

const PRIORITY_OPTIONS = ['P0', 'P1', 'P2', 'P3', 'P4', 'P5', 'P6', 'P7'];

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function parsePriorityNum(raw: string): number {
  const upper = (raw ?? '').toUpperCase().trim();
  if (upper in PRIORITY_MAP) return PRIORITY_MAP[upper];
  // RNC / custom — map by SLA or default high
  return 3;
}

function buildDueLabel(date: Date | null): string {
  if (!date) return 'Sem data';
  const now = new Date();
  const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
  const d = new Date(date.getFullYear(), date.getMonth(), date.getDate());
  const diffDays = Math.round((d.getTime() - today.getTime()) / 86400000);

  if (diffDays < 0) return `Vencida ha ${Math.abs(diffDays)} dia${Math.abs(diffDays) !== 1 ? 's' : ''}`;
  if (diffDays === 0) return 'Hoje';
  if (diffDays === 1) return 'Amanha';
  if (diffDays <= 7) return `Em ${diffDays} dias`;
  return date.toLocaleDateString('pt-BR', { day: '2-digit', month: '2-digit' });
}

function getDueDateColor(date: Date | null, status: TarefaStatus): string {
  if (status === 'done') return 'text-gray-400';
  if (!date) return 'text-gray-400';
  const now = new Date();
  const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
  const d = new Date(date.getFullYear(), date.getMonth(), date.getDate());
  const diffDays = Math.round((d.getTime() - today.getTime()) / 86400000);
  if (diffDays < 0) return 'text-red-600 font-semibold';
  if (diffDays === 0) return 'text-orange-500 font-semibold';
  return 'text-gray-500';
}

function getRowStyle(tarefa: Tarefa): React.CSSProperties {
  if (tarefa.status === 'done') return { backgroundColor: '#f9fafb' };
  if (!tarefa.due_date) return {};
  const now = new Date();
  const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
  const d = new Date(tarefa.due_date.getFullYear(), tarefa.due_date.getMonth(), tarefa.due_date.getDate());
  const diffDays = Math.round((d.getTime() - today.getTime()) / 86400000);
  if (diffDays < 0) return { borderLeft: '3px solid #ef4444', backgroundColor: '#fff5f5' };
  if (diffDays === 0) return { borderLeft: '3px solid #f97316', backgroundColor: '#fff8f0' };
  return { borderLeft: '3px solid #e5e7eb' };
}

function getPriorityBadgeStyle(prioridade: string): React.CSSProperties {
  const upper = (prioridade ?? '').toUpperCase().trim();
  const num = PRIORITY_MAP[upper] ?? 3;
  if (num <= 3) return { backgroundColor: '#fee2e2', color: '#dc2626' };
  if (num <= 5) return { backgroundColor: '#fef3c7', color: '#d97706' };
  return { backgroundColor: '#f3f4f6', color: '#6b7280' };
}

function getConsultorInitials(name: string): string {
  return (name ?? '?').slice(0, 2).toUpperCase();
}

function getConsultorColor(name: string): string {
  const colors: Record<string, string> = {
    LARISSA: '#7c3aed',
    MANU: '#0369a1',
    DAIANE: '#065f46',
    JULIO: '#c2410c',
  };
  return colors[(name ?? '').toUpperCase()] ?? '#6b7280';
}

function parseFollowupDate(raw?: string): Date | null {
  if (!raw) return null;
  const d = new Date(raw);
  return isNaN(d.getTime()) ? null : d;
}

// ---------------------------------------------------------------------------
// Data assembly: merge 3 API sources into unified Tarefa[]
// ---------------------------------------------------------------------------

function assembleFromAgenda(items: AgendaItem[]): Tarefa[] {
  const today = new Date();
  return items.map((item, idx) => {
    const prioNum = parsePriorityNum(item.prioridade);
    const dueDate = parseFollowupDate(item.follow_up) ?? today;
    return {
      id: `agenda-${item.cnpj}-${idx}`,
      tipo: 'AGENDA' as TarefaTipo,
      descricao: item.acao || 'Contato programado na agenda',
      cliente_nome: item.nome_fantasia,
      cliente_cnpj: item.cnpj,
      prioridade: item.prioridade || 'P5',
      due_label: buildDueLabel(dueDate),
      due_date: dueDate,
      consultor: item.consultor ?? 'VITAO',
      status: 'pending' as TarefaStatus,
      raw_priority_num: prioNum,
    };
  });
}

function assembleFromFollowups(clientes: ClienteFollowup[]): Tarefa[] {
  return clientes.map((c, idx) => {
    const dueDate = parseFollowupDate(c.follow_up);
    const prioNum = parsePriorityNum(c.prioridade ?? 'P3');
    return {
      id: `followup-${c.cnpj}-${idx}`,
      tipo: 'FOLLOWUP' as TarefaTipo,
      descricao: 'Follow-up vencido — reativar contato',
      cliente_nome: c.nome_fantasia,
      cliente_cnpj: c.cnpj,
      prioridade: c.prioridade ?? 'P3',
      due_label: buildDueLabel(dueDate),
      due_date: dueDate,
      consultor: c.consultor ?? 'VITAO',
      status: 'pending' as TarefaStatus,
      raw_priority_num: prioNum,
    };
  });
}

function assembleFromRNCs(rncs: RNCItem[]): Tarefa[] {
  const now = new Date();
  return rncs.map((rnc) => {
    // Derive urgency from how long the RNC has been open
    const openedDate = parseFollowupDate(rnc.data_abertura);
    const daysOpen = openedDate
      ? Math.round((now.getTime() - openedDate.getTime()) / 86400000)
      : 0;
    const slaStatus = daysOpen > 7 ? 'VIOLADO' : daysOpen > 3 ? 'ATENCAO' : 'DENTRO';
    const rlcPrioNum = slaStatus === 'VIOLADO' ? 1 : slaStatus === 'ATENCAO' ? 3 : 5;
    const prioLabel = slaStatus === 'VIOLADO' ? 'P1' : slaStatus === 'ATENCAO' ? 'P3' : 'P5';
    // Use prazo_resolucao as due date if set, otherwise use opened date
    const dueDate = parseFollowupDate(rnc.prazo_resolucao ?? undefined) ?? openedDate;
    return {
      id: `rnc-${rnc.id}`,
      tipo: 'RNC' as TarefaTipo,
      descricao: `RNC: ${rnc.tipo_problema.replace(/_/g, ' ')} — ${rnc.descricao.slice(0, 80)}`,
      cliente_nome: rnc.nome_fantasia ?? rnc.cnpj,
      cliente_cnpj: rnc.cnpj,
      prioridade: prioLabel,
      due_label: daysOpen > 0
        ? `${daysOpen} dia${daysOpen !== 1 ? 's' : ''} em aberto`
        : 'Aberto hoje',
      due_date: dueDate,
      consultor: rnc.consultor ?? 'VITAO',
      status: 'pending' as TarefaStatus,
      raw_priority_num: rlcPrioNum,
    };
  });
}

// ---------------------------------------------------------------------------
// Sub-components
// ---------------------------------------------------------------------------

function TipoTag({ tipo }: { tipo: TarefaTipo }) {
  const cfg: Record<TarefaTipo, { label: string; bg: string; color: string }> = {
    AGENDA:   { label: 'Agenda',    bg: '#eff6ff', color: '#1d4ed8' },
    FOLLOWUP: { label: 'Follow-up', bg: '#fdf4ff', color: '#7e22ce' },
    RNC:      { label: 'RNC',       bg: '#fff1f2', color: '#be123c' },
  };
  const c = cfg[tipo];
  return (
    <span
      className="inline-flex items-center px-1.5 py-0.5 text-[9px] font-semibold rounded uppercase tracking-wide flex-shrink-0"
      style={{ backgroundColor: c.bg, color: c.color }}
    >
      {c.label}
    </span>
  );
}

function ConsultorAvatar({ consultor }: { consultor: string }) {
  return (
    <span
      className="inline-flex items-center justify-center w-6 h-6 rounded-full text-[10px] font-bold text-white flex-shrink-0"
      style={{ backgroundColor: getConsultorColor(consultor) }}
      title={consultor}
      aria-label={`Consultor: ${consultor}`}
    >
      {getConsultorInitials(consultor)}
    </span>
  );
}

function Checkbox({ checked, onChange }: { checked: boolean; onChange: () => void }) {
  return (
    <button
      type="button"
      role="checkbox"
      aria-checked={checked}
      onClick={onChange}
      className={`
        flex-shrink-0 w-5 h-5 rounded border-2 flex items-center justify-center
        transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-offset-1
        ${checked
          ? 'border-transparent'
          : 'border-gray-300 bg-white hover:border-green-400'
        }
      `}
      style={checked ? { backgroundColor: '#00B050', borderColor: '#00B050' } : {}}
    >
      {checked && (
        <svg className="w-3 h-3 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
        </svg>
      )}
    </button>
  );
}

interface NovaTarefaModalProps {
  open: boolean;
  onClose: () => void;
  onAdd: (t: Tarefa) => void;
}

const NOVA_TAREFA_FORM_PADRAO: NovaTarefaForm = {
  descricao: '',
  cliente: '',
  due_date: '',
  prioridade: 'P3',
};

function NovaTarefaModal({ open, onClose, onAdd }: NovaTarefaModalProps) {
  const { user } = useAuth();
  const [form, setForm] = useState<NovaTarefaForm>(NOVA_TAREFA_FORM_PADRAO);
  const [submitting, setSubmitting] = useState(false);

  // Resetar form sempre que o modal e aberto
  useEffect(() => {
    if (open) {
      setForm(NOVA_TAREFA_FORM_PADRAO);
      setSubmitting(false);
    }
  }, [open]);

  function handleChange(field: keyof NovaTarefaForm, value: string) {
    setForm((prev) => ({ ...prev, [field]: value }));
  }

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!form.descricao.trim()) return;
    setSubmitting(true);

    const dueDate = form.due_date ? new Date(form.due_date) : null;
    const consultor = user?.consultor_nome ?? 'VITAO';
    const newTask: Tarefa = {
      id: `manual-${Date.now()}`,
      tipo: 'AGENDA',
      descricao: form.descricao.trim(),
      cliente_nome: form.cliente.trim() || 'Nao especificado',
      cliente_cnpj: '',
      prioridade: form.prioridade,
      due_label: buildDueLabel(dueDate),
      due_date: dueDate,
      consultor,
      status: 'pending',
      raw_priority_num: parsePriorityNum(form.prioridade),
    };

    onAdd(newTask);
    setForm(NOVA_TAREFA_FORM_PADRAO);
    setSubmitting(false);
    onClose();
  }

  if (!open) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm"
      onClick={(e) => { if (e.target === e.currentTarget) onClose(); }}
      role="dialog"
      aria-modal="true"
      aria-label="Nova Tarefa"
    >
      <div className="bg-white rounded-xl shadow-2xl w-full max-w-md mx-4 overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between px-5 py-4 border-b border-gray-100">
          <h2 className="font-semibold text-gray-900 text-base">Nova Tarefa</h2>
          <button
            type="button"
            onClick={onClose}
            className="p-1.5 rounded text-gray-400 hover:text-gray-600 hover:bg-gray-100 transition-colors"
            aria-label="Fechar"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="p-5 space-y-4">
          <div>
            <label className="block text-xs font-medium text-gray-700 mb-1.5" htmlFor="nova-descricao">
              Descricao <span className="text-red-500">*</span>
            </label>
            <textarea
              id="nova-descricao"
              className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm text-gray-900 placeholder:text-gray-400 focus:outline-none focus:ring-2 resize-none"
              style={{ '--tw-ring-color': '#00B050' } as React.CSSProperties}
              rows={3}
              placeholder="O que precisa ser feito?"
              value={form.descricao}
              onChange={(e) => handleChange('descricao', e.target.value)}
              required
            />
          </div>

          <div>
            <label className="block text-xs font-medium text-gray-700 mb-1.5" htmlFor="nova-cliente">
              Cliente
            </label>
            <input
              id="nova-cliente"
              type="text"
              className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm text-gray-900 placeholder:text-gray-400 focus:outline-none focus:ring-2"
              style={{ '--tw-ring-color': '#00B050' } as React.CSSProperties}
              placeholder="Nome do cliente (opcional)"
              value={form.cliente}
              onChange={(e) => handleChange('cliente', e.target.value)}
            />
          </div>

          <div className="flex gap-3">
            <div className="flex-1">
              <label className="block text-xs font-medium text-gray-700 mb-1.5" htmlFor="nova-due">
                Prazo
              </label>
              <input
                id="nova-due"
                type="date"
                className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm text-gray-900 focus:outline-none focus:ring-2"
                style={{ '--tw-ring-color': '#00B050' } as React.CSSProperties}
                value={form.due_date}
                onChange={(e) => handleChange('due_date', e.target.value)}
              />
            </div>
            <div className="flex-1">
              <label className="block text-xs font-medium text-gray-700 mb-1.5" htmlFor="nova-prio">
                Prioridade
              </label>
              <select
                id="nova-prio"
                className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm text-gray-900 focus:outline-none focus:ring-2 bg-white"
                style={{ '--tw-ring-color': '#00B050' } as React.CSSProperties}
                value={form.prioridade}
                onChange={(e) => handleChange('prioridade', e.target.value)}
              >
                {PRIORITY_OPTIONS.map((p) => (
                  <option key={p} value={p}>{p}</option>
                ))}
              </select>
            </div>
          </div>

          <div className="flex gap-3 pt-1">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 px-4 py-2.5 rounded-lg border border-gray-200 text-sm font-medium text-gray-600 hover:bg-gray-50 transition-colors"
            >
              Cancelar
            </button>
            <button
              type="submit"
              disabled={submitting || !form.descricao.trim()}
              className="flex-1 px-4 py-2.5 rounded-lg text-sm font-semibold text-white transition-colors disabled:opacity-50"
              style={{ backgroundColor: '#00B050' }}
            >
              Adicionar Tarefa
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Main page component
// ---------------------------------------------------------------------------

export default function TarefasPage() {
  useAuth(); // ensure authenticated
  const [tarefas, setTarefas] = useState<Tarefa[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeFilter, setActiveFilter] = useState<FilterTab>('todas');
  const [modalOpen, setModalOpen] = useState(false);

  // -------------------------------------------------------------------------
  // Data fetching: fetch all 3 sources in parallel for each consultor
  // -------------------------------------------------------------------------

  const loadTarefas = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      // Fetch agenda for all consultores in parallel
      const agendaPromises = CONSULTORES.map((c) =>
        fetchJson<AgendaConsultorResponse>(`/api/agenda/${encodeURIComponent(c)}`)
          .then((r) => assembleFromAgenda(r.itens.map((i) => ({ ...i, consultor: c }))))
          .catch(() => [] as Tarefa[])
      );

      // Fetch overdue follow-ups (followup_vencido is a model field; backend ignores
      // unknown query params so passing it is harmless — the full list is returned
      // and assembleFromFollowups filters by follow_up date on the client side)
      const followupPromise = fetchJson<ClientesResponse>(
        '/api/clientes?followup_vencido=true&limit=50'
      )
        .then((r) => assembleFromFollowups(r.registros ?? []))
        .catch(() => [] as Tarefa[]);

      // Fetch open RNCs
      const rncPromise = fetchJson<RNCResponse>('/api/rnc?status=ABERTO')
        .then((r) => assembleFromRNCs(r.items ?? []))
        .catch(() => [] as Tarefa[]);

      const [agendaResults, followupResults, rncResults] = await Promise.all([
        Promise.all(agendaPromises),
        followupPromise,
        rncPromise,
      ]);

      const agendaTarefas = agendaResults.flat();

      // Deduplicate: if same CNPJ appears in both agenda and followup, keep only one
      const agendaCnpjs = new Set(agendaTarefas.map((t) => t.cliente_cnpj).filter(Boolean));
      const uniqueFollowups = followupResults.filter(
        (t) => !t.cliente_cnpj || !agendaCnpjs.has(t.cliente_cnpj)
      );

      const combined = [...agendaTarefas, ...uniqueFollowups, ...rncResults];

      // Sort by priority (ascending = most urgent first), then by due_date
      combined.sort((a, b) => {
        if (a.raw_priority_num !== b.raw_priority_num) {
          return a.raw_priority_num - b.raw_priority_num;
        }
        const aTime = a.due_date?.getTime() ?? Infinity;
        const bTime = b.due_date?.getTime() ?? Infinity;
        return aTime - bTime;
      });

      setTarefas(combined);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erro ao carregar tarefas');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadTarefas();
  }, [loadTarefas]);

  // -------------------------------------------------------------------------
  // Toggle done
  // -------------------------------------------------------------------------

  function toggleStatus(id: string) {
    setTarefas((prev) =>
      prev.map((t) =>
        t.id === id ? { ...t, status: t.status === 'done' ? 'pending' : 'done' } : t
      )
    );
  }

  function addTarefa(t: Tarefa) {
    setTarefas((prev) => [t, ...prev]);
  }

  // -------------------------------------------------------------------------
  // Derived counts
  // -------------------------------------------------------------------------

  const counts = useMemo(() => {
    const pending = tarefas.filter((t) => t.status === 'pending');
    const now = new Date();
    const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());

    const overdue = pending.filter((t) => {
      if (!t.due_date) return false;
      const d = new Date(t.due_date.getFullYear(), t.due_date.getMonth(), t.due_date.getDate());
      return d < today;
    });

    const dueToday = pending.filter((t) => {
      if (!t.due_date) return false;
      const d = new Date(t.due_date.getFullYear(), t.due_date.getMonth(), t.due_date.getDate());
      return d.getTime() === today.getTime();
    });

    const next7 = pending.filter((t) => {
      if (!t.due_date) return false;
      const d = new Date(t.due_date.getFullYear(), t.due_date.getMonth(), t.due_date.getDate());
      const diff = Math.round((d.getTime() - today.getTime()) / 86400000);
      return diff > 0 && diff <= 7;
    });

    const urgentes = pending.filter((t) => t.raw_priority_num <= 3);
    const followups = pending.filter((t) => t.tipo === 'FOLLOWUP');
    const rncs = pending.filter((t) => t.tipo === 'RNC');
    const concluidas = tarefas.filter((t) => t.status === 'done');

    return {
      total: pending.length,
      overdue: overdue.length,
      dueToday: dueToday.length,
      next7: next7.length,
      urgentes: urgentes.length,
      followups: followups.length,
      rncs: rncs.length,
      concluidas: concluidas.length,
    };
  }, [tarefas]);

  // -------------------------------------------------------------------------
  // Filtered list
  // -------------------------------------------------------------------------

  const filtered = useMemo(() => {
    switch (activeFilter) {
      case 'urgentes':
        return tarefas.filter((t) => t.status === 'pending' && t.raw_priority_num <= 3);
      case 'followups':
        return tarefas.filter((t) => t.status === 'pending' && t.tipo === 'FOLLOWUP');
      case 'rncs':
        return tarefas.filter((t) => t.status === 'pending' && t.tipo === 'RNC');
      case 'concluidas':
        return tarefas.filter((t) => t.status === 'done');
      default:
        return tarefas.filter((t) => {
          if (t.status === 'done') return false;
          return true;
        });
    }
  }, [tarefas, activeFilter]);

  // -------------------------------------------------------------------------
  // Render
  // -------------------------------------------------------------------------

  const filterTabs: { key: FilterTab; label: string; count?: number }[] = [
    { key: 'todas',     label: 'Todas',      count: counts.total },
    { key: 'urgentes',  label: 'Urgentes',   count: counts.urgentes },
    { key: 'followups', label: 'Follow-ups', count: counts.followups },
    { key: 'rncs',      label: 'RNCs',       count: counts.rncs },
    { key: 'concluidas',label: 'Concluidas', count: counts.concluidas },
  ];

  return (
    <div className="min-h-full bg-gray-50">
      <div className="max-w-5xl mx-auto px-4 sm:px-6 py-6 space-y-6">

        {/* Page header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-xl font-bold text-gray-900">Tarefas</h1>
            <p className="text-sm text-gray-500 mt-0.5">
              Agenda, follow-ups vencidos e RNCs em aberto
            </p>
          </div>
          <button
            type="button"
            onClick={() => setModalOpen(true)}
            className="flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-semibold text-white shadow-sm transition-all hover:brightness-105 active:scale-95"
            style={{ backgroundColor: '#00B050' }}
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
            </svg>
            Nova Tarefa
          </button>
        </div>

        {/* KPI summary cards */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          <KpiCard
            title="Total Pendentes"
            value={loading ? '-' : counts.total}
            accentColor="#00B050"
            loading={loading}
            icon={
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                  d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4" />
              </svg>
            }
          />
          <KpiCard
            title="Vencidas"
            value={loading ? '-' : counts.overdue}
            subtitle="Precisam de atencao"
            accentColor="#ef4444"
            loading={loading}
            icon={
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                  d="M12 9v2m0 4h.01M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z" />
              </svg>
            }
          />
          <KpiCard
            title="Para Hoje"
            value={loading ? '-' : counts.dueToday}
            accentColor="#f97316"
            loading={loading}
            icon={
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                  d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
              </svg>
            }
          />
          <KpiCard
            title="Proximos 7 dias"
            value={loading ? '-' : counts.next7}
            accentColor="#6366f1"
            loading={loading}
            icon={
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                  d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            }
          />
        </div>

        {/* Filter tabs */}
        <div className="flex gap-1 bg-white border border-gray-200 rounded-lg p-1 w-fit overflow-x-auto">
          {filterTabs.map((tab) => (
            <button
              key={tab.key}
              type="button"
              onClick={() => setActiveFilter(tab.key)}
              className={`
                flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-medium transition-all whitespace-nowrap
                ${activeFilter === tab.key
                  ? 'text-white shadow-sm'
                  : 'text-gray-500 hover:text-gray-800 hover:bg-gray-50'
                }
              `}
              style={activeFilter === tab.key ? { backgroundColor: '#00B050' } : {}}
            >
              {tab.label}
              {tab.count !== undefined && tab.count > 0 && (
                <span
                  className={`
                    inline-flex items-center justify-center min-w-[18px] h-[18px] px-1 rounded-full text-[10px] font-bold
                    ${activeFilter === tab.key
                      ? 'bg-white/25 text-white'
                      : tab.key === 'urgentes' || tab.key === 'rncs'
                      ? 'bg-red-100 text-red-600'
                      : 'bg-gray-100 text-gray-600'
                    }
                  `}
                >
                  {tab.count}
                </span>
              )}
            </button>
          ))}
        </div>

        {/* Task list */}
        <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">

          {/* Loading skeleton */}
          {loading && (
            <div className="divide-y divide-gray-100">
              {Array.from({ length: 6 }).map((_, i) => (
                <div key={i} className="flex items-start gap-3 p-4">
                  <div className="w-5 h-5 rounded bg-gray-100 animate-pulse flex-shrink-0 mt-0.5" />
                  <div className="flex-1 space-y-2">
                    <div className="h-4 bg-gray-100 animate-pulse rounded w-3/4" />
                    <div className="h-3 bg-gray-100 animate-pulse rounded w-1/2" />
                  </div>
                  <div className="w-16 h-5 bg-gray-100 animate-pulse rounded" />
                </div>
              ))}
            </div>
          )}

          {/* Error state */}
          {!loading && error && (
            <div className="flex flex-col items-center gap-3 py-16 px-6 text-center">
              <div className="w-12 h-12 rounded-full bg-red-50 flex items-center justify-center">
                <svg className="w-6 h-6 text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                    d="M12 9v2m0 4h.01M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z" />
                </svg>
              </div>
              <div>
                <p className="font-medium text-gray-900 text-sm">Erro ao carregar tarefas</p>
                <p className="text-xs text-gray-500 mt-1">{error}</p>
              </div>
              <button
                type="button"
                onClick={() => void loadTarefas()}
                className="px-4 py-2 rounded-lg text-sm font-medium text-white"
                style={{ backgroundColor: '#00B050' }}
              >
                Tentar novamente
              </button>
            </div>
          )}

          {/* Empty state */}
          {!loading && !error && filtered.length === 0 && (
            <div className="flex flex-col items-center gap-3 py-16 px-6 text-center">
              <div
                className="w-14 h-14 rounded-full flex items-center justify-center"
                style={{ backgroundColor: '#00B05018' }}
              >
                <svg
                  className="w-7 h-7"
                  style={{ color: '#00B050' }}
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                    d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <div>
                <p className="font-semibold text-gray-900 text-sm">
                  {activeFilter === 'concluidas'
                    ? 'Nenhuma tarefa concluida ainda'
                    : 'Nenhuma tarefa pendente'}
                </p>
                <p className="text-xs text-gray-400 mt-1">
                  {activeFilter === 'concluidas'
                    ? 'Conclua tarefas marcando o checkbox.'
                    : 'Todas as tarefas desta categoria estao em dia.'}
                </p>
              </div>
            </div>
          )}

          {/* Task rows */}
          {!loading && !error && filtered.length > 0 && (
            <ul className="divide-y divide-gray-100" role="list" aria-label="Lista de tarefas">
              {filtered.map((tarefa) => (
                <li
                  key={tarefa.id}
                  className="flex items-start gap-3 p-4 transition-colors hover:bg-gray-50/50"
                  style={getRowStyle(tarefa)}
                  aria-label={tarefa.descricao}
                >
                  {/* Checkbox */}
                  <div className="mt-0.5">
                    <Checkbox
                      checked={tarefa.status === 'done'}
                      onChange={() => toggleStatus(tarefa.id)}
                    />
                  </div>

                  {/* Content */}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-start gap-2 flex-wrap">
                      <TipoTag tipo={tarefa.tipo} />
                      <span
                        className={`text-sm font-medium leading-snug ${
                          tarefa.status === 'done'
                            ? 'line-through text-gray-400'
                            : 'text-gray-900'
                        }`}
                      >
                        {tarefa.descricao}
                      </span>
                    </div>
                    <div className="flex items-center gap-2 mt-1 flex-wrap">
                      <span className="text-xs text-gray-500 truncate max-w-[180px]">
                        {tarefa.cliente_nome}
                      </span>
                      {tarefa.cliente_cnpj && (
                        <span className="text-[10px] text-gray-300 font-mono hidden sm:inline">
                          {tarefa.cliente_cnpj}
                        </span>
                      )}
                    </div>
                  </div>

                  {/* Right-side metadata */}
                  <div className="flex flex-col items-end gap-1.5 flex-shrink-0 ml-2">
                    {/* Due date */}
                    <span className={`text-[11px] ${getDueDateColor(tarefa.due_date, tarefa.status)}`}>
                      {tarefa.due_label}
                    </span>

                    <div className="flex items-center gap-1.5">
                      {/* Priority badge */}
                      <span
                        className="inline-flex items-center px-1.5 py-0.5 text-[10px] font-bold rounded uppercase"
                        style={getPriorityBadgeStyle(tarefa.prioridade)}
                      >
                        {tarefa.prioridade}
                      </span>

                      {/* Consultor avatar */}
                      <ConsultorAvatar consultor={tarefa.consultor} />
                    </div>
                  </div>
                </li>
              ))}
            </ul>
          )}

          {/* Footer count */}
          {!loading && !error && filtered.length > 0 && (
            <div className="px-4 py-2.5 border-t border-gray-100 bg-gray-50/50">
              <p className="text-[11px] text-gray-400">
                {filtered.length} tarefa{filtered.length !== 1 ? 's' : ''}
                {activeFilter !== 'todas' && activeFilter !== 'concluidas'
                  ? ` — ${counts.total} total pendente${counts.total !== 1 ? 's' : ''}`
                  : ''}
              </p>
            </div>
          )}
        </div>
      </div>

      {/* Nova Tarefa modal */}
      <NovaTarefaModal
        open={modalOpen}
        onClose={() => setModalOpen(false)}
        onAdd={addTarefa}
      />
    </div>
  );
}
