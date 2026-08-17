#!/usr/bin/env node
/**
 * Best-effort Playwright exporter for the GSC *UI-only* surfaces: the Page
 * indexing report and its per-issue URL drilldowns, which the Search Console
 * API cannot enumerate.
 *
 * Auth model: a persistent Chromium profile (default ~/.cache/gsc-ui-profile,
 * override with GSC_UI_PROFILE_DIR). Google blocks scripted logins, so the
 * login itself is a ONE-TIME manual step; the saved cookies then keep
 * headless-ish runs working for weeks/months until Google expires the session.
 *
 *   # one-time (headed): log in to the Google account that owns GSC, then
 *   # wait for the script to confirm and close
 *   GSC_SITE_URL="sc-domain:example.com" node gsc_ui_export.mjs --setup
 *
 *   # recurring run: exports issue CSVs into ./gsc-exports (or --out=<dir>,
 *   # or GSC_EXPORTS_DIR)
 *   GSC_SITE_URL="sc-domain:example.com" node gsc_ui_export.mjs
 *
 * Exit codes: 0 = exported (possibly partially, see log), 2 = session
 * expired (re-run --setup), 1 = other failure. Callers should treat a
 * non-zero exit as "skip UI ingestion this run" — any API sweep still runs.
 *
 * GSC's UI has no stable public selectors; this script uses aria-labels and
 * visible text and logs loudly when a step does not match. Expect to tune it
 * after the first supervised run.
 */

import { createRequire } from 'node:module';
import { execFileSync } from 'node:child_process';
import { existsSync, mkdirSync, readdirSync } from 'node:fs';
import { homedir } from 'node:os';
import { join, resolve } from 'node:path';

function log(msg) {
  process.stderr.write(`[gsc-ui-export] ${msg}\n`);
}

/** Resolve Playwright from the current project (plain import, then a
 * createRequire rooted at the cwd, accepting either the `playwright` or the
 * `@playwright/test` package). */
async function loadChromium() {
  try {
    return (await import('playwright')).chromium;
  } catch {
    /* fall through */
  }
  try {
    const require = createRequire(join(process.cwd(), 'package.json'));
    for (const pkg of ['playwright', '@playwright/test']) {
      try {
        return require(pkg).chromium;
      } catch {
        /* try next */
      }
    }
  } catch {
    /* fall through */
  }
  log('Playwright is not installed in this project.');
  log('Install it with: npm i -D playwright && npx playwright install chromium');
  process.exit(1);
}

const SITE_URL = process.env.GSC_SITE_URL;
if (!SITE_URL) {
  log('GSC_SITE_URL is not set. Set it to your Search Console property:');
  log('  export GSC_SITE_URL="sc-domain:example.com"    # domain property');
  log('  export GSC_SITE_URL="https://example.com/"     # URL-prefix property (trailing slash required)');
  process.exit(1);
}

const outFlag = process.argv.find((a) => a.startsWith('--out='));
const EXPORTS_DIR = resolve(
  outFlag ? outFlag.slice('--out='.length) : process.env.GSC_EXPORTS_DIR || './gsc-exports',
);
const PROFILE_DIR =
  process.env.GSC_UI_PROFILE_DIR || join(homedir(), '.cache', 'gsc-ui-profile');
const RESOURCE_ID = encodeURIComponent(SITE_URL);
const INDEXING_REPORT_URL = `https://search.google.com/search-console/index?resource_id=${RESOURCE_ID}`;

const isSetup = process.argv.includes('--setup');
const headless = process.argv.includes('--headless');

const chromium = await loadChromium();

async function launch() {
  return chromium.launchPersistentContext(PROFILE_DIR, {
    headless: isSetup ? false : headless,
    viewport: { width: 1440, height: 900 },
    acceptDownloads: true,
  });
}

async function setup() {
  const ctx = await launch();
  const page = ctx.pages()[0] ?? (await ctx.newPage());
  await page.goto(INDEXING_REPORT_URL, { waitUntil: 'domcontentloaded' });
  log('Log in to Google in the opened window. Waiting up to 5 minutes...');
  await page.waitForURL(/search-console/, { timeout: 300_000 });
  // Search Console chrome renders this once authenticated.
  await page
    .getByText(/page indexing|why pages aren.t indexed/i)
    .first()
    .waitFor({ timeout: 120_000 });
  log(`Login confirmed. Profile saved at ${PROFILE_DIR}.`);
  await ctx.close();
}

async function exportReport() {
  mkdirSync(EXPORTS_DIR, { recursive: true });
  const ctx = await launch();
  const page = ctx.pages()[0] ?? (await ctx.newPage());
  await page.goto(INDEXING_REPORT_URL, { waitUntil: 'domcontentloaded' });

  if (page.url().includes('accounts.google.com')) {
    log('Session expired — run again with --setup to re-login.');
    await ctx.close();
    process.exit(2);
  }
  await page
    .getByText(/why pages aren.t indexed/i)
    .first()
    .waitFor({ timeout: 60_000 });

  // Issue rows in the "Why pages aren't indexed" table. Each opens a
  // drilldown whose Export menu yields a zip with the URL list (Table.csv).
  const issueNames = await page
    .locator('table tr td:first-child')
    .allInnerTexts()
    .then((rows) => rows.map((r) => r.trim()).filter(Boolean))
    .catch(() => []);
  log(`Issue rows found: ${issueNames.length} — ${issueNames.join(' | ')}`);

  let exported = 0;
  for (const issue of issueNames) {
    try {
      await page.goto(INDEXING_REPORT_URL, { waitUntil: 'domcontentloaded' });
      await page.getByText(issue, { exact: true }).first().click();
      await page.waitForLoadState('domcontentloaded');

      const exportBtn = page.getByRole('button', { name: /export/i }).first();
      await exportBtn.waitFor({ timeout: 30_000 });
      await exportBtn.click();

      const downloadPromise = page.waitForEvent('download', {
        timeout: 60_000,
      });
      await page
        .getByRole('menuitem', { name: /download csv/i })
        .first()
        .click();
      const download = await downloadPromise;

      const slug = issue
        .toLowerCase()
        .replace(/[^a-z0-9]+/g, '-')
        .replace(/(^-|-$)/g, '');
      const target = join(EXPORTS_DIR, `${slug}.zip`);
      await download.saveAs(target);
      try {
        execFileSync('unzip', ['-o', target, '-d', join(EXPORTS_DIR, slug)]);
        // Downstream consumers glob gsc-exports/*.csv — surface Table.csv there.
        const tableCsv = join(EXPORTS_DIR, slug, 'Table.csv');
        if (existsSync(tableCsv)) {
          execFileSync('cp', [tableCsv, join(EXPORTS_DIR, `${slug}.csv`)]);
        }
      } catch (unzipErr) {
        log(`unzip failed for ${slug}: ${unzipErr.message}`);
      }
      log(`exported: ${issue} -> ${slug}.csv`);
      exported += 1;
    } catch (err) {
      log(`SKIP "${issue}": ${err.message.split('\n')[0]}`);
    }
  }

  await ctx.close();
  log(
    `done: ${exported}/${issueNames.length} issue exports in ${EXPORTS_DIR}: ` +
      readdirSync(EXPORTS_DIR).filter((f) => f.endsWith('.csv')).join(', '),
  );
  if (exported === 0 && issueNames.length > 0) process.exit(1);
}

if (isSetup) {
  await setup();
} else {
  await exportReport();
}
