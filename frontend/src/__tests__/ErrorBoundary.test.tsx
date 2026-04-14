import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import React from 'react';
import ErrorBoundary from '@/components/ErrorBoundary';

// Suprime console.error para os testes de erro esperado
const originalConsoleError = console.error;
beforeEach(() => {
  console.error = vi.fn();
});
afterEach(() => {
  console.error = originalConsoleError;
});

// Componente auxiliar que lança erro quando commanded
function BombinaErro({ shouldThrow }: { shouldThrow: boolean }) {
  if (shouldThrow) {
    throw new Error('Erro de teste do componente');
  }
  return <div>Conteúdo normal</div>;
}

describe('ErrorBoundary', () => {
  it('renderiza children quando não há erro', () => {
    render(
      <ErrorBoundary>
        <div>Conteúdo normal</div>
      </ErrorBoundary>
    );
    expect(screen.getByText('Conteúdo normal')).toBeInTheDocument();
  });

  it('renderiza UI de erro padrão quando child lança exceção', () => {
    render(
      <ErrorBoundary>
        <BombinaErro shouldThrow={true} />
      </ErrorBoundary>
    );
    expect(screen.getByRole('alert')).toBeInTheDocument();
    expect(screen.getByText('Algo deu errado')).toBeInTheDocument();
  });

  it('renderiza fallback customizado quando fornecido e child lança exceção', () => {
    render(
      <ErrorBoundary fallback={<div>Fallback customizado</div>}>
        <BombinaErro shouldThrow={true} />
      </ErrorBoundary>
    );
    expect(screen.getByText('Fallback customizado')).toBeInTheDocument();
    expect(screen.queryByText('Algo deu errado')).not.toBeInTheDocument();
  });

  it('botão "Tentar novamente" reseta o estado de erro e renderiza children quando filho para de lançar', () => {
    // Wrapper controlável: após reset, o filho não lança mais
    let shouldThrow = true;

    function ControllableChild() {
      if (shouldThrow) throw new Error('Erro controlado');
      return <div>Recuperado com sucesso</div>;
    }

    render(
      <ErrorBoundary>
        <ControllableChild />
      </ErrorBoundary>
    );

    expect(screen.getByText('Algo deu errado')).toBeInTheDocument();

    // Para o filho de lançar antes de clicar em reset
    shouldThrow = false;
    fireEvent.click(screen.getByText('Tentar novamente'));

    expect(screen.getByText('Recuperado com sucesso')).toBeInTheDocument();
    expect(screen.queryByText('Algo deu errado')).not.toBeInTheDocument();
  });

  it('exibe mensagem de erro em modo de desenvolvimento', () => {
    render(
      <ErrorBoundary>
        <BombinaErro shouldThrow={true} />
      </ErrorBoundary>
    );
    // NODE_ENV é 'test' (não 'production'), então a mensagem deve aparecer
    expect(screen.getByText('Erro de teste do componente')).toBeInTheDocument();
  });

  it('mostra o role="alert" na UI de erro padrão', () => {
    render(
      <ErrorBoundary>
        <BombinaErro shouldThrow={true} />
      </ErrorBoundary>
    );
    expect(screen.getByRole('alert')).toBeInTheDocument();
  });
});
