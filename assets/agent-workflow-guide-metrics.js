(() => {
  const guideKind = document.body?.dataset.agentGuide
    || ({
      '/texas-agent-offer-workflow': 'offer',
      '/texas-listing-workflow': 'listing',
      '/texas-lease-offer-workflow': 'lease',
      '/texas-agent-form-library': 'form_library',
    }[window.location.pathname] || 'offer');
  const storagePrefix = 'hof_agent_workflow_guide_' + guideKind + '_';
  const channel = (() => {
    const params = new URLSearchParams(window.location.search);
    const source = String(params.get('utm_source') || '').trim().toLowerCase();
    const medium = String(params.get('utm_medium') || '').trim().toLowerCase();
    // Public guide links use a guide-specific source plus organic_content.
    // Keep that acquisition signal in the allowlisted aggregate channel rather
    // than collapsing every search visit into "unspecified".
    if (medium === 'installed_app' || source === 'pwa_shortcut') return 'pwa_shortcut';
    if (medium === 'organic_content' || source === 'organic') return 'organic';
    return ['email', 'social', 'referral'].includes(source) ? source : 'unspecified';
  })();
  const record = (eventType, ctaPath = '') => {
    try {
      const storageKey = storagePrefix + eventType + (ctaPath ? '_' + ctaPath : '');
      if (sessionStorage.getItem(storageKey)) return;
      sessionStorage.setItem(storageKey, '1');
      const body = {
        request_type: 'agent_landing_event',
        event_type: eventType,
        channel,
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
  document.querySelectorAll('a[href]').forEach((link) => {
    link.addEventListener('click', () => {
      const target = new URL(link.href, window.location.origin);
      const startsQuestionOne = target.pathname === '/agents' && target.hash === '#transaction-start';
      if (!startsQuestionOne && target.searchParams.get('agent') !== '1') return;
      const workflow = target.searchParams.get('workflow');
      const ctaPath = startsQuestionOne && guideKind === 'listing'
        ? 'listing_guide'
        : startsQuestionOne && guideKind === 'lease'
        ? 'lease_guide'
        : startsQuestionOne && guideKind === 'form_library'
        ? 'form_library_guide'
        : workflow === 'sale_listing'
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
