const BUILD_VERSION = '1.0.14';
const CACHE_NAME = 'sdn-toolset-v' + BUILD_VERSION;
const ASSETS = [
  '/bluetooth-handshake/',
  '/bluetooth-handshake/index.html',
  '/bluetooth-handshake/manifest.json',
  '/bluetooth-handshake/favicon.ico',
  '/bluetooth-handshake/sgn-radio-512x512.png',
  '/bluetooth-handshake/sgn-radio.svg'
];

// Install Event: Prepare the offline local container storage
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      return cache.addAll(ASSETS);
    })
  );
});

// Intercept Network Requests
self.addEventListener('fetch', (event) => {
  event.respondWith(
    fetch(event.request)
      .then((response) => {
        // If the network network check works, update the cache copy dynamically
        if (response.status === 200) {
          const responseClone = response.clone();
          caches.open(CACHE_NAME).then((cache) => {
            cache.put(event.request, responseClone);
          });
        }
        return response;
      })
      .catch(() => {
        // Fallback: If network is broken, serve the asset from local storage
        return caches.match(event.request);
      })
  );
});

// Listen for a message from the main application window asking for the version
// self.addEventListener('message', (event) => {
//   if (event.data && event.data.type === 'GET_VERSION') {
//     event.ports[0].postMessage({ version: BUILD_VERSION });
//   }
// });

self.addEventListener('message', (event) => {
  if (event.data && event.data.type === 'GET_VERSION') {
    // Handshake: Send our version back to the UI
    event.ports[0].postMessage({ version: BUILD_VERSION });
  } 
  else if (event.data && event.data.type === 'SKIP_WAITING') {
    // Command: Force this worker to wake up and take over immediately
    self.skipWaiting();
  }
});
