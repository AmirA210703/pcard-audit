"""OSU P-card audit workbench.

Two tabs:
  1. Ask the data  -- auditors ask questions in plain language; Claude writes the
     SQLite query, the server runs it read-only and shows both the answer and the query.
  2. Prohibited purchases -- a dashboard for searching transaction descriptions and
     vendor names for the purchase types the P-card procedure forbids.

Configuration comes from the environment.  Either export the variables, or put
them in a local `.env` file next to this module -- `.env` is gitignored, so a key
placed there is never committed.  See `.env.example`.

Run:  python app.py            (reads ./.env)
      ANTHROPIC_API_KEY=... PCARD_DB=/path/to/pcards.db python app.py
"""
from __future__ import annotations

import csv
import io
import os
import traceback

import sys

import envfile

# Our own loader handles .env, so silence Flask's "install python-dotenv" tip.
os.environ.setdefault("FLASK_SKIP_DOTENV", "1")

# Must happen before pcard_db is imported: that module resolves PCARD_DB at
# import time.
_ENV_KEYS = envfile.load()

# Expand data/pcards.db.gz if no database is in place yet, and set PCARD_DB to
# wherever it ended up.  On a local checkout that already points PCARD_DB at the
# original download this is a no-op.
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scripts"))
import prepare_db  # noqa: E402

_DB_ERROR = None
try:
    prepare_db.ensure_db()
except Exception as exc:  # the dashboard cannot work, but the page must still load
    _DB_ERROR = str(exc)

from flask import Flask, Response, jsonify, render_template, request  # noqa: E402

import pcard_db  # noqa: E402
import nl_query  # noqa: E402
from prohibited import CATEGORIES  # noqa: E402

app = Flask(__name__)


# --------------------------------------------------------------------------- #
# Pages
# --------------------------------------------------------------------------- #

@app.get("/")
def index():
    try:
        years = pcard_db.available_years()
        db_error = None
    except Exception as exc:
        # If the database never got unpacked, that is the more useful message.
        years, db_error = [], _DB_ERROR or str(exc)
    return render_template(
        "index.html",
        years=years,
        categories=CATEGORIES,
        db_error=db_error,
        nl_enabled=nl_query.configured(),
        nl_provider=nl_query.provider(),
        nl_model=nl_query.model_name(),
        db_name=os.path.basename(pcard_db.DB_PATH),
    )


# --------------------------------------------------------------------------- #
# Tab 1 -- natural-language questions
# --------------------------------------------------------------------------- #

@app.post("/api/ask")
def api_ask():
    payload = request.get_json(silent=True) or {}
    question = (payload.get("question") or "").strip()
    if not question:
        return jsonify({"ok": False, "error": "Type a question first."}), 400
    if len(question) > 2000:
        return jsonify({"ok": False, "error": "That question is too long."}), 400

    try:
        return jsonify(nl_query.ask(question, payload.get("history")))
    except nl_query.NotConfigured as exc:
        return jsonify({"ok": False, "error": str(exc), "needs_key": True}), 503
    except nl_query.Unavailable as exc:
        # The provider is busy. Nothing is wrong with the question or the key, so
        # say so and let the auditor retry.
        return jsonify({"ok": False, "error": str(exc), "retry": True}), 503
    except Exception as exc:
        app.logger.error("ask failed: %s", traceback.format_exc())
        return jsonify({"ok": False, "error": "The model call failed: %s" % exc}), 502


# --------------------------------------------------------------------------- #
# Tab 2 -- prohibited-purchase dashboard
# --------------------------------------------------------------------------- #

@app.get("/api/search")
def api_search():
    field = request.args.get("field", "Description")
    # Repeated ?q= lets one search cover every term in a prohibited category.
    keywords = request.args.getlist("q") or [request.args.get("q", "")]
    year = request.args.get("year") or None
    min_amount = request.args.get("min_amount") or None
    try:
        result = pcard_db.search(field, keywords, year, min_amount)
        result["ok"] = True
        return jsonify(result)
    except pcard_db.QueryRejected as exc:
        return jsonify({"ok": False, "error": str(exc)}), 400
    except Exception as exc:
        app.logger.error("search failed: %s", traceback.format_exc())
        return jsonify({"ok": False, "error": str(exc)}), 500


def _csv_response(columns, rows, filename):
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(columns)
    for row in rows:
        writer.writerow([row.get(c) for c in columns])
    return Response(
        buf.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": 'attachment; filename="%s"' % filename},
    )


@app.get("/api/search.csv")
def api_search_csv():
    """Same search, delivered as a CSV working paper."""
    field = request.args.get("field", "Description")
    keywords = request.args.getlist("q") or [request.args.get("q", "")]
    year = request.args.get("year") or None
    min_amount = request.args.get("min_amount") or None
    result = pcard_db.search(field, keywords, year, min_amount, limit=50_000)

    slug = "".join(ch if ch.isalnum() else "_" for ch in "_".join(keywords))[:40] or "search"
    return _csv_response(result["columns"], result["rows"],
                         "pcard_%s_%s_%s.csv" % (field.lower(), slug, year or "all"))


@app.post("/api/ask.csv")
def api_ask_csv():
    """Export the result of a question the auditor already ran.

    The query comes back from the browser rather than being re-generated, so the
    CSV is the same population that was on screen. It goes through the same
    read-only guard, so nothing here can be used to run something the Ask tab
    would have refused.
    """
    payload = request.get_json(silent=True) or {}
    sql = (payload.get("sql") or "").strip()
    if not sql:
        return jsonify({"ok": False, "error": "No query to export."}), 400
    try:
        columns, rows, _ = pcard_db.run_select(sql, limit=50_000)
    except pcard_db.QueryRejected as exc:
        return jsonify({"ok": False, "error": str(exc)}), 400
    return _csv_response(columns, rows, "pcard_question_result.csv")


@app.get("/api/health")
def api_health():
    try:
        pcard_db.run_select("SELECT 1 AS ok", limit=1)
        return jsonify({"ok": True, "database": os.path.basename(pcard_db.DB_PATH),
                        "nl_enabled": nl_query.configured(),
                        "provider": nl_query.provider(),
                        "model": nl_query.model_name()})
    except Exception as exc:
        return jsonify({"ok": False, "error": str(exc)}), 500


if __name__ == "__main__":
    if _ENV_KEYS:
        # Names only -- never print a value.
        print("loaded from .env: %s" % ", ".join(sorted(_ENV_KEYS)))
    if nl_query.configured():
        print("model provider : %s (%s)" % (nl_query.provider(), nl_query.model_name()))
    else:
        print("warning: no ANTHROPIC_API_KEY or GEMINI_API_KEY - the 'Ask the data' tab "
              "is disabled; the dashboard still works.")
    app.run(host=os.environ.get("HOST", "127.0.0.1"),
            port=int(os.environ.get("PORT", 5000)),
            debug=os.environ.get("FLASK_DEBUG") == "1")
