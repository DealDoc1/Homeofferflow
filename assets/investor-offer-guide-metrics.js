(() => {
  // Aggregate guide conversion only. No investor identity, entity, client,
  // property, URL, or arbitrary campaign value is included in these events.
  const record = (eventType) => {
    try {
      const key = 'hof_investor_offer_guide_' + eventType;
      if (sessionStorage.getItem(key)) return;
      sessionStorage.setItem(key, '1');
      fetch('/api/fsbo-lead', {
        method: 'POST', headers: {'Content-Type': 'application/json'}, keepalive: true,
        body: JSON.stringify({request_type: 'investor_landing_event', event_type: eventType}),
      }).catch(() => {});
    } catch (_) {}
  };
  record('investor_offer_guide_viewed');
  document.querySelectorAll('a[href^="/?investor=1"]').forEach((link) => {
    link.addEventListener('click', () => record('investor_offer_guide_cta_selected'));
  });
})();
