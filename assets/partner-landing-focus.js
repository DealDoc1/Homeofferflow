(() => {
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
        body: JSON.stringify({request_type: 'partner_landing_event', event_type: 'partner_guide_expanded', tier: 'unspecified', category: 'unspecified', channel: 'direct'})
      }).catch(() => {});
    } catch (_) {}
  });
  guideNote.replaceWith(details);
})();
