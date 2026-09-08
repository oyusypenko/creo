# Platform audit — reading config facts

`audit-platform.sh` and `audit-schema.sh` capture CONTEXT: facts about the
server process, the database configuration and the schema. They are captured
once per label, extend the picture, and explain scenario numbers — they are
never before/after evidence on their own. A config change is proven by
re-running a scenario and diffing its plan or latency.

## Backend process

| Fact | Why it matters | Where the automated probe looks |
|---|---|---|
| Handler style (sync vs async) | sync handlers block a threadpool worker (AnyIO default 40) during DB I/O; async handlers with a sync driver block the event loop | fastapi: `@router.get` + following `def`/`async def` |
| Workers x pool | `workers x (pool_size + max_overflow)` must stay below `max_connections`; too few connections show as pool-timeout tails under concurrency | start scripts, Dockerfile CMD, `create_engine(...)` args |
| Out-of-pool connections | a `/health` that opens `engine.connect()` and never closes leaks until GC | `engine.connect()` sites without `with` |
| Middleware | absent compression / timing middleware means the edge must do it (or nobody does) | `add_middleware`, `compression()` |
| Serialization | stdlib json is measurable at 100s of KB per response; orjson/ORJSONResponse is a drop-in | imports, `pyproject.toml`, `package.json` |
| Statement reuse | f-string-assembled SQL yields a distinct statement per filter combination — no prepared-statement / plan cache reuse, and `pg_stat_statements` fragments | `f"""` / template-literal SQL sites |

Stacks without an automated probe (`PERF_BACKEND_KIND=other`): record the
same six facts by hand in the platform metrics file under `| Fact | Value |`.

## PostgreSQL settings

| Setting | Read it against |
|---|---|
| `work_mem` | any `Sort Method: external merge Disk` line in a scenario plan |
| `shared_buffers` | the hot table's total size: when the table is larger than the cache, unbounded scans churn it and inflate the next scenario |
| `effective_cache_size`, `random_page_cost` | whether the planner will pick a new index at all (4.0 is the spinning-disk default; SSDs want ~1.1) |
| `max_connections` | worker x pool arithmetic above |
| `jit` | JIT overhead in complex plans (visible as `JIT:` blocks) |
| `max_parallel_workers_per_gather` | ceiling for parallel aggregates |
| `autovacuum_analyze_scale_factor` | analyze trigger threshold; with `last_autoanalyze = never` the planner runs on empty statistics — a finding in itself, but do NOT run `ANALYZE` mid-audit |

Container limits (`Memory`, `NanoCpus`; 0 = unlimited) make timings
interpretable on another machine.

## Schema audit

Per table: heap / TOAST / indexes / total, row count, stats state. Per
column: type, average width, null fraction, `n_distinct`, top-value skew
(> 50% flagged), covering indexes, read-path usage (from
`column-usage.tsv`). Per index: size, `idx_scan`, definition; `UNUSED`
marks `idx_scan = 0` in the current counter window, not a dead index.

What to look for:

- A large GIN over the whole document that no predicate can use (an
  `ILIKE '%x%'` over `doc::text` never touches it).
- Only an ASC btree on the default sort column when the app orders
  `DESC NULLS LAST`.
- Filter columns with extreme skew: a broad filter equals the unfiltered
  page; the WHERE is not the bottleneck, the payload and sort are.
- Row estimates 100x off on planner-opaque expressions (SubPlans over
  jsonb): the planner cannot pick a good join order without a stored
  expression it can gather statistics on.
- Geometry shape (PostGIS): count, average / max vertices, max size per
  geometry type. A "complex polygon" premise is checked here before any
  simplification work; a corpus of points needs clustering, not
  `ST_Simplify`.

## Hypothetical indexes (hypopg)

`hypopg-candidates.tsv` lists index ideas; the schema audit runs plain
`EXPLAIN` of the real runner section with the candidate in place and
reports `USED by planner (cost=...)` or `NOT used`. USED means the planner
would pick it at current statistics and cost settings — the proof is still
a scenario re-capture after creating the real index. Remove a candidate line
once the real index exists (the verdict becomes redundant and reads as a
regression).

## Observability enablement

`observability-setup.sh` sets `shared_preload_libraries = pg_stat_statements,
auto_explain` via `ALTER SYSTEM` (separate SQL values — one quoted `a,b`
string breaks the boot), restarts postgres, then the API container (stale
pooled connections without `pool_pre_ping`). It is an environment change:
log it in the extension doc and validate with a cheap scenario re-capture
under a throwaway label; DB medians must stay within noise of the baseline.
`--with-hypopg` apt-installs the package inside the container (lost on
container recreation). `workload-post.sh --teardown` reverts everything.
