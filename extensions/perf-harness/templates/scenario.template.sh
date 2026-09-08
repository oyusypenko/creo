# Scenario definition for the creo-perf harness — sourced by audit-scenario.sh.
# One file per user-facing scenario: .claude/skills/creo-perf/scenarios/<id>.sh
# Everything the harness needs is declared here; the runner stays generic.
# Helpers available inside functions: $PERF_API, $PERF_PROXY, $OUT, $RAW, $SQLDIR,
# run_sql, exec_median, plan_fact, result_of, pg_scalar, pg_idx_info, pg_idx_named,
# http_loop, emit. See references/scenario-spec.md in the creo-perf skill.

SCENARIO_ID="__ID__"
SCENARIO_DESC="__DESC__"          # one line, human: "user opens the list page (page 1, 100 rows)"

# Request set, "<drive-count> <url>" per line. The FIRST entry is the primary
# URL: it gets direct + proxy loops, on-wire bytes, gzip and ETag replay.
# Later entries get a shorter direct loop. workload-drive.sh replays all of
# them <count> times. Build URLs from $PERF_API so the proxy rewrite works.
SCENARIO_URLS=(
  "3 ${PERF_API}/items?page=0&page_size=100"
)

# SQL runner names (files sql/<name>.sql produced by sql-runners.py from
# sql-src/<name>/<label>.sql in compile mode, or by sql-calls.py in record
# mode; or hand-written under .claude/skills/creo-perf/sql/). Each section
# inside a runner is EXPLAIN'd 3× and reported as "DB · <name> · <label>".
SCENARIO_SQL=()
# e.g. SCENARIO_SQL=(__ID___default)

# Key into fe-interactions.json (browser interaction probe). Empty = skip.
SCENARIO_FE=""

# Optional: override which EXPLAIN lines are quoted in the plan-fact cell.
# SCENARIO_PLAN_REGEX='Seq Scan|Index.*Scan|Sort Method|Rows Removed'

# Optional: mechanism probes — run after the runners, before HTTP. Use them to
# prove a cause at its own layer (a rewritten predicate, a hypothetical index,
# a NULLS ordering check). Write extra runner files into $SQLDIR and run_sql them.
# scenario_probes() {
#   cat > "$SQLDIR/${SCENARIO_ID}_probe.sql" <<'EOF'
# \pset pager off
# \echo === __ID___probe/plain_desc run 1 ===
# EXPLAIN (ANALYZE, BUFFERS) SELECT id FROM items ORDER BY created_at DESC LIMIT 100;
# \echo === __ID___probe/plain_desc run 2 ===
# EXPLAIN (ANALYZE, BUFFERS) SELECT id FROM items ORDER BY created_at DESC LIMIT 100;
# \echo === __ID___probe/plain_desc run 3 ===
# EXPLAIN (ANALYZE, BUFFERS) SELECT id FROM items ORDER BY created_at DESC LIMIT 100;
# \echo === __ID___probe/plain_desc RESULT (correctness) ===
# SELECT count(*) FROM items WHERE created_at IS NULL;
# EOF
#   run_sql "$SQLDIR/${SCENARIO_ID}_probe.sql"
#   PROBE_MS=$(exec_median __ID___probe/plain_desc)
#   PROBE_PLAN=$(plan_fact __ID___probe/plain_desc 'Index Scan|Seq Scan')
# }

# Optional: extra report rows (index facts, payload composition, variant notes).
# Row grammar: "| <Layer> | <metric name — stable across labels> | <value> |"
# Never embed run-specific values in the metric name; the dashboard keys on it.
# scenario_report() {
#   SORT_IDX=$(pg_idx_info items "pg_get_indexdef(s.indexrelid) ~ 'USING btree \(created_at'")
#   emit "| Index | created_at (sort column) | $SORT_IDX |"
#   emit "| Index probe | plain DESC | ${PROBE_MS:-n/a} ms ($PROBE_PLAN) |"
# }
