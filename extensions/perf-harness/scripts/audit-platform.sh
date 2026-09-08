#!/usr/bin/env bash
set -euo pipefail

# audit-platform.sh — one-time platform configuration audit (scenario id
# "platform"): backend process facts + database server settings. Read-only:
# inspects source, running containers and pg_settings; mutates nothing.
#
# These are CONTEXT facts, not before/after metrics: a config change is proven
# by re-running a scenario and diffing its plan/latency, never by quoting a
# setting from this report.
#
# Backend section depends on PERF_BACKEND_KIND (fastapi | node | other).
# Usage: audit-platform.sh <label> [--force]

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck disable=SC1091
source "$DIR/common/lib-harness.sh"
need_label "$@"
claim_out platform
MD="$OUT/platform-metrics.md"
stamp
echo "== platform audit '$LABEL' | $STAMP | HEAD $GIT_HEAD =="

BK="${PERF_BACKEND_KIND:-other}"
BDIR="${PERF_BACKEND_DIR:-}"
ROWS=()
row() { ROWS+=("| $1 | $2 |"); }

# ---------- backend ----------
if [[ -n "$BDIR" && -d "$BDIR" ]]; then
  case "$BK" in
    fastapi)
      python3 - "$BDIR" "${PERF_ROUTES_GLOB:-$BDIR/app/route/*.py}" > "$OUT/endpoints.txt" <<'PY'
import glob, re, sys
from pathlib import Path
deco = re.compile(r"^@(?:router|app|\w+_router)\.(get|post|put|delete|patch)\(")
files = sorted(Path(p) for p in glob.glob(sys.argv[2]))
sync_n = async_n = 0
for f in files:
    lines = f.read_text(errors="ignore").splitlines()
    for i, line in enumerate(lines):
        if deco.match(line.strip()):
            for j in range(i + 1, min(i + 12, len(lines))):
                s = lines[j].strip()
                if s.startswith("async def"):
                    async_n += 1; print(f"{f.name}\tasync\t{s.split('(')[0]}"); break
                if s.startswith("def"):
                    sync_n += 1; print(f"{f.name}\tsync\t{s.split('(')[0]}"); break
