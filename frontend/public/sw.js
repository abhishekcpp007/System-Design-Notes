/**
 * Service Worker — Offline-first caching strategy
 * 
 * Strategies:
 * - Cache First: Static assets (fonts, images, CSS/JS bundles)
 * - Network First: API responses (fresh data preferred, cached fallback)
 * - Stale-While-Revalidate: Blog posts, project data (show cached, update bg)
 * 
 * Features:
 * - Offline support with cached content
 * - Background sync for form submissions
 * - Push notification support
 * - Automatic cache versioning and cleanup
 */

const CACHE_VERSION = 'v1';
const STATIC_CACHE = `portfolio-static-${CACHE_VERSION}`;
const DYNAMIC_CACHE = `portfolio-dynamic-${CACHE_VERSION}`;
const API_CACHE = `portfolio-api-${CACHE_VERSION}`;

// Static assets to pre-cache on install
const PRECACHE_URLS = [
  '/',
  '/projects',
  '/blog',
  '/contact',
  '/offline',
];

// URL patterns for different caching strategies
const CACHE_STRATEGIES = {
  cacheFirst: [
    /\.(woff2?|ttf|eot)$/,  // Fonts
    /\.(png|jpg|jpeg|gif|svg|webp|ico)$/, // Images
    /\/_next\/static\//,  // Next.js static chunks
  ],
  networkFirst: [
    /\/api\/v1\//,  // API calls
  ],
  staleWhileRevalidate: [
    /\/_next\/data\//,  // Next.js ISR data
    /\/manifest\.json$/,
  ],
};

// ─── Install Event ─────────────────────────────────────────────────────────

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(STATIC_CACHE).then((cache) => {
      return cache.addAll(PRECACHE_URLS).catch((err) => {
        console.warn('[SW] Precache failed for some URLs:', err);
      });
    })
  );
  // Activate immediately without waiting for old service worker
  self.skipWaiting();
});

// ─── Activate Event ────────────────────────────────────────────────────────

self.addEventListener('activate', (event) => {
  event.waitUntil(
    // Clean up old caches from previous versions
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames
          .filter((name) => {
            return name.startsWith('portfolio-') && 
                   name !== STATIC_CACHE && 
                   name !== DYNAMIC_CACHE && 
                   name !== API_CACHE;
          })
          .map((name) => caches.delete(name))
      );
    })
  );
  // Take control of all open tabs
  self.clients.claim();
});

// ─── Fetch Event ───────────────────────────────────────────────────────────

self.addEventListener('fetch', (event) => {
  const { request } = event;
  const url = new URL(request.url);

  // Skip non-GET requests (let mutations go through normally)
  if (request.method !== 'GET') {
    return;
  }

  // Skip WebSocket connections
  if (url.protocol === 'ws:' || url.protocol === 'wss:') {
    return;
  }

  // Skip chrome-extension and other non-http
  if (!url.protocol.startsWith('http')) {
    return;
  }

  // Determine caching strategy
  const strategy = getStrategy(url);

  switch (strategy) {
    case 'cacheFirst':
      event.respondWith(cacheFirst(request));
      break;
    case 'networkFirst':
      event.respondWith(networkFirst(request));
      break;
    case 'staleWhileRevalidate':
      event.respondWith(staleWhileRevalidate(request));
      break;
    default:
      // Network-first for everything else (pages)
      event.respondWith(networkFirst(request));
  }
});

// ─── Caching Strategies ────────────────────────────────────────────────────

/**
 * Cache First: Best for static assets that don't change.
 * Check cache → if miss, fetch from network and cache.
 */
async function cacheFirst(request) {
  const cached = await caches.match(request);
  if (cached) return cached;

  try {
    const response = await fetch(request);
    if (response.ok) {
      const cache = await caches.open(STATIC_CACHE);
      cache.put(request, response.clone());
    }
    return response;
  } catch {
    return offlineFallback(request);
  }
}

/**
 * Network First: Best for API data where freshness matters.
 * Try network → if fails, serve from cache.
 */
