(() => {
  const storagePrefix = 'hof_agent_workflow_guide_';
  const record = (eventType, ctaPath = '') => {
    try {
      const storageKey = storagePrefix + eventType + (ctaPath ? '_' + ctaPath : '');
      if (sessionStorage.getItem(storageKey)) return;
      sessionStorage.setItem(storageKey, '1');
      const body = {
        request_type: 'agent_landing_event',
        event_type: eventType,
        channel: 'unspecified',
      };
      if (ctaPath) body.cta_path = ctaPath;
      fetch('/api/fsbo-lead', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        keepalive: true,
        body: JSON.stringify(body),
      }).catch(() => {});
    } catch (_) {}
  };

  record('agent_workflow_guide_viewed');
  document.querySelectorAll('a[href^="/?agent=1"]').forEach((link) => {
    link.addEventListener('click', () => {
      const target = new URL(link.href, window.location.origin);
      const ctaPath = target.searchParams.get('workspace') === 'relationship'
        ? 'relationship_drafts'
        : 'client_draft';
      record('agent_workflow_guide_cta_selected', ctaPath);
    });
  });
})();
