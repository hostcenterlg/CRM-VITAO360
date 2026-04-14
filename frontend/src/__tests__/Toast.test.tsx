import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { Toast } from '@/components/Toast';

describe('Toast', () => {
  describe('visibilidade', () => {
    it('renderiza a mensagem quando visible=true', () => {
      render(
        <Toast
          message="Operação realizada com sucesso"
          type="success"
          visible={true}
          onDismiss={vi.fn()}
        />
      );
      expect(screen.getByText('Operação realizada com sucesso')).toBeInTheDocument();
    });

    it('não renderiza nada quando visible=false', () => {
      render(
        <Toast
          message="Mensagem oculta"
          type="success"
          visible={false}
          onDismiss={vi.fn()}
        />
      );
      expect(screen.queryByText('Mensagem oculta')).not.toBeInTheDocument();
    });
  });

  describe('disparo de onDismiss', () => {
    it('chama onDismiss ao clicar no botão de fechar (X)', () => {
      vi.useFakeTimers();
      const onDismiss = vi.fn();
      render(
        <Toast
          message="Toast de teste"
          type="info"
          visible={true}
          onDismiss={onDismiss}
        />
      );
      fireEvent.click(screen.getByRole('button', { name: /fechar notificacao/i }));
      // onDismiss é chamado após 300ms de animação de saída
      vi.advanceTimersByTime(350);
      expect(onDismiss).toHaveBeenCalledOnce();
      vi.useRealTimers();
    });
  });

  describe('ícone e label por tipo', () => {
    it('renderiza label "Sucesso" para tipo success', () => {
      render(
        <Toast message="msg" type="success" visible={true} onDismiss={vi.fn()} />
      );
      expect(screen.getByText('Sucesso')).toBeInTheDocument();
    });

    it('renderiza label "Erro" para tipo error', () => {
      render(
        <Toast message="msg" type="error" visible={true} onDismiss={vi.fn()} />
      );
      expect(screen.getByText('Erro')).toBeInTheDocument();
    });

    it('renderiza label "Aviso" para tipo warning', () => {
      render(
        <Toast message="msg" type="warning" visible={true} onDismiss={vi.fn()} />
      );
      expect(screen.getByText('Aviso')).toBeInTheDocument();
    });

    it('renderiza label "Informacao" para tipo info', () => {
      render(
        <Toast message="msg" type="info" visible={true} onDismiss={vi.fn()} />
      );
      expect(screen.getByText('Informacao')).toBeInTheDocument();
    });
  });

  describe('acessibilidade', () => {
    it('tem role="status" e aria-live="polite"', () => {
      render(
        <Toast message="msg" type="info" visible={true} onDismiss={vi.fn()} />
      );
      const toast = screen.getByRole('status');
      expect(toast).toHaveAttribute('aria-live', 'polite');
    });
  });
});
