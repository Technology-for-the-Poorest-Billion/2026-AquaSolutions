# Design — Neighborhoods + per-neighborhood station listing

**Date:** 2026-06-01
**Status:** Approved (brainstorming complete; awaiting implementation plan).
**Scope:** Introduce a `neighborhood` grouping for stations. Dashboard's Station Status panel gains a top-right dropdown to filter by neighborhood; an Add Station form sits below the list when a specific neighborhood is selected. Seed data grows from 10 stations to 32 across 4 neighborhoods.

## 1. Context

The Gen-1 portal currently has 10 stations seeded with Harare-suburb names but no structural grouping. As the seeded set grows for the demo, dashboard scrolling will become unwieldy and gov officials will want to scope their attention to a specific area. This design adds a thin neighborhood layer on top of the existing schema with no impact on illness reports, interventions, or sensor readings.

## 2. Key design decisions

| Decision | Choice | Rationale |
|---|---|---|
| Data model | **Separate `neighborhoods` table + nullable FK on `stations`** | Normalised; lets neighborhood metadata grow later (e.g., centroid for map fit-to-bounds). FK is nullable so the migration is safe on existing rows. |
| Neighborhood count | **4 (POC scope)** | The 10 existing stations group naturally into 4 Harare zones; user explicitly capped at 3-5. |
| Stations per neighborhood | **8 (32 total)** | User-chosen target. 32 stations × one reading every 5 s = ~384 readings/min — well within Postgres + Railway envelope. |
| Filter mechanism | **URL query param `?neighborhood=<id>`** | No JS state; shareable links; selected option re-populates from `request.args.get('neighborhood')` on render. |
| Default view | **"All neighborhoods"** | Zero-regression default — matches existing dashboard behavior. |
| Add Station form visibility | **Only when a specific neighborhood is selected** | "All" has no neighborhood context to add to; a small note replaces the form in that mode. |
| Add Station UX | **Inline form at bottom of Station Status panel** | Matches user's explicit request ("at the bottom of the stations list"). No modal; no separate page. |
| Out-of-zoom-12 suburbs | **Replaced with closer-in alternatives** | User explicitly chose option 3 — all 32 stations sit inside the existing Leaflet view at `setView([-17.83, 31.05], 12)`. |

## 3. Schema changes

Idempotent via the existing `_migrate(conn)` pattern.

### New table `neighborhoods`

```python
neighborhoods = Table(
    "neighborhoods", metadata,
    Column("neighborhood_id", Integer, primary_key=True, autoincrement=True),
    Column("name", Text, unique=True, nullable=False),
)
```

Created on fresh DBs by `metadata.create_all(conn)`. No explicit `_migrate` step needed.

### `stations` — add column

```python
Column("neighborhood_id", Integer, ForeignKey("neighborhoods.neighborhood_id"))
```

Nullable so existing rows on Railway stay valid. Migration via `_migrate(conn)`:

```python
existing_station_cols = {c["name"] for c in insp.get_columns("stations")}
if "neighborhood_id" not in existing_station_cols:
    conn.execute(text(
        "ALTER TABLE stations ADD COLUMN neighborhood_id INTEGER "
        "REFERENCES neighborhoods(neighborhood_id)"
    ))
```

Note: SQLite ignores `REFERENCES` constraints in `ALTER TABLE ADD COLUMN` (they are accepted syntactically but not enforced); Postgres enforces. This is fine for the demo — application code enforces non-orphan neighborhood_id at insert time.

## 4. Seed data

Seeded by `init_db()` on every boot via `ON CONFLICT DO UPDATE` (same pattern used for stations).

### Neighborhoods (4)

| neighborhood_id | name |
|---|---|
| 1 | Central Harare |
| 2 | Northern Suburbs |
| 3 | Southern Areas |
| 4 | Eastern Suburbs |

Seed via:

```python
SEED_NEIGHBORHOODS = [
    (1, "Central Harare"),
    (2, "Northern Suburbs"),
    (3, "Southern Areas"),
    (4, "Eastern Suburbs"),
]

for nid, name in SEED_NEIGHBORHOODS:
    conn.execute(text(
        "INSERT INTO neighborhoods (neighborhood_id, name) VALUES (:nid, :name) "
        "ON CONFLICT (neighborhood_id) DO UPDATE SET name = excluded.name"
    ), {"nid": nid, "name": name})
```

### Stations (32 total)

`SEED_STATIONS` extends to 32 entries. Each row becomes `(station_id, name, latitude, longitude, neighborhood_id)`.

**Central Harare** (8 stations, all within ~1 km of CBD):

| id | name | lat | lon |
|---|---|---|---|
| 1 | Avenues — central clinic | -17.815 | 31.050 |
| 2 | Belvedere — community hall | -17.840 | 31.025 |
| 7 | Milton Park — health post | -17.832 | 31.030 |
| 11 | Causeway — government complex | -17.831 | 31.048 |
| 12 | Kopje — civic hall | -17.835 | 31.038 |
| 13 | CBD — central market | -17.828 | 31.052 |
| 14 | Africa Unity Square — fountain | -17.830 | 31.054 |
| 15 | Workington — industrial water point | -17.840 | 31.030 |

