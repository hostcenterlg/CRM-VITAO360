// frontend/src/components/ui/typography/Text.tsx
// Componente de texto genérico com controle de tamanho, variante e peso.
// Substitui usos de texto inline com tamanhos arbitrários (text-[8px], text-[9px], etc.)
// e cores com baixo contraste (gray-300, gray-400).

import React from 'react';

export type TextSize = 'xs' | 'sm' | 'base' | 'md' | 'lg';

export type TextVariant = 'primary' | 'secondary' | 'tertiary' | 'danger' | 'success' | 'inverse';

export type TextWeight = 'regular' | 'medium' | 'semibold' | 'bold';

export interface TextProps {
  /** Tamanho da fonte: xs=12px, sm=13px, base=14px (default), md=15px, lg=17px */
  size?: TextSize;
  /** Variante de cor — todos com contraste WCAG AA mínimo */
  variant?: TextVariant;
  /** Peso tipográfico */
  weight?: TextWeight;
  /** Tag HTML de renderização */
  as?: keyof JSX.IntrinsicElements;
  children: React.ReactNode;
  className?: string;
}

const sizeStyles: Record<TextSize, string> = {
  xs:   'text-xs',
  sm:   'text-sm',
  base: 'text-base',
  md:   'text-md',
  lg:   'text-lg',
};

const variantStyles: Record<TextVariant, string> = {
  primary:   'text-text-primary',   // #111827 — ratio ~16.75:1
  secondary: 'text-text-secondary', // #374151 — ratio ~9.4:1
  tertiary:  'text-text-tertiary',  // #6B7280 — ratio ~4.62:1 (limite, só metadata small)
  danger:    'text-text-danger',    // #DC2626
  success:   'text-text-success',   // #059669
  inverse:   'text-text-inverse',   // #FFFFFF (sobre fundo escuro)
};

const weightStyles: Record<TextWeight, string> = {
  regular:  'font-normal',
  medium:   'font-medium',
  semibold: 'font-semibold',
  bold:     'font-bold',
};

export function Text({
  size = 'base',
  variant = 'primary',
  weight = 'regular',
  as: Tag = 'p',
  children,
  className = '',
}: TextProps) {
  const classes = [
    sizeStyles[size],
    variantStyles[variant],
    weightStyles[weight],
    className,
  ]
    .filter(Boolean)
    .join(' ');

  return <Tag className={classes}>{children}</Tag>;
}
