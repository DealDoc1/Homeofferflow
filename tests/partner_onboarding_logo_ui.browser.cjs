const { chromium } = require('playwright');

(async () => {
  const origin = process.env.TEST_ORIGIN || 'http://127.0.0.1:8765';
  const browser = await chromium.launch({ headless: true, channel: 'chrome' });
  const page = await browser.newPage({ viewport: { width: 390, height: 844 } });
  const pageErrors = [];
  page.on('pageerror', error => pageErrors.push(String(error)));

  await page.goto(origin, { waitUntil: 'domcontentloaded' });
  await page.evaluate(() => window.openPartnerOnboarding());

  const result = await page.evaluate(() => ({
    fileLabel: document.querySelector('label[for="partnerSetupLogoFile"]')?.textContent?.trim(),
    fileHelp: document.getElementById('partnerSetupLogoFile')?.parentElement?.querySelector('small')?.textContent?.trim(),
    hiddenLogoType: document.getElementById('partnerSetupLogo')?.type,
    pastedUrlChoiceVisible: document.body.innerText.includes('paste a secure logo URL'),
    buttonLabel: document.querySelector('label[for="partnerSetupCta"]')?.textContent?.trim(),
  }));

  if (result.fileLabel !== 'Logo image (optional)') throw new Error(`Unexpected logo label: ${result.fileLabel}`);
  if (!result.fileHelp?.includes('Leave this blank to keep your current logo.')) throw new Error('Existing-logo guidance is missing.');
  if (result.hiddenLogoType !== 'hidden') throw new Error('Existing logo state is not preserved privately.');
  if (result.pastedUrlChoiceVisible) throw new Error('The technical logo URL choice is still visible.');
  if (result.buttonLabel !== 'Directory button text (optional)') throw new Error(`Unexpected directory label: ${result.buttonLabel}`);
  if (pageErrors.length) throw new Error(`Page errors: ${pageErrors.join(' | ')}`);

  process.stdout.write(JSON.stringify({ ...result, pageErrors }, null, 2) + '\n');
  await browser.close();
})().catch(error => {
  console.error(error);
  process.exit(1);
});
