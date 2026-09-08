# Layer audit checklists

Top-down triage, bottom-up proof: attribute every symptom to a layer with
that layer's profiler, and never claim a cause you did not measure at its
own layer. For each layer: what to audit, the tool, what to record, and the
fix directions that have paid off.

## 1. Database (PostgreSQL)

**Audit**: the hot query shapes extracted from the handler — default sorted
page (`ORDER BY ... DESC NULLS LAST LIMIT`), text search, each filter, any
per-request aggregate (count, ETag seed), heavy endpoints (tiles, exports).
Index coverage: which exist, which are unused, whether predicates and sorts
are sargable against them. Planner statistics state. Column skew (a "broad"
filter on a column where 99% of rows share one value is the unfiltered page
in disguise). Row-estimate vs actual on the hot scan.

**Tool**: `EXPLAIN (ANALYZE, BUFFERS)` via the scenario runners; hypopg for
index ideas without creating them; `pg_stat_statements` for whole-traffic
ranking; `auto_explain` for plans of real traffic.

**Record**: plan node types (Seq Scan vs Index/Bitmap Scan, Sort Method,
`external merge Disk`), execution time, buffers hit/read, rows removed by
filter, SubPlan loop counts, estimate/actual ratio.

**Fix directions**: `ILIKE '%x%'` over a whole-document cast is unindexable
as written -> a stable expression (`search_text(doc, ...)`) + trigram GIN;
an ASC btree scanned backwards yields NULLS FIRST and cannot serve
`DESC NULLS LAST` -> matching DESC index; per-row SubPlan selectors ->
containment (`@>`) on an expression index; duplicate count + ETag aggregates
sharing a WHERE -> one aggregate; unbounded `page=None` paths -> cap or
stream; oversized whole-document GIN nothing uses -> drop.

## 2. API shape

**Audit**: queries per request (repeated WHERE across ETag/count/data);
response columns vs what the UI reads (does the list ship full documents and
geometry the table never renders?); pagination limits and unbounded paths;
sync vs async handlers vs pool size; serialization path (stdlib json vs
orjson) when payloads are 100s of KB; f-string SQL = no plan reuse.

**Tool**: timed curl loops (harness `API (direct)` rows), payload
composition (`python3 -c` over the body: bytes per top-level key), the
platform audit's handler/pool facts, per-scenario `App-executed` rows.

**Record**: p50/p95 per endpoint, queries per request, bytes per row at each
page size the UI offers, payload composition by key.

**Fix directions**: trim the list payload to the columns the UI reads (a
detail endpoint carries the rest); merge aggregates; cache per-request
lookups that never change (classification selectors); RFC 9110 weak
comparison for `If-None-Match` so proxies that weaken ETags still 304;
`Cache-Control: private, no-cache` with a versioned ETag seed so a response-
shape change invalidates clients.

## 3. Edge / proxy

**Audit**: compression coverage for the actual response content types
(`gzip_types` vs the API's `Content-Type` — `application/geo+json` is not
`application/json`); brotli / pre-compressed static assets; `Cache-Control`
and immutable hashed assets; whether a 304 still pays the full server-side
work; proxy overhead (proxy p50 minus direct p50).

**Tool**: `curl -H 'Accept-Encoding: gzip, br'` vs identity at the proxy
port only (the dev server bypasses it); `If-None-Match` replay; the fe
audit's served-assets table.

**Record**: wire bytes with/without compression and the ratio, time-to-304
vs time-to-200, header presence/correctness, `Content-Encoding` per asset.

**Fix directions**: add the API's media types to the compressor; enable
`brotli_static` / `gzip_static` with build-time precompression; 1y immutable
on hashed assets, `no-cache` on `index.html`; proxy-cache public third-party
tiles but never authenticated responses without identity in the key.

## 4. Client data layer

**Audit**: query-client config (`staleTime`, `gcTime`, `placeholderData`,
persisters and where they serialize), refetches per interaction (typing N
characters, page change, sort change), duplicate calls on initial load
(two mounted consumers of the same query without dedup), request waterfall.

**Tool**: harness FE probe (`requests` fired per interaction, `minRows`
during refetch), Lighthouse network log duplicate-API-call row, DevTools
Network + Performance for the persister.

**Record**: refetches while typing, whether the table blanks (minRows 0) on
page/sort change, long-task ms attributable to serialization.

**Fix directions**: debounce search input; `placeholderData: keepPreviousData`
so the view holds through a refetch; sane `staleTime`; hoist shared queries;
lazy persisters off the main thread.

## 5. Rendering

**Audit**: compiler opt-outs (`'use no memo'`), per-row work in cell
renderers (validation, date formatting, tooltip instances), list
virtualization for page sizes >= 100, effect dependencies that fire per
keystroke or per mousemove, splitter/drag handlers.

**Tool**: FE probe long tasks (count, worst ms, @4x CPU), Lighthouse TBT /
bootup, React DevTools Profiler commit counts and durations at page sizes
100 and 1000, Performance panel during a 2 s drag.

**Record**: long tasks per interaction, worst task ms, commit count/duration
per page render, frame rate during drag.

**Fix directions**: virtualize the table; move per-row validation to the
server or a stored column; memo-free React 19 with the compiler on (remove
opt-outs rather than hand-adding memo); throttle drag handlers.

## 6. Browser resources / lifecycle

**Audit**: initial bundle composition (eager heavy libs behind a toggle or on
other routes: data grids, map stacks, form/schema validators, editors),
route-level code splitting, fonts (files emitted vs fetched, subsetting,
self-hosting), auth clients shipped for a stub, dead dependencies, map/WebGL
mount-unmount leaks, memory growth across repeated interactions.

**Tool**: fe audit build + composition rows, Lighthouse unused JS/CSS and
long tasks, Chrome Memory panel and WebGL context warnings for lifecycle.

**Record**: initial JS bytes raw/compressed, largest chunks by package,
dynamic-import count, fonts fetched, heap / WebGL context count after N
toggles.

**Fix directions**: `lazy()` route boundaries for editors, maps, forms, data
grids; a boot shell with an async entry script; latin-subset self-hosted
fonts; replace a full OIDC client with a local shim when auth is stubbed;
pin CDN-loaded versions to `package.json`; dispose map instances on unmount.

## Severity scale

- **Critical** — every page load, or grows super-linearly with data
- **High** — a common interaction, or a large constant cost
- **Medium** — a specific filter or interaction path
- **Low** — hygiene

Each finding: layer · symptom · mechanism (`file:line`) · evidence (numbers +
the decisive plan/trace excerpt) · fix direction · effort S/M/L.
