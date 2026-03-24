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
        // CRM VITAO360 brand colors (R9)
        vitao: {
          verde: '#00B050',      // ATIVO, sinaleiro VERDE, curva A
          amarelo: '#FFC000',    // INAT.REC, sinaleiro AMARELO, curva C
          vermelho: '#FF0000',   // INAT.ANT, sinaleiro VERMELHO
          roxo: '#800080',       // sinaleiro ROXO
          cinza: '#808080',      // PROSPECT
          abc_b: '#FFFF00',      // curva B
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