**Northern Suburbs** (8 stations, north of CBD within zoom-12):

| id | name | lat | lon |
|---|---|---|---|
| 6 | Newlands — shopping centre | -17.810 | 31.067 |
| 9 | Mt Pleasant — north well | -17.795 | 31.045 |
| 16 | Avondale — north clinic | -17.797 | 31.038 |
| 17 | Belgravia — community well | -17.800 | 31.038 |
| 18 | Mt Pleasant Heights — school | -17.785 | 31.040 |
| 19 | Marlborough — clinic | -17.795 | 31.025 |
| 20 | Strathaven — water point | -17.797 | 31.045 |
| 21 | Pomona — north settlement | -17.787 | 31.060 |

**Southern Areas** (8 stations, south of CBD within zoom-12):

| id | name | lat | lon |
|---|---|---|---|
| 4 | Mbare — Musika market | -17.860 | 31.045 |
| 5 | Hatfield — community borehole | -17.852 | 31.072 |
| 22 | Waterfalls — south clinic | -17.870 | 31.058 |
| 23 | Sunningdale — water point | -17.875 | 31.078 |
| 24 | Lichendale — primary school | -17.875 | 31.050 |
| 25 | Southerton — community well | -17.865 | 31.020 |
| 26 | Aspindale Park — water point | -17.870 | 31.025 |
| 27 | Prospect — health post | -17.878 | 31.015 |

**Eastern Suburbs** (8 stations, east of CBD within zoom-12):

| id | name | lat | lon |
|---|---|---|---|
| 3 | Eastlea — primary school | -17.825 | 31.062 |
| 8 | Hillside — water point | -17.847 | 31.058 |
| 10 | Greendale — east settlement | -17.835 | 31.082 |
| 28 | Highlands — east clinic | -17.820 | 31.075 |
| 29 | Athlone — primary school | -17.825 | 31.085 |
| 30 | Cranborne — water point | -17.850 | 31.075 |
| 31 | Donnybrook — community hall | -17.855 | 31.085 |
| 32 | Msasa — industrial water point | -17.830 | 31.090 |

`SEED_STATIONS` gets an additional `neighborhood_id` column in each tuple, written by the seed loop's `ON CONFLICT DO UPDATE` to assign existing rows (1-10) to their neighborhoods on next boot.

## 5. Endpoint map

### New routes

| Method | Path | Role | Purpose |
|---|---|---|---|
| POST | `/dashboard/stations` | government | Create a new station in the neighborhood specified by `request.form['neighborhood_id']`. Validates lat/lon as float; redirects back to `/dashboard?neighborhood=<id>`. |

### Changed routes

| Method | Path | Change |
|---|---|---|
| GET | `/dashboard` | Reads `request.args.get('neighborhood')` (string-or-None); filters the stations query by `s.neighborhood_id = :nid` when present. Always passes `neighborhoods` (the full list) and `selected_neighborhood_id` to the template. |

### Unchanged

All other routes. The `/medical/*` and `/dashboard/reports/*` paths do not see neighborhoods at all in v1.

## 6. Dashboard UX

### Dropdown (top-right of Station Status panel)

In `dashboard.html`, the `<h4>` of the Station Status panel becomes a flex container with the heading on the left and a small `<form>` on the right whose `<select>` triggers GET navigation on change:

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

The select inherits `.field`-style focus colors via the small inline style block above; consistent enough with the rest of the chrome without introducing a new component.

### Filtered station list

The existing `{% for s in stations %}` loop renders whatever the view passes. The view's SQL gains an optional `WHERE` clause:

```python
nid_raw = request.args.get("neighborhood")
selected_nid = int(nid_raw) if (nid_raw and nid_raw.isdigit()) else None

stations = conn.execute(
    text(f"""
        ... latest CTE ...
        SELECT s.station_id, s.name, s.is_closed, s.neighborhood_id, ...
        FROM stations s
        LEFT JOIN latest l ON ...
        LEFT JOIN sensor_readings r ON ...
        {"WHERE s.neighborhood_id = :nid" if selected_nid else ""}
        ORDER BY s.station_id
    """),
    {"cutoff": status_cutoff, **({"nid": selected_nid} if selected_nid else {})},
).mappings().all()
```

(The string interpolation is safe — `selected_nid` is only used to gate which static WHERE clause is added; the actual value goes via a bound parameter.)

### Add Station form (bottom of panel)

Rendered only when `selected_nid is not None`. When "All" is selected, a slim muted note replaces the form: *"Select a neighborhood to add a station."*

```html
{% if selected_neighborhood_id %}
    <form method="POST" action="{{ url_for('add_station') }}" style="margin-top:var(--space-3);padding-top:var(--space-3);border-top:1px dotted var(--border)">
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
        <p style="color:var(--severe-fg);font-size:12px;margin-top:var(--space-2)">{{ add_station_error }}</p>
    {% endif %}
{% else %}
    <p style="color:var(--muted);font-size:12px;font-style:italic;margin-top:var(--space-3)">{{ _("Select a neighborhood to add a station.") }}</p>
{% endif %}
```

