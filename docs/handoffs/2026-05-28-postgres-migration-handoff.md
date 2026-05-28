# Postgres migration handoff — 2026-05-28

> **For ao565 (and any future agent picking up this branch):** This document is the single source of truth for what's been done, what's been learned, and what's next. Read it end-to-end before doing anything else, then read the plan linked below.

## TL;DR

The Railway deploy at `https://gm2aquasolutions-production.up.railway.app` was wiping its SQLite DB on every redeploy because Railway containers have an ephemeral filesystem. We're migrating the Flask backend in `App/backend/` from on-disk SQLite to Railway Postgres via SQLAlchemy Core. The full 14-task implementation plan was written and is being executed on a feature branch.

- **Plan:** `docs/superpowers/plans/2026-05-28-sqlite-to-postgres-migration.md`
- **Branch:** `worktree-postgres-migration` on `origin`
- **State:** Tasks 1 and 2 complete (with code-review fixes), Tasks 3–14 pending
- **Pick up at:** Task 3 (port `conftest.py` to use `DATABASE_URL`)

---

## How to pick this up (do this first)

Assuming you've cloned the repo and have a working Python environment:

```bash
# Pull the in-flight branch
git fetch origin
git checkout worktree-postgres-migration
git pull

# Install backend deps (Task 1 added SQLAlchemy + psycopg)
python -m venv .venv
.venv/bin/pip install -r App/backend/requirements.txt

# Sanity-check the work-so-far is green
cd App/backend
DATABASE_URL=sqlite:///:memory: ../../.venv/bin/python -m pytest tests/test_engine.py tests/test_schema.py -v
# Expected: 7 passed
```

If those 7 tests pass, the engine module and the SQLAlchemy schema are working. The rest of the test suite is **intentionally red** — see *Expected red-state* below. Then read the plan, then Task 3.

---

## What's been done

### Pre-migration housekeeping (on `main`)

| SHA       | What                                                              |
| --------- | ----------------------------------------------------------------- |
| `869409e` | Untracked `App/backend/flask_server.log` and gitignored `*.log`. The log was being committed by mistake and on a Railway deploy it leaks `DEVICE_SECRET` and Twilio `From` numbers via gunicorn request logs. |
| `56a6eda` | Added the migration plan at `docs/superpowers/plans/2026-05-28-sqlite-to-postgres-migration.md`. |

### Migration work (on `worktree-postgres-migration`)

| Task | SHAs                  | What                                                                        |
| ---- | --------------------- | --------------------------------------------------------------------------- |
| 1    | `5ed9b6d`, `5118956`  | New `App/backend/engine.py` — SQLAlchemy `Engine` factory keyed off `DATABASE_URL`, rewrites `postgresql://` and `postgres://` to `postgresql+psycopg://`. `requirements.txt` updated. Two smoke tests + two regression tests in `tests/test_engine.py`. |
| 2    | `bfca632`, `d4b6acd`  | Full rewrite of `App/backend/database.py` to SQLAlchemy `MetaData` + `Table` declarations. Five tables, CHECK constraints, indexes, FKs. `connection()` yields a SQLAlchemy `Connection`. `_migrate()` uses `inspect()` for portable column introspection. `init_db()` runs `create_all` + `_migrate` + seed inside one `engine.begin()` transaction. Three tests in `tests/test_schema.py`. |

Each task went through the subagent-driven workflow: implementer → spec compliance reviewer → code quality reviewer → fix commit → re-review. The "second SHA" per task is the code-review fix commit.

---

## Findings worth keeping

These came up during execution and aren't in the plan. Apply them as you go.

1. **Pytest test isolation needs `sys.modules.pop("engine", None)` AND `sys.modules.pop("database", None)`.** The plan only mentioned popping `engine`. But `database` caches its own reference to `engine.get_engine` at import time, so popping only `engine` leaves the second/third test in any run looking at the previous test's engine pointing at a now-defunct DB. The Task 2 tests in `tests/test_schema.py` do both — copy that pattern for any new tests that interact with the engine module.

2. **`postgres://` short form must be rewritten too**, not just `postgresql://`. Railway templates emit `postgresql://`, but Heroku-lineage providers and some older Railway services emit `postgres://`. SQLAlchemy 2.x rejects the short form outright. `engine.py:_resolve_url()` handles both.

3. **SQLAlchemy 2.x autobegin trap.** A SQLAlchemy 2.x `Connection` returned by `engine.connect()` starts a transaction on the first statement and *silently rolls it back* when the connection closes. Calling `conn.begin()` on an already-begun connection returns a savepoint, NOT the outer transaction. So writes need either `conn.commit()` or `with conn.begin():` as the OUTER context manager. The `connection()` docstring at `database.py:148-156` says this — when porting routes in Tasks 4–9, every write block needs `with conn.begin():` around it. Don't be fooled by examples online that use bare `conn.begin()`.

