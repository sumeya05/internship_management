/*
 * Minimal Service Worker
 *
 * Purpose: prevent console/network noise caused by missing /sw.js.
 * This file intentionally does not cache assets.
 */

self.addEventListener('install', (event) => {
  // Activate immediately
  self.skipWaiting();
});

self.addEventListener('activate', (event) => {
  event.waitUntil(self.clients.claim());
});

self.addEventListener('fetch', (event) => {
  // No special handling; let the browser handle requests.
});