async function networkFirst(request) {
  try {
    const response = await fetch(request);
    
    // Cache successful API responses
    if (response.ok && request.url.includes('/api/')) {
      const cache = await caches.open(API_CACHE);
      cache.put(request, response.clone());
    }
    
    // Cache successful page navigations
    if (response.ok && response.headers.get('content-type')?.includes('text/html')) {
      const cache = await caches.open(DYNAMIC_CACHE);
      cache.put(request, response.clone());
    }
    
    return response;
  } catch {
    // Network failed — try cache
    const cached = await caches.match(request);
    if (cached) return cached;
    
    return offlineFallback(request);
  }
}

/**
 * Stale While Revalidate: Best for content that can be slightly stale.
 * Return cached immediately, update cache in background.
 */
async function staleWhileRevalidate(request) {
  const cached = await caches.match(request);
  
  // Fetch fresh version in background regardless
  const fetchPromise = fetch(request)
    .then((response) => {
      if (response.ok) {
        const cache = caches.open(DYNAMIC_CACHE).then((c) => {
          c.put(request, response.clone());
        });
      }
      return response;
    })
    .catch(() => null);

  // Return cached version immediately if available
  if (cached) return cached;
  
  // No cache — wait for network
  const response = await fetchPromise;
  if (response) return response;
  
  return offlineFallback(request);
}

// ─── Helpers ───────────────────────────────────────────────────────────────

function getStrategy(url) {
  const fullUrl = url.href;
  const pathname = url.pathname;

  for (const pattern of CACHE_STRATEGIES.cacheFirst) {
    if (pattern.test(fullUrl) || pattern.test(pathname)) return 'cacheFirst';
  }
  for (const pattern of CACHE_STRATEGIES.networkFirst) {
    if (pattern.test(fullUrl) || pattern.test(pathname)) return 'networkFirst';
  }
  for (const pattern of CACHE_STRATEGIES.staleWhileRevalidate) {
    if (pattern.test(fullUrl) || pattern.test(pathname)) return 'staleWhileRevalidate';
  }
  
  return 'networkFirst'; // Default
}

function offlineFallback(request) {
  // Return offline page for navigation requests
  if (request.mode === 'navigate') {
    return caches.match('/offline') || new Response(
      '<html><body><h1>Offline</h1><p>Please check your connection.</p></body></html>',
      { headers: { 'Content-Type': 'text/html' } }
    );
  }
  
  // Return empty response for other requests
  return new Response('', { status: 503, statusText: 'Offline' });
}

// ─── Background Sync ───────────────────────────────────────────────────────

self.addEventListener('sync', (event) => {
  if (event.tag === 'contact-form') {
    event.waitUntil(syncContactForm());
  }
});

async function syncContactForm() {
  // Retrieve queued form submissions from IndexedDB
  // (Implementation would use idb-keyval or similar)
  console.log('[SW] Syncing contact form submissions...');
}

// ─── Push Notifications ────────────────────────────────────────────────────

self.addEventListener('push', (event) => {
  if (!event.data) return;

  const data = event.data.json();
  
  event.waitUntil(
    self.registration.showNotification(data.title || 'Portfolio Update', {
      body: data.body || '',
      icon: '/images/icon-192.png',
      badge: '/images/icon-192.png',
      data: { url: data.url || '/' },
      actions: [
        { action: 'open', title: 'View' },
        { action: 'dismiss', title: 'Dismiss' },
      ],
    })
  );
});

self.addEventListener('notificationclick', (event) => {
  event.notification.close();
  
  if (event.action === 'dismiss') return;
  
  const url = event.notification.data?.url || '/';
  event.waitUntil(
    self.clients.matchAll({ type: 'window' }).then((clients) => {
      // Focus existing tab or open new one
      const existingClient = clients.find((c) => c.url === url);
      if (existingClient) {
        return existingClient.focus();
      }
      return self.clients.openWindow(url);
    })
  );
});
