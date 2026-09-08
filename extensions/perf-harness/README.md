# Perf Harness Extension for Creo

The executable half of the `creo-perf` skill: a deterministic, project-agnostic
performance-measurement suite. Every number a performance audit produces comes
from one of these scripts, so any before/after pair is script-to-script
comparable and fully reproducible.

## What it does

- **Scenario captures** (`audit-scenario.sh`) — per user-facing scenario:
  median-of-3 `EXPLAIN (ANALYZE, BUFFERS)` per SQL section with the decisive
  plan lines quoted, 1 cold + N warm HTTP loops with p50/p95 against the API
  directly and through the proxy, on-wire bytes vs offline gzip potential,
  `If-None-Match` replay (time-to-304, weak-ETag-through-gzip), an optional
  Playwright interaction probe, and correctness references (row counts) that
  ride along so a "win" that changed results is caught as a regression
- **Initial-load audit** (`audit-fe.sh`) — served-asset headers and bytes,
  production build sizes and code-splitting counts, bundle composition (vite),
  Lighthouse xN pinned at major 13 with median-by-LCP selection
- **Platform audit** (`audit-platform.sh`) — handler style, worker x pool
  arithmetic, middleware, serialization, statement reuse; PostgreSQL key
  settings, stats state, extensions, container limits
- **Schema audit** (`audit-schema.sh`) — per table: sizes, column width /
  null% / skew, covering indexes, read-path usage; per index: size, counters,
  definition; hypothetical-index verdicts via hypopg against the real SQL
- **Workload discovery** (`workload-*.sh`) — `pg_stat_statements` ranking of
  what is hot under whole-app traffic, harvested `auto_explain` plans
- **Dashboard** (`build-dashboard.py`) — one pivot table per scenario, columns
  = capture labels, unit-aware delta column, index-inventory churn summary;
  rebuilt automatically after every capture

## Design principles

1. **Determinism** — fixed URLs and run counts, medians not averages, pinned
   tool versions, every number labeled by environment.
2. **Immutable captures** — a label directory is written once; `--force`
   exists for non-baseline reruns only.
3. **Measure the real thing** — SQL comes from the running application code
   (record mode) or is archived verbatim next to the numbers (compile mode);
   payloads and headers are measured on the wire at the proxy boundary.
4. **Discovery vs proof** — `pg_stat_statements` ranks what is hot; scenario
   scripts prove individual findings with repeatable pairs.
5. **Project-agnostic** — every project fact (targets, tables, containers,
   scenarios, probes) lives in the project's `.claude/skills/creo-perf/`,
   scaffolded by `/creo perf init`. The scripts here never change per project.

## Requirements

- bash 4+, curl, gzip, awk, python3 (stdlib only), node 18+
- Docker when the database is containerised (restarts, log harvest, hypopg apt install)
- Chrome/Chromium for Lighthouse (`npx lighthouse@13` is fetched on demand)
- Optional: Playwright in the frontend project (`npm i -D playwright && npx playwright install chromium`) for interaction probes; `pgbadger` on the host for workload HTML
- Record-mode SQL extraction needs the backend's Python venv (SQLAlchemy / SQLModel apps)

Supported in this version: PostgreSQL (incl. PostGIS) databases; FastAPI and
Node backends for the platform probe (other stacks record facts by hand);
any frontend served as static assets (Vite gets a composition breakdown).

## Install

```bash
./extensions/perf-harness/install.sh      # -> ~/.claude/skills/creo-perf-harness/
```

Plugin installs (`/plugin install creo@creo`) ship this directory as part of
the plugin; the skill resolves it from `${CLAUDE_PLUGIN_ROOT}/extensions/perf-harness`.

## Use

```bash
# in the project repo
/creo perf init                                   # scaffold + fill .claude/skills/creo-perf/
.claude/skills/creo-perf/perf preflight
.claude/skills/creo-perf/perf audit-all before    # immutable baseline (~15-30 min)
# ... implement one fix ...
.claude/skills/creo-perf/perf audit-scenario s2 after-search-index
cat .claude/skills/creo-perf/results/dashboard.md
```

## Layout

```
perf-harness/
├── SKILL.md, README.md
├── install.sh / uninstall.sh / install.ps1 / uninstall.ps1
├── scripts/
│   ├── init-project.sh, preflight.sh, audit-all.sh
│   ├── audit-scenario.sh, audit-fe.sh, audit-platform.sh, audit-schema.sh
│   ├── observability-setup.sh, workload-pre.sh, workload-drive.sh, workload-post.sh
│   └── common/
│       ├── lib-harness.sh      bootstrap: config, PSQL, labels, immutability, dashboard
│       ├── lib-scenario.sh     measurement engine: http_loop, gzip_potential, etag_replay, EXPLAIN parsing
│       ├── build-dashboard.py  results/dashboard.md aggregator
│       ├── sql-runners.py      psql runner generation (compile | record)
│       └── fe-interactions.mjs Playwright interaction probe
└── templates/                  copied into the project by init-project.sh
    ├── perf.config.sh, dashboard.json, fe-interactions.json, sql-calls.py
    ├── scenario.template.sh, column-usage.tsv, hypopg-candidates.tsv
    ├── creo-perf-project.md, README.md, gitignore.snippet
```

## Results layout (in the project)

```
.claude/skills/creo-perf/results/
├── dashboard.md              # rows = metrics, columns = capture labels (committed)
└── <label>/                  # before/, after-index/, ... (gitignored)
    ├── fe/ platform/ schema/ s1/ ... db-workload/
    │   ├── <id>-metrics.md   # paste-ready table
    │   ├── sql/              # exact SQL this capture measured
    │   └── raw-plans.txt, http-*.log, body-*.bin, etag-*.log, fe-interactions.json ...
```

## Gotchas

- Lighthouse numbers are **lab** (headless, simulated mobile throttling) —
  never compare them to wall-clock desktop times.
- `observability-setup.sh` restarts the database — an environment change.
  Validate with a cheap scenario re-run under a throwaway label and keep it.
- An unclean postgres shutdown resets `pg_stat_*` counters; planner histograms
  persist, but usage-counter claims must be re-based.
- A config value is never evidence by itself: prove any config change by
  re-running a scenario and diffing its plan/latency.
- Never run two captures concurrently; order cache-churning scenarios last.
