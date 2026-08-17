#!/usr/bin/env python3
"""
Pull GSC Search Analytics over the last 12 ISO weeks (Mon-anchored), aggregate
weekly buckets per query and per page, apply the shared noise filter, compute
half-over-half trend signals (rising / falling / new / lost / stable), and
write three artefacts under --out-dir.

Window: rolling — end defaults to today - 3 days (GSC ~2-day lag plus one
safety day), start defaults to 12 ISO weeks before that. Override with
--start / --end (ISO dates).

Required env:
  GSC_SITE_URL                     GSC property, e.g. "sc-domain:example.com"
  GSC_KEY_FILE or
  GOOGLE_APPLICATION_CREDENTIALS   service-account JSON key path

Site taxonomy comes from the shared site config (seo_site_config.py):
  --site-config PATH   or env SEO_SITE_CONFIG, default ./seo-site-config.json

Outputs (default --out-dir ./seo-reports/trends/):
  - queries-12w.csv
  - pages-12w.csv
  - _trend-summary.json   (machine-readable summary; also echoed on stdout)
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import sys
from collections import defaultdict
from dataclasses import dataclass, field
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

DEFAULT_WEEKS = 12
END_LAG_DAYS = 3  # GSC ~2-day lag plus one safety day

# Floors: queries need less volume than pages to be interesting.
QUERY_MIN_IMPRESSIONS = 10
PAGE_MIN_IMPRESSIONS = 30


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(description="12-week GSC trend analysis.")
    ap.add_argument("--site-config", default="", help="path to seo-site-config.json")
    ap.add_argument(
        "--out-dir", default="./seo-reports/trends",
        help="output directory (default ./seo-reports/trends)",
    )
    ap.add_argument(
        "--core-csv", default="./seo-reports/semantic-core.csv",
        help="focused-core CSV used to flag in_focused_core",
    )
    ap.add_argument(
        "--start", default="",
        help="window start (ISO date); default derived from --end and --weeks",
    )
    ap.add_argument(
        "--end", default="",
        help=f"window end (ISO date); default today - {END_LAG_DAYS} days",
    )
    ap.add_argument("--weeks", type=int, default=DEFAULT_WEEKS)
    return ap.parse_args()


# ---------------------------------------------------------------------------
# Week bucketing
# ---------------------------------------------------------------------------


def monday_of(d: date) -> date:
    """Return the Monday of the ISO week that contains d."""
    return d - timedelta(days=d.weekday())


def build_week_buckets(end_date: date, weeks: int) -> list[tuple[date, date, str]]:
    """Return list of (week_start_monday, week_end_sunday, label) for the
    `weeks` Mon-anchored ISO weeks ending in the week that contains end_date."""
    end_monday = monday_of(end_date)
    first_monday = end_monday - timedelta(weeks=weeks - 1)
    buckets = []
    for i in range(weeks):
        ws = first_monday + timedelta(weeks=i)
        we = ws + timedelta(days=6)
        buckets.append((ws, we, ws.isoformat()))
    return buckets


def bucket_for_date(d: date, buckets: list[tuple[date, date, str]]) -> str | None:
    for ws, we, label in buckets:
        if ws <= d <= we:
            return label
    return None


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


def fetch_paged(service: Any, site_url: str, body: dict[str, Any]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    start_row = 0
    while True:
        body_paged = dict(body)
        body_paged["startRow"] = start_row
        body_paged["rowLimit"] = ROW_LIMIT
        resp = (
            service.searchanalytics()
            .query(siteUrl=site_url, body=body_paged)
            .execute()
        )
        batch = resp.get("rows", [])
        if not batch:
            break
        out.extend(batch)
        if len(batch) < ROW_LIMIT:
            break
        start_row += ROW_LIMIT
    return out


# ---------------------------------------------------------------------------
# Trend math (half-over-half)
# ---------------------------------------------------------------------------


@dataclass
class WeeklySeries:
    impressions: dict[str, int] = field(default_factory=dict)
    clicks: dict[str, int] = field(default_factory=dict)
    pos_num: dict[str, float] = field(default_factory=dict)  # weighted-position numerator

    def add(self, week_label: str, impr: int, clk: int, pos: float) -> None:
        self.impressions[week_label] = self.impressions.get(week_label, 0) + impr
        self.clicks[week_label] = self.clicks.get(week_label, 0) + clk
        self.pos_num[week_label] = self.pos_num.get(week_label, 0.0) + pos * impr


def split_halves(series: WeeklySeries, week_labels: list[str]) -> dict[str, Any]:
    half = len(week_labels) // 2
    first = week_labels[:half]
    second = week_labels[half:]

    def agg(weeks: list[str]) -> tuple[int, int, float]:
        impr = sum(series.impressions.get(w, 0) for w in weeks)
        clk = sum(series.clicks.get(w, 0) for w in weeks)
        pos_num = sum(series.pos_num.get(w, 0.0) for w in weeks)
        pos = (pos_num / impr) if impr else 0.0
        return impr, clk, pos

    h1_impr, h1_clk, h1_pos = agg(first)
    h2_impr, h2_clk, h2_pos = agg(second)

    total_impr = h1_impr + h2_impr
    total_clk = h1_clk + h2_clk
    total_pos = (
        sum(series.pos_num.values()) / total_impr if total_impr else 0.0
    )

    if h1_impr > 0:
        delta_impr_pct = (h2_impr - h1_impr) / h1_impr * 100.0
    elif h2_impr > 0:
        delta_impr_pct = float("inf")
    else:
        delta_impr_pct = 0.0

    if h1_pos > 0 and h2_pos > 0:
        delta_pos = h2_pos - h1_pos
    else:
        delta_pos = 0.0

    return {
        "h1_impressions": h1_impr,
        "h1_clicks": h1_clk,
        "h1_position": h1_pos,
        "h2_impressions": h2_impr,
        "h2_clicks": h2_clk,
        "h2_position": h2_pos,
        "total_impressions": total_impr,
        "total_clicks": total_clk,
        "avg_position": total_pos,
        "delta_impressions_pct": delta_impr_pct,
        "delta_position": delta_pos,
    }


def label_trend(stats: dict[str, Any]) -> str:
    """5-label taxonomy with asymmetric, volume-gated rules:
    new/lost need meaningful volume on one side; rising needs both a big
    impression jump AND a position signal; falling triggers on either a big
    impression drop OR a big position slide."""
    h1 = stats["h1_impressions"]
    h2 = stats["h2_impressions"]
    h2_pos = stats["h2_position"]
    delta_pct = stats["delta_impressions_pct"]
    delta_pos = stats["delta_position"]

    # New: only appeared in second half
    if h1 == 0 and h2 >= 30:
        return "new"
    # Lost: visible first half, evaporated second half
    if h1 >= 30 and h2 <= 10:
        return "lost"

    # Need both halves with traffic for rising/falling
    if h1 == 0 or h2 == 0:
        return "stable"

    rising = (delta_pct >= 25.0) and (delta_pos <= -2.0 or h2_pos <= 10.0)
    falling = (delta_pct <= -25.0) or (delta_pos >= 5.0)

    if rising:
        return "rising"
    if falling:
        return "falling"
    return "stable"


# ---------------------------------------------------------------------------
# Focused-core lookup
# ---------------------------------------------------------------------------


def load_focused_core(core_csv: str) -> dict[str, dict[str, str]]:
    """Return dict[query_lower] -> { target_url, cluster, priority }."""
    out: dict[str, dict[str, str]] = {}
    if not core_csv:
        return out
    path = Path(core_csv)
    if not path.exists():
        print(
            f"WARN: focused-core CSV not found: {path} — in_focused_core "
            "will be false everywhere.",
            file=sys.stderr,
        )
        return out
    with path.open(encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            out[(row.get("query") or "").lower()] = {
                "target_url": row.get("target_url") or "",
                "cluster": row.get("cluster") or "",
                "priority": row.get("priority") or "",
            }
    return out


# ---------------------------------------------------------------------------
# Row records
# ---------------------------------------------------------------------------


@dataclass
class QueryRow:
    query: str
    target_url: str
    cluster: str
    total_impressions: int
    total_clicks: int
    avg_position: float
    h1_impressions: int
    h2_impressions: int
    delta_impressions_pct: float
    h1_position: float
    h2_position: float
    delta_position: float
    trend: str
    in_focused_core: bool


@dataclass
class PageRow:
    page: str
    cluster: str
    total_impressions: int
    total_clicks: int
    avg_position: float
    h1_impressions: int
    h2_impressions: int
    delta_impressions_pct: float
    h1_position: float
    h2_position: float
    delta_position: float
    trend: str


def fmt_pct(v: float) -> str:
    if v == float("inf"):
        return "inf"
    if v == float("-inf"):
        return "-inf"
    return f"{v:.1f}"


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


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

    # Rolling window: end = today - lag; start = end - N ISO weeks.
    end_date = (
        date.fromisoformat(args.end)
        if args.end
        else date.today() - timedelta(days=END_LAG_DAYS)
    )
    if args.start:
        start_date = date.fromisoformat(args.start)
        weeks = ((monday_of(end_date) - monday_of(start_date)).days // 7) + 1
        if weeks < 2:
            print("ERROR: window must span at least 2 weeks.", file=sys.stderr)
            return 1
    else:
        weeks = args.weeks

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    queries_csv = out_dir / "queries-12w.csv"
    pages_csv = out_dir / "pages-12w.csv"
    summary_json = out_dir / "_trend-summary.json"

    week_buckets = build_week_buckets(end_date, weeks)
    week_labels = [b[2] for b in week_buckets]
    pull_start = week_buckets[0][0].isoformat()

    # The API call must not run past the last complete data day: end_date may
    # be earlier than the final bucket's Sunday.
    api_end = min(end_date, week_buckets[-1][1])
    api_end_s = api_end.isoformat()

    print(f"GSC property: {site_url}", file=sys.stderr)
    print(f"Window: {pull_start} -> {api_end_s}  ({weeks} weeks)", file=sys.stderr)

    service = build_service(key_file)

    # ----- pass 1: query x date -----
    print("Pulling query x date ...", file=sys.stderr)
    q_rows = fetch_paged(service, site_url, {
        "startDate": pull_start,
        "endDate": api_end_s,
        "dimensions": ["query", "date"],
        "type": "web",
    })
    print(f"  raw rows: {len(q_rows)}", file=sys.stderr)

    # ----- pass 2: page x date -----
    print("Pulling page x date ...", file=sys.stderr)
    p_rows = fetch_paged(service, site_url, {
        "startDate": pull_start,
        "endDate": api_end_s,
        "dimensions": ["page", "date"],
        "type": "web",
    })
    print(f"  raw rows: {len(p_rows)}", file=sys.stderr)

    # ----- aggregate query x week -----
    query_series: dict[str, WeeklySeries] = defaultdict(WeeklySeries)
    for row in q_rows:
        keys = row.get("keys") or []
        if len(keys) < 2:
            continue
        query, date_s = keys[0], keys[1]
        try:
            d = date.fromisoformat(date_s)
        except ValueError:
            continue
        wk = bucket_for_date(d, week_buckets)
        if wk is None:
            continue
        impr = int(row.get("impressions", 0) or 0)
        clk = int(row.get("clicks", 0) or 0)
        pos = float(row.get("position", 0.0) or 0.0)
        if impr <= 0:
            continue
        query_series[query].add(wk, impr, clk, pos)

    # ----- aggregate page x week -----
    page_series: dict[str, WeeklySeries] = defaultdict(WeeklySeries)
    for row in p_rows:
        keys = row.get("keys") or []
        if len(keys) < 2:
            continue
        page, date_s = keys[0], keys[1]
        try:
            d = date.fromisoformat(date_s)
        except ValueError:
            continue
        wk = bucket_for_date(d, week_buckets)
        if wk is None:
            continue
        impr = int(row.get("impressions", 0) or 0)
        clk = int(row.get("clicks", 0) or 0)
        pos = float(row.get("position", 0.0) or 0.0)
        if impr <= 0:
            continue
        page_series[page].add(wk, impr, clk, pos)

    print(f"Distinct queries (any imp): {len(query_series)}", file=sys.stderr)
    print(f"Distinct pages   (any imp): {len(page_series)}", file=sys.stderr)

    focused_core = load_focused_core(args.core_csv)

    # We need a target_url per query: pick the page where this query had the
    # most impressions. One extra aggregated pull (no date dim) keyed by
    # [query, page] over the whole window keeps API usage low.
    print("Pulling query x page (attribution) ...", file=sys.stderr)
    qp_rows = fetch_paged(service, site_url, {
        "startDate": pull_start,
        "endDate": api_end_s,
        "dimensions": ["query", "page"],
        "type": "web",
    })
    print(f"  raw rows: {len(qp_rows)}", file=sys.stderr)

    best_page_for_query: dict[str, tuple[str, int]] = {}
    for row in qp_rows:
        keys = row.get("keys") or []
        if len(keys) < 2:
            continue
        q, p = keys[0], keys[1]
        impr = int(row.get("impressions", 0) or 0)
        if impr <= 0:
            continue
        prev = best_page_for_query.get(q)
        if prev is None or impr > prev[1]:
            best_page_for_query[q] = (p, impr)

    # ----- query post-processing: noise filter + thresholds + trend -----
    query_rows: list[QueryRow] = []
    dropped_noise = 0
    dropped_threshold = 0
    for q, series in query_series.items():
        stats = split_halves(series, week_labels)
        if stats["total_impressions"] < QUERY_MIN_IMPRESSIONS:
            dropped_threshold += 1
            continue
        if cfg.classify_noise(q):
            dropped_noise += 1
            continue
        target_url = best_page_for_query.get(q, ("", 0))[0]
        cluster = ""
        if target_url:
            try:
                cluster = cfg.cluster_for_path(urlparse(target_url).path or "/")
            except Exception:
                cluster = ""
        trend = label_trend(stats)
        query_rows.append(QueryRow(
            query=q,
            target_url=target_url,
            cluster=cluster,
            total_impressions=stats["total_impressions"],
            total_clicks=stats["total_clicks"],
            avg_position=round(stats["avg_position"], 2),
            h1_impressions=stats["h1_impressions"],
            h2_impressions=stats["h2_impressions"],
            delta_impressions_pct=stats["delta_impressions_pct"],
            h1_position=round(stats["h1_position"], 2) if stats["h1_position"] else 0.0,
            h2_position=round(stats["h2_position"], 2) if stats["h2_position"] else 0.0,
            delta_position=round(stats["delta_position"], 2),
            trend=trend,
            in_focused_core=q.lower() in focused_core,
        ))

    # ----- page post-processing -----
    page_rows: list[PageRow] = []
    for p, series in page_series.items():
        stats = split_halves(series, week_labels)
        if stats["total_impressions"] < PAGE_MIN_IMPRESSIONS:
            continue
        try:
            path = urlparse(p).path or "/"
        except Exception:
            path = "/"
        cluster = cfg.cluster_for_path(path)
        trend = label_trend(stats)
        page_rows.append(PageRow(
            page=p,
            cluster=cluster,
            total_impressions=stats["total_impressions"],
            total_clicks=stats["total_clicks"],
            avg_position=round(stats["avg_position"], 2),
            h1_impressions=stats["h1_impressions"],
            h2_impressions=stats["h2_impressions"],
            delta_impressions_pct=stats["delta_impressions_pct"],
            h1_position=round(stats["h1_position"], 2) if stats["h1_position"] else 0.0,
            h2_position=round(stats["h2_position"], 2) if stats["h2_position"] else 0.0,
            delta_position=round(stats["delta_position"], 2),
            trend=trend,
        ))

    # Sort: focused-core first (queries), then trend (rising/falling/new/lost
    # before stable), then total impressions desc.
    trend_order = {"rising": 0, "falling": 1, "new": 2, "lost": 3, "stable": 4}
    query_rows.sort(key=lambda r: (
        not r.in_focused_core, trend_order.get(r.trend, 9), -r.total_impressions
    ))
    page_rows.sort(key=lambda r: (
        trend_order.get(r.trend, 9), -r.total_impressions
    ))

    # ----- write CSVs -----
    with queries_csv.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow([
            "query", "target_url", "cluster",
            "total_impressions", "total_clicks", "avg_position",
            "first_half_impressions", "second_half_impressions",
            "delta_impressions_pct",
            "first_half_position", "second_half_position", "delta_position",
            "trend", "in_focused_core",
        ])
        for r in query_rows:
            w.writerow([
                r.query, r.target_url, r.cluster,
                r.total_impressions, r.total_clicks, f"{r.avg_position:.2f}",
                r.h1_impressions, r.h2_impressions,
                fmt_pct(r.delta_impressions_pct),
                f"{r.h1_position:.2f}", f"{r.h2_position:.2f}", f"{r.delta_position:.2f}",
                r.trend, "true" if r.in_focused_core else "false",
            ])

    with pages_csv.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow([
            "page", "cluster",
            "total_impressions", "total_clicks", "avg_position",
            "first_half_impressions", "second_half_impressions",
            "delta_impressions_pct",
            "first_half_position", "second_half_position", "delta_position",
            "trend",
        ])
        for r in page_rows:
            w.writerow([
                r.page, r.cluster,
                r.total_impressions, r.total_clicks, f"{r.avg_position:.2f}",
                r.h1_impressions, r.h2_impressions,
                fmt_pct(r.delta_impressions_pct),
                f"{r.h1_position:.2f}", f"{r.h2_position:.2f}", f"{r.delta_position:.2f}",
                r.trend,
            ])

    # ----- summary JSON -----
    def trend_count(rows, attr_filter=None):
        c: dict[str, int] = defaultdict(int)
        for r in rows:
            if attr_filter and not attr_filter(r):
                continue
            c[r.trend] += 1
        return dict(c)

    core_queries = [r for r in query_rows if r.in_focused_core]

    # Aggregate trajectory of the focused core (impression-weighted).
    core_h1_impr = sum(r.h1_impressions for r in core_queries)
    core_h2_impr = sum(r.h2_impressions for r in core_queries)
    core_delta_pct = (
        (core_h2_impr - core_h1_impr) / core_h1_impr * 100.0 if core_h1_impr else 0.0
    )
    core_h1_pos_w = sum(r.h1_position * r.h1_impressions for r in core_queries if r.h1_impressions)
    core_h1_pos_d = sum(r.h1_impressions for r in core_queries if r.h1_impressions)
    core_h2_pos_w = sum(r.h2_position * r.h2_impressions for r in core_queries if r.h2_impressions)
    core_h2_pos_d = sum(r.h2_impressions for r in core_queries if r.h2_impressions)
    core_h1_pos = core_h1_pos_w / core_h1_pos_d if core_h1_pos_d else 0.0
    core_h2_pos = core_h2_pos_w / core_h2_pos_d if core_h2_pos_d else 0.0

    # Per-cluster impression totals (page-level) for a quick landscape view.
    cluster_impressions: dict[str, int] = defaultdict(int)
    for r in page_rows:
        cluster_impressions[r.cluster] += r.total_impressions

    summary = {
        "property": site_url,
        "site_config": cfg.loaded_from or None,
        "window_start": pull_start,
        "window_end": api_end_s,
        "weeks": weeks,
        "raw_query_rows": len(q_rows),
        "raw_page_rows": len(p_rows),
        "raw_qp_rows": len(qp_rows),
        "queries": {
            "in_scope_after_filter": len(query_rows),
            "dropped_noise": dropped_noise,
            "dropped_threshold": dropped_threshold,
            "trend_counts": trend_count(query_rows),
            "trend_counts_focused_core": trend_count(query_rows, lambda r: r.in_focused_core),
        },
        "pages": {
            "in_scope_after_filter": len(page_rows),
            "trend_counts": trend_count(page_rows),
        },
        "focused_core_trajectory": {
            "queries": len(core_queries),
            "h1_impressions": core_h1_impr,
            "h2_impressions": core_h2_impr,
            "delta_impressions_pct": round(core_delta_pct, 1),
            "h1_avg_position": round(core_h1_pos, 2),
            "h2_avg_position": round(core_h2_pos, 2),
            "delta_position": round(core_h2_pos - core_h1_pos, 2),
        },
        "cluster_impressions": dict(
            sorted(cluster_impressions.items(), key=lambda kv: -kv[1])
        ),
    }
    with summary_json.open("w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, default=str)

    print(json.dumps(summary, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
