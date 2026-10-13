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
  const actions = (provider, esc, marker) => {
    if (!['data-partner-link', 'data-offer-completion-partner-link'].includes(marker)) return '';
    const attrs = `${marker} data-partner-id="${esc(provider.id)}" data-partner-type="${esc(provider.partner_type)}" data-placement-tier="${esc(provider.placement_tier)}"`;
    const website = websiteUrl(provider.website_url), phone = phoneUrl(provider);
    const name = String(provider.public_contact_name || '').trim().slice(0, 80);
    return `<div class="hof-partner-actions">${website ? `<a href="${esc(website)}" ${attrs} target="_blank" rel="noopener noreferrer">${esc(websiteLabel(provider))} ↗</a>` : ''}${phone ? `<a href="${esc(phone)}" ${attrs} aria-label="${esc((name ? 'Call ' + name : 'Call') + ' at ' + provider.public_contact_phone)}">${esc(name ? 'Call ' + name : 'Call')} →</a>` : ''}</div>`;
  };
  window.hofPartnerProfile = Object.freeze({ websiteUrl, phoneUrl, websiteLabel, actions });
}());
