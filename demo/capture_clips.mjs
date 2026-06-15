import { chromium } from 'playwright';
import fs from 'fs';
import path from 'path';

const base = process.argv[2] || 'https://web-production-89f52.up.railway.app';
const manifest = JSON.parse(fs.readFileSync('demo/audio/manifest.json', 'utf8'));
const outDir = 'demo/clips';
fs.mkdirSync(outDir, { recursive: true });

// beat id -> what to show on screen. `url` overrides the base+nav (e.g. GitHub).
const REPO = 'https://github.com/harrywinner2/synthetic-learner-red-team-harness';
const BEATS = {
  1:  { view: 'overview', scroll: 0 },
  2:  { view: 'overview', scroll: 120 },
  3:  { view: 'learners', scroll: 0 },
  4:  { view: 'learners', scroll: 360 },
  5:  { view: 'transcripts', scroll: 0 },
  6:  { view: 'metrics', scroll: 0 },
  7:  { view: 'metrics', scroll: 640 },
  8:  { view: 'failures', scroll: 0 },
  9:  { view: 'improve', scroll: 0 },
  10: { view: 'run', scroll: 0 },
  11: { view: 'run', scroll: 360 },
  12: { url: REPO, scroll: 420 },
  13: { view: 'about', scroll: 0 },
  14: { view: 'overview', scroll: 0 },
};
const W = 1440, H = 900;

for (const beat of manifest) {
  const id = String(beat.id).padStart(3, '0');
  const dur = Math.max(3, beat.seconds);
  const cfg = BEATS[beat.id] || { view: 'overview', scroll: 0 };
  const tmp = path.join(outDir, `tmp_${id}`);
  fs.mkdirSync(tmp, { recursive: true });

  const browser = await chromium.launch();
  const ctx = await browser.newContext({ viewport: { width: W, height: H },
    recordVideo: { dir: tmp, size: { width: W, height: H } } });
  const page = await ctx.newPage();
  if (cfg.url) {
    await page.goto(cfg.url, { waitUntil: 'domcontentloaded' }).catch(() => {});
    await page.waitForTimeout(2500);
  } else {
    await page.goto(base, { waitUntil: 'networkidle' });
    await page.waitForTimeout(1200);
    if (cfg.view !== 'overview') {
      await page.click(`.nav[data-v="${cfg.view}"]`).catch(() => {});
      await page.waitForTimeout(900);
    }
  }
  if (cfg.scroll) {
    await page.evaluate((y) => window.scrollTo({ top: y, behavior: 'smooth' }), cfg.scroll);
  }
  // gentle motion for the remainder of the beat
  const steps = Math.max(2, Math.round(dur / 2));
  for (let s = 0; s < steps; s++) {
    await page.waitForTimeout((dur * 1000) / steps);
    if (!cfg.sel) await page.mouse.wheel(0, 90).catch(() => {});
  }
  await ctx.close();   // flush video
  await browser.close();

  // move the generated webm to clip_<id>.webm
  const vid = fs.readdirSync(tmp).find((f) => f.endsWith('.webm'));
  if (vid) {
    fs.renameSync(path.join(tmp, vid), path.join(outDir, `clip_${id}.webm`));
    console.log(`clip_${id}.webm  (${dur.toFixed(1)}s)  [${cfg.view}]`);
  } else {
    console.log(`clip_${id}: NO VIDEO`);
  }
  fs.rmSync(tmp, { recursive: true, force: true });
}
console.log('capture done');
