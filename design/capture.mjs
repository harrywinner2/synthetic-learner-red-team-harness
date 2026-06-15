import { chromium } from 'playwright';

const targets = [
  { url: 'https://www.varsitytutors.com/', name: 'varsitytutors-home' },
  { url: 'https://www.nerdy.com/', name: 'nerdy-home' },
];

const browser = await chromium.launch();
const ctx = await browser.newContext({ viewport: { width: 1440, height: 900 } });

for (const t of targets) {
  try {
    const page = await ctx.newPage();
    await page.goto(t.url, { waitUntil: 'networkidle', timeout: 45000 });
    await page.waitForTimeout(2000);
    await page.screenshot({ path: `design/${t.name}.png`, fullPage: false });

    const tokens = await page.evaluate(() => {
      const seen = {};
      const bump = (map, k) => { if (!k) return; map[k] = (map[k] || 0) + 1; };
      const colors = {}, bgs = {}, fonts = {}, radii = {}, sizes = {};
      const els = Array.from(document.querySelectorAll('body *')).slice(0, 4000);
      for (const el of els) {
        const s = getComputedStyle(el);
        bump(colors, s.color);
        bump(bgs, s.backgroundColor);
        bump(fonts, s.fontFamily);
        bump(radii, s.borderRadius);
        bump(sizes, s.fontSize);
      }
      const top = (m, n = 8) => Object.entries(m)
        .filter(([k]) => k && k !== 'rgba(0, 0, 0, 0)' && k !== 'none' && k !== '0px')
        .sort((a, b) => b[1] - a[1]).slice(0, n).map(([k, v]) => ({ k, v }));
      const h1 = document.querySelector('h1');
      const btn = document.querySelector('button, a.btn, [class*="button" i]');
      return {
        title: document.title,
        topColors: top(colors), topBackgrounds: top(bgs),
        topFonts: top(fonts, 4), topRadii: top(radii), topSizes: top(sizes),
        h1Font: h1 ? getComputedStyle(h1).fontFamily : null,
        h1Weight: h1 ? getComputedStyle(h1).fontWeight : null,
        h1Size: h1 ? getComputedStyle(h1).fontSize : null,
        btnBg: btn ? getComputedStyle(btn).backgroundColor : null,
        btnColor: btn ? getComputedStyle(btn).color : null,
        btnRadius: btn ? getComputedStyle(btn).borderRadius : null,
      };
    });
    console.log('=== ' + t.name + ' ===');
    console.log(JSON.stringify(tokens, null, 2));
    await page.close();
  } catch (e) {
    console.log('FAILED ' + t.name + ': ' + e.message);
  }
}
await browser.close();
