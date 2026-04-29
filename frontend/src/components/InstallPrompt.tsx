'use client';

import { useEffect, useState } from 'react';

// ---------------------------------------------------------------------------
// InstallPrompt — PWA install banner for mobile
// Detects beforeinstallprompt event, shows a discrete bottom banner.
// Hides permanently (localStorage) after install or dismiss.
// Only shown on mobile (viewport width < 768px).
// ---------------------------------------------------------------------------

const STORAGE_KEY = 'crm_pwa_install_dismissed';

interface BeforeInstallPromptEvent extends Event {
  prompt(): Promise<void>;
  userChoice: Promise<{ outcome: 'accepted' | 'dismissed' }>;
}

export default function InstallPrompt() {
  const [promptEvent, setPromptEvent] = useState<BeforeInstallPromptEvent | null>(null);
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    if (typeof window === 'undefined') return;

    // Already dismissed permanently
    try {
      if (localStorage.getItem(STORAGE_KEY) === 'true') return;
    } catch {
      return;
    }

    // Only show on mobile viewports
    const isMobile = window.matchMedia('(max-width: 767px)').matches;
    if (!isMobile) return;

    function handleBeforeInstall(e: Event) {
      e.preventDefault();
      setPromptEvent(e as BeforeInstallPromptEvent);
      setVisible(true);
    }

    window.addEventListener('beforeinstallprompt', handleBeforeInstall);
    return () => window.removeEventListener('beforeinstallprompt', handleBeforeInstall);
  }, []);

  function handleDismiss() {
    setVisible(false);
    try {
      localStorage.setItem(STORAGE_KEY, 'true');
    } catch {
      // Storage not available — banner hides for this session only
    }
  }

  async function handleInstall() {
    if (!promptEvent) return;
    await promptEvent.prompt();
    const choice = await promptEvent.userChoice;
    if (choice.outcome === 'accepted' || choice.outcome === 'dismissed') {
      handleDismiss();
    }
  }

  if (!visible) return null;

  return (
    <div
      role="banner"
      aria-live="polite"
      className="md:hidden fixed left-0 right-0 z-40 px-3 py-2"
      style={{
        bottom: 'calc(3.5rem + env(safe-area-inset-bottom, 0px))',
      }}
    >
      <div className="bg-white border border-gray-200 rounded-xl shadow-lg px-4 py-3 flex items-center gap-3">
        {/* App icon */}
        <div
          className="flex-shrink-0 w-10 h-10 rounded-xl flex items-center justify-center"
          style={{ backgroundColor: '#00B050' }}
          aria-hidden="true"
        >
          <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"
            />
          </svg>
        </div>

        {/* Text */}
        <div className="flex-1 min-w-0">
          <p className="text-sm font-semibold text-gray-900 leading-tight">Instalar CRM VITAO360</p>
          <p className="text-xs text-gray-500 mt-0.5">Acesso rapido direto na tela inicial</p>
        </div>

        {/* Actions */}
        <div className="flex items-center gap-2 flex-shrink-0">
          <button
            type="button"
            onClick={handleDismiss}
            aria-label="Dispensar banner de instalacao"
            className="p-1.5 text-gray-500 hover:text-gray-600 rounded-md transition-colors"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
          <button
            type="button"
            onClick={handleInstall}
            className="px-3 py-1.5 text-xs font-semibold text-white rounded-lg transition-colors touch-manipulation"
            style={{ backgroundColor: '#00B050' }}
          >
            Instalar
          </button>
        </div>
      </div>
    </div>
  );
}
