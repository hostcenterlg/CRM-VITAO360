// gestao/_components/PreviewBanner.tsx
// Banner amarelo "dados ilustrativos" — obrigatório em toda feature preview (R8)
// Server-safe (no 'use client')

interface PreviewBannerProps {
  mensagem?: string;
  fase?: string;
}

export function PreviewBanner({
  mensagem = 'PREVIEW — dados ilustrativos. Integração real em Fase 3a.',
  fase = 'Fase 3a — Maio/2026',
}: PreviewBannerProps) {
  return (
    <div className="flex items-start gap-3 bg-amber-50 border border-amber-200 rounded-xl px-4 py-3">
      <svg
        className="w-4 h-4 text-amber-500 flex-shrink-0 mt-0.5"
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
      <div className="flex-1 min-w-0">
        <p className="text-xs font-bold text-amber-800 uppercase tracking-wide">
          Mockup ilustrativo — feature em desenvolvimento
        </p>
        <p className="text-xs text-amber-700 mt-0.5 leading-snug">
          {mensagem} Previsão de entrega: <span className="font-semibold">{fase}</span>
        </p>
      </div>
    </div>
  );
}
