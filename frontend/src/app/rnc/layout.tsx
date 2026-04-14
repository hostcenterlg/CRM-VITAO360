import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'RNC',
};

export default function RNCLayout({ children }: { children: React.ReactNode }) {
  return <>{children}</>;
}
