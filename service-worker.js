const CACHE_NAME = 'baseball-live-v1';
const ASSETS = [
  '/',
  '/api/games'
];

// 安裝 Service Worker
self.addEventListener('install', (e) => {
  e.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      return cache.addAll(ASSETS);
    })
  );
});

// 攔截請求（優先使用網路，網路失敗時使用快取）
self.addEventListener('fetch', (e) => {
  e.respondWith(
    fetch(e.request).catch(() => {
      return caches.match(e.request);
    })
  );
});
