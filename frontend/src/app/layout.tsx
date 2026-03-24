import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import './globals.css';
import AppShell from '@/components/AppShell';

// ---------------------------------------------------------------------------
// Inter font via next/font/google — zero layout shift, self-hosted by Next.js
// ---------------------------------------------------------------------------
const inter = Inter({
  subsets: ['latin'],
  weight: ['400', '500', '600', '700'],
  variable: '--font-inter',
  display: 'swap',
});

export const metadata: Metadata = {
  title: 'CRM VITAO360',
  description: 'Sistema de Inteligencia Comercial — VITAO Alimentos B2B',
  robots: 'noindex, nofollow', // internal tool
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="pt-BR" className={inter.variable}>
      <body className="antialiased">
        <AppShell>
          {children}
        </AppShell>
      </body>
    </html>
  );
}
