// frontend/src/styles/tokens.ts
// Design tokens — fonte de verdade para CRM VITAO360.
// Valores espelhados em tailwind.config.ts e globals.css (CSS custom properties).
// Wave 2 aplica esses tokens diretamente nas páginas.

export const typography = {
  fontFamily: {
    sans: ['Inter', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'sans-serif'],
    mono: ['ui-monospace', 'SFMono-Regular', 'Menlo', 'monospace'],
  },
  fontSize: {
    xs:   '12px',  // micro labels: tabular nums, badges, metadata mínima
    sm:   '13px',  // texto secundário, colunas de tabela densas
    base: '14px',  // body — DEFAULT (substituir text-[8/9/10px])
    md:   '15px',  // corpo enfatizado
    lg:   '17px',  // subtítulos de seção
    xl:   '20px',  // títulos de seção
    '2xl': '24px', // subtítulo de página
    '3xl': '30px', // título de página
    '4xl': '36px', // números hero
    '5xl': '48px', // KPIs de dashboard
  },
  fontWeight: {
    regular:  400,
    medium:   500,
    semibold: 600,
    bold:     700,
  },
  lineHeight: {
    tight:   1.2,
    snug:    1.375,
    normal:  1.5,
    relaxed: 1.625,
  },
};

export const colors = {
  // Vitao palette — preservada do tailwind existente
  vitao: {
    // PT (legacy — em uso em componentes existentes)
    verde:    '#00B050',
    amarelo:  '#FFC000',
    vermelho: '#FF0000',
    roxo:     '#800080',
    cinza:    '#808080',
    abc_b:    '#FFFF00',
    // EN (MVP demo)
    green:      '#00A859',
    darkgreen:  '#008C4A',
    lightgreen: '#E6F7EF',
    blue:       '#0066CC',
    purple:     '#7C3AED',
    orange:     '#F59E0B',
    red:        '#EF4444',
  },
  // Status (regras CRM — R9 CLAUDE.md)
  status: {
    ativo:          '#00B050',
    inativoRecente: '#FFC000',
    inativoAntigo:  '#FF0000',
  },
  // Curva ABC
  abc: {
    a: '#00B050',
    b: '#FFFF00',
    c: '#FFC000',
  },
  // Text — escala com contraste WCAG AA mínimo 4.5:1 sobre branco
  // primary:   gray-900 #111827  ratio ~16.75:1
  // secondary: gray-700 #374151  ratio ~9.4:1
  // tertiary:  gray-500 #6B7280  ratio ~4.62:1 — LIMITE mínimo, usar só em metadata small
  // NUNCA usar gray-300/gray-400 para texto (ratio abaixo de 4.5:1)
  text: {
    primary:   '#111827',
    secondary: '#374151',
    tertiary:  '#6B7280',
    inverse:   '#FFFFFF',
    danger:    '#DC2626',
    success:   '#059669',
  },
  // Surface
  surface: {
    base:    '#FFFFFF',
    raised:  '#F9FAFB',
    sunken:  '#F3F4F6',
    inverse: '#111827',
  },
  // Border
  border: {
    default: '#E5E7EB', // gray-200
    strong:  '#D1D5DB', // gray-300
    subtle:  '#F3F4F6', // gray-100
  },
};

export const spacing = {
  // Base unit: 4px
  '0':  '0',
  '1':  '4px',
  '2':  '8px',
  '3':  '12px',
  '4':  '16px',
  '5':  '20px',
  '6':  '24px',
  '8':  '32px',
  '10': '40px',
  '12': '48px',
  '16': '64px',
  '20': '80px',
};

export const radius = {
  none: '0',
  sm:   '4px',
  md:   '8px',
  lg:   '12px',
  xl:   '16px',
  '2xl': '20px',
  full: '9999px',
};

export const shadow = {
  sm:   '0 1px 2px 0 rgba(0,0,0,0.05)',
  base: '0 1px 3px 0 rgba(0,0,0,0.1), 0 1px 2px 0 rgba(0,0,0,0.06)',
  md:   '0 4px 6px -1px rgba(0,0,0,0.1)',
  lg:   '0 10px 15px -3px rgba(0,0,0,0.1)',
};
