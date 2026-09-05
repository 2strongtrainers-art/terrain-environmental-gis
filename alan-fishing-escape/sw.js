const CACHE='alan-fishing-escape-v7';
const CORE=['./','./index.html','./manifest.webmanifest'];
const THREE='https://cdn.jsdelivr.net/npm/three@0.185.1/build/three.module.min.js';
self.addEventListener('install',event=>{self.skipWaiting();event.waitUntil((async()=>{const cache=await caches.open(CACHE);await cache.addAll(CORE);try{await cache.add(THREE);}catch{}})())});
self.addEventListener('activate',event=>{event.waitUntil((async()=>{await self.clients.claim();const keys=await caches.keys();await Promise.all(keys.filter(k=>k!==CACHE).map(k=>caches.delete(k)))} )())});
self.addEventListener('fetch',event=>{if(event.request.method!=='GET')return;event.respondWith((async()=>{const cached=await caches.match(event.request);if(cached)return cached;try{const response=await fetch(event.request);if(response&&(response.ok||response.type==='opaque')){const cache=await caches.open(CACHE);cache.put(event.request,response.clone()).catch(()=>{})}return response}catch{if(event.request.mode==='navigate'){const shell=await caches.match('./index.html');if(shell)return shell}return new Response('Offline resource unavailable',{status:503,statusText:'Offline'})}})())});
