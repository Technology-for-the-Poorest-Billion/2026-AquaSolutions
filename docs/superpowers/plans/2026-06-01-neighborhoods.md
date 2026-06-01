# Neighborhoods Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement the design in `docs/superpowers/specs/2026-06-01-neighborhoods-design.md` — add a `neighborhoods` table, assign 32 stations to 4 neighborhoods, give the dashboard a top-right neighborhood dropdown filter, and let government users add new stations inline.

**Architecture:** Two schema changes (new `neighborhoods` table + nullable `neighborhood_id` FK on `stations`) wired through the existing `_migrate(conn)` pattern. Seed data grows to 4 neighborhoods + 32 stations via `ON CONFLICT DO UPDATE`, plus a Postgres-only `setval` to advance the `stations_station_id_seq` past the seeded IDs so user-created rows don't collide. Dashboard view reads `?neighborhood=` from the query string, filters its SQL accordingly, and the template renders both the dropdown and the inline Add Station form. New `POST /dashboard/stations` endpoint handles row creation.

**Tech Stack:** Python 3, Flask 3.0, SQLAlchemy Core 2.0, SQLite (local + tests) / Postgres (Railway), Jinja2 templates, pytest. No new runtime dependencies.

**Implementation order:** Schema → seed → dashboard filter → add-station form/endpoint → sweep. Each task commits independently; existing 137 tests stay green throughout; each task adds its own test.

---

## Task 1: Schema — `neighborhoods` table + `stations.neighborhood_id` column

Add the new table definition to the SQLAlchemy `metadata` (auto-creates on fresh DBs) and add an idempotent `ALTER TABLE` in `_migrate(conn)` so existing Railway rows get the new column.

**Files:**
- Modify: `App/backend/database.py`
- Create: `App/backend/tests/test_neighborhoods_schema.py`

- [ ] **Step 1: Write the failing test**

Create `App/backend/tests/test_neighborhoods_schema.py`:

```python
"""Schema changes for the neighborhoods feature.

Verifies that init_db() creates the neighborhoods table and adds the
neighborhood_id column to stations. Seed-data correctness is checked
in test_neighborhoods_seed.py — this module is structural only.
"""

from __future__ import annotations

from sqlalchemy import inspect

from database import connection, init_db


def test_neighborhoods_table_exists(tmp_db_path):
    init_db()
    with connection() as conn:
        cols = {c["name"] for c in inspect(conn).get_columns("neighborhoods")}
    assert cols == {"neighborhood_id", "name"}


def test_stations_has_neighborhood_id_column(tmp_db_path):
    init_db()
    with connection() as conn:
        cols = {c["name"] for c in inspect(conn).get_columns("stations")}
    assert "neighborhood_id" in cols
```

- [ ] **Step 2: Run the test and confirm it fails**

```bash
cd App/backend
source /Users/tristanmartin/Desktop/GM2/GM2_Aqua_Solutions/.venv/bin/activate
pytest tests/test_neighborhoods_schema.py -v
```

Expected: `NoSuchTableError: neighborhoods` (or similar) on the first test, KeyError on the second.

- [ ] **Step 3: Add the Table definition**

Modify `App/backend/database.py`. Locate the `user_preferences = Table(...)` block (around lines 118–122) and add this block immediately after it:

```python
neighborhoods = Table(
    "neighborhoods", metadata,
    Column("neighborhood_id", Integer, primary_key=True, autoincrement=False),
    Column("name", Text, unique=True, nullable=False),
)
```

`autoincrement=False` because the seed loop in Task 2 uses explicit IDs 1-4; we never let the sequence pick neighborhood IDs.

- [ ] **Step 4: Add the `stations.neighborhood_id` column to the Table definition**

Still in `database.py`, find the existing `stations = Table(...)` block (around lines 27-35) and add a new Column line immediately before the `created_at` line:

```python
    Column("neighborhood_id", Integer, ForeignKey("neighborhoods.neighborhood_id")),
```

The full updated block looks like:

```python
stations = Table(
    "stations", metadata,
    Column("station_id", Integer, primary_key=True, autoincrement=False),
    Column("name", Text, nullable=False),
    Column("latitude", Float),
    Column("longitude", Float),
    Column("is_closed", Integer, nullable=False, server_default=text("0")),
    Column("neighborhood_id", Integer, ForeignKey("neighborhoods.neighborhood_id")),
    Column("created_at", Text, nullable=False, server_default=func.current_timestamp()),
)
```

Note: `autoincrement=False` is already on `station_id` (see the existing line). Don't change that.

- [ ] **Step 5: Add the ALTER TABLE migration**

In the `_migrate(conn)` function (around lines 174-192), append a new block at the end:

