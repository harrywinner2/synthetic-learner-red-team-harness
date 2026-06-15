import { chromium } from 'playwright';
const path = 'file://' + process.cwd() + '/ui/mockup.html';
const browser = await chromium.launch();
const page = await browser.newContext({ viewport:{width:1440,height:900} }).then(c=>c.newPage());
const errors=[];
page.on('console', m=>{ if(m.type()==='error') errors.push(m.text()); });
page.on('pageerror', e=>errors.push('PAGEERROR: '+e.message));
await page.goto(path,{waitUntil:'networkidle'});
const views=['overview','failures','improve','metrics','learners','run','transcripts','about'];
for(const v of views){
  await page.click(`.nav[data-v="${v}"]`).catch(()=>{});
  await page.waitForTimeout(500);
  const visible = await page.locator(`#v-${v}`).isVisible();
  const h1 = await page.locator(`#v-${v} h1`).first().textContent().catch(()=>'(none)');
  console.log(`${v.padEnd(12)} visible=${visible}  h1="${(h1||'').trim()}"`);
  await page.screenshot({ path:`design/mockup-${v}.png` });
}
console.log('\nCONSOLE ERRORS:', errors.length? errors : 'none');
await browser.close();
