'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';

// ---------------------------------------------------------------------------
// useKeyboardShortcuts — atalhos globais de teclado para o CRM VITAO360
//
// Atalhos ativos quando o foco NAO esta em input/textarea/select:
//   Ctrl+K ou /     → Busca global (abre modal)
//   N               → Novo atendimento (abre modal na pagina atual ou navega)
//   A               → Agenda (/agenda)
//   C               → Carteira (/carteira)
//   I               → IA (/ia)
// ---------------------------------------------------------------------------

function isEditableTarget(e: KeyboardEvent): boolean {
  const target = e.target as HTMLElement | null;
  if (!target) return false;
  const tag = target.tagName.toUpperCase();
  if (tag === 'INPUT' || tag === 'TEXTAREA' || tag === 'SELECT') return true;
  if (target.isContentEditable) return true;
  return false;
}

interface UseKeyboardShortcutsOptions {
  onOpenSearch: () => void;
  onNewAtendimento?: () => void;
}

export function useKeyboardShortcuts({
  onOpenSearch,
  onNewAtendimento,
}: UseKeyboardShortcutsOptions) {
  const router = useRouter();

  useEffect(() => {
    function handleKeyDown(e: KeyboardEvent) {
      // Ctrl+K / Cmd+K — sempre ativo (mesmo em inputs)
      if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
        e.preventDefault();
        onOpenSearch();
        return;
      }

      // Atalhos de letra — apenas quando nao esta em campo de texto
      if (isEditableTarget(e)) return;

      // Ignorar quando modificadores estao ativos (exceto Shift)
      if (e.ctrlKey || e.metaKey || e.altKey) return;

      switch (e.key) {
        case '/':
          // Barra tambem abre busca global
          e.preventDefault();
          onOpenSearch();
          break;

        case 'n':
        case 'N':
          // Novo atendimento
          if (onNewAtendimento) {
            e.preventDefault();
            onNewAtendimento();
          }
          break;

        case 'a':
        case 'A':
          // Agenda
          e.preventDefault();
          router.push('/agenda');
          break;

        case 'c':
        case 'C':
          // Carteira
          e.preventDefault();
          router.push('/carteira');
          break;

        case 'i':
        case 'I':
          // IA
          e.preventDefault();
          router.push('/ia');
          break;

        default:
          break;
      }
    }

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [router, onOpenSearch, onNewAtendimento]);
}
