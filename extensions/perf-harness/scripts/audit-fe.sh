#!/usr/bin/env bash
set -euo pipefail

# audit-fe.sh — deterministic initial-load / build audit of the served frontend
# (scenario id "fe"). Captures in one run:
#   1. served assets at $PERF_WEB: on-wire bytes, encoding, cache headers,
#      bytes-to-first-render, root element before JS
#   2. local production build: chunk counts, raw/gzip sizes, dynamic-import count,
#      fonts emitted, dependencies declared but absent from the bundle
#   3. bundle composition (vite only): top packages by rendered bytes
#   4. Lighthouse ×N (pinned major 13, headless, default simulated mobile
#      throttling), median-by-LCP: score, FCP/LCP/SI, TBT/TTI/CLS, bootup, long
#      tasks, unused JS/CSS, full-load bytes, largest request, duplicate API calls
#
# Usage: audit-fe.sh <label> [--runs N] [--skip-build] [--skip-composition] [--force]
# Lighthouse numbers are LAB numbers — never compare them to wall-clock desktop times.

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck disable=SC1091
source "$DIR/common/lib-harness.sh"

RUNS="${PERF_LIGHTHOUSE_RUNS:-3}"
need_label "$@"
SKIP_BUILD=0 SKIP_COMP=0
for a in "${EXTRA_ARGS[@]:-}"; do case "$a" in
  --skip-build) SKIP_BUILD=1 ;;
  --skip-composition) SKIP_COMP=1 ;;
  "") ;;
  *) echo "unknown flag: $a" >&2; exit 2 ;;
esac; done
claim_out fe
MD="$OUT/fe-metrics.md"

fail() { echo "PREFLIGHT FAIL: $*" >&2; exit 1; }
[[ -n "$PERF_WEB" ]] || fail "PERF_WEB not set in perf.config.sh"
curl -sf -o /dev/null --max-time 5 "$PERF_WEB/" || fail "frontend not reachable at $PERF_WEB (stack up?)"
command -v node >/dev/null || fail "node not found"
command -v gzip >/dev/null || fail "gzip not found"
CHROME="${CHROME_PATH:-$(command -v google-chrome || command -v google-chrome-stable || command -v chromium || command -v chromium-browser || true)}"
[[ -n "$CHROME" ]] || fail "no Chrome binary (google-chrome/chromium) for Lighthouse — set CHROME_PATH"
stamp
echo "== FE audit '$LABEL' | $STAMP | HEAD $GIT_HEAD | chrome: $("$CHROME" --version 2>/dev/null | head -1) =="

probe_url() { # URL -> "<plain_bytes> <wire_bytes> <content_encoding> <cache_control>"
  local url="$1" plain wire enc cc
  plain=$(curl -so /dev/null --max-time 30 -w '%{size_download}' "$url")
  enc=$(curl -sI --compressed --max-time 30 "$url" | tr -d '\r' | awk -F': ' 'tolower($1)=="content-encoding"{print $2}')
  cc=$(curl -sI --max-time 30 "$url" | tr -d '\r' | awk -F': ' 'tolower($1)=="cache-control"{print $2}' | tr ' ' '_')
  if [[ -n "$enc" ]]; then wire=$(curl -s --compressed --max-time 30 -o /dev/null -w '%{size_download}' "$url"); else wire=$plain; fi
  echo "$plain $wire ${enc:-none} ${cc:-none}"
}

# ---------- 1. served assets ----------
echo "-- [1/4] served assets at $PERF_WEB"
INDEX_HTML="$OUT/index.html"
curl -s --max-time 30 "$PERF_WEB/" -o "$INDEX_HTML"
HTML_PROBE=($(probe_url "$PERF_WEB/"))
mapfile -t LOCAL_ASSETS < <(grep -oE '(src|href)="[^"]+"' "$INDEX_HTML" | sed -E 's/^(src|href)="//; s/"$//' | grep -E '^/|^\./' | sort -u)
mapfile -t EXT_ASSETS < <(grep -oE '(src|href)="https?://[^"]+"' "$INDEX_HTML" | sed -E 's/^(src|href)="//; s/"$//' | grep -E '\.(css|js)($|\?)|fonts' | sort -u)
ASSET_TABLE="$OUT/served-assets.tsv"
echo -e "url\tplain_bytes\twire_bytes\tencoding\tcache_control" > "$ASSET_TABLE"
echo -e "/\t${HTML_PROBE[0]}\t${HTML_PROBE[1]}\t${HTML_PROBE[2]}\t${HTML_PROBE[3]}" >> "$ASSET_TABLE"
JS_WIRE=0; CSS_WIRE=0; EXT_WIRE=0; STATIC_OK="yes"
for a in "${LOCAL_ASSETS[@]:-}"; do
  [[ -n "$a" ]] || continue
  p=($(probe_url "$PERF_WEB${a#.}"))
  echo -e "$a\t${p[0]}\t${p[1]}\t${p[2]}\t${p[3]}" >> "$ASSET_TABLE"
  if [[ "$a" == *.js || "$a" == *.css ]]; then
    { [[ "${p[2]}" == "gzip" || "${p[2]}" == "br" ]] && [[ "${p[3]}" == *max-age=31536000* ]]; } || STATIC_OK="NO ($a: enc=${p[2]} cc=${p[3]})"
  fi
  [[ "$a" == *.js ]] && JS_WIRE=$((JS_WIRE + p[1]))
  [[ "$a" == *.css ]] && CSS_WIRE=$((CSS_WIRE + p[1]))
