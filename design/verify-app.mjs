import { chromium } from 'playwright';
const base = process.argv[2] || 'http://127.0.0.1:8231';
const browser = await chromium.launch();
const page = await browser.newContext({ viewport:{width:1440,height:900} }).then(c=>c.newPage());
const errors=[];
page.on('console', m=>{ if(m.type()==='error') errors.push(m.text()); });
page.on('pageerror', e=>errors.push('PAGEERROR: '+e.message));
await page.goto(base, {waitUntil:'networkidle'});
await page.waitForTimeout(1500);
const views=['overview','failures','improve','metrics','learners','run','transcripts','about'];
for(const v of views){
  await page.click(`.nav[data-v="${v}"]`).catch(()=>{});
  await page.waitForTimeout(600);
  const h1 = await page.locator(`#v-${v} h1`).first().textContent().catch(()=>'(none)');
  const txt = await page.locator(`#v-${v}`).textContent().catch(()=>'');
  console.log(`${v.padEnd(12)} h1="${(h1||'').trim().slice(0,38)}"  len=${txt.length}`);
  await page.screenshot({ path:`design/app-${v}.png` });
}
console.log('\nCONSOLE ERRORS:', errors.length? errors.slice(0,8) : 'none');
await browser.close();
