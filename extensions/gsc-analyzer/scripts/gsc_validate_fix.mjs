#!/usr/bin/env node
/**
 * Best-effort Playwright automation that clicks GSC's "Validate Fix" button —
 * a UI-only action (no Search Console API exists for it) used to ask Google
 * to re-check an issue class whose fix is already live.
 *
 * Auth model: the SAME persistent Chromium profile as gsc_ui_export.mjs
 * (default ~/.cache/gsc-ui-profile, override with GSC_UI_PROFILE_DIR).
 * Google blocks scripted logins, so login is a ONE-TIME manual step; saved
 * cookies then keep headless runs working for weeks/months. One `--setup`
 * serves both this script and the exporter.
 *
 *   # one-time (headed): log in to the Google account that owns GSC
 *   GSC_SITE_URL="sc-domain:example.com" node gsc_validate_fix.mjs --setup
 *
 *   # validate the default issue classes (Not found 404 + Server error 5xx):
 *   GSC_SITE_URL="sc-domain:example.com" node gsc_validate_fix.mjs
 *
 *   # custom issue list (exact GSC row labels, comma-separated):
 *   node gsc_validate_fix.mjs --issues="Not found (404),Server error (5xx)"
 *
 *   # locate the button but DON'T click (safe rehearsal):
 *   node gsc_validate_fix.mjs --dry-run
 *
 *   # attach to an already-running, signed-in Chrome instead of the profile:
 *   node gsc_validate_fix.mjs --cdp=http://localhost:9222
 *
 * Exit codes: 0 = ran (see per-issue log; "started" vs "skipped"),
 * 2 = session expired (re-run --setup), 1 = other failure. Callers should
 * treat a non-zero exit as "skip validation this run, flag the human" — the
 * fixes still clear organically; Validate Fix only accelerates Google's recheck.
 *
 * GSC's UI has no stable public selectors; this uses roles/aria/visible text,
 * is idempotent (skips issues with no clickable "Validate Fix"), and logs
 * loudly. Expect to tune selectors after the first supervised run.
 */

import { createRequire } from 'node:module';
import { homedir } from 'node:os';
import { join } from 'node:path';

