(() => {
  // This guide is a public acquisition surface. Record only aggregate stages
  // once per browser session: no seller identity, address, email, campaign
  // value, or page URL is included in these guide events.
  const storagePrefix = 'hof_fsbo_guide_';
  const record = (eventType) => {
    try {
      const key = storagePrefix + eventType;
      if (sessionStorage.getItem(key)) return;
      sessionStorage.setItem(key, '1');
      fetch('/api/fsbo-lead', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        keepalive: true,
        body: JSON.stringify({
          request_type: 'fsbo_landing_event',
          event_type: eventType,
          service_level: 'free_intake',
        }),
      }).catch(() => {});
    } catch (_) {}
  };

  record('fsbo_guide_viewed');
  document.querySelectorAll('a[href*="seller=1"][href*="seller_package=free_intake"]').forEach((link) => {
    link.addEventListener('click', () => record('fsbo_guide_cta_selected'));
  });
})();