done
for a in "${EXT_ASSETS[@]:-}"; do
  [[ -n "$a" ]] || continue
  p=($(probe_url "$a" 2>/dev/null || echo "0 0 n/a n/a"))
  echo -e "$a\t${p[0]}\t${p[1]}\t${p[2]}\t${p[3]}" >> "$ASSET_TABLE"
  EXT_WIRE=$((EXT_WIRE + p[1]))
done
FIRST_RENDER_BYTES=$((HTML_PROBE[1] + JS_WIRE + CSS_WIRE + EXT_WIRE))
ROOT_DIV=$(grep -oE '<div id="(root|app|__next)">[^<]{0,80}' "$INDEX_HTML" | head -1 || echo 'n/a')

# ---------- 2. local build ----------
BUILD_ROWS=""
if [[ $SKIP_BUILD -eq 0 && -n "${PERF_APP_DIR:-}" && -d "${PERF_APP_DIR:-/nonexistent}" ]]; then
  echo "-- [2/4] production build (${PERF_BUILD_CMD:-npx --yes vite build})"
  (cd "$PERF_APP_DIR" && bash -c "${PERF_BUILD_CMD:-npx --yes vite build --logLevel error}") > "$OUT/build.log" 2>&1 \
    || fail "build failed — see $OUT/build.log"
  DIST="${PERF_DIST_DIR:-$PERF_APP_DIR/dist}"
  [[ -d "$DIST" ]] || fail "dist dir $DIST not found after build (set PERF_DIST_DIR)"
  JS_COUNT=$(find "$DIST" -name '*.js' -not -name '*.map' | wc -l)
  CSS_COUNT=$(find "$DIST" -name '*.css' | wc -l)
  sum_bytes() { find "$DIST" -name "$1" -not -name '*.map' -printf '%s\n' | awk '{s+=$1} END{print s+0}'; }
  gz_bytes() { find "$DIST" -name "$1" -not -name '*.map' -exec cat {} + 2>/dev/null | gzip -6 -c | wc -c; }
  JS_RAW=$(sum_bytes '*.js'); JS_GZ=$(gz_bytes '*.js')
  CSS_RAW=$(sum_bytes '*.css'); CSS_GZ=$(gz_bytes '*.css')
  FONT_FILES=$(find "$DIST" -name '*.woff*' | wc -l); FONT_BYTES=$(sum_bytes '*.woff*')
  PRECOMP=$(find "$DIST" \( -name '*.br' -o -name '*.gz' \) | wc -l)
  SRC="${PERF_SRC_DIR:-$PERF_APP_DIR/src}"
  DYN_IMPORTS=$(grep -rE 'React\.lazy|lazy\(|import\(' "$SRC" --include='*.ts' --include='*.tsx' --include='*.js' --include='*.jsx' --include='*.vue' --include='*.svelte' 2>/dev/null | grep -vc 'import type' || true)
  # declared runtime deps absent from the built output = dead weight (or a CDN load)
  DEAD=$(node -e '
const fs=require("fs"),path=require("path");
const p=JSON.parse(fs.readFileSync(path.join(process.argv[1],"package.json"),"utf8"));
const dist=process.argv[2]; let blob="";
(function walk(d){for(const f of fs.readdirSync(d)){const q=path.join(d,f);const s=fs.statSync(q);
 if(s.isDirectory())walk(q);else if(/\.(js|css)$/.test(f))blob+=fs.readFileSync(q,"utf8").slice(0,2e6);}})(dist);
const dead=Object.keys(p.dependencies||{}).filter(d=>!blob.includes(d.split("/").pop()));
console.log(dead.length?dead.join(", "):"none");' "$PERF_APP_DIR" "$DIST" 2>/dev/null || echo "n/a")
  BUILD_ROWS=$(cat <<EOF
| Build | JS chunks | $JS_COUNT files · $JS_RAW B raw / $JS_GZ B gzip-6 (on-wire entry JS: $JS_WIRE B) |
| Build | CSS files | $CSS_COUNT files · $CSS_RAW B raw / $CSS_GZ B gzip-6 (on-wire entry CSS: $CSS_WIRE B) |
| Build | code splitting | dynamic imports in src: $DYN_IMPORTS · pre-compressed siblings (.br/.gz) in dist: $PRECOMP |
| Build | fonts emitted | $FONT_FILES files, $FONT_BYTES B in dist (fetched count from LH below) |
| Build | deps declared but not in bundle (heuristic) | $DEAD |
EOF
)
else
  echo "-- [2/4] build skipped"
fi

# ---------- 3. composition (vite only) ----------
COMP_ROWS=""
if [[ $SKIP_COMP -eq 0 && $SKIP_BUILD -eq 0 && "${PERF_BUNDLER:-vite}" == "vite" && -n "${PERF_APP_DIR:-}" ]]; then
  echo "-- [3/4] bundle composition (vite-bundle-visualizer raw-data)"
  if (cd "$PERF_APP_DIR" && npx --yes vite-bundle-visualizer -t raw-data -o "$OUT/bundle-raw.json") > "$OUT/visualizer.log" 2>&1; then
    COMP_ROWS=$(node -e '
const fs=require("fs");const data=JSON.parse(fs.readFileSync(process.argv[1],"utf8"));
const parts=data.nodeParts,metas=data.nodeMetas;const byPkg={};let total=0;
for(const uid of Object.keys(parts)){const meta=metas[parts[uid].metaUid];if(!meta)continue;
 const id=meta.id||"";const len=parts[uid].renderedLength||0;total+=len;
 const m=id.match(/(?:node_modules|vendor)\/(@[^/]+\/[^/]+|[^/]+)\//);const pkg=m?m[1]:"(app source)";
 byPkg[pkg]=(byPkg[pkg]||0)+len;}
const top=Object.entries(byPkg).sort((a,b)=>b[1]-a[1]);
fs.writeFileSync(process.argv[2]+"/composition-top.tsv","total rendered: "+total+" B\n"+top.slice(0,30).map(([p,s])=>`${p}\t${s}\t${(100*s/total).toFixed(1)}%`).join("\n")+"\n");
const fmt=n=>n.toLocaleString("en");
console.log(`| Build | bundle composition (rendered) | total ${fmt(total)} B · app source ${fmt(byPkg["(app source)"]||0)} B · top: ${top.filter(([p])=>p!=="(app source)").slice(0,8).map(([p,s])=>`${p} ${fmt(s)} B`).join(" · ")} |`);
' "$OUT/bundle-raw.json" "$OUT")
  else
    COMP_ROWS="| Build | bundle composition | visualizer FAILED — see visualizer.log |"
  fi
else
  echo "-- [3/4] composition skipped"
fi

# ---------- 4. Lighthouse ----------
echo "-- [4/4] lighthouse x$RUNS (headless, default simulated mobile throttling)"
LH_URL="$PERF_WEB${PERF_WEB_PATH:-/}"
for i in $(seq 1 "$RUNS"); do
  CHROME_PATH="$CHROME" npx --yes lighthouse@13 "$LH_URL" \
    --only-categories=performance --output=json --output-path="$OUT/lh-run$i.json" \
    --chrome-flags="--headless=new --no-sandbox" --quiet || fail "lighthouse run $i failed"
  echo "   run $i done"
done
LH_ROWS=$(OUT="$OUT" node -e '
const fs=require("fs");const files=process.argv.slice(2);const apiRe=new RegExp(process.argv[1]||"/api/");
const runs=files.map(f=>{const r=JSON.parse(fs.readFileSync(f,"utf8"));const a=r.audits;
 const net=(a["network-requests"]?.details?.items)||[];const api={};
 for(const it of net){const m=(it.url||"").match(apiRe);if(m){const k=(it.url||"").replace(/^https?:\/\/[^/]+/,"").split("?")[0];api[k]=(api[k]||0)+1;}}
 const reqBytes=net.reduce((s,i)=>s+(i.transferSize||0),0);
 const biggest=net.slice().sort((x,y)=>(y.transferSize||0)-(x.transferSize||0))[0]||{};
 const fonts=net.filter(i=>i.resourceType==="Font"||/\.woff2?($|\?)/.test(i.url||"")).length;
 const lt=(a["long-tasks"]?.details?.items)||[];
 const uj=a["unused-javascript"]?.details;const ujW=(uj?.items||[]).reduce((s,i)=>s+(i.wastedBytes||0),0);const ujT=(uj?.items||[]).reduce((s,i)=>s+(i.totalBytes||0),0);
 const uc=a["unused-css-rules"]?.details;const ucW=(uc?.items||[]).reduce((s,i)=>s+(i.wastedBytes||0),0);const ucT=(uc?.items||[]).reduce((s,i)=>s+(i.totalBytes||0),0);
 return {score:r.categories.performance.score,fcp:a["first-contentful-paint"].numericValue,lcp:a["largest-contentful-paint"].numericValue,
  si:a["speed-index"].numericValue,tbt:a["total-blocking-time"].numericValue,tti:a["interactive"]?.numericValue||0,cls:a["cumulative-layout-shift"].numericValue,
  bootup:a["bootup-time"].numericValue,ltN:lt.length,ltMax:Math.max(0,...lt.map(t=>t.duration||0)),reqN:net.length,reqBytes,
  bigUrl:(biggest.url||"").replace(/^https?:\/\/[^/]+/,""),bigBytes:biggest.transferSize||0,fonts,ujW,ujT,ujMs:Math.round(uj?.overallSavingsMs||0),ucW,ucT,
  dupes:Object.entries(api).filter(([,n])=>n>1).map(([u,n])=>`${u} x${n}`)};});
runs.sort((x,y)=>x.lcp-y.lcp);const m=runs[Math.floor(runs.length/2)];
fs.writeFileSync(process.env.OUT+"/lh-summary.json",JSON.stringify({median:m,all:runs},null,1));
const n=x=>Math.round(x).toLocaleString("en");const f=x=>x.toLocaleString("en");
console.log([
`| Lighthouse (lab, mobile) | performance score | ${m.score} (all runs: ${runs.map(r=>r.score).join(" / ")}) |`,
`| Lighthouse | FCP / LCP / Speed Index | ${n(m.fcp)} / ${n(m.lcp)} / ${n(m.si)} ms |`,
`| Lighthouse | TBT / TTI / CLS | ${n(m.tbt)} ms / ${n(m.tti)} ms / ${m.cls.toFixed(3)} |`,
`| Lighthouse | bootup / long tasks | ${n(m.bootup)} ms · ${m.ltN} long tasks, worst ${n(m.ltMax)} ms |`,
`| Lighthouse | unused JS | ${f(m.ujW)} of ${f(m.ujT)} B (${m.ujT?(100*m.ujW/m.ujT).toFixed(1):"n/a"}%), est. ${f(m.ujMs)} ms savings |`,
`| Lighthouse | unused CSS | ${f(m.ucW)} of ${f(m.ucT)} B (${m.ucT?(100*m.ucW/m.ucT).toFixed(1):"n/a"}% of transferred) |`,
`| Network | full load (LH network log) | ${f(m.reqBytes)} B / ${m.reqN} requests |`,
`| Network | largest request | ${m.bigUrl} — ${f(m.bigBytes)} B (${m.reqBytes?(100*m.bigBytes/m.reqBytes).toFixed(0):0}% of full load) |`,
`| Network | duplicate API calls on load | ${m.dupes.join("; ")||"none"} |`,
`| Network | fonts fetched | ${m.fonts} (vs emitted count in Build rows) |`].join("\n"));
' "${PERF_API_PATTERN:-/api/}" "$OUT"/lh-run*.json)

# ---------- report ----------
{
  echo "## FE metrics (initial load / build) — label: $LABEL"
  echo
  echo "Captured $STAMP · HEAD $GIT_HEAD · $LH_URL · lighthouse@13 headless, default simulated mobile throttling · $RUNS run(s), median-by-LCP reported"
  echo
  echo "| Layer | Metric | Value |"
  echo "|---|---|---|"
  echo "$LH_ROWS"
  echo "| Network | bytes to first render | $FIRST_RENDER_BYTES B (HTML ${HTML_PROBE[1]} + JS $JS_WIRE + CSS $CSS_WIRE + external $EXT_WIRE) |"
  echo "| Network | root element before JS | \`$(mdsafe <<<"$ROOT_DIV")\` |"
  echo "| Network | index.html Cache-Control | ${HTML_PROBE[3]} |"
  echo "| Ruled out | static serving (compressed + 1y immutable on all JS/CSS) | $STATIC_OK |"
  [[ -n "$BUILD_ROWS" ]] && echo "$BUILD_ROWS"
  [[ -n "$COMP_ROWS" ]] && echo "$COMP_ROWS"
  echo
  echo "Artifacts: served-assets.tsv · lh-run*.json · lh-summary.json$( [[ -n "$BUILD_ROWS" ]] && echo ' · build.log' )$( [[ -n "$COMP_ROWS" ]] && echo ' · bundle-raw.json · composition-top.tsv' )"
} > "$MD"

echo; cat "$MD"; echo; echo "== written: $MD =="
rebuild_dashboard
