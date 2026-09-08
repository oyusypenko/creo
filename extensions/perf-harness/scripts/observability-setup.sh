#!/usr/bin/env bash
set -euo pipefail

# observability-setup.sh — one-time, idempotent enablement of DB-boundary
# observability:
#   * pg_stat_statements — normalized per-query aggregates -> ranked hot-query list
#   * auto_explain — the server logs EXPLAIN (ANALYZE, BUFFERS) for every query
#     slower than --min-duration, from real traffic (no hand-written EXPLAIN)
#   * hypopg (optional, --with-hypopg) — hypothetical indexes without creating them
#
# !! RESTARTS postgres (docker restart of PERF_DB_CONTAINER — the data volume is
# untouched) and then PERF_API_CONTAINER (its pool would otherwise hold dead
# connections). It is an ENVIRONMENT CHANGE: validate with a cheap scenario
# re-run under a throwaway label (DB medians must stay within noise) and keep
# that capture as evidence.
#
# Usage: observability-setup.sh [--min-duration 50ms] [--with-hypopg]

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck disable=SC1091
source "$DIR/common/lib-harness.sh"
db_enabled || { echo "observability needs PERF_DB_KIND=postgres" >&2; exit 2; }

MIN_DUR="50ms"; WITH_HYPOPG=0
while [[ $# -gt 0 ]]; do case "$1" in
  --min-duration) MIN_DUR="$2"; shift 2 ;;
  --with-hypopg) WITH_HYPOPG=1; shift ;;
  *) echo "usage: $0 [--min-duration 50ms] [--with-hypopg]" >&2; exit 2 ;;
esac; done

CURRENT=$(pg_scalar "SHOW shared_preload_libraries;")
echo "current shared_preload_libraries: '${CURRENT}'"
if [[ "$CURRENT" == *pg_stat_statements* && "$CURRENT" == *auto_explain* ]]; then
  echo "preload already configured — skipping restart"
else
  echo "-- ALTER SYSTEM shared_preload_libraries + restart postgres"
  # MUST be separate SQL values — one 'a,b' string is quoted into ONE library
  # name in postgresql.auto.conf and postgres refuses to boot.
  pg_scalar "ALTER SYSTEM SET shared_preload_libraries = 'pg_stat_statements', 'auto_explain';" >/dev/null
  db_restart
fi

echo "-- pg_stat_statements extension + auto_explain settings"
pg_scalar "CREATE EXTENSION IF NOT EXISTS pg_stat_statements;" >/dev/null
pg_scalar "ALTER SYSTEM SET auto_explain.log_min_duration = '$MIN_DUR';" >/dev/null
pg_scalar "ALTER SYSTEM SET auto_explain.log_analyze = on;" >/dev/null
pg_scalar "ALTER SYSTEM SET auto_explain.log_buffers = on;" >/dev/null
pg_scalar "ALTER SYSTEM SET auto_explain.log_nested_statements = on;" >/dev/null
pg_scalar "ALTER SYSTEM SET auto_explain.log_format = 'text';" >/dev/null
pg_scalar "SELECT pg_reload_conf();" >/dev/null

if [[ $WITH_HYPOPG -eq 1 ]]; then
  echo "-- hypopg"
  if pg_scalar "CREATE EXTENSION IF NOT EXISTS hypopg;" >/dev/null 2>&1; then
    echo "   hypopg extension created"
  elif [[ -n "$PERF_DB_CONTAINER" ]]; then
    PGMAJ=$(pg_scalar "SHOW server_version;" | cut -d. -f1)
    if docker exec -u root "$PERF_DB_CONTAINER" sh -c "apt-get update -qq && apt-get install -yqq postgresql-$PGMAJ-hypopg" >/dev/null 2>&1; then
      pg_scalar "CREATE EXTENSION IF NOT EXISTS hypopg;" >/dev/null && echo "   hypopg installed + extension created"
      echo "   NOTE: the apt layer is lost if the container is recreated — re-run with --with-hypopg then."
    else
      echo "   WARN: hypopg install failed (offline or no package) — hypothetical-index checks stay unavailable" >&2
    fi
  else
    echo "   WARN: hypopg not available and no container to install into" >&2
  fi
fi

echo "-- verification"
pg_scalar "SELECT 'pg_stat_statements rows: ' || count(*) FROM pg_stat_statements;"
pg_scalar "SELECT 'auto_explain.log_min_duration = ' || current_setting('auto_explain.log_min_duration');"
pg_scalar "SELECT 'preload = ' || current_setting('shared_preload_libraries');"
echo
echo "DONE. Next: overhead spot-check — audit-scenario.sh <cheap-id> obs-check --runs 5 (DB medians within noise of the baseline), then workload-pre.sh."
