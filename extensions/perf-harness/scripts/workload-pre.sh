#!/usr/bin/env bash
set -euo pipefail

# workload-pre.sh — open a DB workload window (discovery layer).
# 1. Ensures observability is enabled (observability-setup.sh, idempotent —
#    the FIRST run restarts postgres + the API container).
# 2. Resets pg_stat_statements counters and marks the postgres-log position.
# Then drive traffic — workload-drive.sh or by hand in the UI — and snapshot
# with workload-post.sh <label>.
#
# Usage: workload-pre.sh [--min-duration 50ms] [--with-hypopg]

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck disable=SC1091
source "$DIR/common/lib-harness.sh"
db_enabled || { echo "workload window needs PERF_DB_KIND=postgres" >&2; exit 2; }

"$DIR/observability-setup.sh" "$@"
pg_scalar "SELECT pg_stat_statements_reset();" >/dev/null
mkdir -p "$RESULTS"
date -u +%Y-%m-%dT%H:%M:%S > "$RESULTS/.workload-mark"
echo
echo "== workload window OPEN since $(cat "$RESULTS/.workload-mark")Z =="
echo "   next: $DIR/workload-drive.sh   (or drive the UI by hand)"
echo "   then: $DIR/workload-post.sh <label>"
