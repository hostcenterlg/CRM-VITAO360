import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import KpiCard from '@/components/KpiCard';

describe('KpiCard', () => {
  it('renderiza o title', () => {
    render(<KpiCard title="Faturamento" value="R$ 2.091.000" />);
    expect(screen.getByText('Faturamento')).toBeInTheDocument();
  });

  it('renderiza o value', () => {
    render(<KpiCard title="Clientes" value={158} />);
    expect(screen.getByText('158')).toBeInTheDocument();
  });

  it('renderiza o subtitle quando fornecido', () => {
    render(<KpiCard title="KPI" value="0" subtitle="vs mês anterior" />);
    expect(screen.getByText('vs mês anterior')).toBeInTheDocument();
  });

  it('não renderiza subtitle quando omitido', () => {
    render(<KpiCard title="KPI" value="0" />);
    expect(screen.queryByText('vs mês anterior')).not.toBeInTheDocument();
  });

  it('aplica accentColor padrão verde na borda esquerda', () => {
    const { container } = render(<KpiCard title="KPI" value="0" />);
    const card = container.firstChild as HTMLElement;
    expect(card).toHaveStyle({ borderLeftColor: '#00B050' });
  });

  it('aplica accentColor customizado na borda esquerda', () => {
    const { container } = render(<KpiCard title="KPI" value="0" accentColor="#3B82F6" />);
    const card = container.firstChild as HTMLElement;
    expect(card).toHaveStyle({ borderLeftColor: '#3B82F6' });
  });

  it('renderiza estado de loading com placeholder animado no lugar do valor', () => {
    render(<KpiCard title="KPI" value="R$ 2.091.000" loading={true} />);
    // O valor real não deve aparecer quando loading
    expect(screen.queryByText('R$ 2.091.000')).not.toBeInTheDocument();
    // O placeholder de loading deve estar presente
    const { container } = render(<KpiCard title="KPI" value="R$ 2.091.000" loading={true} />);
    expect(container.querySelector('.animate-pulse')).toBeInTheDocument();
  });

  it('renderiza icon quando fornecido', () => {
    render(<KpiCard title="KPI" value="0" icon={<span data-testid="icone-kpi" />} />);
    expect(screen.getByTestId('icone-kpi')).toBeInTheDocument();
  });

  it('não renderiza wrapper de icon quando icon omitido', () => {
    const { container } = render(<KpiCard title="KPI" value="0" />);
    // Sem icon, não deve existir o span de ícone
    expect(container.querySelector('[aria-hidden="true"]')).not.toBeInTheDocument();
  });
});
