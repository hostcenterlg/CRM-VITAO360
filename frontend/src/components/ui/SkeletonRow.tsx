// frontend/src/components/ui/SkeletonRow.tsx
// Skeleton table row with variable column widths to simulate real content.
// Usage: replace loading rows with <SkeletonRow cols={[...]} /> to give
// visual hierarchy instead of uniform grey bars.

import { cn } from '@/lib/cn';

export interface SkeletonCol {
  /** Width as a fraction of parent (e.g. 0.4 = 40%) or fixed px string (e.g. '80px') */
  width?: number | string;
  align?: 'left' | 'right' | 'center';
}

export interface SkeletonRowProps {
  /** Column definitions. If omitted, renders 6 default columns. */
  cols?: SkeletonCol[];
  /** Extra classes applied to <tr> */
  className?: string;
  /** Cell vertical padding. Default py-3. */
  cellPy?: string;
}

const DEFAULT_COLS: SkeletonCol[] = [
  { width: '40px' },
  { width: '45%' },
  { width: '20%' },
  { width: '15%' },
  { width: '10%', align: 'right' },
  { width: '10%', align: 'right' },
];

export function SkeletonRow({ cols = DEFAULT_COLS, className, cellPy = 'py-3' }: SkeletonRowProps) {
  return (
    <tr className={cn('border-b border-gray-100 animate-pulse', className)}>
      {cols.map((col, i) => {
        const barWidth =
          typeof col.width === 'number'
            ? `${Math.round(col.width * 100)}%`
            : col.width ?? '60%';
        const align = col.align === 'right' ? 'ml-auto' : col.align === 'center' ? 'mx-auto' : '';
        return (
          <td key={i} className={cn('px-4', cellPy)}>
            <div
              className={cn('h-3 bg-gray-100 rounded', align)}
              style={{ width: barWidth }}
            />
          </td>
        );
      })}
    </tr>
  );
}

/** Renders N skeleton rows — convenience helper */
export function SkeletonRows({ count = 8, cols, className }: { count?: number; cols?: SkeletonCol[]; className?: string }) {
  return (
    <>
      {Array.from({ length: count }).map((_, i) => (
        <SkeletonRow key={i} cols={cols} className={className} />
      ))}
    </>
  );
}
