// Keep public discovery pages installable without adding an app-store or
// third-party dependency. The main workspace owns update prompts; public
// pages only need to register the same lightweight shell service worker.
(() => {
  const guideKind = {
    '/texas-agent-offer-workflow': 'offer',
    '/texas-listing-workflow': 'listing',
    '/texas-lease-offer-workflow': 'lease',
    '/texas-agent-form-library': 'form_library',
  }[window.location.pathname];
  if (guideKind) {
    const metrics = document.createElement('script');
    metrics.defer = true;
    metrics.src = '/assets/agent-workflow-guide-metrics.js';
    document.head.appendChild(metrics);
  }
  if (window.location.pathname === '/texas-fsbo-closing-checklist') {
    const metrics = document.createElement('script');
    metrics.defer = true;
    metrics.src = '/assets/fsbo-closing-checklist-metrics.js';
    document.head.appendChild(metrics);
  }
  if (guideKind === 'offer' || guideKind === 'listing' || guideKind === 'lease' || guideKind === 'form_library') {
    const addTrialPath = () => {
      const actions = document.querySelector('main .actions');
      if (!actions || document.getElementById('hofGuideTrialCta')) return;
      if (guideKind !== 'form_library' && !document.getElementById('hofGuideLibraryCta')) {
        const libraryLink = document.createElement('a');
        libraryLink.id = 'hofGuideLibraryCta';
        libraryLink.className = 'button secondary';
        libraryLink.href = '/texas-agent-form-library?utm_source=agent_workspace&utm_medium=pwa_shortcut&utm_campaign=form_library';
        libraryLink.textContent = 'Open the shared form library';
        actions.appendChild(libraryLink);
      }
      const link = document.createElement('a');
      link.id = 'hofGuideTrialCta';
      link.className = 'button secondary';
      const source = guideKind === 'form_library' ? 'agent_form_library' : `organic_${guideKind}_workflow`;
      link.href = `/ondemand?utm_source=${source}&utm_medium=guide&utm_campaign=agent_acquisition`;
      link.textContent = 'See the OnDemand 60-day plan';
      actions.appendChild(link);
    };
    if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', addTrialPath, {once: true});
    else addTrialPath();
  }
  if (window.location.pathname === '/agents') {
    const tagAgentTrialLinks = () => {
      const actions = document.querySelector('main .actions');
      if (actions && !document.getElementById('hofAgentFormLibraryCta')) {
        const libraryLink = document.createElement('a');
        libraryLink.id = 'hofAgentFormLibraryCta';
        libraryLink.className = 'button secondary';
        libraryLink.href = '/texas-agent-form-library?utm_source=agent_workspace&utm_medium=agent_page&utm_campaign=form_library';
        libraryLink.textContent = 'See the shared form library';
        actions.appendChild(libraryLink);
      }
      document.querySelectorAll('a[href^="/ondemand"]').forEach(link => {
        if (!link.href.includes('utm_source=')) {
          link.href = '/ondemand?utm_source=agent_workspace&utm_medium=agent_page&utm_campaign=agent_acquisition';
        }
      });
    };
    if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', tagAgentTrialLinks, {once: true});
    else tagAgentTrialLinks();
  }
  if (window.location.pathname === '/sellers') {
    const addUnderContractPath = () => {
      const question = document.getElementById('seller-question-one')?.closest('section');
      if (!question || document.getElementById('hofSellerClosingChecklistCta')) return;
      const note = document.createElement('p');
      note.id = 'hofSellerClosingChecklistCta';
      note.className = 'note';
      note.style.marginTop = '1rem';
      note.innerHTML = '<strong>Already under contract?</strong> Keep closing deadlines and open questions organized before your next handoff. <a href="/texas-fsbo-closing-checklist?utm_source=seller_question_one&amp;utm_medium=owned_navigation&amp;utm_campaign=seller_acquisition" style="color:inherit;font-weight:800">Open the FSBO closing checklist →</a>';
      question.insertAdjacentElement('afterend', note);
    };
    if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', addUnderContractPath, {once: true});
    else addUnderContractPath();
  }
  if (window.location.pathname === '/texas-buyer-representation-guide') {
    const addWrittenAgreementReminder = () => {
      const lead = document.querySelector('main .lead');
      if (!lead || document.getElementById('hofWrittenAgreementReminder')) return;
      const note = document.createElement('p');
      note.id = 'hofWrittenAgreementReminder';
      note.className = 'note';
      note.innerHTML = '<strong>2026 Texas workflow reminder:</strong> Texas REALTORS® explains that a written agreement is required before showing residential property to a prospective buyer, or—if there is no showing—before presenting a purchase offer on the buyer’s behalf. Follow your brokerage-approved process and <a href="https://www.texasrealestate.com/wp-content/uploads/Written-Agreement-Explainer.pdf" target="_blank" rel="noopener noreferrer" style="color:inherit;font-weight:800">review the official explainer ↗</a>.';
      lead.insertAdjacentElement('afterend', note);
    };
    if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', addWrittenAgreementReminder, {once: true});
    else addWrittenAgreementReminder();
  }
  if (!('serviceWorker' in navigator)) return;
  let deferredInstallPrompt = null;
  const dismissKey = 'hof_public_pwa_install_dismissed_v1';
  const trackInstallEvent = (event, extra = {}) => {
    try {
      window.va = window.va || function () { (window.vaq = window.vaq || []).push(arguments); };
      window.va('event', { name: `Public PWA Install ${event}`, ...extra, surface: window.location.pathname });
    } catch (_) {}
  };
  const isMobileInstallSurface = () => /Android|iPhone|iPad|iPod/i.test(navigator.userAgent || '')
    || (navigator.maxTouchPoints > 1 && /Macintosh/i.test(navigator.userAgent || ''));
  const isIosInstallSurface = () => /iPhone|iPad|iPod/i.test(navigator.userAgent || '')
    || (navigator.maxTouchPoints > 1 && /Macintosh/i.test(navigator.userAgent || ''));
  const isStandaloneSurface = () => window.matchMedia?.('(display-mode: standalone)').matches === true
    || window.navigator.standalone === true;
  const publicInstallEvents = {
    Shown: 'shown', NativeAvailable: 'native_available', CtaClicked: 'cta_clicked',
    PromptOpened: 'prompt_opened', Accepted: 'accepted', Dismissed: 'dismissed',
    Installed: 'installed', InstructionsOpened: 'instructions_opened',
  };
  const publicInstallPlatform = () => /iPhone|iPad|iPod/i.test(navigator.userAgent || '')
    || (navigator.maxTouchPoints > 1 && /Macintosh/i.test(navigator.userAgent || '')) ? 'ios'
    : /Android/i.test(navigator.userAgent || '') ? 'android' : 'web';
  const trackPublicInstallEvent = event => {
    const eventKey = publicInstallEvents[event];
    if (!eventKey) return;
    try {
      const key = `hof_public_pwa_install_${eventKey}_${window.location.pathname}`;
      if (sessionStorage.getItem(key) === '1') return;
      sessionStorage.setItem(key, '1');
      fetch('/api/fsbo-lead', {
        method: 'POST', headers: {'Content-Type': 'application/json'}, keepalive: true,
        body: JSON.stringify({request_type: 'public_pwa_install_event', event_type: `pwa_install_${eventKey}`, platform: publicInstallPlatform(), surface: window.location.pathname}),
      }).catch(() => {});
    } catch (_) {}
  };
  const trackPublicInstall = event => { trackInstallEvent(event); trackPublicInstallEvent(event); };
  const removeInstallCard = () => document.getElementById('hofPublicPwaInstallCard')?.remove();
  const renderOfflineNotice = () => {
    let notice = document.getElementById('hofPublicPwaOfflineNotice');
    if (navigator.onLine !== false) {
      notice?.remove();
      return;
    }
    if (notice) return;
    notice = document.createElement('aside');
    notice.id = 'hofPublicPwaOfflineNotice';
    notice.setAttribute('role', 'status');
    notice.setAttribute('aria-live', 'polite');
    notice.style.cssText = 'position:fixed;left:1rem;right:1rem;bottom:1rem;z-index:19;margin:auto;max-width:32rem;padding:.75rem .9rem;border:1px solid rgba(200,151,63,.55);border-radius:12px;background:#10243a;color:#fff;box-shadow:0 12px 30px rgba(0,0,0,.24);font:14px/1.4 Arial,sans-serif;';
    notice.textContent = 'You are offline. This saved public page remains available; sign-in, live searches, and submissions resume when you reconnect.';
    document.body.appendChild(notice);
  };
  const showUpdateNotice = registration => {
    if (!isMobileInstallSurface() || !registration?.waiting || document.getElementById('hofPublicPwaUpdateNotice')) return;
    const notice = document.createElement('aside');
    notice.id = 'hofPublicPwaUpdateNotice';
    notice.setAttribute('role', 'status');
    notice.setAttribute('aria-live', 'polite');
    notice.style.cssText = 'position:fixed;right:1rem;bottom:1rem;z-index:20;max-width:min(23rem,calc(100% - 2rem));padding:.8rem .9rem;border:1px solid rgba(109,179,143,.45);border-radius:12px;background:#10243a;color:#fff;box-shadow:0 12px 30px rgba(0,0,0,.28);font:14px/1.4 Arial,sans-serif;';
    notice.innerHTML = '<strong style="display:block;color:#bce8d0;margin-bottom:.2rem">A newer HomeOfferFlow version is ready</strong><span style="display:block;color:#b6c4d5;margin-bottom:.55rem">Refresh when you are finished with this page to use the latest app shell.</span><button type="button" id="hofPublicPwaUpdateButton" style="padding:.45rem .65rem;border:0;border-radius:7px;background:#6db38f;color:#102033;font-weight:800;cursor:pointer">Refresh for latest version</button>';
    document.body.appendChild(notice);
    notice.querySelector('#hofPublicPwaUpdateButton')?.addEventListener('click', () => {
      registration.waiting?.postMessage({ type: 'HOF_SKIP_WAITING' });
      window.location.reload();
    });
  };
  const renderInstallCard = () => {
    if (!isMobileInstallSurface() || isStandaloneSurface() || (!deferredInstallPrompt && !isIosInstallSurface()) || document.getElementById('hofPublicPwaInstallCard')) return;
    try { if (sessionStorage.getItem(dismissKey) === '1') return; } catch (_) {}
    const card = document.createElement('aside');
    card.id = 'hofPublicPwaInstallCard';
    card.setAttribute('aria-label', 'HomeOfferFlow app installation');
    card.style.cssText = 'position:fixed;right:1rem;bottom:1rem;z-index:20;max-width:min(22rem,calc(100% - 2rem));padding:.8rem .9rem;border:1px solid rgba(200,151,63,.45);border-radius:12px;background:#10243a;color:#fff;box-shadow:0 12px 30px rgba(0,0,0,.28);font:14px/1.4 Arial,sans-serif;';
    const formLibrarySurface = window.location.pathname === '/texas-agent-form-library';
    const partnerSurface = window.location.pathname === '/partners';
    const sellerOfferReviewSurface = window.location.pathname === '/texas-seller-offer-review';
    const onDemandSurface = window.location.pathname === '/ondemand';
    const buyerSurface = window.location.pathname === '/buyers';
    const buyerGuideSurface = window.location.pathname === '/texas-homebuyer-offer-guide';
    const investorGuideSurface = window.location.pathname === '/texas-investor-offer-guide';
    const sellerSurface = window.location.pathname === '/sellers';
    const agentSurface = window.location.pathname === '/agents';
    const agentGuideSurface = Boolean(guideKind);
    const investorSurface = window.location.pathname === '/investors';
    const directorySurface = window.location.pathname === '/directory';
    const fsboGuideSurface = window.location.pathname === '/texas-fsbo-guide';
    const sellerNetProceedsSurface = window.location.pathname === '/texas-seller-net-proceeds-calculator';
    const title = formLibrarySurface
      ? 'Keep the Texas form library one tap away'
      : partnerSurface
      ? 'Keep partner placements one tap away'
      : sellerOfferReviewSurface
      ? 'Keep seller offer review one tap away'
      : onDemandSurface
      ? 'Keep your agent workspace one tap away'
      : buyerSurface
      ? 'Keep your buyer offer one tap away'
      : buyerGuideSurface
      ? 'Keep your buyer offer plan one tap away'
      : investorGuideSurface
      ? 'Keep your investor offer plan one tap away'
      : sellerSurface
      ? 'Keep your seller plan one tap away'
      : agentSurface
      ? 'Keep your agent workspace one tap away'
      : agentGuideSurface
      ? guideKind === 'listing'
        ? 'Keep your listing workflow one tap away'
        : guideKind === 'lease'
        ? 'Keep your lease workflow one tap away'
        : guideKind === 'form_library'
        ? 'Keep the Texas form library one tap away'
        : 'Keep your offer workflow one tap away'
      : investorSurface
      ? 'Keep your investor workspace one tap away'
      : directorySurface
      ? 'Keep the provider directory one tap away'
      : fsboGuideSurface
      ? 'Keep your FSBO plan one tap away'
      : sellerNetProceedsSurface
      ? 'Keep your seller proceeds worksheet one tap away'
      : 'Keep HomeOfferFlow one tap away';
    const copy = formLibrarySurface
      ? 'Install the lightweight app shell to return quickly to the shared form guide and Question 1.'
      : partnerSurface
      ? 'Install the lightweight app shell to return quickly to partner pricing, your application, and setup details.'
      : sellerOfferReviewSurface
      ? 'Install the lightweight app shell to return quickly to your seller offer-review checklist and next conversation.'
      : onDemandSurface
      ? 'Install the lightweight app shell to return quickly to your OnDemand agent workspace and first saved offer.'
      : buyerSurface
      ? 'Install the lightweight app shell to return quickly to your saved offer and review summary.'
      : buyerGuideSurface
      ? 'Install the lightweight app shell to return quickly to your buyer checklist and offer workflow.'
      : investorGuideSurface
      ? 'Install the lightweight app shell to return quickly to your investor checklist and repeat-offer workflow.'
      : sellerSurface
      ? 'Install the lightweight app shell to return quickly to your seller plan and support paths.'
      : agentSurface
      ? 'Install the lightweight app shell to return quickly to Question 1, drafts, and your workspace.'
      : agentGuideSurface
      ? guideKind === 'listing'
        ? 'Install the lightweight app shell to return quickly to your listing plan, offer comparison, and next action.'
        : guideKind === 'lease'
        ? 'Install the lightweight app shell to return quickly to your lease workflow and next client step.'
        : guideKind === 'form_library'
        ? 'Install the lightweight app shell to return quickly to the shared form library and Question 1.'
        : 'Install the lightweight app shell to return quickly to your offer workflow and Question 1.'
      : investorSurface
      ? 'Install the lightweight app shell to return quickly to saved investor defaults and repeat-offer tools.'
      : directorySurface
      ? 'Install the lightweight app shell to return quickly to provider search and partner placement paths.'
      : fsboGuideSurface
      ? 'Install the lightweight app shell to return quickly to your seller plan and support paths.'
      : sellerNetProceedsSurface
      ? 'Install the lightweight app shell to return quickly to your private proceeds worksheet and seller planning paths.'
      : 'Install the lightweight app shell for faster returns to your workspace.';
    const iosInstall = isIosInstallSurface() && !deferredInstallPrompt;
    card.innerHTML = `<strong style="display:block;color:#e8b86d;margin-bottom:.2rem">${title}</strong><span style="display:block;color:#b6c4d5;margin-bottom:.55rem">${copy}</span><div style="display:flex;gap:.45rem;flex-wrap:wrap"><button type="button" id="hofPublicPwaInstallButton" style="padding:.45rem .65rem;border:0;border-radius:7px;background:#c8973f;color:#102033;font-weight:800;cursor:pointer">${iosInstall ? 'Show install steps' : 'Install app'}</button><button type="button" id="hofPublicPwaInstallDismiss" style="padding:.45rem .65rem;border:1px solid rgba(255,255,255,.25);border-radius:7px;background:transparent;color:#fff;cursor:pointer">Not now</button></div><div id="hofPublicPwaInstallNote" role="status" aria-live="polite" style="display:none;margin-top:.55rem;color:#b6c4d5;font-size:.8rem;line-height:1.45"></div>`;
    document.body.appendChild(card);
    trackPublicInstall('Shown');
    card.querySelector('#hofPublicPwaInstallDismiss')?.addEventListener('click', () => {
      try { sessionStorage.setItem(dismissKey, '1'); } catch (_) {}
      trackPublicInstall('Dismissed');
      removeInstallCard();
    });
    card.querySelector('#hofPublicPwaInstallButton')?.addEventListener('click', async () => {
      if (!deferredInstallPrompt) {
        const note = card.querySelector('#hofPublicPwaInstallNote');
        if (note) {
          note.style.display = 'block';
          note.textContent = 'In Safari, tap Share, then choose Add to Home Screen. The lightweight HomeOfferFlow app will open from your new icon.';
        }
        trackPublicInstall('InstructionsOpened');
        return;
      }
      const prompt = deferredInstallPrompt;
      deferredInstallPrompt = null;
      removeInstallCard();
      trackPublicInstall('CtaClicked');
      await prompt.prompt();
      trackPublicInstall('PromptOpened');
      await prompt.userChoice.then(choice => trackPublicInstall(choice?.outcome === 'accepted' ? 'Accepted' : 'Dismissed')).catch(() => {});
    });
  };
  window.addEventListener('beforeinstallprompt', event => {
    if (!isMobileInstallSurface()) return;
    event.preventDefault();
    deferredInstallPrompt = event;
    trackPublicInstall('NativeAvailable');
    renderInstallCard();
  });
  window.addEventListener('appinstalled', () => { trackPublicInstall('Installed'); deferredInstallPrompt = null; removeInstallCard(); });
  window.addEventListener('load', () => { if (isIosInstallSurface()) renderInstallCard(); }, { once: true });
  window.addEventListener('offline', renderOfflineNotice);
  window.addEventListener('online', renderOfflineNotice);
  window.addEventListener('load', renderOfflineNotice, { once: true });
  window.addEventListener('load', () => {
    navigator.serviceWorker.register('/service-worker.js', { scope: '/' }).then(registration => {
      showUpdateNotice(registration);
      registration.addEventListener('updatefound', () => {
        const installing = registration.installing;
        installing?.addEventListener('statechange', () => {
          if (installing.state === 'installed' && navigator.serviceWorker.controller) showUpdateNotice(registration);
        });
      });
    }).catch(() => {});
  }, { once: true });
})();