4. **`metadata.create_all(conn)` accepts a Connection, not just an Engine.** Pass the connection so `create_all` + `_migrate` + seed all run in one transaction — that way a partial failure rolls back cleanly on Postgres.

5. **Expected red-state through Tasks 2–10.** After Task 2, the schema is SQLAlchemy but `app.py`, `sensor_ingest.py`, and `labels.py` still use raw `sqlite3` API. The full `pytest` run is RED until those files are ported. **Don't try to "fix" the red tests as a side effect of any task** — that's scope creep. Each task's verification is scoped to specific test files (the ones the plan lists for that task). Task 11 is when the full suite returns to green.

6. **`conftest.py` is stale** — it still sets `DATABASE_PATH` (old env var the new engine ignores). All `test_schema.py` tests currently get accidental isolation only because they happen to be idempotent, not because the fixture works. Task 3 fixes this. Until Task 3 lands, any new test using `tmp_db_path` needs to set `DATABASE_URL` itself via monkeypatch (as `test_engine.py` does).

7. **The simulator script defaults to the Railway URL.** `App/scripts/simulate_sensor.py` has `--url` defaulting to `https://gm2aquasolutions-production.up.railway.app`. Anyone running it without flags writes to production. If you're testing locally, pass `--url http://localhost:5000`.

---

## Next steps

### Immediate: Task 3 (conftest)

Read the plan's Task 3 in full. The TL;DR:

- Rewrite `App/backend/conftest.py` so `tmp_db_path` sets `DATABASE_URL=sqlite:///<tmpfile>` (not `DATABASE_PATH`).
- Pop the `engine` module from `sys.modules` inside the fixture so the singleton rebuilds against the new URL.
- The `app` fixture's `sys.modules.pop` list grows to include `engine`.
- After Task 3, `test_schema.py` tests pass WITHOUT the `DATABASE_URL=sqlite:///:memory:` prefix workaround.

This is the smallest task in the plan but the rest of the suite depends on it being correct.

### After Task 3: Tasks 4–9 (port application code)

Port each file's queries from raw `sqlite3` to SQLAlchemy `text()` + named params:

- Task 4: `sensor_ingest.py` (1 file, 1 endpoint)
- Task 5: `labels.py` (1 function)
- Tasks 6–9: `app.py` route by route (dashboard, medical routes, SMS, actions+detail)

Each task's test scope is the corresponding `test_<feature>.py` file(s). Don't run the full suite per task — it'll be red.

### Then: Tasks 10–14

- Task 10: Port `test_migrations.py` from `PRAGMA` + `sqlite3.IntegrityError` to `inspect()` + `sqlalchemy.exc.IntegrityError`.
- Task 11: Full suite green-check + clean up any straggler queries.
- Task 12: Add `release: python -c "from database import init_db; init_db()"` to `Procfile` so Railway fails the deploy on schema errors.
- Task 13: **Manual** — Tristan / ao565 in the Railway dashboard. Add Postgres service, wire `DATABASE_URL` env var, watch deploy logs for "schema OK", force a redeploy and verify data persists.
- Task 14: Document in `CLAUDE.md` and close the ephemeral-FS risk in `issues_v3.md`.

---

## Workflow (subagent-driven development)

This branch is being executed using the `superpowers:subagent-driven-development` pattern. The shape:

```
For each task:
  1. Dispatch an implementer subagent with the FULL task text + context
     (don't make the subagent read the plan file).
  2. Implementer writes failing test, makes it pass, commits.
  3. Dispatch a spec compliance reviewer subagent with the task spec
     and the implementer's claimed work. Reviewer verifies independently.
  4. If issues → implementer fixes → re-dispatch reviewer.
  5. Once spec-compliant, dispatch a code quality reviewer.
  6. If issues → implementer fixes → re-dispatch.
  7. Once approved, mark task complete, move to next.
```

Prompt templates live in the superpowers plugin cache, but the simpler thing is to look at the prompts I used in the conversation history — they're verbose-but-bulletproof, and you can adapt them per task. Each implementer prompt for THIS migration should include:

