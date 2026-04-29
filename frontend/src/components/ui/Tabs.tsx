'use client';
// frontend/src/components/ui/Tabs.tsx
// Pill navigation tabs — active: bg-vitao-green text-white
import { cn } from '@/lib/cn';
import type { ReactNode } from 'react';

export interface TabItem {
  id: string;
  label: string;
  count?: number;
  icon?: ReactNode;
  disabled?: boolean;
}

export interface TabsProps {
  tabs: TabItem[];
  activeId: string;
  onChange: (id: string) => void;
  size?: 'sm' | 'md';
  fullWidth?: boolean;
  className?: string;
  ariaLabel?: string;
}

const TAB_BASE =
  'inline-flex items-center gap-1.5 font-medium rounded-full transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-vitao-green focus-visible:ring-offset-1';

const TAB_SIZE = {
  sm: 'text-xs px-3 py-1',
  md: 'text-sm px-4 py-1.5',
};

export function Tabs({
  tabs,
  activeId,
  onChange,
  size = 'md',
  fullWidth,
  className,
  ariaLabel,
}: TabsProps) {
  return (
    <div
      role="tablist"
      aria-label={ariaLabel ?? 'Navegação por abas'}
      className={cn('inline-flex items-center gap-2 flex-wrap', fullWidth && 'w-full', className)}
    >
      {tabs.map((t) => {
        const active = t.id === activeId;
        return (
          <button
            key={t.id}
            type="button"
            role="tab"
            aria-selected={active}
            aria-controls={`panel-${t.id}`}
            id={`tab-${t.id}`}
            disabled={t.disabled}
            onClick={() => !t.disabled && onChange(t.id)}
            className={cn(
              TAB_BASE,
              TAB_SIZE[size],
              active
                ? 'bg-vitao-green text-white shadow-sm'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200',
              t.disabled && 'opacity-40 cursor-not-allowed',
            )}
          >
            {t.icon && <span aria-hidden="true">{t.icon}</span>}
            <span>{t.label}</span>
            {typeof t.count === 'number' && (
              <span
                className={cn(
                  'inline-flex items-center justify-center min-w-[20px] h-5 px-1.5 rounded-full text-[10px] font-bold tabular-nums',
                  active ? 'bg-white/25 text-white' : 'bg-gray-300/60 text-gray-700',
                )}
              >
                {t.count > 99 ? '99+' : t.count}
              </span>
            )}
          </button>
        );
      })}
    </div>
  );
}
