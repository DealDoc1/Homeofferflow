(function initBuildReadinessChecklist(root) {
  'use strict';

  const storageKey = 'hof:build-readiness-checklist:v1';
  const allowed = new Set(['discovery', 'readiness', 'financing', 'land', 'builder', 'transition', 'movein']);
  const boxes = Array.from(root.document?.querySelectorAll('[data-build-readiness-task]') || []);
  if (!boxes.length) return;

  const progress = root.document.getElementById('buildReadinessProgress');
  const message = root.document.getElementById('buildReadinessChecklistStatus');
  const clearButton = root.document.getElementById('buildReadinessClear');
  const printButton = root.document.getElementById('buildReadinessPrint');
  let state = {};

  try {
    const saved = JSON.parse(root.localStorage.getItem(storageKey) || '{}');
    if (saved && typeof saved === 'object' && !Array.isArray(saved)) {
      state = Object.fromEntries(Object.entries(saved).filter(([key, value]) => allowed.has(key) && value === true));
    }
  } catch (_) {
    state = {};
  }

  const count = () => boxes.filter(box => box.checked).length;
  function updateProgress() {
    if (progress) progress.textContent = `${count()} of ${boxes.length} steps marked`;
  }

  boxes.forEach(box => {
    const key = box.dataset.buildReadinessTask;
    if (!allowed.has(key)) {
      box.disabled = true;
      return;
    }
    box.checked = state[key] === true;
    box.addEventListener('change', () => {
      if (box.checked) state[key] = true;
      else delete state[key];
      try {
        root.localStorage.setItem(storageKey, JSON.stringify(state));
        if (message) message.textContent = '';
      } catch (_) {
        if (message) message.textContent = 'Progress is shown for this visit but could not be saved on this device.';
      }
      updateProgress();
    });
  });

  clearButton?.addEventListener('click', () => {
    boxes.forEach(box => { box.checked = false; });
    state = {};
    try {
      root.localStorage.removeItem(storageKey);
      if (message) message.textContent = 'Saved checkmarks cleared.';
    } catch (_) {
      if (message) message.textContent = 'Checkmarks cleared for this visit; saved browser data could not be removed.';
    }
    updateProgress();
  });

  printButton?.addEventListener('click', () => root.print?.());
  updateProgress();
})(typeof window !== 'undefined' ? window : globalThis);
