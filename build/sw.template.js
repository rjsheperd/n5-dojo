// N5 Renshū Dōjō service worker: every page, font, icon and audio file is cached on install,
// so the whole app runs with no connection. A new deploy changes VERSION and replaces the cache.
const VERSION = "__VERSION__";
const CACHE = "n5-dojo-" + VERSION;
const ASSETS = __ASSETS__;

self.addEventListener("install", e => {
  e.waitUntil(caches.open(CACHE).then(c => c.addAll(ASSETS.map(a => new Request(a, { cache: "reload" })))).then(() => self.skipWaiting()));
});

self.addEventListener("activate", e => {
  e.waitUntil(caches.keys()
    .then(keys => Promise.all(keys.filter(k => k.startsWith("n5-dojo-") && k !== CACHE).map(k => caches.delete(k))))
    .then(() => self.clients.claim()));
});

// Safari asks for audio in byte ranges; answer those from the cached file.
async function rangeResponse(req, res) {
  const buf = await res.arrayBuffer();
  const m = /bytes=(\d*)-(\d*)/.exec(req.headers.get("range") || "");
  const total = buf.byteLength;
  let start = m && m[1] ? +m[1] : 0, end = m && m[2] ? +m[2] : total - 1;
  if (m && !m[1] && m[2]) { start = Math.max(0, total - +m[2]); end = total - 1; }
  end = Math.min(end, total - 1);
  return new Response(buf.slice(start, end + 1), {
    status: 206,
    headers: { "Content-Type": res.headers.get("Content-Type") || "audio/mpeg", "Content-Range": `bytes ${start}-${end}/${total}`,
      "Content-Length": String(end - start + 1), "Accept-Ranges": "bytes" },
  });
}

self.addEventListener("fetch", e => {
  const req = e.request;
  if (req.method !== "GET" || new URL(req.url).origin !== location.origin) return;
  e.respondWith((async () => {
    const cache = await caches.open(CACHE);
    const hit = await cache.match(req, { ignoreSearch: true });
    if (hit) return req.headers.has("range") ? rangeResponse(req, hit) : hit;
    try {
      const res = await fetch(req);
      if (res.ok && res.status === 200) cache.put(req, res.clone());
      return res;
    } catch (err) {
      if (req.mode === "navigate") return (await cache.match("index.html")) || Response.error();
      return Response.error();
    }
  })());
});
