#!/usr/bin/env bash
set -euo pipefail

# audit-schema.sh — table/column/index audit (scenario id "schema") for the
# tables in PERF_DB_TABLES. Per table: size row -> column rows (type, width,
# null%, skew, covering indexes, read-path usage) -> index rows (size, usage
# counter, definition). Then hypothetical-index verdicts (hypopg, against the
# project's real runner SQL), relevant extensions, and PostGIS geometry shape
# when a geometry column exists.
#
# Optional project inputs in .claude/skills/creo-perf/:
#   column-usage.tsv       "<table>.<column>\t<which scenarios/queries touch it>"
#   hypopg-candidates.tsv  "<name>\t<CREATE INDEX stmt>\t<runner>\t<section label>"
#
# Read-only: catalog queries + plain EXPLAIN; hypopg indexes are session-local.
# Usage: audit-schema.sh <label> [--force]

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck disable=SC1091
source "$DIR/common/lib-harness.sh"
db_enabled || { echo "schema audit needs PERF_DB_KIND=postgres" >&2; exit 2; }
need_label "$@"
claim_out schema
MD="$OUT/schema-metrics.md"
stamp
echo "== schema audit '$LABEL' | $STAMP | HEAD $GIT_HEAD =="
PGA() { PSQL -t -A "$@" </dev/null; }

