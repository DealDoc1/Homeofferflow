// Keep public discovery pages installable without adding an app-store or
// third-party dependency. The main workspace owns update prompts; public
// pages only need to register the same lightweight shell service worker.
(() => {
  if (!('serviceWorker' in navigator)) return;
  window.addEventListener('load', () => {
    navigator.serviceWorker.register('/service-worker.js', { scope: '/' }).catch(() => {});
  }, { once: true });
})();
