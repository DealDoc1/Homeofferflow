(function () {
  'use strict';
  const websiteUrl = value => {
    try {
      const url = new URL(String(value || ''));
      return ['https:', 'http:'].includes(url.protocol) && !url.username && !url.password ? url.href : '';
    } catch (_) { return ''; }
  };
  const phoneUrl = provider => /^\+[1-9][0-9]{9,14}$/.test(String(provider.public_contact_phone || ''))
    ? 'tel:' + provider.public_contact_phone : '';
  const websiteLabel = provider => {
    const label = String(provider.cta_label || '').trim().slice(0, 80);
    return label && !/^(call|text|sms|phone)\b/i.test(label) ? label : 'Visit website';
  };
  const portrait = (provider, esc) => {
    const url = websiteUrl(provider.public_headshot_url);
    if (!url || !url.startsWith('https:')) return '';
    const name = String(provider.public_contact_name || '').trim().slice(0, 80);
    return `<span class="hof-partner-portrait-slot"><img class="hof-partner-headshot" src="${esc(url)}" alt="${esc(name ? name + ', company representative' : 'Company representative')}" width="64" height="64" loading="lazy" decoding="async" referrerpolicy="no-referrer"></span>`;
  };
  const actions = (provider, esc, marker) => {
    if (!['data-partner-link', 'data-offer-completion-partner-link', 'data-inspection-partner-link'].includes(marker)) return '';
    const attrs = `${marker} data-partner-id="${esc(provider.id)}" data-partner-type="${esc(provider.partner_type)}" data-placement-tier="${esc(provider.placement_tier)}"`;
    const website = websiteUrl(provider.website_url), phone = phoneUrl(provider);
    const name = String(provider.public_contact_name || '').trim().slice(0, 80);
    return `<div class="hof-partner-actions">${website ? `<a href="${esc(website)}" ${attrs} target="_blank" rel="noopener noreferrer">${esc(websiteLabel(provider))} ↗</a>` : ''}${phone ? `<a href="${esc(phone)}" ${attrs} aria-label="${esc((name ? 'Call ' + name : 'Call') + ' at ' + provider.public_contact_phone)}">${esc(name ? 'Call ' + name : 'Call')} →</a>` : ''}</div>`;
  };
  const placementTierLabel = partner => partner?.placement_tier === 'exclusive_market' ? 'Premier Partner'
    : partner?.placement_tier === 'premier' ? 'Featured Partner'
    : 'Partner';
  const placementLabel = partner => {
    const tierLabel = placementTierLabel(partner);
    if (!partner?.is_category_founder) return tierLabel;
    return tierLabel === 'Partner' ? 'Founding Partner' : `Founding Partner · ${tierLabel}`;
  };
  const topWorkflowPremier = partners => Array.isArray(partners)
    ? partners.find(partner => partner?.placement_tier === 'exclusive_market') || null
    : null;
  const directoryRequests = new Map();
  if (typeof document !== 'undefined') document.addEventListener('error', event => {
    if (!event.target?.matches?.('.hof-partner-headshot')) return;
    event.target.parentElement.hidden = true;
    event.target.closest('.has-portrait')?.classList.remove('has-portrait');
  }, true);
  const load = surface => {
    const view = surface === 'workflow' ? 'workflow' : 'directory';
    const current = directoryRequests.get(view);
    if (!current || Date.now() >= current.expiresAt) {
      const query = new URLSearchParams({partner_directory:'1',surface:view});
      const request = fetch('/api/fsbo-lead?' + query)
      .then(async response => {
        const result = await response.json();
        if (!response.ok || !result.ok) throw new Error('Directory unavailable');
        return Array.isArray(result.partners) ? result.partners : [];
      }).catch(error => {
        if (directoryRequests.get(view)?.request === request) directoryRequests.delete(view);
        throw error;
      });
      directoryRequests.set(view,{expiresAt:Date.now()+300000,request});
    }
    return directoryRequests.get(view).request;
  };
  window.hofPartnerProfile = Object.freeze({ websiteUrl, phoneUrl, websiteLabel, placementLabel, topWorkflowPremier, portrait, actions, load });
}());
