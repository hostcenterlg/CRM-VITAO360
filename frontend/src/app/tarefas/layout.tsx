import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'Tarefas',
};

export default function TarefasLayout({ children }: { children: React.ReactNode }) {
  return <>{children}</>;
}
