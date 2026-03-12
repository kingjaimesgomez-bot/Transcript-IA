// sw.js — Transcript IA Service Worker

const CACHE_NAME = 'transcript-ia-v1';

const ASSETS = [
  '/',
  '/index.html',
  '/assets/images/hero-bg.png',
  'https://fonts.googleapis.com/css2?family=Syne:wght@400;700;800&family=IBM+Plex+Mono:ital,wght@0,300;0,400;0,600&display=swap'
];

// Instalar — cachear assets
self.addEventListener('install', e => {
  e.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => cache.addAll(ASSETS))
      .then(() => self.skipWaiting())
  );
});

// Activar — limpiar caches viejos
self.addEventListener('activate', e => {
  e.waitUntil(
    caches.keys().then(keys =>
      Promise.all(
        keys.filter(k => k !== CACHE_NAME).map(k => caches.delete(k))
      )
    ).then(() => self.clients.claim())
  );
});

// Fetch — cache first, network fallback
self.addEventListener('fetch', e => {
  // No cachear llamadas al backend
  if (e.request.url.includes('localhost:8000')) return;

  e.respondWith(
    caches.match(e.request).then(cached => {
      return cached || fetch(e.request).then(response => {
        // Cachear recursos estáticos nuevos
        if (response.ok && e.request.method === 'GET') {
          const clone = response.clone();
          caches.open(CACHE_NAME).then(cache => cache.put(e.request, clone));
        }
        return response;
      });
    }).catch(() => caches.match('/index.html'))
  );
});