#!/usr/bin/env node
// Screen-record PUBLIC web pages as Reel footage.
// Usage: node record.mjs spec.json [--out /path/out.mp4]
// Hard rules: fresh in-memory browser every run (chromium.launch + newContext, no
// userDataDir, no storageState, no cookies, no CDP/extension attach), public http(s)
// pages only, no logins, no form submits (all non-GET/HEAD requests are aborted).
import { chromium } from 'playwright';
import { readFileSync, mkdirSync, rmSync, statSync, readdirSync } from 'node:fs';
import { execFileSync } from 'node:child_process';
import path from 'node:path';
import os from 'node:os';

const args = process.argv.slice(2);
if (!args[0]) { console.error('usage: node record.mjs spec.json [--out out.mp4]'); process.exit(2); }
const spec = JSON.parse(readFileSync(args[0], 'utf8'));
const outIdx = args.indexOf('--out');
const out = path.resolve(outIdx > 0 ? args[outIdx + 1] : (spec.out || 'recording.mp4'));

// ---- safety guards ----
const FORBIDDEN_KEYS = ['storageState', 'cookies', 'userDataDir', 'profile', 'cdp', 'cdpUrl', 'wsEndpoint', 'extension', 'login', 'password', 'fill', 'type'];
(function scan(o) {
  if (o && typeof o === 'object') for (const [k, v] of Object.entries(o)) {
    if (FORBIDDEN_KEYS.includes(k)) throw new Error(`spec key "${k}" is not allowed (public pages only, no profiles/cookies/logins/typing)`);
    scan(v);
  }
})(spec);
const checkUrl = (u) => {
  const p = new URL(u);
  if (!['http:', 'https:'].includes(p.protocol)) throw new Error(`only http(s) URLs allowed: ${u}`);
  if (/^(localhost|127\.|10\.|192\.168\.|0\.0\.0\.0|\[::1\])/.test(p.hostname)) throw new Error(`private host not allowed: ${u}`);
  if (/(^|\.)(instagram\.com|threads\.(net|com)|facebook\.com|accounts\.google\.com|login\.)/.test(p.hostname)) console.warn(`WARNING: ${p.hostname} — public view only, logged out; never sign in.`);
  return u;
};
checkUrl(spec.url);

// ---- geometry: default vertical 1080x1920 output ----
// viewport = CSS pixels the page lays out at. Playwright's screencast captures in CSS pixels
// (deviceScaleFactor is NOT reflected in the video), so we record at viewport size and
// upscale with lanczos to outSize. Default 720x1280 -> 1080x1920 (phone-ish layout, readable
// text, slightly soft). For max sharpness use viewport 1080x1920 (desktop layout, small text).
const vp = spec.viewport || { width: 720, height: 1280 };
const scale = spec.scale || 1;
const size = { width: vp.width, height: vp.height };
const outSize = spec.outSize || { width: 1080, height: 1920 };
const fps = spec.fps || 30;

const tmp = path.join(os.tmpdir(), `screenrec-${Date.now()}`);
mkdirSync(tmp, { recursive: true });
const webm = path.join(tmp, 'raw.webm');

const browser = await chromium.launch({ headless: spec.headless !== false });
const context = await browser.newContext({
  viewport: vp, deviceScaleFactor: scale, isMobile: !!spec.mobile, hasTouch: !!spec.mobile,
  locale: spec.locale || 'en-US', colorScheme: spec.colorScheme || 'light',
  acceptDownloads: false,
});
await context.route('**/*', (route) => {
  const m = route.request().method();
  if (m === 'GET' || m === 'HEAD' || m === 'OPTIONS') return route.continue();
  console.warn(`blocked ${m} ${route.request().url().slice(0, 100)}`);
  return route.abort();
});
const page = await context.newPage();
page.setDefaultTimeout(spec.timeout || 15000);

await page.goto(spec.url, { waitUntil: 'domcontentloaded' });
await page.waitForLoadState('networkidle', { timeout: 8000 }).catch(() => {});
if (spec.hide) for (const sel of spec.hide) await page.addStyleTag({ content: `${sel}{display:none !important}` }).catch(() => {});

await page.screencast.start({ path: webm, size, fps });
const s = spec.showActions ?? true;
if (s) await page.screencast.showActions({
  cursor: 'pointer', duration: 900, position: 'top',
  style: {
    point: 'width:26px;height:26px;border-radius:50%;background:rgba(255,200,0,.55);border:2px solid #ffb400',
    highlight: 'outline:4px solid #ffb400;background:rgba(255,200,0,.12);border-radius:6px',
    title: 'font-size:22px;background:rgba(0,0,0,.75);color:#fff;padding:6px 12px;border-radius:8px',
  },
});

