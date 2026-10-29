"""Natural-language -> SQLite translation for the auditor question page.

Two model providers are supported; the app uses whichever key is present:

    ANTHROPIC_API_KEY  ->  Claude   (pip install anthropic)
    GEMINI_API_KEY     ->  Gemini   (pip install google-genai)

Set AI_PROVIDER to "anthropic" or "gemini" to force one when both keys exist.
The key is read from the environment and never appears in this repository.

The provider only ever writes SQL.  It is not given any transaction data: the
prompt contains the table definition and the auditor's question, nothing else.
Whatever comes back is put through pcard_db.guard() and executed read-only by
this server, so a wrong or hostile query cannot read outside the one table or
change anything.
"""
from __future__ import annotations

import json
import os
import re
import threading
import time
from concurrent.futures import FIRST_COMPLETED, ThreadPoolExecutor, wait

import pcard_db

# Same reasoning as the Gemini default below: this is a small, well-specified
# translation job, so the cheap fast tier is the right choice.
ANTHROPIC_MODEL = os.environ.get("ANTHROPIC_MODEL", "claude-haiku-4-5-20251001")
# Turning one plain-language question into one SELECT is a small job, so the
# cheapest, fastest tier is the right default -- a larger model buys nothing here
# and is markedly slower under free-tier load.
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-3.5-flash-lite")
MAX_TOKENS = 8000

# Free-tier capacity moves around, so a busy model is retried on the next name
# here rather than failing the auditor's question.  GEMINI_MODEL is tried first,
# whatever it is set to, then the fast "lite" models, then the larger ones.
#
# Measured on this exact workload (the schema prompt plus a real question):
# 3.5-flash-lite answered in 1.4 s using 1,421 tokens, 3.7-flash in 3.5 s using
# 2,014, and 3.1-flash-lite in 4.0 s.  Deliberately absent:
#   * gemini-3.6-flash    -- 504 DEADLINE_EXCEEDED after 44 s
#   * gemini-3.8-flash    -- flagship, consistently out of capacity
#   * gemini-flash-latest -- an alias for the flagship, so it inherits its queue
#   * the whole 2.5 series -- 404 "no longer available to new users"
GEMINI_FALLBACKS = [
    "gemini-3.5-flash-lite",
    "gemini-3.1-flash-lite",
    "gemini-3.7-flash",
    "gemini-3.5-flash",
]

# Per attempt, in milliseconds.  The SDK also sends this to Google as the
# server-side deadline, so a model that is stuck in a queue ends with a 504.
GEMINI_TIMEOUT_MS = 20_000

# A healthy model answers in 1-4 s.  If the current attempt has not answered
# after HEDGE_AFTER_S, the next model is started alongside it and whichever
# answers first wins -- a slow model no longer holds the question hostage.
HEDGE_AFTER_S = float(os.environ.get("AI_HEDGE_AFTER_S", "4"))

# The whole question gives up after this, well inside the ~100 s a hosting
# proxy allows before it returns its own HTML error page instead of our JSON.
TOTAL_DEADLINE_S = float(os.environ.get("AI_TOTAL_DEADLINE_S", "45"))

# A model that just failed is moved to the back of the queue for this long, and
# the model that answered last is tried first, so only the first question after
# an outage pays for discovering it.
COOLDOWN_S = float(os.environ.get("AI_COOLDOWN_S", "300"))


# Values left over from .env.example. Treated as "not set" so that the user gets a
# clear instruction instead of a raw 401 from the provider.
_PLACEHOLDERS = ("REPLACE-ME", "REPLACE_ME", "PASTE_YOUR_KEY_HERE", "PASTE-YOUR-KEY-HERE")


def _real(value):
    """The key, or None if it is blank or still a placeholder."""
    value = (value or "").strip()
    if not value:
        return None
    if any(token in value.upper() for token in _PLACEHOLDERS):
        return None
    return value


def _model_not_found(exc) -> bool:
    """True when the provider rejected the model name itself."""
    text = str(exc).lower()
    return "not found" in text or "404" in text or "unsupported model" in text


# Conditions that another model might not be suffering from: capacity, the
# per-model free-tier quota, and a model that is simply too slow to answer.
#
# 504 / DEADLINE_EXCEEDED belongs here and was missing, which is what made a
# deadline read as a permanent failure: the chain stopped on the first model
# instead of moving to the next one, and the auditor got a bare
# "The model call failed: 504 DEADLINE_EXCEEDED".
_TRY_ANOTHER_MODEL = (
    "503", "unavailable", "high demand", "overloaded", "capacity",
    "504", "deadline", "timeout", "timed out",
    "429", "resource_exhausted", "quota", "rate limit",
    "500 internal", "internal error",
)