### `POST /dashboard/stations` handler

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
        lat = float(lat_raw)
        lon = float(lon_raw)
    except ValueError:
        return redirect(url_for("dashboard", neighborhood=nid_raw, station_error="invalid_field"))

    if not name or not (-90 <= lat <= 90) or not (-180 <= lon <= 180):
        return redirect(url_for("dashboard", neighborhood=nid, station_error="invalid_field"))

    with connection() as conn:
        with conn.begin():
            # Confirm neighborhood exists.
            row = conn.execute(
                text("SELECT 1 FROM neighborhoods WHERE neighborhood_id = :nid"),
                {"nid": nid},
            ).first()
            if row is None:
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

The new station gets an auto-assigned `station_id` (the schema's `autoincrement=True` is intentional; the seeded 1-32 use explicit IDs, but new application-created stations let the DB pick the next id). Note: this changes one assumption in `database.py` — the seeded SEED_STATIONS were always inserted with `autoincrement=False` style explicit IDs. Both paths can coexist; the autoincrement counter advances past 32 after the seed.

Errors surfaced via `station_error` query param on the redirect; the dashboard view maps it to the inline `add_station_error` template variable (no flash messages, no session state).

## 7. Out of scope (intentional)

- Editing or deleting stations (read + create only — matches the demo's append-only ethos).
- Editing or deleting neighborhoods (the 4 are hard-seeded; admin UI is post-demo).
- Neighborhood field on illness reports / interventions.
- Map clustering by neighborhood (Phase 2). The map continues to render all visible stations.
- Per-neighborhood map view (auto-zooming the Leaflet map when a neighborhood is selected). Phase 2.
- Translating neighborhood names (proper nouns; stay in English).
- Granular permissions (a gov user can add a station to any neighborhood; no per-neighborhood ACLs).
- Simulator updates beyond passing `--stations 1..32` at restart time. The simulator itself stays unchanged.

## 8. Testing

- **Existing 137 tests stay green**. The new column on `stations` is nullable; existing queries that don't `SELECT neighborhood_id` are unaffected.
- **New tests** in `tests/test_neighborhoods.py`:
  1. `test_neighborhoods_table_seeded` — after `init_db()`, the `neighborhoods` table has exactly 4 rows with the expected names.
  2. `test_stations_assigned_to_neighborhoods` — after `init_db()`, each of stations 1-32 has a non-null `neighborhood_id`, distribution is 8-8-8-8.
  3. `test_dashboard_unfiltered_shows_all_stations` — GET `/dashboard` (no `?neighborhood=`) renders all 32 stations.
  4. `test_dashboard_filtered_shows_only_neighborhood_stations` — GET `/dashboard?neighborhood=1` renders exactly 8 station rows; STN-1 (Avenues) present; STN-22 (Waterfalls, Southern) absent.
  5. `test_dashboard_dropdown_renders_with_4_options_plus_all` — the topnav dropdown has 5 `<option>` tags (4 neighborhoods + "All").
  6. `test_dashboard_add_station_form_visible_when_filter_active` — when `?neighborhood=1`, the `form[action=/dashboard/stations]` is in the body; when no filter, it's absent.
  7. `test_post_add_station_inserts_row_and_redirects` — POST `/dashboard/stations` with valid fields creates a station_id > 32, redirects to `/dashboard?neighborhood=1`, and the new station appears in a follow-up GET.
  8. `test_post_add_station_rejects_bad_lat_lon` — POST with `latitude=999` 302s with `station_error=invalid_field`; no row inserted.
  9. `test_post_add_station_requires_gov_role` — medical user POST → 403.

- **Manual sweep**: load `/dashboard`, click through all 4 neighborhoods + "All", add a test station to Central Harare, confirm it appears in the filtered view and persists across reloads.

## 9. Risks

- **Auto-increment collision with seed IDs.** Seeded stations use explicit IDs 1-32; `autoincrement` may set its starting cursor to 1 on a fresh table and collide on the first `INSERT` from the new endpoint. *Mitigation:* after the seed loop, bump the sequence: `SELECT setval('stations_station_id_seq', (SELECT MAX(station_id) FROM stations))` on Postgres; on SQLite the `INTEGER PRIMARY KEY AUTOINCREMENT` rowid pattern picks `MAX(station_id) + 1` automatically. Test #7 catches a collision early.
- **The simulator continues posting to stations 1-10 only.** Until the operator restarts with `--stations 1,2,...,32`, stations 11-32 show "no readings yet" — visible but uninformative. *Mitigation:* documented in spec §2; restart is part of the rollout, not a code change.
- **Station name uniqueness not enforced.** Two different gov users could add "CBD — water point" in different neighborhoods. Acceptable for v1 — neighborhood column disambiguates.
- **Inline form scrolls the panel on narrow viewports.** The `grid-template-columns:2fr 1fr 1fr auto` may overflow at < 700 px. *Mitigation:* desktop-first is locked per UI spec §2; revisit when mobile work begins.
- **No CSRF token on the add-station POST.** Consistent with the rest of the app's forms; not a regression. CSRF protection is post-demo work.
