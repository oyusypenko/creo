#!/usr/bin/env python3
"""
Shared per-project site configuration for the SEO analytics scripts.

All site-specific knowledge (cluster taxonomy, noise-filter regexes,
commercial signals, priority rubric inputs) lives in a JSON file that each
project provides. The scripts in this directory load it through this module
so none of them carry hardcoded taxonomy.

Config resolution order:
  1. explicit path passed to ``load_config()`` (usually from a
     ``--site-config`` CLI flag)
  2. ``SEO_SITE_CONFIG`` environment variable
  3. ``./seo-site-config.json`` in the current working directory

Config JSON shape (see templates/seo-site-config.example.json):
  target_domain       str    e.g. "example.com"
  known_locales       [str]  locale path prefixes to strip ("en", "de", ...)
  clusters            [{"prefix": "/blog/", "name": "blog-post"}, ...]
                             ordered, first match wins; fallback is "other"
  commercial_signals  [str]  substrings that mark real intent (override noise)
  noise_patterns      [str]  regexes (applied to the lowercased query) that
                             classify a query as noise
  purpose_patterns    [str]  regexes that cancel a noise classification
  p0_clusters         [str]  cluster names for the P0 priority band
  p2_clusters         [str]  cluster names for the P2 priority band
  commercial_paths    [str]  path prefixes considered transactional
                             (clustered as "commercial" when no cluster rule
                             matched first)

Graceful degradation: if no config file exists, everything clusters to
"other", the noise filter is disabled, and priorities are assigned from
impressions/position only. A stderr warning recommends creating a config.

Top-level keys starting with "_" (e.g. "_comment") are ignored, so the
config file can carry inline documentation.
"""

from __future__ import annotations

import json
import os
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

DEFAULT_CONFIG_FILENAME = "seo-site-config.json"
CONFIG_ENV_VAR = "SEO_SITE_CONFIG"

# ---------------------------------------------------------------------------
# Generic (project-agnostic) intent triggers
# ---------------------------------------------------------------------------

INFO_TRIGGERS = ("how to", " vs ", "alternative", "what is", "why ")
COMMERCIAL_TRIGGERS = (
    "best ", "top ", " app", " apps", " software", " tool", " tools",
)
TRANSACTIONAL_TRIGGERS = (
    "buy ", "price", "pricing", "subscription", "discount", "coupon",
)

# ---------------------------------------------------------------------------
# Priority rubric thresholds (P0-P3, used post noise-filter)
# ---------------------------------------------------------------------------

P0_MIN_IMPRESSIONS = 50
P0_MAX_POSITION = 20.0
P1_MIN_IMPRESSIONS = 100
P1_MIN_POSITION = 4.0
P1_MAX_POSITION = 30.0
P2_MIN_IMPRESSIONS = 30


def _prefix_match(rest: str, prefix: str) -> bool:
    """Segment-aware prefix match. Trailing slashes are irrelevant:
    prefix "/blog/" (or "/blog") matches "/blog", "/blog/" and "/blog/x".
    The root prefix "/" matches only the root path itself."""
    p = prefix.lower()
    if p in ("", "/"):
        return rest == "/"
    p = p.rstrip("/")
    return rest == p or rest == p + "/" or rest.startswith(p + "/")


