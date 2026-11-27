// Bump the shell whenever a released public workflow changes. That makes an
// already-installed app fetch the new worker and retire stale public pages.
// The worker activates in the background but never reloads an open workflow.
const SHELL_CACHE = 'homeofferflow-shell-v238';
const SHELL_ASSETS = [
  // Keep installation lightweight. Public pages cache after the visitor has
  // actually opened them; preloading every guide would spend bandwidth for
  // pages most visitors never use.
  '/manifest.webmanifest',
  '/assets/pwa-register.js',
  '/assets/build-readiness-checklist.js',
  '/assets/pwa-share-target.js',
  '/assets/under-contract-companion.js',
  '/assets/trec-62-followup.js',
  '/assets/trec-38-8-followup.js',
  '/assets/trec-39-11-amendment.js',
  '/assets/seller-disclosure-interview.js',
  '/assets/saved-disclosure-attachment.js?v=20261022-summary1',
  '/assets/agent-landing-focus.css',
  '/assets/agent-landing-focus.js',
  '/assets/agent-build-readiness-share.css',
  '/assets/agent-build-readiness-share.js',
  '/assets/partner-landing-focus.css',
  '/assets/partner-landing-focus.js',
  '/assets/partner-profile.js?v=20261106-lookup-timeout',
  '/assets/partner-profile.css?v=20261021-portrait1',
  '/assets/inspection-partners.js?v=20261118-partner-retry-status',
  '/assets/insurance-partners.js?v=20261118-partner-retry-status',
  '/assets/inspection-partners.css?v=20261118-partner-retry-status',
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
  '/partners', '/directory', '/ondemand', '/texas-fsbo-guide', '/build-readiness',
  '/texas-seller-offer-review',
  '/texas-agent-offer-workflow', '/texas-homebuyer-offer-guide',
  '/texas-lease-offer-workflow',
  '/texas-listing-workflow',
  '/texas-agent-form-library',
  '/texas-seller-financing-guide',
  '/texas-buyer-representation-guide',
  '/texas-flat-fee-mls-guide',
  '/texas-seller-net-proceeds-calculator',
  '/texas-fsbo-closing-checklist',
  '/texas-investor-offer-guide',
  '/texas-home-service-partner-guide'
]);

// Cache only the two public Build Readiness hero images, and only after a
// visitor requests them. Do not preload them for every installed user.
const OFFLINE_PUBLIC_IMAGE_PATHS = new Set([
  '/assets/build-readiness-blueprint-banner.jpg',
  '/assets/build-readiness-blueprint-mobile.jpg'
]);

self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(SHELL_CACHE)
      .then(cache => cache.addAll(SHELL_ASSETS))
      .then(() => self.skipWaiting())
  );
});

// Keep compatibility with a previously installed worker that is already
// waiting for the older explicit-update message.
self.addEventListener('message', event => {
  if (event.data?.type === 'HOF_SKIP_WAITING') self.skipWaiting();
});

self.addEventListener('activate', event => {
  event.waitUntil(
    Promise.all([
      caches.keys().then(keys => Promise.all(
        keys.filter(key => key.startsWith('homeofferflow-shell-') && key !== SHELL_CACHE)
          .map(key => caches.delete(key))
      )),
      self.clients.claim()
    ])
  );
});

self.addEventListener('fetch', event => {
  if (event.request.method !== 'GET') return;
  const requestUrl = new URL(event.request.url);

  // Never cache API, authenticated, signed-document, or third-party requests.
  if (requestUrl.origin !== self.location.origin || requestUrl.pathname.startsWith('/api/')) return;

  if (event.request.mode !== 'navigate' &&
      SHELL_ASSETS.includes(requestUrl.pathname + requestUrl.search) &&
      !event.request.headers.has('Authorization') && !event.request.headers.has('Range')) {
    event.respondWith(fetch(event.request).catch(async error => {
      const cache = await caches.open(SHELL_CACHE);
      const cached = await cache.match(event.request);
      if (cached) return cached;
      throw error;
    }));
    return;
  }

  if (OFFLINE_PUBLIC_IMAGE_PATHS.has(requestUrl.pathname) && !requestUrl.search &&
      !event.request.headers.has('Authorization') && !event.request.headers.has('Range')) {
    event.respondWith((async () => {
      const cache = await caches.open(SHELL_CACHE);
      const cached = await cache.match(event.request);
      try {
        const response = await fetch(event.request);
        const contentType = response.headers.get('content-type') || '';
        if (response.ok && contentType.startsWith('image/')) {
          await cache.put(event.request, response.clone());
          return response;
        }
        return cached || response;
      } catch (error) {
        if (cached) return cached;
        throw error;
      }
    })());
    return;
  }

  // The shell stays network-first and bypasses the browser HTTP cache, so a
  // completed deploy is visible immediately even when the prior public page
  // was recently opened in an installed app or browser tab.
  // Refresh the cached *public* HTML shell after a successful navigation. That
  // lets a recently used installed app open the current interface when it goes
  // offline, without ever caching API, document, or account-specific responses.
  // Only navigation requests can fall back to cached HTML while offline.
  if (event.request.mode === 'navigate') {
    const networkResponse = fetch(event.request, { cache: 'no-store' });
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
        const offlineCopy = response.clone();
        return caches.open(SHELL_CACHE).then(cache => cache.put(cacheKey, offlineCopy));
      }).catch(() => undefined)
    );
  }
});
