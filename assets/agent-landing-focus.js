(() => {
  const params = new URLSearchParams(window.location.search);
  const rawSource = String(params.get('utm_source') || '').trim().toLowerCase();
  const rawMedium = String(params.get('utm_medium') || '').trim().toLowerCase();
  const channel = window.hofAgentLandingChannel || (rawMedium === 'installed_app' ? 'pwa_shortcut' : rawSource || 'direct');
  const allowedChannels = new Set(['direct', 'organic', 'pwa_shortcut', 'direct_outreach', 'email', 'social', 'referral', 'local_event', 'print']);
  const safeChannel = allowedChannels.has(channel) ? channel : 'direct';
  const note = document.querySelector('.note:not(#agentTrialOffer)');
  const start = document.querySelector('#transaction-start');
  if (!note || !start) return;

  let resourceLinks = Array.from(note.querySelectorAll('a')).filter((link) => {
    const href = link.getAttribute('href') || '';
    return href.includes('texas-agent-offer-workflow')
      || href.includes('texas-agent-form-library')
      || href.includes('texas-listing-workflow')
      || href.includes('texas-lease-offer-workflow');
  });

  // The main page keeps Question 1 intentionally clean. Create the optional
  // reference shelf here so it stays one tap away without putting a catalog
  // between an agent and the transaction they came to start.
  if (!resourceLinks.length) {
    resourceLinks = [
      ['/texas-agent-offer-workflow', 'Offer workflow guide'],
      ['/texas-agent-form-library', 'Shared form library'],
      ['/texas-listing-workflow', 'Listing workflow guide'],
      ['/texas-lease-offer-workflow', 'Lease workflow guide']
    ].map(([href, label]) => {
      const link = document.createElement('a');
      link.href = href;
      link.textContent = label;
      return link;
    });
  }

  const workflowLink = resourceLinks.find((link) => link.href.includes('texas-agent-offer-workflow'));
  note.replaceChildren();
  const strong = document.createElement('strong');
  strong.textContent = 'No brokerage seat required.';
  note.append(strong, " Every signed-in agent can use HomeOfferFlow's released shared form workflows. Start with the client and property details you have, then save your agent defaults afterward for faster repeat work.");
  if (workflowLink) {
    note.append(' ', workflowLink.cloneNode(true));
  }

  const details = document.createElement('details');
  details.className = 'agent-resource-links';
  const summary = document.createElement('summary');
  summary.textContent = 'Explore shared forms and workflow guides';
  details.append(summary);
  const list = document.createElement('div');
  list.className = 'agent-resource-list';
  resourceLinks.slice(workflowLink ? 1 : 0).forEach((link) => list.append(link.cloneNode(true)));
  details.append(list);
  details.addEventListener('toggle', () => {
    if (!details.open) return;
    try {
      const key = 'hof_agent_resource_links_expanded';
      if (sessionStorage.getItem(key)) return;
      sessionStorage.setItem(key, '1');
      fetch('/api/fsbo-lead', {
        method: 'POST', headers: {'Content-Type': 'application/json'}, keepalive: true,
        body: JSON.stringify({request_type: 'agent_landing_event', event_type: 'agent_resource_links_expanded', channel: safeChannel})
      }).catch(() => {});
    } catch (_) {}
  });
  start.insertAdjacentElement('afterend', details);
})();
