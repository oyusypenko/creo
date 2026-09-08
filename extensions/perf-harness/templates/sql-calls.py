"""sql-calls.py — record-mode hook for the creo-perf harness (PERF_SQL_MODE=record).

sql-runners.py imports this file under PERF_SQL_PYTHON (the backend venv),
wraps the app's Session in a recording subclass, and calls `scenarios(call,
session)`. Every statement the endpoint functions execute is captured with
its bind params, executed for real, inlined as literals, and written to a
psql runner file `<runner>.sql` with `=== <runner>/<label> run N ===` markers.

Because the REAL endpoint code runs, benchmark SQL cannot drift from app SQL.

Fill in for project __PROJECT_ID__: the engine import, the statement filter,
and one entry per scenario runner. Labels matching ROWS_LABELS get a
`SELECT count(*) FROM (...)` correctness query; others run the statement.
"""
import os
import sys

# Make the backend importable and give it the same DB connection the app uses.
BACKEND = os.path.join(os.environ.get("PERF_PROJECT_ROOT", "."), "backend")
sys.path.insert(0, BACKEND)
os.environ.setdefault("DATABASE_URL", "postgresql://user:pass@localhost:5432/db")

from app.db import engine  # noqa: E402  — the app's own engine
import app.route.items as items  # noqa: E402  — module holding the hot endpoints

ENGINE = engine
STATEMENT_FILTER = "items"          # keep only statements mentioning the hot table
ROWS_LABELS = r"^(data|rows|list|page|tile)"


class FakeRequest:
    headers = {}


def scenarios(call, session):
    """Return {runner_name: [(label, sql), ...]}.

    `call(fn, *args, **kwargs)` runs an endpoint function and returns the list
    of statements it executed (in order). Pass `session` where the endpoint
    expects a DB session; pass FakeRequest() where it expects a request.
    """
    req = FakeRequest()
    out = {}

    q = call(items.list_items, req, session, filters=None, page=0, page_size=100,
             sort_by="created_at", sort_dir="desc")
    # list_items executes exactly [count aggregate, data page] — label them in order
    out["s1_default"] = list(zip(("count", "data_p100"), q))

    # q = call(items.list_items, req, session, filters='{"text": "composite"}', page=0, page_size=100)
    # out["s2_search"] = list(zip(("count", "data_p100"), q))

    return out
