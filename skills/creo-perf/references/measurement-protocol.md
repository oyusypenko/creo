# Measurement protocol

The rules that make a performance number defensible. They apply whether the
harness runs or the measurement is manual.

## 1. Labels and immutability

- A **label** names a capture campaign (`before`, `after-search-index`,
  `after-gzip`). The same label across scripts = one dashboard column.
- `before` (or `baseline`) is captured before ANY code change and is never
  re-run afterwards. If a fix has already landed, there is no baseline for it:
  say so, do not fabricate a "before".
- A `results/<label>/<scenario>/` directory is written once. `--force` exists
  for non-baseline reruns only (e.g. a broken after-capture).
- Pre-fix corrections to the harness itself (a scenario that captured `n/a`)
  may be re-captured under the baseline label with `--force` as long as no
  application change has landed.

## 2. Comparability

- Only script-to-script pairs are comparable. Ad-hoc curl loops, DevTools
  eyeballing, or numbers from a different machine never enter a before/after
  table.
- Identical scenario, URLs, run counts, environment, and harness version on
  both sides. A pair that mixes docker with local, proxy with direct, or dev
  with prod build is invalid.
- Every number carries its environment: `direct :8001` vs `proxy :80`,
  `warm` vs `cold`, `prod build` vs `dev server`, `docker` vs `host`,
  Lighthouse `lab, simulated mobile`.

## 3. Statistics

- HTTP: 1 cold hit + N warm runs (default 10). Report p50 (rank ceil(N/2))
  and p95 (rank ceil(0.95 N)) of the warm runs plus the cold hit. Never an
  average. Flag a cold outlier > 5x p50 and keep p50 as representative.
- DB: median of 3 `EXPLAIN (ANALYZE, BUFFERS)` runs per statement. Quote
  the decisive 3-5 plan lines (scan type, sort method, rows removed, actual
  time of the slowest node). A plan diff is the strongest DB evidence.
- Lighthouse: N runs (default 3), the median-by-LCP run reported, all scores
  listed. Lab numbers only compare to lab numbers.
- Interaction probes: N runs under CPU throttling, the median-by-worst-long-task
  run reported.

## 4. Two channels per scenario

Each scenario measures its DB cost twice: psql EXPLAIN medians (plan shape and
node costs) and an app-executed `pg_stat_statements` window opened AFTER the
EXPLAIN phase (real HTTP traffic only; binds, pool and driver included). When
both agree the number is solid; sub-ms queries read slightly faster
app-executed because EXPLAIN ANALYZE carries instrumentation overhead.

## 5. Discovery vs proof

`pg_stat_statements` under whole-app traffic **discovers** what is hot (ranks
by total time, finds unknowns). Scenario captures **prove** individual
findings with reproducible pairs. A report cites both: the ranking that led
to the finding, the pair that proves the fix.

## 6. Correctness rides along

Every scenario carries correctness references: total counts, rows returned,
filter result counts, ETag/304 behavior. They must be identical before vs
after. A faster response that returns different rows is a regression.

## 7. Environment hygiene

- Never run two captures concurrently.
- Order matters: unbounded or huge-payload scenarios churn the buffer cache
  and inflate the next scenario's detoast-heavy scans. Run them last, or
  re-warm with one throwaway request before capturing.
- FE builds and Lighthouse load the machine: run `fe` after all loops.
- The workload window runs last with its own counter reset so the
  benchmark's own EXPLAIN traffic never pollutes the ranking.
- Never `ANALYZE` mid-audit. Record `last_analyze` / `last_autoanalyze`;
  stale statistics are themselves a finding.
- Enabling observability restarts the DB: record it in the environment log
  and validate with a cheap re-capture under a throwaway label (DB medians
  within noise of `before`).
- An unclean postgres shutdown zeroes `pg_stat_*` counters; planner
  histograms persist. Re-base any usage-counter claim.

## 8. Config is not evidence

`work_mem`, `pool_size`, `gzip_types`, `staleTime` are context facts. A change
to any of them is proven by re-running a scenario and diffing its plan or
latency (`external merge Disk -> quicksort`, `identity -> gzip 8.6x`), never
by quoting the setting.

## 9. Manual fallback (no harness, or a layer it cannot reach)

Write every number to `results/<label>/<scenario>/manual.md` with the exact
command or DevTools steps that produced it, so anyone can re-run it:

```bash
# API latency: 1 cold + 10 warm
for i in $(seq 0 10); do curl -s -o /dev/null -w '%{http_code} %{size_download} %{time_total}\n' '<URL>'; done
# wire bytes with/without compression
curl -s -o /dev/null -w 'bytes=%{size_download}\n' '<URL>'
curl -s --compressed -o /dev/null -w 'bytes=%{size_download} enc=%{content_type}\n' '<URL>'
# conditional request
ETAG=$(curl -sI '<URL>' | awk -F': ' 'tolower($1)=="etag"{print $2}' | tr -d '\r')
curl -s -o /dev/null -H "If-None-Match: $ETAG" -w '%{http_code} %{time_total}\n' '<URL>'
# plan
psql "$DSN" -c "EXPLAIN (ANALYZE, BUFFERS) <statement with binds inlined>"
```

Browser layers without Playwright: Chrome DevTools Performance panel — record
(a) typing 5 characters in search, (b) next page, (c) a 2 s drag; capture long
task count, total scripting ms, INP; React DevTools Profiler commit counts.
Export traces into the results dir. Say explicitly which numbers are manual.
