import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'Sinaleiro',
};

export default function SinaleiroLayout({ children }: { children: React.ReactNode }) {
  return <>{children}</>;
}
