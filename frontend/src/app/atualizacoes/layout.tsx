import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'Atualizações',
};

export default function AtualizacoesLayout({ children }: { children: React.ReactNode }) {
  return <>{children}</>;
}
