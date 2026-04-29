'use client';
// frontend/src/components/ui/SearchInput.tsx
// Search input with optional Ctrl+K shortcut visual
// Two modes: 'inline' (real input) and 'trigger' (button that fires onTriggerClick)
import { useEffect, useState } from 'react';
import { cn } from '@/lib/cn';

export interface SearchInputProps {
  value?: string;
  defaultValue?: string;
  onChange?: (value: string) => void;
  onSubmit?: (value: string) => void;
  placeholder?: string;
  showShortcut?: boolean;
  shortcut?: string;
  size?: 'sm' | 'md' | 'lg';
  variant?: 'inline' | 'trigger';
  onTriggerClick?: () => void;
  autoFocus?: boolean;
  className?: string;
  ariaLabel?: string;
}

const SIZE_CLASSES = {
  sm: 'h-8 text-xs px-2',
  md: 'h-9 text-sm px-3',
  lg: 'h-10 text-base px-4',
};

function detectShortcut(): string {
  if (typeof navigator !== 'undefined' && /Mac/i.test(navigator.platform)) return '⌘K';
  return 'Ctrl K';
}

function SearchIcon() {
  return (
    <svg
      className="w-4 h-4 text-gray-500 shrink-0"
      fill="none"
      stroke="currentColor"
      viewBox="0 0 24 24"
      aria-hidden="true"
    >
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth={2}
        d="M21 21l-4.35-4.35M11 19a8 8 0 100-16 8 8 0 000 16z"
      />
    </svg>
  );
}

export function SearchInput({
  value,
  defaultValue,
  onChange,
  onSubmit,
  placeholder = 'Buscar...',
  showShortcut,
  shortcut,
  size = 'md',
  variant = 'inline',
  onTriggerClick,
  autoFocus,
  className,
  ariaLabel = 'Buscar',
}: SearchInputProps) {
  const [localShortcut, setLocalShortcut] = useState<string | undefined>(shortcut);

  useEffect(() => {
    if (!shortcut) setLocalShortcut(detectShortcut());
  }, [shortcut]);

  const wrapperBase = cn(
    'inline-flex items-center gap-2 w-full bg-white border border-gray-200 rounded-lg',
    'focus-within:border-vitao-green focus-within:ring-2 focus-within:ring-vitao-green/20',
    'transition-colors',
    SIZE_CLASSES[size],
    className,
  );

  if (variant === 'trigger') {
    return (
      <button
        type="button"
        onClick={onTriggerClick}
        aria-label={ariaLabel}
        className={cn(wrapperBase, 'cursor-pointer hover:border-gray-300 text-left')}
      >
        <SearchIcon />
        <span className="flex-1 text-gray-500">{placeholder}</span>
        {(showShortcut ?? true) && (
          <kbd className="hidden sm:inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-xs font-semibold text-gray-500 bg-gray-100 border border-gray-200">
            {localShortcut}
          </kbd>
        )}
      </button>
    );
  }

  return (
    <div className={wrapperBase}>
      <SearchIcon />
      <input
        type="search"
        value={value}
        defaultValue={defaultValue}
        autoFocus={autoFocus}
        onChange={(e) => onChange?.(e.target.value)}
        onKeyDown={(e) => {
          if (e.key === 'Enter') onSubmit?.((e.target as HTMLInputElement).value);
        }}
        placeholder={placeholder}
        aria-label={ariaLabel}
        className="flex-1 bg-transparent border-0 outline-none text-gray-900 placeholder:text-gray-400"
      />
      {showShortcut && (
        <kbd className="hidden sm:inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-xs font-semibold text-gray-500 bg-gray-100 border border-gray-200">
          {localShortcut}
        </kbd>
      )}
    </div>
  );
}
