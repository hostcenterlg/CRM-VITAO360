import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'Projeção',
};

export default function ProjecaoLayout({ children }: { children: React.ReactNode }) {
  return <>{children}</>;
}
