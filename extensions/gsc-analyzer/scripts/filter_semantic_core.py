#!/usr/bin/env python3
"""
Split a semantic-core pull into a raw file and a focused core:
  - <raw-out>   all rows + is_noise column (preserved for audits)
  - <out>       filtered focused core, re-prioritised with the P0-P3 rubric

The noise classifier, priority rubric, and opportunity score come from the
shared site config (seo_site_config.py). Without a site config the noise
filter is disabled and the rubric degrades to impressions/position only.

Usage:
  python3 filter_semantic_core.py \
      [--in ./seo-reports/semantic-core.csv] \
      [--raw-out ./seo-reports/semantic-core.raw.csv] \
      [--out ./seo-reports/semantic-core.csv] \
      [--site-config ./seo-site-config.json]

All paths resolve relative to the current working directory (not the script
location). The default --out overwrites the input in place, keeping the raw
file as the pre-filter record.
"""

from __future__ import annotations

import argparse
import csv
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from seo_site_config import SiteConfig, load_config  # noqa: E402


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(description="Filter a semantic-core CSV.")
    ap.add_argument(
        "--in", dest="in_path", default="./seo-reports/semantic-core.csv",
        help="input CSV from pull_semantic_core.py",
    )
    ap.add_argument(
        "--raw-out", default="./seo-reports/semantic-core.raw.csv",
        help="raw output (all rows + is_noise column)",
    )
    ap.add_argument(
        "--out", default="./seo-reports/semantic-core.csv",
        help="focused-core output (noise dropped, re-prioritised)",
    )
    ap.add_argument("--site-config", default="", help="path to seo-site-config.json")
    ap.add_argument(
        "--top", type=int, default=25,
        help="number of top P0+P1 rows to print (default 25)",
    )
    return ap.parse_args()


def main() -> int:
    args = parse_args()
    cfg: SiteConfig = load_config(args.site_config)

    src = Path(args.in_path)
    if not src.exists():
        print(f"ERROR: input CSV missing: {src}", file=sys.stderr)
        return 1

    with src.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        original_fieldnames = list(reader.fieldnames or [])

    if not rows:
        print("ERROR: input CSV has no rows.", file=sys.stderr)
        return 1

    # Tag each row.
    for row in rows:
        row["is_noise"] = "true" if cfg.classify_noise(row["query"]) else "false"

    # Write raw with is_noise column (preserved pre-filter record).
    raw_out = Path(args.raw_out)
    raw_out.parent.mkdir(parents=True, exist_ok=True)
    raw_fields = original_fieldnames + ["is_noise"]
    with raw_out.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=raw_fields)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)

    # Build focused core.
    focused = [r for r in rows if r["is_noise"] == "false"]

    # Re-rank priorities with the P0-P3 rubric.
    for row in focused:
        row["priority"] = cfg.assign_priority(
            row["cluster"],
            int(row["impressions_90d"]),
            float(row["current_position"]),
        )

    def score(row: dict) -> float:
        return cfg.opportunity_score(
            int(row["impressions_90d"]), float(row["current_position"])
        )

    # Sort: priority P0 -> P3, then by opportunity score desc.
    priority_order = {"P0": 0, "P1": 1, "P2": 2, "P3": 3}
    focused.sort(
        key=lambda r: (priority_order.get(r["priority"], 9), -score(r))
    )

    # Strip is_noise from focused output (always false), keep original schema.
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=original_fieldnames)
        writer.writeheader()
        for row in focused:
            writer.writerow({k: row[k] for k in original_fieldnames})

    # ---------- stats ----------
    total = len(rows)
    noise = sum(1 for r in rows if r["is_noise"] == "true")
    kept = total - noise

    cluster_counts: Counter = Counter(r["cluster"] for r in focused)
    priority_counts: Counter = Counter(r["priority"] for r in focused)

    print(f"Input rows:    {total}")
    print(f"Noise dropped: {noise} ({100 * noise / total:.1f}%)")
    print(f"Focused core:  {kept} ({100 * kept / total:.1f}%)")
    print()
    print("Focused core by cluster:")
    for c, n in cluster_counts.most_common():
        print(f"  {c}: {n}")
    print()
    print("Focused core by priority:")
    for p in ("P0", "P1", "P2", "P3"):
        print(f"  {p}: {priority_counts.get(p, 0)}")

    # Top-N P0+P1 by opportunity score.
    p0p1 = [r for r in focused if r["priority"] in ("P0", "P1")]
    p0p1.sort(key=lambda r: -score(r))
    print()
    print(f"Top {args.top} P0+P1 by opportunity score (impressions / position):")
    for r in p0p1[: args.top]:
        print(
            f"  [{r['priority']}] [{r['cluster']:>16}] "
            f"pos={float(r['current_position']):>6.2f} "
            f"imp={r['impressions_90d']:>4} clk={r['clicks_90d']:>3} "
            f"| {r['query']}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
