import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { StatusPill } from '@/components/ui/StatusPill';

describe('StatusPill', () => {
  it('renders ATIVO status with correct label', () => {
    render(<StatusPill status="ATIVO" />);
    expect(screen.getByText('Ativo')).toBeInTheDocument();
  });

  it('renders INAT.REC with warning variant', () => {
    const { container } = render(<StatusPill status="INAT.REC" />);
    const span = container.querySelector('span');
    expect(span?.className).toContain('bg-orange-100');
  });

  it('renders QUENTE with fire emoji when showIcon=true', () => {
    render(<StatusPill status="QUENTE" showIcon />);
    expect(screen.getByText('🔥')).toBeInTheDocument();
  });

  it('hides icon when showIcon=false', () => {
    render(<StatusPill status="QUENTE" showIcon={false} />);
    expect(screen.queryByText('🔥')).not.toBeInTheDocument();
  });

  it('renders unknown status as neutral with raw key', () => {
    render(<StatusPill status="STATUS_DESCONHECIDO" />);
    expect(screen.getByText('STATUS_DESCONHECIDO')).toBeInTheDocument();
  });

  it('handles EM RISCO (space variant)', () => {
    render(<StatusPill status="EM RISCO" />);
    expect(screen.getByText('Em Risco')).toBeInTheDocument();
  });
});
