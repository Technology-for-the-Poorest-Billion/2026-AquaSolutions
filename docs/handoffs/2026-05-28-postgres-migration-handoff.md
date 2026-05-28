# Postgres migration record — 2026-05-28

> **Status:** Migration is **code-complete**. Tasks 1–12 and 14 from the plan are on `main`. Only **Task 13** (manual Railway Postgres provisioning, done from the Railway dashboard) is left. Until Task 13 is done, the deployed Flask app falls back to the ephemeral-filesystem SQLite — data still gets wiped on redeploy.

This file started life as a handoff between Tristan (Claude session 1, Tasks 1–2) and ao565. While that handoff was being written, Aidan picked up the branch and finished Tasks 3–12 + 14 himself. It is now a *record* of the migration plus the standing reminder of what's left.

- **Plan:** `docs/superpowers/plans/2026-05-28-sqlite-to-postgres-migration.md`
- **All code is on `main`** (`origin/main` at or beyond `615c29e`)
- **Feature branch deleted** (`worktree-postgres-migration` was merged into main and cleaned up — its commits live in the merge)

---

## What got done

### Pre-migration housekeeping (`main`)

| What | Who |
| --- | --- |
| Untracked `App/backend/flask_server.log` and gitignored `*.log` (it was leaking `DEVICE_SECRET` and Twilio `From` numbers via gunicorn logs) | Tristan / Claude |
| Added the implementation plan at `docs/superpowers/plans/2026-05-28-sqlite-to-postgres-migration.md` | Tristan / Claude |
| Documented the live Railway ingest target for the sensor simulator (`App/DEMO.md`) | Aidan |

### Migration work (originally on `worktree-postgres-migration`, merged into `main`)

| Task | Who | What |
| --- | --- | --- |
| 1 | Tristan / Claude | New `App/backend/engine.py` — SQLAlchemy `Engine` factory keyed off `DATABASE_URL`, rewrites `postgresql://` and `postgres://` to `postgresql+psycopg://`. Two smoke + two regression tests. `requirements.txt` adds SQLAlchemy 2.0.36 + psycopg[binary] 3.2.3. |
| 2 | Tristan / Claude | Full rewrite of `App/backend/database.py` to SQLAlchemy `MetaData` + `Table` declarations. CHECK constraints, indexes, FKs, idempotent `init_db()` running inside one `engine.begin()` transaction. Three schema tests. |
| 3 | Aidan | `conftest.py` switched from `DATABASE_PATH` to `DATABASE_URL`. |
| 4 | Aidan | `/ingest` ported to SQLAlchemy `text()` with `RETURNING`. |
| 5 | Aidan | `label_readings_for_report` ported to SQLAlchemy `text()`. |
| 6 | Aidan | `/dashboard` view ported. |
| 7 | Aidan | `/medical` routes ported. |
| 8 | Aidan | `/sms` webhook + helpers ported. |
| 9 | Aidan | `/actions` + `/dashboard/reports/<id>` ported. |
| 10 | Aidan | `tests/test_migrations.py` rewritten with `inspect()` + `sqlalchemy.exc.IntegrityError`. |
| 11 | Aidan | Test-helper SQL ported — full suite green at 99/99. |
| 12 | Aidan | Procfile gets `release: python -c "from database import init_db; init_db(); print('schema OK')"` so a broken schema fails the Railway deploy loudly. |
| 14 | Aidan | `CLAUDE.md` updated with a Postgres bullet under "Application-layer guardrails"; the ephemeral-FS risk closed in `issues_v3.md`. |
| 13 | **Pending — manual** | See "What's left" below. |

---

## What's left — Task 13 (manual, Railway dashboard)

Do this in the Railway dashboard for the existing `GM2_Aqua_Solutions` project. It is the load-bearing remaining step — until it's done, the production demo still loses data on every redeploy.

