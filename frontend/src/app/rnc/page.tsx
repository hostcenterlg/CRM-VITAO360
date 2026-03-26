'use client';

import { useState, useEffect, useCallback } from 'react';
import { fetchJson } from '@/lib/api-internal';

// ---------------------------------------------------------------------------
// Tipos
// ---------------------------------------------------------------------------

type StatusRNC = 'ABERTO' | 'EM_ANDAMENTO' | 'RESOLVIDO' | 'ENCERRADO';

interface RNCItem {
  id: number;
  data_abertura: string;
  cliente_nome: string;
  cliente_cnpj: string;
  tipo_problema: string;
  area_responsavel: string;
  status: StatusRNC;
  dias_aberto: number;
  sla_status: 'DENTRO' | 'ATENCAO' | 'VIOLADO';
  descricao: string;
  consultor?: string;
}

interface RNCResumo {
  total: number;
  resolvido: number;
  resolvido_pct: number;
  em_andamento: number;
  em_andamento_pct: number;
  pendente: number;
  pendente_pct: number;
}

interface RNCResponse {
  resumo: RNCResumo;
  itens: RNCItem[];
}

interface NovaRNCForm {
  cliente_cnpj: string;
  cliente_nome: string;
  tipo_problema: string;
  descricao: string;
}

// ---------------------------------------------------------------------------
// Constantes
// ---------------------------------------------------------------------------

const TIPOS_PROBLEMA = [
  { value: 'ATRASO_ENTREGA', label: 'Atraso na Entrega', area: 'Expedicao' },
  { value: 'PRODUTO_AVARIADO', label: 'Produto Avariado', area: 'Qualidade' },
  { value: 'ERRO_SEPARACAO', label: 'Erro de Separacao', area: 'Expedicao' },
  { value: 'ERRO_NOTA_FISCAL', label: 'Erro na Nota Fiscal', area: 'Faturamento' },
  { value: 'DIVERGENCIA_PRECO', label: 'Divergencia de Preco', area: 'Faturamento' },
  { value: 'COBRANCA_INDEVIDA', label: 'Cobranca Indevida', area: 'Financeiro' },
  { value: 'RUPTURA_ESTOQUE', label: 'Ruptura de Estoque', area: 'Fabrica/PCP' },
  { value: 'PROBLEMA_SISTEMA', label: 'Problema de Sistema', area: 'TI' },
] as const;

const STATUS_CONFIG: Record<StatusRNC, { label: string; bg: string; text: string }> = {
  ABERTO:       { label: 'ABERTO',        bg: '#FF0000', text: '#fff' },
  EM_ANDAMENTO: { label: 'EM ANDAMENTO',  bg: '#FFC000', text: '#1a1a1a' },
  RESOLVIDO:    { label: 'RESOLVIDO',     bg: '#00B050', text: '#fff' },
  ENCERRADO:    { label: 'ENCERRADO',     bg: '#6B7280', text: '#fff' },
};

const SLA_CONFIG = {
  DENTRO:  { label: 'DENTRO',   bg: '#00B050', text: '#fff' },
  ATENCAO: { label: 'ATENCAO',  bg: '#FFC000', text: '#1a1a1a' },
  VIOLADO: { label: 'VIOLADO',  bg: '#FF0000', text: '#fff' },
};

// ---------------------------------------------------------------------------
// Dados mock para quando a API ainda nao esta pronta
// ---------------------------------------------------------------------------

