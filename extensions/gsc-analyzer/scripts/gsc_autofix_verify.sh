#!/usr/bin/env bash
# Post-deploy verification for the GSC auto-fix loop (see docs/autofix.md).
#
# Usage:
#   BASE_URL=https://example.com gsc_autofix_verify.sh [options]
#   gsc_autofix_verify.sh --base https://example.com \
#       [--canaries seo-canaries.txt] [--expectations fixes.txt]
#
# Options:
#   --base <url>          site base URL, no trailing slash (or BASE_URL env)
#   --canaries <file>     canary expectations file, run every time; see
#                         templates/seo-canaries.example.txt for the format
#   --expectations <file> per-run fixed-URL expectations (same format)
#
# Expectations file format, one check per line:
#   <url> <expected_final_url>
# Blank lines and lines starting with # are skipped; a line with a URL but no
# expected final URL counts as a failure (malformed). Each URL is fetched
# following redirects (max 3). The check passes when the final status is 200,
# the final URL matches expected_final_url exactly, and the chain used at most
# 2 redirects (Google penalizes longer chains).
#
# Regardless of files given, two invariants always run:
#   - robots.txt is 200 and contains no blanket "Disallow: /"
#   - sitemap.xml is 200 and has >= SEO_SITEMAP_MIN_URLS <loc> entries
#     (default 1, i.e. only "non-empty" — set a real floor for your site to
#     catch silent truncation)
#
# Exit code = number of failures (0 = all pass).

set -u

BASE="${BASE_URL:-}"
SITEMAP_MIN_URLS="${SEO_SITEMAP_MIN_URLS:-1}"
CANARIES_FILE=""
EXPECTATIONS_FILE=""
MAX_HOPS=2
CURL_OPTS=(--silent --max-time 30 -o /dev/null)

while [[ $# -gt 0 ]]; do
  case "$1" in
    --base)         BASE="$2"; shift 2 ;;
    --canaries)     CANARIES_FILE="$2"; shift 2 ;;
    --expectations) EXPECTATIONS_FILE="$2"; shift 2 ;;
    *)
      echo "unknown argument: $1" >&2
      exit 64
      ;;
  esac
done

if [[ -z "$BASE" ]]; then
  echo "error: base URL required (--base https://example.com or BASE_URL env)" >&2
  exit 64
fi
BASE="${BASE%/}"

failures=0
passes=0

check_chain() {
  local url="$1" expected_final="$2"
  local out
  out=$(curl "${CURL_OPTS[@]}" -L --max-redirs 3 \
    -w "%{http_code} %{num_redirects} %{url_effective}" "$url") || {
    echo "FAIL  $url  (curl error)"
    failures=$((failures + 1))
    return
  }
  local code hops final
  read -r code hops final <<<"$out"
  if [[ "$code" == "200" && "$final" == "$expected_final" && "$hops" -le "$MAX_HOPS" ]]; then
    echo "PASS  $url -> $final (${hops} hops)"
    passes=$((passes + 1))
  else
    echo "FAIL  $url -> status=$code hops=$hops final=$final expected=$expected_final"
    failures=$((failures + 1))
  fi
}

run_expectations_file() {
  local file="$1"
  while read -r url expected_final; do
    [[ -z "$url" || "$url" == \#* ]] && continue
    if [[ -z "${expected_final:-}" ]]; then
      echo "FAIL  malformed line for $url (need: <url> <expected_final_url>)"
      failures=$((failures + 1))
      continue
    fi
    check_chain "$url" "$expected_final"
  done < "$file"
}

if [[ -n "$CANARIES_FILE" ]]; then
  echo "== Canary suite ($CANARIES_FILE) =="
  run_expectations_file "$CANARIES_FILE"
fi

echo "== robots.txt =="
robots=$(curl --silent --max-time 30 -w "\n%{http_code}" "$BASE/robots.txt")
robots_code=$(echo "$robots" | tail -n1)
robots_body=$(echo "$robots" | sed '$d')
if [[ "$robots_code" == "200" ]] && ! echo "$robots_body" | grep -qE '^Disallow: /$'; then
  echo "PASS  robots.txt 200, no blanket disallow"
  passes=$((passes + 1))
else
  echo "FAIL  robots.txt status=$robots_code or contains blanket 'Disallow: /'"
  failures=$((failures + 1))
fi

echo "== sitemap.xml =="
sitemap_tmp=$(mktemp)
sitemap_code=$(curl --silent --max-time 120 -o "$sitemap_tmp" -w "%{http_code}" "$BASE/sitemap.xml")
loc_count=$(grep -o "<loc>" "$sitemap_tmp" | wc -l | tr -d ' ')
rm -f "$sitemap_tmp"
if [[ "$sitemap_code" == "200" && "$loc_count" -ge "$SITEMAP_MIN_URLS" ]]; then
  echo "PASS  sitemap.xml 200 with $loc_count URLs (floor $SITEMAP_MIN_URLS)"
  passes=$((passes + 1))
else
  echo "FAIL  sitemap.xml status=$sitemap_code urls=$loc_count (floor $SITEMAP_MIN_URLS)"
  failures=$((failures + 1))
fi

if [[ -n "$EXPECTATIONS_FILE" ]]; then
  echo "== Fixed URLs from $EXPECTATIONS_FILE =="
  run_expectations_file "$EXPECTATIONS_FILE"
fi

echo
echo "Result: $passes passed, $failures failed"
exit "$failures"