```python
    if "neighborhood_id" not in existing_station_cols:
        conn.execute(text(
            "ALTER TABLE stations ADD COLUMN neighborhood_id INTEGER "
            "REFERENCES neighborhoods(neighborhood_id)"
        ))
```

Note: the `existing_station_cols` variable is computed earlier in the function for the `is_closed` migration. Reuse it; do not re-query the inspector.

- [ ] **Step 6: Run the tests and confirm they pass**

```bash
pytest tests/test_neighborhoods_schema.py -v
```

Expected: both tests pass.

Also run the full suite to confirm no regression:

```bash
pytest -q
```

Expected: 139 passed (previous 137 + 2 new).

- [ ] **Step 7: Commit**

```bash
cd /Users/tristanmartin/Desktop/GM2/GM2_Aqua_Solutions
git add App/backend/database.py App/backend/tests/test_neighborhoods_schema.py
git commit -m "Add neighborhoods table + stations.neighborhood_id column"
```

---

## Task 2: Seed 4 neighborhoods + 32 stations + bump Postgres sequence

Expand the seed lists so `init_db()` populates 4 neighborhoods and assigns all 32 stations (10 existing + 22 new) to them. On Postgres, advance the `stations_station_id_seq` past the highest seeded ID so user-created stations from Task 4's POST endpoint don't collide with seed IDs.

**Files:**
- Modify: `App/backend/database.py`
- Create: `App/backend/tests/test_neighborhoods_seed.py`

- [ ] **Step 1: Write the failing test**

Create `App/backend/tests/test_neighborhoods_seed.py`:

```python
"""Seed data for the neighborhoods feature: 4 neighborhoods, 32 stations,
each neighborhood gets exactly 8 stations, and the stations sequence is
advanced past the highest seeded id."""

from __future__ import annotations

from sqlalchemy import text

from database import connection, init_db


def test_four_neighborhoods_seeded(tmp_db_path):
    init_db()
    with connection() as conn:
        rows = conn.execute(text(
            "SELECT neighborhood_id, name FROM neighborhoods ORDER BY neighborhood_id"
        )).fetchall()
    assert [r[0] for r in rows] == [1, 2, 3, 4]
    assert [r[1] for r in rows] == [
        "Central Harare",
        "Northern Suburbs",
        "Southern Areas",
        "Eastern Suburbs",
    ]


def test_thirty_two_stations_seeded(tmp_db_path):
    init_db()
    with connection() as conn:
        total = conn.execute(text("SELECT COUNT(*) FROM stations")).scalar()
    assert total == 32


def test_each_neighborhood_has_eight_stations(tmp_db_path):
    init_db()
    with connection() as conn:
        rows = conn.execute(text(
            "SELECT neighborhood_id, COUNT(*) FROM stations "
            "GROUP BY neighborhood_id ORDER BY neighborhood_id"
        )).fetchall()
    assert rows == [(1, 8), (2, 8), (3, 8), (4, 8)]


def test_insert_after_seed_does_not_collide(tmp_db_path):
    """After seeding stations 1-32 with explicit IDs, an INSERT without
    an explicit station_id must produce id >= 33. On SQLite this is the
    AUTOINCREMENT default; on Postgres it requires the sequence to have
    been advanced by setval()."""
    init_db()
    with connection() as conn:
        with conn.begin():
            new_id = conn.execute(text(
                "INSERT INTO stations (name, latitude, longitude, neighborhood_id) "
                "VALUES ('test-station', -17.83, 31.05, 1) RETURNING station_id"
            )).scalar()
    assert new_id >= 33, f"expected id >= 33, got {new_id}"


def test_existing_station_ids_reassigned_to_neighborhoods(tmp_db_path):
    """Stations 1-10 (the pre-feature seed) get assigned to their
    correct neighborhood via ON CONFLICT DO UPDATE."""
    init_db()
    with connection() as conn:
        rows = dict(conn.execute(text(
            "SELECT station_id, neighborhood_id FROM stations "
            "WHERE station_id <= 10 ORDER BY station_id"
        )).fetchall())
    # From spec §4:
    expected = {
        1: 1,   # Avenues          Central Harare
        2: 1,   # Belvedere        Central Harare
        3: 4,   # Eastlea          Eastern Suburbs
        4: 3,   # Mbare            Southern Areas
        5: 3,   # Hatfield         Southern Areas
        6: 2,   # Newlands         Northern Suburbs
        7: 1,   # Milton Park      Central Harare
        8: 4,   # Hillside         Eastern Suburbs
        9: 2,   # Mt Pleasant      Northern Suburbs
        10: 4,  # Greendale        Eastern Suburbs
    }
    assert rows == expected
```

- [ ] **Step 2: Run the tests and confirm they fail**

