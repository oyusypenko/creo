# Report templates

## Metrics file (produced by the harness)

```markdown
## S2 metrics — user types in the search box (...) — label: before

Captured 2026-08-04T20:33Z · HEAD 3bc4cbd · direct :8001, proxy :80/api, psql via PERF_PSQL_CMD · HTTP p50/p95 over 10 warm runs (+1 cold) · DB = median of 3 EXPLAIN (ANALYZE, BUFFERS) runs · exact SQL archived in sql/

| Layer | Metric | Value |
|---|---|---|
| FE | interaction (typing) | typing "composite" (9 keystrokes): 2 requests fired · view BLANKS mid-refetch (min 0 rendered rows) · 4 long tasks, worst 1112 ms · median of 3/3 runs @4x CPU |
| Network (proxy) | on-wire payload | 437585 B identity (offline gzip -6: 26486 B = 16.5×) · to a browser: 437585 B identity in 1.013s (1.0×) |
| Network (proxy) | warm p50 / p95 | 1.013 s / 1.064 s (cold 1.027 s; proxy overhead ≈ 0.000 s) |
| Network (proxy) | If-None-Match → 304 | code 304, p50 0.325 s · gzip client: 304 |
| API (direct) | warm p50 / p95 | 1.019 s / 1.071 s (cold 1.040 s; HTTP 200, payload 437585 B) |
| DB | s2_search · count | 332.453 ms — Seq Scan on items (cost=... rows=3 ...) (actual time=31.7..355.2 rows=289 loops=1) · Filter: ((doc)::text ~~* '%composite%') · Rows Removed by Filter: 27244 |
| DB | s2_search · data_p100 | 358.154 ms — ... |
| DB | s2_search · per-request time | count 332.453 ms + data_p100 358.154 ms ≈ 691 ms |
| Index | text-search indexes | pg_trgm installed: f · idx_items_doc_gin (42 MB · gin (doc)) — unreachable from doc::text ILIKE |

Correctness ref: s2_search/count=289 · s2_search/data_p100=100
```

## Dashboard (auto-built)

One table per scenario; columns are labels (baseline first); the Δ column
diffs the last label against the first using the cell's headline number: the
stated `≈ total`, else the slowest EXPLAIN node's actual time, else the first
number-with-unit. Rows about index inventories and counters get no Δ. Read
Δ cells for direction and magnitude, then open the metrics files for the
plan lines that explain them.

## Finding entry (SOLUTION.md-style deliverable)

```markdown
### Finding N — <one line: what was slow and why>

- **Scenario**: S2 text search (`GET /items?filters={text}` → `search_items()` `app/route/items.py:164`)
- **Layer**: database
- **Symptom**: 1.01 s p50 per keystroke-triggered refetch; the whole table stalls while typing.
- **Mechanism**: predicate `doc::text ILIKE '%term%'` is unindexable as written — the 42 MB
  whole-document GIN can never serve a leading-wildcard match; three statements share the same
  sequential scan per request (`items.py:164`, `http_cache.py:31`).
- **Proof** (label `before`, direct :8001, warm p50 of 10, median-of-3 plans):
  ```
  Seq Scan on items (cost=0.00..6192.83 rows=3 width=12) (actual time=31.696..355.204 rows=289 loops=1)
    Filter: ((doc)::text ~~* '%composite%'::text)
    Rows Removed by Filter: 27244            -- estimate rows=3 vs actual 289
  ```
- **Fix** (commit `abc1234`): stable `search_text(doc, id, ts...)` expression + trigram GIN
  (`db/08-search-text.sql`); predicate rewritten to target it (`items.py:164`); count folded
  into the ETag aggregate (`http_cache.py:31`).
- **Before → after** (labels `before` vs `after-search-index`, same environment):

  | Metric | Before | After | Δ |
  |---|---|---|---|
  | API (direct) · warm p50 / p95 | 1.019 s / 1.071 s | 0.032 s / 0.061 s | -97% |
  | DB · per-request time | ≈ 1011 ms | ≈ 27 ms | -97% |
  | DB plan | Seq Scan, Rows Removed 27244 | Bitmap Index Scan on idx_items_search_trgm | — |
  | Correctness ref | total=289, rows=100 | total=289, rows=100 | identical |

- **Not done / follow-ups**: estimate still rows=3 (planner-opaque expression); revisit if
  the trigram scan degrades with corpus growth.
```

Rules: numbers are copied from `results/dashboard.md` cells; the plan
excerpt is the decisive 3-5 lines from `raw-plans.txt`; both labels named;
correctness stated explicitly; anything identified but not prioritized goes
under a separate "Identified, not prioritized" list.

## Commit message

```
perf(db): trigram search index for text filter — S2 p50 1.019 s -> 0.032 s

The text filter ran `doc::text ILIKE '%term%'` (items.py:164) — unindexable,
a full Seq Scan with 27,244 rows removed, executed 3x per request. Adds
search_text() + gin_trgm_ops index (08-search-text.sql), targets it from the
predicate, folds count(*) into the ETag aggregate.

Measured before/after (labels before -> after-search-index, docker :8001
direct, 10 warm runs): API p50 1.019 -> 0.032 s (-97%), DB ≈ 1011 -> 27 ms,
plan Seq Scan -> Bitmap Index Scan on idx_items_search_trgm. Correctness
refs identical (total=289, rows=100). Harness: sql-calls.py section labels
aligned to the new query shape; dashboard.md updated.
```

One concern per commit. Environment repairs (`chore(env)`) and harness-only
changes (`chore(perf-harness)`) land separately from perf commits.

## Auditor report (creo-perf-audit final message)

1. **Environment header** — stack state, git HEAD, stats state, date, mode, labels.
2. **Findings ranked by severity** — each: layer · symptom · mechanism
   (`file:line`) · evidence (numbers + decisive excerpt) · fix direction ·
   effort S/M/L.
3. **Evidence index** — the `results/<label>/...` files written.
4. **What could not be measured** and why, with the manual script if relevant.
