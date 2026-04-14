'use client';

import { useEffect, useRef, useState } from 'react';
import { registrarAtendimento, AgendaItem, AtendimentoResponse } from '@/lib/api';
import StatusBadge from '@/components/StatusBadge';

// ---------------------------------------------------------------------------
// Constantes de dominio
// ---------------------------------------------------------------------------

const RESULTADOS = [
  'VENDA/PEDIDO',
  'ORCAMENTO',
  'POS-VENDA',
  'CS (SUCESSO DO CLIENTE)',
  'RELACIONAMENTO',
  'EM ATENDIMENTO',
  'FOLLOW UP 7',
  'FOLLOW UP 15',
  'SUPORTE',
  'NAO ATENDE',
  'NAO RESPONDE',
  'RECUSOU LIGACAO',
  'CADASTRO',
  'PERDA/FECHOU LOJA',
] as const;

type Resultado = (typeof RESULTADOS)[number];

// ---------------------------------------------------------------------------
// Helpers visuais
// ---------------------------------------------------------------------------

function formatCnpj(cnpj: string): string {
  const d = cnpj.replace(/\D/g, '').padStart(14, '0');
  if (d.length !== 14) return cnpj;
  return `${d.slice(0, 2)}.${d.slice(2, 5)}.${d.slice(5, 8)}/${d.slice(8, 12)}-${d.slice(12)}`;
}

function SinaleiroDot({ value }: { value?: string }) {
  const colorMap: Record<string, string> = {
    VERDE: '#00B050',
    AMARELO: '#FFC000',
    VERMELHO: '#FF0000',
    ROXO: '#7030A0',
    LARANJA: '#FF8C00',
  };
  const color = colorMap[(value ?? '').toUpperCase()] ?? '#D1D5DB';
  return (
    <span
      aria-label={`Sinaleiro: ${value ?? 'desconhecido'}`}
      style={{ backgroundColor: color }}
      className="inline-block w-2.5 h-2.5 rounded-full flex-shrink-0"
    />
  );
}

// ---------------------------------------------------------------------------
// Estado apos salvar — feedback do Motor
// ---------------------------------------------------------------------------

interface MotorFeedback {
  estagio_funil?: string;
  temperatura?: string;
  fase?: string;
  acao_futura?: string;
  follow_up?: string;
}

interface MotorResultProps {
  motor: MotorFeedback;
  onClose: () => void;
}

