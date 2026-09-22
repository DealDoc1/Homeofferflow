(function initUnderContractCompanion(root) {
  'use strict';

  const TRACKING_VERSION = 1;

  function escapeHtml(value) {
    return String(value ?? '').replace(/[&<>"']/g, char => ({
      '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
    }[char]));
  }

  function validDate(value) {
    const match = String(value || '').match(/^(\d{4})-(\d{2})-(\d{2})$/);
    if (!match) return null;
    const date = new Date(Date.UTC(Number(match[1]), Number(match[2]) - 1, Number(match[3])));
    return date.getUTCFullYear() === Number(match[1])
      && date.getUTCMonth() === Number(match[2]) - 1
      && date.getUTCDate() === Number(match[3]) ? date : null;
  }

  function isoDate(date) {
    return date instanceof Date && !Number.isNaN(date.getTime())
      ? date.toISOString().slice(0, 10)
      : '';
  }

  function addCalendarDays(value, days) {
    const date = validDate(value);
    const amount = Number(days);
    if (!date || !Number.isSafeInteger(amount) || amount < 0) return '';
    date.setUTCDate(date.getUTCDate() + amount);
    return isoDate(date);
  }

  function calendarKey(value) {
    const date = validDate(value);
    return date ? isoDate(date).replace(/-/g, '') : '';
  }

  function nextDate(value) {
    return addCalendarDays(value, 1);
  }

  function calendarEscape(value) {
    return String(value || '').replace(/\\/g, '\\\\').replace(/;/g, '\\;').replace(/,/g, '\\,').replace(/\r?\n/g, '\\n');
  }

  function formatDate(value) {
    const date = validDate(value);
    if (!date) return '';
    return new Intl.DateTimeFormat(undefined, { month: 'short', day: 'numeric', year: 'numeric', timeZone: 'UTC' }).format(date);
  }

  function buildCalendar({ property = '', effectiveDate = '', optionDeadline = '', closingDate = '' } = {}) {
    const events = [];
    const address = String(property || '').trim();
    const withProperty = label => address ? `${label} — ${address}` : label;
    const addAllDayEvent = (date, summary, description) => {
      if (!validDate(date)) return;
      events.push([
        'BEGIN:VEVENT',
        `UID:homeofferflow-${calendarKey(date)}-${events.length + 1}@homeofferflow.com`,
        `DTSTART;VALUE=DATE:${calendarKey(date)}`,
        `DTEND;VALUE=DATE:${calendarKey(nextDate(date))}`,
        `SUMMARY:${calendarEscape(summary)}`,
        `DESCRIPTION:${calendarEscape(description)}`,
        'END:VEVENT'
      ].join('\r\n'));
    };

    addAllDayEvent(
      effectiveDate,
      withProperty('Contract effective date'),
      'Date entered from the fully signed contract. Confirm all deadlines with the contract and your transaction professional.'
    );
    addAllDayEvent(
      optionDeadline,
      withProperty('Option-period deadline'),
      'Review the fully signed contract. TREC 20-19 states that a Paragraph 5B termination notice must be given by 5:00 p.m. local time where the property is located on the specified date.'
    );
    addAllDayEvent(
      closingDate,
      withProperty('Target closing'),
      'Confirm the final date, time, location, and any later written changes with the fully signed contract and title company.'
    );

    if (!events.length) return '';
    const stamp = new Date().toISOString().replace(/[-:]/g, '').replace(/\.\d{3}/, '');
    return [
      'BEGIN:VCALENDAR',
      'VERSION:2.0',
      'PRODID:-//HomeOfferFlow//Under Contract Timeline//EN',
      'CALSCALE:GREGORIAN',
      `DTSTAMP:${stamp}`,
      ...events,
      'END:VCALENDAR',
      ''
    ].join('\r\n');
  }

  function offerList() {
    return Array.isArray(root.hofAuth?.myOffers) ? root.hofAuth.myOffers : [];
  }

  function findOffer(offerId) {
    return offerList().find(item => String(item?.id) === String(offerId)) || null;
  }

  function offerProperty(offer) {
    const data = offer?.offer_data || {};
    return offer?.property_address || data.propertyAddress || data.propAddress || 'This property';
  }

  function offerOptionDays(offer) {
    const raw = offer?.offer_data?.optionDays ?? offer?.offer_data?.option_days ?? offer?.option_days;
    const days = Number(raw);
    return Number.isSafeInteger(days) && days > 0 ? days : 0;
  }

  function downloadCalendar(offer, tracking) {
    const calendar = buildCalendar({
      property: offerProperty(offer),
      effectiveDate: tracking?.effectiveDate,
      optionDeadline: tracking?.optionDeadline,
      closingDate: tracking?.closingDate
    });
    if (!calendar) return false;
    const url = URL.createObjectURL(new Blob([calendar], { type: 'text/calendar;charset=utf-8' }));
    const link = document.createElement('a');
    link.href = url;
    link.download = `homeofferflow-contract-timeline-${calendarKey(tracking.effectiveDate || tracking.closingDate)}.ics`;
    document.body.appendChild(link);
    link.click();
    link.remove();
    root.setTimeout(() => URL.revokeObjectURL(url), 0);
    return true;
  }

  function announce(message) {
    root.announceWorkspaceStatus?.(message);
  }

  function renderSavedState(modal, offer, tracking) {
    const summary = modal.querySelector('#hofContractTimelineSummary');
    const form = modal.querySelector('form');
    if (form) form.hidden = true;
    if (!summary) return;
    const dates = [
      tracking.effectiveDate ? `<li><strong>Effective date:</strong> ${escapeHtml(formatDate(tracking.effectiveDate))}</li>` : '',
      tracking.optionDeadline ? `<li><strong>Option-period date:</strong> ${escapeHtml(formatDate(tracking.optionDeadline))} <span style="color:var(--gray-light)">(review the 5:00 p.m. property-local deadline in the contract)</span></li>` : '',
      tracking.closingDate ? `<li><strong>Target closing:</strong> ${escapeHtml(formatDate(tracking.closingDate))}</li>` : ''
    ].filter(Boolean).join('');
    summary.hidden = false;
    summary.innerHTML = `<div class="notice sage"><strong>Contract timeline saved.</strong><br>These dates remain attached to ${escapeHtml(offerProperty(offer))} in your private workspace.</div><ul style="margin:.9rem 0 1rem;padding-left:1.25rem;color:var(--gray-light);line-height:1.7">${dates}</ul><div class="hof-agreement-footer"><button type="button" class="btn-secondary" id="hofContractCalendarDownload">Download calendar</button><button type="button" class="btn-primary" id="hofContractTimelineDone">Done</button></div>`;
    summary.querySelector('#hofContractCalendarDownload')?.addEventListener('click', () => {
      if (downloadCalendar(offer, tracking)) {
        const eventWrite = root.logOfferEvent?.(offer.id, 'contract_timeline_calendar_downloaded', 'downloaded', 'Contract timeline calendar downloaded.', {
          surface: 'offer_workspace', has_option_date: Boolean(tracking.optionDeadline), has_closing_date: Boolean(tracking.closingDate)
        });
        eventWrite?.catch?.(() => {});
      }
    });
    summary.querySelector('#hofContractTimelineDone')?.addEventListener('click', () => modal.remove());
  }

  function open(offerId) {
    const offer = findOffer(offerId);
    const user = root.hofAuth?.session?.user;
    if (!offer || !user?.id) {
      announce('Sign in and refresh My Offers before opening the contract timeline.');
      return;
    }

    document.getElementById('hofUnderContractCompanion')?.remove();
    const data = offer.offer_data || {};
    const saved = data.transactionTracking || {};
    const optionDays = offerOptionDays(offer);
    const effectiveDate = saved.effectiveDate || '';
    const derivedOptionDate = optionDays ? addCalendarDays(effectiveDate, optionDays) : '';
    const closingDate = saved.closingDate || data.closingDate || data.closing_date || '';
    const modal = document.createElement('div');
    modal.id = 'hofUnderContractCompanion';
    modal.className = 'hof-agreement-modal';
    modal.innerHTML = `<div class="hof-agreement-dialog" role="dialog" aria-modal="true" aria-labelledby="hofContractTimelineTitle">
      <form id="hofContractTimelineForm">
        <p class="hof-agent-question-step">Accepted contract</p>
        <h3 id="hofContractTimelineTitle">Confirm the dates that control this transaction</h3>
        <p>Use the fully signed contract—not the original offer—to confirm these dates. HomeOfferFlow saves the dates and creates reminders; it does not change the contract or replace professional deadline review.</p>
        <div class="notice" style="margin-top:.8rem"><strong>${escapeHtml(offerProperty(offer))}</strong><br><span style="color:var(--gray-light)">${optionDays ? `${optionDays}-day option period requested in the saved offer.` : 'No option-period length is available in the saved offer.'}</span></div>
        <div class="hof-agreement-grid">
          <label>Effective date from signed contract<input name="effectiveDate" type="date" required value="${escapeHtml(effectiveDate)}"></label>
          <label>Target closing date<input name="closingDate" type="date" value="${escapeHtml(closingDate)}"><small>Confirm any later written change before relying on this reminder.</small></label>
          <label class="hof-agreement-wide">Option-period date<input name="optionDeadline" type="date" readonly value="${escapeHtml(derivedOptionDate)}"><small>${optionDays ? `Calculated as ${optionDays} calendar days after the effective date. Review Paragraph 5B and confirm the 5:00 p.m. local deadline for the property.` : 'Add the option-period length to the signed contract record before relying on a deadline.'}</small></label>
          <div class="hof-agreement-wide notice" style="font-size:.78rem;line-height:1.55"><strong>Also confirm separately:</strong> earnest money and option-fee delivery, title and survey dates, financing and appraisal dates, disclosure receipt dates, and every amendment. Some depend on receipt, weekends, legal holidays, or later events and are not calculated here.</div>
          <label class="hof-agreement-wide hof-agreement-services"><input name="contractConfirmed" type="checkbox" required> I confirm this offer was accepted and I entered the effective and closing dates from the fully signed contract.</label>
        </div>
        <div id="hofContractTimelineStatus" class="hof-iabs-status" role="status" aria-live="polite"></div>
        <div class="hof-agreement-footer"><button class="btn-secondary" type="button" id="hofContractTimelineCancel">Cancel</button><button class="btn-primary" type="submit">Save contract timeline</button></div>
      </form>
      <div id="hofContractTimelineSummary" hidden></div>
    </div>`;
    document.body.appendChild(modal);
    const form = modal.querySelector('form');
    const effectiveInput = form.elements.effectiveDate;
    const optionInput = form.elements.optionDeadline;
    const refreshOptionDate = () => { optionInput.value = optionDays ? addCalendarDays(effectiveInput.value, optionDays) : ''; };
    effectiveInput.addEventListener('change', refreshOptionDate);
    modal.querySelector('#hofContractTimelineCancel')?.addEventListener('click', () => modal.remove());
    modal.addEventListener('click', event => { if (event.target === modal) modal.remove(); });
    form.addEventListener('submit', async event => {
      event.preventDefault();
      const submit = form.querySelector('button[type="submit"]');
      const status = modal.querySelector('#hofContractTimelineStatus');
      if (!submit || submit.disabled) return;
      refreshOptionDate();
      const tracking = {
        version: TRACKING_VERSION,
        acceptedContractConfirmed: true,
        effectiveDate: effectiveInput.value,
        optionDeadline: optionInput.value,
        closingDate: form.elements.closingDate.value,
        updatedAt: new Date().toISOString()
      };
      submit.disabled = true;
      submit.setAttribute('aria-busy', 'true');
      submit.textContent = 'Saving timeline…';
      status.className = 'hof-iabs-status';
      status.textContent = 'Saving confirmed contract dates…';
      try {
        if (root.hofAuth?.session?.user?.id !== user.id) {
          throw new Error('Your signed-in account changed. Reopen the timeline from My Offers.');
        }
        const client = root.getSupabaseClient?.();
        if (!client) throw new Error('Workspace connection unavailable.');
        const latest = await client.from('hof_offers').select('offer_data').eq('user_id', user.id).eq('id', offer.id).single();
        if (latest.error) throw latest.error;
        const latestOfferData = latest.data?.offer_data || data;
        const nextOfferData = { ...latestOfferData, transactionTracking: tracking };
        const result = await client.from('hof_offers').update({
          offer_data: nextOfferData
        }).eq('user_id', user.id).eq('id', offer.id).select('*').single();
        if (result.error) throw result.error;
        Object.assign(offer, result.data || { offer_data: nextOfferData });
        if (!offer.offer_data?.transactionTracking) offer.offer_data = nextOfferData;
        renderSavedState(modal, offer, tracking);
        try {
          await root.logOfferEvent?.(offer.id, 'contract_timeline_saved', 'saved', 'Confirmed contract timeline saved.', {
            surface: 'offer_workspace', has_option_date: Boolean(tracking.optionDeadline), has_closing_date: Boolean(tracking.closingDate)
          });
        } catch (_) {}
        try {
          if (typeof root.renderMyOffers === 'function') {
            const list = document.getElementById('myOffersList');
            if (list) list.innerHTML = root.renderMyOffers(offerList());
          }
        } catch (_) {}
      } catch (error) {
        console.error('Contract timeline save failed:', error);
        status.className = 'hof-iabs-status error';
        status.textContent = root.hofCustomerActionError?.(error, 'We couldn’t save the contract timeline. Your offer is unchanged—please try again.') || 'We couldn’t save the contract timeline. Your offer is unchanged—please try again.';
        submit.disabled = false;
        submit.setAttribute('aria-busy', 'false');
        submit.textContent = 'Save contract timeline';
      }
    });
    effectiveInput.focus();
  }

  root.hofUnderContract = Object.freeze({
    open,
    addCalendarDays,
    buildCalendar,
    formatDate
  });
})(window);
