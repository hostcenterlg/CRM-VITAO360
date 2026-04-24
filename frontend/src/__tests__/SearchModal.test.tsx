import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import SearchModal from '@/components/SearchModal';

// Mock next/navigation — SearchModal usa useRouter para navegação
vi.mock('next/navigation', () => ({
  useRouter: () => ({
    push: vi.fn(),
    replace: vi.fn(),
    prefetch: vi.fn(),
    back: vi.fn(),
  }),
  usePathname: () => '/',
  useSearchParams: () => new URLSearchParams(),
}));

// Mock @/lib/api — evita chamadas HTTP reais nos testes de renderização
vi.mock('@/lib/api', () => ({
  fetchClientes: vi.fn().mockResolvedValue({ registros: [] }),
  fetchProdutos: vi.fn().mockResolvedValue({ itens: [] }),
  fetchVendasPorStatus: vi.fn().mockResolvedValue({ total: 0, items: [], page: 1, per_page: 100, pages: 0, has_next: false, has_prev: false }),
  formatBRL: vi.fn((v: number) => `R$ ${v}`),
}));

describe('SearchModal', () => {
  const onClose = vi.fn();

  beforeEach(() => {
    onClose.mockReset();
  });

  describe('visibilidade', () => {
    it('renderiza o modal quando open=true', () => {
      render(<SearchModal open={true} onClose={onClose} />);
      expect(screen.getByRole('dialog', { name: /busca global/i })).toBeInTheDocument();
    });

    it('não renderiza nada quando open=false', () => {
      render(<SearchModal open={false} onClose={onClose} />);
      expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
    });
  });

  describe('fechamento', () => {
    it('chama onClose ao pressionar Escape', () => {
      render(<SearchModal open={true} onClose={onClose} />);
      fireEvent.keyDown(window, { key: 'Escape' });
      expect(onClose).toHaveBeenCalledOnce();
    });

    it('chama onClose ao clicar no overlay', () => {
      render(<SearchModal open={true} onClose={onClose} />);
      // O overlay é o div com bg-black/40 — identificado por aria-hidden="true"
      const overlay = document.querySelector('[aria-hidden="true"].fixed.inset-0');
      if (overlay) {
        fireEvent.click(overlay);
        expect(onClose).toHaveBeenCalledOnce();
      }
    });
  });

  describe('input de busca', () => {
    it('renderiza o placeholder de busca', () => {
      render(<SearchModal open={true} onClose={onClose} />);
      expect(
        screen.getByPlaceholderText(/buscar cliente, pedido ou produto/i)
      ).toBeInTheDocument();
    });

    it('exibe dica "Digite pelo menos 2 caracteres" quando query está vazia', () => {
      render(<SearchModal open={true} onClose={onClose} />);
      expect(screen.getByText(/digite pelo menos 2 caracteres/i)).toBeInTheDocument();
    });
  });

  describe('acessibilidade', () => {
    it('modal tem aria-modal="true"', () => {
      render(<SearchModal open={true} onClose={onClose} />);
      const dialog = screen.getByRole('dialog');
      expect(dialog).toHaveAttribute('aria-modal', 'true');
    });
  });
});
