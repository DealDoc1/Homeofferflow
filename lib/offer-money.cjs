function invalidMoneyEntry() {
  return { valid: false, empty: false, digits: '', value: undefined };
}

function canonicalDecimal(value) {
  const [whole, fraction = ''] = String(value).split('.');
  const normalizedWhole = whole.replace(/^0+(?=\d)/, '');
  const normalizedFraction = fraction.replace(/0+$/, '');
  return normalizedFraction ? `${normalizedWhole}.${normalizedFraction}` : normalizedWhole;
}

function parseOfferMoneyEntry(value, { allowIncomplete = false } = {}) {
  const entry = String(value ?? '').trim();
  if (!entry) return { valid: true, empty: true, digits: '', value: null };
  const amount = entry.replace(/^\$\s*/, '');
  const decimal = allowIncomplete ? '(?:\\.\\d{0,2})?' : '(?:\\.\\d{1,2})?';
  if (!new RegExp(`^(?:\\d+|\\d{1,3}(?:,\\d{3})+)${decimal}$`).test(amount)) {
    return invalidMoneyEntry();
  }
  const digits = amount.replace(/,/g, '');
  if (allowIncomplete) return { valid: true, empty: false, digits, value: null };

  const numeric = Number(digits);
  if (!Number.isFinite(numeric) || numeric < 0 ||
      numeric !== Number(numeric.toFixed(2)) ||
      !Number.isSafeInteger(Math.round(numeric * 100)) ||
      canonicalDecimal(digits) !== canonicalDecimal(String(numeric))) {
    return invalidMoneyEntry();
  }
  return { valid: true, empty: false, digits, value: numeric };
}

function normalizeOfferMoney(value, { allowEmpty = true, positive = false } = {}) {
  const parsed = parseOfferMoneyEntry(value);
  if (!parsed.valid || (parsed.empty && !allowEmpty)) return { valid: false, value: undefined };
  if (parsed.empty) return { valid: true, value: null };
  if (positive && parsed.value <= 0) return { valid: false, value: undefined };
  return { valid: true, value: parsed.value };
}

exports.parseOfferMoneyEntry = parseOfferMoneyEntry;
exports.normalizeOfferMoney = normalizeOfferMoney;
