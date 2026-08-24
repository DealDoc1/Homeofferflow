// Bump the shell when manifest shortcuts or core install behavior changes so
// an already-installed agent receives the current app metadata immediately.
const SHELL_CACHE = 'homeofferflow-shell-v40';
const SHELL_ASSETS = [
  '/',
  '/index.html',
  '/agents',
  '/sellers',
  '/partners',
  '/ondemand',
  '/buyers',
  '/investors',
  '/directory',
  '/texas-fsbo-guide',
  '/texas-seller-offer-review',
  '/texas-agent-offer-workflow',
  '/texas-lease-offer-workflow',
  '/texas-listing-workflow',
  '/texas-agent-form-library',
  '/texas-homebuyer-offer-guide',
  '/texas-investor-offer-guide',
  '/manifest.webmanifest',
  '/assets/pwa-register.js',
  '/assets/agent-landing-focus.css',
  '/assets/agent-landing-focus.js',
  '/assets/partner-landing-focus.css',
  '/assets/partner-landing-focus.js',
  '/assets/homeofferflow-app-icon.svg',
  '/assets/homeofferflow-app-icon-192.png',
  '/assets/homeofferflow-app-icon-512.png',
  '/assets/homeofferflow-apple-touch-icon.png'
];
// These are public, non-account-specific pages. Cache each only after the
// browser has loaded it successfully, so an installed app can revisit the
// most recently used public workspace while offline. Never use this list for
// API, documents, authentication, or account-specific routes.
const PUBLIC_PAGE_PATHS = new Set([
  '/', '/index.html', '/buyers', '/agents', '/investors', '/sellers',
  '/partners', '/directory', '/ondemand', '/texas-fsbo-guide',
  '/texas-seller-offer-review',
  '/texas-agent-offer-workflow', '/texas-homebuyer-offer-guide',
  '/texas-lease-offer-workflow',
  '/texas-listing-workflow',
  '/texas-agent-form-library',
  '/texas-investor-offer-guide'
]);

self.addEventListener('install', event => {
  event.waitUntil(caches.open(SHELL_CACHE).then(cache => cache.addAll(SHELL_ASSETS)));
});

// A newer shell waits for an explicit in-app confirmation before taking over.
// That keeps an agent in control of a live field workflow while still making
// the update immediately available from the dashboard notification.
self.addEventListener('message', event => {
  if (event.data?.type === 'HOF_SKIP_WAITING') self.skipWaiting();
});

self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys().then(keys => Promise.all(
      keys.filter(key => key.startsWith('homeofferflow-shell-') && key !== SHELL_CACHE)
        .map(key => caches.delete(key))
    ))
  );
  self.clients.claim();
});

self.addEventListener('fetch', event => {
  if (event.request.method !== 'GET') return;
  const requestUrl = new URL(event.request.url);

  // Never cache API, authenticated, signed-document, or third-party requests.
  if (requestUrl.origin !== self.location.origin || requestUrl.pathname.startsWith('/api/')) return;

  // The shell stays network-first, so a completed deploy is visible immediately.
  // Refresh the cached *public* HTML shell after a successful navigation. That
  // lets a recently used installed app open the current interface when it goes
  // offline, without ever caching API, document, or account-specific responses.
  // Only a navigation request can fall back to the cached shell while offline.
  if (event.request.mode === 'navigate') {
    const networkResponse = fetch(event.request);
    const cacheKey = PUBLIC_PAGE_PATHS.has(requestUrl.pathname) ? requestUrl.pathname : '';
    event.respondWith(networkResponse.catch(() => (
      cacheKey
        ? caches.match(cacheKey).then(response => response || caches.match('/index.html'))
        : caches.match('/index.html')
    )));
    event.waitUntil(
      networkResponse.then(response => {
        const contentType = response.headers.get('content-type') || '';
        if (!cacheKey || !response.ok || !contentType.includes('text/html')) return;
        return caches.open(SHELL_CACHE).then(cache => cache.put(cacheKey, response.clone()));
      }).catch(() => undefined)
    );
  }
});
