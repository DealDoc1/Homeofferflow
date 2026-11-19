(function () {
  'use strict';
  const esc = value => String(value || '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  let loaded = false, loading = false;
  const shown = new Set();
  const event = (kind, provider) => {
    if (!/^[0-9a-f-]{36}$/i.test(String(provider.id || ''))) return;
    const body = {request_type:'partner_directory_event', event_type:kind, partner_id:provider.id, partner_type:provider.partner_type, placement_tier:provider.placement_tier, directory_surface:'insurance_planning'};
    void fetch('/api/fsbo-lead', {method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body),keepalive:true}).catch(() => {});
  };
  function start() {
    const step = document.getElementById('step4'), planner = document.getElementById('paymentCalcCard'), target = document.getElementById('hofInsurancePartners');
    if (!step || !planner || !target) return;
    const visible = () => step.classList.contains('active') && planner.open &&
      document.getElementById('hofInsurancePartners') === target;
    async function render(triggerEvent) {
      if (!visible() || loaded || loading) return;
      const retry = triggerEvent?.type === 'click' ? triggerEvent.currentTarget : null;
      const restoreFocus = () => retry && document.activeElement === retry;
      loading = true;
      if (retry) {
        retry.setAttribute('aria-disabled', 'true');
        retry.textContent = 'Trying again…';
      }
      try {
        const providers = (await window.hofPartnerProfile.load('workflow')).filter(p => p.partner_type === 'insurance' && window.hofPartnerProfile.websiteUrl(p.website_url));
        if (!visible()) return;
        const moveFocus = restoreFocus();
        if (!providers.length) {
          target.hidden = true;
          target.innerHTML = '';
          if (moveFocus) document.getElementById('nextBtn')?.focus();
          loaded = true;
          return;
        }
        target.innerHTML = providers.map(provider => {
          const website = window.hofPartnerProfile.websiteUrl(provider.website_url), logo = window.hofPartnerProfile.websiteUrl(provider.logo_url);
          const label = `Sponsored · ${window.hofPartnerProfile.placementLabel(provider)}`;
          const portrait = (window.hofPartnerProfile.portrait?.(provider, esc) || "");
          return `<div class="hof-inspection-partner${logo ? "" : " no-logo"}${portrait ? ' has-portrait' : ''}">${logo ? `<a class="hof-inspection-partner-logo" href="${esc(website)}" target="_blank" rel="noopener noreferrer" data-insurance-brand="${esc(provider.id)}"><img src="${esc(logo)}" alt="${esc(provider.partner_name)} logo" loading="lazy" decoding="async"></a>` : ''}<div class="hof-inspection-partner-copy">${portrait}<div class="hof-inspection-label">Home insurance · ${label}</div><strong>${esc(provider.partner_name)}</strong><p>${esc(provider.market_area || 'Contact for service area')}.</p><p>Explore coverage and request a quote directly with the agent.</p>${window.hofPartnerProfile.actions(provider, esc, 'data-partner-link')}</div></div>`;
        }).join('') + '<p class="hof-inspection-choice">Optional service providers. Choose any provider or none. Your information is not shared automatically.</p>';
        target.hidden = false;
        if (moveFocus) {
          target.tabIndex = -1;
          target.focus();
        }
        target.querySelectorAll('[data-partner-link], [data-insurance-brand]').forEach(link => {
          const id = link.dataset.partnerId || link.dataset.insuranceBrand;
          const provider = providers.find(p => String(p.id) === id);
          if (provider) link.addEventListener('click', () => event('partner_directory_outbound_click', provider));
        });
        providers.forEach(provider => { if (!shown.has(provider.id)) { shown.add(provider.id); event('partner_directory_impression', provider); } });
        loaded = true;
      } catch (_) {
        if (visible()) {
          const moveFocus = restoreFocus();
          target.innerHTML = '<p class="hof-partner-load-status" role="status" aria-live="polite"><span>Optional insurance suggestions are temporarily unavailable. Your planning can continue without them.</span><button class="btn-secondary" type="button" data-partner-retry>Try again</button></p>';
          target.hidden = false;
          const nextRetry = target.querySelector('[data-partner-retry]');
          nextRetry?.addEventListener('click', render);
          if (moveFocus) nextRetry?.focus();
        }
      }
      finally {
        loading = false;
        if (retry) {
          retry.removeAttribute('aria-disabled');
          retry.textContent = 'Try again';
        }
      }
    }
    planner.addEventListener('toggle', render);
    new MutationObserver(render).observe(step, {attributes:true,attributeFilter:['class']});
    void render();
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', start, {once:true});
  else start();
}());