function MotorResultPanel({ motor, onClose }: MotorResultProps) {
  return (
    <div className="flex flex-col gap-4">
      {/* Cabecalho de sucesso */}
      <div className="flex items-center gap-2 p-3 bg-green-50 border border-green-200 rounded-md">
        <svg
          aria-hidden="true"
          className="w-5 h-5 text-green-600 flex-shrink-0"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
          strokeWidth={2.5}
        >
          <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
        </svg>
        <span className="text-sm font-semibold text-green-800">Motor processou com sucesso</span>
      </div>

      {/* Grid de outputs do Motor */}
      <div className="grid grid-cols-2 gap-x-6 gap-y-3 text-sm">
        {motor.estagio_funil && (
          <div>
            <p className="text-[10px] font-semibold text-gray-500 uppercase tracking-wide mb-0.5">Estagio Funil</p>
            <p className="font-medium text-gray-900">{motor.estagio_funil}</p>
          </div>
        )}
        {motor.temperatura && (
          <div>
            <p className="text-[10px] font-semibold text-gray-500 uppercase tracking-wide mb-0.5">Temperatura</p>
            <p className="font-medium text-gray-900">{motor.temperatura}</p>
          </div>
        )}
        {motor.fase && (
          <div>
            <p className="text-[10px] font-semibold text-gray-500 uppercase tracking-wide mb-0.5">Fase</p>
            <p className="font-medium text-gray-900">{motor.fase}</p>
          </div>
        )}
        {motor.follow_up && (
          <div>
            <p className="text-[10px] font-semibold text-gray-500 uppercase tracking-wide mb-0.5">Proximo Follow-up</p>
            <p className="font-medium text-gray-900">{motor.follow_up}</p>
          </div>
        )}
      </div>

      {motor.acao_futura && (
        <div>
          <p className="text-[10px] font-semibold text-gray-500 uppercase tracking-wide mb-1">Acao Futura</p>
          <div className="p-2.5 bg-blue-50 border-l-[3px] border-blue-400 rounded-r-md">
            <p className="text-sm font-semibold text-gray-900">{motor.acao_futura}</p>
          </div>
        </div>
      )}

      <button
        type="button"
        onClick={onClose}
        className="mt-1 w-full py-2.5 bg-green-600 hover:bg-green-700 text-white text-sm font-semibold rounded-md transition-colors focus:outline-none focus:ring-2 focus:ring-green-500 focus:ring-offset-2"
      >
        Fechar e continuar agenda
      </button>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Props do modal principal
// ---------------------------------------------------------------------------

export interface AtendimentoModalProps {
  item: AgendaItem;
  onClose: () => void;
  onSaved: (cnpj: string) => void;
}

// ---------------------------------------------------------------------------
// Modal principal
// ---------------------------------------------------------------------------

export default function AtendimentoModal({ item, onClose, onSaved }: AtendimentoModalProps) {
  const [resultado, setResultado] = useState<Resultado | ''>('');
  const [descricao, setDescricao] = useState('');
  const [viaLigacao, setViaLigacao] = useState(true);
  const [viaWhatsapp, setViaWhatsapp] = useState(false);
  const [saving, setSaving] = useState(false);
  const [errors, setErrors] = useState<{ resultado?: string; descricao?: string; api?: string }>({});
  const [motorFeedback, setMotorFeedback] = useState<MotorFeedback | null>(null);

  const firstFocusRef = useRef<HTMLSelectElement>(null);
  const dialogRef = useRef<HTMLDivElement>(null);

  // Foca o primeiro elemento ao abrir
  useEffect(() => {
    const t = setTimeout(() => firstFocusRef.current?.focus(), 80);
    return () => clearTimeout(t);
  }, []);

  // Fecha com ESC
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    document.addEventListener('keydown', handler);
    return () => document.removeEventListener('keydown', handler);
  }, [onClose]);

  // Trava scroll do body enquanto modal esta aberto
  useEffect(() => {
    document.body.style.overflow = 'hidden';
    return () => { document.body.style.overflow = ''; };
  }, []);

  // Trap foco dentro do modal
  const handleBackdropClick = (e: React.MouseEvent<HTMLDivElement>) => {
    if (e.target === e.currentTarget) onClose();
  };

  // ---------------------------------------------------------------------------
  // Validacao
  // ---------------------------------------------------------------------------

  function validate(): boolean {
    const errs: typeof errors = {};
    if (!resultado) errs.resultado = 'Selecione o resultado do contato';
    if (descricao.trim().length < 10) errs.descricao = 'Minimo 10 caracteres';
    setErrors(errs);
    return Object.keys(errs).length === 0;
  }

  // ---------------------------------------------------------------------------
  // Submit
  // ---------------------------------------------------------------------------

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!validate()) return;

    setSaving(true);
    setErrors({});

    try {
      const response: AtendimentoResponse = await registrarAtendimento({
        cnpj: item.cnpj,
        resultado: resultado as string,
        descricao: descricao.trim(),
        via_ligacao: viaLigacao,
        via_whatsapp: viaWhatsapp,
      });

      // Marca o card como concluido na agenda
      onSaved(item.cnpj);

      // Exibe feedback do Motor se disponivel
      if (response.motor && Object.keys(response.motor).length > 0) {
        setMotorFeedback(response.motor);
      } else {
        // Motor sem feedback — fecha diretamente
        onClose();
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Erro ao salvar atendimento';
      setErrors({ api: msg });
    } finally {
      setSaving(false);
    }
  }

  // ---------------------------------------------------------------------------
  // Cor de fundo do bloco de acao baseada no sinaleiro
  // ---------------------------------------------------------------------------

  function acaoBgClass(): string {
    switch ((item.sinaleiro ?? '').toUpperCase()) {
      case 'VERMELHO': return 'bg-red-50 border-red-400';
      case 'AMARELO':  return 'bg-yellow-50 border-yellow-400';
      case 'ROXO':     return 'bg-purple-50 border-purple-400';
      default:         return 'bg-green-50 border-green-400';
    }
  }

  // ---------------------------------------------------------------------------
  // Render
  // ---------------------------------------------------------------------------

  return (
    <div
      className="fixed inset-0 z-50 flex items-end sm:items-center justify-center sm:p-4 bg-black/50 backdrop-blur-sm"
      onClick={handleBackdropClick}
      aria-modal="true"
      role="dialog"
      aria-labelledby="modal-titulo"
    >
      <div
        ref={dialogRef}
        className="bg-white sm:rounded-xl shadow-2xl w-full sm:max-w-[560px] max-h-[95vh] sm:max-h-[calc(100vh-2rem)] flex flex-col rounded-t-2xl"
        style={{ animation: 'modalIn 200ms ease-out' }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="px-6 pt-6 pb-4 border-b border-gray-200 flex-shrink-0">
          <div className="flex items-start justify-between gap-4">
            <div className="min-w-0">
              <h2
                id="modal-titulo"
                className="text-base font-bold text-gray-900 leading-tight"
              >
                {motorFeedback ? 'Motor Processou' : 'Registrar Atendimento'}
              </h2>
              {!motorFeedback && (
                <p className="text-sm font-semibold text-gray-700 mt-0.5 truncate">
                  {item.nome_fantasia}
                </p>
              )}
            </div>
            <button
              type="button"
              onClick={onClose}
              aria-label="Fechar modal"
              className="flex-shrink-0 p-1.5 rounded-md text-gray-400 hover:text-gray-700 hover:bg-gray-100 transition-colors focus:outline-none focus:ring-2 focus:ring-green-500"
            >
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>

          {/* Linha de identidade do cliente */}
          {!motorFeedback && (
            <div className="mt-2 flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-gray-500">
              <span className="font-mono text-gray-400">{formatCnpj(item.cnpj)}</span>
              {item.situacao && (
                <StatusBadge value={item.situacao} variant="situacao" small />
              )}
              <span className="flex items-center gap-1">
                <SinaleiroDot value={item.sinaleiro} />
                <span className="uppercase">{item.sinaleiro ?? '—'}</span>
              </span>
              {item.score !== undefined && (
                <span className="font-medium text-gray-700">Score {item.score}</span>
              )}
              {item.prioridade && (
                <StatusBadge value={item.prioridade} variant="prioridade" small />
              )}
            </div>
          )}
        </div>

        {/* Body */}
        <div className="flex-1 overflow-y-auto px-6 py-5">
          {motorFeedback ? (
            <MotorResultPanel motor={motorFeedback} onClose={onClose} />
          ) : (
            <form id="form-atendimento" onSubmit={handleSubmit} noValidate>
              {/* Acao prescrita (contexto visual) */}
              {item.acao && (
                <div className={`mb-5 p-2.5 border-l-[3px] rounded-r-md ${acaoBgClass()}`}>
                  <p className="text-[10px] font-semibold text-gray-500 uppercase tracking-wide mb-0.5">
                    Acao prescrita pelo Motor
                  </p>
                  <p className="text-sm font-semibold text-gray-900">{item.acao}</p>
                </div>
              )}

              {/* Erro de API */}
              {errors.api && (
                <div
                  role="alert"
                  className="mb-4 px-3 py-2.5 bg-red-50 border border-red-200 rounded-md text-sm text-red-700"
                >
                  {errors.api}
                </div>
              )}

              {/* Campo RESULTADO */}
              <div className="mb-4">
                <label
                  htmlFor="campo-resultado"
                  className="block text-xs font-semibold text-gray-700 mb-1.5 uppercase tracking-wide"
                >
                  Resultado do Contato <span className="text-red-500">*</span>
                </label>
                <select
                  id="campo-resultado"
                  ref={firstFocusRef}
                  value={resultado}
                  onChange={(e) => {
                    setResultado(e.target.value as Resultado | '');
                    if (errors.resultado) setErrors((p) => ({ ...p, resultado: undefined }));
                  }}
                  aria-required="true"
                  aria-invalid={!!errors.resultado}
                  aria-describedby={errors.resultado ? 'erro-resultado' : undefined}
                  className={`w-full h-10 px-3 text-sm rounded-md border bg-white text-gray-900 focus:outline-none focus:ring-2 focus:ring-green-500 transition-colors ${
                    errors.resultado ? 'border-red-500 bg-red-50' : 'border-gray-300'
                  }`}
                >
                  <option value="">Selecione o resultado...</option>
                  {RESULTADOS.map((r) => (
                    <option key={r} value={r}>
                      {r}
                    </option>
                  ))}
                </select>
                {errors.resultado && (
                  <p id="erro-resultado" role="alert" className="mt-1 text-xs text-red-600">
                    {errors.resultado}
                  </p>
                )}
              </div>

              {/* Campo DESCRICAO */}
              <div className="mb-4">
                <label
                  htmlFor="campo-descricao"
                  className="block text-xs font-semibold text-gray-700 mb-1.5 uppercase tracking-wide"
                >
                  Descricao <span className="text-red-500">*</span>
                </label>
                <textarea
                  id="campo-descricao"
                  value={descricao}
                  onChange={(e) => {
                    setDescricao(e.target.value);
                    if (errors.descricao) setErrors((p) => ({ ...p, descricao: undefined }));
                  }}
                  rows={3}
                  placeholder="O que aconteceu neste contato?"
                  aria-required="true"
                  aria-invalid={!!errors.descricao}
                  aria-describedby={errors.descricao ? 'erro-descricao' : 'hint-descricao'}
                  className={`w-full px-3 py-2 text-sm rounded-md border bg-white text-gray-900 resize-none focus:outline-none focus:ring-2 focus:ring-green-500 transition-colors placeholder:text-gray-400 ${
                    errors.descricao ? 'border-red-500 bg-red-50' : 'border-gray-300'
                  }`}
                />
                <div className="mt-1 flex justify-between">
                  {errors.descricao ? (
                    <p id="erro-descricao" role="alert" className="text-xs text-red-600">
                      {errors.descricao}
                    </p>
                  ) : (
                    <p id="hint-descricao" className="text-xs text-gray-400">
                      Minimo 10 caracteres
                    </p>
                  )}
                  <p
                    className={`text-xs ${descricao.length < 10 ? 'text-gray-400' : 'text-green-600'}`}
                    aria-live="polite"
                  >
                    {descricao.length} car.
                  </p>
                </div>
              </div>

              {/* Tipo de contato */}
              <div className="mb-4">
                <p className="text-xs font-semibold text-gray-700 mb-2 uppercase tracking-wide">
                  Tipo de Contato
                </p>
                <div className="flex flex-wrap gap-4">
                  <label className="flex items-center gap-2 cursor-pointer select-none">
                    <input
                      type="checkbox"
                      checked={viaLigacao}
                      onChange={(e) => setViaLigacao(e.target.checked)}
                      className="w-4 h-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                    />
                    <span className="text-sm text-gray-700">Ligacao</span>
                  </label>
                  <label className="flex items-center gap-2 cursor-pointer select-none">
                    <input
                      type="checkbox"
                      checked={viaWhatsapp}
                      onChange={(e) => setViaWhatsapp(e.target.checked)}
                      className="w-4 h-4 rounded border-gray-300 text-green-600 focus:ring-green-500"
                    />
                    <span className="text-sm text-gray-700">WhatsApp</span>
                  </label>
                </div>
              </div>

              {/* Nota Two-Base */}
              <p className="text-[10px] text-gray-400 mt-3 pt-3 border-t border-gray-100">
                Valor: R$ 0,00 (log de atendimento — Two-Base Architecture)
              </p>
            </form>
          )}
        </div>

        {/* Footer — so exibe antes de salvar */}
        {!motorFeedback && (
          <div className="px-4 sm:px-6 py-4 border-t border-gray-200 flex items-center justify-between gap-3 flex-shrink-0">
            <button
              type="button"
              onClick={onClose}
              disabled={saving}
              className="min-h-11 px-4 py-2 text-sm font-medium text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-md transition-colors focus:outline-none focus:ring-2 focus:ring-gray-400 disabled:opacity-50"
            >
              Cancelar
            </button>
            <button
              type="submit"
              form="form-atendimento"
              disabled={saving}
              aria-label={`Salvar atendimento de ${item.nome_fantasia}`}
              className="min-h-11 flex-1 sm:flex-none px-5 py-2 bg-green-600 hover:bg-green-700 disabled:opacity-60 text-white text-sm font-semibold rounded-md transition-colors focus:outline-none focus:ring-2 focus:ring-green-500 focus:ring-offset-2 flex items-center justify-center gap-2"
            >
              {saving && (
                <svg
                  className="w-4 h-4 animate-spin"
                  fill="none"
                  viewBox="0 0 24 24"
                >
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                </svg>
              )}
              {saving ? 'Salvando...' : 'Salvar Atendimento'}
            </button>
          </div>
        )}
      </div>

      {/* Animacao de abertura do modal */}
      <style>{`
        @keyframes modalIn {
          from { opacity: 0; transform: scale(0.96); }
          to   { opacity: 1; transform: scale(1); }
        }
      `}</style>
    </div>
  );
}
