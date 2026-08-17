#!/usr/bin/env python3
"""
Snapshot LLM citability for the focused commercial core (P0 / P1 queries in
the semantic-core CSV) using DataForSEO Live SERP endpoints.

For each query, run three checks:

  1. Google AI Overview SERP feature  — does the target domain appear in the
     AI Overview block?
  2. ChatGPT SERP                      — does the target domain appear in
     ChatGPT's web results?
  3. Perplexity SERP                   — does the target domain appear in
     Perplexity's citations?

Output:
  <out-dir>/<YYYY-MM-DD>.csv (date is run date, UTC)

Auth: env DATAFORSEO_LOGIN and DATAFORSEO_PASSWORD (HTTP Basic). If either
is missing the script exits with status 2 and prints a clear error so a CI
workflow surfaces the misconfig.

Target domain: SEO_TARGET_DOMAIN env var, falling back to target_domain in
the shared site config (--site-config / SEO_SITE_CONFIG /
./seo-site-config.json). Missing both also exits 2.

Cost: estimated as rows x 3 endpoints x an upper-bound per-call price and
logged on stderr BEFORE any API call is issued, so runaway spend is visible
up front.

Note: exact endpoint paths for ChatGPT and Perplexity may differ by account
plan. If your account does not have an endpoint enabled it will 404; this
script records the error per row and continues instead of retrying.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

try:
    import requests
except ImportError:  # pragma: no cover
    requests = None

sys.path.insert(0, str(Path(__file__).resolve().parent))
from seo_site_config import load_config  # noqa: E402

# DataForSEO base URL + endpoint paths.
DFS_BASE = "https://api.dataforseo.com"
ENDPOINT_AI_OVERVIEW = "/v3/serp/google/ai_overview/live/advanced"
ENDPOINT_CHATGPT = "/v3/serp/chatgpt/live/advanced"
ENDPOINT_PERPLEXITY = "/v3/serp/perplexity/live/advanced"

# Conservative price estimate per Live SERP call. AI surfaces run roughly
# $0.005-$0.015 / call; $0.01 is a defensive midpoint for cost logging.
# Treat as an estimate, not exact billing.
EST_PRICE_PER_CALL_USD = 0.01

REQUEST_TIMEOUT_S = 60
RETRY_ATTEMPTS = 2
RETRY_BACKOFF_S = 5


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(description="LLM citability snapshot via DataForSEO.")
    ap.add_argument("--site-config", default="", help="path to seo-site-config.json")
    ap.add_argument(
        "--core-csv", default="./seo-reports/semantic-core.csv",
        help="focused-core CSV (default ./seo-reports/semantic-core.csv)",
    )
    ap.add_argument(
        "--out-dir", default="./seo-reports/llm-visibility",
        help="output directory (default ./seo-reports/llm-visibility)",
    )
    ap.add_argument(
        "--location-code", type=int, default=2840,
        help="DataForSEO location code (default 2840 = United States)",
    )
    return ap.parse_args()


# ---------------------------------------------------------------------------
# Input loading
# ---------------------------------------------------------------------------


# Priority filter: P0 + P1 only by default. Override via env var, e.g.
# LLM_PRIORITY_FILTER="P0,P1,P2".
PRIORITY_FILTER = tuple(
    p.strip()
    for p in os.environ.get("LLM_PRIORITY_FILTER", "P0,P1").split(",")
    if p.strip()
)


@dataclass
class CoreQuery:
    query: str
    target_url: str
    priority: str
    cluster: str
    locale: str


def load_core_queries(core_csv: Path) -> list[CoreQuery]:
    if not core_csv.exists():
        raise FileNotFoundError(
            f"Focused core CSV missing: {core_csv}. "
            "Run pull_semantic_core.py (and filter_semantic_core.py) first."
        )
    out: list[CoreQuery] = []
    with core_csv.open(encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            pri = (row.get("priority") or "").strip()
            if PRIORITY_FILTER and pri not in PRIORITY_FILTER:
                continue
            q = (row.get("query") or "").strip()
            url = (row.get("target_url") or "").strip()
            if not q or not url:
                continue
            out.append(CoreQuery(
                query=q,
                target_url=url,
                priority=pri,
                cluster=(row.get("cluster") or "").strip(),
                locale=(row.get("locale") or "").strip(),
            ))
    # De-dup by (query, target_url) — sometimes the same query is rowed
    # twice in the focused core (different priority bands, etc.).
    seen: set[tuple[str, str]] = set()
    unique: list[CoreQuery] = []
    for cq in out:
        key = (cq.query.lower(), cq.target_url)
        if key in seen:
            continue
        seen.add(key)
        unique.append(cq)
    return unique


# ---------------------------------------------------------------------------
# DataForSEO client (thin)
# ---------------------------------------------------------------------------


@dataclass
class LlmCheckResult:
    cited: bool = False
    position: int | None = None
    error: str = ""
    raw_count: int = 0


def dfs_request(
    endpoint: str,
    payload: list[dict[str, Any]],
    auth: tuple[str, str],
) -> dict[str, Any]:
    if requests is None:
        raise RuntimeError("requests is not installed.")
    url = DFS_BASE + endpoint
    last_exc: Exception | None = None
    for attempt in range(RETRY_ATTEMPTS + 1):
        try:
            resp = requests.post(
                url,
                json=payload,
                auth=auth,
                timeout=REQUEST_TIMEOUT_S,
                headers={"Content-Type": "application/json"},
            )
            if resp.status_code == 404:
                # Endpoint not enabled on this account — surface as a
                # structured error rather than retrying.
                return {
                    "_http_status": 404,
                    "_error": (
                        f"endpoint {endpoint} returned 404 — likely not "
                        "available on your DataForSEO plan"
                    ),
                }
            resp.raise_for_status()
            return resp.json()
        except Exception as exc:
            last_exc = exc
            if attempt < RETRY_ATTEMPTS:
                time.sleep(RETRY_BACKOFF_S * (attempt + 1))
                continue
    return {"_http_status": -1, "_error": str(last_exc)}


def domain_matches(url: str, domain: str) -> bool:
    if not url:
        return False
    try:
        host = urlparse(url).netloc.lower()
    except Exception:
        return False
    if not host:
        # Sometimes citations come as bare domain strings.
        return domain in url.lower()
    return host == domain or host.endswith("." + domain)


# ---------------------------------------------------------------------------
# Result extractors — defensive against API shape drift.
# ---------------------------------------------------------------------------


def _iter_items(payload: dict[str, Any]) -> list[dict[str, Any]]:
    """Walk DataForSEO's tasks -> result -> items list, return [] on shape miss."""
    tasks = payload.get("tasks") or []
    if not tasks:
        return []
    result = (tasks[0].get("result") or [])
    if not result:
        return []
    items = result[0].get("items") or []
    return items if isinstance(items, list) else []


