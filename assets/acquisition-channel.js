(() => {
  const outreachChannels = new Set([
    'direct_outreach',
    'email',
    'social',
    'referral',
    'local_event',
    'print',
  ]);
  const searchHosts = [
    /(^|\.)google\./,
    /(^|\.)bing\.com$/,
    /(^|\.)search\.yahoo\.com$/,
    /(^|\.)duckduckgo\.com$/,
    /(^|\.)ecosia\.org$/,
    /(^|\.)search\.brave\.com$/,
    /(^|\.)yandex\./,
    /(^|\.)baidu\.com$/,
  ];

  function referrerChannel() {
    try {
      if (!document.referrer) return 'direct';
      const referrer = new URL(document.referrer);
      if (referrer.origin === window.location.origin) return 'direct';
      return searchHosts.some((pattern) => pattern.test(referrer.hostname.toLowerCase()))
        ? 'organic'
        : 'referral';
    } catch (_) {
      return 'direct';
    }
  }

  window.hofAcquisitionChannel = function acquisitionChannel() {
    const params = new URLSearchParams(window.location.search);
    const source = String(params.get('utm_source') || '').trim().toLowerCase();
    const medium = String(params.get('utm_medium') || '').trim().toLowerCase();
    if (medium === 'installed_app' || source === 'pwa_shortcut') return 'pwa_shortcut';
    if (medium === 'organic_content' || source === 'organic') return 'organic';
    if (source === 'homeofferflow' || medium === 'homepage') return 'homepage';
    if (source === 'homeofferflow_admin' && outreachChannels.has(medium)) return medium;
    if (outreachChannels.has(source)) return source;
    return referrerChannel();
  };
})();
