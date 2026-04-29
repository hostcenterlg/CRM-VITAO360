import type { Config } from 'tailwindcss';

const config: Config = {
  // Disable dark mode — CRM VITAO360 is LIGHT THEME ONLY (R9)
  darkMode: 'class', // requires explicit .dark class — never applied
  content: [
    './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
    './src/components/**/*.{js,ts,jsx,tsx,mdx}',
    './src/app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'sans-serif'],
        mono: ['ui-monospace', 'SFMono-Regular', 'Menlo', 'Monaco', 'Consolas', 'monospace'],
      },
      // Escala harmônica — substitui text-[8px]/text-[9px]/text-[10px] arbitrários
      fontSize: {
        xs:   ['12px', { lineHeight: '1.5' }],  // micro labels, badges
        sm:   ['13px', { lineHeight: '1.5' }],  // texto secundário, tabelas densas
        base: ['14px', { lineHeight: '1.5' }],  // body — DEFAULT
        md:   ['15px', { lineHeight: '1.5' }],  // corpo enfatizado
        lg:   ['17px', { lineHeight: '1.375' }], // subtítulos de seção
        xl:   ['20px', { lineHeight: '1.375' }], // títulos de seção
        '2xl': ['24px', { lineHeight: '1.2' }],  // subtítulo de página
        '3xl': ['30px', { lineHeight: '1.2' }],  // título de página
        '4xl': ['36px', { lineHeight: '1.2' }],  // números hero
        '5xl': ['48px', { lineHeight: '1.2' }],  // KPIs de dashboard
      },
      colors: {
        // CRM VITAO360 brand colors (R9) — paleta canônica
        vitao: {
          // PT (legacy — em uso em vários componentes existentes)
          verde:    '#00B050',  // ATIVO, sinaleiro VERDE, curva A
          amarelo:  '#FFC000',  // INAT.REC, sinaleiro AMARELO, curva C
          vermelho: '#FF0000',  // INAT.ANT, sinaleiro VERMELHO
          roxo:     '#800080',  // sinaleiro ROXO
          cinza:    '#808080',  // PROSPECT
          abc_b:    '#FFFF00',  // curva B
          // EN (Vitão MVP demo paleta — para Dashboard hero KPIs e Inbox)
          green:      '#00A859',
          darkgreen:  '#008C4A',
          lightgreen: '#E6F7EF',
          blue:       '#0066CC',
          purple:     '#7C3AED',
          orange:     '#F59E0B',
          red:        '#EF4444',
        },
        // Text — escala WCAG AA (ratio mínimo 4.5:1 sobre branco)
        // NUNCA usar raw gray-300/gray-400 para texto
        text: {
          primary:   '#111827', // gray-900 — ratio ~16.75:1
          secondary: '#374151', // gray-700 — ratio ~9.4:1
          tertiary:  '#6B7280', // gray-500 — ratio ~4.62:1 (limite, só metadata small)
          inverse:   '#FFFFFF',
          danger:    '#DC2626',
          success:   '#059669',
        },
        // Surface
        surface: {
          base:    '#FFFFFF',
          raised:  '#F9FAFB', // gray-50
          sunken:  '#F3F4F6', // gray-100
          inverse: '#111827', // gray-900
        },
        // Border
        border: {
          default: '#E5E7EB', // gray-200
          strong:  '#D1D5DB', // gray-300
          subtle:  '#F3F4F6', // gray-100
        },
        // Status (regras CRM — referência explícita para uso em classes arbitrárias)
        status: {
          ativo:           '#00B050',
          inativo_recente: '#FFC000',
          inativo_antigo:  '#FF0000',
        },
      },
      borderWidth: {
        '3': '3px',
      },
      borderRadius: {
        sm:   '4px',
        md:   '8px',
        lg:   '12px',
        xl:   '16px',
        '2xl': '20px',
      },
      boxShadow: {
        sm:   '0 1px 2px 0 rgba(0,0,0,0.05)',
        base: '0 1px 3px 0 rgba(0,0,0,0.1), 0 1px 2px 0 rgba(0,0,0,0.06)',
        md:   '0 4px 6px -1px rgba(0,0,0,0.1)',
        lg:   '0 10px 15px -3px rgba(0,0,0,0.1)',
      },
    },
  },
  plugins: [],
};

export default config;
