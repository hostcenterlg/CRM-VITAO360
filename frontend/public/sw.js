// CRM VITAO360 — Service Worker v1
// Strategy: network-first with cache fallback for pages/assets
// API calls: NEVER cached (Two-Base Architecture requires fresh data)

const CACHE_NAME = 'crm-vitao360-v1';
const PRECACHE_URLS = ['/', '/login', '/agenda', '/carteira'];

// ---------------------------------------------------------------------------
// Install — pre-cache critical pages
// ---------------------------------------------------------------------------
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      return cache.addAll(PRECACHE_URLS).catch((err) => {
        // Non-fatal: pre-cache may fail if the server is not reachable during install
        console.warn('[SW] Pre-cache failed (non-fatal):', err);
      });
    })
  );
  // Activate immediately without waiting for old SW to be removed
  self.skipWaiting();
});

// ---------------------------------------------------------------------------
// Activate — clean up old caches
// ---------------------------------------------------------------------------
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(
        keys
          .filter((key) => key !== CACHE_NAME)
          .map((key) => caches.delete(key))
      )
    )
  );
  // Take control of all clients immediately
  self.clients.claim();
});

// ---------------------------------------------------------------------------
// Fetch — network-first, cache fallback for pages/assets
// API calls ALWAYS go to network only — never cache business data
// ---------------------------------------------------------------------------
self.addEventListener('fetch', (event) => {
  const url = event.request.url;

  // Skip non-GET requests
  if (event.request.method !== 'GET') return;

  // Skip chrome-extension and non-http requests
  if (!url.startsWith('http')) return;

  // API calls: network only — NEVER cache (fresh data mandatory)
  if (
    url.includes('/api/') ||
    url.includes('vercel.app/api') ||
    url.includes('/_next/webpack-hmr') ||
    url.includes('/__nextjs_original-stack-frame')
  ) {
    return; // Let the browser handle it natively
  }

  // Pages and static assets: network first, cache fallback
  event.respondWith(
    fetch(event.request)
      .then((response) => {
        // Only cache successful responses
        if (response && response.status === 200) {
          const clone = response.clone();
          caches.open(CACHE_NAME).then((cache) => {
            cache.put(event.request, clone);
          });
        }
        return response;
      })
      .catch(() => {
        // Network failed — try cache
        return caches.match(event.request).then((cached) => {
          if (cached) return cached;
          // No cache for this URL — return a minimal offline response for navigation requests
          if (event.request.mode === 'navigate') {
            return caches.match('/').then((root) => root ?? new Response('Offline', { status: 503 }));
          }
          return new Response('', { status: 503 });
        });
      })
  );
});
