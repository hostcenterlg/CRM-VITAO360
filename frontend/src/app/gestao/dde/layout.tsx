import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'DDE — Diagnostico Demonstrativo',
};

export default function DDELayout({ children }: { children: React.ReactNode }) {
  return <>{children}</>;
}
