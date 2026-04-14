import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'Produtos',
};

export default function ProdutosLayout({ children }: { children: React.ReactNode }) {
  return <>{children}</>;
}