1. **Add Postgres.** In the project view, click `+ New` → `Database` → `PostgreSQL`. Wait ~30 seconds for it to provision.
2. **Wire `DATABASE_URL` on the web service.** Open the web (Flask) service → `Variables` tab → add `DATABASE_URL` with value `${{ Postgres.DATABASE_URL }}` (Railway templating). Save. Railway will redeploy automatically.
3. **Watch the deploy logs for the release phase.** Look for:
   - `Running release phase`
   - `schema OK` (from the Procfile's release command)
   - `Listening at: http://0.0.0.0:$PORT`

   If `schema OK` does not appear, the deploy is broken. Read the error, fix locally, push again — do not skip this check.
4. **Smoke-test the live URL.** `curl -s https://gm2aquasolutions-production-aff9.up.railway.app/health` should return `{"status": "ok", ...}`. Sign in as the government user; the dashboard should show 10 stations with "no readings yet" and "no illness reports yet" — that's correct, Postgres is empty.
5. **Push a few readings and send a test SMS.**

   ```bash
   python App/scripts/simulate_sensor.py --secret <DEVICE_SECRET> --interval 5 --stations 1,2,3
   ```

   Let it run ~30 seconds, ctrl-C. Send one SMS to the Twilio number (e.g. `4`). Refresh the dashboard — both should now show data.
6. **Force a redeploy and confirm data persists.** In Railway, manually trigger a redeploy of the web service. After it comes back up, refresh the dashboard. Readings and the SMS report should **still be there**. That's the durability invariant we're paying Postgres for. If they're gone, `DATABASE_URL` is not being read or the volume isn't mounted — stop and debug before declaring this done.

---

## Findings worth keeping

These came out of execution and aren't in the plan. If anyone re-touches the migration code, apply them.

1. **Pytest test isolation needs both `sys.modules.pop("engine", None)` AND `sys.modules.pop("database", None)`.** The plan only mentioned `engine`. Without popping `database` too, the cached `database` module retains its reference to the engine singleton from the prior test's `:memory:` DB, causing `NoSuchTableError` on later tests in the same run.

2. **`postgres://` short form must be rewritten too**, not just `postgresql://`. Railway templates emit `postgresql://`, but Heroku-lineage providers and some older Railway services emit `postgres://`. SQLAlchemy 2.x rejects the short form outright. `engine.py:_resolve_url()` handles both.

3. **SQLAlchemy 2.x autobegin trap.** A `Connection` returned by `engine.connect()` starts a transaction on the first statement and *silently rolls it back* when the connection closes. Calling `conn.begin()` on an already-begun connection returns a **savepoint**, NOT the outer transaction. Writes need either `conn.commit()` or `with conn.begin():` as the OUTER context manager. The `connection()` docstring at `database.py` says this — every write block uses `with conn.begin():` around it.

4. **`metadata.create_all(conn)` accepts a Connection, not just an Engine.** `init_db()` passes the open connection so `create_all` + `_migrate` + seed all run in one transaction; a Postgres failure mid-init rolls back cleanly.

5. **The simulator script defaults to the Railway URL.** `App/scripts/simulate_sensor.py` has `--url` defaulting to `https://gm2aquasolutions-production-aff9.up.railway.app`. Anyone running it unflagged writes to production. Local testing needs `--url http://localhost:5000`.

---

## Open questions / decisions deferred

- **Timestamps stay as ISO text strings, not native `TIMESTAMPTZ`.** A cleaner Postgres-native design would use TIMESTAMPTZ, but `_find_open_conversation` and template slices like `received_at[:19]` rely on string-comparison and string-shape. Out of scope for this migration; future cleanup.
- **`feature_engineering.py` stays on raw `sqlite3`.** It's an offline pipeline that opens its own connection, not part of the Flask request path. Post-migration, training over Railway data requires dumping Postgres to a local SQLite snapshot first (or porting that module in a separate plan).
- **Test suite stays on SQLite locally.** Pytest doesn't run against Postgres in CI. Trade-off: fast tests + no Postgres install requirement, but the suite won't catch Postgres-specific issues (CHECK phrasing, timestamp casting). Task 13's "force a redeploy and verify data persists" is the integration check.

---

## Environment notes

- **Python:** `/Users/tristanmartin/Desktop/GM2/GM2_Aqua_Solutions/.venv/bin/python` is Python 3.13.12 with SQLite 3.53.1 (well above the 3.35+ needed for `RETURNING` and 3.24+ for `ON CONFLICT`).
- **Backend deps:** Flask 3.0.3, twilio 9.3.7, gunicorn 23.0.0, python-dotenv 1.0.1, SQLAlchemy 2.0.36, psycopg[binary] 3.2.3, pytest 8.3.3. All in `App/backend/requirements.txt`.
- **Running tests:** From `App/backend/`, `../../.venv/bin/python -m pytest -v` → 99 passed (or use the absolute path to the venv's pytest).
- **Railway production URL:** `https://gm2aquasolutions-production-aff9.up.railway.app`. Tristan controls the Railway dashboard; Aidan/ao565 only need GitHub push access to trigger deploys (Railway watches the repo, not who pushes). For Railway dashboard access — required to do Task 13 — they need an invite from the Railway project's Members tab.
- **Background context:** the repo's `CLAUDE.md` has the project's framing, style guidelines (minimal comments, no defensive validation for impossible scenarios, YAGNI), and the non-negotiable "this is not a cholera detector" rule.
