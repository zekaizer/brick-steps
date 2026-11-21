// Brick Steps service worker: cache-first with background refresh for same-origin GETs and Google Fonts.
// One cache name for the life of the site, so manuals opened before stay readable offline after an update.
const CACHE = "brick-steps";
const SHELL = [
  "./", "./assets/site.css", "./assets/manual.js", "./manifest.webmanifest", "./brand/brick-steps-lockup.svg", "./favicon.svg",
  // 3D step view (ADR 0002)
  "./assets/viewer3d.js",
  "./assets/vendor/three/three.module.min.js",
  "./assets/vendor/three/addons/controls/OrbitControls.js",
  "./assets/vendor/three/addons/loaders/LDrawLoader.js",
  "./assets/vendor/three/addons/materials/LDrawConditionalLineMaterial.js",
  "./assets/vendor/three/addons/lines/LineSegments2.js",
  "./assets/vendor/three/addons/lines/LineSegmentsGeometry.js",
  "./assets/vendor/three/addons/lines/LineMaterial.js",
];

self.addEventListener("install", (event) => {
  self.skipWaiting();
  event.waitUntil(caches.open(CACHE).then((c) => c.addAll(SHELL)).catch(() => {}));
});

self.addEventListener("activate", (event) => {
  event.waitUntil(self.clients.claim());
});

function cacheable(request) {
  if (request.method !== "GET") return false;
  const url = new URL(request.url);
  return url.origin === self.location.origin || url.hostname.endsWith("fonts.googleapis.com") || url.hostname.endsWith("fonts.gstatic.com");
}

self.addEventListener("fetch", (event) => {
  if (!cacheable(event.request)) return;
  event.respondWith(
    caches.open(CACHE).then(async (cache) => {
      const hit = await cache.match(event.request, { ignoreSearch: true });
      const fresh = fetch(event.request)
        .then((res) => {
          if (res.ok || res.type === "opaque") cache.put(event.request, res.clone());
          return res;
        })
        .catch(() => hit);
      if (hit) {
        event.waitUntil(fresh);
        return hit;
      }
      return fresh;
    })
  );
});

self.addEventListener("message", (event) => {
  const data = event.data || {};
  if (data.type !== "cache" || !Array.isArray(data.urls)) return;
  event.waitUntil(
    caches.open(CACHE).then((cache) =>
      Promise.all(data.urls.map((u) => cache.match(u).then((hit) => hit || cache.add(u)).catch(() => {})))
    )
  );
});
