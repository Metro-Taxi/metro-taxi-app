const CACHE_NAME = 'metro-taxi-v4';
const STATIC_CACHE = 'metro-taxi-static-v4';
const DYNAMIC_CACHE = 'metro-taxi-dynamic-v4';
const API_CACHE = 'metro-taxi-api-v3';

// Resources to cache immediately
const STATIC_ASSETS = [
  '/',
  '/index.html',
  '/offline.html',
  '/manifest.json',
  '/icons/icon-72x72.png',
  '/icons/icon-192x192.png',
  '/icons/icon-512x512.png',
  '/icons/favicon.ico'
];

// API endpoints to cache for offline use
const CACHEABLE_API_ROUTES = [
  '/api/auth/me',
  '/api/subscriptions/plans',
  '/api/rides/history',
  '/api/notifications'
];

// Listen for skip waiting message from main thread
self.addEventListener('message', (event) => {
  if (event.data && event.data.type === 'SKIP_WAITING') {
    console.log('[Service Worker] Received SKIP_WAITING, activating new version...');
    self.skipWaiting();
  }
});

// Install event - cache static assets
self.addEventListener('install', (event) => {
  console.log('[Service Worker] Installing v4...');
  event.waitUntil(
    caches.open(STATIC_CACHE)
      .then((cache) => {
        console.log('[Service Worker] Caching static assets');
        return cache.addAll(STATIC_ASSETS);
      })
      .then(() => {
        console.log('[Service Worker] Install complete');
        // Auto skip waiting for faster updates
        return self.skipWaiting();
      })
      .catch((error) => {
        console.error('[Service Worker] Install failed:', error);
      })
  );
});

// Activate event - clean old caches
self.addEventListener('activate', (event) => {
  console.log('[Service Worker] Activating...');
  event.waitUntil(
    caches.keys()
      .then((cacheNames) => {
        return Promise.all(
          cacheNames
            .filter((cacheName) => {
              return cacheName !== STATIC_CACHE && 
                     cacheName !== DYNAMIC_CACHE &&
                     cacheName !== API_CACHE &&
                     cacheName.startsWith('metro-taxi-');
            })
            .map((cacheName) => {
              console.log('[Service Worker] Deleting old cache:', cacheName);
              return caches.delete(cacheName);
            })
        );
      })
      .then(() => {
        console.log('[Service Worker] Claiming clients');
        return self.clients.claim();
      })
  );
});

// Fetch event - network first with cache fallback
self.addEventListener('fetch', (event) => {
  const { request } = event;
  const url = new URL(request.url);

  // Skip non-GET requests
  if (request.method !== 'GET') {
    return;
  }

  // Skip WebSocket connections
  if (url.protocol === 'ws:' || url.protocol === 'wss:') {
    return;
  }

  // Skip external resources
  if (url.origin !== location.origin) {
    return;
  }

  // Handle API requests with stale-while-revalidate for cacheable routes
  if (url.pathname.startsWith('/api')) {
    const isCacheable = CACHEABLE_API_ROUTES.some(route => url.pathname.includes(route));
    
    if (isCacheable) {
      event.respondWith(
        caches.open(API_CACHE).then((cache) => {
          return fetch(request)
            .then((networkResponse) => {
              // Cache the fresh response
              cache.put(request, networkResponse.clone());
              return networkResponse;
            })
            .catch(() => {
              // Return cached response if network fails
              return cache.match(request).then((cachedResponse) => {
                if (cachedResponse) {
                  return cachedResponse;
                }
                return new Response(JSON.stringify({ error: 'Offline', cached: false }), {
                  status: 503,
                  headers: { 'Content-Type': 'application/json' }
                });
              });
            });
        })
      );
      return;
    }
    // Non-cacheable API calls - network only
    return;
  }

  event.respondWith(
    // Network first strategy for pages
    fetch(request)
      .then((response) => {
        // Clone the response before caching
        const responseClone = response.clone();
        
        // Cache successful responses
        if (response.status === 200) {
          caches.open(DYNAMIC_CACHE)
            .then((cache) => {
              cache.put(request, responseClone);
            });
        }
        
        return response;
      })
      .catch(() => {
        // If network fails, try cache
        return caches.match(request)
          .then((cachedResponse) => {
            if (cachedResponse) {
              return cachedResponse;
            }
            
            // Return offline page for navigation requests
            if (request.mode === 'navigate') {
              return caches.match('/offline.html');
            }
            
            return new Response('Offline', {
              status: 503,
              statusText: 'Service Unavailable'
            });
          });
      })
  );
});

// Handle push notifications
self.addEventListener('push', (event) => {
  console.log('[Service Worker] Push received');
  
  let notificationData = {
    title: 'Métro-Taxi',
    body: 'Nouvelle notification',
    icon: '/icons/icon-192x192.png',
    badge: '/icons/icon-72x72.png',
    data: {}
  };
  
  if (event.data) {
    try {
      const payload = event.data.json();
      notificationData = {
        title: payload.title || 'Métro-Taxi',
        body: payload.body || 'Nouvelle notification',
        icon: payload.icon || '/icons/icon-192x192.png',
        badge: payload.badge || '/icons/icon-72x72.png',
        data: payload.data || {}
      };
    } catch (e) {
      // If not JSON, use text
      notificationData.body = event.data.text();
    }
  }

  const options = {
    body: notificationData.body,
    icon: notificationData.icon,
    badge: notificationData.badge,
    vibrate: [100, 50, 100],
    data: notificationData.data,
    tag: 'metro-taxi-notification',
    renotify: true,
    actions: [
      { action: 'open', title: 'Ouvrir', icon: '/icons/icon-72x72.png' },
      { action: 'close', title: 'Fermer', icon: '/icons/icon-72x72.png' }
    ]
  };

  event.waitUntil(
    self.registration.showNotification(notificationData.title, options)
  );
});

// Handle notification clicks
self.addEventListener('notificationclick', (event) => {
  event.notification.close();

  const data = event.notification.data || {};
  let targetUrl = '/dashboard';
  
  // Navigate based on notification type
  if (data.type === 'subscription_expiry') {
    targetUrl = '/subscription';
  } else if (data.type === 'ride_accepted' || data.type === 'driver_arrived') {
    targetUrl = '/dashboard';
  }

  if (event.action === 'open' || event.action === '' || !event.action) {
    event.waitUntil(
      clients.matchAll({ type: 'window', includeUncontrolled: true })
        .then((clientList) => {
          // If a window is already open, focus it
          for (const client of clientList) {
            if (client.url.includes(self.location.origin) && 'focus' in client) {
              client.navigate(targetUrl);
              return client.focus();
            }
          }
          // Otherwise open a new window
          if (clients.openWindow) {
            return clients.openWindow(targetUrl);
          }
        })
    );
  }
});

// Background sync (for future use)
self.addEventListener('sync', (event) => {
  if (event.tag === 'sync-rides') {
    event.waitUntil(syncRides());
  }
});

async function syncRides() {
  // Future: sync pending ride requests when back online
  console.log('[Service Worker] Syncing rides...');
}
