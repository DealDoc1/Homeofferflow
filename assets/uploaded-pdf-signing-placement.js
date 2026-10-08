(() => {
  'use strict';

  const PDFJS_VERSION = '3.11.174';
  const PDFJS_SCRIPT = `https://cdnjs.cloudflare.com/ajax/libs/pdf.js/${PDFJS_VERSION}/pdf.min.js`;
  const PDFJS_WORKER = `https://cdnjs.cloudflare.com/ajax/libs/pdf.js/${PDFJS_VERSION}/pdf.worker.min.js`;
  const FIELD_TYPES = [
    ['buyer1_signature', 'Buyer 1 signature', 145, 20],
    ['buyer1_date', 'Buyer 1 signing date', 66, 16],
    ['buyer1_initials', 'Buyer 1 initials', 24, 10],
    ['buyer2_signature', 'Buyer 2 signature', 145, 20],
    ['buyer2_date', 'Buyer 2 signing date', 66, 16],
    ['buyer2_initials', 'Buyer 2 initials', 24, 10]
  ];

  let pdfJsPromise;
  let activeDialog;

  const escapeHtml = value => String(value ?? '').replace(/[&<>"']/g, char => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
  })[char]);

  function hasBuyerTwo() {
    const input = document.getElementById('buyer2Email') || document.querySelector('[name="buyer2Email"]');
    return Boolean(String(input?.value || '').trim());
  }

  function fieldSpecs() {
    return FIELD_TYPES.filter(([type]) => !type.startsWith('buyer2_') || hasBuyerTwo());
  }

  function loadPdfJs() {
    if (window.pdfjsLib) return Promise.resolve(window.pdfjsLib);
    if (pdfJsPromise) return pdfJsPromise;
    pdfJsPromise = new Promise((resolve, reject) => {
      const script = document.createElement('script');
      script.src = PDFJS_SCRIPT;
      script.async = true;
      script.onload = () => window.pdfjsLib ? resolve(window.pdfjsLib) : reject(new Error('PDF preview did not initialize.'));
      script.onerror = () => reject(new Error('Could not load the secure PDF preview. Check your connection and try again.'));
      document.head.appendChild(script);
    });
    return pdfJsPromise;
  }

  function ensureStyles() {
    if (document.getElementById('hof-uploaded-signing-styles')) return;
    const style = document.createElement('style');
    style.id = 'hof-uploaded-signing-styles';
    style.textContent = `
      .hof-upload-sign-fields { margin-left:.3rem; }
      .hof-upload-sign-count { color:#365a48; font-size:.76rem; }
      .hof-signing-modal { position:fixed; inset:0; z-index:10020; display:flex; align-items:center; justify-content:center; padding:1rem; background:rgba(8,18,24,.78); }
      .hof-signing-panel { width:min(960px,100%); max-height:min(92vh,980px); overflow:auto; border:1px solid #d6e0da; border-radius:16px; background:#fff; color:#17241e; box-shadow:0 24px 80px rgba(0,0,0,.3); padding:1rem; }
      .hof-signing-head,.hof-signing-toolbar,.hof-signing-foot { display:flex; align-items:center; gap:.65rem; flex-wrap:wrap; }
      .hof-signing-head { justify-content:space-between; margin-bottom:.4rem; }
      .hof-signing-head h2 { margin:0; font-size:1.1rem; }
      .hof-signing-copy { margin:.3rem 0 .8rem; color:#52625a; font-size:.88rem; line-height:1.45; }
      .hof-signing-toolbar { margin:.75rem 0; }
      .hof-signing-tool { border:1px solid #cad8d0; border-radius:999px; background:#f6f9f7; padding:.46rem .7rem; color:#183d31; cursor:pointer; }
      .hof-signing-tool[aria-pressed="true"] { background:#173f35; color:white; border-color:#173f35; }
      .hof-signing-pagebar { display:flex; align-items:center; gap:.55rem; margin:.5rem 0; }
      .hof-signing-pagebar button,.hof-signing-close,.hof-signing-done { border:1px solid #cbd8d1; border-radius:8px; background:#fff; color:#173f35; cursor:pointer; padding:.48rem .7rem; }
      .hof-signing-preview { position:relative; width:min(100%,800px); margin:.6rem auto; border:1px solid #d8dfdb; background:#f2f4f3; min-height:260px; display:flex; align-items:flex-start; justify-content:center; overflow:auto; }
      .hof-signing-canvas-wrap { position:relative; width:100%; max-width:800px; line-height:0; }
      .hof-signing-canvas { display:block; width:100%; height:auto; background:white; }
      .hof-signing-pin { position:absolute; z-index:1; display:flex; align-items:center; justify-content:center; border:2px solid #1c6a50; border-radius:3px; background:rgba(220,247,233,.82); color:#124530; font:600 10px/1.1 Arial,sans-serif; text-align:center; overflow:hidden; cursor:pointer; }
      .hof-signing-pin:hover { border-color:#b24335; background:rgba(255,234,229,.9); color:#782b23; }
      .hof-signing-status { min-height:1.3rem; color:#5c4530; font-size:.82rem; }
      .hof-signing-foot { justify-content:space-between; border-top:1px solid #e3e9e5; padding-top:.8rem; margin-top:.6rem; }
      .hof-signing-done { background:#173f35; border-color:#173f35; color:white; font-weight:700; }
      @media(max-width:600px){ .hof-signing-modal{padding:.35rem}.hof-signing-panel{max-height:96vh;padding:.75rem}.hof-signing-tool{font-size:.75rem;padding:.4rem .55rem} }
    `;
    document.head.appendChild(style);
  }

  function fieldCount(doc) {
    return Array.isArray(doc.signaturePlacements) ? doc.signaturePlacements.length : 0;
  }

  function enhanceRows() {
    const docs = window.hofUploadedDisclosureDocs || [];
    document.querySelectorAll('#uploadedDocsList .uploaded-doc-row').forEach(row => {
      const index = Number(row.dataset.uploadedIndex);
      const doc = docs[index];
      if (!doc) return;
      let button = row.querySelector('.hof-upload-sign-fields');
      if (!button) {
        button = document.createElement('button');
        button.type = 'button';
        button.className = 'btn-secondary hof-upload-sign-fields';
        button.addEventListener('click', () => openPlacementDialog(Number(row.dataset.uploadedIndex)));
        row.appendChild(button);
      }
      button.textContent = fieldCount(doc) ? 'Edit signing fields' : 'Place signing fields';
      button.setAttribute('aria-label', `${button.textContent} for ${doc.name}`);
      let count = row.querySelector('.hof-upload-sign-count');
      if (fieldCount(doc)) {
        if (!count) {
          count = document.createElement('small');
          count.className = 'hof-upload-sign-count';
          row.appendChild(count);
        }
        count.textContent = `${fieldCount(doc)} buyer field${fieldCount(doc) === 1 ? '' : 's'}`;
      } else count?.remove();
    });
  }

  function wrapRenderer() {
    if (typeof window.renderUploadedDocsList !== 'function' || window.renderUploadedDocsList.__hofPlacementWrapped) return;
    const original = window.renderUploadedDocsList;
    const wrapped = function (...args) {
      const result = original.apply(this, args);
      enhanceRows();
      return result;
    };
    wrapped.__hofPlacementWrapped = true;
    window.renderUploadedDocsList = wrapped;
    enhanceRows();
  }

  function closeDialog() {
    activeDialog?.remove();
    activeDialog = null;
  }

  function openPlacementDialog(docIndex) {
    const doc = (window.hofUploadedDisclosureDocs || [])[docIndex];
    if (!doc || !doc.base64) return;
    closeDialog();
    ensureStyles();
    const specs = fieldSpecs();
    const modal = document.createElement('div');
    modal.className = 'hof-signing-modal';
    modal.setAttribute('role', 'dialog');
    modal.setAttribute('aria-modal', 'true');
    modal.setAttribute('aria-labelledby', 'hofSigningTitle');
    modal.innerHTML = `<section class="hof-signing-panel"><div class="hof-signing-head"><h2 id="hofSigningTitle">Place signing fields</h2><button type="button" class="hof-signing-close" aria-label="Close">Close</button></div><p class="hof-signing-copy">${escapeHtml(doc.name)} · Choose a field, then click its printed signing line on the page. Fields are for buyer signers only. Review every placement before sending. Click a placed field to remove it; then place it again where needed.</p><div class="hof-signing-toolbar" role="group" aria-label="Field to place">${specs.map(([type,label]) => `<button type="button" class="hof-signing-tool" data-field="${type}" aria-pressed="false">${label}</button>`).join('')}</div><div class="hof-signing-pagebar"><button type="button" data-page-step="-1">Previous page</button><span class="hof-signing-page-label">Loading preview…</span><button type="button" data-page-step="1">Next page</button></div><div class="hof-signing-preview"><div class="hof-signing-canvas-wrap"><canvas class="hof-signing-canvas"></canvas></div></div><div class="hof-signing-status" role="status" aria-live="polite"></div><div class="hof-signing-foot"><span class="hof-signing-copy" style="margin:0">No signing fields are added unless you place them here.</span><button type="button" class="hof-signing-done">Save placements</button></div></section>`;
    document.body.appendChild(modal);
    activeDialog = modal;
    const canvas = modal.querySelector('canvas');
    const wrap = modal.querySelector('.hof-signing-canvas-wrap');
    const label = modal.querySelector('.hof-signing-page-label');
    const status = modal.querySelector('.hof-signing-status');
    const preview = modal.querySelector('.hof-signing-preview');
    let activeField = specs[0]?.[0] || 'buyer1_signature';
    let pdf = null;
    let currentPage = 1;

    function setStatus(message) { status.textContent = message || ''; }
    function paintPins() {
      wrap.querySelectorAll('.hof-signing-pin').forEach(pin => pin.remove());
      const renderedWidth = canvas.clientWidth || canvas.width;
      const renderedHeight = canvas.clientHeight || canvas.height;
      (doc.signaturePlacements || []).filter(pin => Number(pin.page) === currentPage).forEach((placement,index) => {
        const spec = specs.find(([type]) => type === placement.type) || FIELD_TYPES.find(([type]) => type === placement.type);
        if (!spec) return;
        const pin = document.createElement('button');
        pin.type = 'button';
        pin.className = 'hof-signing-pin';
        pin.title = `Remove ${spec[1]}`;
        pin.textContent = spec[1];
        pin.style.left = `${Math.max(0,Math.min(1,Number(placement.xRatio)||0))*renderedWidth}px`;
        pin.style.top = `${Math.max(0,Math.min(1,Number(placement.yRatio)||0))*renderedHeight}px`;
        pin.style.width = `${Math.max(24,spec[2]/816*renderedWidth)}px`;
        pin.style.height = `${Math.max(10,spec[3]/1056*renderedHeight)}px`;
        pin.addEventListener('click', event => {
          event.stopPropagation();
          doc.signaturePlacements.splice((doc.signaturePlacements || []).indexOf(placement),1);
          paintPins();
          setStatus('Field removed. Choose a field and click to place it again.');
        });
        wrap.appendChild(pin);
      });
    }

    async function renderPage(pageNumber) {
      if (!pdf) return;
      currentPage = Math.max(1,Math.min(pdf.numPages,pageNumber));
      label.textContent = `Page ${currentPage} of ${pdf.numPages}`;
      preview.style.minHeight = '260px';
      const page = await pdf.getPage(currentPage);
      const base = page.getViewport({scale:1});
      const scale = Math.min(1.5,Math.max(.5,(wrap.parentElement.clientWidth-24)/base.width));
      const viewport = page.getViewport({scale});
      canvas.width = Math.ceil(viewport.width);
      canvas.height = Math.ceil(viewport.height);
      canvas.style.width = '100%';
      canvas.style.height = 'auto';
      await page.render({canvasContext:canvas.getContext('2d'),viewport}).promise;
      paintPins();
    }

    modal.querySelectorAll('.hof-signing-tool').forEach(button => button.addEventListener('click', () => {
      activeField = button.dataset.field;
      modal.querySelectorAll('.hof-signing-tool').forEach(item => item.setAttribute('aria-pressed',String(item === button)));
      setStatus(`Selected: ${specs.find(([type]) => type === activeField)?.[1] || activeField}. Click the matching line on the page.`);
    }));
    modal.querySelector('.hof-signing-tool')?.setAttribute('aria-pressed','true');
    modal.querySelectorAll('[data-page-step]').forEach(button => button.addEventListener('click', () => renderPage(currentPage + Number(button.dataset.pageStep)).catch(() => setStatus('Could not render that page.'))));
    modal.querySelector('.hof-signing-close').addEventListener('click',closeDialog);
    modal.addEventListener('click', event => { if (event.target === modal) closeDialog(); });
    modal.addEventListener('keydown', event => { if (event.key === 'Escape') closeDialog(); });
    modal.querySelector('.hof-signing-done').addEventListener('click', () => {
      doc.signaturePlacements = Array.isArray(doc.signaturePlacements) ? doc.signaturePlacements : [];
      resetAck();
      closeDialog();
      enhanceRows();
      try { window.renderReview?.(); } catch (_) {}
    });
    wrap.addEventListener('click', event => {
      if (event.target.closest('.hof-signing-pin')) return;
      const rect = canvas.getBoundingClientRect();
      if (!rect.width || !rect.height) return;
      doc.signaturePlacements = Array.isArray(doc.signaturePlacements) ? doc.signaturePlacements : [];
      doc.signaturePlacements.push({type:activeField,page:currentPage,xRatio:Math.max(0,Math.min(1,(event.clientX-rect.left)/rect.width)),yRatio:Math.max(0,Math.min(1,(event.clientY-rect.top)/rect.height))});
      paintPins();
      setStatus(`${specs.find(([type]) => type === activeField)?.[1] || activeField} placed. Continue, or click the field to remove it.`);
    });

    loadPdfJs().then(async library => {
      library.GlobalWorkerOptions.workerSrc = PDFJS_WORKER;
      const bytes = Uint8Array.from(atob(doc.base64),char => char.charCodeAt(0));
      pdf = await library.getDocument({data:bytes}).promise;
      await renderPage(1);
      setStatus('Preview ready. Place fields only where the uploaded document calls for buyer signatures, dates, or initials.');
    }).catch(error => {
      label.textContent = 'Preview unavailable';
      setStatus(error?.message || 'Could not open this PDF preview.');
    });
  }

  function resetAck() {
    const ack = document.getElementById('uploadedDisclosureAck');
    if (ack) {
      ack.checked = false;
      const copy = ack.parentElement?.querySelector('span');
      if (copy) copy.textContent = 'I reviewed each uploaded PDF, its label and packet order, and any buyer signing fields I placed. I have authority to include these documents; if no buyer signing is needed, I leave fields unplaced.';
    }
  }

  function attachPlacements(payload) {
    const docs = window.hofUploadedDisclosureDocs || [];
    if (!Array.isArray(payload?.uploadedDisclosureDocs)) return;
    payload.uploadedDisclosureDocs = payload.uploadedDisclosureDocs.map(upload => {
      const source = docs.find(doc => doc && upload && String(doc.name) === String(upload.name));
      if (!source || !Array.isArray(source.signaturePlacements) || !source.signaturePlacements.length) return upload;
      return {...upload,signaturePlacements:source.signaturePlacements.map(({type,page,xRatio,yRatio}) => ({type,page,xRatio,yRatio}))};
    });
  }

  function wrapFetch() {
    if (window.fetch.__hofUploadedPlacementWrapped) return;
    const original = window.fetch.bind(window);
    const wrapped = async (input,init={}) => {
      const url = typeof input === 'string' ? input : input?.url || '';
      if (/\/api\/(?:create-checkout|fill-pdf)(?:[/?#]|$)/.test(url) && typeof init.body === 'string') {
        try {
          const body = JSON.parse(init.body);
          if (body.offerData && typeof body.offerData === 'object') attachPlacements(body.offerData);
          const encodedOffer = body?.data?.object?.metadata?.offer_data;
          if (typeof encodedOffer === 'string') {
            const offerData = JSON.parse(encodedOffer);
            attachPlacements(offerData);
            body.data.object.metadata.offer_data = JSON.stringify(offerData);
          }
          init = {...init,body:JSON.stringify(body)};
        } catch (_) {}
      }
      return original(input,init);
    };
    wrapped.__hofUploadedPlacementWrapped = true;
    window.fetch = wrapped;
  }

  function start() {
    wrapRenderer();
    wrapFetch();
    document.addEventListener('change', event => {
      if (event.target?.id === 'buyer2Email' || event.target?.name === 'buyer2Email') enhanceRows();
    });
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded',start,{once:true});
  else start();
})();
