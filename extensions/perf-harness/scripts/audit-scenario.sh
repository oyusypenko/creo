#!/usr/bin/env bash
set -euo pipefail

# audit-scenario.sh — deterministic capture of ONE user-facing scenario, defined
# by the project at .claude/skills/creo-perf/scenarios/<id>.sh (see
# templates/scenario.template.sh). The runner is generic; the scenario file
# owns its URLs, SQL runner names, FE interaction key and any mechanism probes.
#
# Usage:
#   audit-scenario.sh <id> <label> [--runs N] [--force]     capture
#   audit-scenario.sh <id> --urls                           print "<count> <url>" lines
#   audit-scenario.sh --list                                list scenario ids
#
# Default flow (each part skipped when the scenario does not declare it):
#   DB    run every SCENARIO_SQL runner (3× EXPLAIN (ANALYZE, BUFFERS) per section),
#         report per-section medians + decisive plan lines + per-runner ≈ totals
#   probes scenario_probes()  (optional — extra EXPLAINs, catalog facts)
#   HTTP  primary URL: direct + proxy loops, on-wire bytes, gzip potential, ETag replay;
#         secondary URLs: direct p50
#   FE    fe-interactions.mjs for SCENARIO_FE (needs Playwright + fe-interactions.json)
#   report scenario_report()  (optional — extra rows) then finish_report
#   Correctness ref line from every RESULT section.

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [[ "${1:-}" == "--list" ]]; then
  export PERF_ALLOW_NO_CONFIG=1
  # shellcheck disable=SC1091
  source "$DIR/common/lib-harness.sh"
  ls "$EXT_DIR/scenarios/"*.sh 2>/dev/null | xargs -n1 basename 2>/dev/null | sed 's/\.sh$//' || true
  exit 0
fi

SCENARIO_ID="${1:-}"; shift || true
[[ -n "$SCENARIO_ID" && "$SCENARIO_ID" != -* ]] || { echo "usage: $0 <id> <label> [--runs N] [--force] | $0 <id> --urls | $0 --list" >&2; exit 2; }

# shellcheck disable=SC1091
source "$DIR/common/lib-scenario.sh"
SCENARIO_FILE="$EXT_DIR/scenarios/$SCENARIO_ID.sh"
[[ -f "$SCENARIO_FILE" ]] || { echo "ERROR: no scenario file $SCENARIO_FILE (ids: $("$0" --list | paste -sd' '))" >&2; exit 2; }

SCENARIO_DESC="" SCENARIO_URLS=() SCENARIO_SQL=() SCENARIO_FE="" SCENARIO_PLAN_REGEX=""
# shellcheck disable=SC1090
source "$SCENARIO_FILE"
SCENARIO_ID="${SCENARIO_ID:-$(basename "$SCENARIO_FILE" .sh)}"
[[ -n "$SCENARIO_DESC" ]] || SCENARIO_DESC="scenario $SCENARIO_ID"
PLAN_REGEX="${SCENARIO_PLAN_REGEX:-Seq Scan|Index.*Scan|Bitmap.*Scan|Sort Method|Rows Removed|external merge|SubPlan|Recheck Cond}"

if [[ "${1:-}" == "--urls" ]]; then
  printf '%s\n' "${SCENARIO_URLS[@]}"
  exit 0
fi

scenario_init "$@"

