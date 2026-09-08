# Analytics Mindset — P-Card case (Oklahoma State University)

Internal-audit analysis of OSU purchasing-card transactions for calendar year 2014, plus the
auditor-facing web tool required by Part IV.

| Deliverable | Link |
|---|---|
| **Live website** | https://pcard-audit-workbench.onrender.com |
| **GitHub repository** | https://github.com/AmirA210703/pcard-audit |
| **Completed assignment document** | [`Analytics_mindset_PCard_assignment_COMPLETED.docx`](Analytics_mindset_PCard_assignment_COMPLETED.docx) |

The site is on Render's free plan, which sleeps after 15 minutes idle — the first request
after a quiet spell takes about 40 seconds to wake, and is normal after that.

Source data: `pcards.db` — one table, `pcards`, 489,178 rows covering 2010–2014
(116,031 rows in 2014), all for agency 1000, Oklahoma State University. Cardholder names are
de-identified in the source file.

## What is here

| Path | Contents |
|---|---|
| `Analytics_mindset_PCard_assignment_COMPLETED.docx` | The assignment document with Parts II and III filled in — 22 SQLite queries and a results-and-conclusion write-up for each |
| `sql/` | Each query as a runnable `.sql` file (`qry_T2_Question1` … `qry_T3_Question8`) |
| `results/` | The output of every query as CSV (gitignored — regenerate with `make results`) |
| `webapp/` | Part IV: the two-tab P-Card Audit Workbench (see `webapp/README.md`) |
| `data/pcards.db.gz` | The database, compressed to 24 MB so the repository is self-contained |
| `scripts/prepare_db.py` | Expands that archive to the full ~115 MB database on first use |
| `render.yaml` | Deployment blueprint for the live site |
| `docgen/` | The script that writes the answers into the .docx, and the answer text itself |
| `run.sh` | `./run.sh sql/qry_T2_Question4.sql` runs one query against the database |

## Reproducing the analysis

```bash
python3 scripts/prepare_db.py                # expand data/pcards.db.gz, prints the path
export PCARD_DB=$(python3 scripts/prepare_db.py)
./run.sh sql/qry_T2_Question1.sql            # one query, formatted for reading
./run.sh sql/qry_T3_Question2.sql csv        # same query as CSV
make results                                 # every query -> results/*.csv
make doc                                     # rebuild the completed .docx
```

If you already have the original `pcards.db`, point `PCARD_DB` at it instead and skip the
first two lines. The committed archive is the same 489,178 rows (total `$164,412,724.26`),
VACUUMed and indexed on `Year` and `(Year, Month)`.

Every query is self-contained: it filters `Year = 2014` and
`AgencyName = 'OKLAHOMA STATE UNIVERSITY'` itself, and the ones that need a real date build
an ISO date from the `M/D/YYYY` text in a CTE.

## Part II — internal-control tests

| # | Control | Exceptions found |
|---|---|---|
| 1 | Annual spend over $50,000 | 127 cardholders, $15.53 m |
| 2 | Monthly spend over $10,000 | 457 cardholder-months (40 over $50,000) |
| 3 | Single transaction over $5,000 | 33 transactions, $357,871, 6 cardholders |
| 4 | Split between swipes of one card | 254 transactions in 66 clusters, $470,369 |
| 5 | Split between two cardholders | 24 vendor-days, $146,967 |
| 6 | Split between two vendors | 59 cardholder-days, $368,167 |
| 7 | Food while in travel status | 99 charges, 31 employees, $19,448 |
| 8 | Alcohol *(student-defined)* | 15 charges, $20,856 — one cardholder holds $17,418 of it |
| 9 | Gasoline *(student-defined)* | 730 charges, $296,421, 189 cardholders |
| 10 | Mail and postage *(student-defined)* | 89 charges, $14,726 |
| 11 | Gifts, flowers, decorations *(student-defined)* | 356 charges, $83,882 |
| 12 | Personal memberships and clubs *(student-defined)* | 147 charges, $79,239 |
| 13 | Cash / ATM / insurance / late fees *(student-defined)* | 18 charges, $9,823 — all insurance; **zero** cash, ATM or late fees |
| 14 | Recurring monthly agreements over $5,000/yr *(student-defined)* | 46 recurring patterns, 31 cardholder-vendor pairs |

