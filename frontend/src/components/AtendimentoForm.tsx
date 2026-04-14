'use client';

// AtendimentoForm — modal generico de registro de atendimento.
// Aceita qualquer cliente via { cnpj, nome_fantasia }.
// Pode ser chamado da Carteira, do ClienteDetalhe ou de qualquer outra pagina.
// A versao especifica da Agenda continua usando AtendimentoModal.tsx (que aceita AgendaItem).

import { useEffect, useRef, useState } from 'react';
import { registrarAtendimento, AtendimentoResponse } from '@/lib/api';
import MotorFeedback, { MotorFeedbackData } from '@/components/MotorFeedback';
import StatusBadge from '@/components/StatusBadge';

// ---------------------------------------------------------------------------
// Constantes de dominio
// ---------------------------------------------------------------------------

const RESULTADOS_GRUPOS = [
  {
    grupo: 'Positivos',
    itens: [
      'VENDA/PEDIDO',
      'ORCAMENTO',
      'EM ATENDIMENTO',
      'CADASTRO',
    ],
  },
  {
    grupo: 'Pos-venda',
    itens: [
      'POS-VENDA',
      'CS (SUCESSO DO CLIENTE)',
      'RELACIONAMENTO',
    ],
  },
  {
    grupo: 'Follow-up',
    itens: [
      'FOLLOW UP 7',
      'FOLLOW UP 15',
    ],
  },
  {
    grupo: 'Problemas',
    itens: [
      'SUPORTE',
      'NAO ATENDE',
      'NAO RESPONDE',
      'RECUSOU LIGACAO',
      'PERDA/FECHOU LOJA',
    ],
  },
] as const;

const TIPOS_CONTATO = [
  'LIGACAO',
  'WHATSAPP',
  'VISITA',
  'EMAIL',
  'VIDEOCHAMADA',
] as const;

type TipoContato = (typeof TIPOS_CONTATO)[number];

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function formatCnpj(cnpj: string): string {
  const d = cnpj.replace(/\D/g, '').padStart(14, '0');
  if (d.length !== 14) return cnpj;
  return `${d.slice(0, 2)}.${d.slice(2, 5)}.${d.slice(5, 8)}/${d.slice(8, 12)}-${d.slice(12)}`;
}

// ---------------------------------------------------------------------------
// Props
// ---------------------------------------------------------------------------

export interface AtendimentoFormCliente {
  cnpj: string;
  nome_fantasia: string;
  situacao?: string;
  sinaleiro?: string;
  score?: number;
  prioridade?: string;
  consultor?: string;
  uf?: string;
}

export interface AtendimentoFormProps {
  cliente: AtendimentoFormCliente;
  onClose: () => void;
  /** Chamado apos salvar com sucesso, antes de exibir feedback do motor */
  onSaved?: (cnpj: string) => void;
  /** Texto do botao de fechar apos feedback. Padrao: "Fechar" */
  labelFechar?: string;
}

// ---------------------------------------------------------------------------
// Componente principal
// ---------------------------------------------------------------------------

