// Keep public discovery pages installable without adding an app-store or
// third-party dependency. The main workspace owns update prompts; public
// pages only need to register the same lightweight shell service worker.
(() => {
  if (!('serviceWorker' in navigator)) return;
  let deferredInstallPrompt = null;
  const dismissKey = 'hof_public_pwa_install_dismissed_v1';
  const isMobileInstallSurface = () => /Android|iPhone|iPad|iPod/i.test(navigator.userAgent || '')
    || (navigator.maxTouchPoints > 1 && /Macintosh/i.test(navigator.userAgent || ''));
  const removeInstallCard = () => document.getElementById('hofPublicPwaInstallCard')?.remove();
  const showUpdateNotice = registration => {
    if (!isMobileInstallSurface() || !registration?.waiting || document.getElementById('hofPublicPwaUpdateNotice')) return;
    const notice = document.createElement('aside');
    notice.id = 'hofPublicPwaUpdateNotice';
    notice.setAttribute('role', 'status');
    notice.setAttribute('aria-live', 'polite');
    notice.style.cssText = 'position:fixed;right:1rem;bottom:1rem;z-index:20;max-width:min(23rem,calc(100% - 2rem));padding:.8rem .9rem;border:1px solid rgba(109,179,143,.45);border-radius:12px;background:#10243a;color:#fff;box-shadow:0 12px 30px rgba(0,0,0,.28);font:14px/1.4 Arial,sans-serif;';
    notice.innerHTML = '<strong style="display:block;color:#bce8d0;margin-bottom:.2rem">A newer HomeOfferFlow version is ready</strong><span style="display:block;color:#b6c4d5;margin-bottom:.55rem">Refresh when you are finished with this page to use the latest app shell.</span><button type="button" id="hofPublicPwaUpdateButton" style="padding:.45rem .65rem;border:0;border-radius:7px;background:#6db38f;color:#102033;font-weight:800;cursor:pointer">Refresh for latest version</button>';
    document.body.appendChild(notice);
    notice.querySelector('#hofPublicPwaUpdateButton')?.addEventListener('click', () => {
      registration.waiting?.postMessage({ type: 'HOF_SKIP_WAITING' });
      window.location.reload();
    });
  };
  const renderInstallCard = () => {
    if (!isMobileInstallSurface() || !deferredInstallPrompt || document.getElementById('hofPublicPwaInstallCard')) return;
    try { if (sessionStorage.getItem(dismissKey) === '1') return; } catch (_) {}
    const card = document.createElement('aside');
    card.id = 'hofPublicPwaInstallCard';
    card.setAttribute('aria-label', 'HomeOfferFlow app installation');
    card.style.cssText = 'position:fixed;right:1rem;bottom:1rem;z-index:20;max-width:min(22rem,calc(100% - 2rem));padding:.8rem .9rem;border:1px solid rgba(200,151,63,.45);border-radius:12px;background:#10243a;color:#fff;box-shadow:0 12px 30px rgba(0,0,0,.28);font:14px/1.4 Arial,sans-serif;';
    card.innerHTML = '<strong style="display:block;color:#e8b86d;margin-bottom:.2rem">Keep HomeOfferFlow one tap away</strong><span style="display:block;color:#b6c4d5;margin-bottom:.55rem">Install the lightweight app shell for faster returns to your workspace.</span><div style="display:flex;gap:.45rem;flex-wrap:wrap"><button type="button" id="hofPublicPwaInstallButton" style="padding:.45rem .65rem;border:0;border-radius:7px;background:#c8973f;color:#102033;font-weight:800;cursor:pointer">Install app</button><button type="button" id="hofPublicPwaInstallDismiss" style="padding:.45rem .65rem;border:1px solid rgba(255,255,255,.25);border-radius:7px;background:transparent;color:#fff;cursor:pointer">Not now</button></div>';
    document.body.appendChild(card);
    card.querySelector('#hofPublicPwaInstallDismiss')?.addEventListener('click', () => {
      try { sessionStorage.setItem(dismissKey, '1'); } catch (_) {}
      removeInstallCard();
    });
    card.querySelector('#hofPublicPwaInstallButton')?.addEventListener('click', async () => {
      if (!deferredInstallPrompt) return;
      const prompt = deferredInstallPrompt;
      deferredInstallPrompt = null;
      removeInstallCard();
      await prompt.prompt();
      await prompt.userChoice.catch(() => {});
    });
  };
  window.addEventListener('beforeinstallprompt', event => {
    if (!isMobileInstallSurface()) return;
    event.preventDefault();
    deferredInstallPrompt = event;
    renderInstallCard();
  });
  window.addEventListener('appinstalled', () => { deferredInstallPrompt = null; removeInstallCard(); });
  window.addEventListener('load', () => {
    navigator.serviceWorker.register('/service-worker.js', { scope: '/' }).then(registration => {
      showUpdateNotice(registration);
      registration.addEventListener('updatefound', () => {
        const installing = registration.installing;
        installing?.addEventListener('statechange', () => {
          if (installing.state === 'installed' && navigator.serviceWorker.controller) showUpdateNotice(registration);
        });
      });
    }).catch(() => {});
  }, { once: true });
})();
