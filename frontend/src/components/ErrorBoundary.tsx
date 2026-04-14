'use client';

import React from 'react';

// ---------------------------------------------------------------------------
// ErrorBoundary — captura erros em toda a arvore de componentes
// Classe obrigatória: error boundaries só funcionam como class components
// Tema LIGHT exclusivamente
// ---------------------------------------------------------------------------

interface Props {
  children: React.ReactNode;
  /** Fallback customizado. Se omitido, usa o UI padrão. */
  fallback?: React.ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
  errorInfo: React.ErrorInfo | null;
}

export default class ErrorBoundary extends React.Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false, error: null, errorInfo: null };
  }

  static getDerivedStateFromError(error: Error): Partial<State> {
    return { hasError: true, error };
  }

  override componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    this.setState({ errorInfo });

    // Log estruturado — sem dependência externa
    if (process.env.NODE_ENV !== 'production') {
      console.error('[ErrorBoundary]', error.message, errorInfo.componentStack);
    }
  }

  private handleReset = () => {
    this.setState({ hasError: false, error: null, errorInfo: null });
  };

  private handleReload = () => {
    if (typeof window !== 'undefined') {
      window.location.reload();
    }
  };

  override render() {
    const { hasError, error } = this.state;
    const { children, fallback } = this.props;

    if (!hasError) return children;

    // Fallback customizado do caller
    if (fallback) return fallback;

    // UI padrão amigável
    return (
      <div
        role="alert"
        aria-live="assertive"
        className="min-h-[300px] flex items-center justify-center p-8"
      >
        <div className="max-w-md w-full bg-white rounded-xl border border-red-100 shadow-sm p-8 text-center">
          {/* Icone de erro */}
          <div className="w-14 h-14 mx-auto mb-4 rounded-full bg-red-50 flex items-center justify-center">
            <svg
              className="w-7 h-7 text-red-500"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              strokeWidth={1.5}
              aria-hidden="true"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.007v.008H12v-.008z"
              />
            </svg>
          </div>

          {/* Titulo */}
          <h2 className="text-base font-semibold text-gray-900 mb-1">
            Algo deu errado
          </h2>

          {/* Mensagem de erro (apenas em dev ou para erros conhecidos) */}
          <p className="text-sm text-gray-500 mb-6">
            {process.env.NODE_ENV !== 'production' && error?.message
              ? error.message
              : 'Ocorreu um erro inesperado. Tente novamente ou recarregue a pagina.'}
          </p>

          {/* Acoes */}
          <div className="flex flex-col sm:flex-row gap-3 justify-center">
            <button
              type="button"
              onClick={this.handleReset}
              className="inline-flex items-center justify-center gap-2 px-4 py-2 text-sm font-semibold text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 hover:border-gray-400 transition-colors"
            >
              <svg
                className="w-4 h-4"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
                strokeWidth={2}
                aria-hidden="true"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  d="M16.023 9.348h4.992v-.001M2.985 19.644v-4.992m0 0h4.992m-4.993 0l3.181 3.183a8.25 8.25 0 0013.803-3.7M4.031 9.865a8.25 8.25 0 0113.803-3.7l3.181 3.182m0-4.991v4.99"
                />
              </svg>
              Tentar novamente
            </button>
            <button
              type="button"
              onClick={this.handleReload}
              className="inline-flex items-center justify-center gap-2 px-4 py-2 text-sm font-semibold text-white rounded-lg transition-colors"
              style={{ backgroundColor: '#00B050' }}
            >
              <svg
                className="w-4 h-4"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
                strokeWidth={2}
                aria-hidden="true"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  d="M16.023 9.348h4.992v-.001M2.985 19.644v-4.992m0 0h4.992m-4.993 0l3.181 3.183a8.25 8.25 0 0013.803-3.7M4.031 9.865a8.25 8.25 0 0113.803-3.7l3.181 3.182m0-4.991v4.99"
                />
              </svg>
              Recarregar pagina
            </button>
          </div>
        </div>
      </div>
    );
  }
}

// ---------------------------------------------------------------------------
// withErrorBoundary — HOC para envolver componentes facilmente
// ---------------------------------------------------------------------------

export function withErrorBoundary<P extends object>(
  Component: React.ComponentType<P>,
  fallback?: React.ReactNode
): React.FC<P> {
  const Wrapped: React.FC<P> = (props) => (
    <ErrorBoundary fallback={fallback}>
      <Component {...props} />
    </ErrorBoundary>
  );
  Wrapped.displayName = `withErrorBoundary(${Component.displayName ?? Component.name ?? 'Component'})`;
  return Wrapped;
}