def _transient(exc) -> bool:
    """True when the failure is about this model rather than the request."""
    text = str(exc).lower()
    return any(token in text for token in _TRY_ANOTHER_MODEL)


# Per worker process: model -> time until which it counts as unhealthy, and the
# model that answered most recently.
_health_lock = threading.Lock()
_cooling_until: dict[str, float] = {}
_last_good: list[str] = []


def _mark_failed(model):
    with _health_lock:
        _cooling_until[model] = time.monotonic() + COOLDOWN_S
        if _last_good and _last_good[0] == model:
            _last_good.clear()


def _mark_ok(model):
    with _health_lock:
        _cooling_until.pop(model, None)
        _last_good[:] = [model]


def _gemini_candidates():
    """The order to try models in for this question.

    The last model that answered goes first, then GEMINI_MODEL and the fallbacks
    in their configured order.  Models that failed within COOLDOWN_S are not
    dropped -- they go to the back, as a last resort.
    """
    seen, out = set(), []
    with _health_lock:
        preferred = list(_last_good)
        cooling = {m for m, until in _cooling_until.items() if until > time.monotonic()}
    for name in preferred + [GEMINI_MODEL] + GEMINI_FALLBACKS:
        if name and name not in seen:
            seen.add(name)
            out.append(name)
    return [m for m in out if m not in cooling] + [m for m in out if m in cooling]


def _race(candidates, attempt):
    """Run `attempt(model)` down the candidate list and return the first success.

    The next candidate is started as soon as the current one fails, or after
    HEDGE_AFTER_S if it is merely slow; earlier attempts keep running, so a slow
    model that does answer can still win.  An error that another model would
    not fix (a bad key, a malformed request) is raised at once.
    """
    queue = list(candidates)
    pending = {}
    last = None
    deadline = time.monotonic() + TOTAL_DEADLINE_S
    pool = ThreadPoolExecutor(max_workers=len(queue))

    def launch():
        model = queue.pop(0)
        pending[pool.submit(attempt, model)] = model
        return model

    try:
        newest = launch()
        while pending:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                break
            done, _ = wait(pending, return_when=FIRST_COMPLETED,
                           timeout=min(HEDGE_AFTER_S, remaining) if queue else remaining)
            if not done:
                if queue:
                    # Too slow to be first choice for the next question either.
                    _mark_failed(newest)
                    newest = launch()
                continue
            for future in done:
                model = pending.pop(future)
                try:
                    result = future.result()
                except Exception as exc:
                    if not (_model_not_found(exc) or _transient(exc)):
                        raise
                    last = exc
                    if queue:
                        newest = launch()
                    continue
                _mark_ok(model)
                return result
    finally:
        # Abandoned attempts finish on their own within GEMINI_TIMEOUT_MS.
        pool.shutdown(wait=False, cancel_futures=True)

    if last is None:
        last = TimeoutError("timed out: no model answered within %.0f s" % TOTAL_DEADLINE_S)
    raise last


def _gemini_key():
    # The Google SDK reads either name, with GOOGLE_API_KEY taking precedence.
    return _real(os.environ.get("GOOGLE_API_KEY")) or _real(os.environ.get("GEMINI_API_KEY"))


def _anthropic_key():
    return _real(os.environ.get("ANTHROPIC_API_KEY"))


def provider():
    """Which provider to use: an explicit choice, else whichever key is set."""
    choice = (os.environ.get("AI_PROVIDER") or "").strip().lower()
    if choice in {"anthropic", "claude"}:
        return "anthropic"
    if choice in {"gemini", "google"}:
        return "gemini"
    if _anthropic_key():
        return "anthropic"
    if _gemini_key():
        return "gemini"
    return None


def configured():
    """True when the question page can actually call a model."""
    name = provider()
    if name == "anthropic":
        return bool(_anthropic_key())
    if name == "gemini":
        return bool(_gemini_key())
    return False


def model_name():
    return {"anthropic": ANTHROPIC_MODEL, "gemini": GEMINI_MODEL}.get(provider(), "none")

