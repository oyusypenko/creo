#!/usr/bin/env node
// =============================================================================
// check_year_staleness.mjs
//
// Purpose
// -------
// CI guard against year-rollover staleness. Walks all JSON content files
// under a content root and flags any string value that hardcodes a year
// token (current year or current year - 1) when the file's date field
// (default `dateModified`) is older than --max-age-days (default 90).
//
// Why: search engines demote year-stamped pages whose freshness signal lags.
// A title like "best X apps 2026" combined with a dateModified months in the
// past is a conjunctive rot signal: EITHER update the content (and bump the
// date field) OR drop the year from the copy. This check makes the pattern
// visible in CI before rankings drop.
//
// Usage
// -----
//   node check_year_staleness.mjs --root=content/en/pages
//   node check_year_staleness.mjs --root=content/en/pages \
//     --out=./seo-reports/year-staleness-report.csv \
//     --date-field=dateModified --max-age-days=90 \
//     --allow-list=path/one.json,path/two.json
//
// Exit codes
// ----------
//   0  no findings (clean)
//   1  findings exist (CI fails)
//   2  script error (missing --root, unreadable root, write failure, ...)
//
// Allow-list semantics (layered)
// ------------------------------
// A file is exempt from the check if any of:
//   - Its path is in the explicit `--allow-list=` arg (comma-separated,
//     relative to the CWD or to the content root).
//   - Its file name contains the substring `copyright` (case-insensitive).
//   - Any string value in the JSON contains the literal text `Copyright`
//     (case-sensitive — matches typical "(c) 2026 Copyright Notice" footers).
// The third rule lets footer JSON keep `Copyright 2026` without flagging.
//
// Output
// ------
// CSV with columns:
//   file_path, year_in_string, year_string_path, date_field_value,
//   days_since_modified
// Written to --out (default ./seo-reports/year-staleness-report.csv). The
// file is also created when there are zero findings — header only — so a
// downstream workflow can always read it.
// =============================================================================

import { readdirSync, readFileSync, statSync, writeFileSync, mkdirSync } from 'node:fs';
import { dirname, join, relative, resolve, sep } from 'node:path';

// -----------------------------------------------------------------------------
// Constants
// -----------------------------------------------------------------------------

const CWD = process.cwd();
const NOW = new Date();
const CURRENT_YEAR = NOW.getUTCFullYear();
const PREV_YEAR = CURRENT_YEAR - 1;
const TARGET_YEARS = new Set([String(CURRENT_YEAR), String(PREV_YEAR)]);

// Match a 4-digit year that is NOT immediately surrounded by other digits, so
// "version 12026" doesn't get flagged but "best apps 2026" does.
const YEAR_TOKEN_RE = /(?<![0-9])(20\d{2})(?![0-9])/g;

// Date-ish field suffixes that legitimately contain years and must never be
// flagged. The configured --date-field is added to this list at runtime.
const DATE_FIELD_SUFFIXES = [
  'datemodified',
  'datepublished',
  'datecreated',
  'foundingdate',
  'startdate',
  'enddate',
];

// -----------------------------------------------------------------------------
// CLI args
// -----------------------------------------------------------------------------

function parseArgs(argv) {
  const out = {
    root: null,
    outPath: './seo-reports/year-staleness-report.csv',
    dateField: 'dateModified',
    maxAgeDays: 90,
    allowList: [],
  };
  for (const arg of argv.slice(2)) {
    if (arg.startsWith('--root=')) {
      out.root = arg.slice('--root='.length);
    } else if (arg.startsWith('--out=')) {
      out.outPath = arg.slice('--out='.length);
    } else if (arg.startsWith('--date-field=')) {
      out.dateField = arg.slice('--date-field='.length);
    } else if (arg.startsWith('--max-age-days=')) {
      out.maxAgeDays = Number.parseInt(arg.slice('--max-age-days='.length), 10);
    } else if (arg.startsWith('--allow-list=')) {
      out.allowList = arg
        .slice('--allow-list='.length)
        .split(',')
        .map((s) => s.trim())
        .filter(Boolean);
    } else if (arg === '--help' || arg === '-h') {
      console.log(
        'Usage: node check_year_staleness.mjs --root=DIR [--out=PATH.csv] ' +
          '[--date-field=dateModified] [--max-age-days=90] ' +
          '[--allow-list=path1,path2]',
      );
      process.exit(0);
    }
  }
  return out;
}

