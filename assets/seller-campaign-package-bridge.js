(() => {
  // The campaign toolkit can target every current seller package. Preserve
  // that exact allowlisted selection through this explanatory page and into
  // the shared intake instead of silently reverting to the free path.
  const source = new URLSearchParams(window.location.search);
  const labels = {
    free_intake: 'Free Seller Intake',
    seller_prep: 'Seller Prep Plan',
    launch_kit: 'FSBO Launch Kit',
    flat_fee_mls: 'Flat-Fee MLS Listing',
    offer_review: 'Seller Offer Review',
    contract_help: 'Contract-to-Close Support',
    premium_bundle: 'Premium FSBO Bundle'
  };
  const selected = String(source.get('seller_package') || '').trim().toLowerCase();
  if (!Object.prototype.hasOwnProperty.call(labels, selected)) return;

  const context = document.getElementById('sellerCampaignContext');
  if (context) {
    context.hidden = false;
    context.textContent = `Your selected path: ${labels[selected]}. You can start this intake now or compare the options below—nothing is purchased or committed here.`;
  }
  document.querySelectorAll('[data-seller-apply]').forEach(link => {
    const destination = new URL(link.href, window.location.origin);
    if (destination.searchParams.get('seller_package') === 'free_intake') {
      destination.searchParams.set('seller_package', selected);
      link.href = destination.pathname + '?' + destination.searchParams.toString();
    }
  });
  try { window.va?.('event', { name: 'FSBO Seller Expanded Campaign Landing Viewed', sellerPackage: selected }); } catch (_) {}
})();
