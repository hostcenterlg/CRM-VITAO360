import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { Badge } from '@/components/ui/Badge';

describe('Badge', () => {
  it('renders children without crash', () => {
    render(<Badge>ATIVO</Badge>);
    expect(screen.getByText('ATIVO')).toBeInTheDocument();
  });

  it('applies success variant classes', () => {
    const { container } = render(<Badge variant="success">OK</Badge>);
    const span = container.firstChild as HTMLElement;
    expect(span.className).toContain('bg-green-100');
    expect(span.className).toContain('text-green-800');
  });

  it('applies danger variant classes', () => {
    const { container } = render(<Badge variant="danger">Risco</Badge>);
    const span = container.firstChild as HTMLElement;
    expect(span.className).toContain('bg-red-100');
    expect(span.className).toContain('text-red-800');
  });

  it('applies brand variant classes', () => {
    const { container } = render(<Badge variant="brand">Vitao</Badge>);
    const span = container.firstChild as HTMLElement;
    expect(span.className).toContain('bg-vitao-green');
    expect(span.className).toContain('text-white');
  });

  it('renders dot when dot=true', () => {
    const { container } = render(<Badge dot>Com dot</Badge>);
    // dot renders a span with aria-hidden
    const dot = container.querySelector('[aria-hidden="true"]');
    expect(dot).toBeInTheDocument();
  });

  it('merges custom className', () => {
    const { container } = render(<Badge className="my-custom-class">X</Badge>);
    const span = container.firstChild as HTMLElement;
    expect(span.className).toContain('my-custom-class');
  });
});
