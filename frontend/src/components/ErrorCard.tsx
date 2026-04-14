'use client';

// ---------------------------------------------------------------------------
// ErrorCard — card de erro reutilizavel com botao retry
// Variantes: padrao (com icone grande) e compact (linha simples)
// Tema LIGHT, textos pt-BR
// ---------------------------------------------------------------------------

export interface ErrorCardProps {
  message: string;
  onRetry?: () => void;
  compact?: boolean;
}

export function ErrorCard({ message, onRetry, compact = false }: ErrorCardProps) {
  if (compact) {
    return (
      <div
        role="alert"
        className="flex items-center gap-2 px-3 py-2 rounded-lg border border-red-200 bg-red-50"
      >
        <svg
          className="w-3.5 h-3.5 text-red-500 flex-shrink-0"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
          aria-hidden="true"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
          />
        </svg>
        <p className="text-xs text-red-700 flex-1 leading-snug">{message}</p>
        {onRetry && (
          <button
            type="button"
            onClick={onRetry}
            className="text-xs text-red-600 underline underline-offset-2 hover:text-red-800 transition-colors focus:outline-none focus:ring-2 focus:ring-red-400 rounded flex-shrink-0"
          >
            Tentar novamente
          </button>
        )}
      </div>
    );
  }

  return (
    <div
      role="alert"
      className="flex items-start gap-4 p-5 rounded-xl border border-red-200 bg-red-50"
    >
      {/* Icone */}
      <div
        className="flex-shrink-0 w-10 h-10 rounded-full flex items-center justify-center"
        style={{ backgroundColor: '#FEE2E2' }}
        aria-hidden="true"
      >
        <svg
          className="w-5 h-5 text-red-500"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
          />
        </svg>
      </div>

      {/* Conteudo */}
      <div className="flex-1 min-w-0">
        <p className="text-sm font-semibold text-red-800 mb-0.5">Erro ao carregar dados</p>
        <p className="text-xs text-red-600 leading-relaxed">{message}</p>

        {onRetry && (
          <button
            type="button"
            onClick={onRetry}
            className="mt-3 inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold text-red-700 border border-red-300 rounded-lg bg-white hover:bg-red-50 transition-colors focus:outline-none focus:ring-2 focus:ring-red-400"
          >
            <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
            Tentar novamente
          </button>
        )}
      </div>
    </div>
  );
}

export default ErrorCard;
