#!/usr/bin/env python3
"""Rebuild results/dashboard.md — the single aggregate view of all captures.

One pivot table per scenario: rows = metrics, columns = capture labels
('before'/'baseline' first, then by capture time), plus a Δ column between the
first and last label. Reads every results/<label>/<scenario>/<scenario>-metrics.md.

Project tuning lives in .claude/skills/creo-perf/dashboard.json (optional):
  {
    "order":       ["platform", "schema", "s1", "s2", "fe"],   # scenario order; unknown ids appended
    "titles":      {"s1": "S1 — default list page"},
    "endpoints":   {"s1": "`GET /items` → `list_items()` — `app/route/items.py:40`"},
    "hidden_rows": ["^Correctness ref$", "^hypothetical · "],  # regexes on the metric key
    "no_delta":    ["· idx ", "^Index ·"],                     # rows where a numeric Δ is noise
    "baseline_labels": ["before", "baseline"]
  }
Env: PERF_RESULTS (results dir), PERF_EXT_DIR (extension dir holding dashboard.json).
Called automatically at the end of every capture; safe to run by hand.
"""
import json
import os
import re
from pathlib import Path

RESULTS = Path(os.environ.get("PERF_RESULTS") or ".claude/skills/creo-perf/results").resolve()
EXT = Path(os.environ.get("PERF_EXT_DIR") or RESULTS.parent).resolve()
DASH = RESULTS / "dashboard.md"

CFG = {}
cfg_path = EXT / "dashboard.json"
if cfg_path.exists():
    CFG = json.loads(cfg_path.read_text())

ORDER = CFG.get("order", ["fe", "platform", "schema"])
TITLES = {
    "fe": "FE — initial app load (build + Lighthouse lab)",
    "platform": "Platform — backend process + database settings",
    "schema": "Schema — table/column/index audit",
    "db-workload": "DB workload — pg_stat_statements ranking (discovery layer)",
    **CFG.get("titles", {}),
}
ENDPOINTS = CFG.get("endpoints", {})
BASELINE_LABELS = tuple(CFG.get("baseline_labels", ["before", "baseline"]))

# Rows captured on disk but not rendered. Defaults: correctness references
# (a per-capture identity check — ETag seeds and max(updated_at) change whenever
# a row is written, so a pair reads as a diff that isn't one), hypothetical
# index verdicts (redundant once the real index exists), per-index scan
# counters (cumulative, traffic-dependent), variant prose cells.
HIDDEN_ROWS = re.compile(
    "|".join(
        [
            r"^Correctness ref$",
            r"^Variants$",
            r"^hypothetical · ",
            r"^meta · ",
        ]
        + CFG.get("hidden_rows", [])
    )
)
# rows describing indexes / their counters / source line numbers: numeric Δ is noise
NO_DELTA = re.compile("|".join([r"· idx ", r"unused indexes", r"^Index ·", r"^Q\[", r"^Out-of-pool$"] + CFG.get("no_delta", [])))

FREE_LINE = re.compile(r"^(Variants|Correctness ref|Disposition):\s*(.+)$")
SEP_CELL = re.compile(r"^:?-{3,}:?$")
HEADER_KEYS = ("Layer", "Fact", "Setting", "Metric")


def parse_metrics(path):
    """Return (ordered_keys, {key: value}) from one <scenario>-metrics.md."""
    keys, rows = [], {}
    header = None
    for line in path.read_text().splitlines():
        s = line.strip()
        if s.startswith("|"):
            cells = [c.strip() for c in s.strip("|").split("|")]
            if all(SEP_CELL.fullmatch(c) for c in cells):
                continue
            if "Value" in cells and any(h in cells for h in HEADER_KEYS):
                header = cells
                continue
            if header is None:
                continue
            vi = header.index("Value") if "Value" in header else len(cells) - 1
            key = " · ".join(
                cells[i]
                for i in range(len(cells))
                if i != vi and (i >= len(header) or header[i] != "Why it matters") and cells[i]
            )
            if key and key not in rows and vi < len(cells):
                rows[key] = cells[vi]
                keys.append(key)
        else:
            m = FREE_LINE.match(s)
            if m and m.group(1) not in rows:
                rows[m.group(1)] = m.group(2)
                keys.append(m.group(1))
    return keys, rows