function log(msg) {
  process.stderr.write(`[gsc-validate-fix] ${msg}\n`);
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

const PROFILE_DIR =
  process.env.GSC_UI_PROFILE_DIR || join(homedir(), '.cache', 'gsc-ui-profile');
const RESOURCE_ID = encodeURIComponent(SITE_URL);
const INDEXING_REPORT_URL = `https://search.google.com/search-console/index?resource_id=${RESOURCE_ID}`;

const isSetup = process.argv.includes('--setup');
const headless = process.argv.includes('--headless');
const dryRun = process.argv.includes('--dry-run');

/** Read a flag that takes a value, accepting both `--flag=value` and
 * `--flag value`. Returns `fallback` when the flag is present with no value,
 * or null when absent. */
function flagValue(name, fallback = null) {
  const eq = process.argv.find((a) => a.startsWith(`${name}=`));
  if (eq) return eq.slice(name.length + 1) || fallback;
  const idx = process.argv.indexOf(name);
  if (idx === -1) return null;
  const next = process.argv[idx + 1];
  return next && !next.startsWith('--') ? next : fallback;
}

// --cdp[=<http endpoint>]: instead of the persistent profile, attach to an
// already-running Chrome over the DevTools protocol (e.g. one launched with
// --remote-debugging-port=9222 on a profile that's already signed into GSC).
// Bypasses Google's automated-login block by reusing a real session.
const CDP_ENDPOINT = flagValue('--cdp', 'http://localhost:9222');

const issuesRaw = flagValue('--issues');
const TARGET_ISSUES = issuesRaw
  ? issuesRaw.split(',').map((s) => s.trim()).filter(Boolean)
  : ['Not found (404)', 'Server error (5xx)'];

const chromium = await loadChromium();

async function launch() {
  return chromium.launchPersistentContext(PROFILE_DIR, {
    headless: isSetup ? false : headless,
    viewport: { width: 1440, height: 900 },
  });
}

async function setup() {
  const ctx = await launch();
  const page = ctx.pages()[0] ?? (await ctx.newPage());
  await page.goto(INDEXING_REPORT_URL, { waitUntil: 'domcontentloaded' });
  log('Log in to Google in the opened window. Waiting up to 5 minutes...');
  await page.waitForURL(/search-console/, { timeout: 300_000 });
  await page
    .getByText(/page indexing|why pages aren.t indexed/i)
    .first()
    .waitFor({ timeout: 120_000 });
  log(`Login confirmed. Profile saved at ${PROFILE_DIR} (shared with gsc_ui_export.mjs).`);
  await ctx.close();
}

/** Click a confirm/primary button if a dialog pops, then best-effort wait for
 * the "validation started" status (the click already succeeded — this is for
 * the log only). */
async function confirmAndWait(page) {
  const confirm = page.getByRole('button', { name: /^(validate|start|ok|confirm|got it)$/i }).first();
  if (await confirm.isVisible({ timeout: 3_000 }).catch(() => false)) {
    await confirm.click().catch(() => {});
  }
  await page
    .getByText(/validation started|validation requested|we.?ll let you know|validating/i)
    .first()
    .waitFor({ timeout: 15_000 })
    .catch(() => {});
}

/** On an issue drilldown, request validation. Handles the three real GSC
 * states (verified against the live UI):
 *   - fresh issue        → a "VALIDATE FIX" button is present → click it ('started')
 *   - validation FAILED  → no button; "SEE DETAILS" → "START NEW VALIDATION" ('restarted')
 *   - already validating → "Validation started" banner, no button ('already-validating')
 * Returns 'started' | 'restarted' | 'already-validating' | 'no-button'. */
async function clickValidateOnDetailPage(page) {
  // Let the drilldown render its validation banner / button first.
  await page
    .getByText(/validate fix|validation (started|failed|succeeded|in progress)/i)
    .first()
    .waitFor({ timeout: 20_000 })
    .catch(() => {});

  // 1) Fresh issue: a "Validate Fix" button is present.
  const fixBtn = page.getByRole('button', { name: /validate fix/i }).first();
  if (await fixBtn.isVisible().catch(() => false)) {
    if (dryRun) { log('  [dry-run] "Validate Fix" found — not clicking.'); return 'started'; }
    await fixBtn.click();
    await confirmAndWait(page);
    return 'started';
  }

  // 2) Previous validation FAILED → re-run via "See details" → "Start new validation".
  if (await page.getByText(/validation failed/i).first().isVisible().catch(() => false)) {
    if (dryRun) { log('  [dry-run] validation failed — would Start New Validation.'); return 'restarted'; }
    await page.getByRole('button', { name: /see details/i }).first().click({ timeout: 8_000 }).catch(() => {});
    const snv = page.getByRole('button', { name: /start new validation/i }).first();
    if (await snv.isVisible({ timeout: 6_000 }).catch(() => false)) {
      await snv.click();
      await confirmAndWait(page);
      return 'restarted';
    }
    return 'no-button';
  }

  // 3) Already running (started / in progress) — don't re-trigger.
  if (await page.getByText(/validation started|validating|in progress/i).first().isVisible().catch(() => false)) {
    return 'already-validating';
  }
  return 'no-button';
}

/** Drive the Page Indexing report on an authenticated page: for each target
 * issue, open it and click "Validate Fix". Exits 2 if the session is expired. */
async function runValidation(page) {
  await page.goto(INDEXING_REPORT_URL, { waitUntil: 'domcontentloaded' });
  if (page.url().includes('accounts.google.com')) {
    log('Session expired / not logged in — re-run --setup (persistent) or relaunch Chrome signed in (cdp).');
    process.exit(2);
  }
  await page
    .getByText(/why pages aren.t indexed/i)
    .first()
    .waitFor({ timeout: 60_000 })
    .catch(() => log('WARN: "Why pages aren\'t indexed" header not found — UI may have changed.'));

  const results = {};
  for (const issue of TARGET_ISSUES) {
    try {
      await page.goto(INDEXING_REPORT_URL, { waitUntil: 'domcontentloaded' });
      const row = page.getByText(issue, { exact: true }).first();
      const found = await row.waitFor({ state: 'visible', timeout: 20_000 }).then(() => true).catch(() => false);
      if (!found) {
        results[issue] = 'not-listed';
        log(`SKIP "${issue}": not present in the report (already cleared or label changed).`);
        continue;
      }
      await row.click();
      await page.waitForLoadState('domcontentloaded');
      const outcome = await clickValidateOnDetailPage(page);
      results[issue] = outcome;
      log(`${issue} -> ${outcome}`);
    } catch (err) {
      results[issue] = `error: ${err.message.split('\n')[0]}`;
      log(`SKIP "${issue}": ${err.message.split('\n')[0]}`);
    }
  }
  log(`done${dryRun ? ' (dry-run)' : ''}: ${JSON.stringify(results)}`);
  const anyStarted = Object.values(results).some((v) => v === 'started' || v === 'restarted');
  const anyError = Object.values(results).some((v) => String(v).startsWith('error'));
  return { anyStarted, anyError };
}

async function validate() {
  const ctx = await launch();
  const page = ctx.pages()[0] ?? (await ctx.newPage());
  const { anyStarted, anyError } = await runValidation(page);
  await ctx.close();
  if (!anyStarted && anyError) process.exit(1);
}

async function validateOverCdp(endpoint) {
  log(`connecting over CDP: ${endpoint}`);
  const browser = await chromium.connectOverCDP(endpoint);
  const ctx = browser.contexts()[0] ?? (await browser.newContext());
  const page = ctx.pages().find((p) => !p.isClosed()) ?? (await ctx.newPage());
  const { anyStarted, anyError } = await runValidation(page);
  await browser.close(); // detaches CDP; does NOT quit the user's Chrome
  if (!anyStarted && anyError) process.exit(1);
}

if (isSetup) {
  await setup();
} else if (CDP_ENDPOINT) {
  await validateOverCdp(CDP_ENDPOINT);
} else {
  await validate();
}
