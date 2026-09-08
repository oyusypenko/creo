#!/usr/bin/env bash
set -euo pipefail

# workload-drive.sh — scripted traffic for a workload window, composed from
# every scenario's OWN request set (audit-scenario.sh <id> --urls prints
# "<count> <url>" lines). Add or change traffic in the scenario file, never here.
#
# Usage: workload-drive.sh [id ...]      (default: every scenario)

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck disable=SC1091
source "$DIR/common/lib-harness.sh"

IDS=("$@")
[[ ${#IDS[@]} -gt 0 ]] || mapfile -t IDS < <("$DIR/audit-scenario.sh" --list)
TOTAL=0
for id in "${IDS[@]}"; do
  echo "-- $id traffic"
  while read -r n url; do
    [[ -n "${url:-}" ]] || continue
    for _ in $(seq 1 "$n"); do
      curl -s -o /dev/null --max-time 120 "$url" || echo "   WARN: request failed: $url" >&2
      TOTAL=$((TOTAL + 1))
    done
  done < <("$DIR/audit-scenario.sh" "$id" --urls)
done
echo "== drive done: $TOTAL requests =="
