"""Read-only access to the P-card SQLite database, plus the SQL safety guard.

Everything the web application does against the database goes through this module.
The connection is opened in read-only mode (`mode=ro`), so even a query that gets
past the guard below cannot modify the auditors' evidence file.
"""
from __future__ import annotations

import os
import re
import sqlite3
import threading
import time

DB_PATH = os.environ.get(
    "PCARD_DB", os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "pcards.db")
)

TABLE = "pcards"
COLUMNS = [
    "Year", "Month", "FullName", "ID", "AgencyNumber", "AgencyName",
    "CardholderLastName", "CardholderFirstInitial", "Description", "Amount",
    "Vendor", "TransactionDate", "PostedDate", "MCC",
]

MAX_ROWS = 500          # rows returned to the browser
STATEMENT_TIMEOUT_S = 20  # wall-clock ceiling for a single query

_local = threading.local()


class QueryRejected(Exception):
    """Raised when a generated query fails the read-only guard."""


def connect() -> sqlite3.Connection:
    """One read-only connection per thread."""
    conn = getattr(_local, "conn", None)
    if conn is None:
        if not os.path.exists(DB_PATH):
            raise FileNotFoundError(
                "P-card database not found at %s. Set the PCARD_DB environment "
                "variable to the location of pcards.db." % DB_PATH
            )
        uri = "file:%s?mode=ro" % DB_PATH.replace("?", "%3f").replace("#", "%23")
        conn = sqlite3.connect(uri, uri=True, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        _local.conn = conn
    return conn


# --------------------------------------------------------------------------- #
# SQL guard
# --------------------------------------------------------------------------- #

# Anything that could write, attach another file, or reach outside the one table.
_FORBIDDEN = re.compile(
    r"\b("
    r"insert|update|delete|drop|alter|create|replace|truncate|"
    r"attach|detach|pragma|vacuum|reindex|analyze|"
    r"begin|commit|rollback|savepoint|release|"
    r"load_extension|readfile|writefile|edit"
    r")\b",
    re.IGNORECASE,
)

_COMMENT_LINE = re.compile(r"--[^\n]*")
_COMMENT_BLOCK = re.compile(r"/\*.*?\*/", re.DOTALL)


def _strip_comments(sql: str) -> str:
    return _COMMENT_LINE.sub(" ", _COMMENT_BLOCK.sub(" ", sql))


def guard(sql: str) -> str:
    """Return the query if it is a single read-only SELECT, else raise."""
    if not sql or not sql.strip():
        raise QueryRejected("Empty query.")

    stripped = _strip_comments(sql).strip().rstrip(";").strip()
    if not stripped:
        raise QueryRejected("The query contained only comments.")

    if ";" in stripped:
        raise QueryRejected("Only a single statement is allowed.")

    if not re.match(r"^(select|with)\b", stripped, re.IGNORECASE):
        raise QueryRejected("Only SELECT (or WITH ... SELECT) queries are allowed.")

    hit = _FORBIDDEN.search(stripped)
    if hit:
        raise QueryRejected("The keyword '%s' is not allowed in an audit query." % hit.group(1))

    return stripped


def run_select(sql: str, params=(), limit: int = MAX_ROWS):
    """Execute a guarded read-only query and return (columns, rows, truncated)."""
    safe = guard(sql)
    conn = connect()

    # sqlite calls the progress handler every N vm steps; use it as a kill switch
    # so that a runaway generated query cannot hold the request open.
    started = time.time()

    def _progress():
        if time.time() - started > STATEMENT_TIMEOUT_S:
            return 1
        return 0

    conn.set_progress_handler(_progress, 100_000)
    try:
        cur = conn.execute(safe, params)
        rows = cur.fetchmany(limit + 1)
        cols = [d[0] for d in cur.description] if cur.description else []
    except sqlite3.OperationalError as exc:
        if "interrupted" in str(exc).lower():
            raise QueryRejected(
                "The query took longer than %d seconds and was stopped. Try adding a "
                "year filter or narrowing the search." % STATEMENT_TIMEOUT_S
            )
        raise
    finally:
        conn.set_progress_handler(None, 0)

    truncated = len(rows) > limit
    return cols, [dict(r) for r in rows[:limit]], truncated


# --------------------------------------------------------------------------- #
# Dashboard queries (parameterised - no user text is ever concatenated into SQL)
# --------------------------------------------------------------------------- #

RESULT_COLUMNS = (
    "TransactionDate, PostedDate, FullName AS Cardholder, Vendor, Description, "
    "Amount, MCC, Month, Year"
)


def available_years():
    cols, rows, _ = run_select(
        "SELECT Year, COUNT(*) AS Transactions, ROUND(SUM(Amount), 2) AS TotalSpend "
        "FROM pcards GROUP BY Year ORDER BY Year DESC", limit=50)
    return rows


def search(field: str, keyword: str, year=None, min_amount=None, limit: int = MAX_ROWS):
    """Keyword search over Description or Vendor, optionally restricted to a year."""
    if field not in {"Description", "Vendor"}:
        raise QueryRejected("Search field must be Description or Vendor.")
    keyword = (keyword or "").strip()
    if not keyword:
        raise QueryRejected("Enter a keyword to search for.")

    where = ["UPPER(%s) LIKE ?" % field]
    params = ["%" + keyword.upper() + "%"]
    if year:
        where.append("Year = ?")
        params.append(int(year))
    if min_amount not in (None, ""):
        where.append("ABS(Amount) >= ?")
        params.append(float(min_amount))

    clause = " AND ".join(where)

    sql = ("SELECT %s FROM pcards WHERE %s ORDER BY ABS(Amount) DESC"
           % (RESULT_COLUMNS, clause))
    cols, rows, truncated = run_select(sql, params, limit=limit)

    tot = connect().execute(
        "SELECT COUNT(*) AS n, ROUND(SUM(Amount), 2) AS total, "
        "COUNT(DISTINCT FullName) AS cardholders, COUNT(DISTINCT Vendor) AS vendors "
        "FROM pcards WHERE %s" % clause, params).fetchone()

    return {
        "columns": cols,
        "rows": rows,
        "truncated": truncated,
        "summary": dict(tot),
        "sql": sql,
        "params": params,
    }
