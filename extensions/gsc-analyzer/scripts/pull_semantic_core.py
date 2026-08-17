#!/usr/bin/env python3
"""
Pull GSC Search Analytics for the last N days (default 90), cluster rows by
the per-project route taxonomy, assign a first-pass priority, and write a
semantic-core CSV.

Required env:
  GSC_SITE_URL                     GSC property, e.g. "sc-domain:example.com"
                                   or "https://example.com/"
  GSC_KEY_FILE or
  GOOGLE_APPLICATION_CREDENTIALS   path to a service-account JSON key with
                                   read access to the property

Site taxonomy comes from the shared site config (see seo_site_config.py):
  --site-config PATH   or env SEO_SITE_CONFIG, default ./seo-site-config.json

Outputs:
  - CSV at --out (default ./seo-reports/semantic-core.csv)
  - machine-readable JSON summary on stdout (progress goes to stderr)

Follow up with filter_semantic_core.py to drop noise queries and re-rank
with the P0-P3 rubric.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
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

sys.path.insert(0, str(Path(__file__).resolve().parent))
from seo_site_config import SiteConfig, load_config  # noqa: E402

SCOPES = ["https://www.googleapis.com/auth/webmasters.readonly"]
ROW_LIMIT = 25000


@dataclass
class Row:
    cluster: str
    query: str
    target_url: str
    locale: str
    intent: str
    priority: str
    current_position: float
    impressions_90d: int
    clicks_90d: int
    ctr: float
    source: str


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    ap.add_argument("--site-config", default="", help="path to seo-site-config.json")
    ap.add_argument(
        "--out", default="./seo-reports/semantic-core.csv",
        help="output CSV path (default ./seo-reports/semantic-core.csv)",
    )
    ap.add_argument("--window-days", type=int, default=90)
    ap.add_argument("--min-impressions", type=int, default=10)
    return ap.parse_args()


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


def fetch_all(service: Any, site_url: str, start: str, end: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    start_row = 0
    while True:
        body = {
            "startDate": start,
            "endDate": end,
            "dimensions": ["query", "page", "country"],
            "rowLimit": ROW_LIMIT,
            "startRow": start_row,
            "type": "web",
        }
        resp = service.searchanalytics().query(siteUrl=site_url, body=body).execute()
        batch = resp.get("rows", [])
        if not batch:
            break
        rows.extend(batch)
        if len(batch) < ROW_LIMIT:
            break
        start_row += ROW_LIMIT
    return rows


def assign_priorities(records: list[Row]) -> list[Row]:
    """Two-pass priority: P1 = top-impression query per (cluster, url);
    P2 = page-1 queries with real volume; P3 = the rest."""
    by_url: dict[tuple[str, str], list[Row]] = defaultdict(list)
    for r in records:
        by_url[(r.cluster, r.target_url)].append(r)

    p1_set: set[tuple[str, str, str]] = set()
    for (_cluster, _url), bucket in by_url.items():
        bucket.sort(key=lambda x: x.impressions_90d, reverse=True)
        if bucket:
            top = bucket[0]
            p1_set.add((top.cluster, top.query, top.target_url))

    out: list[Row] = []
    for r in records:
        key = (r.cluster, r.query, r.target_url)
        if key in p1_set:
            r.priority = "P1"
        elif 1.0 <= r.current_position <= 10.0 and r.impressions_90d >= 100:
            r.priority = "P2"
        else:
            r.priority = "P3"
        out.append(r)
    return out


def main() -> int:
    args = parse_args()
    cfg: SiteConfig = load_config(args.site_config)

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

    end = date.today() - timedelta(days=2)  # GSC has ~2-day lag
    start = end - timedelta(days=args.window_days - 1)
    start_s = start.isoformat()
    end_s = end.isoformat()

    print(f"GSC property: {site_url}", file=sys.stderr)
    print(f"Date window: {start_s} -> {end_s}", file=sys.stderr)

    service = build_service(key_file)
    raw = fetch_all(service, site_url, start_s, end_s)
    print(f"Fetched rows: {len(raw)}", file=sys.stderr)

    # Aggregate by (query, page) summing across countries. Position is
    # impression-weighted; CTR is computed from the summed totals.
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
        a = agg[(query, page)]
        a["clicks"] += clicks
        a["impressions"] += impr
        # Weighted average for position (weight = impressions).
        a["pos_num"] += pos * impr

    records: list[Row] = []
    for (query, page), v in agg.items():
        impressions = int(v["impressions"])
        if impressions < args.min_impressions:
            continue
        clicks = int(v["clicks"])
        ctr = (clicks / impressions) if impressions else 0.0
        position = (v["pos_num"] / impressions) if impressions else 0.0
        path = urlparse(page).path or "/"
        records.append(
            Row(
                cluster=cfg.cluster_for_path(path),
                query=query,
                target_url=page,
                locale=cfg.locale_for_path(path),
                intent=cfg.classify_intent(query),
                priority="P3",  # placeholder, set in next pass
                current_position=round(position, 2),
                impressions_90d=impressions,
                clicks_90d=clicks,
                ctr=round(ctr, 4),
                source=f"gsc-{args.window_days}d",
            )
        )

    records = assign_priorities(records)

    # Sort: cluster asc, priority asc (P1 first), impressions desc.
    pri_order = {"P1": 0, "P2": 1, "P3": 2}
    records.sort(
        key=lambda r: (r.cluster, pri_order.get(r.priority, 9), -r.impressions_90d)
    )

    out_csv = Path(args.out)
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    with out_csv.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow([
            "cluster", "query", "target_url", "locale", "intent", "priority",
            "current_position", "impressions_90d", "clicks_90d", "ctr",
            "source",
        ])
        for r in records:
            w.writerow([
                r.cluster, r.query, r.target_url, r.locale, r.intent,
                r.priority, f"{r.current_position:.2f}", r.impressions_90d,
                r.clicks_90d, f"{r.ctr:.4f}", r.source,
            ])

    # Summary stats for the calling agent / workflow.
    cluster_counts: dict[str, int] = defaultdict(int)
    cluster_impr: dict[str, int] = defaultdict(int)
    cluster_avg_pos_num: dict[str, float] = defaultdict(float)
    cluster_avg_pos_den: dict[str, int] = defaultdict(int)
    for r in records:
        cluster_counts[r.cluster] += 1
        cluster_impr[r.cluster] += r.impressions_90d
        cluster_avg_pos_num[r.cluster] += r.current_position * r.impressions_90d
        cluster_avg_pos_den[r.cluster] += r.impressions_90d

    p1 = [r for r in records if r.priority == "P1"]
    p1.sort(key=lambda r: r.impressions_90d, reverse=True)

    summary = {
        "property": site_url,
        "site_config": cfg.loaded_from or None,
        "start_date": start_s,
        "end_date": end_s,
        "raw_rows": len(raw),
        "csv_rows": len(records),
        "unique_queries": len({r.query for r in records}),
        "unique_pages": len({r.target_url for r in records}),
        "out_file": str(out_csv),
        "clusters": [
            {
                "cluster": c,
                "rows": cluster_counts[c],
                "impressions": cluster_impr[c],
                "avg_position": round(
                    cluster_avg_pos_num[c] / cluster_avg_pos_den[c], 2
                )
                if cluster_avg_pos_den[c]
                else None,
            }
            for c in sorted(cluster_counts)
        ],
        "top_p1": [
            {
                "cluster": r.cluster,
                "query": r.query,
                "target_url": r.target_url,
                "position": r.current_position,
                "impressions": r.impressions_90d,
                "clicks": r.clicks_90d,
            }
            for r in p1[:10]
        ],
    }
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