NUM = re.compile(r"-?\d[\d,]*\.?\d*")
# a measurement = number immediately followed by a unit (so "z2"/"x2" never count)
MEASURE = re.compile(r"(-?\d[\d,]*\.?\d*)\s*(ms|s|kB|MB|GB|B)\b")
# EXPLAIN fragments: compare the slowest node's actual end time
ACTUAL_TIME = re.compile(r"actual time=[\d.]+\.\.([\d.]+)")
# composite cells like "etag 1.7 ms + data 13.4 ms ≈ 15 ms": the ≈-total is the headline
APPROX_TOTAL = re.compile(r"≈\s*(-?\d[\d,]*\.?\d*)\s*ms")

# pg_stat index counters are cumulative since the last reset — they measure how
# much traffic a capture drove, not the effect of a fix. Scrubbed from cells.
IDX_SCAN = [
    (re.compile(r",\s*\d+\s+scans"), ""),
    (re.compile(r",\s*idx_scan\s*=\s*\d+"), ""),
    (re.compile(r"idx_scan\s*=\s*\d+\s*—\s*"), ""),
    (re.compile(r"\s*·\s*idx_scan\s*=\s*\d+"), ""),
    (re.compile(r"\s*idx_scan\s*=\s*\d+"), ""),
    (re.compile(r"\s*·\s*UNUSED"), ""),
]
# A validator is a hash of the response: two captures agree only when nothing
# changed, so the literal tag never belongs in a comparison cell.
ETAG_HASH = [
    (re.compile(r'\s*\(ETag "?[0-9a-fA-FW/"]+"?\)'), ""),
    (re.compile(r"\s*·?\s*ETag seed=[0-9a-fA-F]+"), ""),
    (re.compile(r'\s*ETag "[0-9a-fA-F]+"'), ""),
]


def scrub(value):
    for pattern, repl in IDX_SCAN + ETAG_HASH:
        value = pattern.sub(repl, value)
    return value


def _fmt(d, unit=""):
    body = f"{d:+,.0f}" if abs(d) >= 100 else f"{d:+,.3g}"
    return f"{body} {unit}".rstrip()


def _diff(a, b, unit=""):
    d = b - a
    if d == 0:
        return "≠"
    pct = f" ({d / a * 100:+.0f}%)" if a else ""
    return f"{_fmt(d, unit)}{pct}"


def delta_cell(base, cur):
    if base == cur:
        return ""
    if base == "—":
        return "new"
    if cur == "—":
        return "removed"
    aa, bb = APPROX_TOTAL.findall(base), APPROX_TOTAL.findall(cur)
    if aa and bb:
        return _diff(float(aa[-1].replace(",", "")), float(bb[-1].replace(",", "")), "ms")
    ta = [float(x) for x in ACTUAL_TIME.findall(base)]
    tb = [float(x) for x in ACTUAL_TIME.findall(cur)]
    if ta and tb:
        return _diff(max(ta), max(tb), "ms")
    ma, mb = MEASURE.search(base), MEASURE.search(cur)
    if ma and mb and ma.group(2) == mb.group(2):
        return _diff(float(ma.group(1).replace(",", "")), float(mb.group(1).replace(",", "")), ma.group(2))
    ma, mb = NUM.search(base), NUM.search(cur)
    if ma and mb:
        try:
            return _diff(float(ma.group().replace(",", "")), float(mb.group().replace(",", "")))
        except ValueError:
            return "≠"
    return "≠"


SIZE = re.compile(r"^\s*([\d.]+)\s*(bytes|kB|MB|GB)\b")
UNIT = {"bytes": 1, "kB": 1024, "MB": 1024**2, "GB": 1024**3}
IDX_KEY = re.compile(r"^(?P<table>[^·]+?) · idx (?P<name>.+)$")


def _bytes(cell):
    m = SIZE.match(cell)
    return int(float(m.group(1)) * UNIT[m.group(2)]) if m else 0


def _size(n):
    return f"{n / UNIT['MB']:.1f} MB" if n >= UNIT["MB"] else f"{n / UNIT['kB']:.0f} kB"


def index_inventory(rows):
    """Per table: '<n> indexes / <size> total' — comparable independently of scan counters."""
    inv = {}
    for key, cell in rows.items():
        m = IDX_KEY.match(key)
        if not m:
            continue
        t = m.group("table").strip()
        n, b = inv.get(t, (0, 0))
        inv[t] = (n + 1, b + _bytes(cell))
    return {t: f"{n} indexes / {_size(b)} total" for t, (n, b) in inv.items()}


