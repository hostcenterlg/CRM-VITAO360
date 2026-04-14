import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { ErrorCard } from '@/components/ErrorCard';

describe('ErrorCard', () => {
  describe('modo padrão (compact=false)', () => {
    it('renderiza a mensagem de erro', () => {
      render(<ErrorCard message="Falha ao carregar clientes" />);
      expect(screen.getByText('Falha ao carregar clientes')).toBeInTheDocument();
    });

    it('renderiza o título "Erro ao carregar dados"', () => {
      render(<ErrorCard message="Erro genérico" />);
      expect(screen.getByText('Erro ao carregar dados')).toBeInTheDocument();
    });

    it('renderiza botão "Tentar novamente" quando onRetry é fornecido', () => {
      const onRetry = vi.fn();
      render(<ErrorCard message="Erro" onRetry={onRetry} />);
      expect(screen.getByRole('button', { name: /tentar novamente/i })).toBeInTheDocument();
    });

    it('não renderiza botão retry quando onRetry é omitido', () => {
      render(<ErrorCard message="Erro" />);
      expect(screen.queryByRole('button', { name: /tentar novamente/i })).not.toBeInTheDocument();
    });

    it('chama onRetry ao clicar no botão retry', () => {
      const onRetry = vi.fn();
      render(<ErrorCard message="Erro" onRetry={onRetry} />);
      fireEvent.click(screen.getByRole('button', { name: /tentar novamente/i }));
      expect(onRetry).toHaveBeenCalledOnce();
    });

    it('tem role="alert" para acessibilidade', () => {
      render(<ErrorCard message="Erro" />);
      expect(screen.getByRole('alert')).toBeInTheDocument();
    });
  });

  describe('modo compact', () => {
    it('renderiza a mensagem em modo compact', () => {
      render(<ErrorCard message="Erro compacto" compact />);
      expect(screen.getByText('Erro compacto')).toBeInTheDocument();
    });

    it('não renderiza o título "Erro ao carregar dados" em modo compact', () => {
      render(<ErrorCard message="Erro compacto" compact />);
      expect(screen.queryByText('Erro ao carregar dados')).not.toBeInTheDocument();
    });

    it('renderiza link/botão retry inline em modo compact quando onRetry fornecido', () => {
      const onRetry = vi.fn();
      render(<ErrorCard message="Erro" compact onRetry={onRetry} />);
      expect(screen.getByRole('button', { name: /tentar novamente/i })).toBeInTheDocument();
    });

    it('chama onRetry ao clicar em modo compact', () => {
      const onRetry = vi.fn();
      render(<ErrorCard message="Erro" compact onRetry={onRetry} />);
      fireEvent.click(screen.getByRole('button', { name: /tentar novamente/i }));
      expect(onRetry).toHaveBeenCalledOnce();
    });

    it('tem role="alert" em modo compact para acessibilidade', () => {
      render(<ErrorCard message="Erro compacto" compact />);
      expect(screen.getByRole('alert')).toBeInTheDocument();
    });
  });
});
