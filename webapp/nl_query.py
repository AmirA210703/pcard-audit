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

import pcard_db

ANTHROPIC_MODEL = os.environ.get("ANTHROPIC_MODEL", "claude-opus-5")
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-3.7-flash")
MAX_TOKENS = 8000

# Free-tier capacity moves around, and the newest model is the most contended --
# a question can come back "503 ... currently experiencing high demand" or a 504
# through no fault of the request.  So a busy model is retried on the next name
# here instead of failing the auditor's question.  GEMINI_MODEL is tried first,
# whatever it is set to.
#
# This order was measured against a new free-tier key: 3.7 answered in 1.4 s,
# 3.6 in 3.9 s, 3.5 in 8.0 s and 3.5-flash-lite in 0.6 s, while the flagship
# gemini-3.8-flash timed out and the 2.5 series returns 404 "no longer available
# to new users".  Deliberately no 2.5 entries and no `-latest` alias, which
# resolves to the flagship and inherits its queue.
GEMINI_FALLBACKS = [
    "gemini-3.7-flash",
    "gemini-3.6-flash",
    "gemini-3.5-flash",
    "gemini-3.5-flash-lite",
]

# Per attempt, in milliseconds.  This has to leave room for several attempts
# inside the ~100 s that hosting proxies allow before they return their own
# error page -- which would reach the browser as HTML, not JSON.
GEMINI_TIMEOUT_MS = 20_000


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


# Conditions that another model might not be suffering from: capacity, and the
# per-model free-tier quota.
_TRY_ANOTHER_MODEL = (
    "503", "unavailable", "high demand", "overloaded", "capacity",
    "429", "resource_exhausted", "quota", "rate limit", "timeout", "timed out",
)


def _transient(exc) -> bool:
    """True when the failure is about this model rather than the request."""
    text = str(exc).lower()
    return any(token in text for token in _TRY_ANOTHER_MODEL)


def _gemini_candidates():
    """GEMINI_MODEL first, then the fallbacks, without repeats."""
    seen, out = set(), []
    for name in [GEMINI_MODEL] + GEMINI_FALLBACKS:
        if name and name not in seen:
            seen.add(name)
            out.append(name)
    return out


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

    candidates = _gemini_candidates()
    last = None
    for model in candidates:
        try:
            response = _one_model(model)
        except Exception as exc:
            # A model that is missing or busy is worth trying the next name for;
            # anything else (a bad key, a malformed request) is not.
            if _model_not_found(exc) or _transient(exc):
                last = exc
                continue
            raise
        return (response.text or ""), model

    # Every candidate failed the same way, so report the underlying cause plainly
    # rather than as a generic 502.
    if last is not None and _transient(last):
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


def to_sql(question: str, history=None) -> dict:
    """Ask the configured provider for a query. Returns sql / explanation / answerable."""
    name = provider()
    if name is None:
        raise NotConfigured(_NO_KEY)

    text, used_model = _BACKENDS[name](question, history)
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
