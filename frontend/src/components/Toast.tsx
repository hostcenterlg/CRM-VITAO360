'use client';

import { useCallback, useEffect, useRef, useState } from 'react';

// ---------------------------------------------------------------------------
// Toast — notificacao flutuante reutilizavel
// Posicao: fixed top-4 right-4, z-50
// Animacao: slide-in da direita, fade-out
// Tema LIGHT exclusivamente
// ---------------------------------------------------------------------------

export interface ToastProps {
  message: string;
  type: 'success' | 'error' | 'warning' | 'info';
  visible: boolean;
  onDismiss: () => void;
  duration?: number;
}

// ---------------------------------------------------------------------------
// Configuracao visual por tipo
// ---------------------------------------------------------------------------

const TYPE_CONFIG = {
  success: {
    bg: '#F0FDF4',
    border: '#86EFAC',
    text: '#166534',
    iconColor: '#16A34A',
    icon: (
      <svg className="w-4 h-4 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
      </svg>
    ),
    barColor: '#00B050',
    label: 'Sucesso',
  },
  error: {
    bg: '#FFF1F2',
    border: '#FECACA',
    text: '#991B1B',
    iconColor: '#EF4444',
    icon: (
      <svg className="w-4 h-4 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
      </svg>
    ),
    barColor: '#EF4444',
    label: 'Erro',
  },
  warning: {
    bg: '#FFFBEB',
    border: '#FDE68A',
    text: '#92400E',
    iconColor: '#F59E0B',
    icon: (
      <svg className="w-4 h-4 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
          d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
      </svg>
    ),
    barColor: '#F59E0B',
    label: 'Aviso',
  },
  info: {
    bg: '#EFF6FF',
    border: '#BFDBFE',
    text: '#1E40AF',
    iconColor: '#3B82F6',
    icon: (
      <svg className="w-4 h-4 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
    ),
    barColor: '#3B82F6',
    label: 'Informacao',
  },
} as const;

// ---------------------------------------------------------------------------
// Toast component
// ---------------------------------------------------------------------------

export function Toast({ message, type, visible, onDismiss, duration = 5000 }: ToastProps) {
  const cfg = TYPE_CONFIG[type];
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const [exiting, setExiting] = useState(false);

  const startDismiss = useCallback(() => {
    setExiting(true);
    setTimeout(onDismiss, 300);
  }, [onDismiss]);

  useEffect(() => {
    if (!visible) {
      setExiting(false);
      return;
    }
    if (timerRef.current) clearTimeout(timerRef.current);
    timerRef.current = setTimeout(startDismiss, duration);
    return () => {
      if (timerRef.current) clearTimeout(timerRef.current);
    };
  }, [visible, duration, startDismiss]);

  if (!visible && !exiting) return null;

  return (
    <div
      role="status"
      aria-live="polite"
      aria-atomic="true"
      className="fixed top-4 right-4 z-50 w-full max-w-sm pointer-events-auto"
      style={{
        animation: exiting
          ? 'toastSlideOut 0.3s ease-in forwards'
          : 'toastSlideIn 0.3s ease-out forwards',
      }}
    >
      <div
        className="flex items-start gap-3 px-4 py-3 rounded-lg shadow-lg border"
        style={{
          backgroundColor: cfg.bg,
          borderColor: cfg.border,
          color: cfg.text,
        }}
      >
        {/* Icone tipo */}
        <span style={{ color: cfg.iconColor }} className="mt-0.5">
          {cfg.icon}
        </span>

        {/* Mensagem */}
        <div className="flex-1 min-w-0">
          <p className="text-xs font-semibold uppercase tracking-wide opacity-70 mb-0.5">
            {cfg.label}
          </p>
          <p className="text-sm leading-snug break-words">{message}</p>
        </div>

        {/* Botao fechar */}
        <button
          type="button"
          onClick={startDismiss}
          aria-label="Fechar notificacao"
          className="flex-shrink-0 mt-0.5 rounded p-0.5 opacity-60 hover:opacity-100 transition-opacity focus:outline-none focus:ring-2 focus:ring-offset-1"
          style={{ color: cfg.text }}
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>

      {/* Barra de progresso temporal */}
      <div
        className="h-0.5 rounded-b-lg mt-0"
        style={{
          backgroundColor: cfg.barColor,
          animation: visible && !exiting ? `toastProgress ${duration}ms linear forwards` : 'none',
          opacity: 0.5,
        }}
      />

      {/* Keyframes inline via style tag — Tailwind nao suporta keyframes customizados inline */}
      <style>{`
        @keyframes toastSlideIn {
          from { opacity: 0; transform: translateX(100%); }
          to   { opacity: 1; transform: translateX(0); }
        }
        @keyframes toastSlideOut {
          from { opacity: 1; transform: translateX(0); }
          to   { opacity: 0; transform: translateX(100%); }
        }
        @keyframes toastProgress {
          from { width: 100%; }
          to   { width: 0%; }
        }
      `}</style>
    </div>
  );
}

// ---------------------------------------------------------------------------
// useToast hook
// ---------------------------------------------------------------------------

interface ToastState {
  message: string;
  type: ToastProps['type'];
  visible: boolean;
  key: number;
}

interface UseToastReturn {
  toast: {
    success: (message: string, duration?: number) => void;
    error: (message: string, duration?: number) => void;
    warning: (message: string, duration?: number) => void;
    info: (message: string, duration?: number) => void;
  };
  ToastComponent: React.ReactNode;
}

export function useToast(): UseToastReturn {
  const [state, setState] = useState<ToastState>({
    message: '',
    type: 'info',
    visible: false,
    key: 0,
  });
  const [duration, setDuration] = useState(5000);

  const show = useCallback((message: string, type: ToastProps['type'], dur = 5000) => {
    setDuration(dur);
    setState((prev) => ({
      message,
      type,
      visible: true,
      key: prev.key + 1,
    }));
  }, []);

  const dismiss = useCallback(() => {
    setState((prev) => ({ ...prev, visible: false }));
  }, []);

  const toast = {
    success: (message: string, dur?: number) => show(message, 'success', dur),
    error: (message: string, dur?: number) => show(message, 'error', dur),
    warning: (message: string, dur?: number) => show(message, 'warning', dur),
    info: (message: string, dur?: number) => show(message, 'info', dur),
  };

  const ToastComponent = (
    <Toast
      key={state.key}
      message={state.message}
      type={state.type}
      visible={state.visible}
      onDismiss={dismiss}
      duration={duration}
    />
  );

  return { toast, ToastComponent };
}

export default Toast;
