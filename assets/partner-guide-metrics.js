(() => {
  const params = new URLSearchParams(window.location.search || '');
  const rawSource = String(params.get('utm_source') || '').toLowerCase();
  const channel = ['provider_directory', 'texas_home_service_partner_guide', 'organic'].includes(rawSource)
    ? 'organic'
    : ['email', 'social', 'referral', 'pwa_shortcut'].includes(rawSource)
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
          channel
        })
      }).catch(() => {});
    } catch (_) {}
  };
  record('partner_landing_viewed');
  document.querySelectorAll('a[href*="/partners"]').forEach((link) => {
    link.addEventListener('click', () => record('partner_landing_cta_selected'));
  });
})();