// -----------------------------------------------------------------------------
// FS walk
// -----------------------------------------------------------------------------

function walkJsonFiles(root) {
  const acc = [];
  function recur(dir) {
    let entries;
    try {
      entries = readdirSync(dir, { withFileTypes: true });
    } catch {
      return;
    }
    for (const ent of entries) {
      const full = join(dir, ent.name);
      if (ent.isDirectory()) {
        recur(full);
      } else if (ent.isFile() && ent.name.endsWith('.json')) {
        acc.push(full);
      }
    }
  }
  recur(root);
  return acc.sort();
}

// -----------------------------------------------------------------------------
// JSON traversal: yield every string leaf with its dotted path
// -----------------------------------------------------------------------------

function* walkStrings(node, path = []) {
  if (node === null || node === undefined) return;
  if (typeof node === 'string') {
    yield { path: path.join('.'), value: node };
    return;
  }
  if (Array.isArray(node)) {
    for (let i = 0; i < node.length; i++) {
      yield* walkStrings(node[i], [...path, String(i)]);
    }
    return;
  }
  if (typeof node === 'object') {
    for (const [k, v] of Object.entries(node)) {
      yield* walkStrings(v, [...path, k]);
    }
  }
}

// -----------------------------------------------------------------------------
// Find the date field anywhere in the JSON. We accept either a top-level
// field or any nested one (e.g. `seo.schemas.article.dateModified`).
// If multiple exist, use the MOST RECENT one — being permissive errs toward
// fewer false positives.
// -----------------------------------------------------------------------------

function findMostRecentDateField(json, dateField) {
  let best = null;
  for (const { path, value } of walkStrings(json)) {
    if (!path.endsWith(dateField)) continue;
    if (typeof value !== 'string') continue;
    const t = Date.parse(value);
    if (Number.isNaN(t)) continue;
    if (best === null || t > best.timestamp) {
      best = { timestamp: t, raw: value, path };
    }
  }
  return best;
}

function daysSince(timestampMs) {
  const diffMs = NOW.getTime() - timestampMs;
  return Math.floor(diffMs / (1000 * 60 * 60 * 24));
}

// -----------------------------------------------------------------------------
// Allow-list logic
// -----------------------------------------------------------------------------

function isAllowedByPath(filePath, contentRoot, allowList) {
  if (allowList.length === 0) return false;
  const relFromCwd = relative(CWD, filePath);
  const relFromRoot = relative(contentRoot, filePath);
  for (const entry of allowList) {
    if (entry === relFromCwd || entry === relFromRoot) return true;
    // Allow OS path-separator variation.
    if (entry.replace(/\\/g, '/') === relFromCwd.replace(/\\/g, '/')) return true;
    if (entry.replace(/\\/g, '/') === relFromRoot.replace(/\\/g, '/')) return true;
  }
  return false;
}

function isAllowedByDefault(filePath, json) {
  // Rule 1: file name contains "copyright"
  const baseName = filePath.split(sep).pop() ?? '';
  if (baseName.toLowerCase().includes('copyright')) return true;

  // Rule 2: any string contains the literal "Copyright"
  for (const { value } of walkStrings(json)) {
    if (value.includes('Copyright')) return true;
  }
  return false;
}

// -----------------------------------------------------------------------------
// Per-file check
// -----------------------------------------------------------------------------

