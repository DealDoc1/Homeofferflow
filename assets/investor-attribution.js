(() => {
  const allowed = ['utm_source', 'utm_medium', 'utm_campaign', 'utm_content'];
  const incoming = new URLSearchParams(window.location.search);
  const campaign = new URLSearchParams();
  allowed.forEach(key => {
    const value = incoming.get(key);
    if (value) campaign.set(key, value);
  });
  if (!campaign.size) {
    campaign.set('utm_source', 'investor_workspace');
    campaign.set('utm_medium', 'organic_landing');
    campaign.set('utm_campaign', 'investor_acquisition');
  }
  document.querySelectorAll('[data-investor-start]').forEach(link => {
    const destination = new URL(link.href, window.location.origin);
    campaign.forEach((value, key) => destination.searchParams.set(key, value));
    link.href = destination.pathname + '?' + destination.searchParams.toString();
  });
})();
