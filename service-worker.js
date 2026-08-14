const SHELL_CACHE = 'homeofferflow-shell-v9';
const SHELL_ASSETS = [
  '/',
  '/index.html',
  '/manifest.webmanifest',
  '/assets/homeofferflow-app-icon.svg',
  '/assets/homeofferflow-app-icon-192.png',
  '/assets/homeofferflow-app-icon-512.png',
  '/assets/homeofferflow-apple-touch-icon.png'
];

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
    event.respondWith(networkResponse.catch(() => caches.match('/index.html')));
    event.waitUntil(
      networkResponse.then(response => {
        const contentType = response.headers.get('content-type') || '';
        if (!response.ok || !contentType.includes('text/html')) return;
        return caches.open(SHELL_CACHE).then(cache => cache.put('/index.html', response.clone()));
      }).catch(() => undefined)
    );
  }
});