SCHEMA_DOC = """\
The database has exactly one table.

CREATE TABLE pcards (
    Year                   INTEGER,  -- calendar year of TransactionDate
    Month                  INTEGER,  -- calendar month of TransactionDate (1-12)
    FullName               TEXT,     -- de-identified cardholder, e.g. 'Employee 51914657'
    ID                     INTEGER,  -- row id, unique within a month
    AgencyNumber           INTEGER,  -- always 1000
    AgencyName             TEXT,     -- always 'OKLAHOMA STATE UNIVERSITY'
    CardholderLastName     TEXT,     -- e.g. 'Employee51914657'
    CardholderFirstInitial TEXT,
    Description            TEXT,     -- merchant-supplied line detail; often 'GENERAL PURCHASE'
    Amount                 REAL,     -- positive = charge, negative = credit / return
    Vendor                 TEXT,     -- merchant name as it appears on the statement
    TransactionDate        TEXT,     -- 'M/D/YYYY 0:00:00'  (no leading zeros!)
    PostedDate             TEXT,     -- 'M/D/YYYY 0:00:00'
    MCC                    TEXT      -- Merchant Category Code description, e.g. 'HARDWARE STORES'
);

Facts an auditor needs to know:
* Years present: 2010-2014.  2010 is a partial year.  The audit year is 2014.
* 489,178 rows in total; 116,031 of them are 2014.
* Dates are TEXT in US format with no zero padding, so they cannot be compared or
  sorted as strings.  Use Year and Month for period filters.  When a real date is
  needed, build an ISO date like this:

  WITH parsed AS (
      SELECT p.*,
             substr(p.TransactionDate, 1, instr(p.TransactionDate, '/') - 1) AS m_raw,
             substr(p.TransactionDate, instr(p.TransactionDate, '/') + 1)    AS rest
      FROM pcards AS p
      WHERE p.Year = 2014
  ),
  osu2014 AS (
      SELECT parsed.*,
             printf('%04d-%02d-%02d',
                    CAST(substr(rest, instr(rest, '/') + 1, 4) AS INTEGER),
                    CAST(m_raw AS INTEGER),
                    CAST(substr(rest, 1, instr(rest, '/') - 1) AS INTEGER)) AS TxnDate
      FROM parsed
  )
  SELECT ... FROM osu2014 ...

  strftime('%w', TxnDate) then gives the weekday (0 = Sunday, 6 = Saturday).
* MCC holds a text description, not a numeric code, so match it with
  UPPER(MCC) LIKE '%...%'.
* Amount is a REAL; positive rows are charges and negative rows are credits or
  returns.  Exclude negatives with Amount > 0 when counting purchases.
* FullName is de-identified.  There is no department, approver or account column,
  so questions about departments or approvers cannot be answered from this table --
  say so rather than inventing a column.

The internal controls being audited:
* single transaction limit  $5,000
* cycle (monthly) credit limit  ceiling $50,000; departmental justification needed above $10,000
* split purchasing to evade the $5,000 limit is prohibited
* prohibited purchases include alcohol, cash / cash advances / ATM, decorations,
  donations and sponsorships, gasoline, gifts and gift cards, insurance, late fees,
  mail and postage, moving expenses, personal purchases, personal or individual
  memberships and dues, salaries and benefits, service and incentive awards,
  food and mileage while in travel status, and prepayments or deposits.
"""

SYSTEM_PROMPT = """\
You are a data analyst supporting an internal audit of Oklahoma State University's
purchasing-card (P-card) transactions. You turn an auditor's question into ONE SQLite
query against the single table described below, and explain in plain language what the
query does and how the auditor should read the result.

%s

Rules for the SQL you write:
1. Produce exactly ONE statement. It must be a SELECT, or a WITH ... SELECT. Never write
   INSERT, UPDATE, DELETE, DROP, ALTER, CREATE, ATTACH or PRAGMA -- the server rejects them.
2. Do not end the statement with a semicolon.
3. Only the pcards table exists. Common table expressions are fine.
4. If the auditor does not name a year, default to the audit year 2014 and say so in the
   explanation.
5. Return only the columns the auditor needs, and give them readable aliases.
6. Always ORDER BY something meaningful (usually the amount or the count, largest first).
7. Add a LIMIT when the question implies a "top N"; the server caps output at 500 rows
   regardless.
8. Round money with ROUND(x, 2).
9. If the question cannot be answered from these columns, still return a query that gets
   as close as possible, and use the explanation to state exactly what is missing.

In the explanation, write for an auditor, not a programmer: say what population the query
selects, what would make a returned row a potential exception, and name the most likely
false positives. Two to four sentences.
""" % SCHEMA_DOC

RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "sql": {"type": "string", "description": "The single SQLite SELECT statement."},
        "explanation": {"type": "string", "description": "Plain-language explanation for an auditor."},
        "answerable": {
            "type": "boolean",
            "description": "False when the question cannot be answered from these columns.",
        },
    },
    "required": ["sql", "explanation", "answerable"],
    "additionalProperties": False,
}


class NotConfigured(Exception):
    """Raised when no usable API key is available."""


class Unavailable(Exception):
    """Raised when the provider is reachable but has no capacity right now.

    Kept separate from NotConfigured because the remedy is different: waiting,
    not fixing a key or a model name.
    """


_NO_KEY = (
    "The natural-language page needs an API key for a model provider. Put a real key on "
    "the GEMINI_API_KEY line of webapp/.env (get one at https://aistudio.google.com/apikey) "
    "or on the ANTHROPIC_API_KEY line, then restart the server. If the line still reads "
    "PASTE_YOUR_KEY_HERE or REPLACE-ME it does not count as set. The prohibited-purchase "
    "dashboard works without a key."
)

_JSON_BLOCK = re.compile(r"\{.*\}", re.DOTALL)


def _parse(text: str) -> dict:
    """Read the provider's reply as JSON, tolerating any prose around it."""
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        m = _JSON_BLOCK.search(text)
        if not m:
            raise ValueError("The model did not return JSON:\n" + text[:500])
        return json.loads(m.group(0))


def _messages(question: str, history=None):
    """Trim the conversation to the last few turns, in role/content form."""
    turns = []
    for turn in (history or [])[-6:]:
        if turn.get("role") in {"user", "assistant"} and turn.get("content"):
            turns.append({"role": turn["role"], "content": str(turn["content"])[:4000]})
    turns.append({"role": "user", "content": question})
    return turns


# --------------------------------------------------------------------------- #
# Claude
# --------------------------------------------------------------------------- #

def _ask_anthropic(question: str, history=None) -> str:
    if not _anthropic_key():
        raise NotConfigured(_NO_KEY)
    try:
        import anthropic
    except ImportError as exc:  # pragma: no cover
        raise NotConfigured(
            "AI_PROVIDER is anthropic but the 'anthropic' package is not installed "
            "(pip install -r requirements.txt)."
        ) from exc

    # A key that is not scoped to a single workspace must name the workspace on
    # every request, or the API returns 400 "anthropic-workspace-id is required".
    workspace = os.environ.get("ANTHROPIC_WORKSPACE_ID")
    client = (anthropic.Anthropic(default_headers={"anthropic-workspace-id": workspace})
              if workspace else anthropic.Anthropic())

    kwargs = dict(
        model=ANTHROPIC_MODEL,
        max_tokens=MAX_TOKENS,
        system=SYSTEM_PROMPT,
        messages=_messages(question, history),
    )
    try:
        try:
            response = client.messages.create(
                output_config={"format": {"type": "json_schema", "schema": RESPONSE_SCHEMA}},
                **kwargs
            )
        except TypeError:
            # Older anthropic SDK without output_config -- ask for JSON in the prompt.
            kwargs["system"] += (
                '\n\nReply with a single JSON object and nothing else: '
                '{"sql": "...", "explanation": "...", "answerable": true}'
            )
            response = client.messages.create(**kwargs)
    except Exception as exc:
        # Overloaded / rate-limited: reported as Unavailable so that to_sql() can
        # hand the question to the other provider if one is configured.
        if _transient(exc) or "529" in str(exc):
            raise Unavailable("Claude is busy right now: %s" % exc) from exc
        raise

    text = "".join(b.text for b in response.content if getattr(b, "type", None) == "text")
    return text, ANTHROPIC_MODEL


# --------------------------------------------------------------------------- #
# Gemini
# --------------------------------------------------------------------------- #

