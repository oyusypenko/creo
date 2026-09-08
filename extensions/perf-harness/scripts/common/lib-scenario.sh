#!/usr/bin/env bash
# lib-scenario.sh — shared measurement engine for scenario captures
# (audit-scenario.sh sources it after lib-harness.sh). Provides, all raw
# output archived under $OUT:
#   scenario_init "$@"        arg parsing (<label> [--runs N] [--force]), preflight,
#                             immutability guard, SQL runner regeneration
#   http_loop TAG URL [N]     1 cold + N warm (default $RUNS) requests; sets
#                             HL_CODE HL_PAYLOAD HL_COLD HL_P50 HL_P95
#   gzip_potential TAG URL    offline gzip -6 potential + what the server puts on
#                             the wire for a gzip-advertising client:
#                             GP_PLAIN GP_GZ GP_RATIO GP_WIRE GP_ENC GP_WIRE_TIME GP_WIRE_RATIO
#   etag_replay TAG URL [N]   If-None-Match replay: ER_ETAG ER_CODE ER_P50 ER_GZ_CODE
#   run_sql FILE              execute a psql runner file; plans -> $RAW
#   sections_of RUNNER        section names ("runner/label") found in $RAW for a runner
#   exec_median SECTION       median 'Execution Time' (ms) across that section's runs
#   plan_fact SECTION REGEX   matching plan lines from run 2, ' · '-joined, pipe-safe
#   result_of SECTION         the correctness RESULT rows of a section, one line
#   obs_begin / finish_report per-scenario pg_stat_statements window + report
#   emit ROW                  append a row to the metrics table
#
# Protocol: p50 = rank ceil(N/2) of warm runs, p95 = rank ceil(0.95*N). DB
# medians over 3 EXPLAIN (ANALYZE, BUFFERS) runs. A label dir is immutable.

# shellcheck disable=SC1091
source "$(dirname "${BASH_SOURCE[0]}")/lib-harness.sh"

scenario_init() { # SCENARIO_ID SCENARIO_DESC must be set by the caller
  need_label "$@"
  claim_out "$SCENARIO_ID"
  MD="$OUT/${SCENARIO_ID}-metrics.md"
  RAW="$OUT/raw-plans.txt"; : > "$RAW"
  preflight_http

  # Archive the exact SQL with the capture (record mode runs the real app
  # code, compile mode assembles hand-written statements). Either way the
  # SQL a capture measured lives next to its numbers.
  SQLDIR="$OUT/sql"
  if db_enabled && [[ "${PERF_SQL_MODE:-none}" != "none" ]]; then
    if SQL_OUT="$SQLDIR" PERF_EXT_DIR="$EXT_DIR" PERF_SQL_PYTHON="${PERF_SQL_PYTHON:-python3}" \
       python3 "$HARNESS_COMMON/sql-runners.py" "${PERF_SQL_MODE}" >/dev/null 2>"$OUT/sql-runners.err"; then
      rm -f "$OUT/sql-runners.err"
      echo "   sql: runners generated (${PERF_SQL_MODE} mode) -> sql/"
    else
      echo "WARN: SQL runner generation failed (see $OUT/sql-runners.err) — DB sections will be empty" >&2
    fi
  fi

  stamp
  echo "== $SCENARIO_ID capture '$LABEL' | $STAMP | HEAD $GIT_HEAD | warm runs: $RUNS =="
  local env_note="direct ${PERF_API:-n/a}"
  [[ -n "$PERF_PROXY" ]] && env_note+=", proxy $PERF_PROXY"
  db_enabled && env_note+=", psql via PERF_PSQL_CMD"
  {
    echo "## ${SCENARIO_ID^^} metrics — $SCENARIO_DESC — label: $LABEL"
    echo
    echo "Captured $STAMP · HEAD $GIT_HEAD · $env_note · HTTP p50/p95 over $RUNS warm runs (+1 cold) · DB = median of 3 EXPLAIN (ANALYZE, BUFFERS) runs · exact SQL archived in sql/"
    echo
    echo "| Layer | Metric | Value |"
    echo "|---|---|---|"
  } > "$MD"
}

_rank() { # N P(0.xx) <values on stdin> -> value at rank ceil(P*N)
  local n="$1" p="$2"
  sort -n | awk -v n="$n" -v p="$p" 'BEGIN{i=int(p*n); if (i<p*n) i++; if(i<1)i=1} NR==i{print; exit}'
}

