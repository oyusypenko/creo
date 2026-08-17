#!/usr/bin/env python3
"""
Detection phase of the GSC auto-fix loop (see docs/autofix.md).

Pulls two signals from Google Search Console and emits a structured issues
report for the fix phase:

1. URL Inspection sweep over a budgeted sample:
     - every URL in the auto-fix ledger (re-verify prior fixes)
     - URLs from manual GSC UI CSV exports (--exports-dir)
     - curated URL lists (--urls-file, repeatable or comma-separated)
     - a deterministic rotating sample of the live sitemap (rotation keyed by
       ISO week so consecutive runs cover different slices without state)
2. Site-level Search Analytics week-over-week anomaly check (informational).

Also fetches the sitemap (--sitemap-url or SEO_SITEMAP_URL) and flags it when
the URL count drops below the expected floor (catches silent-truncation
failures where the sitemap builder loses its data source at build time).

Quota: URL Inspection allows 2,000 requests/day and 600/min per property.
Default budget here is 300 per run with a 0.2s inter-request delay.

Requires google-api-python-client (see requirements.txt):
  python3 gsc_autofix_detect.py --budget 300 --out ./gsc-autofix-report.json

Env:
  GSC_SITE_URL                    REQUIRED. GSC property, e.g.
                                  "sc-domain:example.com" or
                                  "https://example.com/"
  SEO_SITEMAP_URL                 sitemap URL (or use --sitemap-url)
  SEO_SITEMAP_MIN_URLS            sitemap URL-count floor (or --sitemap-min-urls)

Auth (first match wins):
  GSC_SERVICE_ACCOUNT_JSON        service-account JSON *content* (cloud runs)
  GSC_KEY_FILE                    path to service-account JSON
  GOOGLE_APPLICATION_CREDENTIALS  path to service-account JSON
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
import urllib.request
from datetime import date, timedelta
from pathlib import Path
from typing import Any

try:
    from google.oauth2 import service_account
    from googleapiclient.discovery import build
except ImportError:  # pragma: no cover
    service_account = None
    build = None

SCOPES = ["https://www.googleapis.com/auth/webmasters.readonly"]

INSPECT_DELAY_SEC = 0.2  # 600/min quota -> stay well under

# pageFetchState values that mean "the page itself is broken" (fixable class)
BROKEN_FETCH_STATES = {
    "NOT_FOUND",
    "SOFT_404",
    "SERVER_ERROR",
    "REDIRECT_ERROR",
    "BLOCKED_ROBOTS_TXT",
    "BLOCKED_4XX",
    "ACCESS_DENIED",
    "INTERNAL_CRAWL_ERROR",
}

# WoW site-level click drop (fractional) that flags an anomaly
ANOMALY_DROP_THRESHOLD = 0.4


def require_site_url() -> str:
    site = os.environ.get("GSC_SITE_URL")
    if not site:
        raise RuntimeError(
            "GSC_SITE_URL is required, e.g. 'sc-domain:example.com' or "
            "'https://example.com/'"
        )
    return site


def resolve_credentials():
    if service_account is None or build is None:
        raise RuntimeError(
            "google-api-python-client is not installed. "
            "Install the gsc-analyzer requirements first: "
            "pip install -r requirements.txt"
        )
    inline = os.environ.get("GSC_SERVICE_ACCOUNT_JSON")
    if inline:
        info = json.loads(inline)
        return service_account.Credentials.from_service_account_info(
            info, scopes=SCOPES
        )
    key_file = os.environ.get("GSC_KEY_FILE") or os.environ.get(
        "GOOGLE_APPLICATION_CREDENTIALS"
    )
    if not key_file:
        raise RuntimeError(
            "no credentials: set GSC_SERVICE_ACCOUNT_JSON (JSON content), "
            "GSC_KEY_FILE, or GOOGLE_APPLICATION_CREDENTIALS (key file path)"
        )
    if not Path(key_file).exists():
        raise RuntimeError(f"GSC key file missing: {key_file}")
    return service_account.Credentials.from_service_account_file(
        key_file, scopes=SCOPES
    )


def read_url_list(path: Path) -> list[str]:
    if not path.exists():
        return []
    out: list[str] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            out.append(line)
    return out


def load_ledger_urls(ledger_path: Path) -> list[str]:
    if not ledger_path.exists():
        return []
    data = json.loads(ledger_path.read_text(encoding="utf-8"))
    return [e["url"] for e in data.get("entries", []) if e.get("url")]


def load_gsc_export_urls(exports_dir: Path) -> list[str]:
    """URLs from manual GSC UI CSV exports (column named 'URL' or first col)."""
    if not exports_dir.is_dir():
        return []
    import csv as _csv

    out: list[str] = []
    for path in sorted(exports_dir.glob("*.csv")):
        with path.open(encoding="utf-8-sig") as f:
            reader = _csv.reader(f)
            header = next(reader, None)
            if header is None:
                continue
            try:
                col = [h.strip().lower() for h in header].index("url")
            except ValueError:
                col = 0
            for row in reader:
                if len(row) > col and row[col].startswith("http"):
                    out.append(row[col].strip())
    return out


def fetch_sitemap_urls(
    sitemap_url: str | None, min_urls: int
) -> tuple[list[str], dict[str, Any]]:
    """Return (urls, sitemap_health). Never raises — health carries errors."""
    if not sitemap_url:
        return [], {
            "url": None,
            "ok": True,
            "skipped": True,
            "urlCount": 0,
            "note": "no sitemap URL configured (--sitemap-url / SEO_SITEMAP_URL)",
        }
    health: dict[str, Any] = {"url": sitemap_url, "ok": False, "urlCount": 0}
    try:
        req = urllib.request.Request(
            sitemap_url, headers={"User-Agent": "gsc-autofix-detect/1.0"}
        )
        with urllib.request.urlopen(req, timeout=60) as resp:
            health["httpStatus"] = resp.status
            body = resp.read().decode("utf-8", errors="replace")
    except Exception as exc:
        health["error"] = str(exc)
        return [], health
    locs = re.findall(r"<loc>\s*(.*?)\s*</loc>", body)
    health["urlCount"] = len(locs)
    health["ok"] = health.get("httpStatus") == 200 and len(locs) >= min_urls
    if len(locs) < min_urls:
        health["warning"] = (
            f"sitemap has {len(locs)} URLs, expected >= {min_urls} "
            "— possible silent truncation (check the sitemap builder's "
            "data source)"
        )
    return locs, health


def rotating_sample(urls: list[str], count: int) -> list[str]:
    """Deterministic slice rotated by ISO week so runs cover new ground."""
    if not urls or count <= 0:
        return []
    week = date.today().isocalendar()[1]
    start = (week * count) % len(urls)
    doubled = urls + urls
    return doubled[start : start + min(count, len(urls))]


def inspect_url(svc: Any, site_url: str, url: str) -> dict[str, Any]:
    resp = (
        svc.urlInspection()
        .index()
        .inspect(body={"inspectionUrl": url, "siteUrl": site_url})
        .execute()
    )
    return resp.get("inspectionResult", {})


def classify(url: str, result: dict[str, Any]) -> list[dict[str, Any]]:
    """Map one inspection result to zero or more issue records."""
    issues: list[dict[str, Any]] = []
    idx = result.get("indexStatusResult", {})
    fetch_state = idx.get("pageFetchState", "")
    coverage = idx.get("coverageState", "")
    verdict = idx.get("verdict", "")
    google_canonical = idx.get("googleCanonical")
    user_canonical = idx.get("userCanonical")
    last_crawl = idx.get("lastCrawlTime")

    base = {
        "url": url,
        "coverageState": coverage,
        "verdict": verdict,
        "lastCrawlTime": last_crawl,
    }

    if fetch_state in BROKEN_FETCH_STATES:
        issues.append({**base, "issueType": f"fetch:{fetch_state}"})

    if idx.get("indexingState") in (
        "BLOCKED_BY_META_TAG",
        "BLOCKED_BY_HTTP_HEADER",
    ):
        issues.append({**base, "issueType": "noindex"})

    if idx.get("robotsTxtState") == "DISALLOWED":
        issues.append({**base, "issueType": "robots-disallowed"})

    if (
        google_canonical
        and user_canonical
        and google_canonical != user_canonical
    ):
        issues.append(
            {
                **base,
                "issueType": "canonical-mismatch",
                "googleCanonical": google_canonical,
                "userCanonical": user_canonical,
            }
        )

    rich = result.get("richResultsResult", {})
    if rich.get("verdict") in ("FAIL", "PARTIAL"):
        detected = rich.get("detectedItems", [])
        issues.append(
            {
                **base,
                "issueType": "rich-results",
                "richResultsDetail": detected,
            }
        )

    # Informational (not auto-fixable): indexing-state observations the fix
    # phase uses only to update the ledger, never to edit code. Substring
    # matching is unsafe here ("Crawled - currently not indexed" contains
    # "indexed"), so compare against the known-good coverage states.
    OK_COVERAGE = {
        "Submitted and indexed",
        "Indexed, not submitted in sitemap",
    }
    if not issues and coverage and coverage not in OK_COVERAGE:
        issues.append({**base, "issueType": f"coverage:{coverage}", "informational": True})

    return issues


def search_analytics_anomaly(creds, site_url: str) -> dict[str, Any]:
    """Compare site-level clicks for the last two complete weeks."""
    svc = build("webmasters", "v3", credentials=creds, cache_discovery=False)
    safe_end = date.today() - timedelta(days=3)  # GSC ~2-day lag + margin
    this_start = safe_end - timedelta(days=6)
    prev_end = this_start - timedelta(days=1)
    prev_start = prev_end - timedelta(days=6)

    def total_clicks(start: date, end: date) -> int:
        resp = (
            svc.searchanalytics()
            .query(
                siteUrl=site_url,
                body={
                    "startDate": start.isoformat(),
                    "endDate": end.isoformat(),
                    "dimensions": [],
                    "type": "web",
                },
            )
            .execute()
        )
        rows = resp.get("rows", [])
        return int(rows[0]["clicks"]) if rows else 0

    cur = total_clicks(this_start, safe_end)
    prev = total_clicks(prev_start, prev_end)
    drop = ((prev - cur) / prev) if prev > 0 else 0.0
    return {
        "currentWeekClicks": cur,
        "previousWeekClicks": prev,
        "dropFraction": round(drop, 3),
        # floor of 50 clicks/week: below that a WoW halving is noise
        "anomaly": prev >= 50 and drop >= ANOMALY_DROP_THRESHOLD,
        "window": {
            "current": [this_start.isoformat(), safe_end.isoformat()],
            "previous": [prev_start.isoformat(), prev_end.isoformat()],
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--budget", type=int, default=300,
                        help="max URL inspections this run (quota: 2000/day)")
    parser.add_argument("--out", default="./gsc-autofix-report.json",
                        help="output JSON path (not committed)")
    parser.add_argument("--ledger", default="./seo-autofix-ledger.json",
                        help="path to the auto-fix ledger JSON")
    parser.add_argument("--exports-dir", default="./gsc-exports",
                        help="directory of GSC UI CSV exports (Pages report)")
    parser.add_argument("--urls-file", action="append", default=[],
                        help="curated URL list file (repeatable or "
                             "comma-separated; one URL per line, # comments)")
    parser.add_argument("--sitemap-url",
                        default=os.environ.get("SEO_SITEMAP_URL"),
                        help="sitemap URL (default: SEO_SITEMAP_URL env; "
                             "omit to skip the sitemap check)")
    # Default floor of 1 only asserts "non-empty". Set a real floor for your
    # site (e.g. 90% of its normal URL count) via --sitemap-min-urls or
    # SEO_SITEMAP_MIN_URLS to catch silent truncation.
    parser.add_argument("--sitemap-min-urls", type=int,
                        default=int(os.environ.get("SEO_SITEMAP_MIN_URLS", "1")),
                        help="sitemap URL-count floor (default: "
                             "SEO_SITEMAP_MIN_URLS env or 1)")
    parser.add_argument("--skip-analytics", action="store_true",
                        help="skip the Search Analytics anomaly check")
    args = parser.parse_args()

    site_url = require_site_url()
    creds = resolve_credentials()
    inspect_svc = build(
        "searchconsole", "v1", credentials=creds, cache_discovery=False
    )

    sitemap_urls, sitemap_health = fetch_sitemap_urls(
        args.sitemap_url, args.sitemap_min_urls
    )
    print(
        f"sitemap: {sitemap_health.get('urlCount', 0)} URLs "
        f"(ok={sitemap_health['ok']})",
        file=sys.stderr,
    )

    curated_files = [
        Path(p.strip())
        for spec in args.urls_file
        for p in spec.split(",")
        if p.strip()
    ]

    # Sample assembly: ledger first (always re-verified), then UI exports and
    # curated lists, then a rotating sitemap slice with whatever budget remains.
    seen: set[str] = set()
    sample: list[str] = []
    sources: list[list[str]] = [
        load_ledger_urls(Path(args.ledger)),
        load_gsc_export_urls(Path(args.exports_dir)),
    ]
    sources.extend(read_url_list(path) for path in curated_files)
    for source in sources:
        for url in source:
            if url not in seen:
                seen.add(url)
                sample.append(url)
    remaining = args.budget - len(sample)
    if remaining > 0:
        for url in rotating_sample(
            [u for u in sitemap_urls if u not in seen], remaining
        ):
            seen.add(url)
            sample.append(url)
    sample = sample[: args.budget]
    print(f"inspecting {len(sample)} URLs (budget {args.budget})", file=sys.stderr)

    issues: list[dict[str, Any]] = []
    inspected = 0
    errors: list[dict[str, str]] = []
    for url in sample:
        try:
            result = inspect_url(inspect_svc, site_url, url)
            issues.extend(classify(url, result))
        except Exception as exc:  # quota/transient — record and continue
            errors.append({"url": url, "error": str(exc)})
            if "quota" in str(exc).lower() or "429" in str(exc):
                print("quota hit — stopping inspection sweep", file=sys.stderr)
                break
        inspected += 1
        if inspected % 25 == 0:
            print(f"  ...{inspected}/{len(sample)}", file=sys.stderr)
        time.sleep(INSPECT_DELAY_SEC)

    analytics = None
    if not args.skip_analytics:
        try:
            analytics = search_analytics_anomaly(creds, site_url)
        except Exception as exc:
            analytics = {"error": str(exc)}

    actionable = [i for i in issues if not i.get("informational")]
    report = {
        "generatedAt": None,  # stamped by the orchestrating session
        "site": site_url,
        "inspected": inspected,
        "budget": args.budget,
        "sitemapHealth": sitemap_health,
        "searchAnalytics": analytics,
        "issues": issues,
        "actionableCount": len(actionable),
        "inspectionErrors": errors,
    }
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print(
        json.dumps(
            {
                "out": str(out_path),
                "inspected": inspected,
                "issuesTotal": len(issues),
                "actionable": len(actionable),
                "sitemapOk": sitemap_health["ok"],
                "analyticsAnomaly": (analytics or {}).get("anomaly"),
                "errors": len(errors),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
