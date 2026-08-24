(() => {
  const note = document.querySelector('.note:not(#agentTrialOffer)');
  const start = document.querySelector('#transaction-start');
  if (!note || !start) return;

  const resourceLinks = Array.from(note.querySelectorAll('a')).filter((link) => {
    const href = link.getAttribute('href') || '';
    return href.includes('texas-agent-offer-workflow')
      || href.includes('texas-agent-form-library')
      || href.includes('texas-listing-workflow')
      || href.includes('texas-lease-offer-workflow');
  });
  if (!resourceLinks.length) return;

  const workflowLink = resourceLinks.find((link) => link.href.includes('texas-agent-offer-workflow'));
  note.replaceChildren();
  const strong = document.createElement('strong');
  strong.textContent = 'No password and no charge to start a private workspace.';
  note.append(strong, ' Start with the client and property details you have, then save your agent defaults afterward for faster repeat work.');
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
  start.insertAdjacentElement('afterend', details);
})();