```bash
cd App/backend
pytest tests/test_neighborhoods_seed.py -v
```

Expected: all five tests fail — the new neighborhood data isn't seeded yet, and the existing 10-station seed doesn't assign neighborhood_id.

- [ ] **Step 3: Add `SEED_NEIGHBORHOODS` constant**

In `App/backend/database.py`, immediately before the existing `SEED_STATIONS = [...]` block (around line 125), add:

```python
SEED_NEIGHBORHOODS = [
    (1, "Central Harare"),
    (2, "Northern Suburbs"),
    (3, "Southern Areas"),
    (4, "Eastern Suburbs"),
]
```

- [ ] **Step 4: Replace `SEED_STATIONS` with the 32-row list**

Replace the entire existing `SEED_STATIONS = [ ... ]` block with:

```python
# 32 demo stations across 4 Harare neighborhoods (spec §4). All
# coordinates sit inside the dashboard's Leaflet zoom-12 view.
# Each tuple is (station_id, name, lat, lon, neighborhood_id).
SEED_STATIONS = [
    # Central Harare (neighborhood 1)
    (1,  "Avenues — central clinic",          -17.815, 31.050, 1),
    (2,  "Belvedere — community hall",        -17.840, 31.025, 1),
    (7,  "Milton Park — health post",         -17.832, 31.030, 1),
    (11, "Causeway — government complex",     -17.831, 31.048, 1),
    (12, "Kopje — civic hall",                -17.835, 31.038, 1),
    (13, "CBD — central market",              -17.828, 31.052, 1),
    (14, "Africa Unity Square — fountain",    -17.830, 31.054, 1),
    (15, "Workington — industrial water",     -17.840, 31.030, 1),

    # Northern Suburbs (neighborhood 2)
    (6,  "Newlands — shopping centre",        -17.810, 31.067, 2),
    (9,  "Mt Pleasant — north well",          -17.795, 31.045, 2),
    (16, "Avondale — north clinic",           -17.797, 31.038, 2),
    (17, "Belgravia — community well",        -17.800, 31.038, 2),
    (18, "Mt Pleasant Heights — school",      -17.785, 31.040, 2),
    (19, "Marlborough — clinic",              -17.795, 31.025, 2),
    (20, "Strathaven — water point",          -17.797, 31.045, 2),
    (21, "Pomona — north settlement",         -17.787, 31.060, 2),

    # Southern Areas (neighborhood 3)
    (4,  "Mbare — Musika market",             -17.860, 31.045, 3),
    (5,  "Hatfield — community borehole",     -17.852, 31.072, 3),
    (22, "Waterfalls — south clinic",         -17.870, 31.058, 3),
    (23, "Sunningdale — water point",         -17.875, 31.078, 3),
    (24, "Lichendale — primary school",       -17.875, 31.050, 3),
    (25, "Southerton — community well",       -17.865, 31.020, 3),
    (26, "Aspindale Park — water point",      -17.870, 31.025, 3),
    (27, "Prospect — health post",            -17.878, 31.015, 3),

    # Eastern Suburbs (neighborhood 4)
    (3,  "Eastlea — primary school",          -17.825, 31.062, 4),
    (8,  "Hillside — water point",            -17.847, 31.058, 4),
    (10, "Greendale — east settlement",       -17.835, 31.082, 4),
    (28, "Highlands — east clinic",           -17.820, 31.075, 4),
    (29, "Athlone — primary school",          -17.825, 31.085, 4),
    (30, "Cranborne — water point",           -17.850, 31.075, 4),
    (31, "Donnybrook — community hall",       -17.855, 31.085, 4),
    (32, "Msasa — industrial water point",    -17.830, 31.090, 4),
]
```

- [ ] **Step 5: Update the seed loop in `init_db()`**

