'use client';

import { useState, useCallback } from 'react';
import { downloadRelatorio } from '@/lib/api';

// ---------------------------------------------------------------------------
// Relatorios — hub de download de relatórios xlsx por tipo e filtros
// ---------------------------------------------------------------------------

// ---------------------------------------------------------------------------
// Toast simples
// ---------------------------------------------------------------------------

interface ToastMsg {
  id: number;
  tipo: 'sucesso' | 'erro';
  texto: string;
}

function ToastContainer({ toasts, onRemove }: { toasts: ToastMsg[]; onRemove: (id: number) => void }) {
  return (
    <div className="fixed bottom-4 right-4 z-50 flex flex-col gap-2 pointer-events-none">
      {toasts.map((t) => (
        <div
          key={t.id}
          role="status"
          aria-live="polite"
          className={`pointer-events-auto flex items-center gap-2 px-4 py-3 rounded-lg shadow-lg text-xs font-medium animate-fade-in ${
            t.tipo === 'sucesso'
              ? 'bg-green-50 border border-green-300 text-green-800'
              : 'bg-red-50 border border-red-300 text-red-800'
          }`}
        >
          {t.tipo === 'sucesso' ? (
            <svg className="w-4 h-4 text-green-600 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
            </svg>
          ) : (
            <svg className="w-4 h-4 text-red-600 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          )}
          <span className="flex-1">{t.texto}</span>
          <button
            type="button"
            onClick={() => onRemove(t.id)}
            className="ml-2 text-current opacity-60 hover:opacity-100 focus:outline-none"
            aria-label="Fechar notificacao"
          >
            <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
      ))}
    </div>
  );
}

function useToast() {
  const [toasts, setToasts] = useState<ToastMsg[]>([]);
  const nextId = useCallback(() => Date.now(), []);

  const addToast = useCallback((tipo: ToastMsg['tipo'], texto: string) => {
    const id = nextId();
    setToasts((prev) => [...prev, { id, tipo, texto }]);
    setTimeout(() => {
      setToasts((prev) => prev.filter((t) => t.id !== id));
    }, 4000);
  }, [nextId]);

  const removeToast = useCallback((id: number) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  }, []);

  return { toasts, addToast, removeToast };
}

const CONSULTORES = ['LARISSA', 'MANU', 'DAIANE', 'JULIO'];

const MESES = [
  { value: '1', label: 'Janeiro' },
  { value: '2', label: 'Fevereiro' },
  { value: '3', label: 'Marco' },
  { value: '4', label: 'Abril' },
  { value: '5', label: 'Maio' },
  { value: '6', label: 'Junho' },
  { value: '7', label: 'Julho' },
  { value: '8', label: 'Agosto' },
  { value: '9', label: 'Setembro' },
  { value: '10', label: 'Outubro' },
  { value: '11', label: 'Novembro' },
  { value: '12', label: 'Dezembro' },
];

const ANO_ATUAL = new Date().getFullYear();
const ANOS = [ANO_ATUAL, ANO_ATUAL - 1, ANO_ATUAL - 2].map(String);

// ---------------------------------------------------------------------------
// Tipos
// ---------------------------------------------------------------------------

interface FiltrosVendas {
  data_inicio: string;
  data_fim: string;
  consultor: string;
}

interface FiltrosMesAno {
  mes: string;
  ano: string;
  consultor: string;
}

interface FiltrosAtividades {
  data_inicio: string;
  data_fim: string;
  consultor: string;
}

interface FiltrosInativos {
  consultor: string;
}

interface FiltrosMetas {
  consultor: string;
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function hoje(): string {
  return new Date().toISOString().slice(0, 10);
}

function primeiroDiaMes(): string {
  const d = new Date();
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-01`;
}

async function triggerDownload(tipo: string, params: Record<string, string>): Promise<void> {
  // Remove params vazios
  const limpo = Object.fromEntries(
    Object.entries(params).filter(([, v]) => v !== '')
  );
  const blob = await downloadRelatorio(tipo, limpo);
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `relatorio_${tipo}_${new Date().toISOString().slice(0, 10)}.xlsx`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

// ---------------------------------------------------------------------------
// Sub-componentes de filtro
// ---------------------------------------------------------------------------

interface SelectFiltroProps {
  id: string;
  label: string;
  value: string;
  onChange: (v: string) => void;
  options: { value: string; label: string }[];
  placeholder?: string;
}

function SelectFiltro({ id, label, value, onChange, options, placeholder = 'Todos' }: SelectFiltroProps) {
  return (
    <div className="flex flex-col gap-1">
      <label htmlFor={id} className="text-[10px] font-semibold text-gray-500 uppercase tracking-wide">
        {label}
      </label>
      <select
        id={id}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className={`h-8 px-2.5 text-xs border rounded focus:outline-none focus:ring-2 focus:ring-green-200 focus:border-green-400 bg-white transition-colors ${
          value ? 'border-green-400 bg-green-50 text-green-800' : 'border-gray-200 text-gray-700'
        }`}
      >
        <option value="">{placeholder}</option>
        {options.map((o) => (
          <option key={o.value} value={o.value}>{o.label}</option>
        ))}
      </select>
    </div>
  );
}

interface DateFiltroProps {
  id: string;
  label: string;
  value: string;
  onChange: (v: string) => void;
}

function DateFiltro({ id, label, value, onChange }: DateFiltroProps) {
  return (
    <div className="flex flex-col gap-1">
      <label htmlFor={id} className="text-[10px] font-semibold text-gray-500 uppercase tracking-wide">
        {label}
      </label>
      <input
        id={id}
        type="date"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className={`h-8 px-2.5 text-xs border rounded focus:outline-none focus:ring-2 focus:ring-green-200 focus:border-green-400 bg-white transition-colors ${
          value ? 'border-green-400 bg-green-50' : 'border-gray-200'
        }`}
      />
    </div>
  );
}

// ---------------------------------------------------------------------------
// Botao de download
// ---------------------------------------------------------------------------

interface BotaoDownloadProps {
  loading: boolean;
  onClick: () => void;
}

function BotaoDownload({ loading, onClick }: BotaoDownloadProps) {
  return (
    <button
      type="button"
      onClick={onClick}
      disabled={loading}
      className="mt-3 w-full flex items-center justify-center gap-2 py-2 px-4 text-xs font-semibold text-white rounded-lg transition-colors disabled:opacity-60 disabled:cursor-not-allowed"
      style={{ backgroundColor: loading ? '#9CA3AF' : '#00B050' }}
    >
      {loading ? (
        <>
          <svg className="w-3.5 h-3.5 animate-spin" fill="none" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
          </svg>
          Gerando...
        </>
      ) : (
        <>
          <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
          </svg>
          Baixar Excel
        </>
      )}
    </button>
  );
}

// ---------------------------------------------------------------------------
// Card base de relatório
// ---------------------------------------------------------------------------

interface CardRelatorioProps {
  icon: React.ReactNode;
  titulo: string;
  descricao: string;
  children: React.ReactNode;
  loading: boolean;
  error: string | null;
  onDownload: () => void;
}

function CardRelatorio({ icon, titulo, descricao, children, loading, error, onDownload }: CardRelatorioProps) {
  return (
    <div className="bg-white rounded-lg border border-gray-200 shadow-sm p-4 flex flex-col">
      {/* Header */}
      <div className="flex items-start gap-3 mb-3">
        <div
          className="w-9 h-9 rounded-lg flex items-center justify-center flex-shrink-0"
          style={{ backgroundColor: '#00B05015' }}
        >
          <span style={{ color: '#00B050' }}>{icon}</span>
        </div>
        <div className="min-w-0">
          <h3 className="text-sm font-bold text-gray-900">{titulo}</h3>
          <p className="text-[11px] text-gray-500 mt-0.5 leading-snug">{descricao}</p>
        </div>
      </div>

      {/* Filtros */}
      <div className="flex flex-wrap gap-2 flex-1">
        {children}
      </div>

      {/* Erro */}
      {error && (
        <p role="alert" className="mt-2 text-[10px] text-red-600 bg-red-50 border border-red-200 rounded px-2 py-1">
          {error}
        </p>
      )}

      {/* Botao */}
      <BotaoDownload loading={loading} onClick={onDownload} />
    </div>
  );
}

// ---------------------------------------------------------------------------
// Ícones SVG inline (heroicons outline)
// ---------------------------------------------------------------------------

const IconVendas = (
  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
      d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
  </svg>
);

const IconPositivacao = (
  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
      d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0z" />
  </svg>
);

const IconAtividades = (
  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
      d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
  </svg>
);

const IconInativos = (
  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
      d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
  </svg>
);

const IconMetas = (
  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
      d="M9 12l2 2 4-4M7.835 4.697a3.42 3.42 0 001.946-.806 3.42 3.42 0 014.438 0 3.42 3.42 0 001.946.806 3.42 3.42 0 013.138 3.138 3.42 3.42 0 00.806 1.946 3.42 3.42 0 010 4.438 3.42 3.42 0 00-.806 1.946 3.42 3.42 0 01-3.138 3.138 3.42 3.42 0 00-1.946.806 3.42 3.42 0 01-4.438 0 3.42 3.42 0 00-1.946-.806 3.42 3.42 0 01-3.138-3.138 3.42 3.42 0 00-.806-1.946 3.42 3.42 0 010-4.438 3.42 3.42 0 00.806-1.946 3.42 3.42 0 013.138-3.138z" />
  </svg>
);

// ---------------------------------------------------------------------------
// Página principal
// ---------------------------------------------------------------------------

export default function RelatoriosPage() {
  // Estado de loading e erro por card
  const [loadingMap, setLoadingMap] = useState<Record<string, boolean>>({});
  const [errorMap, setErrorMap] = useState<Record<string, string | null>>({});

  const { toasts, addToast, removeToast } = useToast();

  // Filtros Vendas
  const [filtrosVendas, setFiltrosVendas] = useState<FiltrosVendas>({
    data_inicio: primeiroDiaMes(),
    data_fim: hoje(),
    consultor: '',
  });

  // Filtros Positivacao
  const [filtrosPositivacao, setFiltrosPositivacao] = useState<FiltrosMesAno>({
    mes: String(new Date().getMonth() + 1),
    ano: String(ANO_ATUAL),
    consultor: '',
  });

  // Filtros Atividades
  const [filtrosAtividades, setFiltrosAtividades] = useState<FiltrosAtividades>({
    data_inicio: primeiroDiaMes(),
    data_fim: hoje(),
    consultor: '',
  });

  // Filtros Inativos
  const [filtrosInativos, setFiltrosInativos] = useState<FiltrosInativos>({ consultor: '' });

  // Filtros Metas
  const [filtrosMetas, setFiltrosMetas] = useState<FiltrosMetas>({ consultor: '' });

  const setLoading = (tipo: string, val: boolean) =>
    setLoadingMap((prev) => ({ ...prev, [tipo]: val }));
  const setError = (tipo: string, msg: string | null) =>
    setErrorMap((prev) => ({ ...prev, [tipo]: msg }));

  const handleDownload = useCallback(async (tipo: string, params: Record<string, string>) => {
    setLoading(tipo, true);
    setError(tipo, null);
    try {
      await triggerDownload(tipo, params);
      addToast('sucesso', 'Relatorio gerado com sucesso');
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Erro ao baixar relatorio';
      setError(tipo, msg);
      addToast('erro', msg);
    } finally {
      setLoading(tipo, false);
    }
  }, [addToast]);

  const consultorOptions = CONSULTORES.map((c) => ({ value: c, label: c }));
  const mesOptions = MESES;
  const anoOptions = ANOS.map((a) => ({ value: a, label: a }));

  return (
    <div className="space-y-5">
      {/* Cabecalho */}
      <div>
        <h1 className="text-lg sm:text-xl font-bold text-gray-900">Central de Relatorios</h1>
        <p className="text-xs text-gray-500 mt-0.5">
          Gere e baixe relatorios em Excel com os filtros desejados
        </p>
      </div>

      {/* Grid de cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">

        {/* Card Vendas */}
        <CardRelatorio
          icon={IconVendas}
          titulo="Vendas"
          descricao="Vendas detalhadas por periodo com valor, consultor e cliente"
          loading={loadingMap['vendas'] ?? false}
          error={errorMap['vendas'] ?? null}
          onDownload={() =>
            void handleDownload('vendas', {
              data_inicio: filtrosVendas.data_inicio,
              data_fim: filtrosVendas.data_fim,
              consultor: filtrosVendas.consultor,
            })
          }
        >
          <DateFiltro
            id="vendas-inicio"
            label="Data Inicio"
            value={filtrosVendas.data_inicio}
            onChange={(v) => setFiltrosVendas((f) => ({ ...f, data_inicio: v }))}
          />
          <DateFiltro
            id="vendas-fim"
            label="Data Fim"
            value={filtrosVendas.data_fim}
            onChange={(v) => setFiltrosVendas((f) => ({ ...f, data_fim: v }))}
          />
          <SelectFiltro
            id="vendas-consultor"
            label="Consultor"
            value={filtrosVendas.consultor}
            onChange={(v) => setFiltrosVendas((f) => ({ ...f, consultor: v }))}
            options={consultorOptions}
          />
        </CardRelatorio>

        {/* Card Positivacao */}
        <CardRelatorio
          icon={IconPositivacao}
          titulo="Positivacao"
          descricao="Clientes que realizaram pelo menos uma compra no mes selecionado"
          loading={loadingMap['positivacao'] ?? false}
          error={errorMap['positivacao'] ?? null}
          onDownload={() =>
            void handleDownload('positivacao', {
              mes: filtrosPositivacao.mes,
              ano: filtrosPositivacao.ano,
              consultor: filtrosPositivacao.consultor,
            })
          }
        >
          <SelectFiltro
            id="positivacao-mes"
            label="Mes"
            value={filtrosPositivacao.mes}
            onChange={(v) => setFiltrosPositivacao((f) => ({ ...f, mes: v }))}
            options={mesOptions}
          />
          <SelectFiltro
            id="positivacao-ano"
            label="Ano"
            value={filtrosPositivacao.ano}
            onChange={(v) => setFiltrosPositivacao((f) => ({ ...f, ano: v }))}
            options={anoOptions}
          />
          <SelectFiltro
            id="positivacao-consultor"
            label="Consultor"
            value={filtrosPositivacao.consultor}
            onChange={(v) => setFiltrosPositivacao((f) => ({ ...f, consultor: v }))}
            options={consultorOptions}
          />
        </CardRelatorio>

        {/* Card Atividades */}
        <CardRelatorio
          icon={IconAtividades}
          titulo="Atividades"
          descricao="Atendimentos realizados: WhatsApp, ligacoes, visitas e emails por periodo"
          loading={loadingMap['atividades'] ?? false}
          error={errorMap['atividades'] ?? null}
          onDownload={() =>
            void handleDownload('atividades', {
              data_inicio: filtrosAtividades.data_inicio,
              data_fim: filtrosAtividades.data_fim,
              consultor: filtrosAtividades.consultor,
            })
          }
        >
          <DateFiltro
            id="atividades-inicio"
            label="Data Inicio"
            value={filtrosAtividades.data_inicio}
            onChange={(v) => setFiltrosAtividades((f) => ({ ...f, data_inicio: v }))}
          />
          <DateFiltro
            id="atividades-fim"
            label="Data Fim"
            value={filtrosAtividades.data_fim}
            onChange={(v) => setFiltrosAtividades((f) => ({ ...f, data_fim: v }))}
          />
          <SelectFiltro
            id="atividades-consultor"
            label="Consultor"
            value={filtrosAtividades.consultor}
            onChange={(v) => setFiltrosAtividades((f) => ({ ...f, consultor: v }))}
            options={consultorOptions}
          />
        </CardRelatorio>

        {/* Card Inativos */}
        <CardRelatorio
          icon={IconInativos}
          titulo="Clientes Inativos"
          descricao="Clientes sem compra recente classificados por risco de abandono"
          loading={loadingMap['inativos'] ?? false}
          error={errorMap['inativos'] ?? null}
          onDownload={() =>
            void handleDownload('inativos', {
              consultor: filtrosInativos.consultor,
            })
          }
        >
          <SelectFiltro
            id="inativos-consultor"
            label="Consultor"
            value={filtrosInativos.consultor}
            onChange={(v) => setFiltrosInativos({ consultor: v })}
            options={consultorOptions}
          />
        </CardRelatorio>

        {/* Card Metas */}
        <CardRelatorio
          icon={IconMetas}
          titulo="Metas"
          descricao="Meta vs Realizado por consultor com percentual de atingimento"
          loading={loadingMap['metas'] ?? false}
          error={errorMap['metas'] ?? null}
          onDownload={() =>
            void handleDownload('metas', {
              consultor: filtrosMetas.consultor,
            })
          }
        >
          <SelectFiltro
            id="metas-consultor"
            label="Consultor"
            value={filtrosMetas.consultor}
            onChange={(v) => setFiltrosMetas({ consultor: v })}
            options={consultorOptions}
          />
        </CardRelatorio>

      </div>

      {/* Nota de rodape */}
      <p className="text-[10px] text-gray-400">
        Os arquivos sao gerados em tempo real com os dados mais recentes do sistema. Formato: .xlsx compativel com Microsoft Excel.
      </p>

      {/* Toasts */}
      <ToastContainer toasts={toasts} onRemove={removeToast} />
    </div>
  );
}