function getMockData(): RNCResponse {
  return {
    resumo: {
      total: 135,
      resolvido: 84,
      resolvido_pct: 62,
      em_andamento: 31,
      em_andamento_pct: 23,
      pendente: 20,
      pendente_pct: 15,
    },
    itens: [
      {
        id: 1, data_abertura: '2026-03-25', cliente_nome: 'Distribuidora Ligeiro',
        cliente_cnpj: '04067573000193', tipo_problema: 'ATRASO_ENTREGA',
        area_responsavel: 'Expedicao', status: 'ABERTO', dias_aberto: 0,
        sla_status: 'DENTRO', descricao: 'Pedido #12.456 nao chegou na data prevista.',
        consultor: 'LARISSA',
      },
      {
        id: 2, data_abertura: '2026-03-20', cliente_nome: 'Natural Shop',
        cliente_cnpj: '12345678000100', tipo_problema: 'ERRO_NOTA_FISCAL',
        area_responsavel: 'Faturamento', status: 'EM_ANDAMENTO', dias_aberto: 5,
        sla_status: 'ATENCAO', descricao: 'Nota fiscal com CNPJ incorreto.',
        consultor: 'LARISSA',
      },
      {
        id: 3, data_abertura: '2026-03-15', cliente_nome: 'BioBom Ltda',
        cliente_cnpj: '98765432000100', tipo_problema: 'PRODUTO_AVARIADO',
        area_responsavel: 'Qualidade', status: 'RESOLVIDO', dias_aberto: 8,
        sla_status: 'DENTRO', descricao: 'Caixas de caldo natural chegaram amassadas.',
        consultor: 'MANU',
      },
      {
        id: 4, data_abertura: '2026-03-10', cliente_nome: 'Verde Vida',
        cliente_cnpj: '11122233000155', tipo_problema: 'COBRANCA_INDEVIDA',
        area_responsavel: 'Financeiro', status: 'ABERTO', dias_aberto: 15,
        sla_status: 'VIOLADO', descricao: 'Cobranca duplicada na fatura de marco.',
        consultor: 'DAIANE',
      },
      {
        id: 5, data_abertura: '2026-03-08', cliente_nome: 'Fitland SP 01',
        cliente_cnpj: '22233344000177', tipo_problema: 'RUPTURA_ESTOQUE',
        area_responsavel: 'Fabrica/PCP', status: 'EM_ANDAMENTO', dias_aberto: 17,
        sla_status: 'VIOLADO', descricao: 'Produto granola tradicional sem estoque ha 3 semanas.',
        consultor: 'JULIO',
      },
    ],
  };
}

// ---------------------------------------------------------------------------
// Componentes internos
// ---------------------------------------------------------------------------

function StatusBadgeRNC({ status }: { status: StatusRNC }) {
  const cfg = STATUS_CONFIG[status] ?? STATUS_CONFIG.ABERTO;
  return (
    <span
      className="inline-flex items-center px-2 py-0.5 text-[10px] font-semibold rounded uppercase"
      style={{ backgroundColor: cfg.bg, color: cfg.text }}
    >
      {cfg.label}
    </span>
  );
}

function SlaBadge({ sla, dias }: { sla: 'DENTRO' | 'ATENCAO' | 'VIOLADO'; dias: number }) {
  const cfg = SLA_CONFIG[sla];
  const pulse = sla === 'VIOLADO' && dias > 10;
  return (
    <span
      className={`inline-flex items-center px-2 py-0.5 text-[10px] font-semibold rounded uppercase ${pulse ? 'animate-pulse' : ''}`}
      style={{ backgroundColor: cfg.bg, color: cfg.text }}
    >
      {cfg.label}
    </span>
  );
}

interface ModalNovaRNCProps {
  onClose: () => void;
  onSalvar: (form: NovaRNCForm) => Promise<void>;
}

