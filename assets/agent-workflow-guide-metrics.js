(() => {
  const guideKind = document.body?.dataset.agentGuide
    || ({
      '/texas-agent-offer-workflow': 'offer',
      '/texas-listing-workflow': 'listing',
      '/texas-lease-offer-workflow': 'lease',
    }[window.location.pathname] || 'offer');
  const storagePrefix = 'hof_agent_workflow_guide_' + guideKind + '_';
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
      const workflow = target.searchParams.get('workflow');
      const ctaPath = workflow === 'sale_listing'
        ? 'listing_guide'
        : workflow === 'lease_listing' || workflow === 'lease_representation'
        ? 'lease_guide'
        : target.searchParams.get('workspace') === 'relationship'
        ? 'relationship_drafts'
        : 'client_draft';
      record('agent_workflow_guide_cta_selected', ctaPath);
    });
  });
})();
