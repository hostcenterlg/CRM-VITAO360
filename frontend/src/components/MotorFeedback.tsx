'use client';

// MotorFeedback — card reutilizavel que exibe o resultado do Motor de Regras
// apos o registro de um atendimento.
// Pode ser usado em linha (inline) ou dentro de um modal.

export interface MotorFeedbackData {
  estagio_funil?: string;
  temperatura?: string;
  fase?: string;
  acao_futura?: string;
  follow_up?: string;
}

// ---------------------------------------------------------------------------
// Helpers de cor
// ---------------------------------------------------------------------------

function temperaturaColor(temp?: string): { bg: string; text: string; border: string } {
  switch ((temp ?? '').toUpperCase()) {
    case 'QUENTE':  return { bg: '#FEF2F2', text: '#991B1B', border: '#F87171' };
    case 'MORNO':   return { bg: '#FFFBEB', text: '#92400E', border: '#FCD34D' };
    case 'FRIO':    return { bg: '#EFF6FF', text: '#1E3A8A', border: '#93C5FD' };
    case 'CRITICO': return { bg: '#FDF4FF', text: '#6B21A8', border: '#C084FC' };
    default:        return { bg: '#F9FAFB', text: '#374151', border: '#D1D5DB' };
  }
}

function estagioColor(estagio?: string): { bg: string; text: string } {
  const s = (estagio ?? '').toUpperCase();
  if (s.includes('GANHO') || s.includes('ATIVO'))  return { bg: '#DCFCE7', text: '#166534' };
  if (s.includes('PERDA') || s.includes('CRITICO')) return { bg: '#FEE2E2', text: '#991B1B' };
  if (s.includes('NUTRI'))                          return { bg: '#F0FDF4', text: '#14532D' };
  if (s.includes('AQUISI'))                         return { bg: '#EFF6FF', text: '#1E40AF' };
  if (s.includes('REATIV'))                         return { bg: '#FFF7ED', text: '#9A3412' };
  if (s.includes('SEGURAN'))                        return { bg: '#F5F3FF', text: '#5B21B6' };
  return { bg: '#F3F4F6', text: '#374151' };
}

// ---------------------------------------------------------------------------
// Componente principal
// ---------------------------------------------------------------------------

interface MotorFeedbackProps {
  data: MotorFeedbackData;
  onClose?: () => void;
  /** Texto do botao de fechar. Padrao: "Fechar" */
  labelFechar?: string;
  /** Se true, nao renderiza o botao de fechar */
  semBotao?: boolean;
}

export default function MotorFeedback({
  data,
  onClose,
  labelFechar = 'Fechar',
  semBotao = false,
}: MotorFeedbackProps) {
  const tempColors = temperaturaColor(data.temperatura);
  const estagColors = estagioColor(data.estagio_funil);

  const temDados =
    data.estagio_funil ||
    data.temperatura ||
    data.fase ||
    data.acao_futura ||
    data.follow_up;

  return (
    <div className="flex flex-col gap-4">
      {/* Cabecalho de sucesso */}
      <div className="flex items-center gap-2.5 px-3.5 py-3 bg-green-50 border border-green-200 rounded-lg">
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
        <div>
          <p className="text-sm font-semibold text-green-800">Atendimento registrado</p>
          <p className="text-xs text-green-600">Motor processou e atualizou o perfil do cliente</p>
        </div>
      </div>

      {/* Grid de outputs do Motor */}
      {temDados && (
        <div className="grid grid-cols-2 gap-x-4 gap-y-3">
          {/* Estagio Funil */}
          {data.estagio_funil && (
            <div className="col-span-2">
              <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-1">
                Estagio do Funil
              </p>
              <span
                className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-semibold"
                style={{ backgroundColor: estagColors.bg, color: estagColors.text }}
              >
                {data.estagio_funil}
              </span>
            </div>
          )}

          {/* Temperatura */}
          {data.temperatura && (
            <div>
              <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-1">
                Temperatura
              </p>
              <span
                className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-bold border"
                style={{
                  backgroundColor: tempColors.bg,
                  color: tempColors.text,
                  borderColor: tempColors.border,
                }}
              >
                {data.temperatura}
              </span>
            </div>
          )}

          {/* Fase */}
          {data.fase && (
            <div>
              <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-1">
                Fase
              </p>
              <p className="text-sm font-medium text-gray-900">{data.fase}</p>
            </div>
          )}

          {/* Proximo follow-up */}
          {data.follow_up && (
            <div className="col-span-2">
              <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-1">
                Proximo Follow-up
              </p>
              <div className="inline-flex items-center gap-1.5 px-2.5 py-1 bg-blue-50 border border-blue-200 rounded-lg">
                <svg
                  aria-hidden="true"
                  className="w-3.5 h-3.5 text-blue-500 flex-shrink-0"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                  strokeWidth={2}
                >
                  <path strokeLinecap="round" strokeLinejoin="round" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                </svg>
                <span className="text-xs font-semibold text-blue-800">{data.follow_up}</span>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Acao futura */}
      {data.acao_futura && (
        <div>
          <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-1.5">
            Acao Futura Recomendada
          </p>
          <div className="px-3 py-2.5 bg-blue-50 border-l-[3px] border-blue-400 rounded-r-lg">
            <p className="text-sm font-semibold text-gray-900">{data.acao_futura}</p>
          </div>
        </div>
      )}

      {/* Botao de fechar */}
      {!semBotao && onClose && (
        <button
          type="button"
          onClick={onClose}
          className="mt-1 w-full py-2.5 bg-green-600 hover:bg-green-700 text-white text-sm font-semibold rounded-lg transition-colors focus:outline-none focus:ring-2 focus:ring-green-500 focus:ring-offset-2"
        >
          {labelFechar}
        </button>
      )}
    </div>
  );
}
