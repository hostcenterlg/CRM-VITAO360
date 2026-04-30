// frontend/src/components/ui/EmptyState.tsx
// Standard empty-state block with icon, title, optional subtitle and CTA.
// Usage: <EmptyState title="Nenhum cliente" subtitle="Tente ajustar os filtros" />

import { cn } from '@/lib/cn';
import type { ReactNode } from 'react';

export interface EmptyStateProps {
  /** Primary message */
  title: string;
  /** Secondary message */
  subtitle?: string;
  /** Optional SVG/icon node. If omitted, renders a generic magnifier. */
  icon?: ReactNode;
  /** Optional CTA button or link */
  action?: ReactNode;
  className?: string;
  /** Size variant */
  size?: 'sm' | 'md' | 'lg';
}

const SIZE_ICON: Record<NonNullable<EmptyStateProps['size']>, string> = {
  sm: 'w-8 h-8',
  md: 'w-12 h-12',
  lg: 'w-16 h-16',
};

const SIZE_TITLE: Record<NonNullable<EmptyStateProps['size']>, string> = {
  sm: 'text-sm',
  md: 'text-base',
  lg: 'text-lg',
};

const SIZE_SUBTITLE: Record<NonNullable<EmptyStateProps['size']>, string> = {
  sm: 'text-xs',
  md: 'text-sm',
  lg: 'text-sm',
};

function DefaultIcon({ className }: { className: string }) {
  return (
    <svg
      className={cn('text-gray-300', className)}
      fill="none"
      stroke="currentColor"
      viewBox="0 0 24 24"
      aria-hidden="true"
    >
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth={1.5}
        d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
      />
    </svg>
  );
}

export function EmptyState({
  title,
  subtitle,
  icon,
  action,
  className,
  size = 'md',
}: EmptyStateProps) {
  return (
    <div
      className={cn(
        'flex flex-col items-center justify-center gap-3 py-10 px-4 text-center',
        className,
      )}
      role="status"
      aria-label={title}
    >
      <div className={cn('text-gray-300', SIZE_ICON[size])}>
        {icon ?? <DefaultIcon className={SIZE_ICON[size]} />}
      </div>
      <p className={cn('font-semibold text-gray-700', SIZE_TITLE[size])}>{title}</p>
      {subtitle && (
        <p className={cn('text-gray-500', SIZE_SUBTITLE[size])}>{subtitle}</p>
      )}
      {action && <div className="mt-1">{action}</div>}
    </div>
  );
}
