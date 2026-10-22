(function () {
  'use strict';
  const esc = value => String(value || '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  let loaded = false, loading = false;
  const shown = new Set();
  const event = (kind, provider) => {
    if (!/^[0-9a-f-]{36}$/i.test(String(provider.id || ''))) return;
    const body = {request_type:'partner_directory_event', event_type:kind, partner_id:provider.id, partner_type:provider.partner_type, placement_tier:provider.placement_tier, directory_surface:'inspection_interview'};
    void fetch('/api/fsbo-lead', {method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body),keepalive:true}).catch(() => {});
  };
  async function render() {
    const step = document.getElementById('step6'), target = document.getElementById('hofInspectionPartners');
    if (!step?.classList.contains('active') || !target || loaded || loading) return;
    loading = true;
    try {
      const providers = window.hofPartnerProfile.selectWorkflowPartners(await window.hofPartnerProfile.load()).filter(p => p.partner_type === 'roofing' && window.hofPartnerProfile.websiteUrl(p.website_url));
      if (!step.classList.contains('active') || document.getElementById('hofInspectionPartners') !== target) return;
      if (!providers.length) { loaded = true; return; }
      target.innerHTML = providers.map(provider => {
        const website = window.hofPartnerProfile.websiteUrl(provider.website_url), logo = window.hofPartnerProfile.websiteUrl(provider.logo_url);
        const label = provider.partner_program === 'beta' ? 'Beta partner · Premier Partner' : 'Sponsored · Premier Partner';
        const portrait = (window.hofPartnerProfile.portrait?.(provider, esc) || "");
        return `<div class="hof-inspection-partner${logo ? "" : " no-logo"}${portrait ? ' has-portrait' : ''}">${logo ? `<a class="hof-inspection-partner-logo" href="${esc(website)}" target="_blank" rel="noopener noreferrer" data-inspection-brand="${esc(provider.id)}"><img src="${esc(logo)}" alt="${esc(provider.partner_name)} logo" loading="lazy" decoding="async"></a>` : ''}<div class="hof-inspection-partner-copy">${portrait}<div class="hof-inspection-label">Roofing · ${label}</div><strong>${esc(provider.partner_name)}</strong><p>${esc(provider.market_area || 'Local service')} · Roof inspections, replacement and storm-damage support.</p>${window.hofPartnerProfile.actions(provider, esc, 'data-inspection-partner-link')}</div></div>`;
      }).join('') + '<p class="hof-inspection-choice">Optional service providers. You can choose any provider or none.</p>';
      target.hidden = false;
      target.querySelectorAll('[data-inspection-partner-link], [data-inspection-brand]').forEach(link => {
        const id = link.dataset.partnerId || link.dataset.inspectionBrand;
        const provider = providers.find(p => String(p.id) === id);
        if (provider) link.addEventListener('click', () => event('partner_directory_outbound_click', provider));
      });
      providers.forEach(provider => { if (!shown.has(provider.id)) { shown.add(provider.id); event('partner_directory_impression', provider); } });
      loaded = true;
    } catch (_) { target.hidden = true; }
    finally { loading = false; }
  }
  function start() {
    const step = document.getElementById('step6');
    if (!step) return;
    new MutationObserver(render).observe(step, {attributes:true,attributeFilter:['class']});
    void render();
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', start, {once:true});
  else start();
}());
