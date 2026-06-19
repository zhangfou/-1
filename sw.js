const RP_HUB_CACHE = 'rp-hub-shell-v2';

const LOCAL_ASSETS = [
  './',
  './index.html',
  './manifest.webmanifest',
  './assets/css/styles.css',
  './assets/js/utils.js',
  './assets/js/card-utils.js',
  './assets/js/ui-select.js',
  './assets/js/app.js',
  './assets/vendor/vue.global.prod.js',
  './assets/vendor/marked.min.js',
  './assets/vendor/purify.min.js',
  './assets/vendor/Sortable.min.js',
  './assets/icons/icon.svg'
];

self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(RP_HUB_CACHE)
      .then(cache => cache.addAll(LOCAL_ASSETS))
      .then(() => self.skipWaiting())
  );
});

self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys()
      .then(keys => Promise.all(
        keys
          .filter(key => key !== RP_HUB_CACHE)
          .map(key => caches.delete(key))
      ))
      .then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', event => {
  const request = event.request;
  if (request.method !== 'GET') return;
  const url = new URL(request.url);
  if (url.origin !== self.location.origin) return;

  event.respondWith(
    caches.match(request, { ignoreSearch: true }).then(cached => (
      cached || fetch(request).then(response => {
        const copy = response.clone();
        caches.open(RP_HUB_CACHE).then(cache => cache.put(request, copy));
        return response;
      })
    ))
  );
});
