(() => {
  const params = new URLSearchParams(window.location.search);
  const rawMedium = String(params.get('utm_medium') || '').trim().toLowerCase();
  const channel = rawMedium === 'installed_app' ? 'pwa_shortcut' : rawMedium || 'direct';
  const allowedChannels = new Set(['direct', 'organic', 'pwa_shortcut', 'email', 'social', 'referral', 'other']);
  const safeChannel = allowedChannels.has(channel) ? channel : 'direct';
  const guideNote = Array.from(document.querySelectorAll('p.note')).find((node) =>
    node.textContent.includes('Want the short version first?')
  );
  if (!guideNote) return;
  const details = document.createElement('details');
  details.className = 'partner-resource-links';
  const summary = document.createElement('summary');
  summary.textContent = 'Read the short partner placement guide';
  details.append(summary);
  const content = document.createElement('p');
  content.innerHTML = guideNote.innerHTML.replace('Want the short version first? ', '');
  details.append(content);
  details.addEventListener('toggle', () => {
    if (!details.open) return;
    try {
      const key = 'hof_partner_guide_expanded';
      if (sessionStorage.getItem(key)) return;
      sessionStorage.setItem(key, '1');
      fetch('/api/fsbo-lead', {
        method: 'POST', headers: {'Content-Type': 'application/json'}, keepalive: true,
        body: JSON.stringify({request_type: 'partner_landing_event', event_type: 'partner_guide_expanded', tier: 'unspecified', category: 'unspecified', channel: safeChannel})
      }).catch(() => {});
    } catch (_) {}
  });
  guideNote.replaceWith(details);
})();
