(function initUnderContractCompanion(root) {
  'use strict';

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
    return String(value || '').replace(/\\/g, '\\\\').replace(/;/g, '\\;').replace(/,/g, '\\,').replace(/\r\n|\r|\n/g, '\\n');
  }

  function foldCalendarLine(line) {
    let folded = '';
    let physicalLineBytes = 0;
    for (const character of String(line)) {
      const codePoint = character.codePointAt(0);
      const byteLength = codePoint <= 0x7f ? 1 : codePoint <= 0x7ff ? 2 : codePoint <= 0xffff ? 3 : 4;
      if (physicalLineBytes + byteLength > 75) {
        folded += '\r\n ';
        physicalLineBytes = 1;
      }
      folded += character;
      physicalLineBytes += byteLength;
    }
    return folded;
  }

  function formatDate(value) {
    const date = validDate(value);
    if (!date) return '';
    return new Intl.DateTimeFormat(undefined, { month: 'short', day: 'numeric', year: 'numeric', timeZone: 'UTC' }).format(date);
  }

  function normalizeMilestones(rows, { rejectDuplicates = false } = {}) {
    if (rows == null) return [];
    if (!Array.isArray(rows) || rows.length > 12) {
      throw new Error('Add no more than 12 confirmed dates.');
    }
    const milestones = [];
    const seen = new Set();
    for (const row of rows) {
      const label = String(row?.label || '').trim();
      const date = String(row?.date || '').trim();
      if (!label && !date) continue;
      if (label.length < 2 || label.length > 80 || !validDate(date)) {
        throw new Error('For each added date, enter a short name and the date shown in the signed contract or a written amendment.');
      }
      const duplicateKey = `${label.replace(/\s+/g, ' ').toLowerCase()}\u0000${date}`;
      if (rejectDuplicates && seen.has(duplicateKey)) {
        throw new Error('Enter each confirmed date once. If an amendment changed it, use a distinct name for the updated date.');
      }
      seen.add(duplicateKey);
      milestones.push({ label, date });
    }
    return milestones;
  }

  function buildCalendar({ offerId = '', property = '', effectiveDate = '', optionDeadline = '', closingDate = '', milestones = [] } = {}) {
    const events = [];
    const stamp = new Date().toISOString().replace(/[-:]/g, '').replace(/\.\d{3}/, '');
    const offerKey = encodeURIComponent(offerId);
    const address = String(property || '').trim();
    const withProperty = label => address ? `${label} — ${address}` : label;
    const addAllDayEvent = (date, summary, description, eventKey) => {
      if (!validDate(date)) return;
      // Keep the published IDs for dates agents may already have imported.
      const uid = offerKey && eventKey ? `${offerKey}-${eventKey}` : `${calendarKey(date)}-${events.length + 1}`;
      events.push([
        'BEGIN:VEVENT',
        `DTSTAMP:${stamp}`,
        `UID:homeofferflow-${uid}@homeofferflow.com`,
        `DTSTART;VALUE=DATE:${calendarKey(date)}`,
        `DTEND;VALUE=DATE:${calendarKey(nextDate(date))}`,
        `SUMMARY:${calendarEscape(summary)}`,
        `DESCRIPTION:${calendarEscape(description)}`,
        'END:VEVENT'
      ]);
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
    for (const [index, milestone] of normalizeMilestones(milestones).entries()) {
      addAllDayEvent(
        milestone.date,
        withProperty(milestone.label),
        'Date entered by the agent from the fully signed contract or a written amendment. HomeOfferFlow does not calculate this deadline.',
        `milestone-${index + 1}`
      );
    }

    if (!events.length) return '';
    return [
      'BEGIN:VCALENDAR',
      'VERSION:2.0',
      'PRODID:-//HomeOfferFlow//Under Contract Timeline//EN',
      'CALSCALE:GREGORIAN',
      ...events.flat(),
      'END:VCALENDAR',
      ''
    ].map(foldCalendarLine).join('\r\n');
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
    const data = offer?.offer_data || {};
    const raw = Object.hasOwn(data, 'optionDays') ? data.optionDays :
      (Object.hasOwn(data, 'option_days') ? data.option_days : offer?.option_days);
    const days = Number(raw);
    return Number.isInteger(days) && days > 0 && days <= 365 && String(raw).trim() === String(days) ? days : 0;
  }

  function downloadCalendar(offer, tracking) {
    const calendar = buildCalendar({
      offerId: offer.id,
      property: offerProperty(offer),
      effectiveDate: tracking?.effectiveDate,
      optionDeadline: tracking?.optionDeadline,
      closingDate: tracking?.closingDate,
      milestones: tracking?.milestones
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
    const eventWrite = root.logOfferEvent?.(offer.id, 'contract_timeline_calendar_downloaded', 'downloaded', 'Contract timeline calendar downloaded.', {
      surface: 'offer_workspace', has_option_date: Boolean(tracking.optionDeadline), has_closing_date: Boolean(tracking.closingDate)
    });
    eventWrite?.catch?.(() => {});
    return true;
  }

  function announce(message) {
    root.announceWorkspaceStatus?.(message);
  }

  function canDownloadCalendar(tracking) {
    return tracking?.acceptedContractConfirmed === true && Boolean(validDate(tracking.effectiveDate));
  }

  function downloadSavedCalendar(offerId) {
    const offer = findOffer(offerId);
    const tracking = offer?.offer_data?.transactionTracking;
    if (!root.hofAuth?.session?.user?.id || !canDownloadCalendar(tracking)) {
      announce('Open the contract timeline to save the confirmed dates before downloading a calendar.');
      return false;
    }
    return downloadCalendar(offer, tracking);
  }

  function renderSavedState(modal, offer, tracking, close) {
    const summary = modal.querySelector('#hofContractTimelineSummary');
    const form = modal.querySelector('form');
    if (form) form.hidden = true;
    if (!summary) return;
    const dates = [
      tracking.effectiveDate ? `<li><strong>Effective date:</strong> ${escapeHtml(formatDate(tracking.effectiveDate))}</li>` : '',
      tracking.optionDeadline ? `<li><strong>Option-period date:</strong> ${escapeHtml(formatDate(tracking.optionDeadline))} <span style="color:var(--gray-light)">(review the 5:00 p.m. property-local deadline in the contract)</span></li>` : '',
      tracking.closingDate ? `<li><strong>Target closing:</strong> ${escapeHtml(formatDate(tracking.closingDate))}</li>` : '',
      ...normalizeMilestones(tracking.milestones).map(item => `<li><strong>${escapeHtml(item.label)}:</strong> ${escapeHtml(formatDate(item.date))}</li>`)
    ].filter(Boolean).join('');
    summary.hidden = false;
    summary.innerHTML = `<div class="notice sage"><strong>Contract timeline saved.</strong><br>These dates remain attached to ${escapeHtml(offerProperty(offer))} in your private workspace.</div><ul style="margin:.9rem 0 1rem;padding-left:1.25rem;color:var(--gray-light);line-height:1.7">${dates}</ul><div class="hof-agreement-footer"><button type="button" class="btn-secondary" id="hofContractCalendarDownload">Download calendar</button><button type="button" class="btn-primary" id="hofContractTimelineDone">Done</button></div>`;
    summary.querySelector('#hofContractCalendarDownload')?.addEventListener('click', () => downloadCalendar(offer, tracking));
    summary.querySelector('#hofContractTimelineDone')?.addEventListener('click', close);
    summary.querySelector('#hofContractCalendarDownload')?.focus();
  }

  function dismiss() {
    document.getElementById('hofUnderContractCompanion')?.remove();
  }

  function open(offerId) {
    const offer = findOffer(offerId);
    const user = root.hofAuth?.session?.user;
    const epoch = root.__hofAccountProfileEpoch || 0;
    const opener = document.activeElement;
    if (!offer || !user?.id) {
      announce('Sign in and refresh My Offers before opening the contract timeline.');
      return;
    }
    const isCurrent = () => root.hofAuth?.session?.user?.id === user.id &&
      (root.__hofAccountProfileEpoch || 0) === epoch;

    dismiss();
    const data = offer.offer_data || {};
    const saved = data.transactionTracking || {};
    const optionDays = offerOptionDays(offer);
    const effectiveDate = saved.effectiveDate || '';
    const derivedOptionDate = optionDays ? addCalendarDays(effectiveDate, optionDays) : '';
    const closingDate = saved.closingDate ?? (data.closingDate || data.closing_date || '');
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
          <fieldset class="hof-agreement-wide" style="border:1px solid var(--border,#d7dee7);border-radius:10px;padding:.8rem 1rem"><legend><strong>Other dates confirmed in the signed contract</strong></legend><p style="margin:.25rem 0 .75rem">Optional. Add up to 12 dates exactly as stated in the fully signed contract or a written amendment. HomeOfferFlow will not calculate these dates.</p><div id="hofContractMilestoneRows"></div><button type="button" class="btn-secondary" id="hofAddContractMilestone">Add a confirmed date</button></fieldset>
          <label class="hof-agreement-wide hof-agreement-services"><input name="contractConfirmed" type="checkbox" required> I confirm this offer was accepted and the dates entered are from the fully signed contract.</label>
        </div>
        <div id="hofContractTimelineStatus" class="hof-iabs-status" role="status" aria-live="polite"></div>
        ${canDownloadCalendar(saved) ? '<div><button type="button" class="btn-secondary" id="hofDownloadSavedContractCalendar">Download saved calendar</button><p>Uses the last saved dates. Save any changes before downloading an updated calendar.</p></div>' : ''}
        <div class="hof-agreement-footer"><button class="btn-secondary" type="button" id="hofContractTimelineCancel">Cancel</button><button class="btn-primary" type="submit">Save contract timeline</button></div>
      </form>
      <div id="hofContractTimelineSummary" hidden></div>
    </div>`;
    document.body.appendChild(modal);
    const close = () => {
      modal.remove();
      if (!isCurrent()) return;
      const replacement = [...document.querySelectorAll('[data-contract-timeline-offer]')]
        .find(button => button.dataset.contractTimelineOffer === String(offer.id));
      (opener?.isConnected && opener !== document.body ? opener :
        replacement || document.getElementById('offerWorkspaceSearch'))?.focus();
    };
    modal.addEventListener('keydown', event => {
      if (event.key === 'Escape') {
        event.preventDefault();
        event.stopPropagation();
        close();
        return;
      }
      if (event.key !== 'Tab') return;
      const controls = [...modal.querySelectorAll('input, button')]
        .filter(control => !control.disabled && !control.closest('[hidden]'));
      const first = controls[0], last = controls.at(-1);
      if ((event.shiftKey && document.activeElement === first) ||
          (!event.shiftKey && document.activeElement === last)) {
        event.preventDefault();
        (event.shiftKey ? last : first)?.focus();
      }
    });
    const form = modal.querySelector('form');
    const effectiveInput = form.elements.effectiveDate;
    const optionInput = form.elements.optionDeadline;
    const milestoneRows = modal.querySelector('#hofContractMilestoneRows');
    const addMilestoneButton = modal.querySelector('#hofAddContractMilestone');
    const addMilestone = (milestone = {}) => {
      if (!milestoneRows || milestoneRows.children.length >= 12) return;
      const row = document.createElement('div');
      row.className = 'hof-contract-milestone';
      row.style.cssText = 'display:flex;flex-wrap:wrap;gap:.5rem;align-items:end;margin:.55rem 0';
      row.innerHTML = `<label style="flex:1 1 10rem;min-width:8rem">Deadline name<input name="milestoneLabel" type="text" maxlength="80" autocomplete="off" value="${escapeHtml(milestone.label || '')}" placeholder="For example, survey delivery"></label><label style="flex:1 1 9rem;min-width:8rem">Confirmed date<input name="milestoneDate" type="date" value="${escapeHtml(milestone.date || '')}"></label><button type="button" class="btn-secondary" aria-label="Remove this confirmed date">Remove</button>`;
      row.querySelector('button')?.addEventListener('click', () => {
        row.remove();
        if (addMilestoneButton) addMilestoneButton.disabled = false;
      });
      milestoneRows.appendChild(row);
      if (addMilestoneButton) addMilestoneButton.disabled = milestoneRows.children.length >= 12;
      return row;
    };
    normalizeMilestones(saved.milestones).forEach(addMilestone);
    addMilestoneButton?.addEventListener('click', () => {
      const row = addMilestone();
      row?.querySelector('input[name="milestoneLabel"]')?.focus();
    });
    const refreshOptionDate = () => { optionInput.value = optionDays ? addCalendarDays(effectiveInput.value, optionDays) : ''; };
    effectiveInput.addEventListener('change', refreshOptionDate);
    modal.querySelector('#hofContractTimelineCancel')?.addEventListener('click', close);
    modal.querySelector('#hofDownloadSavedContractCalendar')?.addEventListener('click', () => {
      if (isCurrent()) downloadCalendar(offer, saved);
    });
    modal.addEventListener('click', event => { if (event.target === modal) close(); });
    form.addEventListener('submit', async event => {
      event.preventDefault();
      const submit = form.querySelector('button[type="submit"]');
      const status = modal.querySelector('#hofContractTimelineStatus');
      if (!submit || submit.disabled) return;
      refreshOptionDate();
      let milestones;
      try {
        milestones = normalizeMilestones(Array.from(milestoneRows?.querySelectorAll('.hof-contract-milestone') || []).map(row => ({
          label: row.querySelector('input[name="milestoneLabel"]')?.value,
          date: row.querySelector('input[name="milestoneDate"]')?.value
        })), { rejectDuplicates: true });
      } catch (error) {
        status.className = 'hof-iabs-status error';
        status.textContent = error.message;
        return;
      }
      submit.disabled = true;
      submit.setAttribute('aria-busy', 'true');
      submit.textContent = 'Saving timeline…';
      status.className = 'hof-iabs-status';
      status.textContent = 'Saving confirmed contract dates…';
      try {
        if (!isCurrent()) {
          throw new Error('Your signed-in account changed. Reopen the timeline from My Offers.');
        }
        const response = await fetch('/api/admin-dashboard', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            Authorization: `Bearer ${root.hofAuth?.session?.access_token || ''}`
          },
          body: JSON.stringify({
            action: 'save_agent_contract_timeline', offerId: offer.id,
            effectiveDate: effectiveInput.value,
            closingDate: form.elements.closingDate.value,
            milestones,
            expectedUpdatedAt: saved.updatedAt || null
          })
        });
        const result = await response.json().catch(() => ({}));
        if (!isCurrent()) { modal.remove(); return; }
        if (!response.ok) throw new Error(result.error || 'We couldn’t save the contract timeline. Please try again.');
        const tracking = result.tracking;
        if (!tracking || result.offerId !== offer.id) throw new Error('Refresh My Offers to confirm the saved dates before trying again.');
        const currentOffer = findOffer(offer.id);
        if (currentOffer && !(Date.parse(currentOffer.offer_data?.transactionTracking?.updatedAt) > Date.parse(tracking.updatedAt))) {
          currentOffer.offer_data = { ...(currentOffer.offer_data || {}), transactionTracking: tracking };
          const list = document.getElementById('myOffersList');
          if (list && typeof root.renderMyOffers === 'function') {
            try { list.innerHTML = root.renderMyOffers(offerList()); }
            catch (error) { console.warn('My Offers could not refresh after the timeline save:', error); }
          }
        }
        if (modal.isConnected) renderSavedState(modal, currentOffer || offer, tracking, close);
        try {
          await root.logOfferEvent?.(offer.id, 'contract_timeline_saved', 'saved', 'Confirmed contract timeline saved.', {
            surface: 'offer_workspace', has_option_date: Boolean(tracking.optionDeadline), has_closing_date: Boolean(tracking.closingDate)
          });
        } catch (_) {}
      } catch (error) {
        if (!isCurrent()) { modal.remove(); return; }
        console.error('Contract timeline save failed:', error);
        status.className = 'hof-iabs-status error';
        const fallback = 'Please refresh My Offers to confirm the saved dates before trying again.';
        status.textContent = root.hofCustomerActionError?.(error, fallback) || fallback;
        submit.disabled = false;
        submit.setAttribute('aria-busy', 'false');
        submit.textContent = 'Save contract timeline';
      }
    });
    effectiveInput.focus();
  }

  root.hofUnderContract = Object.freeze({
    open,
    dismiss,
    canDownloadCalendar,
    downloadSavedCalendar,
    addCalendarDays,
    buildCalendar,
    formatDate,
    normalizeMilestones
  });
})(window);
