import type { Metadata, Viewport } from 'next';
import { Inter } from 'next/font/google';
import './globals.css';
import { AuthProvider } from '@/contexts/AuthContext';
import RouteGuard from '@/components/RouteGuard';
import ErrorBoundary from '@/components/ErrorBoundary';
import { Analytics } from '@vercel/analytics/react';

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
  title: {
    default: 'CRM VITAO360',
    template: '%s | CRM VITAO360',
  },
  description: 'CRM Inteligente para VITAO Alimentos — Inteligência Comercial B2B',
  robots: 'noindex, nofollow', // internal tool — not meant for search engines
  openGraph: {
    title: 'CRM VITAO360',
    description: 'Motor de Inteligência Comercial',
    siteName: 'VITAO360',
    type: 'website',
  },
  // PWA manifest declared here; <link rel="manifest"> injected by Next.js
  manifest: '/manifest.json',
  appleWebApp: {
    capable: true,
    statusBarStyle: 'default',
    title: 'VITAO360',
  },
  icons: {
    icon: '/icon-192.png',
    apple: '/icon-192.png',
  },
};

export const viewport: Viewport = {
  width: 'device-width',
  initialScale: 1,
  maximumScale: 1,
  themeColor: '#00B050',
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
          <ErrorBoundary>
            <RouteGuard>{children}</RouteGuard>
          </ErrorBoundary>
        </AuthProvider>
        <Analytics />
      </body>
    </html>
  );
}