def _ask_gemini(question: str, history=None) -> str:
    key = _gemini_key()
    if not key:
        raise NotConfigured(_NO_KEY)
    try:
        from google import genai
        from google.genai import types
    except ImportError as exc:
        raise NotConfigured(
            "AI_PROVIDER is gemini but the 'google-genai' package is not installed "
            "(pip install google-genai)."
        ) from exc

    # Cap each attempt, so that walking the fallback list still finishes before a
    # hosting proxy gives up and replaces our JSON with its own HTML error page.
    try:
        client = genai.Client(
            api_key=key,
            http_options=types.HttpOptions(timeout=GEMINI_TIMEOUT_MS),
        )
    except TypeError:
        # Older SDKs do not accept http_options here.
        client = genai.Client(api_key=key)

    # Gemini has no assistant/user message objects in this call, so the prior
    # turns are folded into the prompt text.
    turns = _messages(question, history)
    prompt = "\n\n".join(
        ("Auditor: " if t["role"] == "user" else "Previous answer: ") + t["content"]
        for t in turns
    )

    base = dict(
        system_instruction=SYSTEM_PROMPT,
        max_output_tokens=MAX_TOKENS,
        response_mime_type="application/json",
    )

    def _call(model, config_kwargs):
        return client.models.generate_content(
            model=model,
            contents=prompt,
            config=types.GenerateContentConfig(**config_kwargs),
        )

    def _one_model(model):
        try:
            return _call(model, dict(base, response_json_schema=RESPONSE_SCHEMA))
        except Exception as exc:
            if _model_not_found(exc) or _transient(exc):
                raise
            # Not every model / SDK version accepts a full JSON Schema here. JSON
            # mode plus the schema described in the prompt is enough, because
            # _parse() is tolerant and pcard_db.guard() is the real safety net.
            return _call(model, base)

    def _attempt(model):
        # Failures are recorded here, in the worker thread, so that an attempt
        # the race has already given up on still marks its model when it ends.
        # Success is recorded by _race(), and only for the answer it used.
        try:
            response = _one_model(model)
        except Exception as exc:
            if _model_not_found(exc) or _transient(exc):
                _mark_failed(model)
            raise
        return (response.text or ""), model

    candidates = _gemini_candidates()
    try:
        return _race(candidates, _attempt)
    except Exception as exc:
        if not (_model_not_found(exc) or _transient(exc)):
            raise
        last = exc

    # Every candidate failed the same way, so report the underlying cause plainly
    # rather than as a generic 502.
    if _transient(last):
        raise Unavailable(
            "Gemini had no capacity for any of the models tried (%s). Google returns "
            "this when the free tier is busy; it is usually temporary, so wait a "
            "minute and ask again. The Prohibited purchases tab does not use the "
            "model and is unaffected.\n\nProvider said: %s"
            % (", ".join(candidates), last)
        ) from last
    raise NotConfigured(
        "None of the Gemini models tried (%s) accepted the request. Set GEMINI_MODEL "
        "to a current model from https://ai.google.dev/gemini-api/docs/models.\n\n"
        "Provider said: %s" % (", ".join(candidates), last)
    ) from last


_BACKENDS = {"anthropic": _ask_anthropic, "gemini": _ask_gemini}
_KEYS = {"anthropic": _anthropic_key, "gemini": _gemini_key}


def to_sql(question: str, history=None) -> dict:
    """Ask the configured provider for a query. Returns sql / explanation / answerable.

    When keys for both providers are set and the chosen one has no capacity,
    the question goes to the other one instead of failing.
    """
    name = provider()
    if name is None:
        raise NotConfigured(_NO_KEY)

    order = [name] + [other for other in _BACKENDS if other != name and _KEYS[other]()]
    for i, name in enumerate(order):
        try:
            text, used_model = _BACKENDS[name](question, history)
            break
        except Unavailable:
            if i == len(order) - 1:
                raise
    data = _parse(text)

    return {
        "sql": (data.get("sql") or "").strip(),
        "explanation": (data.get("explanation") or "").strip(),
        "answerable": bool(data.get("answerable", True)),
        "provider": name,
        # The model that actually answered, which is not always the configured
        # one when the first choice was out of capacity.
        "model": used_model,
    }


def ask(question: str, history=None) -> dict:
    """Full round trip: question -> SQL -> guarded read-only execution -> rows."""
    plan = to_sql(question, history)
    if not plan["sql"]:
        return {"ok": False, "error": "The model did not produce a query.", **plan}
    try:
        columns, rows, truncated = pcard_db.run_select(plan["sql"])
    except pcard_db.QueryRejected as exc:
        return {"ok": False, "error": "Query rejected: %s" % exc, **plan}
    except Exception as exc:  # SQL that the model got syntactically wrong
        return {"ok": False, "error": "SQLite could not run the query: %s" % exc, **plan}
    return {
        "ok": True,
        "columns": columns,
        "rows": rows,
        "truncated": truncated,
        "rowcount": len(rows),
        **plan
    }