print(f"TOTAL\tsync={sync_n}\tasync={async_n}")
PY
      HANDLERS=$(tail -1 "$OUT/endpoints.txt" | tr '\t' ' ')
      row "Handler style (decorated endpoints)" "$HANDLERS — sync def = blocking DB I/O on the AnyIO threadpool (default 40/worker)"
      WORKERS=$(grep -rhoE 'WORKERS[:=-]+[0-9]+|--workers[ =][0-9]+|workers *= *[0-9]+' "$BDIR" --include='*.sh' --include='*.py' --include='Dockerfile*' --include='*.toml' 2>/dev/null | head -1 || true)
      row "Workers" "${WORKERS:-not found in start scripts/Dockerfile (uvicorn default: 1)}"
      POOL=$(grep -rnE 'pool_size|max_overflow|pool_pre_ping|pool_recycle|pool_timeout' "$BDIR" --include='*.py' 2>/dev/null | grep -v '/\.venv/' | head -3 | mdsafe | paste -sd' ' || true)
      row "Connection pool" "${POOL:-no explicit pool args -> SQLAlchemy QueuePool defaults: pool_size=5, max_overflow=10 = 15 conns/worker; no pre_ping/recycle}"
      MW=$(grep -rnE 'add_middleware|GZipMiddleware|CORSMiddleware' "$BDIR" --include='*.py' 2>/dev/null | grep -v '/\.venv/' | head -4 | mdsafe | paste -sd' ' || true)
      row "Middleware" "${MW:-NONE registered (no GZip, no timing, no CORS)}"
      ORJSON=$(grep -rlE 'orjson|ORJSONResponse' "$BDIR" --include='*.py' --include='pyproject.toml' 2>/dev/null | grep -v '/\.venv/' | head -1 || true)
      row "Serialization" "${ORJSON:+orjson present: $ORJSON}${ORJSON:-stdlib json + pydantic only (no orjson) — matters when payloads are 100s of KB}"
      FSTR=$(grep -rcE 'f"""|f"SELECT|f"WITH' "$BDIR" --include='*.py' 2>/dev/null | grep -v '/\.venv/' | grep -v ':0$' | sed "s|$BDIR/||" | paste -sd' ' || true)
      row "Statement reuse" "f-string SQL assemblies per file: ${FSTR:-none} -> distinct SQL string per filter combo, no plan reuse where present"
      ;;
    node)
      ASYNC=$(grep -rhoE '\.(get|post|put|delete|patch)\(' "$BDIR" --include='*.ts' --include='*.js' 2>/dev/null | grep -v node_modules | wc -l || echo 0)
      row "Route registrations (heuristic)" "$ASYNC handler registrations under $(basename "$BDIR")"
      COMP=$(grep -rlE "compression\(|fastify-compress|@fastify/compress" "$BDIR" --include='*.ts' --include='*.js' 2>/dev/null | grep -v node_modules | head -1 || true)
      row "Compression middleware" "${COMP:-none in source (edge proxy must compress)}"
      POOL=$(grep -rnE 'new Pool\(|connectionLimit|pool: *\{|connection_limit|poolSize' "$BDIR" --include='*.ts' --include='*.js' --include='*.prisma' --include='.env*' 2>/dev/null | grep -v node_modules | head -3 | mdsafe | paste -sd' ' || true)
      row "Connection pool" "${POOL:-no explicit pool config found (driver default: pg Pool max=10; Prisma connection_limit = num_cpus*2+1)}"
      ORM=$(grep -rhoE '"(prisma|@prisma/client|typeorm|knex|drizzle-orm|sequelize|pg|mysql2)"' "$BDIR/package.json" 2>/dev/null | tr -d '"' | sort -u | paste -sd', ' || true)
      row "Data layer" "${ORM:-unknown}"
      ;;
    *)
      row "Backend" "PERF_BACKEND_KIND=$BK — no automated backend probe; record handler style, worker/pool arithmetic, middleware and serialization by hand (see platform-audit.md)"
      ;;
  esac
else
  row "Backend" "PERF_BACKEND_DIR unset or missing — backend section skipped"
fi

# ---------- edge compression probe ----------
PROBE="${PERF_PROBE_URL:-}"
if [[ -n "$PROBE" ]]; then
  probe() { local enc bytes
    enc=$(curl -s -D- -o /dev/null --max-time 30 -H "Accept-Encoding: $2" "$1" | tr -d '\r' | awk -F': ' 'tolower($1)=="content-encoding"{print $2}')
    bytes=$(curl -s -o /dev/null --max-time 30 -w '%{size_download}' -H "Accept-Encoding: $2" "$1")
    echo "${enc:-identity} ${bytes:-0}"; }
  read -r _ ID <<<"$(probe "$PROBE" identity)"
  read -r ENC CMP <<<"$(probe "$PROBE" 'gzip, br')"
  row "Edge compression (probe URL)" "$ENC $(printf "%'d" "${CMP:-0}") B from $(printf "%'d" "${ID:-0}") B ($(awk -v a="${ID:-1}" -v b="${CMP:-1}" 'BEGIN{printf "%.1f", (b>0)?a/b:0}')x) — ${PROBE#"$PERF_API"}"
fi

