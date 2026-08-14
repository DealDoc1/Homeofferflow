(() => {
  // The campaign toolkit can target every current seller package. Preserve
  // that exact allowlisted selection through this explanatory page and into
  // the shared intake instead of silently reverting to the free path.
  const source = new URLSearchParams(window.location.search);
  const packages = {
    free_intake: { label: 'Free Seller Intake', cta: 'Get my free seller plan' },
    seller_prep: { label: 'Seller Prep Plan', cta: 'Request seller prep details' },
    launch_kit: { label: 'FSBO Launch Kit', cta: 'Request FSBO launch kit details' },
    flat_fee_mls: { label: 'Flat-Fee MLS Listing', cta: 'Request flat-fee MLS details' },
    offer_review: { label: 'Seller Offer Review', cta: 'Request seller offer review details' },
    contract_help: { label: 'Contract-to-Close Support', cta: 'Request contract-to-close details' },
    premium_bundle: { label: 'Premium FSBO Bundle', cta: 'Request premium bundle details' }
  };
  const selected = String(source.get('seller_package') || '').trim().toLowerCase();
  if (!Object.prototype.hasOwnProperty.call(packages, selected)) return;
  const selectedPackage = packages[selected];

  const context = document.getElementById('sellerCampaignContext');
  if (context) {
    context.hidden = false;
    context.textContent = `Your selected path: ${selectedPackage.label}. You can start this intake now or compare the options below—nothing is purchased or committed here.`;
  }
  // The inline campaign-preservation script may already have changed the
  // destination package before this deferred bridge runs.  Identify the
  // primary/free-intake calls by their original copy as well, so their label
  // always matches the selected campaign path instead of implying that a
  // paid-path visitor is starting the free package.
  const primaryCtaLabels = new Set([
    'Start free seller intake',
    'Get my free seller plan',
    'Tell us about your property'
  ]);
  document.querySelectorAll('[data-seller-apply]').forEach(link => {
    const isCampaignPrimaryCta = primaryCtaLabels.has(link.textContent.trim());
    const destination = new URL(link.href, window.location.origin);
    if (destination.searchParams.get('seller_package') === 'free_intake') {
      destination.searchParams.set('seller_package', selected);
      link.href = destination.pathname + '?' + destination.searchParams.toString();
    }
    if (isCampaignPrimaryCta) {
      link.textContent = selectedPackage.cta;
    }
  });
  try { window.va?.('event', { name: 'FSBO Seller Expanded Campaign Landing Viewed', sellerPackage: selected }); } catch (_) {}
})();
