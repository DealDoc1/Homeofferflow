const SHELL_CACHE = 'homeofferflow-shell-v3';
const SHELL_ASSETS = [
  '/',
  '/index.html',
  '/manifest.webmanifest',
  '/assets/homeofferflow-app-icon.svg'
];

self.addEventListener('install', event => {
  event.waitUntil(caches.open(SHELL_CACHE).then(cache => cache.addAll(SHELL_ASSETS)));
  self.skipWaiting();
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
  // Only a navigation request can fall back to the cached shell while offline.
  if (event.request.mode === 'navigate') {
    event.respondWith(fetch(event.request).catch(() => caches.match('/index.html')));
  }
});
