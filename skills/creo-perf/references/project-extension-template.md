# Project extension — `creo-perf-{project_id}.md`

Written by `/creo perf init`, kept current by every `/creo perf optimize`
iteration. Lives at `.claude/skills/creo-perf/creo-perf-{project_id}.md`
next to `perf.config.sh` (its machine-readable twin). The skill and the
auditor agent load it before any work; it must answer, without reading the
repo again: what stack, which targets, which scenarios, where the hot path
is, what never to do, what changed in the environment, what has been fixed.

## Required sections

### Stack
Table: layer -> what -> where. Database engine and version with extensions;
backend framework, ORM, worker model; edge proxy and its config file;
frontend framework, bundler, data layer, the hot page's component files.

### Targets
Table mirroring `perf.config.sh`: API direct, API via proxy, frontend, DB
access command. State explicitly which port bypasses the proxy and which
target produces "stable" numbers vs iteration-only numbers.

### Scenarios
Table: id -> scenario -> primary endpoint -> handler `file:line` -> SQL
runners -> FE key. Plus the ordering rules `audit-all` must respect and why
(which scenario churns the cache).

### Hot path map
`file:line` for: the handlers, the query/filter builder, schema and index
DDL, the frontend page and its data-layer config, the proxy config. Update
when a fix moves code.

### Hazards
Files never to open (size), commands never to run (`down -v`, `ANALYZE`,
test suites that need unavailable env), port collisions, broken scripts,
framework rules (React Compiler: no hand memo), style authority.

### Environment log
Date -> change -> validated by. Observability enablement, container
restarts, extension installs, seed changes.

### Findings ledger
One row per finding in commit order: # -> scenario -> layer -> bottleneck ->
fix -> before -> after -> commit. Numbers from the dashboard.

## Optional sections

- **Layer notes** — per-layer observations that are not findings yet
  (config values, unused indexes, "identified, not prioritized").
- **Manual measurements** — browser-layer numbers taken by hand with the
  exact DevTools steps.
- **Open questions** for the user (production proxy differences,
  credentials, which page the complaint is about).

## Machine twin — `perf.config.sh`

Every target in the doc has a variable; every variable in the config has a
sentence in the doc. When they disagree, the config is what ran — fix the
doc. `perf preflight` checks the config; the doc is checked by reading.