function checkFile(filePath, opts) {
  const { contentRoot, allowList, dateField, maxAgeDays } = opts;
  const findings = [];
  let raw;
  try {
    raw = readFileSync(filePath, 'utf-8');
  } catch (err) {
    return { findings, parseError: `read failed: ${err.message}` };
  }

  let json;
  try {
    json = JSON.parse(raw);
  } catch (err) {
    return { findings, parseError: `JSON parse failed: ${err.message}` };
  }

  if (isAllowedByPath(filePath, contentRoot, allowList) || isAllowedByDefault(filePath, json)) {
    return { findings, parseError: null, allowed: true };
  }

  const dateMod = findMostRecentDateField(json, dateField);
  if (!dateMod) {
    // No date field at all — can't classify staleness, so skip silently.
    // (Files without the date field rely on out-of-band freshness signals;
    // that is a separate concern.)
    return { findings, parseError: null };
  }

  const days = daysSince(dateMod.timestamp);
  if (days <= maxAgeDays) {
    return { findings, parseError: null };
  }

  // The date field is stale — scan strings for year tokens. Both conditions
  // (year token present AND stale date) must hold: the check is conjunctive.
  const suppressSuffixes = [...DATE_FIELD_SUFFIXES, dateField.toLowerCase()];
  for (const { path, value } of walkStrings(json)) {
    // Skip the date-field value itself and any date-ish fields — those
    // legitimately contain years.
    const lowerPath = path.toLowerCase();
    if (suppressSuffixes.some((sfx) => lowerPath.endsWith(sfx))) {
      continue;
    }

    // Reset regex state per value (global flag is stateful).
    YEAR_TOKEN_RE.lastIndex = 0;
    let match;
    const yearsInString = new Set();
    while ((match = YEAR_TOKEN_RE.exec(value)) !== null) {
      if (TARGET_YEARS.has(match[1])) {
        yearsInString.add(match[1]);
      }
    }
    for (const y of yearsInString) {
      findings.push({
        file_path: relative(CWD, filePath),
        year_in_string: y,
        year_string_path: path,
        date_field_value: dateMod.raw,
        days_since_modified: days,
      });
    }
  }

  return { findings, parseError: null };
}

// -----------------------------------------------------------------------------
// CSV emit
// -----------------------------------------------------------------------------

function csvEscape(s) {
  const str = String(s);
  if (/[",\n]/.test(str)) {
    return `"${str.replace(/"/g, '""')}"`;
  }
  return str;
}

function rowsToCsv(findings) {
  const header =
    'file_path,year_in_string,year_string_path,date_field_value,days_since_modified';
  const lines = [header];
  for (const f of findings) {
    lines.push(
      [
        csvEscape(f.file_path),
        csvEscape(f.year_in_string),
        csvEscape(f.year_string_path),
        csvEscape(f.date_field_value),
        csvEscape(f.days_since_modified),
      ].join(','),
    );
  }
  return lines.join('\n') + '\n';
}

// -----------------------------------------------------------------------------
// Main
// -----------------------------------------------------------------------------

function main() {
  const { root, outPath, dateField, maxAgeDays, allowList } = parseArgs(process.argv);

  if (!root) {
    console.error('[year-staleness] ERROR: --root=<content-dir> is required.');
    process.exit(2);
  }
  if (!Number.isFinite(maxAgeDays) || maxAgeDays < 0) {
    console.error('[year-staleness] ERROR: --max-age-days must be a non-negative integer.');
    process.exit(2);
  }

  const contentRoot = resolve(CWD, root);
  let rootStat;
  try {
    rootStat = statSync(contentRoot);
  } catch {
    console.error(`[year-staleness] content root not found: ${contentRoot}`);
    process.exit(2);
  }
  if (!rootStat.isDirectory()) {
    console.error(`[year-staleness] content root is not a directory: ${contentRoot}`);
    process.exit(2);
  }

  const files = walkJsonFiles(contentRoot);
  const allFindings = [];

  for (const f of files) {
    const result = checkFile(f, { contentRoot, allowList, dateField, maxAgeDays });
    if (result.parseError) {
      console.warn(
        `[year-staleness] WARN: ${relative(CWD, f)} — ${result.parseError}`,
      );
      // Parse warnings are soft skips, not exit-2 errors: one malformed file
      // should not hide the report for the rest of the tree.
      continue;
    }
    for (const finding of result.findings) {
      allFindings.push(finding);
    }
  }

  const csv = rowsToCsv(allFindings);

  const outAbs = resolve(CWD, outPath);
  try {
    mkdirSync(dirname(outAbs), { recursive: true });
    writeFileSync(outAbs, csv, 'utf-8');
    console.error(
      `[year-staleness] wrote report: ${relative(CWD, outAbs)} (${allFindings.length} finding(s))`,
    );
  } catch (err) {
    console.error(`[year-staleness] failed to write ${outAbs}: ${err.message}`);
    process.exit(2);
  }

  if (allFindings.length > 0) {
    console.error(
      `[year-staleness] FAIL: ${allFindings.length} finding(s). See ${outPath}. ` +
        `Either bump ${dateField} (after a real content update) or drop the ` +
        'year from the copy (evergreen).',
    );
    process.exit(1);
  }
  console.error('[year-staleness] OK: no stale year-stamped content found.');
  process.exit(0);
}

main();
