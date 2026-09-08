#!/usr/bin/env python3
"""Generate psql runner files for the creo-perf harness.

A runner file is what audit-scenario.sh feeds to psql: for every statement,
three `EXPLAIN (ANALYZE, BUFFERS)` runs plus one correctness query, each
fenced by `\\echo === <runner>/<label> run N ===` markers that lib-scenario.sh
parses. Two ways to produce them:

  compile   from hand-maintained statements
            .claude/skills/creo-perf/sql-src/<runner>/<label>.sql
            one statement per file, binds already inlined as literals.
            A file named <label>.rows.sql gets `SELECT count(*) FROM (<stmt>) sub`
            as its correctness query (row-returning statements); any other
            file runs the statement itself (aggregates, scalars).

  record    from the REAL application code — no hand-mirroring. Imports
            .claude/skills/creo-perf/sql-calls.py, which must expose
              ENGINE               SQLAlchemy engine (the app's own)
              STATEMENT_FILTER     substring a statement must contain to be kept
                                   (usually the hot table name)
              def scenarios(call, session) -> {runner: [(label, sql), ...]}
                                   `call(fn, *a, **kw)` runs an endpoint function
                                   and returns the inlined SQL it executed.
              ROWS_LABELS          optional regex; matching labels get the count(*)
                                   correctness wrapper (default: ^(data|rows|list|page|tile))
            Statements are captured in Session._execute_internal with their bind
            params, executed for real (warms the cache the same way the app
            does), and inlined as literals for EXPLAIN. Any change to the app
            code changes what is extracted — drift is impossible by construction.
            Runs under PERF_SQL_PYTHON (the backend venv) — re-execs itself.

Usage:  sql-runners.py compile|record
Env:    SQL_OUT (output dir, required), PERF_EXT_DIR (project extension dir),
        PERF_SQL_PYTHON (record mode interpreter, default: current)
"""
import os
import re
import sys
from pathlib import Path

RUNS = 3
DEFAULT_ROWS = re.compile(r"^(data|rows|list|page|tile)")


def write_runner(out: Path, name: str, queries, rows_re) -> Path:
    path = out / f"{name}.sql"
    with open(path, "w") as f:
        f.write("\\pset pager off\n")
        for label, q in queries:
            q = q.strip().rstrip(";")
            for run in range(1, RUNS + 1):
                f.write(f"\\echo === {name}/{label} run {run} ===\n")
                f.write(f"EXPLAIN (ANALYZE, BUFFERS) {q};\n")
            f.write(f"\\echo === {name}/{label} RESULT (correctness) ===\n")
            if rows_re(label):
                f.write(f"SELECT count(*) AS returned_rows FROM ({q}) sub;\n")
            else:
                f.write(f"{q};\n")
    return path


def compile_mode(ext: Path, out: Path):
    src = ext / "sql-src"
    if not src.is_dir():
        sys.exit(f"compile: no {src} — add sql-src/<runner>/<label>.sql files")
    n = 0
    for runner_dir in sorted(p for p in src.iterdir() if p.is_dir()):
        queries, rows = [], set()
        for f in sorted(runner_dir.glob("*.sql")):
            label = f.name[: -len(".sql")]
            if label.endswith(".rows"):
                label = label[: -len(".rows")]
                rows.add(label)
            queries.append((label, f.read_text()))
        if queries:
            print(write_runner(out, runner_dir.name, queries, lambda l, r=rows: l in r))
            n += 1
    if not n:
        sys.exit("compile: sql-src/ has no runner directories with .sql files")


def record_mode(ext: Path, out: Path):
    want = os.environ.get("PERF_SQL_PYTHON")
    if want and Path(want).exists() and Path(want).resolve() != Path(sys.executable).resolve():
        os.execv(want, [want, __file__, "record"])

    calls = ext / "sql-calls.py"
    if not calls.exists():
        sys.exit(f"record: no {calls} — see templates/sql-calls.py")
    import importlib.util

    spec = importlib.util.spec_from_file_location("perf_sql_calls", calls)
    mod = importlib.util.module_from_spec(spec)
    sys.path.insert(0, str(calls.parent))
    spec.loader.exec_module(mod)

    from sqlalchemy.orm import Session as _Session

    try:  # sqlmodel sessions subclass sqlalchemy's; prefer the app's flavour
        from sqlmodel import Session as _Session  # type: ignore  # noqa: F811
    except Exception:  # pragma: no cover
        pass

    stmt_filter = getattr(mod, "STATEMENT_FILTER", "")
    rows_re = re.compile(getattr(mod, "ROWS_LABELS", DEFAULT_ROWS.pattern))
    bind = re.compile(r"(?<!:):([A-Za-z_][A-Za-z0-9_]*)")

    def literal(v):
        if v is None:
            return "NULL"
        if isinstance(v, bool):
            return "TRUE" if v else "FALSE"
        if isinstance(v, (int, float)):
            return str(v)
        return "'" + str(v).replace("'", "''") + "'"

    def inline(sql, params):
        return bind.sub(lambda m: literal(params[m.group(1)]) if m.group(1) in params else m.group(0), sql)

    class RecordingSession(_Session):
        def __init__(self, *a, **kw):
            super().__init__(*a, **kw)
            self.recorded = []

        def _execute_internal(self, statement, params=None, *a, **kw):
            sql = str(statement)
            if stmt_filter in sql:
                self.recorded.append((sql, dict(params) if params else {}))
            return super()._execute_internal(statement, params, *a, **kw)

    with RecordingSession(mod.ENGINE) as s:

        def call(fn, *a, **kw):
            start = len(s.recorded)
            fn(*a, **kw)
            return [inline(sql, p) for sql, p in s.recorded[start:]]

        scenarios = mod.scenarios(call, s)

    for name, queries in scenarios.items():
        print(write_runner(out, name, queries, lambda l: bool(rows_re.match(l))))


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else ""
    if mode not in ("compile", "record"):
        sys.exit(__doc__)
    out = Path(os.environ.get("SQL_OUT") or "").expanduser()
    if not str(out):
        sys.exit("SQL_OUT is required")
    out.mkdir(parents=True, exist_ok=True)
    ext = Path(os.environ.get("PERF_EXT_DIR") or ".claude/skills/creo-perf").resolve()
    (compile_mode if mode == "compile" else record_mode)(ext, out)


if __name__ == "__main__":
    main()
