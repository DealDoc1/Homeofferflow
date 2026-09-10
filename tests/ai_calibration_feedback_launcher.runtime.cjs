const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const {test} = require('node:test');

const html = fs.readFileSync(path.join(__dirname, '..', 'index.html'), 'utf8');
const privacyStart = html.indexOf('  function syncAiFeedbackPrivacyGuard()');
const privacyEnd = html.indexOf('\n  function syncFeedbackFields()', privacyStart);
const fieldsEnd = html.indexOf('\n  function closeBetaFeedback()', privacyEnd);
const launcherStart = html.indexOf('  function openAiCalibrationFeedback()');
const launcherEnd = html.indexOf('\n  async function saveAiReviewResultToSupabase', launcherStart);
assert.ok(privacyStart >= 0 && privacyEnd > privacyStart && fieldsEnd > privacyEnd && launcherEnd > launcherStart,
  'AI calibration reviewer helpers must be present');
const source = html.slice(privacyStart, fieldsEnd) + html.slice(launcherStart, launcherEnd);

test('AI calibration launcher refreshes visible reviewer fields before asking for notes', () => {
  const elements = new Map();
  const el = (id, options = {}) => ({id, style: {}, value: '', checked: false, textContent: '', focus() {}, ...options});
  const issue = el('feedbackIssueType', {value: 'bug'});
  const guard = el('aiFeedbackPrivacyGuard');
  const checkbox = el('aiFeedbackAnonymized');
  const scenarioField = el('aiFeedbackScenarioField');
  const scenario = el('aiFeedbackScenario');
  const structured = el('aiFeedbackStructuredFields');
  const missingForm = el('missingFormStructuredFields');
  const label = el('feedbackMessageLabel');
  const message = el('feedbackMessage');
  const title = el('feedbackTitle');
  const intro = el('feedbackIntro');
  [issue, guard, checkbox, scenarioField, scenario, structured, missingForm, label, message, title].forEach(item => elements.set(item.id, item));
  const document = {
    getElementById: id => elements.get(id) || null,
    querySelector: selector => selector === '#feedbackModal .feedback-head p' ? intro : null,
  };
  let opened = 0;
  const context = vm.createContext({
    document,
    openBetaFeedback: () => { opened += 1; },
    setTimeout: callback => callback(),
    state: {data: {_lastAiReview: {score: 8, marketMode: 'balanced'}}},
    normalizeAiReviewResult: value => value || {score: 0, marketMode: 'unknown'},
  });
  vm.runInContext(source, context);
  context.openAiCalibrationFeedback();

  assert.equal(opened, 1);
  assert.equal(issue.value, 'ai_review');
  assert.equal(guard.style.display, 'block');
  assert.equal(scenarioField.style.display, 'block');
  assert.equal(structured.style.display, 'block');
  assert.equal(label.textContent, 'Reviewer summary');
  assert.match(message.placeholder, /independent review/i);
  assert.match(message.value, /Score shown: 8/);
  assert.equal(title.textContent, 'Review AI Offer Assessment');
  assert.match(intro.textContent, /anonymized transaction facts/i);
});
