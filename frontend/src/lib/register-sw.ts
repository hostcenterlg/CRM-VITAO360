// CRM VITAO360 — Service Worker registration
// Called once on mount from AppShell via useEffect
// Safe to call multiple times (navigator.serviceWorker.register is idempotent)

export function registerServiceWorker(): void {
  if (typeof window === 'undefined') return;
  if (!('serviceWorker' in navigator)) return;

  window.addEventListener('load', () => {
    navigator.serviceWorker
      .register('/sw.js')
      .then((registration) => {
        // Check for updates every 30 minutes
        setInterval(() => registration.update(), 30 * 60 * 1000);
      })
      .catch((err) => {
        // Non-fatal — app works without SW
        console.warn('[SW] Registration failed:', err);
      });
  });
}
