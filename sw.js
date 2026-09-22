/* Code 7 service worker — offline app shell. Cache name changes every build, so updates roll out automatically. */
const CACHE = 'code7-3bcb6e0b'; const MCACHE = 'leg3nd-music-v1';
const SHELL = ['./', './index.html', './manifest.webmanifest', './icons/icon-192.png', './icons/icon-512.png', './icons/apple-touch-icon.png'];
self.addEventListener('install', e => { e.waitUntil(caches.open(CACHE).then(c => c.addAll(SHELL)).then(() => self.skipWaiting())); });
self.addEventListener('activate', e => { e.waitUntil(caches.keys().then(ks => Promise.all(ks.filter(k => k !== CACHE && k !== MCACHE).map(k => caches.delete(k)))).then(() => self.clients.claim())); });
self.addEventListener('fetch', e => {
  if (e.request.method !== 'GET') return;
  const url = new URL(e.request.url);
  if (/fonts\.(googleapis|gstatic)\.com$/.test(url.hostname)) { // cache web fonts so the look survives offline
    e.respondWith(caches.open(CACHE).then(c => c.match(e.request).then(r => r || fetch(e.request).then(res => { c.put(e.request, res.clone()); return res; }))));
    return;
  }
  if (url.origin !== location.origin) return;
  if (/\/music\/[a-z]+\.ogg$/.test(url.pathname)) { e.respondWith(musicFetch(e.request, url)); return; }   // soundtrack: cached once, kept across app updates
  // network-first for the page (get updates when online), cache-first for everything else
  if (e.request.mode === 'navigate') {
    e.respondWith(fetch(e.request).then(r => { const cp = r.clone(); caches.open(CACHE).then(c => c.put('./index.html', cp)); return r; }).catch(() => caches.match('./index.html')));
    return;
  }
  e.respondWith(caches.match(e.request, { ignoreSearch: true }).then(r => r || fetch(e.request)));
});

async function musicFetch(req, url) {       // serve the whole file from cache, honouring Range requests from the audio player
  const c = await caches.open(MCACHE); let res = await c.match(url.pathname);
  if (!res) { try { const r = await fetch(url.pathname); if (!r.ok) return r; await c.put(url.pathname, r.clone()); res = r; } catch (e) { return new Response('', { status: 504 }); } }
  const range = req.headers.get('range'); if (!range) return res;
  const buf = await res.clone().arrayBuffer(); const m = /bytes=(\d*)-(\d*)/.exec(range) || []; const size = buf.byteLength;
  const start = m[1] ? +m[1] : 0, end = m[2] ? Math.min(+m[2], size - 1) : size - 1;
  return new Response(buf.slice(start, end + 1), { status: 206, headers: { 'Content-Type': 'audio/ogg', 'Content-Range': `bytes ${start}-${end}/${size}`, 'Content-Length': String(end - start + 1), 'Accept-Ranges': 'bytes' } });
}
