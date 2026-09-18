// Offline real-DOM check: extracted production dialog, mocked auth/source/save.
const fs = require('node:fs');
const path = require('node:path');
const assert = require('node:assert/strict');
const {chromium} = require('playwright');
const root = path.join(__dirname, '..');
const source = fs.readFileSync(path.join(root, 'index.html'), 'utf8');
function block(tag, id) {
  const match = source.match(new RegExp(`<${tag} id="${id}">([\\s\\S]*?)<\\/${tag}>`));
  assert.ok(match, `Missing ${id}`);
  return match[1];
}
const script = block('script', 'hof-txr1507-drafts-v1');
const style = block('style', 'hof-txr1507-drafts-v1');
(async () => {
  const browser = await chromium.launch({headless: true, channel: 'chrome'});
  try {
    const page = await browser.newPage({viewport: {width: 390, height: 844}});
    await page.route('**/*', route => route.abort());
    const errors = [];
    page.on('pageerror', error => errors.push(error.message));
    await page.setContent(`<!doctype html><html><head><style>
      :root{--gray-light:#c8d1db;--white:#fff;--navy:#0d1f35;--gold:#c8973f}
      *{box-sizing:border-box}body{font-family:Arial;margin:0;background:#0d1f35;color:white}
      input,select,textarea{background:#132c45;border:1px solid #8095a6;border-radius:6px}
      button{padding:12px;border-radius:6px} ${style}
      </style></head><body><div id="accountPanelRelationships"></div>
      <script>
      window.hofAuth={role:'agent',session:{user:{id:'qa'},access_token:'offline-test'}};
      window.hofLoadApprovedBrokerageSource=async()=>({id:'00000000-0000-0000-0000-000000000001',source_revision:'06-15-26'});
      window.savedPayloads=[];window.fetch=async(_,options)=>{window.savedPayloads.push(JSON.parse(options.body));return {ok:true,json:async()=>({id:'offline-draft'})};};
      </script><script>${script}</script></body></html>`);
    await page.getByRole('button', {name:'Prepare straightforward representation agreement'}).click();
    const field = name => page.locator(`[name="${name}"]`);
    const showing = page.locator('[name="serviceLevel"][value="showing_services"]');
    const full = page.locator('[name="serviceLevel"][value="full_services"]');
    assert.equal(await field('purchasePercentage').isVisible(), false);
    assert.equal(await field('showingFee').isVisible(), false);
    await full.check();
    assert.equal(await field('purchasePercentage').isVisible(), true);
    await field('purchasePercentage').fill('3.125');
    await field('intermediary').selectOption('authorized');
    await showing.check();
    for (const name of ['purchasePercentage','purchaseFlatFee','leaseOneMonthPercentage','leaseTotalRentsPercentage','leaseFlatFee','intermediary']) {
      assert.equal(await field(name).isVisible(), false);
      assert.equal(await field(name).isDisabled(), true);
    }
    assert.equal(await field('showingFee').isVisible(), true);
    assert.equal(await field('showingFee').getAttribute('required'), '');
    await field('showingFee').fill('150.25');
    await full.check();
    assert.equal(await field('purchasePercentage').inputValue(), '3.125');
    assert.equal(await field('intermediary').inputValue(), 'authorized');
    assert.equal(await field('showingFee').isDisabled(), true);
    let values = await page.locator('form').evaluate(form => Object.fromEntries(new FormData(form)));
    assert.equal(values.showingFee, undefined);
    assert.equal(values.purchasePercentage, '3.125');
    await showing.check();
    assert.equal(await field('showingFee').inputValue(), '150.25');
    await field('clientOne').fill('QA Client');
    await field('marketArea').fill('Collin County, Texas');
    await field('termStart').fill('2026-09-18');
    await field('termEnd').fill('2026-09-19');
    await field('signerPlan').selectOption('clients_and_associate');
    assert.equal(await page.locator('form').evaluate(form => form.checkValidity()), true);
    const folder = process.argv[2];
    if (folder) {
      fs.mkdirSync(folder, {recursive:true});
      await page.screenshot({path:path.join(folder,'showing-mobile.png'),fullPage:true});
      await page.getByRole('button', {name:'Prepare agreement',exact:true}).scrollIntoViewIfNeeded();
      assert.equal(await page.locator('form').evaluate(form => form.scrollWidth <= form.clientWidth), true);
      const submitBox = await page.getByRole('button', {name:'Prepare agreement',exact:true}).boundingBox();
      assert.ok(submitBox.y >= 0 && submitBox.y + submitBox.height <= 844);
      await page.screenshot({path:path.join(folder,'showing-mobile-bottom.png'),fullPage:true});
      await page.setViewportSize({width:1280,height:1000});
      await full.check();
      await page.screenshot({path:path.join(folder,'full-desktop.png'),fullPage:true});
      await showing.check();
    }
    await page.getByRole('button', {name:'Prepare agreement',exact:true}).click();
    await page.getByRole('button', {name:'Draft ready'}).waitFor();
    const payloads = await page.evaluate(() => window.savedPayloads);
    assert.equal(payloads.length,1);
    assert.equal(payloads[0].serviceLevel,'showing_services');
    assert.equal(payloads[0].showingFee,'150.25');
    assert.equal(payloads[0].intermediary,null);
    assert.ok(Object.values(payloads[0].compensation).every(value => value === null));
    assert.deepEqual(errors,[]);
    console.log('PASS: actual dialog toggle, answer retention, native validation, FormData and save payload; no live requests.');
  } finally {
    await browser.close();
  }
})().catch(error => {console.error(error);process.exitCode=1;});