def extract_citation(payload: dict[str, Any], domain: str) -> LlmCheckResult:
    """
    Generic citation extractor: walks ``items`` and looks for either a
    ``url`` field or a ``links``/``references`` sub-list whose URL matches
    the target domain. Returns position = 1-based index of first hit.
    """
    if "_error" in payload:
        return LlmCheckResult(error=str(payload.get("_error")))

    items = _iter_items(payload)
    if not items:
        # Some endpoints (AI Overview) return inside a single "ai_overview"
        # block at the top of result[0].
        tasks = payload.get("tasks") or []
        if tasks:
            result = (tasks[0].get("result") or [])
            if result:
                ai = result[0].get("ai_overview") or {}
                refs = ai.get("references") or ai.get("links") or []
                for idx, ref in enumerate(refs, start=1):
                    u = ref.get("url") or ref.get("link") or ""
                    if domain_matches(u, domain):
                        return LlmCheckResult(
                            cited=True, position=idx, raw_count=len(refs),
                        )
                return LlmCheckResult(cited=False, raw_count=len(refs))
        return LlmCheckResult(cited=False, raw_count=0)

    cited_pos: int | None = None
    seen = 0
    for item in items:
        seen += 1
        # Top-level url
        u = item.get("url") or ""
        if domain_matches(u, domain) and cited_pos is None:
            cited_pos = item.get("rank_absolute") or seen
        # Nested citations (Perplexity / ChatGPT)
        for sub_key in ("links", "references", "citations", "sources"):
            subs = item.get(sub_key) or []
            for sidx, sub in enumerate(subs, start=1):
                if not isinstance(sub, dict):
                    continue
                su = sub.get("url") or sub.get("link") or ""
                if domain_matches(su, domain) and cited_pos is None:
                    cited_pos = sidx
        if cited_pos is not None:
            break

    return LlmCheckResult(
        cited=cited_pos is not None,
        position=cited_pos,
        raw_count=seen,
    )


# ---------------------------------------------------------------------------
# Per-query workflow
# ---------------------------------------------------------------------------


@dataclass
class RowOut:
    query: str
    target_url: str
    priority: str
    cluster: str
    locale: str
    ai_overview_cited: bool = False
    ai_overview_position: int | None = None
    ai_overview_error: str = ""
    chatgpt_cited: bool = False
    chatgpt_position: int | None = None
    chatgpt_error: str = ""
    perplexity_cited: bool = False
    perplexity_position: int | None = None
    perplexity_error: str = ""
    run_at_iso: str = ""


def build_payload(keyword: str, locale: str, location_code: int) -> list[dict[str, Any]]:
    # DataForSEO uses ISO language codes; default to English when locale
    # is empty / unknown.
    language_code = locale if locale and len(locale) == 2 else "en"
    return [{
        "keyword": keyword,
        "language_code": language_code,
        "location_code": location_code,
        "depth": 20,
    }]


