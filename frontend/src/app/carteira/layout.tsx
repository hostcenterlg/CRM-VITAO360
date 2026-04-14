import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'Carteira de Clientes',
};

export default function CarteiraLayout({ children }: { children: React.ReactNode }) {
  return <>{children}</>;
}
