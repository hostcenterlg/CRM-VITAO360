// frontend/src/components/ui/typography/Label.tsx
// Label para formulários e metadata pequena.
// Padrão: text-xs uppercase tracking-wide font-semibold text-tertiary.
// Pode ser usado como <label htmlFor> em formulários ou como tag descritiva em tabelas.

import React from 'react';

export type LabelVariant = 'default' | 'form' | 'inline';

export interface LabelProps {
  /** Variante visual:
   *  - default: uppercase + tracking-wide (metadata, cabeçalhos de seção)
   *  - form:    normal-case + sem tracking extra (label de campo de formulário)
   *  - inline:  inline-block para uso ao lado de outros elementos
   */
  variant?: LabelVariant;
  /** htmlFor para associação semântica com campos de formulário */
  htmlFor?: string;
  children: React.ReactNode;
  className?: string;
}

const variantStyles: Record<LabelVariant, string> = {
  default: 'block text-xs font-semibold uppercase tracking-wide text-text-tertiary',
  form:    'block text-sm font-medium text-text-secondary',
  inline:  'inline-block text-xs font-semibold uppercase tracking-wide text-text-tertiary',
};

export function Label({
  variant = 'default',
  htmlFor,
  children,
  className = '',
}: LabelProps) {
  const base = variantStyles[variant];
  const classes = `${base} ${className}`.trim();

  return (
    <label htmlFor={htmlFor} className={classes}>
      {children}
    </label>
  );
}
