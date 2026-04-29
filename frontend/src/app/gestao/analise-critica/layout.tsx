import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'Analise Critica do Cliente',
};

export default function AnaliseCriticaLayout({ children }: { children: React.ReactNode }) {
  return <>{children}</>;
}
