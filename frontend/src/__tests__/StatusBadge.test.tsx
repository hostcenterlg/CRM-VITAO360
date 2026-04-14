import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import StatusBadge from '@/components/StatusBadge';

describe('StatusBadge', () => {
  describe('variante situacao (padrão)', () => {
    it('renderiza ATIVO com fundo verde', () => {
      render(<StatusBadge value="ATIVO" />);
      const badge = screen.getByRole('status');
      expect(badge).toHaveStyle({ backgroundColor: '#00B050' });
    });

    it('renderiza INAT.REC com fundo amarelo', () => {
      render(<StatusBadge value="INAT.REC" />);
      const badge = screen.getByRole('status');
      expect(badge).toHaveStyle({ backgroundColor: '#FFC000' });
    });

    it('renderiza INAT.ANT com fundo vermelho', () => {
      render(<StatusBadge value="INAT.ANT" />);
      const badge = screen.getByRole('status');
      expect(badge).toHaveStyle({ backgroundColor: '#FF0000' });
    });

    it('renderiza status desconhecido com fallback cinza', () => {
      render(<StatusBadge value="DESCONHECIDO" />);
      const badge = screen.getByRole('status');
      expect(badge).toHaveStyle({ backgroundColor: '#e5e7eb' });
    });

    it('renderiza em maiúsculas mesmo com input minúsculo', () => {
      render(<StatusBadge value="ativo" />);
      const badge = screen.getByRole('status');
      expect(badge).toHaveStyle({ backgroundColor: '#00B050' });
    });

    it('renderiza traço quando value é string vazia', () => {
      render(<StatusBadge value="" />);
      expect(screen.getByText('—')).toBeInTheDocument();
    });
  });

  describe('variante abc', () => {
    it('renderiza A com fundo verde', () => {
      render(<StatusBadge value="A" variant="abc" />);
      const badge = screen.getByRole('status');
      expect(badge).toHaveStyle({ backgroundColor: '#00B050' });
    });

    it('renderiza B com fundo amarelo', () => {
      render(<StatusBadge value="B" variant="abc" />);
      const badge = screen.getByRole('status');
      expect(badge).toHaveStyle({ backgroundColor: '#FFFF00' });
    });

    it('renderiza C com fundo âmbar', () => {
      render(<StatusBadge value="C" variant="abc" />);
      const badge = screen.getByRole('status');
      expect(badge).toHaveStyle({ backgroundColor: '#FFC000' });
    });
  });

  describe('variante sinaleiro', () => {
    it('renderiza VERDE com cor correta', () => {
      render(<StatusBadge value="VERDE" variant="sinaleiro" />);
      const badge = screen.getByRole('status');
      expect(badge).toHaveStyle({ backgroundColor: '#00B050' });
    });

    it('renderiza VERMELHO com cor correta', () => {
      render(<StatusBadge value="VERMELHO" variant="sinaleiro" />);
      const badge = screen.getByRole('status');
      expect(badge).toHaveStyle({ backgroundColor: '#FF0000' });
    });
  });

  describe('variante prioridade', () => {
    it('renderiza P0 com fundo vermelho', () => {
      render(<StatusBadge value="P0" variant="prioridade" />);
      const badge = screen.getByRole('status');
      expect(badge).toHaveStyle({ backgroundColor: '#FF0000' });
    });

    it('renderiza P3 com fundo amarelo', () => {
      render(<StatusBadge value="P3" variant="prioridade" />);
      const badge = screen.getByRole('status');
      expect(badge).toHaveStyle({ backgroundColor: '#FFFF00' });
    });
  });

  describe('aria-label', () => {
    it('inclui variante e valor no aria-label', () => {
      render(<StatusBadge value="ATIVO" variant="situacao" />);
      const badge = screen.getByRole('status', { name: /situacao: ATIVO/i });
      expect(badge).toBeInTheDocument();
    });
  });
});
