'use client';

// CanalIneligivelMessage — empty state para canal não elegível ao DDE
// Exibido quando backend retorna HTTP 422 (canal não tem pré-requisitos DDE)
// Canais elegíveis: DIRETO, INDIRETO, FOOD SERVICE (com dados estruturados)

interface CanalIneligivelMessageProps {
  canal?: string;
}

const CANAIS_ELEGIVEIS = ['DIRETO', 'INDIRETO', 'FOOD SERVICE'];

export function CanalIneligivelMessage({ canal }: CanalIneligivelMessageProps) {
  const nomeCanal = canal ?? 'desconhecido';

  return (
    <div
      className="flex flex-col items-center justify-center py-16 px-8 text-center"
      role="status"
      aria-live="polite"
    >
      <div
        className="w-14 h-14 rounded-2xl flex items-center justify-center mb-4"
        style={{ backgroundColor: '#6B728020' }}
      >
        <svg className="w-7 h-7 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={1.5}
            d="M18.364 18.364A9 9 0 005.636 5.636m12.728 12.728A9 9 0 015.636 5.636m12.728 12.728L5.636 5.636"
          />
        </svg>
      </div>

      <h3 className="text-base font-semibold text-gray-800 mb-2">
        DDE não disponível para este canal
      </h3>

      <p className="text-sm text-gray-600 leading-relaxed max-w-md mb-4">
        O canal atual deste cliente é{' '}
        <span className="font-semibold text-gray-800">{nomeCanal}</span>. O DDE atende apenas
        os canais{' '}
        <span className="font-medium">{CANAIS_ELEGIVEIS.join(', ')}</span>.
      </p>

      <div className="bg-gray-50 border border-gray-200 rounded-lg px-4 py-3 text-xs text-gray-600 max-w-md text-left">
        <p className="font-semibold text-gray-700 mb-1">Por que essa restrição?</p>
        <p className="leading-relaxed">
          O DDE exige massa de dados suficiente: contrato formalizado, verba negociada, frete
          CT-e dedicado e volume de vendas estruturado. Clientes de canais como{' '}
          <span className="italic">Interno, Farma, Body e Digital</span> não possuem esses
          dados, e forçar a cascata P&L geraria linhas vazias sem utilidade analítica.
        </p>
      </div>
    </div>
  );
}