## Part III — forensic analysis

| # | Test | Outcome |
|---|---|---|
| 1 | Benford's Law, first digit | MAD 0.318 pp — close conformity, **low** population-level fraud risk |
| 2 | Possible duplicate payments | 4,924 charges in 1,732 occasions; $670,115 upper-bound exposure |
| 3 | Employees repeatedly duplicated | 577 employees; top employee has 78 occasions |
| 4 | Four-digit round numbers | 160 charges, $343,004 — including 20 at exactly $5,000.00 |
| 5 | Structuring below the $5,000 limit *(student-defined)* | 269 charges in $4,500–4,999.99 vs 22 in $5,000–5,499.99 — a 12:1 cliff |
| 6 | Weekend and holiday purchasing *(student-defined)* | 452 cardholders, 5,717 charges, $1.27 m (travel MCCs excluded) |
| 7 | Sole-cardholder vendors *(student-defined)* | 32 vendor relationships, $632,602 |
| 8 | Credits with no matching charge *(student-defined)* | 358 credits, $91,855 |

Flagged transactions are potential exceptions requiring follow-up, not established
violations. Each conclusion in the document names the legitimate explanations and the
evidence needed to resolve the item.

## Part IV — the web tool

See [`webapp/README.md`](webapp/README.md). Two tabs: a natural-language question page backed
by a model provider — either **Gemini** (which has a free tier) or **Claude** — and a
prohibited-purchase dashboard with year selection and separate description and vendor
searches. Only `nl_query.py` touches the provider, so the two are interchangeable; no
transaction data is sent to the model, only the table definition and the question.

**The API key is never in this repository.** It is read from `GEMINI_API_KEY` or
`ANTHROPIC_API_KEY` at run time. Put it in `webapp/.env` (gitignored, loaded automatically at
start-up), export it in your shell, or set it as a platform secret when deploying — see
[`webapp/README.md`](webapp/README.md#protecting-the-api-key) for all three, plus
`webapp/check_secrets.sh`, which can be installed as a pre-commit hook that refuses to let a
key reach git.

## Deploying the live site

### Why not GitHub Pages

GitHub Pages serves static files only — there is no server process behind it. That rules it
out twice over:

* **The API key would be exposed.** With no server, the only place left to put the key is
  the JavaScript sent to the browser, where anyone can read it with View Source. That is
  precisely the exposure the assignment penalises. A key has to be held by a server that
  the browser talks to, which is what `/api/ask` is.
* **There is nothing to run the SQL.** The queries are executed by Python against a 115 MB
  SQLite file. Pages cannot run Python, and shipping the database to the browser would mean
  a 24 MB download on every visit.

So the site needs a host that runs a process. Render's free tier is the shortest path and
is what `render.yaml` is written for.

### Render, from the browser

1. **Push this repository to GitHub** (see below), then sign in at
   [render.com](https://render.com) with that GitHub account.
2. **New → Blueprint**, pick the repository. Render reads `render.yaml` and fills in the
   build command, start command, Python version and health check itself.
3. It will **prompt for `GEMINI_API_KEY`**, because that variable is marked `sync: false`.
   Paste the key from [aistudio.google.com/apikey](https://aistudio.google.com/apikey)
   there. Render stores it as a secret and injects it at run time — it never reaches the
   repository or the build log.
4. **Apply.** The first build takes a few minutes: it installs the dependencies and expands
   `data/pcards.db.gz`. Your URL is `https://pcard-audit-workbench.onrender.com`.
5. Check `https…/api/health`. It should return `"ok": true` and `"nl_enabled": true`. If
   `nl_enabled` is `false`, the key did not arrive — re-add it under
   **Environment** and redeploy.

On the free plan the service sleeps after 15 minutes idle, so the first visit after a quiet
spell takes around 40 seconds to wake. Open the link once yourself shortly before anyone
else needs it.

### The same repository on Hugging Face Spaces

An alternative if you would rather not have the cold start: create a **Docker** Space, push
this repository to it, and add `GEMINI_API_KEY` under **Settings → Secrets**.
`webapp/Dockerfile` already listens on port 7860, which is what Spaces expects. A Space
stays warm far longer and needs no card on file.
