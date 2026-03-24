'use client';

import { useState } from 'react';
import Sidebar, { HamburgerButton } from './Sidebar';

// ---------------------------------------------------------------------------
// AppShell — wraps sidebar + header + main content
// Client component because sidebar state is interactive
// ---------------------------------------------------------------------------

interface AppShellProps {
  children: React.ReactNode;
  pageTitle?: string;
}

export default function AppShell({ children, pageTitle }: AppShellProps) {
  const [sidebarOpen, setSidebarOpen] = useState(false);

  return (
    <div className="flex h-screen overflow-hidden bg-gray-50">
      {/* Sidebar */}
      <Sidebar
        mobileOpen={sidebarOpen}
        onClose={() => setSidebarOpen(false)}
      />

      {/* Main column */}
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        {/* Top header */}
        <header className="flex-shrink-0 bg-white border-b border-gray-200 px-4 py-3 flex items-center gap-3">
          <HamburgerButton onClick={() => setSidebarOpen(true)} />
          {pageTitle && (
            <h1 className="text-base font-semibold text-gray-900">{pageTitle}</h1>
          )}
        </header>

        {/* Scrollable page content */}
        <main className="flex-1 overflow-y-auto scrollbar-thin">
          <div className="max-w-screen-2xl mx-auto p-4 lg:p-6">
            {children}
          </div>
        </main>
      </div>
    </div>
  );
}