# ---------- DB layer ----------
CORRECTNESS=()
if db_enabled && [[ ${#SCENARIO_SQL[@]} -gt 0 ]]; then
  echo "-- DB: EXPLAIN runs (${SCENARIO_SQL[*]})"
  for runner in "${SCENARIO_SQL[@]}"; do
    f="$SQLDIR/$runner.sql"
    [[ -f "$f" ]] || f="$EXT_DIR/sql/$runner.sql"     # hand-maintained runner files
    if [[ ! -f "$f" ]]; then
      emit "| DB | $runner | runner file missing (sql/$runner.sql) — see scenario-spec.md |"
      continue
    fi
    [[ "$f" == "$SQLDIR"/* ]] || { mkdir -p "$SQLDIR"; cp "$f" "$SQLDIR/"; }
    run_sql "$f"
    total=0; parts=""
    while read -r section; do
      [[ -n "$section" ]] || continue
      label="${section#*/}"
      ms=$(exec_median "$section")
      facts=$(plan_fact "$section" "$PLAN_REGEX")
      emit "| DB | $runner · $label | $ms ms — ${facts:-no plan lines matched} |"
      if [[ "$ms" != "n/a" ]]; then
        total=$(awk -v a="$total" -v b="$ms" 'BEGIN{printf "%.3f", a+b}')
        parts+="${parts:+ + }$label $ms ms"
      fi
      res=$(result_of "$section")
      [[ -n "$res" ]] && CORRECTNESS+=("$runner/$label=$res")
    done < <(sections_of "$runner")
    [[ -n "$parts" ]] && emit "| DB | $runner · per-request time | $parts ≈ $(printf '%.0f' "$total") ms |"
  done
fi

declare -f scenario_probes >/dev/null && { echo "-- probes"; scenario_probes; }

# ---------- HTTP layer ----------
if [[ ${#SCENARIO_URLS[@]} -gt 0 ]]; then
  echo "-- HTTP: direct${PERF_PROXY:+ + proxy} loops"
  obs_begin
  PRIMARY=$(awk '{print $2}' <<<"${SCENARIO_URLS[0]}")
  PRIMARY_PROXY=$(proxy_url "$PRIMARY")
  http_loop api "$PRIMARY"; API_PAYLOAD=$HL_PAYLOAD; API_COLD=$HL_COLD; API_P50=$HL_P50; API_P95=$HL_P95; API_CODE=$HL_CODE
  if [[ -n "$PRIMARY_PROXY" ]]; then
    http_loop proxy "$PRIMARY_PROXY"; NGX_PAYLOAD=$HL_PAYLOAD; NGX_COLD=$HL_COLD; NGX_P50=$HL_P50; NGX_P95=$HL_P95
    PROXY_OH=$(awk -v a="$NGX_P50" -v b="$API_P50" 'BEGIN{printf "%.3f", a-b}')
    WIRE_URL="$PRIMARY_PROXY"; WIRE_LAYER="Network (proxy)"
  else
    WIRE_URL="$PRIMARY"; WIRE_LAYER="Network (direct)"
  fi
  gzip_potential wire "$WIRE_URL" || true
  etag_replay wire "$WIRE_URL" 3
  SECONDARY_ROWS=()
  i=0
  for entry in "${SCENARIO_URLS[@]:1}"; do
    i=$((i+1)); u=$(awk '{print $2}' <<<"$entry"); n=$(( RUNS < 5 ? RUNS : 5 ))
    http_loop "sec$i" "$u" "$n"
    SECONDARY_ROWS+=("${u#"$PERF_API"} → $HL_PAYLOAD B, p50 $HL_P50 s ($n warm)")
  done
fi

# ---------- FE layer ----------
FE_ROW=""
if [[ -n "$SCENARIO_FE" ]]; then
  echo "-- FE: interaction probe ($SCENARIO_FE)"
  FE_ROW=$(PERF_EXT_DIR="$EXT_DIR" PERF_APP_DIR="${PERF_APP_DIR:-}" node "$HARNESS_COMMON/fe-interactions.mjs" "$SCENARIO_FE" "$OUT" 2>"$OUT/fe-interactions.err" \
    || echo "interactive pass unavailable ($(head -1 "$OUT/fe-interactions.err" 2>/dev/null || echo 'see fe-interactions.err'))")
fi

# ---------- report ----------
[[ -n "$FE_ROW" ]] && emit "| FE | interaction ($SCENARIO_FE) | $FE_ROW |"
if [[ ${#SCENARIO_URLS[@]} -gt 0 ]]; then
  if [[ -n "${GP_WIRE:-}" ]]; then
    emit "| $WIRE_LAYER | on-wire payload | $GP_PLAIN B identity (offline gzip -6: $GP_GZ B = ${GP_RATIO}×) · to a browser: $GP_WIRE B $GP_ENC in ${GP_WIRE_TIME}s (${GP_WIRE_RATIO}×) |"
  fi
  if [[ -n "$PRIMARY_PROXY" ]]; then
    emit "| Network (proxy) | warm p50 / p95 | $NGX_P50 s / $NGX_P95 s (cold $NGX_COLD s; proxy overhead ≈ $PROXY_OH s) |"
  fi
  emit "| $WIRE_LAYER | If-None-Match → 304 | code $ER_CODE, p50 $ER_P50 s · gzip client: $ER_GZ_CODE${ER_ETAG:+ (ETag $ER_ETAG)} |"
  emit "| API (direct) | warm p50 / p95 | $API_P50 s / $API_P95 s (cold $API_COLD s; HTTP $API_CODE, payload $API_PAYLOAD B) |"
  for r in "${SECONDARY_ROWS[@]:-}"; do [[ -n "$r" ]] && emit "| API (direct) | secondary | $r |"; done
fi

declare -f scenario_report >/dev/null && scenario_report

if [[ ${#CORRECTNESS[@]} -gt 0 ]]; then
  emit ""
  emit "Correctness ref: $(printf '%s · ' "${CORRECTNESS[@]}" | sed 's/ · $//')"
fi

finish_report
