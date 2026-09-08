#!/usr/bin/env bash
set -euo pipefail

# workload-post.sh — close a DB workload window.
# 1. Snapshots it into results/<label>/db-workload/: ranked hot queries
#    (pg_stat_statements), harvested auto_explain plans (postgres log since the
#    mark), pgBadger HTML if a pgbadger binary exists on the host.
# 2. Resets counters and removes the mark file.
# 3. --teardown reverts observability to stock (drops extensions, RESETs the
#    preload + auto_explain settings, restarts postgres + API container).
#
# Rows are keyed Q[<4-hex>] (hash of the normalized query) so rankings stay
# comparable across labels. The dashboard does not render this scenario
# (a fixed query gets a new hash); read the metrics file directly.
#
# Usage: workload-post.sh <label> [--force] [--teardown]

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck disable=SC1091
source "$DIR/common/lib-harness.sh"
db_enabled || { echo "workload window needs PERF_DB_KIND=postgres" >&2; exit 2; }
need_label "$@"
TEARDOWN=0
for a in "${EXTRA_ARGS[@]:-}"; do [[ "$a" == "--teardown" ]] && TEARDOWN=1; done
MARKFILE="$RESULTS/.workload-mark"
[[ -f "$MARKFILE" ]] || { echo "FAIL: no open window — run workload-pre.sh first" >&2; exit 1; }
pg_scalar "SELECT 1 FROM pg_extension WHERE extname='pg_stat_statements';" | grep -q 1 \
  || { echo "FAIL: pg_stat_statements not installed — run workload-pre.sh" >&2; exit 1; }
claim_out db-workload
MARK=$(cat "$MARKFILE")
stamp

echo "-- pg_stat_statements ranking"
NOISE="pg_stat_statements_reset|pg_extension|pg_stat_user|information_schema|pg_settings|pg_class|pg_attribute|hypopg"
PSQL -c "
  SELECT round(total_exec_time)::bigint AS total_ms, calls, round(mean_exec_time::numeric, 2) AS mean_ms, rows,
         round(100.0*shared_blks_hit/nullif(shared_blks_hit+shared_blks_read,0), 1) AS hit_pct,
         temp_blks_written AS temp_blks,
         regexp_replace(left(query, 400), E'[\\n\\r\\t ]+', ' ', 'g') AS query
  FROM pg_stat_statements WHERE query !~* '$NOISE'
  ORDER BY total_exec_time DESC LIMIT 15;" </dev/null > "$OUT/top-queries.txt"
PSQL -t -A -F $'\t' -c "
  SELECT left(md5(regexp_replace(left(query, 400), E'[\\n\\r\\t ]+', ' ', 'g')), 4),
         round(total_exec_time)::bigint, calls, round(mean_exec_time::numeric,2), rows,
         coalesce(round(100.0*shared_blks_hit/nullif(shared_blks_hit+shared_blks_read,0),1), 100),
         temp_blks_written, regexp_replace(left(query, 160), E'[\\n\\r\\t ]+', ' ', 'g')
  FROM pg_stat_statements WHERE query !~* '$NOISE'
  ORDER BY total_exec_time DESC LIMIT 12;" </dev/null > "$OUT/top-queries.tsv"
TRACKED=$(pg_scalar "SELECT count(*) FROM pg_stat_statements;")
TOTAL_MS=$(pg_scalar "SELECT round(sum(total_exec_time))::bigint FROM pg_stat_statements;")

echo "-- auto_explain plan harvest (postgres log since $MARK)"
db_container_logs_since "$MARK" \
  | awk '/duration: .* plan:/{inplan=1} inplan{print} /^[0-9]{4}-[0-9]{2}-[0-9]{2}.*(LOG|ERROR|STATEMENT|DETAIL):/ && !/plan:/{inplan=0}' \
  > "$OUT/auto-explain-plans.txt" || true
NPLANS=$(grep -c "plan:" "$OUT/auto-explain-plans.txt" 2>/dev/null || true); NPLANS=${NPLANS:-0}

BADGER="not installed (optional: apt install pgbadger)"
if command -v pgbadger >/dev/null && [[ -n "$PERF_DB_CONTAINER" ]]; then
  db_container_logs_since "$MARK" > "$OUT/pg.log" || true
  pgbadger -q -f stderr "$OUT/pg.log" -o "$OUT/pgbadger.html" 2>/dev/null && BADGER="pgbadger.html generated" || BADGER="pgbadger run failed (see pg.log)"
fi

MD="$OUT/db-workload-metrics.md"
{
  echo "## db-workload metrics — pg_stat_statements ranking — label: $LABEL"
  echo
  echo "Captured $STAMP · HEAD $GIT_HEAD · window since ${MARK}Z · env: observability enabled"
  echo
  echo "| Metric | Value |"
  echo "|---|---|"
  echo "| statements tracked / total DB time in window | $TRACKED / ${TOTAL_MS} ms |"
  echo "| auto_explain plans captured | $NPLANS (auto-explain-plans.txt) |"
  echo "| pgBadger | $BADGER |"
  rank=0
  while IFS=$'\t' read -r h total calls mean rows hit temp q; do
    rank=$((rank+1)); q="${q//|/¦}"
    echo "| Q[${h}] · ${q} | #${rank} · ${total} ms total · ${calls} calls · ${mean} ms mean · ${rows} rows · hit ${hit}%$( [[ "${temp:-0}" != "0" ]] && echo " · TEMP ${temp} blks" ) |"
  done < "$OUT/top-queries.tsv"
} > "$MD"

echo; cat "$MD"; echo; echo "== written: $MD =="

echo "-- cleanup: reset counters, close window"
pg_scalar "SELECT pg_stat_statements_reset();" >/dev/null
rm -f "$MARKFILE"

if [[ $TEARDOWN -eq 1 ]]; then
  echo "-- teardown: reverting observability to stock environment"
  pg_scalar "DROP EXTENSION IF EXISTS hypopg;" >/dev/null || true
  pg_scalar "DROP EXTENSION IF EXISTS pg_stat_statements;" >/dev/null || true
  pg_scalar "ALTER SYSTEM RESET shared_preload_libraries;" >/dev/null
  for s in log_min_duration log_analyze log_buffers log_nested_statements log_format; do
    pg_scalar "ALTER SYSTEM RESET auto_explain.$s;" >/dev/null || true
  done
  db_restart
  echo "   environment reverted (preload empty, extensions dropped)"
fi
