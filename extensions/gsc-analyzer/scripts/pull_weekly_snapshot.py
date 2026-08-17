#!/usr/bin/env python3
"""
Pull a weekly GSC (and optionally Bing Webmaster Tools) snapshot for the most
recent ISO week (Mon-Sun) that satisfies the GSC ~2-day reporting lag and
write it to <out-dir>/<YYYY-MM-DD>.csv where the filename date is the Sunday
end-date of the week.

Output schema mirrors the semantic-core CSV plus:
  * week_start_iso        Monday of the snapshot week (ISO date)
  * week_end_iso          Sunday of the snapshot week (ISO date)
  * is_in_focused_core    "true" if the (query, target_url) pair is in the
                          focused-core CSV (--core-csv)
  * source                "gsc-weekly" or "bing-weekly"

Idempotent: if the file for the same Sunday already exists it is overwritten
(GSC backfills late-arriving data for ~2 days; the latest pull always wins).

Required env:
  GSC_SITE_URL                     GSC property, e.g. "sc-domain:example.com"
  GSC_KEY_FILE or
  GOOGLE_APPLICATION_CREDENTIALS   service-account JSON key path

Optional env:
  BING_WEBMASTER_API_KEY           enables the Bing GetQueryStats merge
  BING_SITE_URL                    Bing site URL, e.g. "https://example.com"
                                   (required when the Bing key is set)

Site taxonomy comes from the shared site config (seo_site_config.py):
  --site-config PATH   or env SEO_SITE_CONFIG, default ./seo-site-config.json

Machine JSON summary goes to stdout; progress goes to stderr.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import re
import sys
from collections import defaultdict
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

# Network deps loaded lazily so --help / py_compile don't require them.
try:
    from google.oauth2 import service_account
    from googleapiclient.discovery import build
except ImportError:  # pragma: no cover
    service_account = None
    build = None

try:
    import requests
except ImportError:  # pragma: no cover
    requests = None

sys.path.insert(0, str(Path(__file__).resolve().parent))
from seo_site_config import SiteConfig, load_config  # noqa: E402

SCOPES = ["https://www.googleapis.com/auth/webmasters.readonly"]

# Same aggregation as the 90d pull, but a weekly bucket is small, so the
# floor drops to 1 impression — the historical floor of 10 hides
# week-over-week rank movement of low-volume terms we still want to monitor.
MIN_IMPRESSIONS = 1
ROW_LIMIT = 25000

BING_API_KEY_ENV = "BING_WEBMASTER_API_KEY"
BING_BASE_URL = (
    "https://ssl.bing.com/webmaster/api.svc/json/GetQueryStats"
    "?siteUrl={site}&apikey={key}"
)


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(description="Weekly GSC (+Bing) rank snapshot.")
    ap.add_argument("--site-config", default="", help="path to seo-site-config.json")
    ap.add_argument(
        "--out-dir", default="./seo-reports/rank-history",
        help="snapshot output directory (default ./seo-reports/rank-history)",
    )
    ap.add_argument(
        "--core-csv", default="",
        help="focused-core CSV for is_in_focused_core tagging "
             "(optional; tagging skipped when absent)",
    )
    ap.add_argument(
        "--lag-days", type=int, default=2,
        help="GSC reporting lag in days (default 2)",
    )
    return ap.parse_args()


# ---------------------------------------------------------------------------
# Week math
# ---------------------------------------------------------------------------


def previous_complete_week(today: date, gsc_lag_days: int = 2) -> tuple[date, date]:
    """
    Return (monday, sunday) of the most recent ISO week (Mon-Sun) whose data
    is complete given the GSC reporting lag. Today's date and the lag are
    explicit so unit tests can pin them.
    """
    safe_today = today - timedelta(days=gsc_lag_days)
    # Sunday is weekday() == 6.
    days_since_sunday = (safe_today.weekday() + 1) % 7
    sunday = safe_today - timedelta(days=days_since_sunday)
    monday = sunday - timedelta(days=6)
    return monday, sunday


# ---------------------------------------------------------------------------
# Focused-core lookup
# ---------------------------------------------------------------------------


def load_focused_core(core_csv: str) -> set[tuple[str, str]]:
    """Return set of (query_lower, target_url) tuples present in the core."""
    out: set[tuple[str, str]] = set()
    if not core_csv:
        return out
    path = Path(core_csv)
    if not path.exists():
        print(
            f"WARN: focused-core CSV not found: {path} — core tagging skipped.",
            file=sys.stderr,
        )
        return out
    with path.open(encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            q = (row.get("query") or "").lower()
            u = row.get("target_url") or ""
            if q and u:
                out.add((q, u))
    return out


# ---------------------------------------------------------------------------
# GSC plumbing
# ---------------------------------------------------------------------------


def resolve_gsc_key_file() -> Path | None:
    explicit = os.environ.get("GSC_KEY_FILE")
    if explicit:
        return Path(explicit)
    google_default = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
    if google_default:
        return Path(google_default)
    return None


def build_service(key_file: Path):
    if service_account is None or build is None:
        raise RuntimeError(
            "google-api-python-client is not installed. Install with: "
            "pip install google-api-python-client google-auth"
        )
    creds = service_account.Credentials.from_service_account_file(
        str(key_file), scopes=SCOPES
    )
    return build("webmasters", "v3", credentials=creds, cache_discovery=False)


def fetch_gsc(service: Any, site_url: str, start: str, end: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    start_row = 0
    while True:
        body = {
            "startDate": start,
            "endDate": end,
            "dimensions": ["query", "page"],
            "rowLimit": ROW_LIMIT,
            "startRow": start_row,
            "type": "web",
        }
        resp = (
            service.searchanalytics()
            .query(siteUrl=site_url, body=body)
            .execute()
        )
        batch = resp.get("rows", [])
        if not batch:
            break
        rows.extend(batch)
        if len(batch) < ROW_LIMIT:
            break
        start_row += ROW_LIMIT
    return rows


# ---------------------------------------------------------------------------
# Bing plumbing (best-effort, optional)
# ---------------------------------------------------------------------------


def fetch_bing(api_key: str, week_start: date, week_end: date) -> list[dict[str, Any]]:
    """
    Pull Bing Webmaster Tools GetQueryStats for the week. Bing's API returns
    daily aggregates for the last 6 months; we sum across the 7 days inside
    [week_start, week_end].

    Note: Bing's Webmaster API surface area changes; this function uses
    GetQueryStats which returns query-level aggregates only (no page join).
    """
    if requests is None:
        print("Bing: requests not installed, skipping Bing pull.", file=sys.stderr)
        return []

    site = os.environ.get("BING_SITE_URL", "").strip()
    if not site:
        print(
            "Bing: BING_SITE_URL not set — skipping Bing pull "
            "(set it to e.g. https://example.com).",
            file=sys.stderr,
        )
        return []
    url = BING_BASE_URL.format(site=site, key=api_key)

    try:
        resp = requests.get(url, timeout=30)
        resp.raise_for_status()
    except Exception as exc:
        print(f"Bing: GetQueryStats failed: {exc}", file=sys.stderr)
        return []

    try:
        payload = resp.json()
    except Exception as exc:
        print(f"Bing: response not JSON: {exc}", file=sys.stderr)
        return []

    items = payload.get("d") or payload.get("Items") or []
    out: list[dict[str, Any]] = []
    for item in items:
        # Bing daily fields (varies by SDK version): Query, Impressions,
        # Clicks, Position, Date.
        q = item.get("Query") or item.get("query")
        d_raw = item.get("Date") or item.get("date")
        if not q or not d_raw:
            continue
        # Bing returns dates as "/Date(1700000000000)/" — best-effort parse.
        m = re.match(r"/Date\((\d+)\)/", str(d_raw))
        if m:
            ts_ms = int(m.group(1))
            d = date.fromtimestamp(ts_ms / 1000.0)
        else:
            try:
                d = date.fromisoformat(str(d_raw)[:10])
            except Exception:
                continue
        if not (week_start <= d <= week_end):
            continue
        out.append({
            "query": q,
            "impressions": int(item.get("Impressions") or 0),
            "clicks": int(item.get("Clicks") or 0),
            "position": float(item.get("Position") or 0.0),
        })
    return out


# ---------------------------------------------------------------------------
# Row record + aggregation
# ---------------------------------------------------------------------------


@dataclass
class Row:
    cluster: str
    query: str
    target_url: str
    locale: str
    intent: str
    priority: str
    current_position: float
    impressions: int
    clicks: int
    ctr: float
    source: str
    week_start_iso: str
    week_end_iso: str
    is_in_focused_core: bool


def aggregate_gsc_rows(
    cfg: SiteConfig,
    raw: list[dict[str, Any]],
    week_start: date,
    week_end: date,
    focused_core: set[tuple[str, str]],
) -> list[Row]:
    agg: dict[tuple[str, str], dict[str, float]] = defaultdict(
        lambda: {"clicks": 0.0, "impressions": 0.0, "pos_num": 0.0}
    )
    for row in raw:
        keys = row.get("keys") or []
        if len(keys) < 2:
            continue
        query, page = keys[0], keys[1]
        impr = float(row.get("impressions", 0) or 0)
        clicks = float(row.get("clicks", 0) or 0)
        pos = float(row.get("position", 0) or 0)
        if impr <= 0:
            continue
        a = agg[(query, page)]
        a["clicks"] += clicks
        a["impressions"] += impr
        a["pos_num"] += pos * impr

    out: list[Row] = []
    for (query, page), v in agg.items():
        impressions = int(v["impressions"])
        if impressions < MIN_IMPRESSIONS:
            continue
        if cfg.classify_noise(query):
            continue
        clicks = int(v["clicks"])
        ctr = (clicks / impressions) if impressions else 0.0
        position = (v["pos_num"] / impressions) if impressions else 0.0
        path = urlparse(page).path or "/"
        out.append(Row(
            cluster=cfg.cluster_for_path(path),
            query=query,
            target_url=page,
            locale=cfg.locale_for_path(path),
            intent=cfg.classify_intent(query),
            priority="",  # weekly snapshots inherit the focused-core flag instead
            current_position=round(position, 2),
            impressions=impressions,
            clicks=clicks,
            ctr=round(ctr, 4),
            source="gsc-weekly",
            week_start_iso=week_start.isoformat(),
            week_end_iso=week_end.isoformat(),
            is_in_focused_core=(query.lower(), page) in focused_core,
        ))
    return out


def aggregate_bing_rows(
    cfg: SiteConfig,
    bing_raw: list[dict[str, Any]],
    week_start: date,
    week_end: date,
    focused_core: set[tuple[str, str]],
) -> list[Row]:
    """
    Bing's GetQueryStats is query-only (no page dimension), so we attribute
    the row to the empty target URL. Joiners can lift the GSC target URL
    later.
    """
    agg: dict[str, dict[str, float]] = defaultdict(
        lambda: {"clicks": 0.0, "impressions": 0.0, "pos_num": 0.0, "days": 0.0}
    )
    for item in bing_raw:
        q = item["query"]
        impr = float(item.get("impressions") or 0)
        clk = float(item.get("clicks") or 0)
        pos = float(item.get("position") or 0)
        if impr <= 0:
            continue
        a = agg[q]
        a["clicks"] += clk
        a["impressions"] += impr
        a["pos_num"] += pos * impr
        a["days"] += 1

    out: list[Row] = []
    core_queries = {qc for qc, _ in focused_core}
    for q, v in agg.items():
        impressions = int(v["impressions"])
        if impressions < MIN_IMPRESSIONS:
            continue
        if cfg.classify_noise(q):
            continue
        clicks = int(v["clicks"])
        ctr = (clicks / impressions) if impressions else 0.0
        position = (v["pos_num"] / impressions) if impressions else 0.0
        # Bing has no page dim, so we can't compute a precise focused-core
        # match. Match by query alone.
        out.append(Row(
            cluster="",
            query=q,
            target_url="",
            locale="",
            intent=cfg.classify_intent(q),
            priority="",
            current_position=round(position, 2),
            impressions=impressions,
            clicks=clicks,
            ctr=round(ctr, 4),
            source="bing-weekly",
            week_start_iso=week_start.isoformat(),
            week_end_iso=week_end.isoformat(),
            is_in_focused_core=q.lower() in core_queries,
        ))
    return out


def write_csv(rows: list[Row], out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow([
            "cluster", "query", "target_url", "locale", "intent", "priority",
            "current_position", "impressions", "clicks", "ctr", "source",
            "week_start_iso", "week_end_iso", "is_in_focused_core",
        ])
        for r in rows:
            w.writerow([
                r.cluster,
                r.query,
                r.target_url,
                r.locale,
                r.intent,
                r.priority,
                f"{r.current_position:.2f}",
                r.impressions,
                r.clicks,
                f"{r.ctr:.4f}",
                r.source,
                r.week_start_iso,
                r.week_end_iso,
                "true" if r.is_in_focused_core else "false",
            ])


def main() -> int:
    args = parse_args()
    cfg = load_config(args.site_config)

    site_url = os.environ.get("GSC_SITE_URL", "").strip()
    if not site_url:
        print(
            "ERROR: GSC_SITE_URL env var is required "
            "(e.g. sc-domain:example.com).",
            file=sys.stderr,
        )
        return 1

    key_file = resolve_gsc_key_file()
    if key_file is None:
        print(
            "ERROR: set GSC_KEY_FILE or GOOGLE_APPLICATION_CREDENTIALS to a "
            "service-account JSON key path.",
            file=sys.stderr,
        )
        return 1
    if not key_file.exists():
        print(f"ERROR: GSC key file missing: {key_file}", file=sys.stderr)
        return 1

    week_start, week_end = previous_complete_week(
        date.today(), gsc_lag_days=args.lag_days
    )
    out_path = Path(args.out_dir) / f"{week_end.isoformat()}.csv"

    print(f"GSC property: {site_url}", file=sys.stderr)
    print(f"Week: {week_start.isoformat()} -> {week_end.isoformat()}", file=sys.stderr)
    print(f"Output: {out_path}", file=sys.stderr)
    if out_path.exists():
        print("  (overwriting existing snapshot — GSC backfill wins)", file=sys.stderr)

    focused_core = load_focused_core(args.core_csv)
    print(f"Focused core entries loaded: {len(focused_core)}", file=sys.stderr)

    # GSC pull (mandatory)
    service = build_service(key_file)
    raw_gsc = fetch_gsc(service, site_url, week_start.isoformat(), week_end.isoformat())
    print(f"GSC raw rows: {len(raw_gsc)}", file=sys.stderr)
    rows: list[Row] = aggregate_gsc_rows(cfg, raw_gsc, week_start, week_end, focused_core)
    print(
        f"GSC rows after filter (min imp={MIN_IMPRESSIONS}, noise dropped): {len(rows)}",
        file=sys.stderr,
    )

    # Bing pull (optional)
    bing_key = os.environ.get(BING_API_KEY_ENV)
    if not bing_key:
        print("Bing: skipping — BING_WEBMASTER_API_KEY not set.", file=sys.stderr)
    else:
        raw_bing = fetch_bing(bing_key, week_start, week_end)
        print(f"Bing raw rows (in-week): {len(raw_bing)}", file=sys.stderr)
        bing_rows = aggregate_bing_rows(cfg, raw_bing, week_start, week_end, focused_core)
        print(f"Bing rows after filter: {len(bing_rows)}", file=sys.stderr)
        rows.extend(bing_rows)

    # Sort: focused-core first, then impressions DESC.
    rows.sort(
        key=lambda r: (not r.is_in_focused_core, -r.impressions, r.query)
    )

    write_csv(rows, out_path)

    summary = {
        "site": site_url,
        "site_config": cfg.loaded_from or None,
        "week_start": week_start.isoformat(),
        "week_end": week_end.isoformat(),
        "out_file": str(out_path),
        "total_rows": len(rows),
        "focused_core_rows": sum(1 for r in rows if r.is_in_focused_core),
        "gsc_rows": sum(1 for r in rows if r.source == "gsc-weekly"),
        "bing_rows": sum(1 for r in rows if r.source == "bing-weekly"),
        "bing_enabled": bool(bing_key),
    }
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
