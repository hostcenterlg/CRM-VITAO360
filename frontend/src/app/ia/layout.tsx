import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'IA Comercial',
};

export default function IALayout({ children }: { children: React.ReactNode }) {
  return <>{children}</>;
}
