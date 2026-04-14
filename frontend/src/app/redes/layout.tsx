import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'Redes',
};

export default function RedesLayout({ children }: { children: React.ReactNode }) {
  return <>{children}</>;
}
