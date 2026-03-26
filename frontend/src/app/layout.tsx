import type { Metadata, Viewport } from 'next';
import { Inter } from 'next/font/google';
import './globals.css';
import { AuthProvider } from '@/contexts/AuthContext';
import RouteGuard from '@/components/RouteGuard';

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

export const viewport: Viewport = {
  width: 'device-width',
  initialScale: 1,
  maximumScale: 1,
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="pt-BR" className={inter.variable}>
      <body className="antialiased">
        {/*
          AuthProvider: contexto de auth para toda a arvore.
          RouteGuard: protege rotas e decide se renderiza AppShell.
          Ambos sao client components — layout.tsx (server) apenas os importa.
        */}
        <AuthProvider>
          <RouteGuard>{children}</RouteGuard>
        </AuthProvider>
      </body>
    </html>
  );
}
