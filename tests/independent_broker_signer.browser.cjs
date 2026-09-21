// Offline browser check of the actual send dialog, with all live traffic blocked.
const fs = require('node:fs');
const path = require('node:path');
const assert = require('node:assert/strict');
const {chromium} = require('playwright');
const html = fs.readFileSync(path.join(__dirname, '..', 'index.html'), 'utf8');
const block = (tag, id) => {
  const match = html.match(new RegExp(`<${tag} id="${id}">([\\s\\S]*?)<\\/${tag}>`));
  assert.ok(match, `Missing ${id}`);
  return match[1];
};
const script = block('script', 'hof-standalone-agreement-signing-v1');
const preamble = script.slice(script.indexOf('const root = window;'), script.indexOf('const activeAgent'));
const dialog = script.slice(script.indexOf('async function openSendDialog'), script.indexOf('async function refreshAgreementSignWellStatus'));
const style = block('style', 'hof-txr1507-drafts-v1');

(async () => {
  const browser = await chromium.launch({headless:true, channel:'chrome'});
  try {
    const page = await browser.newPage({viewport:{width:390, height:844}});
    await page.route('**/*', route => route.abort());
    const errors = [];
    page.on('pageerror', error => errors.push(error.message));
    await page.setContent(`<!doctype html><html><head><style>
      :root{--gray-light:#c8d1db;--white:#fff;--navy:#0d1f35;--gold:#c8973f}
      *{box-sizing:border-box}body{font-family:Arial;margin:0;background:#0d1f35}
      input{background:#132c45;border:1px solid #8095a6;border-radius:6px}
      button{padding:12px;border-radius:6px}${style}</style></head><body><script>
      window.hofAuth={session:{access_token:'offline-test'}};
      window.posts=[];window.failSend=true;
      window.contacts=[
        {id:'1',name:'QA Client',email:'',emailEditable:true,label:'Client 1'},
        {id:'broker',name:'',email:'',emailEditable:true,nameEditable:true,label:'Broker signer'}];
      window.fetch=async(url,options)=>{
        if(options.method==='POST'){
          posts.push(JSON.parse(options.body));
          return {ok:!failSend,json:async()=>failSend?{error:'Temporary delivery issue. Try again.'}:{message:'Saved test result.'}};
        }
        return {ok:true,json:async()=>({recipients:contacts})};
      };
      ${preamble}${dialog}
      window.openTestDialog=()=>openSendDialog({id:'qa',form_code:'TXR-1507'},async()=>{});
      </script></body></html>`);
    await page.evaluate(() => openTestDialog());
    const client = page.locator('[name="clientEmail1"]');
    const brokerName = page.getByLabel("Broker's name", {exact:true});
    const brokerEmail = page.getByLabel("Broker's email", {exact:true});
    const submit = page.getByRole('button', {name:'Send signature request',exact:true});
    await client.fill('client@example.test');
    assert.equal(await page.locator('form').evaluate(form => form.checkValidity()), false);
    await brokerName.fill('QA Broker');
    await brokerEmail.fill('client@example.test');
    await submit.click();
    assert.match(await page.locator('#hofStandaloneSendStatus').innerText(), /different email/);
    assert.equal(await page.evaluate(() => posts.length), 0);
    await brokerEmail.fill('broker@example.test');
    assert.equal(await page.locator('form').evaluate(form => form.checkValidity()), true);
    await submit.click();
    await page.getByText('Temporary delivery issue. Try again.', {exact:true}).waitFor();
    assert.equal(await brokerName.inputValue(), 'QA Broker');
    assert.equal(await brokerEmail.inputValue(), 'broker@example.test');
    assert.equal(await submit.isEnabled(), true);
    const folder = process.argv[2];
    if (folder) {
      fs.mkdirSync(folder, {recursive:true});
      await submit.scrollIntoViewIfNeeded();
      assert.equal(await page.locator('form').evaluate(form => form.scrollWidth <= form.clientWidth), true);
      await page.screenshot({path:path.join(folder,'broker-mobile.png'),fullPage:true});
      await page.setViewportSize({width:1280,height:900});
      await page.screenshot({path:path.join(folder,'broker-desktop.png'),fullPage:true});
    }
    await submit.click();
    assert.equal(await page.evaluate(() => posts.length), 2);
    const posted = await page.evaluate(() => posts[0]);
    assert.deepEqual(posted.clientEmails, ['client@example.test']);
    assert.deepEqual(posted.brokerSigner, {id:'broker',name:'QA Broker',email:'broker@example.test'});
    assert.equal(posted.confirmedRecipients.length, 2);
    assert.deepEqual(posted.confirmedRecipients[1], posted.brokerSigner);
    await page.evaluate(() => {
      contacts[1]={id:'broker',name:'Saved Broker',email:'saved@example.test',emailEditable:false,label:'Broker signer'};
      return openTestDialog();
    });
    assert.equal(await page.locator('[name="signerNamebroker"]').count(), 0);
    assert.equal(await page.locator('input[readonly]').inputValue(), 'saved@example.test');
    await page.locator('[name="clientEmail1"]').fill('client@example.test');
    await submit.click();
    const saved = await page.evaluate(() => posts.at(-1));
    assert.equal(saved.brokerSigner, undefined);
    assert.deepEqual(saved.clientEmails, ['client@example.test']);
    assert.equal(saved.confirmedRecipients[1].email, 'saved@example.test');
    await page.evaluate(() => { failSend = false; });
    await submit.click();
    await page.locator('#hofStandaloneSendDialog').waitFor({state:'detached'});
    assert.deepEqual(errors, []);
    console.log('PASS: no-seat broker inputs, native validation, duplicate protection, exact payload, retry retention, saved contact lock, responsive dialog; zero live requests.');
  } finally {
    await browser.close();
  }
})().catch(error => {console.error(error);process.exitCode=1;});
