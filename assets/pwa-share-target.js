(() => {
  const params = new URLSearchParams(window.location.search);
  if (params.get('pwa_share') !== '1') return;
  const title = String(params.get('title') || '').trim().slice(0, 180);
  const text = String(params.get('text') || '').trim().slice(0, 500);
  const sharedUrl = String(params.get('url') || '').trim().slice(0, 1000);
  if (!title && !text && !sharedUrl) return;

  const render = () => {
    if (document.getElementById('hofPwaSharedContext')) return;
    const card = document.createElement('aside');
    card.id = 'hofPwaSharedContext';
    card.setAttribute('role', 'status');
    card.style.cssText = 'margin:1rem auto;max-width:58rem;padding:.9rem 1rem;border:1px solid rgba(200,151,63,.45);border-radius:12px;background:rgba(200,151,63,.1);color:#173f35;font:14px/1.45 Arial,sans-serif;';
    const heading = document.createElement('strong');
    heading.textContent = 'Shared context is ready to review';
    card.appendChild(heading);
    const detail = document.createElement('p');
    detail.style.cssText = 'margin:.35rem 0 0;white-space:pre-wrap;';
    detail.textContent = [title, text].filter(Boolean).join('\n');
    card.appendChild(detail);
    if (/^https?:\/\//i.test(sharedUrl)) {
      const link = document.createElement('a');
      link.href = sharedUrl;
      link.target = '_blank';
      link.rel = 'noopener noreferrer';
      link.textContent = 'Open shared link';
      link.style.cssText = 'display:inline-block;margin-top:.5rem;color:#173f35;font-weight:800;';
      card.appendChild(link);
    }
    const action = document.createElement('button');
    action.type = 'button';
    action.textContent = 'Start a buyer offer with this context';
    action.style.cssText = 'display:block;margin-top:.7rem;padding:.6rem .8rem;border:0;border-radius:8px;background:#c8973f;color:#102033;font:700 14px/1.2 Arial,sans-serif;cursor:pointer;';
    action.addEventListener('click', () => {
      // Keep shared text out of the URL and offer payload. The user reviews
      // the context above, then chooses what to enter in the guided workflow.
      window.trackEvent?.('PWA Shared Context CTA Selected', { surface: 'pwa_share_target' });
      window.logOfferEvent?.(null, 'pwa_shared_context_buyer_offer_opened', 'opened', 'Installed-app shared context opened the buyer offer handoff.', { surface: 'pwa_share_target' });
      window.setAudience?.('homebuyer');
      if (typeof window.beginOfferFrom === 'function') window.beginOfferFrom('pwa_share_target');
      else window.location.assign('/?buyer=1&utm_source=pwa_shortcut&utm_medium=installed_app&utm_campaign=shared_context');
    });
    card.appendChild(action);
    const agentAction = document.createElement('button');
    agentAction.type = 'button';
    agentAction.textContent = 'Open the agent transaction chooser';
    agentAction.style.cssText = 'display:block;margin-top:.45rem;padding:.55rem .8rem;border:1px solid rgba(23,63,53,.35);border-radius:8px;background:transparent;color:#173f35;font:700 14px/1.2 Arial,sans-serif;cursor:pointer;';
    agentAction.addEventListener('click', () => {
      // Shared text remains review-only context. Agents choose the transaction
      // before entering any client, property, or form data.
      window.trackEvent?.('PWA Shared Context Agent CTA Selected', { surface: 'pwa_share_target' });
      window.logOfferEvent?.(null, 'pwa_shared_context_agent_chooser_opened', 'opened', 'Installed-app shared context opened the agent transaction chooser.', { surface: 'pwa_share_target' });
      try { sessionStorage.setItem('hof_pwa_shared_context_agent_pending', '1'); } catch (_) {}
      window.setAudience?.('agent');
      if (typeof window.openAgentTransactionPicker === 'function') window.openAgentTransactionPicker();
      else window.location.assign('/?pwa_action=transaction_start&utm_source=pwa_shortcut&utm_medium=installed_app&utm_campaign=shared_context_agent');
    });
    card.appendChild(agentAction);
    const host = document.querySelector('main') || document.body;
    host.prepend(card);
  };
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', render, { once: true });
  else render();
})();
