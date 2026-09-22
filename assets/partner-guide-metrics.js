(() => {
  const params = new URLSearchParams(window.location.search || '');
  const rawSource = String(params.get('utm_source') || '').toLowerCase();
  const rawMedium = String(params.get('utm_medium') || '').toLowerCase();
  const allowedChannels = new Set(['direct', 'homepage', 'organic', 'pwa_shortcut', 'email', 'partner_receipt', 'social', 'referral', 'other', 'direct_outreach', 'local_event', 'print', 'owned_directory']);
  const channel = rawMedium === 'installed_app' || rawSource === 'pwa_shortcut'
    ? 'pwa_shortcut'
    : rawMedium === 'owned_directory'
      ? 'owned_directory'
      : rawMedium === 'homepage' || rawSource === 'homeofferflow'
        ? 'homepage'
        : rawMedium === 'organic_content' || rawSource === 'organic' || rawSource === 'texas_home_service_partner_guide'
          ? 'organic'
          : allowedChannels.has(rawMedium)
            ? rawMedium
            : allowedChannels.has(rawSource)
              ? rawSource
              : rawSource ? 'other' : 'direct';
  const record = (eventType) => {
    try {
      const key = `hof_partner_guide_${eventType}_${channel}`;
      if (sessionStorage.getItem(key)) return;
      sessionStorage.setItem(key, '1');
      fetch('/api/fsbo-lead', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        keepalive: true,
        body: JSON.stringify({
          request_type: 'partner_landing_event',
          event_type: eventType,
          tier: 'unspecified',
          category: 'other',
          channel,
          surface: 'partner_guide'
        })
      }).catch(() => {});
    } catch (_) {}
  };
  record('partner_landing_viewed');
  document.querySelectorAll('a[href*="/partners"]').forEach((link) => {
    link.addEventListener('click', () => record('partner_landing_cta_selected'));
  });
})();
