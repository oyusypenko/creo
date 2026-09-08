# Scenario specification

Everything project-specific the harness needs lives in
`.claude/skills/creo-perf/` (scaffolded by `/creo perf init`). The scripts
never change per project; these files do.

## perf.config.sh

Bash, sourced by every script. Key groups:

| Group | Variables | Notes |
|---|---|---|
| HTTP | `PERF_API`, `PERF_PROXY`, `PERF_WEB`, `PERF_WEB_PATH`, `PERF_API_PATTERN`, `PERF_PREFLIGHT_URLS`, `PERF_PROBE_URL` | `PERF_PROXY=""` when no edge layer; URLs in scenarios start with `$PERF_API` so the proxy rewrite works |
| DB | `PERF_DB_KIND`, `PERF_PSQL_CMD` (array), `PERF_DB_CONTAINER`, `PERF_API_CONTAINER`, `PERF_DB_TABLES`, `PERF_DB_HOT_TABLE` | `none` disables EXPLAIN/schema/workload; container empty = no restarts / log harvest |
| SQL | `PERF_SQL_MODE` (`record`/`compile`/`none`), `PERF_SQL_PYTHON` | see below |
| FE | `PERF_APP_DIR`, `PERF_SRC_DIR`, `PERF_BUILD_CMD`, `PERF_DIST_DIR`, `PERF_BUNDLER`, `PERF_LIGHTHOUSE_RUNS` | |
| Backend | `PERF_BACKEND_KIND` (`fastapi`/`node`/`other`), `PERF_BACKEND_DIR`, `PERF_ROUTES_GLOB` | platform probe |
| Order | `PERF_ALL_ORDER` | `platform schema <scenarios...> fe`; cache-churning scenarios last |
| Hazards | `PERF_HAZARDS` | echoed by preflight |

## scenarios/<id>.sh

Sourced by `audit-scenario.sh`. Ids are kebab-case (`s1`, `search`,
`tile-z2`). Declares:

```bash
SCENARIO_ID="s2"
SCENARIO_DESC="user types in the search box (term 'composite', 289 matches; page 1, 100 rows)"
SCENARIO_URLS=(                       # "<drive-count> <url>"; FIRST = primary
  "3 ${PERF_API}/items?filters=%7B%22text%22%3A%22composite%22%7D&page=0&page_size=100"
)
SCENARIO_SQL=(s2_search)              # runner names -> DB sections
SCENARIO_FE="typing"                  # key in fe-interactions.json ("" = skip)
SCENARIO_PLAN_REGEX='Seq Scan|Bitmap.*Scan|Index.*Scan|Filter:|Rows Removed'   # optional
scenario_probes() { ... }             # optional: mechanism probes after runners, before HTTP
scenario_report() { ... }             # optional: extra emit rows before finish
```

What the runner does with it:

- **primary URL**: direct loop (1 cold + N warm), proxy loop when `PERF_PROXY`
  is set, on-wire bytes vs offline gzip, `If-None-Match` replay (plus a
  gzip-client replay to catch weak-ETag breakage).
- **secondary URLs**: direct loop, min(N,5) warm — variants (page_size=1000,
  deep offset, contrast zoom). Keep expensive variants here, not primary.
- **runners**: every `=== runner/label run N ===` section is EXPLAIN'd 3x;
  rows `DB · <runner> · <label>` with the median and the plan lines matching
  the regex; a `DB · <runner> · per-request time` row sums the sections
  (`a 1.6 ms + b 8.1 ms ≈ 10 ms` — the ≈-total is what the dashboard diffs).
- **correctness**: every `RESULT (correctness)` section lands in the
  `Correctness ref:` line (hidden in the dashboard, kept in the metrics file).

### Mechanism probes

Prove a cause at its own layer inside `scenario_probes()`: a plain `DESC`
vs the app's `DESC NULLS LAST` ordering, a containment rewrite of a per-row
SubPlan, a bare count of rows a bbox selects vs rows the response carries.
Write a runner file into `$SQLDIR`, `run_sql` it, read `exec_median` /
`plan_fact` / `result_of`, and emit an `| Index probe | ... |` row in
`scenario_report()`. Helpers: `pg_scalar`, `pg_idx_info TABLE PRED`,
`pg_idx_named TABLE PRED`, `http_loop`, `emit`.

### Row grammar

`| <Layer> | <metric name> | <value> |`. The dashboard keys on
`<Layer> · <metric name>`, so names must be stable across labels — never
embed a run-specific value (a count, a hash, a date) in the name; put it in
the value. Layers used by the runner: `DB`, `API (direct)`, `Network (proxy)`
/ `Network (direct)`, `FE`; add `Index`, `Index probe`, `DB plan`, `Ruled out`
freely. Pipe characters inside values are rendered as `¦` by the helpers.

## SQL sources

Runner file format (what psql executes; generated, not hand-edited):

```
\pset pager off
\echo === s2_search/count run 1 ===
EXPLAIN (ANALYZE, BUFFERS) SELECT count(*) FROM items WHERE ...;
... run 2, run 3 ...
\echo === s2_search/count RESULT (correctness) ===
SELECT count(*) FROM items WHERE ...;
```

**compile mode** — `sql-src/<runner>/<label>.sql`, one statement per file,
binds inlined as literals. `<label>.rows.sql` marks a row-returning statement
(its correctness query becomes `SELECT count(*) FROM (...) sub`). Works for
any stack; the statement is what the handler builds for that exact URL —
copy it from server logs (`log_min_duration_statement=0`), the ORM's echo,
or the handler code. Re-verify after any query change.

**record mode** — `sql-calls.py` runs the real endpoint functions with a
recording session (SQLAlchemy / SQLModel). Drift is impossible by
construction: change the handler and the extracted SQL changes with it.
Requires the backend venv (`PERF_SQL_PYTHON`) and the app importable with
its DB connection env set. One `call(fn, ...)` per scenario, labels in
execution order.

Hand-maintained runner files can also be dropped into `sql/<runner>.sql`
(compile mode absent); the runner copies them into the capture.

## fe-interactions.json

One entry per `SCENARIO_FE` key. `path`, `ready` (selector that marks the
page loaded), optional `setup` actions, the measured `actions`, `rows`
(selector counted during the refetch — 0 means the view blanked), and
`apiPattern`. Actions: `click`, `type` (+`text`, `delay`), `fill`, `press`,
`hover`, `select`, `wait`, `waitFor`, `goto`. Global `cpuThrottle` (4),
`runs` (3), `settle` (ms after the last action). Needs Playwright resolvable
from `PERF_APP_DIR`; otherwise the FE row reads "interactive pass
unavailable" and the browser layers fall back to the manual protocol.

## dashboard.json

`order` (scenario ids), `titles`, `endpoints` (`endpoint -> handler
file:line`, shown under each table), `hidden_rows` / `no_delta` (regexes on
the metric key), `baseline_labels`. Defaults already hide correctness refs,
variants, hypothetical verdicts, and skip deltas on index rows.

## Optional inputs

- `column-usage.tsv` — `table.column<TAB>usage`: rendered in the schema audit
  so index decisions read against the read path they serve.
- `hypopg-candidates.tsv` — `name<TAB>CREATE INDEX ...<TAB>runner<TAB>label`:
  index ideas tested without creating them (needs hypopg). Remove a line once
  the real index exists.