export default function AtendimentoForm({
  cliente,
  onClose,
  onSaved,
  labelFechar = 'Fechar',
}: AtendimentoFormProps) {
  const [resultado, setResultado] = useState('');
  const [tipoContato, setTipoContato] = useState<TipoContato>('LIGACAO');
  const [descricao, setDescricao] = useState('');
  const [saving, setSaving] = useState(false);
  const [errors, setErrors] = useState<{
    resultado?: string;
    descricao?: string;
    api?: string;
  }>({});
  const [motorFeedback, setMotorFeedback] = useState<MotorFeedbackData | null>(null);

  const firstFocusRef = useRef<HTMLSelectElement>(null);
  const dialogRef = useRef<HTMLDivElement>(null);

  // Foca o primeiro campo ao abrir
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
    return () => {
      document.body.style.overflow = '';
    };
  }, []);

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
        cnpj: cliente.cnpj,
        resultado,
        descricao: descricao.trim(),
        via_ligacao: tipoContato === 'LIGACAO',
        via_whatsapp: tipoContato === 'WHATSAPP',
        tipo_contato: tipoContato,
      });

      // Notifica pai
      onSaved?.(cliente.cnpj);

      // Exibe feedback do Motor se disponivel
      if (response.motor && Object.keys(response.motor).length > 0) {
        setMotorFeedback(response.motor);
      } else {
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
  // Render
  // ---------------------------------------------------------------------------

  return (
    <div
      className="fixed inset-0 z-50 flex items-end sm:items-center justify-center sm:p-4 bg-black/50 backdrop-blur-sm"
      onClick={(e) => { if (e.target === e.currentTarget) onClose(); }}
      aria-modal="true"
      role="dialog"
      aria-labelledby="atform-titulo"
    >
      <div
        ref={dialogRef}
        className="bg-white sm:rounded-xl shadow-2xl w-full sm:max-w-[560px] max-h-[95vh] sm:max-h-[calc(100vh-2rem)] flex flex-col rounded-t-2xl"
        style={{ animation: 'atformIn 200ms ease-out' }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="px-6 pt-6 pb-4 border-b border-gray-200 flex-shrink-0">
          <div className="flex items-start justify-between gap-4">
            <div className="min-w-0">
              <h2
                id="atform-titulo"
                className="text-base font-bold text-gray-900 leading-tight"
              >
                {motorFeedback ? 'Motor Processou' : 'Registrar Atendimento'}
              </h2>
              {!motorFeedback && (
                <p className="text-sm font-semibold text-gray-700 mt-0.5 truncate">
                  {cliente.nome_fantasia}
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
              <span className="font-mono text-gray-400">{formatCnpj(cliente.cnpj)}</span>
              {cliente.uf && (
                <span className="font-medium text-gray-600">{cliente.uf}</span>
              )}
              {cliente.situacao && (
                <StatusBadge value={cliente.situacao} variant="situacao" small />
              )}
              {cliente.consultor && (
                <span className="text-gray-500">{cliente.consultor}</span>
              )}
              {cliente.score !== undefined && (
                <span className="font-medium text-gray-700">Score {cliente.score}</span>
              )}
              {cliente.prioridade && (
                <StatusBadge value={cliente.prioridade} variant="prioridade" small />
              )}
            </div>
          )}
        </div>

        {/* Body */}
        <div className="flex-1 overflow-y-auto px-6 py-5">
          {motorFeedback ? (
            <MotorFeedback
              data={motorFeedback}
              onClose={onClose}
              labelFechar={labelFechar}
            />
          ) : (
            <form id="form-atendimento-generico" onSubmit={handleSubmit} noValidate>
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
                  htmlFor="atform-resultado"
                  className="block text-xs font-semibold text-gray-700 mb-1.5 uppercase tracking-wide"
                >
                  Resultado do Contato <span className="text-red-500">*</span>
                </label>
                <select
                  id="atform-resultado"
                  ref={firstFocusRef}
                  value={resultado}
                  onChange={(e) => {
                    setResultado(e.target.value);
                    if (errors.resultado) setErrors((p) => ({ ...p, resultado: undefined }));
                  }}
                  aria-required="true"
                  aria-invalid={!!errors.resultado}
                  aria-describedby={errors.resultado ? 'atform-erro-resultado' : undefined}
                  className={`w-full h-10 px-3 text-sm rounded-md border bg-white text-gray-900 focus:outline-none focus:ring-2 focus:ring-green-500 transition-colors ${
                    errors.resultado ? 'border-red-500 bg-red-50' : 'border-gray-300'
                  }`}
                >
                  <option value="">Selecione o resultado...</option>
                  {RESULTADOS_GRUPOS.map((g) => (
                    <optgroup key={g.grupo} label={g.grupo}>
                      {g.itens.map((r) => (
                        <option key={r} value={r}>{r}</option>
                      ))}
                    </optgroup>
                  ))}
                </select>
                {errors.resultado && (
                  <p id="atform-erro-resultado" role="alert" className="mt-1 text-xs text-red-600">
                    {errors.resultado}
                  </p>
                )}
              </div>

              {/* Campo TIPO_CONTATO */}
              <div className="mb-4">
                <label
                  htmlFor="atform-tipo-contato"
                  className="block text-xs font-semibold text-gray-700 mb-1.5 uppercase tracking-wide"
                >
                  Tipo de Contato
                </label>
                <select
                  id="atform-tipo-contato"
                  value={tipoContato}
                  onChange={(e) => setTipoContato(e.target.value as TipoContato)}
                  className="w-full h-10 px-3 text-sm rounded-md border border-gray-300 bg-white text-gray-900 focus:outline-none focus:ring-2 focus:ring-green-500 transition-colors"
                >
                  {TIPOS_CONTATO.map((t) => (
                    <option key={t} value={t}>{t}</option>
                  ))}
                </select>
              </div>

              {/* Campo DESCRICAO */}
              <div className="mb-4">
                <label
                  htmlFor="atform-descricao"
                  className="block text-xs font-semibold text-gray-700 mb-1.5 uppercase tracking-wide"
                >
                  Descricao <span className="text-red-500">*</span>
                </label>
                <textarea
                  id="atform-descricao"
                  value={descricao}
                  onChange={(e) => {
                    setDescricao(e.target.value);
                    if (errors.descricao) setErrors((p) => ({ ...p, descricao: undefined }));
                  }}
                  rows={4}
                  placeholder="O que aconteceu neste contato? Anote detalhes importantes..."
                  aria-required="true"
                  aria-invalid={!!errors.descricao}
                  aria-describedby={errors.descricao ? 'atform-erro-descricao' : 'atform-hint-descricao'}
                  className={`w-full px-3 py-2 text-sm rounded-md border bg-white text-gray-900 resize-none focus:outline-none focus:ring-2 focus:ring-green-500 transition-colors placeholder:text-gray-400 ${
                    errors.descricao ? 'border-red-500 bg-red-50' : 'border-gray-300'
                  }`}
                />
                <div className="mt-1 flex justify-between">
                  {errors.descricao ? (
                    <p id="atform-erro-descricao" role="alert" className="text-xs text-red-600">
                      {errors.descricao}
                    </p>
                  ) : (
                    <p id="atform-hint-descricao" className="text-xs text-gray-400">
                      Minimo 10 caracteres
                    </p>
                  )}
                  <p
                    className={`text-xs tabular-nums ${descricao.length < 10 ? 'text-gray-400' : 'text-green-600 font-medium'}`}
                    aria-live="polite"
                  >
                    {descricao.length} car.
                  </p>
                </div>
              </div>

              {/* Nota Two-Base */}
              <p className="text-[10px] text-gray-400 mt-3 pt-3 border-t border-gray-100">
                Valor: R$ 0,00 — log de atendimento (Two-Base Architecture)
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
              form="form-atendimento-generico"
              disabled={saving}
              aria-label={`Salvar atendimento de ${cliente.nome_fantasia}`}
              className="min-h-11 flex-1 sm:flex-none px-6 py-2 bg-green-600 hover:bg-green-700 disabled:opacity-60 text-white text-sm font-semibold rounded-md transition-colors focus:outline-none focus:ring-2 focus:ring-green-500 focus:ring-offset-2 flex items-center justify-center gap-2"
            >
              {saving && (
                <svg
                  className="w-4 h-4 animate-spin"
                  fill="none"
                  viewBox="0 0 24 24"
                >
                  <circle
                    className="opacity-25"
                    cx="12"
                    cy="12"
                    r="10"
                    stroke="currentColor"
                    strokeWidth="4"
                  />
                  <path
                    className="opacity-75"
                    fill="currentColor"
                    d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
                  />
                </svg>
              )}
              {saving ? 'Salvando...' : 'Salvar Atendimento'}
            </button>
          </div>
        )}
      </div>

      <style>{`
        @keyframes atformIn {
          from { opacity: 0; transform: scale(0.96); }
          to   { opacity: 1; transform: scale(1); }
        }
      `}</style>
    </div>
  );
}