@dataclass
class SiteConfig:
    target_domain: str = ""
    known_locales: frozenset = frozenset()
    clusters: list = field(default_factory=list)  # list[(prefix, name)]
    commercial_signals: tuple = ()
    noise_patterns: list = field(default_factory=list)  # list[re.Pattern]
    purpose_patterns: list = field(default_factory=list)  # list[re.Pattern]
    p0_clusters: frozenset = frozenset()
    p2_clusters: frozenset = frozenset()
    commercial_paths: list = field(default_factory=list)
    loaded_from: str = ""  # empty when running on defaults

    # -- path taxonomy ------------------------------------------------------

    def strip_locale(self, path: str) -> tuple:
        """Return (locale, rest_path). locale is "unknown" when the first
        path segment is not in known_locales."""
        parts = [seg for seg in path.split("/") if seg]
        locale = "unknown"
        if parts and parts[0].lower() in self.known_locales:
            locale = parts[0].lower()
            parts = parts[1:]
        rest = "/" + "/".join(parts) if parts else "/"
        return locale, rest

    def cluster_for_path(self, path: str) -> str:
        """Map a URL path to a cluster name. Ordered first-match-wins over
        the configured cluster rules, then commercial_paths, then "other"."""
        _, rest = self.strip_locale(path.lower())
        for prefix, name in self.clusters:
            if _prefix_match(rest, prefix):
                return name
        for p in self.commercial_paths:
            if _prefix_match(rest, p):
                return "commercial"
        return "other"

    def locale_for_path(self, path: str) -> str:
        return self.strip_locale(path)[0]

    # -- query classification ----------------------------------------------

    def classify_intent(self, query: str) -> str:
        ql = " " + query.lower() + " "
        if any(t in ql for t in TRANSACTIONAL_TRIGGERS):
            return "transactional"
        if any(t in ql for t in COMMERCIAL_TRIGGERS):
            return "commercial"
        if any(t in ql for t in INFO_TRIGGERS):
            return "informational"
        return "informational"

    def classify_noise(self, query: str) -> bool:
        """Layered noise classifier:
          1. purpose_patterns cancel noise (strongest override)
          2. commercial_signals substrings cancel noise
          3. noise_patterns classify noise
        With no configured noise_patterns the filter is disabled and every
        query is kept."""
        if not self.noise_patterns:
            return False
        ql = query.lower().strip()
        for rx in self.purpose_patterns:
            if rx.search(ql):
                return False
        for s in self.commercial_signals:
            if s in ql:
                return False
        for rx in self.noise_patterns:
            if rx.search(ql):
                return True
        return False

    # -- priority rubric ----------------------------------------------------

    def assign_priority(self, cluster: str, impressions: int, position: float) -> str:
        """P0-P3 rubric. Without a config (empty p0/p2 cluster sets) this
        degrades to an impressions/position-only rubric: P1 or P3."""
        if cluster in self.p0_clusters and (
            impressions >= P0_MIN_IMPRESSIONS or position <= P0_MAX_POSITION
        ):
            return "P0"
        if impressions >= P1_MIN_IMPRESSIONS and (
            P1_MIN_POSITION <= position <= P1_MAX_POSITION
        ):
            return "P1"
        if cluster in self.p2_clusters and impressions >= P2_MIN_IMPRESSIONS:
            return "P2"
        return "P3"

    @staticmethod
    def opportunity_score(impressions: int, position: float) -> float:
        """Rough opportunity = impressions * (1 / position). Higher = better."""
        return float(impressions) / max(float(position), 1.0)


def _compile_patterns(raw: list, key: str) -> list:
    out = []
    for pat in raw or []:
        try:
            out.append(re.compile(pat))
        except re.error as exc:
            raise ValueError(
                f"seo-site-config: invalid regex in {key!r}: {pat!r} ({exc})"
            ) from exc
    return out


def resolve_config_path(explicit_path: str = "") -> Path:
    if explicit_path:
        return Path(explicit_path)
    env_path = os.environ.get(CONFIG_ENV_VAR, "")
    if env_path:
        return Path(env_path)
    return Path.cwd() / DEFAULT_CONFIG_FILENAME


def load_config(explicit_path: str = "") -> SiteConfig:
    """Load the per-project site config. Missing file -> defaults + warning.
    A malformed file (bad JSON, bad regex) raises so the caller fails fast
    instead of silently analyzing with the wrong taxonomy."""
    path = resolve_config_path(explicit_path)
    if not path.exists():
        print(
            f"WARN: site config not found at {path} — running with defaults: "
            "all URLs cluster to 'other', noise filter disabled, priorities "
            "from impressions/position only. Create a seo-site-config.json "
            "(see templates/seo-site-config.example.json) for full analysis.",
            file=sys.stderr,
        )
        return SiteConfig()

    with path.open(encoding="utf-8") as f:
        data = json.load(f)

    clusters = []
    for rule in data.get("clusters") or []:
        prefix = (rule.get("prefix") or "").strip()
        name = (rule.get("name") or "").strip()
        if prefix and name:
            clusters.append((prefix, name))

    return SiteConfig(
        target_domain=(data.get("target_domain") or "").strip().lower(),
        known_locales=frozenset(
            str(loc).lower() for loc in data.get("known_locales") or []
        ),
        clusters=clusters,
        commercial_signals=tuple(
            str(s).lower() for s in data.get("commercial_signals") or []
        ),
        noise_patterns=_compile_patterns(
            data.get("noise_patterns"), "noise_patterns"
        ),
        purpose_patterns=_compile_patterns(
            data.get("purpose_patterns"), "purpose_patterns"
        ),
        p0_clusters=frozenset(data.get("p0_clusters") or []),
        p2_clusters=frozenset(data.get("p2_clusters") or []),
        commercial_paths=[str(p) for p in data.get("commercial_paths") or []],
        loaded_from=str(path),
    )
