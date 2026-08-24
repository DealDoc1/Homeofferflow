(() => {
  // This public seller page records only aggregate funnel stages once per
  // browser session. Never send identity, property, URL, referrer, or UTM
  // values with this lightweight acquisition measurement.
  const storagePrefix = 'hof_fsbo_closing_checklist_';
  const allowedPackages = new Set(['free_intake', 'seller_prep', 'launch_kit', 'flat_fee_mls', 'offer_review', 'contract_help', 'premium_bundle']);
  const params = new URLSearchParams(window.location.search);
  const medium = String(params.get('utm_medium') || '').toLowerCase();
  const source = String(params.get('utm_source') || '').toLowerCase();
  const channel = medium === 'organic_content' || source === 'organic' ? 'organic'
    : medium === 'installed_app' || source === 'pwa_shortcut' ? 'pwa_shortcut'
    : medium === 'email' ? 'email'
    : medium === 'social' ? 'social'
    : medium === 'referral' ? 'referral'
    : medium === 'print' ? 'print'
    : 'unspecified';

  const record = (eventType, serviceLevel = 'free_intake') => {
    if (!allowedPackages.has(serviceLevel)) serviceLevel = 'free_intake';
    const key = storagePrefix + eventType + '_' + serviceLevel;
    try {
      if (sessionStorage.getItem(key)) return;
      sessionStorage.setItem(key, '1');
      fetch('/api/fsbo-lead', {
        method: 'POST', keepalive: true,
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({request_type: 'fsbo_landing_event', event_type: eventType, service_level: serviceLevel, channel, surface: 'fsbo_closing_checklist'})
      }).catch(() => {});
    } catch (_) {}
  };

  record('fsbo_closing_checklist_viewed');
  document.querySelectorAll('a[href*="seller_package="]').forEach((link) => {
    link.addEventListener('click', () => {
      const packageKey = new URL(link.href, window.location.origin).searchParams.get('seller_package') || 'free_intake';
      record('fsbo_closing_checklist_cta_selected', packageKey);
    });
  });
})();
