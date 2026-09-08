#!/usr/bin/env node
// fe-interactions.mjs — deterministic browser interaction probe for one scenario.
// Drives the served frontend with Playwright under CPU throttling, performs the
// scripted actions and measures what a user feels during the refetch:
//   requests      API requests matching apiPattern fired by the interaction
//   minRows       fewest rendered rows seen while the refetch is in flight
//                 (0 = the table blanks; > 0 = placeholder data holds the view)
//   longTasks     long tasks (> 50 ms) during the interaction window
//   longTaskMax   the worst of them, ms
// Median-by-longTaskMax of N runs is reported; all runs are archived.
//
// Usage:  node fe-interactions.mjs <scenario-key> <out-dir>
// Reads:  $PERF_EXT_DIR/fe-interactions.json  (see templates/fe-interactions.json)
// Needs:  playwright resolvable from $PERF_APP_DIR, the project root, or globally
//         (npm i -D playwright && npx playwright install chromium). When it is not,
//         exits 1 with a one-line reason so the caller can print "unavailable".
// Output: <out-dir>/fe-interactions.json + one summary line on stdout.

import { createRequire } from 'node:module';
import { readFileSync, writeFileSync } from 'node:fs';
import path from 'node:path';

const [key, outDir] = process.argv.slice(2);
if (!key || !outDir) fail('usage: fe-interactions.mjs <scenario-key> <out-dir>');

const extDir = process.env.PERF_EXT_DIR || path.join(process.cwd(), '.claude/skills/creo-perf');
let cfg;
try { cfg = JSON.parse(readFileSync(path.join(extDir, 'fe-interactions.json'), 'utf8')); }
catch (e) { fail(`no readable fe-interactions.json in ${extDir}`); }
const sc = cfg.scenarios?.[key];
if (!sc) fail(`scenario key "${key}" not in fe-interactions.json`);

const chromium = resolvePlaywright();
const baseUrl = (sc.baseUrl || cfg.baseUrl || process.env.PERF_WEB || '').replace(/\/$/, '');
if (!baseUrl) fail('no baseUrl (fe-interactions.json or PERF_WEB)');
const cpu = sc.cpuThrottle ?? cfg.cpuThrottle ?? 4;
const runs = sc.runs ?? cfg.runs ?? 3;
const settle = sc.settle ?? cfg.settle ?? 1500;
const apiRe = new RegExp(sc.apiPattern || cfg.apiPattern || '/api/');
const viewport = sc.viewport || cfg.viewport || { width: 1440, height: 900 };

const results = [];
const browser = await chromium.launch({ headless: true, args: ['--no-sandbox'] });
try {
  for (let i = 0; i < runs; i++) results.push(await runOnce());
} finally {
  await browser.close();
}

const sorted = [...results].sort((a, b) => a.longTaskMax - b.longTaskMax);
const median = sorted[Math.floor(sorted.length / 2)];
writeFileSync(path.join(outDir, 'fe-interactions.json'), JSON.stringify({ scenario: key, label: sc.label, cpuThrottle: cpu, runs: results, median }, null, 1));

const holds = median.minRows > 0
  ? `view holds its rows through the refetch (min ${median.minRows} rendered)`
  : 'view BLANKS mid-refetch (min 0 rendered rows)';
const rowsPart = sc.rows ? ` · ${holds}` : '';
console.log(`${sc.label}: ${median.requests} ${sc.apiPattern || 'api'} request(s) fired${rowsPart} · ${median.longTasks} long tasks, worst ${median.longTaskMax} ms · median of ${results.length}/${runs} runs @${cpu}x CPU`);

async function runOnce() {
  const context = await browser.newContext({ viewport, storageState: sc.storageState || cfg.storageState });
  const page = await context.newPage();
  await page.addInitScript(() => {
    window.__perfLongTasks = [];
    try {
      new PerformanceObserver((list) => {
        for (const e of list.getEntries()) window.__perfLongTasks.push(Math.round(e.duration));
      }).observe({ type: 'longtask', buffered: true });
    } catch {}
  });
  const cdp = await context.newCDPSession(page);
  await cdp.send('Emulation.setCPUThrottlingRate', { rate: cpu });

  await page.goto(baseUrl + (sc.path || '/'), { waitUntil: 'networkidle' });
  if (sc.ready) await page.waitForSelector(sc.ready, { timeout: 30000 });
  for (const a of sc.setup || []) await act(page, a);
  await page.waitForTimeout(sc.warmup ?? 500);

  let requests = 0;
  const onReq = (r) => { if (apiRe.test(r.url())) requests++; };
  page.on('request', onReq);
  await page.evaluate(() => { window.__perfLongTasks = []; });

  let minRows = Infinity;
  const sampler = sc.rows ? setInterval(async () => {
    try {
      const n = await page.locator(sc.rows).count();
      if (n < minRows) minRows = n;
    } catch {}
  }, 25) : null;

  for (const a of sc.actions || []) await act(page, a);
  await page.waitForTimeout(settle);
  if (sampler) clearInterval(sampler);
  page.off('request', onReq);

  const tasks = await page.evaluate(() => window.__perfLongTasks || []);
  await context.close();
  return {
    requests,
    minRows: sc.rows ? (minRows === Infinity ? 0 : minRows) : null,
    longTasks: tasks.length,
    longTaskMax: tasks.length ? Math.max(...tasks) : 0,
  };
}

async function act(page, a) {
  if (a.click) await page.locator(a.click).first().click();
  else if (a.type) await page.locator(a.type).first().pressSequentially(a.text ?? '', { delay: a.delay ?? 40 });
  else if (a.fill) await page.locator(a.fill).first().fill(a.text ?? '');
  else if (a.press) await page.keyboard.press(a.press);
  else if (a.hover) await page.locator(a.hover).first().hover();
  else if (a.select) await page.locator(a.select).first().selectOption(a.value);
  else if (a.wait) await page.waitForTimeout(a.wait);
  else if (a.waitFor) await page.waitForSelector(a.waitFor, { timeout: a.timeout ?? 30000 });
  else if (a.goto) await page.goto(baseUrl + a.goto, { waitUntil: 'networkidle' });
  else throw new Error(`unknown action ${JSON.stringify(a)}`);
}

function resolvePlaywright() {
  const roots = [process.env.PERF_APP_DIR, process.env.PERF_PROJECT_ROOT, process.cwd(), path.dirname(new URL(import.meta.url).pathname)].filter(Boolean);
  for (const r of roots) {
    try {
      const req = createRequire(path.join(r, 'package.json'));
      return req('playwright').chromium;
    } catch {}
  }
  try { return createRequire(import.meta.url)('playwright').chromium; } catch {}
  fail('playwright not resolvable — npm i -D playwright && npx playwright install chromium (in PERF_APP_DIR)');
}

function fail(msg) { console.error(msg); process.exit(1); }