def index_churn(first, last, table):
    def idx(rows):
        out = {}
        for k, v in rows.items():
            m = IDX_KEY.match(k)
            if m and m.group("table").strip() == table:
                out[m.group("name")] = _bytes(v)
        return out

    was, now = idx(first), idx(last)
    dropped = sorted(set(was) - set(now), key=lambda n: -was[n])
    created = sorted(set(now) - set(was), key=lambda n: -now[n])
    out = []
    for verb, names, src in (("dropped", dropped, was), ("created", created, now)):
        if names:
            listed = ", ".join(f"{n} {_size(src[n])}" for n in names)
            out.append(f"{verb} {len(names)} ({_size(sum(src[n] for n in names))}): {listed}")
    return " · ".join(out)


def main():
    scenarios = {}
    for label_dir in sorted(RESULTS.iterdir()) if RESULTS.is_dir() else []:
        if not label_dir.is_dir() or label_dir.name.startswith("."):
            continue
        label = label_dir.name
        for sdir in sorted(p for p in label_dir.iterdir() if p.is_dir()):
            sid = sdir.name
            f = sdir / f"{sid}-metrics.md"
            if not f.exists() or sid == "db-workload":
                # db-workload rows are per-query-hash and never line up across
                # captures; read results/<label>/db-workload/ directly.
                continue
            sc = scenarios.setdefault(sid, {"labels": [], "keys": [], "data": {}})
            sc["labels"].append((label not in BASELINE_LABELS, f.stat().st_mtime, label))
            keys, rows = parse_metrics(f)
            prev = None
            for k in keys:
                if k not in sc["keys"]:
                    if prev is not None and prev in sc["keys"]:
                        sc["keys"].insert(sc["keys"].index(prev) + 1, k)
                    else:
                        sc["keys"].append(k)
                prev = k
            for table, inv in index_inventory(rows).items():
                key = f"{table} · index inventory"
                rows[key] = inv
                if key not in sc["keys"]:
                    anchor = f"{table} · table"
                    at = sc["keys"].index(anchor) + 1 if anchor in sc["keys"] else len(sc["keys"])
                    sc["keys"].insert(at, key)
            sc["data"][label] = rows

    ordered = [s for s in ORDER if s in scenarios] + sorted(s for s in scenarios if s not in ORDER)
    out = [
        "# Benchmark dashboard — all scenarios × captures",
        "",
        "Auto-generated by the creo-perf harness (`build-dashboard.py`) at the end of every "
        "capture — never edit by hand. Columns are capture labels (baseline first, immutable); "
        "'—' = metric absent in that capture. Δ compares the last column against the first.",
        "",
    ]
    for sid in ordered:
        sc = scenarios[sid]
        labels = [l for _, _, l in sorted(sc["labels"])]
        show_delta = len(labels) >= 2
        out.append(f"## {TITLES.get(sid, sid.upper())}")
        out.append("")
        if sid in ENDPOINTS:
            out.append(f"Endpoint: {ENDPOINTS[sid]}")
            out.append("")
        hdr = "| Metric | " + " | ".join(labels)
        if show_delta:
            hdr += f" | Δ ({labels[-1]} vs {labels[0]})"
        out.append(hdr + " |")
        out.append("|---|" + "---|" * (len(labels) + (1 if show_delta else 0)))
        for k in sc["keys"]:
            if HIDDEN_ROWS.match(k):
                continue
            vals = [scrub(sc["data"].get(l, {}).get(k, "—")) for l in labels]
            row = f"| {k} | " + " | ".join(vals)
            if show_delta:
                cell = "" if NO_DELTA.search(k) else delta_cell(vals[0], vals[-1])
                if k.endswith(" · index inventory"):
                    churn = index_churn(sc["data"].get(labels[0], {}), sc["data"].get(labels[-1], {}), k[: -len(" · index inventory")])
                    cell = f"{cell} · {churn}" if churn else cell
                row += " | " + cell
            out.append(row + " |")
        out.append("")
    DASH.parent.mkdir(parents=True, exist_ok=True)
    DASH.write_text("\n".join(out) + "\n")
    print(f"dashboard: {DASH}")


if __name__ == "__main__":
    main()