function ModalNovaRNC({ onClose, onSalvar }: ModalNovaRNCProps) {
  const [form, setForm] = useState<NovaRNCForm>({
    cliente_cnpj: '',
    cliente_nome: '',
    tipo_problema: '',
    descricao: '',
  });
  const [loading, setLoading] = useState(false);
  const [errors, setErrors] = useState<Partial<Record<keyof NovaRNCForm, string>>>({});

  const areaAuto = TIPOS_PROBLEMA.find(t => t.value === form.tipo_problema)?.area ?? '';

  function validate(): boolean {
    const e: Partial<Record<keyof NovaRNCForm, string>> = {};
    if (!form.cliente_cnpj.trim()) e.cliente_cnpj = 'CNPJ obrigatorio';
    if (!form.tipo_problema) e.tipo_problema = 'Selecione o tipo de problema';
    if (form.descricao.trim().length < 10) e.descricao = 'Minimo 10 caracteres';
    setErrors(e);
    return Object.keys(e).length === 0;
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!validate()) return;
    setLoading(true);
    try {
      await onSalvar(form);
      onClose();
    } catch {
      // erro tratado externamente
    } finally {
      setLoading(false);
    }
  }

  // Fechar com Esc
  useEffect(() => {
    function onKey(e: KeyboardEvent) { if (e.key === 'Escape') onClose(); }
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [onClose]);

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center"
      style={{ backgroundColor: 'rgba(0,0,0,0.5)' }}
      role="dialog"
      aria-modal="true"
      aria-labelledby="modal-rnc-titulo"
    >
      <div className="bg-white rounded-lg shadow-xl w-full max-w-lg mx-4">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200">
          <h2 id="modal-rnc-titulo" className="text-sm font-bold text-gray-900 uppercase tracking-wide">
            Nova RNC
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
          {/* CNPJ */}
          <div>
            <label className="block text-xs font-semibold text-gray-700 mb-1 uppercase tracking-wide">
              CNPJ do Cliente *
            </label>
            <input
              type="text"
              value={form.cliente_cnpj}
              onChange={e => setForm(f => ({ ...f, cliente_cnpj: e.target.value }))}
              placeholder="00.000.000/0001-00"
              className={`w-full h-9 px-3 text-xs border rounded focus:outline-none focus:ring-2 focus:ring-green-500 font-mono ${errors.cliente_cnpj ? 'border-red-500' : 'border-gray-300'}`}
            />
            {errors.cliente_cnpj && (
              <p className="mt-1 text-[10px] text-red-600">{errors.cliente_cnpj}</p>
            )}
          </div>

          {/* Nome cliente */}
          <div>
            <label className="block text-xs font-semibold text-gray-700 mb-1 uppercase tracking-wide">
              Nome do Cliente
            </label>
            <input
              type="text"
              value={form.cliente_nome}
              onChange={e => setForm(f => ({ ...f, cliente_nome: e.target.value }))}
              placeholder="Nome fantasia"
              className="w-full h-9 px-3 text-xs border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-green-500"
            />
          </div>

          {/* Tipo Problema */}
          <div>
            <label className="block text-xs font-semibold text-gray-700 mb-1 uppercase tracking-wide">
              Tipo de Problema *
            </label>
            <select
              value={form.tipo_problema}
              onChange={e => setForm(f => ({ ...f, tipo_problema: e.target.value }))}
              className={`w-full h-9 px-3 text-xs border rounded focus:outline-none focus:ring-2 focus:ring-green-500 bg-white ${errors.tipo_problema ? 'border-red-500' : 'border-gray-300'}`}
            >
              <option value="">Selecione o tipo de problema...</option>
              {TIPOS_PROBLEMA.map(t => (
                <option key={t.value} value={t.value}>{t.label}</option>
              ))}
            </select>
            {errors.tipo_problema && (
              <p className="mt-1 text-[10px] text-red-600">{errors.tipo_problema}</p>
            )}
            {areaAuto && (
              <p className="mt-1 text-[10px] text-gray-500">
                Area responsavel: <strong>{areaAuto}</strong> (preenchido automaticamente)
              </p>
            )}
          </div>

          {/* Descricao */}
          <div>
            <label className="block text-xs font-semibold text-gray-700 mb-1 uppercase tracking-wide">
              Descricao *
            </label>
            <textarea
              value={form.descricao}
              onChange={e => setForm(f => ({ ...f, descricao: e.target.value }))}
              placeholder="Descreva o problema em detalhes..."
              rows={3}
              className={`w-full px-3 py-2 text-xs border rounded resize-none focus:outline-none focus:ring-2 focus:ring-green-500 ${errors.descricao ? 'border-red-500' : 'border-gray-300'}`}
            />
            {errors.descricao && (
              <p className="mt-1 text-[10px] text-red-600">{errors.descricao}</p>
            )}
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
              {loading ? 'Salvando...' : 'Abrir RNC'}
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

export default function RNCPage() {
  const [data, setData] = useState<RNCResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [filtroStatus, setFiltroStatus] = useState('');
  const [filtroTipo, setFiltroTipo] = useState('');
  const [filtroConsultor, setFiltroConsultor] = useState('');
  const [modalAberto, setModalAberto] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const qs = new URLSearchParams();
      if (filtroStatus) qs.set('status', filtroStatus);
      if (filtroTipo) qs.set('tipo', filtroTipo);
      if (filtroConsultor) qs.set('consultor', filtroConsultor);
      const res = await fetchJson<RNCResponse>(`/api/rnc?${qs.toString()}`);
      setData(res);
    } catch {
      // API indisponivel — usar dados mock
      setData(getMockData());
    } finally {
      setLoading(false);
    }
  }, [filtroStatus, filtroTipo, filtroConsultor]);

  useEffect(() => { void load(); }, [load]);

  const itens = data?.itens ?? [];
  const resumo = data?.resumo;

  const itensFiltrados = itens.filter(item => {
    if (filtroStatus && item.status !== filtroStatus) return false;
    if (filtroTipo && item.tipo_problema !== filtroTipo) return false;
    if (filtroConsultor && item.consultor !== filtroConsultor) return false;
    return true;
  });

  async function handleSalvarRNC(form: NovaRNCForm) {
    await fetchJson('/api/rnc', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(form),
    });
    await load();
  }

  const filtrosAtivos = [filtroStatus, filtroTipo, filtroConsultor].filter(Boolean).length;

  function formatarData(iso: string) {
    if (!iso) return '—';
    const d = new Date(iso + 'T00:00:00');
    return d.toLocaleDateString('pt-BR', { day: '2-digit', month: '2-digit' });
  }

  function labelTipo(v: string) {
    return TIPOS_PROBLEMA.find(t => t.value === v)?.label ?? v;
  }

  return (
    <div className="space-y-5">
      {/* Titulo */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-lg font-bold text-gray-900">Registro de Nao-Conformidade (RNC)</h1>
          <p className="text-xs text-gray-500 mt-0.5">Acompanhamento de ocorrencias e SLA</p>
        </div>
        <button
          type="button"
          onClick={() => setModalAberto(true)}
          className="flex items-center gap-2 px-4 py-2 text-xs font-semibold text-white rounded-lg transition-colors"
          style={{ backgroundColor: '#00B050' }}
        >
          <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
          </svg>
          Nova RNC
        </button>
      </div>

      {/* Cards resumo */}
      {resumo && (
        <div className="grid grid-cols-3 gap-4">
          <div className="bg-white rounded-lg border border-gray-200 p-4">
            <p className="text-[10px] font-semibold text-gray-500 uppercase tracking-wide mb-1">Resolvido</p>
            <p className="text-2xl font-bold" style={{ color: '#00B050' }}>{resumo.resolvido}</p>
            <p className="text-xs text-gray-500 mt-1">{resumo.resolvido_pct}% do total</p>
          </div>
          <div className="bg-white rounded-lg border border-gray-200 p-4">
            <p className="text-[10px] font-semibold text-gray-500 uppercase tracking-wide mb-1">Em Andamento</p>
            <p className="text-2xl font-bold" style={{ color: '#FFC000' }}>{resumo.em_andamento}</p>
            <p className="text-xs text-gray-500 mt-1">{resumo.em_andamento_pct}% do total</p>
          </div>
          <div className="bg-white rounded-lg border border-gray-200 p-4">
            <p className="text-[10px] font-semibold text-gray-500 uppercase tracking-wide mb-1">Pendente</p>
            <p className="text-2xl font-bold" style={{ color: '#FF0000' }}>{resumo.pendente}</p>
            <p className="text-xs text-gray-500 mt-1">{resumo.pendente_pct}% do total</p>
          </div>
        </div>
      )}

      {/* Filtros */}
      <div className="bg-white rounded-lg border border-gray-200 p-4">
        <div className="flex flex-wrap items-center gap-3">
          <select
            value={filtroStatus}
            onChange={e => setFiltroStatus(e.target.value)}
            aria-label="Filtrar por status"
            className={`h-8 px-3 text-xs border rounded focus:outline-none focus:ring-2 focus:ring-green-500 bg-white ${filtroStatus ? 'border-green-500 bg-green-50' : 'border-gray-300'}`}
          >
            <option value="">Todos os status</option>
            <option value="ABERTO">Aberto</option>
            <option value="EM_ANDAMENTO">Em Andamento</option>
            <option value="RESOLVIDO">Resolvido</option>
            <option value="ENCERRADO">Encerrado</option>
          </select>

          <select
            value={filtroTipo}
            onChange={e => setFiltroTipo(e.target.value)}
            aria-label="Filtrar por tipo de problema"
            className={`h-8 px-3 text-xs border rounded focus:outline-none focus:ring-2 focus:ring-green-500 bg-white ${filtroTipo ? 'border-green-500 bg-green-50' : 'border-gray-300'}`}
          >
            <option value="">Todos os tipos</option>
            {TIPOS_PROBLEMA.map(t => (
              <option key={t.value} value={t.value}>{t.label}</option>
            ))}
          </select>

          <select
            value={filtroConsultor}
            onChange={e => setFiltroConsultor(e.target.value)}
            aria-label="Filtrar por consultor"
            className={`h-8 px-3 text-xs border rounded focus:outline-none focus:ring-2 focus:ring-green-500 bg-white ${filtroConsultor ? 'border-green-500 bg-green-50' : 'border-gray-300'}`}
          >
            <option value="">Todos os consultores</option>
            <option value="MANU">MANU</option>
            <option value="LARISSA">LARISSA</option>
            <option value="DAIANE">DAIANE</option>
            <option value="JULIO">JULIO</option>
          </select>

          {filtrosAtivos > 0 && (
            <button
              type="button"
              onClick={() => { setFiltroStatus(''); setFiltroTipo(''); setFiltroConsultor(''); }}
              className="h-8 px-3 text-xs text-gray-500 hover:text-gray-900 transition-colors"
            >
              Limpar ({filtrosAtivos})
            </button>
          )}
        </div>
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
                  <th scope="col" className="px-4 py-2.5 text-left text-[10px] font-semibold text-gray-500 uppercase tracking-wide w-10">#</th>
                  <th scope="col" className="px-4 py-2.5 text-left text-[10px] font-semibold text-gray-500 uppercase tracking-wide">Data Abertura</th>
                  <th scope="col" className="px-4 py-2.5 text-left text-[10px] font-semibold text-gray-500 uppercase tracking-wide">Cliente</th>
                  <th scope="col" className="px-4 py-2.5 text-left text-[10px] font-semibold text-gray-500 uppercase tracking-wide">Tipo Problema</th>
                  <th scope="col" className="px-4 py-2.5 text-left text-[10px] font-semibold text-gray-500 uppercase tracking-wide">Area</th>
                  <th scope="col" className="px-4 py-2.5 text-left text-[10px] font-semibold text-gray-500 uppercase tracking-wide">Status</th>
                  <th scope="col" className="px-4 py-2.5 text-left text-[10px] font-semibold text-gray-500 uppercase tracking-wide">Dias</th>
                  <th scope="col" className="px-4 py-2.5 text-left text-[10px] font-semibold text-gray-500 uppercase tracking-wide">SLA</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {itensFiltrados.length === 0 ? (
                  <tr>
                    <td colSpan={8} className="px-4 py-10 text-center text-xs text-gray-400">
                      Nenhuma RNC encontrada com os filtros aplicados.
                    </td>
                  </tr>
                ) : (
                  itensFiltrados.map(item => {
                    const rowBg =
                      item.sla_status === 'VIOLADO'
                        ? '#FEF2F2'
                        : item.status === 'RESOLVIDO'
                        ? '#F0FDF4'
                        : '#FFFFFF';
                    return (
                      <tr
                        key={item.id}
                        className="hover:bg-gray-50 transition-colors"
                        style={{ backgroundColor: rowBg }}
                      >
                        <td className="px-4 py-2.5 text-xs text-gray-500">{item.id}</td>
                        <td className="px-4 py-2.5 text-xs text-gray-700">{formatarData(item.data_abertura)}</td>
                        <td className="px-4 py-2.5">
                          <span className="text-xs font-medium text-gray-900">{item.cliente_nome}</span>
                          <br />
                          <span className="text-[10px] text-gray-400 font-mono">{item.cliente_cnpj}</span>
                        </td>
                        <td className="px-4 py-2.5 text-xs text-gray-700">{labelTipo(item.tipo_problema)}</td>
                        <td className="px-4 py-2.5 text-xs text-gray-600">{item.area_responsavel}</td>
                        <td className="px-4 py-2.5">
                          <StatusBadgeRNC status={item.status} />
                        </td>
                        <td className="px-4 py-2.5 text-xs text-gray-700 tabular-nums">{item.dias_aberto}</td>
                        <td className="px-4 py-2.5">
                          <SlaBadge sla={item.sla_status} dias={item.dias_aberto} />
                        </td>
                      </tr>
                    );
                  })
                )}
              </tbody>
            </table>
            <div className="px-4 py-3 border-t border-gray-100 text-xs text-gray-500">
              Mostrando {itensFiltrados.length} de {itens.length} RNCs
            </div>
          </div>
        )}
      </div>

      {/* Nota SLA */}
      <p className="text-[10px] text-gray-400">
        SLA: Pendentes acima de 5 dias aparecem com fundo vermelho. Acima de 10 dias o badge pulsa.
      </p>

      {/* Modal */}
      {modalAberto && (
        <ModalNovaRNC
          onClose={() => setModalAberto(false)}
          onSalvar={handleSalvarRNC}
        />
      )}
    </div>
  );
}
