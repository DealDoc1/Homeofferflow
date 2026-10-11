// Isolated interview fixtures must execute the real shared default helpers.
const vm = require('node:vm');
module.exports = function loadBrokerageDefaults(context, html) {
  const start = html.indexOf('  function brokerageLicenseDefault(');
  const end = html.indexOf('  function applyProfileDefaultsToWizard(', start);
  if (start < 0 || end <= start) throw new Error('Brokerage default source not found');
  vm.runInContext(html.slice(start, end), context);
};
