'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';

// ---------------------------------------------------------------------------
// BottomNav — mobile-only fixed bottom navigation
// Visible only on mobile (md:hidden). 5 primary nav items.
// Active item: #00B050 green + label. Inactive: gray.
// Safe area support for iPhones (env(safe-area-inset-bottom))
// ---------------------------------------------------------------------------

interface NavItem {
  href: string;
  label: string;
  icon: (active: boolean) => React.ReactNode;
  matchPrefixes?: string[];
}

const NAV_ITEMS: NavItem[] = [
  {
    href: '/',
    label: 'Dashboard',
    matchPrefixes: ['/'],
    icon: (active) => (
      <svg
        className="w-5 h-5"
        fill={active ? '#00B050' : 'none'}
        stroke={active ? '#00B050' : '#9CA3AF'}
        viewBox="0 0 24 24"
        aria-hidden="true"
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={active ? 0 : 1.8}
          d={
            active
              ? 'M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6'
              : 'M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6'
          }
        />
      </svg>
    ),
  },
  {
    href: '/carteira',
    label: 'Carteira',
    icon: (active) => (
      <svg
        className="w-5 h-5"
        fill={active ? '#00B050' : 'none'}
        stroke={active ? '#00B050' : '#9CA3AF'}
        viewBox="0 0 24 24"
        aria-hidden="true"
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={active ? 0 : 1.8}
          d={
            active
              ? 'M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0z'
              : 'M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0z'
          }
        />
      </svg>
    ),
  },
  {
    href: '/agenda',
    label: 'Agenda',
    icon: (active) => (
      <svg
        className="w-5 h-5"
        fill={active ? '#00B050' : 'none'}
        stroke={active ? '#00B050' : '#9CA3AF'}
        viewBox="0 0 24 24"
        aria-hidden="true"
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={active ? 0 : 1.8}
          d={
            active
              ? 'M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z'
              : 'M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z'
          }
        />
      </svg>
    ),
  },
  {
    href: '/ia',
    label: 'IA',
    icon: (active) => (
      <svg
        className="w-5 h-5"
        fill={active ? '#00B050' : 'none'}
        stroke={active ? '#00B050' : '#9CA3AF'}
        viewBox="0 0 24 24"
        aria-hidden="true"
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={active ? 0 : 1.8}
          d={
            active
              ? 'M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z'
              : 'M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z'
          }
        />
      </svg>
    ),
  },
  {
    href: '/inbox',
    label: 'Inbox',
    icon: (active) => (
      <svg
        className="w-5 h-5"
        fill={active ? '#00B050' : 'none'}
        stroke={active ? '#00B050' : '#9CA3AF'}
        viewBox="0 0 24 24"
        aria-hidden="true"
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={active ? 0 : 1.8}
          d={
            active
              ? 'M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z'
              : 'M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z'
          }
        />
      </svg>
    ),
  },
];

function isActive(pathname: string, item: NavItem): boolean {
  if (item.href === '/') {
    return pathname === '/';
  }
  return pathname.startsWith(item.href);
}

export default function BottomNav() {
  const pathname = usePathname();

  return (
    <nav
      className="md:hidden fixed bottom-0 left-0 right-0 z-30 bg-white border-t border-gray-200 shadow-sm"
      style={{ paddingBottom: 'env(safe-area-inset-bottom, 0px)' }}
      aria-label="Navegacao principal mobile"
    >
      <div className="flex items-stretch h-14">
        {NAV_ITEMS.map((item) => {
          const active = isActive(pathname, item);
          return (
            <Link
              key={item.href}
              href={item.href}
              aria-label={item.label}
              aria-current={active ? 'page' : undefined}
              className="flex-1 flex flex-col items-center justify-center gap-0.5 min-w-0 touch-manipulation
                         transition-colors duration-150 active:bg-gray-50"
            >
              {item.icon(active)}
              <span
                className="text-[10px] font-semibold leading-none truncate"
                style={{ color: active ? '#00B050' : '#9CA3AF' }}
              >
                {item.label}
              </span>
            </Link>
          );
        })}
      </div>
    </nav>
  );
}
