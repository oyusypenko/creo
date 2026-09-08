#!/usr/bin/env bash
set -euo pipefail

# audit-all.sh — run every capture sequentially under ONE label, in the order
# PERF_ALL_ORDER declares (default: platform, schema, every scenario, fe).
# Never run captures concurrently — they contaminate each other's latency
# numbers. Put cache-churning scenarios (unbounded pages, huge payloads) LAST
# among scenarios and fe after all loops (builds + Lighthouse load the machine).
# The workload window runs last with its own counter reset, so the benchmark's
# own EXPLAIN traffic never pollutes the ranking.
#
# Usage: audit-all.sh <label> [--force] [--skip-workload]
# Skips a capture whose results/<label>/<id> already exists (unless --force).

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck disable=SC1091
source "$DIR/common/lib-harness.sh"
LABEL="${1:-}"; shift || true
[[ -n "$LABEL" && "$LABEL" != -* ]] || { echo "usage: $0 <label> [--force] [--skip-workload]" >&2; exit 2; }
FORCE=0 SKIP_WL=0
for a in "$@"; do case "$a" in --force) FORCE=1 ;; --skip-workload) SKIP_WL=1 ;; *) echo "unknown flag $a" >&2; exit 2 ;; esac; done
EXTRA=(); [[ $FORCE -eq 1 ]] && EXTRA+=(--force)

if [[ -n "${PERF_ALL_ORDER+x}" && ${#PERF_ALL_ORDER[@]} -gt 0 ]]; then
  ORDER=("${PERF_ALL_ORDER[@]}")
else
  ORDER=(platform schema)
  mapfile -t SCN < <("$DIR/audit-scenario.sh" --list)
  ORDER+=("${SCN[@]}" fe)
fi

run_one() { # id
  local id="$1"
  if [[ -d "$RESULTS/$LABEL/$id" && $FORCE -eq 0 ]]; then echo "-- $id: exists under '$LABEL', skipping"; return 0; fi
  case "$id" in
    platform) if db_enabled || [[ -n "${PERF_BACKEND_DIR:-}" ]]; then "$DIR/audit-platform.sh" "$LABEL" "${EXTRA[@]}"; else echo "-- platform: not applicable (no DB, no PERF_BACKEND_DIR)"; fi ;;
    schema)   if db_enabled; then "$DIR/audit-schema.sh" "$LABEL" "${EXTRA[@]}"; else echo "-- schema: not applicable (PERF_DB_KIND=$PERF_DB_KIND)"; fi ;;
    fe)       if [[ -n "$PERF_WEB" ]]; then "$DIR/audit-fe.sh" "$LABEL" "${EXTRA[@]}"; else echo "-- fe: not applicable (PERF_WEB empty)"; fi ;;
    *)        "$DIR/audit-scenario.sh" "$id" "$LABEL" "${EXTRA[@]}" ;;
  esac
}

for id in "${ORDER[@]}"; do
  echo; echo "########## $id $LABEL ##########"
  run_one "$id" || { echo "FAILED: $id — stopping (fix and re-run; completed captures are kept)" >&2; exit 1; }
done

if [[ $SKIP_WL -eq 0 ]] && db_enabled; then
  echo; echo "########## workload pre -> drive -> post ($LABEL) ##########"
  if "$DIR/workload-pre.sh" && "$DIR/workload-drive.sh"; then
    "$DIR/workload-post.sh" "$LABEL" "${EXTRA[@]}" || echo "NOTE: workload post failed — window left open; run workload-post.sh $LABEL manually" >&2
  else
    echo "NOTE: workload stage skipped (observability setup or drive failed)" >&2
  fi
fi

echo; echo "########## ALL CAPTURES DONE — see $RESULTS/dashboard.md ##########"
