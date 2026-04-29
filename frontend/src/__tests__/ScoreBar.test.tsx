import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { ScoreBar } from '@/components/ui/ScoreBar';

describe('ScoreBar', () => {
  it('renders without crash', () => {
    const { container } = render(<ScoreBar score={75} />);
    expect(container.firstChild).toBeInTheDocument();
  });

  it('has correct role and aria attrs', () => {
    render(<ScoreBar score={80} ariaLabel="Score cliente" />);
    const meter = screen.getByRole('meter', { name: 'Score cliente' });
    expect(meter).toBeInTheDocument();
    expect(meter).toHaveAttribute('aria-valuenow', '80');
    expect(meter).toHaveAttribute('aria-valuemin', '0');
    expect(meter).toHaveAttribute('aria-valuemax', '100');
  });

  it('clamps score above 100 to 100', () => {
    render(<ScoreBar score={150} />);
    const meter = screen.getByRole('meter');
    expect(meter).toHaveAttribute('aria-valuenow', '100');
  });

  it('clamps score below 0 to 0', () => {
    render(<ScoreBar score={-10} />);
    const meter = screen.getByRole('meter');
    expect(meter).toHaveAttribute('aria-valuenow', '0');
  });

  it('applies green color for score >= 70', () => {
    const { container } = render(<ScoreBar score={75} />);
    const fill = container.querySelector('[style]');
    expect(fill?.className).toContain('bg-green-500');
  });

  it('applies red color for score < 40', () => {
    const { container } = render(<ScoreBar score={30} />);
    const fill = container.querySelector('[style]');
    expect(fill?.className).toContain('bg-red-500');
  });

  it('shows label number by default', () => {
    render(<ScoreBar score={55} />);
    expect(screen.getByText('55')).toBeInTheDocument();
  });

  it('hides label when showLabel=false', () => {
    render(<ScoreBar score={55} showLabel={false} />);
    expect(screen.queryByText('55')).not.toBeInTheDocument();
  });
});
