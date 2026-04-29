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
      colors: {
        // CRM VITAO360 brand colors (R9) — paleta canônica
        vitao: {
          // PT (legacy — em uso em vários componentes existentes)
          verde: '#00B050',      // ATIVO, sinaleiro VERDE, curva A
          amarelo: '#FFC000',    // INAT.REC, sinaleiro AMARELO, curva C
          vermelho: '#FF0000',   // INAT.ANT, sinaleiro VERMELHO
          roxo: '#800080',       // sinaleiro ROXO
          cinza: '#808080',      // PROSPECT
          abc_b: '#FFFF00',      // curva B
          // EN (Vitão MVP demo paleta — para Dashboard hero KPIs e Inbox)
          green: '#00A859',
          darkgreen: '#008C4A',
          lightgreen: '#E6F7EF',
          blue: '#0066CC',
          purple: '#7C3AED',
          orange: '#F59E0B',
          red: '#EF4444',
        },
      },
      borderWidth: {
        '3': '3px',
      },
    },
  },
  plugins: [],
};

export default config;