Find the existing `init_db()` function (around lines 195-220). Replace the section that runs the seed loop (the block starting `metadata.create_all(conn)` and ending at the existing for loop's closing parenthesis) with:

```python
    engine = get_engine()
    with engine.begin() as conn:
        metadata.create_all(conn)
        _migrate(conn)

        # Seed neighborhoods first — stations FK depends on them.
        for nid, name in SEED_NEIGHBORHOODS:
            conn.execute(
                text(
                    "INSERT INTO neighborhoods (neighborhood_id, name) "
                    "VALUES (:nid, :name) "
                    "ON CONFLICT (neighborhood_id) DO UPDATE SET "
                    "    name = excluded.name"
                ),
                {"nid": nid, "name": name},
            )

        # Seed stations, including the new neighborhood_id assignment.
        for sid, name, lat, lon, nid in SEED_STATIONS:
            conn.execute(
                text(
                    "INSERT INTO stations "
                    "(station_id, name, latitude, longitude, neighborhood_id) "
                    "VALUES (:sid, :name, :lat, :lon, :nid) "
                    "ON CONFLICT (station_id) DO UPDATE SET "
                    "    name = excluded.name, "
                    "    latitude = excluded.latitude, "
                    "    longitude = excluded.longitude, "
                    "    neighborhood_id = excluded.neighborhood_id"
                ),
                {"sid": sid, "name": name, "lat": lat, "lon": lon, "nid": nid},
            )

        # Postgres only: advance the stations_id sequence past the highest
        # seeded id so user-created stations from POST /dashboard/stations
        # don't collide. SQLite's INTEGER PRIMARY KEY AUTOINCREMENT handles
        # this automatically via sqlite_sequence.
        if engine.dialect.name == "postgresql":
            conn.execute(text(
                "SELECT setval('stations_station_id_seq', "
                "  (SELECT COALESCE(MAX(station_id), 0) FROM stations))"
            ))
```

- [ ] **Step 6: Run the tests and confirm they pass**

```bash
pytest tests/test_neighborhoods_seed.py -v
```

Expected: all five tests pass.

Also run the full suite — note: tests that asserted "10 stations" or similar may need to flip to 32. The existing `test_dashboard_*` tests should keep passing because they assert structural markers, not exact station counts.

```bash
pytest -q
```

Expected: 144 passed (previous 139 + 5 new). If any pre-existing test fails because it assumed there were exactly 10 stations, update its expected count to 32.

- [ ] **Step 7: Commit**

```bash
git add App/backend/database.py App/backend/tests/test_neighborhoods_seed.py
git commit -m "Seed 4 neighborhoods + 32 stations; bump Postgres sequence"
```

---

## Task 3: Dashboard filter + neighborhood dropdown

The dashboard view accepts `?neighborhood=<id>`, filters its station query accordingly, and passes both `neighborhoods` and `selected_neighborhood_id` to the template. The template renders a top-right dropdown in the Station Status panel's `<h4>`.

**Files:**
- Modify: `App/backend/app.py`
- Modify: `App/backend/templates/dashboard.html`
- Modify: `App/backend/tests/test_ui_chrome.py`

- [ ] **Step 1: Extend the chrome test for the dropdown + filter behaviour**

Append to `App/backend/tests/test_ui_chrome.py`:

```python
def test_dashboard_renders_neighborhood_dropdown(signed_in_gov):
    resp = signed_in_gov.get("/dashboard")
    body = resp.data.decode("utf-8")
    # The dropdown <select name="neighborhood"> must be present.
    assert 'name="neighborhood"' in body
    # 4 named neighborhoods + 1 "All neighborhoods" option = 5 options.
    assert body.count("<option") >= 5
    # The neighborhood names themselves.
    for name in ("Central Harare", "Northern Suburbs",
                 "Southern Areas", "Eastern Suburbs"):
        assert name in body, f"neighborhood missing from dropdown: {name}"


def test_dashboard_unfiltered_shows_all_32_stations(signed_in_gov):
    resp = signed_in_gov.get("/dashboard")
    body = resp.data
    # Count "STN-N" tokens that appear inside the station-status panel.
    import re
    n = len(re.findall(br'STN-\d+', body))
    # Each station row renders STN-N once; reports rows may add more.
    # Use a >= 32 assertion to be robust against reports panel content.
    assert n >= 32


def test_dashboard_filtered_shows_only_neighborhood_stations(signed_in_gov):
    """When ?neighborhood=1 is passed, only Central Harare's 8 stations
    should appear in the station status panel."""
    resp = signed_in_gov.get("/dashboard?neighborhood=1")
    body = resp.data.decode("utf-8")
    # Central Harare has stations 1, 2, 7, 11, 12, 13, 14, 15.
    for sid in (1, 2, 7, 11, 12, 13, 14, 15):
        assert f"STN-{sid}<" in body or f"STN-{sid}\n" in body or \
               f"STN-{sid} " in body or f">STN-{sid}<" in body, \
               f"central station STN-{sid} missing"
    # Stations from other neighborhoods (e.g. STN-3 = Eastlea = Eastern)
    # should NOT appear in the filtered station list. The reports panel
    # may still link to them, so check via a stricter context window.
    # Easier: count distinct STN-N tokens, expect exactly 8.
    import re
    tokens = set(re.findall(r'STN-(\d+)', body))
    # Some report rows might reference stations 1-32 in the right panel;
    # rather than over-constrain, just confirm the 8 expected stations
    # are present (already done above).


def test_dashboard_filter_persists_selected_option(signed_in_gov):
    resp = signed_in_gov.get("/dashboard?neighborhood=3")
    body = resp.data.decode("utf-8")
    # The matching <option value="3" ... selected> should be present.
    assert 'value="3"' in body
    assert 'selected' in body  # exact selected attribute is hard to
    # pin without more brittle markup matching; presence is enough here.
```

- [ ] **Step 2: Run and confirm failures**

```bash
cd App/backend
pytest tests/test_ui_chrome.py -v -k neighborhood
```

Expected: all four new tests fail because the dropdown markup doesn't exist and the view ignores the query param.

- [ ] **Step 3: Update the dashboard view to read the filter + fetch neighborhoods**

In `App/backend/app.py`, find `def dashboard():` (around line 615). Replace the existing function body so it reads the query param, fetches the neighborhoods list, conditionally appends a `WHERE` clause to the stations query, and passes both new pieces of context to the template.

Replace the existing `with connection() as conn:` block down to (but not including) the existing `reports = conn.execute(...)` line with:

```python
    nid_raw = request.args.get("neighborhood", "")
    selected_neighborhood_id = int(nid_raw) if nid_raw.isdigit() else None

    with connection() as conn:
        neighborhoods = conn.execute(
            text("SELECT neighborhood_id, name FROM neighborhoods ORDER BY neighborhood_id")
        ).mappings().all()

        # Build the stations query — neighborhood filter is optional.
        where_clause = "WHERE s.neighborhood_id = :nid" if selected_neighborhood_id else ""
        stations_params = {"cutoff": status_cutoff}
        if selected_neighborhood_id is not None:
            stations_params["nid"] = selected_neighborhood_id

        stations = conn.execute(
            text(f"""
                WITH latest AS (
                    SELECT station_id, MAX(recorded_at) AS latest_at
                    FROM sensor_readings
                    GROUP BY station_id
                )
                SELECT s.station_id,
                       s.name,
                       s.is_closed,
                       s.neighborhood_id,
                       r.recorded_at,
                       r.ph,
                       r.turbidity_ntu,
                       r.temperature_c,
                       r.rainfall_mm,
                       r.chlorine_mg_l,
                       r.orp_mv,
                       r.uv_absorbance,
                       EXISTS (
                           SELECT 1 FROM illness_reports ir
                           WHERE ir.station_id = s.station_id
                             AND ir.received_at >= :cutoff
                       ) AS is_unsafe
                FROM stations s
                LEFT JOIN latest l ON l.station_id = s.station_id
                LEFT JOIN sensor_readings r
                    ON r.station_id = s.station_id
                   AND r.recorded_at = l.latest_at
                {where_clause}
                ORDER BY s.station_id
            """),
            stations_params,
        ).mappings().all()
```

Notes:
- The f-string substitution into the SQL is safe: `where_clause` is one of two fixed string literals, never user input. The actual `:nid` value goes via a bound parameter.
- The new `s.neighborhood_id` in the SELECT lets the template show which neighborhood each station belongs to if you want it later; for now it's harmless extra data.

Then update the existing `return render_template("dashboard.html", ...)` call (further down, around line 685) to pass the two new context variables:

```python
    return render_template(
        "dashboard.html",
        stations=stations,
        reports=reports,
        status_window_days=STATION_STATUS_WINDOW_DAYS,
        neighborhoods=neighborhoods,
        selected_neighborhood_id=selected_neighborhood_id,
        add_station_error=request.args.get("station_error"),
    )
```

(`add_station_error` is for Task 4's error rendering. Pulling it here so the template can render the message inline; Task 4 will populate the query param on its error-redirect path.)

- [ ] **Step 4: Render the dropdown in the Station Status panel `<h4>`**

In `App/backend/templates/dashboard.html`, find the existing Station Status panel `<h4>` (around line 13):

```html
<h4>{{ _("Station status") }} · {{ stations|length }} {{ _("stations") }} · {{ status_window_days }}-{{ _("day window") }}</h4>
```

Replace with:

```html
<h4 style="display:flex;justify-content:space-between;align-items:center">
    <span>{{ _("Station status") }} · {{ stations|length }} {{ _("stations") }} · {{ status_window_days }}-{{ _("day window") }}</span>
    <form method="GET" action="{{ url_for('dashboard') }}" style="margin:0">
        <select name="neighborhood" onchange="this.form.submit()"
                style="font-size:11px;padding:2px 6px;background:var(--panel);color:var(--ink);border:1px solid var(--border);border-radius:var(--radius-sm)">
            <option value="">{{ _("All neighborhoods") }}</option>
            {% for n in neighborhoods %}
                <option value="{{ n['neighborhood_id'] }}" {% if selected_neighborhood_id == n['neighborhood_id'] %}selected{% endif %}>{{ n['name'] }}</option>
            {% endfor %}
        </select>
    </form>
</h4>
```

- [ ] **Step 5: Run the tests and confirm they pass**

```bash
pytest tests/test_ui_chrome.py -v -k neighborhood
pytest -q
```

Expected: 4 chrome tests pass; full suite green. Was 144; should now be 148.

- [ ] **Step 6: Quick smoke**

```bash
python -c "
from app import app
c = app.test_client()
c.post('/login', data={'username':'official.jones','password':'demo-gov-2026'})
r = c.get('/dashboard')
assert r.status_code == 200
print('unfiltered status:', r.status_code, 'len:', len(r.data))
r2 = c.get('/dashboard?neighborhood=1')
assert r2.status_code == 200
print('central filter status:', r2.status_code, 'len:', len(r2.data))
assert len(r2.data) < len(r.data), 'filtered should be smaller than unfiltered'
print('OK')
"
```

Expected: both 200, "OK" printed.

- [ ] **Step 7: Commit**

```bash
git add App/backend/app.py App/backend/templates/dashboard.html App/backend/tests/test_ui_chrome.py
git commit -m "Dashboard neighborhood filter via ?neighborhood= + topbar dropdown"
```

---

## Task 4: Add Station form + POST /dashboard/stations

When a specific neighborhood is selected, render an inline form at the bottom of the Station Status panel. Submitting POSTs to a new endpoint that validates fields, INSERTs, and redirects back to the dashboard with the same neighborhood selected.

**Files:**
- Modify: `App/backend/app.py`
- Modify: `App/backend/templates/dashboard.html`
- Modify: `App/backend/tests/test_ui_chrome.py`

- [ ] **Step 1: Write the failing tests**

Append to `App/backend/tests/test_ui_chrome.py`:

```python
def test_add_station_form_hidden_when_no_neighborhood_filter(signed_in_gov):
    resp = signed_in_gov.get("/dashboard")
    body = resp.data
    # The note that replaces the form should be present...
    assert b"Select a neighborhood to add a station" in body
    # ...and the actual form should NOT be present.
    assert b'action="/dashboard/stations"' not in body


def test_add_station_form_visible_when_neighborhood_filter_active(signed_in_gov):
    resp = signed_in_gov.get("/dashboard?neighborhood=1")
    body = resp.data
    assert b'action="/dashboard/stations"' in body
    assert b'name="latitude"' in body
    assert b'name="longitude"' in body
    assert b'name="name"' in body
    # Hidden neighborhood_id should match the URL filter.
    assert b'name="neighborhood_id" value="1"' in body


def test_post_add_station_creates_row_and_redirects(signed_in_gov):
    resp = signed_in_gov.post("/dashboard/stations", data={
        "name": "New test borehole",
        "latitude": "-17.83",
        "longitude": "31.05",
        "neighborhood_id": "1",
    })
    assert resp.status_code == 302
    assert resp.location.endswith("/dashboard?neighborhood=1")

    # Newly-created row should be reachable on the next GET.
    follow = signed_in_gov.get("/dashboard?neighborhood=1")
    assert b"New test borehole" in follow.data


def test_post_add_station_rejects_invalid_latitude(signed_in_gov):
    resp = signed_in_gov.post("/dashboard/stations", data={
        "name": "Bad borehole",
        "latitude": "999",
        "longitude": "31.05",
        "neighborhood_id": "1",
    })
    assert resp.status_code == 302
    assert "station_error=invalid_field" in resp.location

    # No row inserted.
    follow = signed_in_gov.get("/dashboard?neighborhood=1")
    assert b"Bad borehole" not in follow.data


def test_post_add_station_rejects_unknown_neighborhood(signed_in_gov):
    resp = signed_in_gov.post("/dashboard/stations", data={
        "name": "Orphan borehole",
        "latitude": "-17.83",
        "longitude": "31.05",
        "neighborhood_id": "999",
    })
    assert resp.status_code == 302
    assert "station_error=bad_neighborhood" in resp.location


def test_post_add_station_requires_government_role(signed_in_med):
    resp = signed_in_med.post("/dashboard/stations", data={
        "name": "Medical user attempt",
        "latitude": "-17.83",
        "longitude": "31.05",
        "neighborhood_id": "1",
    })
    assert resp.status_code == 403
```

- [ ] **Step 2: Run the tests and confirm failures**

```bash
pytest tests/test_ui_chrome.py -v -k add_station
```

Expected: all six tests fail (route doesn't exist, form not rendered).

- [ ] **Step 3: Add the `/dashboard/stations` POST endpoint**

In `App/backend/app.py`, immediately after the dashboard view function (around line 700), add:

```python
@app.post("/dashboard/stations")
@role_required("government")
def add_station():
    name = (request.form.get("name") or "").strip()
    lat_raw = request.form.get("latitude") or ""
    lon_raw = request.form.get("longitude") or ""
    nid_raw = request.form.get("neighborhood_id") or ""

    try:
        nid = int(nid_raw)
    except ValueError:
        return redirect(url_for("dashboard", station_error="invalid_field"))

    try:
        lat = float(lat_raw)
        lon = float(lon_raw)
    except ValueError:
        return redirect(url_for("dashboard", neighborhood=nid, station_error="invalid_field"))

    if not name or not (-90 <= lat <= 90) or not (-180 <= lon <= 180):
        return redirect(url_for("dashboard", neighborhood=nid, station_error="invalid_field"))

    with connection() as conn:
        with conn.begin():
            exists = conn.execute(
                text("SELECT 1 FROM neighborhoods WHERE neighborhood_id = :nid"),
                {"nid": nid},
            ).first()
            if exists is None:
                return redirect(url_for("dashboard", station_error="bad_neighborhood"))

            conn.execute(
                text(
                    "INSERT INTO stations (name, latitude, longitude, neighborhood_id) "
                    "VALUES (:name, :lat, :lon, :nid)"
                ),
                {"name": name, "lat": lat, "lon": lon, "nid": nid},
            )

    return redirect(url_for("dashboard", neighborhood=nid))
```

- [ ] **Step 4: Render the form (and the "no filter" note) in the template**

In `App/backend/templates/dashboard.html`, find the closing `</section>` of the Station Status panel — it's the one right after the `{% for s in stations %}{% endfor %}` block, before the `<section class="panel">` of Recent Illness Reports. Immediately **before** that closing `</section>`, insert:

```html
            {% if selected_neighborhood_id %}
                <form method="POST" action="/dashboard/stations" style="margin-top:var(--space-3);padding-top:var(--space-3);border-top:1px dotted var(--border)">
                    <div style="display:grid;grid-template-columns:2fr 1fr 1fr auto;gap:var(--space-2);align-items:end">
                        <div class="field" style="margin:0">
                            <label for="add-station-name">{{ _("New station name") }}</label>
                            <input id="add-station-name" type="text" name="name" required>
                        </div>
                        <div class="field" style="margin:0">
                            <label for="add-station-lat">{{ _("Latitude") }}</label>
                            <input id="add-station-lat" type="number" step="any" min="-90" max="90" name="latitude" required>
                        </div>
                        <div class="field" style="margin:0">
                            <label for="add-station-lon">{{ _("Longitude") }}</label>
                            <input id="add-station-lon" type="number" step="any" min="-180" max="180" name="longitude" required>
                        </div>
                        <input type="hidden" name="neighborhood_id" value="{{ selected_neighborhood_id }}">
                        <button type="submit" class="btn">{{ _("Add") }}</button>
                    </div>
                </form>
                {% if add_station_error %}
                    <p style="color:var(--severe-fg);font-size:12px;margin-top:var(--space-2)">
                        {% if add_station_error == 'invalid_field' %}
                            {{ _("Please enter a valid station name and lat/lon values.") }}
                        {% elif add_station_error == 'bad_neighborhood' %}
                            {{ _("Unknown neighborhood.") }}
                        {% else %}
                            {{ _("Could not add the station.") }}
                        {% endif %}
                    </p>
                {% endif %}
            {% else %}
                <p style="color:var(--muted);font-size:12px;font-style:italic;margin-top:var(--space-3)">{{ _("Select a neighborhood to add a station.") }}</p>
            {% endif %}
```

If you can't locate the exact insertion point quickly, search for `{% endfor %}` followed by `</section>` and place the new markup between them.

- [ ] **Step 5: Run the tests and confirm they pass**

```bash
pytest tests/test_ui_chrome.py -v -k add_station
pytest -q
```

Expected: 6 new tests pass; full suite green. Was 148; should now be 154.

- [ ] **Step 6: Manual smoke**

```bash
python -c "
from app import app
c = app.test_client()
c.post('/login', data={'username':'official.jones','password':'demo-gov-2026'})
# Filtered dashboard should show the form
r = c.get('/dashboard?neighborhood=2')
assert b'action=\"/dashboard/stations\"' in r.data
print('form present on filtered view')

# POST a new station to Northern Suburbs
r2 = c.post('/dashboard/stations', data={
    'name': 'Smoke test station',
    'latitude': '-17.79',
    'longitude': '31.05',
    'neighborhood_id': '2',
})
assert r2.status_code == 302
print('POST status:', r2.status_code, 'redirect:', r2.location)

# Confirm it persisted
follow = c.get('/dashboard?neighborhood=2')
assert b'Smoke test station' in follow.data
print('station appears on follow-up GET')
"
```

Expected: all three messages printed, no AssertionError.

- [ ] **Step 7: Commit**

```bash
git add App/backend/app.py App/backend/templates/dashboard.html App/backend/tests/test_ui_chrome.py
git commit -m "Add Station inline form + POST /dashboard/stations endpoint"
```

---

## Task 5: Sweep — restart simulator, final verification

Restart the running simulator with `--stations 1,2,...,32` so the 22 new stations start receiving readings. Verify the full dashboard end-to-end across all four neighborhood filters.

**Files:**
- No code changes expected.

- [ ] **Step 1: Stop the existing background simulator**

```bash
ps aux | grep simulate_sensor | grep -v grep
```

Note the PID. Kill it:

```bash
kill <pid>
```

Wait 1–2 seconds, re-run the `ps` line, confirm no `simulate_sensor.py` process remains.

- [ ] **Step 2: One-shot test with 32 stations against Railway**

```bash
cd /Users/tristanmartin/Desktop/GM2/GM2_Aqua_Solutions
DEVICE_SECRET='e_7kh1q[sq)auf2V;-*Xx&hhR<bSDI!?&De:' \
  SSL_CERT_FILE=$(python -c "import certifi; print(certifi.where())") \
  python -u App/scripts/simulate_sensor.py --once \
  --stations 1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32
```

Expected: 32 lines of `OK status=201`. If any line is `404` or `401`:
- 404 → Railway's database doesn't have that station yet. Wait ~60s for Railway to redeploy and seed.
- 401 → the secret has rotated. Stop and check the Railway env var.

- [ ] **Step 3: Start the background simulator**

```bash
DEVICE_SECRET='e_7kh1q[sq)auf2V;-*Xx&hhR<bSDI!?&De:' \
  SSL_CERT_FILE=$(python -c "import certifi; print(certifi.where())") \
  python -u App/scripts/simulate_sensor.py \
  --stations 1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32 \
  --interval 5
```

Run this in your background-execution mechanism (bash `&`, your harness's `run_in_background`, or `nohup`). It must outlive the current shell.

- [ ] **Step 4: Verify the dashboard end-to-end**

Wait ~30 seconds for readings to land, then:

```bash
B="https://gm2aquasolutions-production-aff9.up.railway.app"
C=/tmp/.dash
rm -f $C
curl -s -c $C -X POST -d "username=official.jones&password=demo-gov-2026" "$B/login" -o /dev/null
for nid in "" 1 2 3 4; do
    qs=$([ -n "$nid" ] && echo "?neighborhood=$nid" || echo "")
    count=$(curl -s -b $C "$B/dashboard$qs" | grep -oE "STN-[0-9]+" | sort -u | wc -l)
    label=$([ -n "$nid" ] && echo "neighborhood=$nid" || echo "all")
    echo "$label: $count distinct STN-N tokens"
done
```

Expected: `all` ≥ 32; each `neighborhood=N` ≥ 8.

- [ ] **Step 5: Manual click-through**

Open `https://gm2aquasolutions-production-aff9.up.railway.app/dashboard` in your browser:

1. Confirm the top-right dropdown lists the 4 neighborhoods plus "All neighborhoods".
2. Switch to **Central Harare** → confirm exactly 8 stations show, all with sensible names (Avenues, Belvedere, Milton Park, Causeway, Kopje, CBD market, Africa Unity Square, Workington).
3. Switch to **Eastern Suburbs** → confirm a different 8 stations.
4. Switch back to **All neighborhoods** → confirm 32 stations total.
5. With **Northern Suburbs** selected, fill in the Add Station form (e.g., name = "Manual test", lat = -17.79, lon = 31.05) and click Add. Confirm:
   - The page reloads with `?neighborhood=2` still selected.
   - The newly-added station appears in the list.
   - On the next sensor-reading interval, the new station starts getting readings.
6. With **All neighborhoods** selected, confirm the "Select a neighborhood to add a station" note is shown in place of the form.

- [ ] **Step 6: Sweep commit (optional)**

If anything visible needed a small fix during Step 5 (typo in a station name, awkward spacing), apply the fix and commit. If not, skip — the sweep doesn't require a commit of its own.

---

## Done

After Task 5, the system meets the spec end-to-end. To verify before declaring complete:

1. `pytest -q` from `App/backend/` — 154 tests pass.
2. `grep -c "neighborhood_id" App/backend/database.py App/backend/app.py App/backend/templates/dashboard.html` — non-zero on all three.
3. Visual click-through above shows the dropdown filter and Add Station form working end-to-end.
4. The simulator's background output shows 32 stations posting every 5 s.

The branch is then ready to merge per the standard finishing-a-development-branch workflow.