def check_query(
    cq: CoreQuery,
    auth: tuple[str, str],
    target_domain: str,
    location_code: int,
) -> RowOut:
    payload = build_payload(cq.query, cq.locale, location_code)
    out = RowOut(
        query=cq.query,
        target_url=cq.target_url,
        priority=cq.priority,
        cluster=cq.cluster,
        locale=cq.locale,
        run_at_iso=datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
    )

    # 1) AI Overview
    ai_payload = dfs_request(ENDPOINT_AI_OVERVIEW, payload, auth)
    ai = extract_citation(ai_payload, target_domain)
    out.ai_overview_cited = ai.cited
    out.ai_overview_position = ai.position
    out.ai_overview_error = ai.error

    # 2) ChatGPT
    cg_payload = dfs_request(ENDPOINT_CHATGPT, payload, auth)
    cg = extract_citation(cg_payload, target_domain)
    out.chatgpt_cited = cg.cited
    out.chatgpt_position = cg.position
    out.chatgpt_error = cg.error

    # 3) Perplexity
    pp_payload = dfs_request(ENDPOINT_PERPLEXITY, payload, auth)
    pp = extract_citation(pp_payload, target_domain)
    out.perplexity_cited = pp.cited
    out.perplexity_position = pp.position
    out.perplexity_error = pp.error

    return out


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------


def write_csv(rows: list[RowOut], out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow([
            "query", "target_url", "priority", "cluster", "locale",
            "ai_overview_cited", "chatgpt_cited", "perplexity_cited",
            "ai_overview_position", "chatgpt_position", "perplexity_position",
            "ai_overview_error", "chatgpt_error", "perplexity_error",
            "run_at_iso",
        ])
        for r in rows:
            w.writerow([
                r.query,
                r.target_url,
                r.priority,
                r.cluster,
                r.locale,
                "true" if r.ai_overview_cited else "false",
                "true" if r.chatgpt_cited else "false",
                "true" if r.perplexity_cited else "false",
                r.ai_overview_position if r.ai_overview_position is not None else "",
                r.chatgpt_position if r.chatgpt_position is not None else "",
                r.perplexity_position if r.perplexity_position is not None else "",
                r.ai_overview_error,
                r.chatgpt_error,
                r.perplexity_error,
                r.run_at_iso,
            ])


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> int:
    args = parse_args()

    login = os.environ.get("DATAFORSEO_LOGIN")
    password = os.environ.get("DATAFORSEO_PASSWORD")
    if not login or not password:
        print(
            "ERROR: DATAFORSEO_LOGIN / DATAFORSEO_PASSWORD env vars are "
            "required. Refusing to run with no auth.",
            file=sys.stderr,
        )
        return 2

    if requests is None:
        print(
            "ERROR: requests is not installed. Install with: pip install requests",
            file=sys.stderr,
        )
        return 1

    cfg = load_config(args.site_config)
    target_domain = (
        os.environ.get("SEO_TARGET_DOMAIN", "").strip().lower()
        or cfg.target_domain
    )
    if not target_domain:
        print(
            "ERROR: no target domain. Set SEO_TARGET_DOMAIN env var or "
            "target_domain in the site config.",
            file=sys.stderr,
        )
        return 2

    try:
        queries = load_core_queries(Path(args.core_csv))
    except FileNotFoundError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    print(
        f"Target domain: {target_domain}",
        file=sys.stderr,
    )
    print(
        f"Loaded {len(queries)} core queries (priority in "
        f"{PRIORITY_FILTER}) from {args.core_csv}",
        file=sys.stderr,
    )

    if not queries:
        print(
            f"WARN: 0 queries match priority filter {PRIORITY_FILTER}. "
            "Nothing to do.",
            file=sys.stderr,
        )
        return 0

    # Pre-spend cost estimate — printed BEFORE the first API call.
    est_calls = len(queries) * 3
    est_cost = est_calls * EST_PRICE_PER_CALL_USD
    print(
        f"Estimated DataForSEO calls: {est_calls} "
        f"(3 surfaces x {len(queries)} queries) ~= ${est_cost:.2f} "
        f"@ ${EST_PRICE_PER_CALL_USD:.3f}/call upper-bound",
        file=sys.stderr,
    )

    auth = (login, password)
    rows: list[RowOut] = []
    for i, cq in enumerate(queries, start=1):
        print(f"[{i}/{len(queries)}] {cq.query!r}", file=sys.stderr)
        rows.append(check_query(cq, auth, target_domain, args.location_code))

    today_utc = datetime.now(timezone.utc).date()
    out_path = Path(args.out_dir) / f"{today_utc.isoformat()}.csv"
    write_csv(rows, out_path)

    summary = {
        "target_domain": target_domain,
        "out_file": str(out_path),
        "queries": len(rows),
        "ai_overview_cited": sum(1 for r in rows if r.ai_overview_cited),
        "chatgpt_cited": sum(1 for r in rows if r.chatgpt_cited),
        "perplexity_cited": sum(1 for r in rows if r.perplexity_cited),
        "ai_overview_errors": sum(1 for r in rows if r.ai_overview_error),
        "chatgpt_errors": sum(1 for r in rows if r.chatgpt_error),
        "perplexity_errors": sum(1 for r in rows if r.perplexity_error),
        "estimated_cost_usd": round(est_cost, 2),
    }
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