http_loop() { # TAG URL [N]
  local tag="$1" url="$2" n="${3:-$RUNS}" log line
  log="$OUT/http-$tag.log"
  echo "# curl -s -o /dev/null -w '%{http_code} %{size_download} %{time_total}' '$url'" > "$log"
  line=$(curl -s -o /dev/null --max-time 120 -w '%{http_code} %{size_download} %{time_total}' "$url")
  echo "cold $line" >> "$log"
  HL_CODE=$(awk '{print $1}' <<<"$line"); HL_PAYLOAD=$(awk '{print $2}' <<<"$line"); HL_COLD=$(awk '{print $3}' <<<"$line")
  local times=()
  for _ in $(seq 1 "$n"); do
    line=$(curl -s -o /dev/null --max-time 120 -w '%{http_code} %{size_download} %{time_total}' "$url")
    echo "warm $line" >> "$log"
    times+=("$(awk '{print $3}' <<<"$line")")
  done
  HL_P50=$(printf '%s\n' "${times[@]}" | _rank "$n" 0.50 | xargs printf '%.3f')
  HL_P95=$(printf '%s\n' "${times[@]}" | _rank "$n" 0.95 | xargs printf '%.3f')
  HL_COLD=$(printf '%.3f' "$HL_COLD")
}

gzip_potential() { # TAG URL
  local body="$OUT/body-$1.bin"
  curl -s --max-time 120 "$2" -o "$body"
  GP_PLAIN=$(stat -c%s "$body")
  GP_GZ=$(gzip -6 -c "$body" | wc -c)
  GP_RATIO=$(awk -v a="$GP_PLAIN" -v b="$GP_GZ" 'BEGIN{printf "%.1f", (b>0)?a/b:0}')
  # what the server actually puts on the wire for a browser (always advertises gzip)
  local hdr="$OUT/hdr-$1.txt" wire
  wire=$(curl -s --max-time 120 -H 'Accept-Encoding: gzip, br' -o /dev/null -D "$hdr" \
    -w '%{http_code} %{size_download} %{time_total}' "$2")
  GP_WIRE_CODE=$(awk '{print $1}' <<<"$wire")
  GP_WIRE=$(awk '{print $2}' <<<"$wire")
  GP_WIRE_TIME=$(awk '{printf "%.3f", $3}' <<<"$wire")
  [[ "$GP_WIRE_CODE" == 200 && "${GP_WIRE:-0}" -gt 0 ]] ||
    { echo "gzip_potential: unusable response ($GP_WIRE_CODE, $GP_WIRE B) for $2" >&2; return 1; }
  GP_ENC=$(tr -d '\r' < "$hdr" | awk -F': ' 'tolower($1)=="content-encoding"{print $2}')
  GP_ENC=${GP_ENC:-identity}
  GP_WIRE_RATIO=$(awk -v a="$GP_PLAIN" -v b="$GP_WIRE" 'BEGIN{printf "%.1f", (b>0)?a/b:0}')
}

etag_replay() { # TAG URL [N]
  local tag="$1" url="$2" n="${3:-3}" log line
  log="$OUT/etag-$tag.log"
  ER_ETAG=$(curl -s --max-time 120 -D - -o /dev/null "$url" | tr -d '\r' | awk -F': ' 'tolower($1)=="etag"{print $2}')
  if [[ -z "$ER_ETAG" ]]; then ER_CODE="n/a"; ER_P50="n/a"; ER_GZ_CODE="n/a"; return; fi
  local times=()
  for _ in $(seq 1 "$n"); do
    line=$(curl -s -o /dev/null --max-time 120 -H "If-None-Match: $ER_ETAG" -w '%{http_code} %{size_download} %{time_total}' "$url")
    echo "$line" >> "$log"
    times+=("$(awk '{print $3}' <<<"$line")")
    ER_CODE=$(awk '{print $1}' <<<"$line")
  done
  ER_P50=$(printf '%s\n' "${times[@]}" | _rank "$n" 0.50 | xargs printf '%.3f')
  # A compressing proxy rewrites strong validators to W/"..." — replay the tag
  # a real browser would hold and assert weak comparison still yields 304.
  local gz_etag
  gz_etag=$(curl -s --max-time 120 -H 'Accept-Encoding: gzip' -D - -o /dev/null "$url" \
    | tr -d '\r' | awk -F': ' 'tolower($1)=="etag"{print $2}')
  ER_GZ_CODE=$(curl -s --max-time 120 -H 'Accept-Encoding: gzip' -H "If-None-Match: $gz_etag" \
    -o /dev/null -w '%{http_code}' "$url")
  echo "gzip replay: tag=$gz_etag code=$ER_GZ_CODE" >> "$log"
}

run_sql() { PSQL < "$1" >> "$RAW" 2>&1; }