# ---------- database ----------
DBROWS=()
if db_enabled; then
  PSQL -c "SELECT name, setting, unit, source FROM pg_settings WHERE source NOT IN ('default','override') ORDER BY name;" </dev/null > "$OUT/pg-nondefault.txt"
  KEYS=(work_mem shared_buffers effective_cache_size random_page_cost max_connections jit max_parallel_workers_per_gather autovacuum_analyze_scale_factor)
  WHY=(
    "sort spill threshold (any 'external merge Disk' plan line points here)"
    "buffer cache; compare with hot-table total size below"
    "planner's cache assumption"
    "4 = spinning-disk assumption; biases the planner against index scans on SSD"
    "vs app-side pool arithmetic"
    "JIT overhead visible in complex plans"
    "parallel scan ceiling"
    "analyze trigger threshold"
  )
  : > "$OUT/pg-key-settings.txt"
  for i in "${!KEYS[@]}"; do
    v=$(pg_scalar "SHOW ${KEYS[$i]};")
    echo "${KEYS[$i]} = $v" >> "$OUT/pg-key-settings.txt"
    DBROWS+=("| ${KEYS[$i]} | $v | ${WHY[$i]} |")
  done
  TABLES_SQL=$(printf "'%s'," "${PERF_DB_TABLES[@]:-}" | sed "s/,$//; s/''//g")
  STATS=$(pg_scalar "SELECT string_agg(relname||': last_analyze='||COALESCE(last_analyze::text,'never')||', last_autoanalyze='||COALESCE(last_autoanalyze::text,'never')||', n_live_tup='||n_live_tup||', mod_since='||n_mod_since_analyze, ' · ' ORDER BY relname) FROM pg_stat_user_tables WHERE relname IN (${TABLES_SQL:-''});")
  EXT_INSTALLED=$(pg_scalar "SELECT string_agg(extname, ', ') FROM pg_extension;")
  EXT_MISSING=""
  for e in pg_trgm pg_stat_statements hypopg; do
    pg_scalar "SELECT 1 FROM pg_extension WHERE extname='$e';" | grep -q 1 || EXT_MISSING+="$e "
  done
  HOT_SIZE=$([[ -n "$PERF_DB_HOT_TABLE" ]] && pg_scalar "SELECT pg_size_pretty(pg_total_relation_size('$PERF_DB_HOT_TABLE'));" || echo n/a)
  LIMITS="n/a"
  if [[ -n "$PERF_DB_CONTAINER" ]]; then
    LIMITS=$(docker inspect "$PERF_DB_CONTAINER" ${PERF_API_CONTAINER:+"$PERF_API_CONTAINER"} --format '{{.Name}}: Memory={{.HostConfig.Memory}} NanoCpus={{.HostConfig.NanoCpus}}' 2>/dev/null | paste -sd' · ' || echo n/a)
  fi
fi

# ---------- report ----------
{
  echo "## Platform configuration — label: $LABEL"
  echo
  echo "Captured $STAMP · HEAD $GIT_HEAD · read-only inspection (source + containers + pg_settings)"
  echo
  echo "### Backend ($BK)"
  echo
  echo "| Fact | Value |"
  echo "|---|---|"
  printf '%s\n' "${ROWS[@]}"
  if db_enabled; then
    echo
    echo "### Database (PostgreSQL)"
    echo
    echo "| Setting | Value | Why it matters |"
    echo "|---|---|---|"
    printf '%s\n' "${DBROWS[@]}"
    echo
    echo "| Fact | Value |"
    echo "|---|---|"
    echo "| Hot table total size | ${PERF_DB_HOT_TABLE:-n/a}: $HOT_SIZE (vs shared_buffers above) |"
    echo "| Non-default settings | see pg-nondefault.txt ($(grep -c '|' "$OUT/pg-nondefault.txt" 2>/dev/null || echo '?') rows) |"
    echo "| Stats state | ${STATS:-n/a} |"
    echo "| Extensions installed | $EXT_INSTALLED |"
    echo "| Extensions ABSENT (relevant) | ${EXT_MISSING:-none missing} |"
    echo "| Container limits | $LIMITS (0 = unlimited; timings reflect the raw host) |"
  fi
  echo
  echo "Disposition: context facts — a config change is proven by re-running a scenario (plan/latency diff), never by quoting a setting."
} > "$MD"

echo; cat "$MD"; echo; echo "== written: $MD =="
rebuild_dashboard
