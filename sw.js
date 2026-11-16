const CACHE_PREFIX = 'terrain-gis-shell-';
const CACHE = CACHE_PREFIX + 'v2';
const SHELL = [
  './', './index.html', './styles.css', './app.js', './share-fix.js',
  './report-plus.js', './viewer.html', './viewer.js', './demo.html',
  './demo.css', './demo.js', './manifest.webmanifest'
];
const ROOT_FILES = new Set(SHELL.map(path => new URL(path, self.registration.scope).pathname));

self.addEventListener('install', event => {
  event.waitUntil(caches.open(CACHE).then(cache => cache.addAll(SHELL)));
});
self.addEventListener('activate', event => {
  // GitHub Pages shares CacheStorage across the GIS, Atlas and fishing game.
  // Only retire this application's older shell caches.
  event.waitUntil(caches.keys().then(keys => Promise.all(
    keys.filter(key => key.startsWith(CACHE_PREFIX) && key !== CACHE)
      .map(key => caches.delete(key))
  )));
});
self.addEventListener('fetch', event => {
  const url = new URL(event.request.url);
  if (event.request.method !== 'GET' || url.origin !== self.location.origin ||
      !ROOT_FILES.has(url.pathname)) return;
  event.respondWith((async () => {
    const cache = await caches.open(CACHE);
    try {
      const response = await fetch(event.request);
      if (response.ok) await cache.put(event.request, response.clone());
      return response;
    } catch {
      return await cache.match(event.request, {ignoreSearch: true}) || Response.error();
    }
  })());
});