const target = (st) => st.selector ? page.locator(st.selector).first()
  : st.role ? page.getByRole(st.role, { name: st.name }).first()
  : page.getByText(st.text, { exact: !!st.exact }).first();

async function smoothScroll(byY, ms) {
  await page.evaluate(async ([dy, dur]) => {
    const start = window.scrollY, t0 = performance.now();
    await new Promise((res) => {
      const f = (t) => {
        const k = Math.min(1, (t - t0) / dur), e = k < .5 ? 2 * k * k : 1 - Math.pow(-2 * k + 2, 2) / 2;
        window.scrollTo(0, start + dy * e);
        k < 1 ? requestAnimationFrame(f) : res();
      };
      requestAnimationFrame(f);
    });
  }, [byY, ms]);
}

const wait = (ms) => page.waitForTimeout(ms);
for (const st of spec.steps || []) {
  const a = st.action;
  console.log('step', JSON.stringify(st));
  if (a === 'wait') await wait(st.ms ?? 1000);
  else if (a === 'chapter') { await page.screencast.showChapter(st.title, { description: st.description, duration: st.ms ?? 2000 }); await wait(st.ms ?? 2000); }
  else if (a === 'scroll') {
    if (st.to || st.selector || st.text || st.role) {
      const loc = target({ ...st, selector: st.to || st.selector });
      const box = await loc.boundingBox();
      const dy = box ? box.y - (st.offset ?? vp.height * 0.25) : 0;
      await smoothScroll(dy, st.ms ?? 1500);
    } else await smoothScroll(st.by ?? vp.height * 0.8, st.ms ?? 1500);
    await wait(st.pause ?? 300);
  }
  else if (a === 'hover') { await target(st).hover(); await wait(st.ms ?? 800); }
  else if (a === 'click') {
    const loc = target(st);
    const tag = await loc.evaluate((el) => (el.closest('form') && (el.type === 'submit' || el.tagName === 'BUTTON')) ? 'form-submit' : 'ok');
    if (tag === 'form-submit') throw new Error('refusing to click a form submit button');
    await loc.click(); await page.waitForLoadState('domcontentloaded').catch(() => {});
    checkUrl(page.url()); await wait(st.ms ?? 1200);
  }
  else if (a === 'highlight') {
    const loc = target(st);
    await loc.scrollIntoViewIfNeeded().catch(() => {});
    await loc.evaluate((el, label) => {
      el.dataset.srPrev = el.getAttribute('style') || '';
      el.style.outline = '5px solid #ffb400'; el.style.outlineOffset = '6px';
      el.style.background = 'rgba(255,200,0,.18)'; el.style.borderRadius = '6px';
      el.style.transition = 'all .3s';
      if (label) {
        const tag = document.createElement('div'); tag.id = 'sr-label'; tag.textContent = label;
        Object.assign(tag.style, { position: 'absolute', zIndex: 2147483647, background: '#ffb400', color: '#111', font: '700 18px system-ui,sans-serif', padding: '4px 10px', borderRadius: '6px' });
        const r = el.getBoundingClientRect();
        tag.style.left = `${r.left + scrollX}px`; tag.style.top = `${r.top + scrollY - 40}px`;
        document.body.appendChild(tag);
      }
    }, st.label || null);
    await wait(st.ms ?? 2000);
    await loc.evaluate((el) => { el.setAttribute('style', el.dataset.srPrev || ''); document.getElementById('sr-label')?.remove(); });
  }
  else if (a === 'goto') { await page.goto(checkUrl(st.url), { waitUntil: 'domcontentloaded' }); await wait(st.ms ?? 1200); }
  else throw new Error(`unknown action ${a}`);
}
await wait(spec.tail ?? 600);
await page.screencast.stop();
await context.close(); await browser.close();

// ---- convert to mp4 (H.264, yuv420p, IG friendly) ----
mkdirSync(path.dirname(out), { recursive: true });
const vf = [`scale=${outSize.width}:${outSize.height}:flags=lanczos`, `fps=${fps}`];
// landscape viewport (e.g. 1280x720) + cropTo916: center-crop to 9:16 before scaling
if (spec.cropTo916 && size.width / size.height > 9 / 16) vf.unshift(`crop=ih*9/16:ih:${spec.cropX ?? '(iw-ow)/2'}:0`);
execFileSync('ffmpeg', ['-y', '-loglevel', 'error', '-i', webm, '-vf', vf.join(','), '-c:v', 'libx264', '-preset', 'slow', '-crf', String(spec.crf ?? 23), '-pix_fmt', 'yuv420p', '-movflags', '+faststart', '-an', out]);
if (spec.keepWebm) execFileSync('cp', [webm, out.replace(/\.mp4$/, '.webm')]);
rmSync(tmp, { recursive: true, force: true });
console.log(`done: ${out} (${(statSync(out).size / 1e6).toFixed(1)} MB)`);
