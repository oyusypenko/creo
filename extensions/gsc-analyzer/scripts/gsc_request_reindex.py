#!/usr/bin/env python3
"""
"Notify Google" phase of the GSC auto-fix loop (see docs/autofix.md).

After fixes are deployed and live-verified, nudge Google to recrawl:

1. --resubmit-sitemap   Re-submit the sitemap via the Sitemaps API.
                        Equivalent to the UI "resubmit" button. Requires the
                        service account to have FULL (not restricted)
                        permission on the GSC property; with read-only
                        permission Google returns 403 and this script reports
                        the needed upgrade. The sitemap URL comes from
                        --sitemap-feed or the GSC_SITEMAP_FEED env var.
2. --urls <file>        One URL per line: send URL_UPDATED notifications via
                        the Indexing API. CAVEAT: Google officially supports
                        the Indexing API only for JobPosting/BroadcastEvent
                        pages; for regular pages it may be ignored. Requires
                        the Indexing API enabled on your GCP project and the
                        service account verified as a property owner.
                        Failures are reported, never fatal.

There is NO public API for the GSC UI "Validate Fix" button — issue
validation requests remain a one-click manual step, which the run report
should call out when relevant.

Env:
  GSC_SITE_URL        REQUIRED. GSC property, e.g. "sc-domain:example.com"
  GSC_SITEMAP_FEED    sitemap URL to resubmit (or use --sitemap-feed)

Auth resolution is identical to gsc_autofix_detect.py
(GSC_SERVICE_ACCOUNT_JSON content, or GSC_KEY_FILE /
GOOGLE_APPLICATION_CREDENTIALS key file path).

Example:
  GSC_SITE_URL=sc-domain:example.com \
  GSC_SITEMAP_FEED=https://example.com/sitemap.xml \
  python3 gsc_request_reindex.py --resubmit-sitemap
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

try:
    from google.oauth2 import service_account
    from googleapiclient.discovery import build
except ImportError:  # pragma: no cover
    service_account = None
    build = None

WEBMASTERS_SCOPE = ["https://www.googleapis.com/auth/webmasters"]
INDEXING_SCOPE = ["https://www.googleapis.com/auth/indexing"]

INDEXING_DELAY_SEC = 0.5  # Indexing API default quota: 200 publishes/day


def require_site_url() -> str:
    site = os.environ.get("GSC_SITE_URL")
    if not site:
        raise RuntimeError(
            "GSC_SITE_URL is required, e.g. 'sc-domain:example.com' or "
            "'https://example.com/'"
        )
    return site


def resolve_credentials(scopes: list[str]):
    if service_account is None or build is None:
        raise RuntimeError(
            "google-api-python-client is not installed. "
            "Install the gsc-analyzer requirements first: "
            "pip install -r requirements.txt"
        )
    inline = os.environ.get("GSC_SERVICE_ACCOUNT_JSON")
    if inline:
        return service_account.Credentials.from_service_account_info(
            json.loads(inline), scopes=scopes
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
        key_file, scopes=scopes
    )


def resubmit_sitemap(site_url: str, sitemap_feed: str) -> dict:
    creds = resolve_credentials(WEBMASTERS_SCOPE)
    svc = build("webmasters", "v3", credentials=creds, cache_discovery=False)
    try:
        svc.sitemaps().submit(siteUrl=site_url, feedpath=sitemap_feed).execute()
        return {"sitemap": sitemap_feed, "submitted": True}
    except Exception as exc:
        msg = str(exc)
        hint = None
        if "403" in msg or "insufficient" in msg.lower():
            hint = (
                "service account lacks FULL permission on the GSC property — "
                "upgrade it in GSC Settings -> Users and permissions"
            )
        return {"sitemap": sitemap_feed, "submitted": False, "error": msg, "hint": hint}


def notify_urls(urls_file: Path) -> list[dict]:
    creds = resolve_credentials(INDEXING_SCOPE)
    svc = build("indexing", "v3", credentials=creds, cache_discovery=False)
    results: list[dict] = []
    urls = [
        line.strip()
        for line in urls_file.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.startswith("#")
    ]
    for url in urls:
        try:
            svc.urlNotifications().publish(
                body={"url": url, "type": "URL_UPDATED"}
            ).execute()
            results.append({"url": url, "notified": True})
        except Exception as exc:
            msg = str(exc)
            hint = None
            if "has not been used" in msg or "disabled" in msg:
                hint = "enable the Indexing API on your GCP project"
            elif "Permission" in msg or "403" in msg:
                hint = "service account must be a verified OWNER of the property"
            results.append({"url": url, "notified": False, "error": msg, "hint": hint})
        time.sleep(INDEXING_DELAY_SEC)
    return results


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--resubmit-sitemap", action="store_true")
    parser.add_argument("--sitemap-feed",
                        default=os.environ.get("GSC_SITEMAP_FEED"),
                        help="sitemap URL to resubmit (default: "
                             "GSC_SITEMAP_FEED env)")
    parser.add_argument("--urls", type=Path, help="file with URLs to notify")
    args = parser.parse_args()

    if not args.resubmit_sitemap and not args.urls:
        parser.error("nothing to do: pass --resubmit-sitemap and/or --urls")
    if args.resubmit_sitemap and not args.sitemap_feed:
        parser.error(
            "--resubmit-sitemap needs a sitemap URL: pass --sitemap-feed "
            "or set GSC_SITEMAP_FEED"
        )

    site_url = require_site_url()

    report: dict = {}
    if args.resubmit_sitemap:
        report["sitemapResubmit"] = resubmit_sitemap(site_url, args.sitemap_feed)
    if args.urls:
        report["urlNotifications"] = notify_urls(args.urls)

    print(json.dumps(report, indent=2))
    ok = report.get("sitemapResubmit", {}).get("submitted", True) and all(
        r.get("notified") for r in report.get("urlNotifications", [])
    )
    # Non-fatal by design: the loop continues even when Google declines the
    # nudge — recrawl happens organically either way.
    print(f"notify-google: {'all OK' if ok else 'partial/failed (see report)'}",
          file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