- **Expected red-state warning** (don't try to fix unrelated failing tests)
- **Sub-suite verification scope** (which test files to run, not the whole suite)
- **The `sys.modules.pop` pattern** for any test that touches the engine

### Model selection

- Tasks 1–2 used `sonnet` for both implementer and reviewers — good balance of cost and reliability.
- Tasks 4–9 (porting application files) are mechanical with clear specs — `haiku` is probably enough for the implementer, `sonnet` for the reviewers.
- Tasks 11–12 (full suite + Procfile) are small but integration-sensitive — `sonnet`.

### Note on `SendMessage`

In this environment `SendMessage` (to continue a previous subagent) isn't available. When a reviewer found fixes, I applied them directly in the controller for small scopes (4 lines, 3 fixes) rather than dispatching a fresh "fix" subagent. That's a deviation from the skill's recommendation; if your environment has `SendMessage`, prefer sending the original implementer back so they keep their context.

---

## Environment notes

### Where the work lives

- Repo root: `/Users/tristanmartin/Desktop/GM2/GM2_Aqua_Solutions` (Tristan's machine).
- Worktree on Tristan's machine: `.claude/worktrees/postgres-migration` (auto-created by EnterWorktree; ao565 doesn't need this — just check out `worktree-postgres-migration` directly).
- Branch on `origin`: `worktree-postgres-migration`.

### Python

- Tristan's `.venv/bin/python` is Python 3.13.12 with SQLite 3.53.1 (well above the 3.35+ needed for `RETURNING` and 3.24+ for `ON CONFLICT`).
- The migration adds `SQLAlchemy==2.0.36` and `psycopg[binary]==3.2.3` to `requirements.txt`. Already installed in Tristan's venv via `pip install` during Task 1; on ao565's machine, `pip install -r App/backend/requirements.txt` does it.
- The pre-existing `pandas`/`scikit-learn`/`xgboost` deps are heavy and unrelated to the migration — they're for the offline ML in `App/feature_engineering.py`. Install them if your environment needs them; they aren't required to run the Flask backend or the migration tests.

### Test-running

From `App/backend/`:

```bash
# Schema + engine tests (the migration's green-so-far surface)
DATABASE_URL=sqlite:///:memory: <path-to-venv>/bin/python -m pytest tests/test_schema.py tests/test_engine.py -v

# Full suite (will be RED until Task 11)
<path-to-venv>/bin/python -m pytest -v
```

After Task 3 lands, the `DATABASE_URL=sqlite:///:memory:` prefix becomes unnecessary for the schema tests.

### Railway

- Production URL: `https://gm2aquasolutions-production.up.railway.app`
- Tristan controls the Railway dashboard. Task 13 (provisioning Postgres) is a manual step in that dashboard — not something a subagent can do.
- Twilio webhook should be pointed at Railway's `/sms` endpoint with signature validation ON.
- Existing env vars on Railway: `DEVICE_SECRET`, `MEDICAL_PASSWORD`, `GOV_PASSWORD`, `SECRET_KEY`, plus the Twilio ones. After Task 13, `DATABASE_URL` is added.

### Background context (`CLAUDE.md`)

The repo's `CLAUDE.md` at the root has the project's framing, style guidelines, and non-negotiable rules (e.g., never describe outputs as "cholera detection"). Read it before making style decisions in the migration code. Key style points:

- Default to no comments — only WHY (non-obvious constraint, hidden invariant, workaround).
- No defensive validation for scenarios that can't happen.
- YAGNI — don't design for hypothetical futures.

---

## Open questions / decisions deferred

- **Timestamps stay as ISO text strings, not native `TIMESTAMPTZ`.** Cleaner Postgres-native design would use TIMESTAMPTZ, but `_find_open_conversation` and template slices like `received_at[:19]` rely on string-comparison and string-shape. Out of scope for this migration; flagged in the plan's "Risks worth flagging" section as a future cleanup.
- **`feature_engineering.py` stays on raw `sqlite3`.** It's an offline pipeline that opens its own `sqlite3.connect()`. Not part of the Flask app, not run on Railway. Post-migration, training over Railway data requires dumping Postgres to a local SQLite file first (or porting `feature_engineering.py` in a separate plan).
- **Test suite stays on SQLite locally.** Pytest doesn't run against Postgres in CI. Trade-off: fast tests + no Postgres install requirement, but tests don't catch Postgres-specific issues (CHECK constraint phrasing, timestamp casting, etc.). Task 13's "force a redeploy and verify data persists" is the integration check.

---

## Memory notes (for Claude sessions specifically)

If you're a Claude session picking this up, the user has auto-memory enabled. The relevant memories already saved:

- `project_railway_demo_deployment.md` — Railway deployment posture, simulator default URL caveats
- `project_sqlite_to_postgres_migration.md` — high-level architectural decisions for THIS migration

Update those memories as new findings emerge. Don't duplicate this handoff doc into memory — the doc lives in the repo for everyone, memory is per-Claude-session.
