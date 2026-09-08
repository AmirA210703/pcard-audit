# OSU P-Card Audit Workbench

A two-tab web tool for the internal audit of Oklahoma State University purchasing-card
transactions (Part IV of the Analytics Mindset P-card case).

| Tab | What it does |
|---|---|
| **Ask the data** | Auditors type a question in plain language. A model writes a SQLite query, the server runs it **read-only** and shows the answer *together with the query and an explanation*, so the auditor can check the logic before relying on it. Works with either Claude or Gemini. |
| **Prohibited purchases** | A dashboard for the purchase types the P-card procedure forbids. Choose a year, then search either the **transaction description** or the **vendor name**. All 14 prohibited categories are listed with pre-loaded search terms and notes on their known false positives. |

## Choosing a model provider

The "Ask the data" tab needs one model provider. Set **one** of these keys and the app picks
it up automatically; `AI_PROVIDER=gemini` or `AI_PROVIDER=anthropic` forces a choice when
both are set.

| Provider | Key variable | Where to get it | Cost |
|---|---|---|---|
| **Gemini** | `GEMINI_API_KEY` | [aistudio.google.com/apikey](https://aistudio.google.com/apikey) | Has a free tier |
| **Claude** | `ANTHROPIC_API_KEY` | [platform.claude.com/settings/keys](https://platform.claude.com/settings/keys) | Paid (prepaid credits) |

Only `nl_query.py` talks to a provider, so switching one out changes nothing else: the SQL
guard, the read-only execution, the dashboard and the whole front end are provider-agnostic.

**What is sent to the provider.** Only the table definition and the auditor's question. No
transaction rows ever leave the server — the model writes SQL, this server executes it. That
matters on Gemini's free tier, where Google states that content *is* used to improve their
products (the paid tier is excluded). An auditor's question can still be sensitive
("show me Employee 3B7AEC76's alcohol purchases"), so for real audit work use a paid tier;
for coursework the free tier is fine.

Gemini's free tier also has per-minute and per-day request limits. The dashboard tab is
unaffected — it never calls a model.

### Notes on the Claude key

Create it at **Create key** → name it, set **Linked account** to yourself, and **scope it to
a single workspace**. A key spanning several workspaces must name the workspace on every
request or you get `400 anthropic-workspace-id is required`; set `ANTHROPIC_WORKSPACE_ID` for
such a key. Copy the `sk-ant-api...` value when it is shown; if you lose it, create a new key
and delete the old one.

## Protecting the API key

Whichever provider you use, the key is read from the environment at run time and appears
nowhere in this repository. There are three ways to supply it; pick one.

### 1. A local `.env` file (easiest for development)

```bash
cp .env.example .env
# edit .env, uncomment and fill in GEMINI_API_KEY *or* ANTHROPIC_API_KEY
chmod 600 .env            # readable only by you
python app.py
```

`envfile.py` loads `.env` into the environment at start-up, before anything else runs, so
this works with `python app.py` and with `gunicorn app:app` alike. On start-up the app
prints the *names* of the keys it loaded, never the values.

`.env` is listed in `.gitignore`, so git will not offer it for commit and `git add .` will
skip it. `.env.example` is the only one committed, and it contains a placeholder.

A real environment variable always beats the file, so you can override for a single run:

```bash
ANTHROPIC_API_KEY=sk-ant-other-key python app.py
```

### 2. Export it in your shell

Nothing is written to disk in the project at all:

```bash
export GEMINI_API_KEY=AIza...          # or ANTHROPIC_API_KEY=sk-ant-...
export PCARD_DB=/path/to/pcards.db
python app.py
```

To make it persistent, put the `export` line in `~/.zshrc` (not in a project file). On macOS
you can keep it out of a plaintext dotfile entirely by storing it in the login keychain:

```bash
# once
security add-generic-password -a "$USER" -s pcard-anthropic-key -w 'sk-ant-...'
# in ~/.zshrc
export ANTHROPIC_API_KEY=$(security find-generic-password -a "$USER" -s pcard-anthropic-key -w)
```

### 3. A platform secret (for the deployed site)

Never put the key in a file you deploy. Set it as a secret in the hosting platform's own
store, where it is injected as an environment variable at run time:

| Platform | Command / location |
|---|---|
| Render | Dashboard → Service → **Environment** → Add Environment Variable |
| Fly.io | `fly secrets set GEMINI_API_KEY=AIza...` |
| Heroku | `heroku config:set GEMINI_API_KEY=AIza...` |
| Railway | Project → **Variables** |
| Docker | `docker run -e GEMINI_API_KEY=... ...` (not `ENV` in the Dockerfile) |

### Checking before you push

`check_secrets.sh` blocks anything that looks like a real key. Run it by hand, or install it
as a git hook so it runs on every commit:

```bash
./webapp/check_secrets.sh                                              # check now
ln -sf ../../webapp/check_secrets.sh .git/hooks/pre-commit             # check on every commit
```

It scans your staged changes (or the working tree if nothing is staged) for a long
`sk-ant-...` or `AIza...` string, and separately fails if a `.env` file has become tracked.
It ignores
`.env` itself, because that file is gitignored, but it does still scan `.env.example`, since
that one *is* committed.

Two other habits worth keeping:

* Confirm `.gitignore` is committed **before** the first `git add`. If a key ever does get
  committed, removing it in a later commit is not enough — it stays in the history. Rotate
  the key in the Anthropic Console instead; that is the only real fix.
* No key is ever sent to the browser. The `/api/ask` endpoint calls the model server-side,
  so nothing sensitive appears in page source or in network requests the user can see.

## Running locally

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

export PCARD_DB=/path/to/pcards.db
export ANTHROPIC_API_KEY=sk-ant-...      # only needed for the "Ask the data" tab
python app.py                            # http://127.0.0.1:5000
```

The dashboard tab works without an API key; the natural-language tab shows a clear notice
if the key is missing.

### Environment variables

| Variable | Required | Default | Purpose |
|---|---|---|---|
| `PCARD_DB` | no | system temp dir | Where the database is; expanded from `data/pcards.db.gz` if not already there |
| `DB_CACHE_DIR` | no | system temp dir | Used instead of `PCARD_DB` to decide where to expand |
| `ENV_FILE` | no | `./.env` | Alternative location for the env file |
| `GEMINI_API_KEY` | for tab 1 (option A) | — | Google AI Studio key; `GOOGLE_API_KEY` also works |
| `ANTHROPIC_API_KEY` | for tab 1 (option B) | — | Anthropic API key |
| `AI_PROVIDER` | no | whichever key is set | `gemini` or `anthropic` |
| `GEMINI_MODEL` | no | `gemini-3.8-flash` | Gemini model that writes the SQL |
| `ANTHROPIC_MODEL` | no | `claude-opus-5` | Claude model that writes the SQL |
| `ANTHROPIC_WORKSPACE_ID` | only for a multi-workspace key | — | Workspace the request runs in |
| `PORT` / `HOST` | no | `5000` / `127.0.0.1` | Local server binding |

## Deploying

```bash
gunicorn --bind 0.0.0.0:$PORT --workers 2 --timeout 120 app:app
```

`render.yaml` (repository root), `Procfile` and `Dockerfile` are included. The full
walkthrough is in the [root README](../README.md#deploying-the-live-site).

**The host needs no database upload.** The expanded database is ~115 MB, more than a git
host wants, so what is committed is `data/pcards.db.gz` (24 MB) and `scripts/prepare_db.py`
expands it in place — during the build if you call it there, otherwise on first start-up.
It checks the row count afterwards and will not reuse a half-written file, so a killed
build recovers on the next boot. Point `PCARD_DB` at a path inside the deploy (not `/tmp`,
which some hosts wipe between the build and the run).

The `--timeout 120` matters because a model call plus a query over 489,178 rows can take
longer than gunicorn's 30-second default.

**GitHub Pages will not work for this app**, and not only for convenience reasons: Pages
serves static files with no server, so the API key would have to sit in JavaScript that
every visitor can read — the exact exposure the assignment penalises. The key must stay on
a server. See the root README for the reasoning in full.

## How the data is treated

* The SQLite connection is opened with `mode=ro`, so no request can modify the evidence file.
* Every generated query passes `pcard_db.guard()`: one statement only, must start with
  `SELECT` or `WITH`, and any write / `ATTACH` / `PRAGMA` keyword is rejected.
* A SQLite progress handler stops any query still running after 20 seconds.
* Dashboard searches are parameter-bound — a keyword such as `%' OR 1=1 --` is treated as
  literal text, never as SQL.
* Output to the browser is capped at 500 rows; the CSV export returns the full population.

## Files

```
app.py            Flask routes (pages, /api/ask, /api/search, /api/search.csv, /api/health)
envfile.py        loads .env into the environment before anything else starts
check_secrets.sh  pre-commit guard: refuses to let an API key reach git
pcard_db.py       read-only database access, the SQL guard, dashboard searches
nl_query.py       schema prompt + provider call (Claude or Gemini) + guarded execution
prohibited.py     the 14 prohibited-purchase categories, search terms and false-positive notes
templates/        index.html
static/           style.css, app.js
```

## Known limitations

* Cardholder names are de-identified in the source data (`Employee 51914657`), and the table
  has no department, approver or account column — so questions about departments or
  approvers cannot be answered. The model is instructed to say so rather than invent a column.
* `Description` is supplied by the merchant and is `GENERAL PURCHASE` for about 65% of 2014
  rows, so a description search cannot be exhaustive. Vendor and MCC searching compensates.
* Transaction dates are stored as `M/D/YYYY 0:00:00` text with no zero padding and cannot be
  compared as strings. The schema prompt shows the model the ISO-date CTE to use instead.
* Every hit is a potential exception. Obtain the receipt and the business purpose recorded in
  Works before concluding that a purchase breached policy.
