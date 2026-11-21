// Brick Steps service worker.
// Pages, styles, scripts, pictures and 3D data: network first, falling back to the cache when offline or slow,
// so a page and the files it was built with always come from the same deploy. Serving each file from the cache
// on its own mixed an old page with a newer stylesheet after an update.
// three.js (pinned version) and Google Fonts never change under the same URL: cache first.
// The build renames the cache after its files (export.stamp_service_worker); a new worker deletes older caches.
// Fonts and pinned three.js go to STATIC, which no deploy deletes: re-downloading fonts after every update made
// the first screen swap fonts (and shift) on the iPad.
const CACHE = "brick-steps";
const STATIC = "brick-steps-static";
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
  const pinned = SHELL.filter((u) => u.includes("/vendor/"));
  const rest = SHELL.filter((u) => !u.includes("/vendor/"));
  event.waitUntil(Promise.all([
    caches.open(CACHE).then((c) => c.addAll(rest)),
    caches.open(STATIC).then(async (c) => {
      for (const u of pinned) if (!(await c.match(u))) await c.add(u);
    }),
  ]).catch(() => {}));
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys()
      .then((names) => Promise.all(names.filter((n) => n.startsWith("brick-steps") && n !== CACHE && n !== STATIC).map((n) => caches.delete(n))))
      .then(() => self.clients.claim())
  );
});

function cacheable(request) {
  if (request.method !== "GET") return false;
  const url = new URL(request.url);
  return url.origin === self.location.origin || url.hostname.endsWith("fonts.googleapis.com") || url.hostname.endsWith("fonts.gstatic.com");
}

const SLOW_MS = 3000;

function immutable(url) {
  return url.pathname.includes("/assets/vendor/") || url.hostname.endsWith("fonts.googleapis.com") || url.hostname.endsWith("fonts.gstatic.com");
}

function save(cache, request, res) {
  if (res.ok || res.type === "opaque") cache.put(request, res.clone());
  return res;
}

async function cacheFirst(cache, request) {
  const hit = await cache.match(request, { ignoreSearch: true });
  return hit || fetch(request).then((res) => save(cache, request, res));
}

async function networkFirst(cache, request) {
  const net = fetch(request).then((res) => save(cache, request, res));
  const cached = () => cache.match(request, { ignoreSearch: true });
  const slow = new Promise((resolve) => setTimeout(resolve, SLOW_MS)).then(async () => (await cached()) || net);
  try {
    return await Promise.race([net, slow]);
  } catch (e) {
    const hit = await cached();
    if (hit) return hit;
    throw e;
  }
}

self.addEventListener("fetch", (event) => {
  if (!cacheable(event.request)) return;
  const url = new URL(event.request.url);
  event.respondWith(immutable(url)
    ? caches.open(STATIC).then((cache) => cacheFirst(cache, event.request))
    : caches.open(CACHE).then((cache) => networkFirst(cache, event.request)));
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
