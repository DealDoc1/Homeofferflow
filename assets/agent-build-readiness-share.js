(() => {
  'use strict';
  for (const card of document.querySelectorAll('[data-hof-blueprint-share]')) {
    const button = card.querySelector('[data-copy-blueprint]');
    const link = card.querySelector('[data-blueprint-link]');
    const manual = card.querySelector('[data-manual-blueprint]');
    const field = manual?.querySelector('input');
    const status = card.querySelector('[data-blueprint-status]');
    if (!button || !link || !manual || !field || !status) continue;

    button.hidden = false;
    button.addEventListener('click', async () => {
      if (button.getAttribute('aria-busy') === 'true') return;
      const shareUrl = new URL(link.getAttribute('href'), 'https://www.homeofferflow.com').href;
      button.setAttribute('aria-busy', 'true');
      try {
        await navigator.clipboard.writeText(shareUrl);
        manual.hidden = true;
        status.textContent = 'Client link copied.';
      } catch (_) {
        field.value = shareUrl;
        manual.hidden = false;
        status.textContent = 'Select and copy this link to share it with your client.';
        field.focus();
        field.select();
        field.scrollLeft = 0;
      } finally {
        button.removeAttribute('aria-busy');
      }
    });
  }
})();
