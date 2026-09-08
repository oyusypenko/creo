#!/usr/bin/env bash
set -uo pipefail

# preflight.sh — verify a project is ready to capture: config present, tools
# installed, targets reachable, scenarios declared. Exit 1 on any hard failure.
# Usage: preflight.sh

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck disable=SC1091
source "$DIR/common/lib-harness.sh"
ok=0; bad=0
pass() { echo "  ok   $*"; ok=$((ok+1)); }
warn() { echo "  warn $*"; }
failc() { echo "  FAIL $*"; bad=$((bad+1)); }

echo "creo-perf preflight — project $PROJECT_ROOT"
echo "config: $CONFIG (project_id=${PERF_PROJECT_ID:-?})"
echo
echo "tools"
for t in curl gzip python3 node awk; do command -v "$t" >/dev/null && pass "$t" || failc "$t missing"; done
CHROME="${CHROME_PATH:-$(command -v google-chrome || command -v google-chrome-stable || command -v chromium || command -v chromium-browser || true)}"
[[ -n "$CHROME" ]] && pass "chrome for Lighthouse: $CHROME" || warn "no Chrome binary — audit-fe.sh Lighthouse runs will fail (set CHROME_PATH)"
command -v docker >/dev/null && pass "docker" || warn "docker missing — container restarts/log harvest unavailable"
if [[ -n "${PERF_APP_DIR:-}" ]]; then
  (cd "$PERF_APP_DIR" 2>/dev/null && node -e 'require("playwright")' 2>/dev/null) && pass "playwright resolvable from PERF_APP_DIR" || warn "playwright not resolvable from PERF_APP_DIR — FE interaction rows will read 'unavailable' (npm i -D playwright && npx playwright install chromium)"
fi

echo; echo "targets"
for u in "${PERF_PREFLIGHT_URLS[@]:-}"; do
  [[ -n "$u" ]] || continue
  curl -sf -o /dev/null --max-time 5 "$u" && pass "$u" || failc "$u unreachable"
done
[[ -n "$PERF_WEB" ]] && { curl -sf -o /dev/null --max-time 5 "$PERF_WEB/" && pass "web $PERF_WEB" || failc "web $PERF_WEB unreachable"; }
if db_enabled; then
  pg_scalar "SELECT version();" 2>/dev/null | grep -q PostgreSQL && pass "postgres via PERF_PSQL_CMD" || failc "PERF_PSQL_CMD cannot reach postgres"
  for t in "${PERF_DB_TABLES[@]:-}"; do
    [[ -n "$t" ]] || continue
    [[ "$(pg_scalar "SELECT count(*) FROM pg_class WHERE relname='$t';" 2>/dev/null)" == "1" ]] && pass "table $t" || failc "table $t not found"
  done
  for e in pg_stat_statements hypopg pg_trgm; do
    pg_scalar "SELECT 1 FROM pg_extension WHERE extname='$e';" 2>/dev/null | grep -q 1 && pass "extension $e" || warn "extension $e absent (observability-setup.sh enables pg_stat_statements/hypopg)"
  done
  [[ -n "$PERF_DB_CONTAINER" ]] && { docker exec "$PERF_DB_CONTAINER" true 2>/dev/null && pass "container $PERF_DB_CONTAINER" || failc "container $PERF_DB_CONTAINER not running"; }
else
  warn "PERF_DB_KIND=$PERF_DB_KIND — DB layers (EXPLAIN, schema, workload) disabled"
fi

echo; echo "scenarios"
mapfile -t IDS < <("$DIR/audit-scenario.sh" --list)
[[ ${#IDS[@]} -gt 0 ]] && pass "${#IDS[@]} scenario file(s): ${IDS[*]}" || failc "no scenario files in $EXT_DIR/scenarios/"
for id in "${IDS[@]}"; do
  n=$("$DIR/audit-scenario.sh" "$id" --urls 2>/dev/null | grep -c . || true)
  [[ "$n" -gt 0 ]] && pass "$id: $n url(s)" || warn "$id declares no URLs"
done
case "${PERF_SQL_MODE:-none}" in
  compile) [[ -d "$EXT_DIR/sql-src" ]] && pass "sql-src/ present (compile mode)" || warn "PERF_SQL_MODE=compile but no sql-src/ — DB sections will be empty" ;;
  record)  [[ -f "$EXT_DIR/sql-calls.py" ]] && pass "sql-calls.py present (record mode)" || failc "PERF_SQL_MODE=record but no sql-calls.py"
           [[ -x "${PERF_SQL_PYTHON:-/nonexistent}" ]] && pass "PERF_SQL_PYTHON=$PERF_SQL_PYTHON" || failc "PERF_SQL_PYTHON not executable" ;;
  none)    warn "PERF_SQL_MODE=none — no EXPLAIN sections (set compile or record)" ;;
esac
[[ -f "$EXT_DIR/fe-interactions.json" ]] && pass "fe-interactions.json present" || warn "no fe-interactions.json — FE interaction rows skipped"
[[ -f "$EXT_DIR/dashboard.json" ]] && pass "dashboard.json present" || warn "no dashboard.json — default titles/order"
for h in "${PERF_HAZARDS[@]:-}"; do [[ -n "$h" ]] && echo "  hazard: $h"; done

echo; echo "$ok ok, $bad failed"
[[ $bad -eq 0 ]]
