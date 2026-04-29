// frontend/src/components/ui/typography/Heading.tsx
// Componente de heading semântico — mapeia level para tag HTML e escala tipográfica.
// Wave 2 substituirá h1-h4 inline por este componente.

import React from 'react';

type HeadingLevel = 1 | 2 | 3 | 4;

export interface HeadingProps {
  /** Nível semântico: 1=página, 2=seção grande, 3=seção, 4=subsection */
  level?: HeadingLevel;
  children: React.ReactNode;
  className?: string;
}

const levelStyles: Record<HeadingLevel, string> = {
  1: 'text-3xl font-semibold leading-tight text-text-primary',   // 30px — título de página
  2: 'text-2xl font-semibold leading-tight text-text-primary',   // 24px — subtítulo de página
  3: 'text-xl  font-semibold leading-snug  text-text-primary',   // 20px — título de seção
  4: 'text-lg  font-medium  leading-snug  text-text-secondary',  // 17px — subtítulo de seção
};

const levelTag: Record<HeadingLevel, keyof JSX.IntrinsicElements> = {
  1: 'h1',
  2: 'h2',
  3: 'h3',
  4: 'h4',
};

export function Heading({ level = 2, children, className = '' }: HeadingProps) {
  const Tag = levelTag[level];
  const base = levelStyles[level];

  return (
    <Tag className={`${base} ${className}`.trim()}>
      {children}
    </Tag>
  );
}
