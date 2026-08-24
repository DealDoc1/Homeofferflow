(() => {
  // This guide is a public acquisition surface. Record only aggregate stages
  // once per browser session: no seller identity, address, email, campaign
  // value, or page URL is included in these guide events.
  const storagePrefix = 'hof_fsbo_guide_';
  const allowedPackages = new Set(['free_intake', 'seller_prep', 'launch_kit', 'flat_fee_mls', 'offer_review', 'contract_help', 'premium_bundle']);
  // Use only the medium so campaign names, query strings, and visitor identity
  // never enter the aggregate seller-guide event.
  const params = new URLSearchParams(window.location.search);
  const medium = String(params.get('utm_medium') || '').trim().toLowerCase();
  const channel = medium === 'organic_content' ? 'organic'
    : medium === 'installed_app' ? 'pwa_shortcut'
    : ['direct', 'email', 'social', 'referral', 'local_event', 'print'].includes(medium) ? medium
    : 'unspecified';
  // The free guide CTA historically sent service_level: 'free_intake'; paid-path
  // attribution now uses the same privacy-safe field with an allowlisted package.
  const record = (eventType, serviceLevel = 'free_intake') => {
    try {
      const packageKey = allowedPackages.has(serviceLevel) ? serviceLevel : 'free_intake';
      const key = storagePrefix + eventType + '_' + packageKey;
      if (sessionStorage.getItem(key)) return;
      sessionStorage.setItem(key, '1');
      fetch('/api/fsbo-lead', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        keepalive: true,
        body: JSON.stringify({
          request_type: 'fsbo_landing_event',
          event_type: eventType,
          service_level: packageKey,
          channel,
        }),
      }).catch(() => {});
    } catch (_) {}
  };

  record('fsbo_guide_viewed');
  document.querySelectorAll('a[data-fsbo-package-cta], a[href*="seller=1"][href*="seller_package=free_intake"]').forEach((link) => {
    link.addEventListener('click', () => {
      const packageKey = new URL(link.href, window.location.origin).searchParams.get('seller_package') || 'free_intake';
      if (packageKey === 'free_intake') record('fsbo_guide_cta_selected');
      else record('fsbo_guide_cta_selected', packageKey);
    });
  });
})();
