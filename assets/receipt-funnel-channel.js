// Preserve receipt-specific campaign attribution in the aggregate landing
// events already emitted by the seller and partner pages.
(() => {
  const medium = String(new URLSearchParams(window.location.search).get('utm_medium') || '').trim().toLowerCase();
  const receiptChannel = medium === 'seller_receipt' ? 'seller_receipt' : medium === 'partner_receipt' ? 'partner_receipt' : '';
  if (!receiptChannel) return;
  const originalFetch = window.fetch.bind(window);
  window.fetch = (input, init = {}) => {
    try {
      const body = typeof init.body === 'string' ? JSON.parse(init.body) : null;
      const expectedType = receiptChannel === 'seller_receipt' ? 'fsbo_landing_event' : 'partner_landing_event';
      if (body?.request_type === expectedType && (!body.channel || body.channel === 'unspecified' || body.channel === 'direct')) {
        body.channel = receiptChannel;
        init = { ...init, body: JSON.stringify(body) };
      }
    } catch (_) {}
    return originalFetch(input, init);
  };
})();
