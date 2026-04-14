import { describe, it, expect } from 'vitest';
import { render } from '@testing-library/react';
import Skeleton, { SkeletonText, SkeletonKpi, SkeletonTableRow } from '@/components/Skeleton';

describe('Skeleton', () => {
  describe('Skeleton.Text', () => {
    it('renderiza div com animate-pulse para linha única', () => {
      const { container } = render(<SkeletonText />);
      const el = container.querySelector('.animate-pulse');
      expect(el).toBeInTheDocument();
    });

    it('renderiza aria-hidden="true" para não poluir leitores de tela', () => {
      const { container } = render(<SkeletonText />);
      expect(container.querySelector('[aria-hidden="true"]')).toBeInTheDocument();
    });

    it('renderiza múltiplas linhas quando lines > 1', () => {
      const { container } = render(<SkeletonText lines={3} />);
      const pulseBlocks = container.querySelectorAll('.animate-pulse');
      expect(pulseBlocks.length).toBe(3);
    });

    it('última linha tem largura reduzida com múltiplas linhas (truncação visual)', () => {
      const { container } = render(<SkeletonText lines={2} />);
      const blocks = container.querySelectorAll('[aria-hidden="true"] > div');
      const lastBlock = blocks[blocks.length - 1] as HTMLElement;
      expect(lastBlock.style.width).toBe('70%');
    });
  });

  describe('Skeleton.Kpi', () => {
    it('renderiza estrutura de card com 3 blocos de shimmer', () => {
      const { container } = render(<SkeletonKpi />);
      const pulseBlocks = container.querySelectorAll('.animate-pulse');
      // O container do Kpi não tem animate-pulse, mas os SkeletonBlock internos têm
      expect(pulseBlocks.length).toBeGreaterThanOrEqual(3);
    });

    it('renderiza com borda esquerda no estilo KpiCard', () => {
      const { container } = render(<SkeletonKpi />);
      const card = container.firstChild as HTMLElement;
      expect(card).toHaveStyle({ borderLeftWidth: '4px' });
    });

    it('não é perceptível por leitores de tela (aria-hidden)', () => {
      const { container } = render(<SkeletonKpi />);
      const card = container.firstChild as HTMLElement;
      expect(card).toHaveAttribute('aria-hidden', 'true');
    });
  });

  describe('Skeleton.TableRow', () => {
    it('renderiza uma linha de tabela (<tr>) por padrão', () => {
      const { container } = render(
        <table>
          <tbody>
            <SkeletonTableRow />
          </tbody>
        </table>
      );
      const rows = container.querySelectorAll('tr');
      expect(rows.length).toBe(1);
    });

    it('renderiza número correto de colunas via prop columns', () => {
      const { container } = render(
        <table>
          <tbody>
            <SkeletonTableRow columns={4} />
          </tbody>
        </table>
      );
      const cells = container.querySelectorAll('td');
      expect(cells.length).toBe(4);
    });

    it('renderiza múltiplas linhas via prop rows', () => {
      const { container } = render(
        <table>
          <tbody>
            <SkeletonTableRow rows={3} />
          </tbody>
        </table>
      );
      const rows = container.querySelectorAll('tr');
      expect(rows.length).toBe(3);
    });

    it('usa o namespace Skeleton.TableRow corretamente', () => {
      const { container } = render(
        <table>
          <tbody>
            <Skeleton.TableRow columns={6} />
          </tbody>
        </table>
      );
      const cells = container.querySelectorAll('td');
      expect(cells.length).toBe(6);
    });
  });

  describe('Skeleton namespace completo', () => {
    it('Skeleton.Block renderiza com animate-pulse', () => {
      const { container } = render(<Skeleton.Block />);
      expect(container.querySelector('.animate-pulse')).toBeInTheDocument();
    });

    it('Skeleton.Card renderiza container com espaço interno', () => {
      const { container } = render(<Skeleton.Card />);
      const card = container.firstChild as HTMLElement;
      expect(card).toBeInTheDocument();
    });
  });
});