declare -A USAGE=()
if [[ -f "$EXT_DIR/column-usage.tsv" ]]; then
  while IFS=$'\t' read -r k v; do [[ -n "$k" && "$k" != \#* ]] && USAGE["$k"]="$v"; done < "$EXT_DIR/column-usage.tsv"
fi

rows=()
emit() { rows+=("$1"); }

for T in "${PERF_DB_TABLES[@]:-}"; do
  [[ -n "$T" ]] || continue
  EXISTS=$(PGA -c "SELECT count(*) FROM pg_class WHERE relname='$T' AND relkind IN ('r','p');")
  [[ "$EXISTS" == "1" ]] || { emit "| $T · table | (table not found) |"; continue; }
  SIZES=$(PGA -c "SELECT pg_size_pretty(pg_relation_size('$T')) || ' heap / ' ||
                 pg_size_pretty(coalesce((SELECT pg_relation_size(reltoastrelid) FROM pg_class WHERE relname='$T' AND reltoastrelid<>0),0)) || ' TOAST / ' ||
                 pg_size_pretty(pg_indexes_size('$T')) || ' indexes / ' ||
                 pg_size_pretty(pg_total_relation_size('$T')) || ' total';")
  NROWS=$(PGA -c "SELECT count(*) FROM $T;")
  STATS=$(PGA -c "SELECT 'analyze='||coalesce(last_analyze::text,'never')||' · autoanalyze='||coalesce(last_autoanalyze::text,'never') FROM pg_stat_user_tables WHERE relname='$T';")
  emit "| $T · table | $SIZES · $NROWS rows · $STATS |"

  while IFS=$'\t' read -r col typ width nullf ndist topfreq; do
    [[ -n "$col" ]] || continue
    IDXS=$(PGA -c "SELECT coalesce(string_agg(c.relname || '(' || pg_size_pretty(pg_relation_size(x.indexrelid)) || ', ' || s.idx_scan || ' scans)', ' + '), 'none')
                   FROM pg_index x JOIN pg_class c ON c.oid = x.indexrelid
                   JOIN pg_stat_user_indexes s ON s.indexrelid = x.indexrelid
                   WHERE x.indrelid = '$T'::regclass AND pg_get_indexdef(x.indexrelid) ~ ('\m$col\M');")
    skew=""
    if [[ -n "$topfreq" && "$topfreq" != "0" ]]; then
      skew=$(awk -v f="$topfreq" 'BEGIN{if (f>0.5) printf " · SKEW top-value %.0f%%", f*100}')
    fi
    use="${USAGE[$T.$col]:-—}"
    emit "| $T · col $col | $typ · avg ${width:-?} B · null ${nullf:-0} · n_distinct ${ndist:-?}$skew · indexes: $(mdsafe <<<"$IDXS") · used by: $use |"
  done < <(PGA -F$'\t' -c "
    SELECT a.attname, format_type(a.atttypid, a.atttypmod), s.avg_width, round(s.null_frac::numeric,3), s.n_distinct,
           coalesce((s.most_common_freqs)[1], 0)
    FROM pg_attribute a LEFT JOIN pg_stats s ON s.tablename='$T' AND s.attname=a.attname
    WHERE a.attrelid='$T'::regclass AND a.attnum > 0 AND NOT a.attisdropped ORDER BY a.attnum;")

  while IFS=$'\t' read -r name size scans def; do
    [[ -n "$name" ]] || continue
    flag=""; [[ "$scans" == "0" ]] && flag=" · UNUSED"
    emit "| $T · idx $name | $size · idx_scan=$scans$flag · $(mdsafe <<<"$def") |"
  done < <(PGA -F$'\t' -c "
    SELECT i.indexrelname, pg_size_pretty(pg_relation_size(i.indexrelid)), i.idx_scan,
           regexp_replace(pg_get_indexdef(i.indexrelid), '^CREATE (UNIQUE )?INDEX \S+ ON \S+ USING ', '')
    FROM pg_stat_user_indexes i WHERE i.relname='$T' ORDER BY pg_relation_size(i.indexrelid) DESC;")
  UNUSED=$(PGA -c "SELECT count(*) || ' / ' || pg_size_pretty(coalesce(sum(pg_relation_size(indexrelid)),0)) FROM pg_stat_user_indexes WHERE relname='$T' AND idx_scan=0;")
  emit "| $T · unused indexes | $UNUSED |"
done

# ---------- hypothetical index verdicts ----------
if PGA -c "SELECT 1 FROM pg_extension WHERE extname='hypopg';" | grep -q 1; then
  if [[ -f "$EXT_DIR/hypopg-candidates.tsv" ]]; then
    echo "-- hypopg candidate verdicts (against real runner SQL)"
    SQLDIR="$OUT/sql"
    if [[ "${PERF_SQL_MODE:-none}" != "none" ]]; then
      SQL_OUT="$SQLDIR" PERF_EXT_DIR="$EXT_DIR" PERF_SQL_PYTHON="${PERF_SQL_PYTHON:-python3}" \
        python3 "$DIR/common/sql-runners.py" "$PERF_SQL_MODE" >/dev/null 2>"$OUT/sql-runners.err" && rm -f "$OUT/sql-runners.err" || true
    fi
    get_query() { # FILE SECTION -> statement without EXPLAIN prefix
      awk -v s="=== $2 run 1 ===" 'found && /^\\echo/ {exit} found {print} $0 == "\\echo " s {found=1}' "$1" | sed '1s/^EXPLAIN (ANALYZE, BUFFERS) //'
    }
    : > "$OUT/hypopg-plans.txt"
    while IFS=$'\t' read -r name create runner section; do
      [[ -n "$name" && "$name" != \#* ]] || continue
      qfile="$SQLDIR/$runner.sql"; [[ -f "$qfile" ]] || qfile="$EXT_DIR/sql/$runner.sql"
      [[ -f "$qfile" ]] || { emit "| hypothetical · $name | runner $runner.sql not found |"; continue; }
      q=$(get_query "$qfile" "$runner/$section")
      [[ -n "$q" ]] || { emit "| hypothetical · $name | section $runner/$section not found |"; continue; }
      { echo "SELECT hypopg_reset();"; echo "SELECT * FROM hypopg_create_index('${create//\'/\'\'}');"; echo "EXPLAIN $q"; } > "$OUT/.hypo.sql"
      plan=$(PSQL < "$OUT/.hypo.sql" 2>&1) || true
      { echo "=== $name ==="; echo "$plan"; } >> "$OUT/hypopg-plans.txt"
      if grep -q '<[0-9]*>' <<<"$plan"; then
        cost=$(grep -oE 'cost=[0-9.]+\.\.[0-9.]+' <<<"$plan" | head -1)
        emit "| hypothetical · $name | USED by planner ($cost) |"
      else
        emit "| hypothetical · $name | NOT used (planner prefers existing plan) |"
      fi
    done < "$EXT_DIR/hypopg-candidates.tsv"
  else
    emit "| hypothetical · (none declared) | add hypopg-candidates.tsv to test index ideas without creating them |"
  fi
else
  emit "| hypothetical · (skipped) | hypopg not installed — observability-setup.sh --with-hypopg |"
fi

# ---------- extensions + PostGIS shape ----------
TRGM=$(PGA -c "SELECT CASE WHEN count(*)>0 THEN 'installed' ELSE 'ABSENT — blocks any trigram index for ILIKE ''%…%'' search paths' END FROM pg_extension WHERE extname='pg_trgm';")
emit "| extension · pg_trgm | $TRGM |"
if PGA -c "SELECT 1 FROM pg_extension WHERE extname='postgis';" | grep -q 1; then
  while IFS=$'\t' read -r t c; do
    [[ -n "$t" ]] || continue
    GEOM=$(PGA -F' ' -c "SELECT GeometryType($c::geometry), count(*), round(avg(ST_NPoints($c::geometry))), max(ST_NPoints($c::geometry)), pg_size_pretty(max(ST_MemSize($c::geometry))::bigint) FROM $t WHERE $c IS NOT NULL GROUP BY 1 ORDER BY 2 DESC;" \
      | awk '{printf "%s%s ×%s (avg %s pts, max %s pts, max size %s %s)", (NR>1?" · ":""), $1, $2, $3, $4, $5, $6}')
    TYPE=$(PGA -c "SELECT format_type(atttypid, atttypmod) FROM pg_attribute WHERE attrelid='$t'::regclass AND attname='$c';")
    emit "| postgis · $t.$c | $(mdsafe <<<"$TYPE") · $GEOM |"
  done < <(PGA -F$'\t' -c "SELECT f_table_name, f_geometry_column FROM geometry_columns WHERE f_table_name IN ($(printf "'%s'," "${PERF_DB_TABLES[@]}" | sed 's/,$//')) UNION SELECT f_table_name, f_geography_column FROM geography_columns WHERE f_table_name IN ($(printf "'%s'," "${PERF_DB_TABLES[@]}" | sed 's/,$//'));" 2>/dev/null || true)
fi
RESET_AT=$(PGA -c "SELECT coalesce(stats_reset::text,'never (counters may still have been zeroed by crash recovery)') FROM pg_stat_database WHERE datname=current_database();")
emit "| meta · pg_stat counters reset | $RESET_AT |"

{
  echo "## Schema metrics — tables/columns/indexes — label: $LABEL"
  echo
  echo "Captured $STAMP · HEAD $GIT_HEAD · read-only (catalog + plain EXPLAIN + session-local hypopg) · tables: ${PERF_DB_TABLES[*]}"
  echo
  echo "| Metric | Value |"
  echo "|---|---|"
  printf '%s\n' "${rows[@]}"
} > "$MD"

echo; cat "$MD"; echo; echo "== written: $MD =="
rebuild_dashboard