sections_of() { # RUNNER -> distinct "runner/label" sections present in $RAW
  grep -oE "^=== $1/[^ ]+ run 1 ===" "$RAW" | sed -E 's/^=== (.*) run 1 ===$/\1/'
}

exec_median() { # SECTION (e.g. s1_default/data_p100)
  awk -v s="=== $1 run" '
    /^=== / { insec = (index($0, s) == 1) }
    insec && /Execution Time:/ { print $3 }
  ' "$RAW" | sort -n | awk '{a[NR]=$1} END{if (NR) print a[int((NR+1)/2)]; else print "n/a"}'
}

_join() { awk 'NR>1{printf " · "} {printf "%s", $0} END{print ""}'; }

plan_fact() { # SECTION REGEX -> matching lines from run 2 (' · '-joined, trimmed, pipe-safe)
  awk -v s="=== $1 run 2 ===" '
    found && /^=== /{exit} found{print} $0 == s{found=1}
  ' "$RAW" | grep -E "$2" | sed 's/^ *//; s/ *$//; s/->  *//; s/|/¦/g' | head -3 | _join || true
}

result_of() { # SECTION -> RESULT value(s) on one line (psql header/dashes/rowcount stripped)
  awk -v s="=== $1 RESULT (correctness) ===" '
    found && /^=== /{exit} found{print} $0 == s{found=1}
  ' "$RAW" | sed 's/^ *//; s/ *$//; s/|/¦/g' \
    | grep -vE '^-+\+?-*$|^\([0-9]+ rows?\)$|^$' | tail -n +2 | _join || true
}

emit() { echo "$1" >> "$MD"; }

# --- per-scenario observability window (pg_stat_statements + auto_explain) ---
# Call obs_begin at the START of the HTTP layer (AFTER all EXPLAIN runs), so the
# window contains ONLY this scenario's real app-executed traffic.
obs_begin() {
  OBS_ACTIVE=0
  db_enabled || return 0
  if [[ -f "$RESULTS/.workload-mark" ]]; then
    echo "   obs: OPEN WORKLOAD WINDOW takes precedence — per-scenario window skipped"
    return 0
  fi
  pg_scalar "SELECT 1 FROM pg_extension WHERE extname='pg_stat_statements';" | grep -q 1 \
    || { echo "   obs: pg_stat_statements not installed — app-executed rows skipped"; return 0; }
  pg_scalar "SELECT pg_stat_statements_reset();" >/dev/null
  OBS_MARK=$(date -u +%Y-%m-%dT%H:%M:%S)
  OBS_ACTIVE=1
  echo "   obs: per-scenario window open (counters reset; app traffic only from here)"
}

_obs_emit() {
  [[ "${OBS_ACTIVE:-0}" == "1" ]] || return 0
  local filter="TRUE" rows
  [[ -n "$PERF_DB_HOT_TABLE" ]] && filter="query ~* 'FROM $PERF_DB_HOT_TABLE'"
  rows=$(PSQL -t -A -F $'\t' -c "
    SELECT left(md5(regexp_replace(left(query, 400), E'[\\n\\r\\t ]+', ' ', 'g')), 4),
           round(total_exec_time)::bigint, calls, round(mean_exec_time::numeric, 2),
           regexp_replace(left(query, 110), E'[\\n\\r\\t ]+', ' ', 'g')
    FROM pg_stat_statements
    WHERE $filter
      AND query !~* 'pg_stat|EXPLAIN|pg_extension'
    ORDER BY total_exec_time DESC LIMIT 8;" </dev/null)
  db_container_logs_since "$OBS_MARK" \
    | awk '/duration: .* plan:/{inplan=1} inplan{print} /^[0-9]{4}-[0-9]{2}-[0-9]{2}.*(LOG|ERROR|STATEMENT|DETAIL):/ && !/plan:/{inplan=0}' \
    > "$OUT/obs-auto-explain.txt" || true
  local nplans
  nplans=$(grep -c "plan:" "$OUT/obs-auto-explain.txt" 2>/dev/null || true)
  nplans=${nplans:-0}
  emit "| App-executed (pg_stat_statements, this capture's HTTP traffic only) | auto_explain plans: $nplans (obs-auto-explain.txt) — cross-check vs the EXPLAIN medians above |"
  local h total calls mean q
  while IFS=$'\t' read -r h total calls mean q; do
    [[ -n "$h" ]] || continue
    q="${q//|/¦}"
    emit "| App-executed · Q[$h] · $q | $calls calls · ${mean} ms mean · ${total} ms total |"
  done <<< "$rows"
}

finish_report() {
  _obs_emit
  echo
  cat "$MD"
  echo
  echo "== written: $MD =="
  rebuild_dashboard
}
