# UI upgrade Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Re-skin the Gen-1 web portal per `docs/superpowers/specs/2026-05-31-ui-upgrade-design.md` — light theme, brand-aligned, "operational console" direction with a dark navy header, monospace data, panel cards. No information-architecture changes.

**Architecture:** Introduce a shared `static/app.css` carrying design tokens (CSS custom properties) and component primitives (`.topbar`, `.panel`, `.btn`, `.pill`, `.chip`, `.segmented`, `.field`, `.kv`, `.reading-table`, `.row`). `_base.html` loses its inline `<style>` block and gains the link to the stylesheet plus a `{% block disclaimer %}` slot mirroring the existing `{% block unverified_banner %}` pattern. Each of the six existing templates converts to use the primitives in turn. The trimmed brand mark is a cropped PNG droplet (`aqua_solutions_drop.png`, transparent bg, produced offline by `scripts/crop_logo.py` via Pillow) plus a CSS wordmark whose colour inverts by context (white "AQUA" on the dark topbar; navy "AQUA" on light cards).

**Tech Stack:** Flask 3.0 + Jinja2 templates, plain CSS (no preprocessor), Pillow for the one-shot logo crop, pytest. No new runtime dependencies.

**Implementation order:** Spec §8 — crop → CSS → chrome refactor → login → dashboard → medical report → remaining details → sweep. Each task commits independently; existing 128 tests stay green throughout; one new structural-markers test gets seeded in Task 3 and extends as templates convert.

---

## Task 1: Crop the logo

Write a one-shot Pillow script that crops `aqua_solutions_logo.png` down to the droplet only, with the white background made transparent. Commit both the script and the resulting PNG. The original logo stays in place for archival; nothing references the new asset yet.

**Files:**
- Modify: `App/backend/requirements-dev.txt`
- Create: `scripts/crop_logo.py`
- Create: `App/backend/static/aqua_solutions_drop.png`

- [ ] **Step 1: Add Pillow to requirements-dev**

Append to `App/backend/requirements-dev.txt`:

```
Pillow>=10.0,<12.0
```

Then install:

```bash
cd App/backend
source /Users/tristanmartin/Desktop/GM2/GM2_Aqua_Solutions/.venv/bin/activate
pip install -r requirements-dev.txt
```

Expected: `Successfully installed pillow-...`. Verify:

```bash
python -c "from PIL import Image; print(Image.__version__)"
```

Should print a version >= 10.0.

- [ ] **Step 2: Write the crop script**

Create `scripts/crop_logo.py`:

```python
"""Crop App/backend/static/aqua_solutions_logo.png to droplet-only with
transparent background.

Usage: python scripts/crop_logo.py

Reads the original logo (3414 x 1584) and writes
App/backend/static/aqua_solutions_drop.png. The crop bounding box was
chosen by visual inspection — the droplet sits in the upper-left
~12% of the source image. Near-white pixels (R, G, B all >= 240)
become transparent so the result can sit on any background.

If the crop is off (droplet clipped or wordmark leaking in), adjust
the percentage constants in crop_drop() and re-run; the script is
idempotent — it always reads the original and overwrites the cropped
output.
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image

REPO_ROOT = Path(__file__).resolve().parent.parent
SRC = REPO_ROOT / "App/backend/static/aqua_solutions_logo.png"
DST = REPO_ROOT / "App/backend/static/aqua_solutions_drop.png"
WHITE_THRESHOLD = 240


def crop_drop(img: Image.Image) -> Image.Image:
    """Return the droplet sub-image. Bounding box as fractions of source size."""
    w, h = img.size
    left = int(w * 0.04)
    upper = int(h * 0.02)
    right = int(w * 0.16)
    lower = int(h * 0.92)
    return img.crop((left, upper, right, lower))


def make_transparent(img: Image.Image, threshold: int = WHITE_THRESHOLD) -> Image.Image:
    """Convert near-white pixels to transparent."""
    rgba = img.convert("RGBA")
    pixels = list(rgba.getdata())
    new_pixels = [
        (r, g, b, 0) if (r >= threshold and g >= threshold and b >= threshold) else (r, g, b, a)
        for r, g, b, a in pixels
    ]
    rgba.putdata(new_pixels)
    return rgba


def main() -> None:
    src = Image.open(SRC)
    cropped = crop_drop(src)
    transparent = make_transparent(cropped)
    transparent.save(DST, "PNG")
    print(f"Wrote {DST.relative_to(REPO_ROOT)} ({transparent.size[0]}x{transparent.size[1]})")


if __name__ == "__main__":
    main()
```

- [ ] **Step 3: Run the script and visually verify**

```bash
cd /Users/tristanmartin/Desktop/GM2/GM2_Aqua_Solutions
python scripts/crop_logo.py
```

Expected: `Wrote App/backend/static/aqua_solutions_drop.png (NNN x NNN)`.

Visually verify the crop:

```bash
python -c "from PIL import Image; Image.open('App/backend/static/aqua_solutions_drop.png').show()"
```

Confirm:
- The whole droplet shape is captured (no top or bottom clipping).
- No wordmark text leaks into the right edge.
- The background appears fully transparent (the image viewer should show the checkerboard transparency pattern around the droplet, not a white halo).

If any of these fail, adjust the four percentage constants in `crop_drop()` (`0.04 / 0.02 / 0.16 / 0.92`) and re-run. Re-run is safe — the script always reads the original and rewrites the output.

- [ ] **Step 4: Confirm tests still pass**

```bash
cd App/backend
pytest -q
```

Expected: 128 passed (unchanged — no code path uses the new PNG yet).

- [ ] **Step 5: Commit**

```bash
cd /Users/tristanmartin/Desktop/GM2/GM2_Aqua_Solutions
git add App/backend/requirements-dev.txt scripts/crop_logo.py App/backend/static/aqua_solutions_drop.png
git commit -m "Crop Aqua Solutions logo to droplet-only PNG with transparency"
```

---

## Task 2: Add static/app.css with tokens and primitives

Introduce the new stylesheet carrying all design tokens and the component primitives that compose them. Wire it into `_base.html` via a `<link>` tag. The existing inline `<style>` block stays for now — both stylesheets are loaded; the inline rules still drive the visible UI in this task. Visual smoke at the end should show **no visible change**.

**Files:**
- Create: `App/backend/static/app.css`
- Modify: `App/backend/templates/_base.html`
- Test: render `/static/app.css` via the test client and assert tokens are present.

- [ ] **Step 1: Write the failing token-presence test**

Append to `App/backend/tests/test_i18n.py` (the closest existing UI-touching test module — a dedicated `test_ui_chrome.py` arrives in Task 3 once chrome markers exist):

```python
def test_app_css_is_served_with_design_tokens(client):
    """The new shared stylesheet must be reachable and must carry the
    full token set the rest of the redesign depends on."""
    resp = client.get("/static/app.css")
    assert resp.status_code == 200, "app.css must be served by Flask's static handler"
    body = resp.data.decode("utf-8")
    for token in (
        "--ink", "--accent", "--teal", "--blue",
        "--bg", "--panel", "--border", "--muted",
        "--clear-bg", "--clear-fg",
        "--medium-bg", "--medium-fg",
        "--high-bg", "--high-fg",
        "--severe-bg", "--severe-fg",
        "--font-sans", "--font-mono",
        "--space-1", "--space-2", "--space-3", "--space-4", "--space-6",
        "--radius-sm", "--radius-md", "--radius-lg",
    ):
        assert token in body, f"missing token: {token}"
```

- [ ] **Step 2: Confirm it fails**

```bash
cd App/backend
pytest tests/test_i18n.py::test_app_css_is_served_with_design_tokens -v
```

Expected: 404 — `/static/app.css` doesn't exist yet.

- [ ] **Step 3: Create the stylesheet**

Create `App/backend/static/app.css`:

```css
/* Design tokens + component primitives — see
   docs/superpowers/specs/2026-05-31-ui-upgrade-design.md §§3-4 */

:root {
  /* Brand */
  --ink: #1a2b47;
  --accent: #3eb1e8;
  --teal: #5fb5a8;
  --blue: #3b8fd1;

  /* Surfaces */
  --bg: #f1f3f5;
  --panel: #ffffff;
  --border: #d6dce3;
  --muted: #6b7280;

  /* Status pills */
  --clear-bg: #d6efe2;   --clear-fg: #0f5b3a;
  --medium-bg: #fff1cc;  --medium-fg: #8a5b00;
  --high-bg: #ffd7b3;    --high-fg: #8a3a00;
  --severe-bg: #fad9d9;  --severe-fg: #7a1c1c;

  /* Typography */
  --font-sans: -apple-system, BlinkMacSystemFont, "Segoe UI", "Helvetica Neue", sans-serif;
  --font-mono: ui-monospace, "SF Mono", Menlo, Consolas, monospace;

  /* Scale */
  --space-1: 4px;
  --space-2: 8px;
  --space-3: 12px;
  --space-4: 16px;
  --space-6: 24px;
  --radius-sm: 3px;
  --radius-md: 6px;
  --radius-lg: 8px;
}

/* Reset + base */
*, *::before, *::after { box-sizing: border-box; }
body.app {
  margin: 0;
  font-family: var(--font-sans);
  background: var(--bg);
  color: var(--ink);
  min-height: 100vh;
}

/* ----- Topbar + brand mark ----- */
.topbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--space-2) var(--space-4);
  background: var(--ink);
  color: #fff;
  font-size: 12px;
}
.topbar .right {
  display: flex;
  gap: var(--space-3);
  align-items: center;
  color: rgba(255,255,255,0.75);
}
.topbar .right select {
  background: #142035;
  color: #fff;
  border: 1px solid rgba(255,255,255,0.1);
  border-radius: var(--radius-sm);
  padding: 3px 6px;
  font-size: 11px;
}
.topbar .user-meta {
  font-family: var(--font-mono);
  font-size: 11px;
}
.topbar a { color: rgba(255,255,255,0.85); text-decoration: none; }
.topbar a:hover { color: #fff; text-decoration: underline; }

.brand-mark {
  display: inline-flex;
  align-items: center;
  gap: var(--space-2);
  line-height: 1;
}
.brand-mark img.drop { display: block; height: 28px; width: auto; }
.brand-mark .wordmark {
  font-weight: 800;
  font-size: 16px;
  letter-spacing: 0.01em;
}
.brand-mark .wordmark .aqua { color: var(--ink); }
.brand-mark .wordmark .solutions { color: var(--accent); }
.topbar .brand-mark .wordmark .aqua { color: #ffffff; }

/* ----- Disclaimer strip ----- */
.disclaim {
  background: var(--severe-bg);
  color: var(--severe-fg);
  padding: 6px var(--space-4);
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  border-bottom: 1px solid #f3d9d9;
}

/* ----- Layout containers ----- */
main.app-main { padding: var(--space-4); }
.crumb {
  font-size: 11px;
  color: var(--muted);
  margin-bottom: var(--space-3);
}
.crumb a { color: var(--accent); text-decoration: none; }
.crumb .mono { font-family: var(--font-mono); }

/* ----- Panel card ----- */
.panel {
  background: var(--panel);
  border: 1px solid var(--border);
  padding: var(--space-3) var(--space-4);
}
.panel + .panel { margin-top: var(--space-3); }
.panel h4 {
  margin: 0 0 var(--space-2);
  font-size: 11px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  border-bottom: 2px solid var(--accent);
  padding-bottom: 4px;
}

/* Two-column page grid (dashboard, detail pages) */
.grid-2 { display: grid; grid-template-columns: 1fr 1fr; gap: var(--space-3); }
.grid-2-asym { display: grid; grid-template-columns: 2fr 1fr; gap: var(--space-3); }

/* ----- Row patterns ----- */
.row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 5px 0;
  border-bottom: 1px dotted var(--border);
  font-size: 12px;
}
.row:last-child { border-bottom: none; }
.row:hover { background: var(--bg); }

/* ----- Pills ----- */
.pill {
  display: inline-block;
  font-family: var(--font-mono);
  font-size: 10px;
  font-weight: 700;
  padding: 1px 6px;
  border-radius: 0;
  text-transform: uppercase;
  letter-spacing: 0.03em;
}
.pill-clear  { background: var(--clear-bg);  color: var(--clear-fg);  }
.pill-medium { background: var(--medium-bg); color: var(--medium-fg); }
.pill-high   { background: var(--high-bg);   color: var(--high-fg);   }
.pill-severe { background: var(--severe-bg); color: var(--severe-fg); }

/* ----- Buttons ----- */
.btn {
  font-family: var(--font-sans);
  font-size: 12px;
  font-weight: 600;
  padding: 6px var(--space-3);
  border: 1px solid var(--ink);
  background: var(--ink);
  color: #fff;
  border-radius: var(--radius-sm);
  cursor: pointer;
}
.btn:hover { filter: brightness(1.05); }
.btn-light { background: var(--panel); color: var(--ink); }
.btn-danger { background: var(--severe-fg); border-color: var(--severe-fg); }
.btn-row { display: flex; gap: var(--space-2); }

/* ----- Form fields ----- */
.field { margin-bottom: var(--space-3); }
.field label {
  display: block;
  font-size: 10px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: var(--ink);
  margin-bottom: 4px;
}
.field input,
.field select,
.field textarea {
  width: 100%;
  font-family: var(--font-sans);
  font-size: 12px;
  padding: 6px var(--space-2);
  border: 1px solid #c1c8d0;
  border-radius: var(--radius-sm);
  background: var(--panel);
  color: var(--ink);
}
.field input:focus,
.field select:focus,
.field textarea:focus {
  outline: none;
  border-color: var(--accent);
  box-shadow: 0 0 0 2px rgba(62,177,232,0.18);
}

/* ----- Chip toggles (multi-select) ----- */
.chip {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 4px var(--space-3);
  border: 1px solid #c1c8d0;
  background: var(--panel);
  font-size: 12px;
  cursor: pointer;
  user-select: none;
  border-radius: var(--radius-sm);
  color: var(--ink);
}
.chip.on { background: var(--ink); color: #fff; border-color: var(--ink); }
.chip .check { font-size: 10px; opacity: 0.7; }

/* ----- Segmented control (single-pick) ----- */
.segmented {
  display: inline-flex;
  border: 1px solid #c1c8d0;
  border-radius: var(--radius-sm);
  overflow: hidden;
}
.segmented .seg {
  padding: 5px var(--space-3);
  font-size: 11px;
  font-weight: 600;
  background: var(--panel);
  color: var(--ink);
  border-right: 1px solid #c1c8d0;
  cursor: pointer;
}
.segmented .seg:last-child { border-right: none; }
.segmented .seg.on { background: var(--ink); color: #fff; }
.segmented .seg.on.tier-low    { background: var(--clear-fg);  }
.segmented .seg.on.tier-medium { background: var(--medium-fg); }
.segmented .seg.on.tier-high   { background: var(--high-fg);   }
.segmented .seg.on.tier-severe { background: var(--severe-fg); }

/* ----- Key-value list ----- */
.kv {
  display: grid;
  grid-template-columns: 130px 1fr;
  gap: 6px var(--space-3);
  font-size: 12px;
  margin: 0;
}
.kv dt {
  font-size: 10px;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  color: var(--muted);
  font-weight: 700;
  padding-top: 1px;
}
.kv dd { margin: 0; font-family: var(--font-mono); }

/* ----- Reading table ----- */
.reading-table {
  width: 100%;
  font-size: 11px;
  border-collapse: collapse;
}
.reading-table th {
  text-align: left;
  padding: 5px 6px;
  background: var(--bg);
  font-size: 10px;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  font-weight: 700;
  border-bottom: 1px solid var(--border);
}
.reading-table td {
  padding: 4px 6px;
  font-family: var(--font-mono);
  border-bottom: 1px dotted var(--border);
}

/* ----- Inline form layout helpers ----- */
.form-grid-3 {
  display: grid;
  grid-template-columns: 2fr 1fr 1fr;
  gap: var(--space-3);
}
.field-row {
  display: grid;
  grid-template-columns: 90px 1fr;
  gap: var(--space-2);
  align-items: center;
  margin-bottom: var(--space-3);
}
.field-row label {
  font-size: 10px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: var(--ink);
}
.inline-row { display: flex; gap: 6px; flex-wrap: wrap; }
.meta-row {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  margin-top: var(--space-3);
}

/* ----- Login card centring (one truly page-specific layout that lives here
        because it's brand-mark-shaped, not page-shaped) ----- */
body.app.app-login {
  display: flex;
  flex-direction: column;
}
.login-body {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: var(--space-6);
}
.login-card {
  width: 320px;
  background: var(--panel);
  border: 1px solid var(--border);
  padding: var(--space-6);
}
.login-card .brand-mark { display: flex; justify-content: center; margin-bottom: var(--space-3); }
.login-card .brand-mark img.drop { height: 40px; }
.login-card .brand-mark .wordmark { font-size: 18px; }
.login-card h3 {
  margin: var(--space-2) 0 4px;
  font-size: 14px;
  text-align: center;
  color: var(--ink);
  font-weight: 600;
}
.login-card p.sub {
  margin: 0 0 var(--space-4);
  font-size: 11px;
  color: var(--muted);
  text-align: center;
  font-style: italic;
}
.login-card .error {
  background: var(--severe-bg);
  color: var(--severe-fg);
  padding: 8px var(--space-3);
  border-radius: var(--radius-sm);
  font-size: 12px;
  margin-bottom: var(--space-3);
}
.login-card .footer {
  margin-top: var(--space-3);
  font-size: 11px;
  color: var(--muted);
  text-align: center;
  line-height: 1.5;
}
```

- [ ] **Step 4: Wire the stylesheet into _base.html**

Modify `App/backend/templates/_base.html`. Find the existing `<head>` block and add a `<link>` to the new stylesheet **before** the existing `<style>` block (so the inline rules from this task's pre-existing styles still cascade-win during the interim). Around line 7, after the existing `{% block head_extra %}{% endblock %}`:

```html
    <link rel="stylesheet" href="{{ url_for('static', filename='app.css') }}">
```

Do **not** delete the existing `<style>` block — that happens in Task 3. Both load concurrently in this commit.

- [ ] **Step 5: Confirm tests pass**

```bash
cd App/backend
pytest -q
```

Expected: 129 passed (the previous 128 + the new token-presence test).

Quick smoke that the page still renders unchanged:

```bash
python -c "
from app import app
c = app.test_client()
r = c.get('/login')
assert r.status_code == 200
assert b'Sign in' in r.data
print('login still renders')
"
```

- [ ] **Step 6: Commit**

```bash
cd /Users/tristanmartin/Desktop/GM2/GM2_Aqua_Solutions
git add App/backend/static/app.css App/backend/templates/_base.html App/backend/tests/test_i18n.py
git commit -m "Add static/app.css with design tokens and component primitives"
```

---

## Task 3: Refactor `_base.html` chrome (new topbar + disclaimer slot)

Replace the inline `<style>` block in `_base.html` with the new chrome markup. After this commit the topbar is the dark navy strip with the brand mark; every page gains it; the disclaimer block exists but child templates don't yet use it (Task 4 onwards). The picker partial is restyled to fit the dark header.

**Files:**
- Modify: `App/backend/templates/_base.html`
- Modify: `App/backend/templates/_lang_picker.html`
- Create: `App/backend/tests/test_ui_chrome.py`

- [ ] **Step 1: Write the chrome-markers test**

Create `App/backend/tests/test_ui_chrome.py`:

```python
"""Structural-markers regression net for the UI upgrade.

Walks the public routes and asserts the stable class hooks defined in
the spec (§10) are present. The test does not assert visual outcomes —
that's eyeballed manually. It asserts the *structural contract* so an
accidental rename of a class breaks the build instead of silently
breaking a page.

The set of pages this covers grows as templates convert (Tasks 4-7).
For Task 3 the only contract is "every page has the new topbar".
"""

from __future__ import annotations

import pytest


@pytest.fixture()
def signed_in_gov(client):
    client.post("/login", data={"username": "official.jones", "password": "gov-pw"})
    return client


@pytest.fixture()
def signed_in_med(client):
    client.post("/login", data={"username": "dr.smith", "password": "med-pw"})
    return client


def test_login_has_topbar_and_brand_mark(client):
    resp = client.get("/login")
    assert resp.status_code == 200
    assert b'class="topbar"' in resp.data
    assert b'class="brand-mark"' in resp.data


def test_dashboard_has_topbar_and_brand_mark(signed_in_gov):
    resp = signed_in_gov.get("/dashboard")
    assert resp.status_code == 200
    assert b'class="topbar"' in resp.data
    assert b'class="brand-mark"' in resp.data


def test_medical_report_form_has_topbar_and_brand_mark(signed_in_med):
    resp = signed_in_med.get("/medical/report")
    assert resp.status_code == 200
    assert b'class="topbar"' in resp.data
    assert b'class="brand-mark"' in resp.data


def test_medical_history_has_topbar_and_brand_mark(signed_in_med):
    resp = signed_in_med.get("/medical/history")
    assert resp.status_code == 200
    assert b'class="topbar"' in resp.data
    assert b'class="brand-mark"' in resp.data
```

- [ ] **Step 2: Confirm it fails**

```bash
cd App/backend
pytest tests/test_ui_chrome.py -v
```

Expected: all four tests fail (no `class="topbar"` in current output — the current chrome class is something else / non-existent).

- [ ] **Step 3: Rewrite `_base.html`**

Replace the entire contents of `App/backend/templates/_base.html` with:

```html
<!doctype html>
<html lang="{{ current_lang() }}">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>{% block title %}{{ _("Water-safety pipeline") }}{% endblock %}</title>
    {% block head_extra %}{% endblock %}
    <link rel="stylesheet" href="{{ url_for('static', filename='app.css') }}">
    {% block extra_style %}{% endblock %}
</head>
<body class="app {% block body_class %}{% endblock %}">
    <header class="topbar">
        <span class="brand-mark">
            <img class="drop" src="{{ url_for('static', filename='aqua_solutions_drop.png') }}" alt="">
            <span class="wordmark"><span class="aqua">AQUA</span> <span class="solutions">SOLUTIONS</span></span>
        </span>
        <div class="right">
            {% if session.get('username') %}
                <span class="user-meta">{{ session['display_name'] }} · {{ session['role'] }}</span>
            {% endif %}
            {% include "_lang_picker.html" %}
            {% if session.get('username') %}
                <a href="{{ url_for('logout') }}">{{ _("Sign out") }}</a>
            {% endif %}
        </div>
    </header>
    {% block unverified_banner %}
        {% if unverified_locale() %}
            <div class="unverified-banner">
                {# TRANSLATORS: shown on every page when the active locale's
                   catalog still has unverified (fuzzy) machine-translated entries. #}
                {{ _("Machine-translated draft — awaiting native review. "
                     "Translations of medical terms may be inaccurate; "
                     "for clinical decisions, switch to English.") }}
            </div>
        {% endif %}
    {% endblock %}
    {% block disclaimer %}
        <div class="disclaim">⚠ {{ _("NOT a cholera detector.") }}</div>
    {% endblock %}
    <main class="app-main">
        {% block content %}{% endblock %}
    </main>
    {% block scripts %}{% endblock %}
</body>
</html>
```

Notes:
- The old inline `<style>` block is gone — all styling now comes from `static/app.css` (loaded above) plus any `extra_style` blocks child templates contribute.
- The `.unverified-banner` class is still referenced from `_base.html` but its CSS lives back in any child template that still defines it. We'll move that rule to `app.css` in the Task 8 sweep — for now the banner still renders correctly because it relies on a single yellow strip rule that can come from anywhere.
- The disclaimer block defaults to a slim red strip; login overrides it in Task 4.
- `session.get('username')` is the existing key; surfacing it in the topbar so the right-side meta works without any view-layer changes.

- [ ] **Step 4: Restyle `_lang_picker.html`**

Replace the contents of `App/backend/templates/_lang_picker.html` with:

```html
{# Top-right language picker. Submits to POST /lang.
   Styled to sit in the dark topbar — see .topbar .right select in app.css. #}
<form method="POST" action="/lang" class="lang-picker" style="margin:0">
    <select name="code" onchange="this.form.submit()" aria-label="{{ _('Language') }}">
        {% for code, label in LANGUAGES.items() %}
            <option value="{{ code }}" {% if code == current_lang() %}selected{% endif %}>
                {{ label }}
            </option>
        {% endfor %}
    </select>
</form>
```

(Functionally unchanged; the `margin: 0` is to remove the default `<form>` margin so the select aligns with the surrounding flex items.)

- [ ] **Step 5: Add a temporary unverified-banner rule to app.css**

The banner was being styled by a rule that previously lived in the inline `<style>` block we just removed. Add it to `app.css` now so we don't regress the banner's appearance.

In `App/backend/static/app.css`, immediately after the `/* ----- Disclaimer strip ----- */` block, append:

```css
/* ----- Unverified-translation banner (from the i18n work) ----- */
.unverified-banner {
  background: rgba(255, 215, 0, 0.08);
  border-bottom: 1px solid rgba(255, 215, 0, 0.25);
  color: #f6d97b;
  padding: 8px var(--space-4);
  font-size: 13px;
  text-align: center;
}
```

(Yellow on yellow-tinted, distinct from the disclaimer red strip — same as before this refactor.)

- [ ] **Step 6: Confirm chrome tests pass**

```bash
cd App/backend
pytest tests/test_ui_chrome.py -v
```

Expected: all four tests pass.

- [ ] **Step 7: Confirm the full suite still passes**

```bash
pytest -q
```

Expected: 133 passed (previous 129 + 4 new chrome tests).

- [ ] **Step 8: Visual smoke**

```bash
python -c "
from app import app
c = app.test_client()
c.post('/login', data={'username':'official.jones','password':'demo-gov-2026'})
r = c.get('/dashboard')
body = r.data.decode('utf-8')
print('topbar present:', '<header class=\"topbar\"' in body)
print('brand-mark present:', '<span class=\"brand-mark\"' in body)
print('disclaimer present:', '<div class=\"disclaim\"' in body)
print('cholera disclaimer text present:', 'cholera detector' in body)
assert all([
    '<header class=\"topbar\"' in body,
    '<span class=\"brand-mark\"' in body,
    '<div class=\"disclaim\"' in body,
])
print('OK')
"
```

Expected: all True, "OK" printed. (Dashboard body styling still reflects the old per-template CSS at this point — that's fine; Task 5 converts the body.)

- [ ] **Step 9: Commit**

```bash
cd /Users/tristanmartin/Desktop/GM2/GM2_Aqua_Solutions
git add App/backend/templates/_base.html App/backend/templates/_lang_picker.html App/backend/static/app.css App/backend/tests/test_ui_chrome.py
git commit -m "Refactor _base.html chrome to new topbar + disclaimer slot"
```

---

## Task 4: Convert `login.html` to the new layout

Login is the simplest page to convert and the right place to validate the chrome on a sparse layout. The new layout: centered card on the page background, brand mark above the form title, no disclaimer (login overrides the new block to empty), no unverified-banner.

**Files:**
- Modify: `App/backend/templates/login.html`
- Modify: `App/backend/tests/test_ui_chrome.py`

- [ ] **Step 1: Extend the chrome-markers test for login**

Append to `App/backend/tests/test_ui_chrome.py`:

```python
def test_login_uses_login_card_and_no_disclaimer(client):
    """Login overrides the disclaimer block to empty and renders a
    centered card with the brand mark above the form."""
    resp = client.get("/login")
    body = resp.data
    assert b'class="login-card"' in body
    # The body class signals login layout so app.css can centre the card.
    assert b'app-login' in body
    # Disclaimer block is overridden to empty.
    assert b'class="disclaim"' not in body
    # Form fields still present.
    assert b'name="username"' in body
    assert b'name="password"' in body
```

- [ ] **Step 2: Confirm it fails**

```bash
cd App/backend
pytest tests/test_ui_chrome.py::test_login_uses_login_card_and_no_disclaimer -v
```

Expected: fails — login still uses the old layout.

- [ ] **Step 3: Rewrite `login.html`**

Replace the entire contents of `App/backend/templates/login.html` with:

```html
{% extends "_base.html" %}

{% block title %}{{ _("Sign in") }} — {{ _("Water-safety pipeline") }}{% endblock %}

{% block body_class %}app-login{% endblock %}

{# Front page intentionally skips the machine-translated draft banner —
   no clinical content here, so the warning is irrelevant. #}
{% block unverified_banner %}{% endblock %}

{# Login also skips the cholera disclaimer — it's a public sign-in page. #}
{% block disclaimer %}{% endblock %}

{% block content %}
<div class="login-body">
    <div class="login-card">
        <span class="brand-mark">
            <img class="drop" src="{{ url_for('static', filename='aqua_solutions_drop.png') }}" alt="">
            <span class="wordmark"><span class="aqua">AQUA</span> <span class="solutions">SOLUTIONS</span></span>
        </span>
        <h3>{{ _("Water-safety pipeline") }}</h3>
        {# TRANSLATORS: tagline under the sign-in title, from the brand. #}
        <p class="sub">{{ _("clean water for Africa") }}</p>

        {% if error %}<div class="error">{{ error }}</div>{% endif %}

        <form method="POST" action="{{ url_for('login') }}">
            <div class="field">
                <label for="username">{{ _("Username") }}</label>
                <input type="text" id="username" name="username" autocomplete="username" autofocus required>
            </div>
            <div class="field">
                <label for="password">{{ _("Password") }}</label>
                <input type="password" id="password" name="password" autocomplete="current-password" required>
            </div>
            <input type="hidden" name="next" value="{{ request.args.get('next', '') }}">
            <button type="submit" class="btn" style="width:100%">{{ _("Sign in") }}</button>
        </form>

        <div class="footer">
            {{ _("Sign in as a government official to view the station-status dashboard, or as a medical professional to file an illness report.") }}
        </div>
    </div>
</div>
{% endblock %}
```

- [ ] **Step 4: Confirm tests pass**

```bash
cd App/backend
pytest tests/test_ui_chrome.py -v
pytest -q
```

Expected: all chrome tests pass; full suite green (134 passed = previous 133 + 1 new).

- [ ] **Step 5: Visual smoke**

```bash
python -c "
from app import app
c = app.test_client()
r = c.get('/login')
body = r.data.decode('utf-8')
assert 'login-card' in body, 'login-card not present'
assert 'brand-mark' in body, 'brand-mark not present'
assert 'disclaim' not in body, 'disclaim leaked onto login'
assert 'aqua_solutions_drop.png' in body, 'drop image not referenced'
print('login looks correct')
"
```

- [ ] **Step 6: Commit**

```bash
git add App/backend/templates/login.html App/backend/tests/test_ui_chrome.py
git commit -m "Convert login.html to new card layout with brand mark"
```

---

## Task 5: Convert `dashboard.html` to panels + rows + pills

Largest page, most components exercised here. Two `.panel` cards side-by-side: Station status (left) with action buttons inline per row, Recent illness reports (right) with risk-tier pills.

**Files:**
- Modify: `App/backend/templates/dashboard.html`
- Modify: `App/backend/tests/test_ui_chrome.py`

- [ ] **Step 1: Extend the chrome-markers test for dashboard**

Append to `App/backend/tests/test_ui_chrome.py`:

```python
def test_dashboard_uses_panels_rows_and_pills(signed_in_gov):
    resp = signed_in_gov.get("/dashboard")
    body = resp.data
    # Two-column grid for the two panels.
    assert b'class="grid-2"' in body
    # Two panels (Station status + Recent illness reports).
    assert body.count(b'class="panel"') >= 2
    # At least one status pill (clear/severe/unsafe).
    assert (
        b'class="pill pill-clear"' in body
        or b'class="pill pill-severe"' in body
    )
```

- [ ] **Step 2: Confirm it fails**

```bash
pytest tests/test_ui_chrome.py::test_dashboard_uses_panels_rows_and_pills -v
```

Expected: fails — dashboard still has the old classes.

- [ ] **Step 3: Read the current dashboard.html**

Before editing, read the current `App/backend/templates/dashboard.html` to understand its data bindings (loop variables, `url_for` references, conditional classes for clear/unsafe/closed stations). Preserve them all — only the *markup* changes.

- [ ] **Step 4: Rewrite dashboard.html using primitives**

Replace the contents of `App/backend/templates/dashboard.html` with:

```html
{% extends "_base.html" %}

{% block title %}{{ _("Dashboard") }} — {{ _("Water-safety pipeline") }}{% endblock %}

{% block head_extra %}
    <meta http-equiv="refresh" content="30">
{% endblock %}

{% block content %}
<div class="grid-2">

    <section class="panel">
        <h4>{{ _("Station status") }}</h4>
        {% for s in stations %}
            <div class="row">
                <span>
                    {% if s.is_closed %}🔒 {% endif %}
                    <span class="mono">STN-{{ s.station_id }}</span>
                    · {{ s.name }}
                </span>
                <span class="btn-row">
                    {% if s.latest_label == 'unsafe' %}
                        <span class="pill pill-severe">{{ _("UNSAFE") }}</span>
                    {% else %}
                        <span class="pill pill-clear">{{ _("CLEAR") }}</span>
                    {% endif %}
                    <form method="POST" action="{{ url_for('post_action') }}" style="display:inline;margin:0"
                          onsubmit="return confirm('{{ _('Confirm action on station') }} {{ s.station_id }}?')">
                        <input type="hidden" name="station_id" value="{{ s.station_id }}">
                        {% if s.is_closed %}
                            <input type="hidden" name="action_type" value="reopen_borehole">
                            <button type="submit" class="btn btn-light">{{ _("Reopen") }}</button>
                        {% else %}
                            <input type="hidden" name="action_type" value="close_borehole">
                            <button type="submit" class="btn btn-danger">{{ _("Close") }}</button>
                        {% endif %}
                    </form>
                </span>
            </div>
        {% endfor %}
    </section>

    <section class="panel">
        <h4>{{ _("Recent illness reports") }}</h4>
        {% if reports %}
            {% for r in reports %}
                <div class="row">
                    <span>
                        <a href="{{ url_for('dashboard_report_detail', report_id=r.report_id) }}">
                            <span class="mono">{{ r.received_at[:16] }}</span>
                            ·
                            {% if r.station_id %}
                                <span class="mono">STN-{{ r.station_id }}</span>
                            {% else %}
                                <span class="pill pill-medium">{{ _("UNPARSED") }}</span>
                            {% endif %}
                        </a>
                    </span>
                    <span>
                        {% if r.risk_tier == 'severe' %}
                            <span class="pill pill-severe">{{ _("SEVERE") }}</span>
                        {% elif r.risk_tier == 'high' %}
                            <span class="pill pill-high">{{ _("HIGH") }}</span>
                        {% elif r.risk_tier == 'medium' %}
                            <span class="pill pill-medium">{{ _("MEDIUM") }}</span>
                        {% elif r.risk_tier == 'low' %}
                            <span class="pill pill-clear">{{ _("LOW") }}</span>
                        {% else %}
                            —
                        {% endif %}
                    </span>
                </div>
            {% endfor %}
        {% else %}
            <p class="row" style="color:var(--muted)">{{ _("No reports yet.") }}</p>
        {% endif %}
    </section>

</div>
{% endblock %}
```

If any data binding above doesn't match what the existing dashboard.html exposes from the view (for example a different attribute name on the station or report dict), update the binding to match the view — do **not** change the view. The view is the source of truth for what's available.

- [ ] **Step 5: Confirm tests pass**

```bash
pytest tests/test_ui_chrome.py -v
pytest -q
```

Expected: all green (135 passed).

- [ ] **Step 6: Visual smoke**

```bash
python -c "
from app import app
c = app.test_client()
c.post('/login', data={'username':'official.jones','password':'demo-gov-2026'})
r = c.get('/dashboard')
body = r.data.decode('utf-8')
print('panels:', body.count('class=\"panel\"'))
print('rows:', body.count('class=\"row\"'))
print('pill-clear/severe present:',
      'pill pill-clear' in body or 'pill pill-severe' in body)
assert body.count('class=\"panel\"') >= 2
print('dashboard looks correct')
"
```

- [ ] **Step 7: Commit**

```bash
git add App/backend/templates/dashboard.html App/backend/tests/test_ui_chrome.py
git commit -m "Convert dashboard.html to panel + row + pill primitives"
```

---

## Task 6: Convert `medical_report.html` to the compact form

Compact 3-col header (Station / Cases / Onset), symptoms as `.chip` toggles, risk tier as `.segmented` control, notes textarea full-width, buttons right-aligned. The form needs a small inline JavaScript helper so chips and segmented cells toggle on click (they're not native form controls).

**Files:**
- Modify: `App/backend/templates/medical_report.html`
- Modify: `App/backend/tests/test_ui_chrome.py`

- [ ] **Step 1: Extend the chrome-markers test**

Append to `App/backend/tests/test_ui_chrome.py`:

```python
def test_medical_report_form_uses_chips_and_segmented(signed_in_med):
    resp = signed_in_med.get("/medical/report")
    body = resp.data
    assert b'class="form-grid-3"' in body
    assert b'class="chip"' in body or b"class='chip'" in body
    assert b'class="segmented"' in body
```

- [ ] **Step 2: Confirm it fails**

```bash
pytest tests/test_ui_chrome.py::test_medical_report_form_uses_chips_and_segmented -v
```

Expected: fails.

- [ ] **Step 3: Read the current medical_report.html and view function**

Read both:
- `App/backend/templates/medical_report.html` — the existing form names + bindings.
- `App/backend/app.py` `medical_report_form()` and `medical_report_submit()` — the field names POST expects.

Preserve every input name. The compact form re-arranges layout; it does not rename a single form field.

- [ ] **Step 4: Rewrite medical_report.html**

Replace the contents of `App/backend/templates/medical_report.html` with:

```html
{% extends "_base.html" %}

{% block title %}{{ _("File a report") }} — {{ _("Water-safety pipeline") }}{% endblock %}

{% block content %}
<section class="panel">
    <h4>{{ _("File a community illness report") }}</h4>

    {% if success_message %}<div class="pill pill-clear" style="display:block;padding:8px var(--space-3);font-family:var(--font-sans);font-size:12px;margin-bottom:var(--space-3)">{{ success_message }}</div>{% endif %}
    {% if error_message %}<div class="pill pill-severe" style="display:block;padding:8px var(--space-3);font-family:var(--font-sans);font-size:12px;margin-bottom:var(--space-3)">{{ error_message }}</div>{% endif %}

    <form method="POST" action="{{ url_for('medical_report_submit') }}" id="report-form">

        <div class="form-grid-3">
            <div class="field">
                <label for="station_id">{{ _("Station") }}</label>
                <select id="station_id" name="station_id" required>
                    <option value="">— {{ _("select") }} —</option>
                    {% for s in stations %}
                        <option value="{{ s.station_id }}">{{ s.station_id }} · {{ s.name }}</option>
                    {% endfor %}
                </select>
            </div>
            <div class="field">
                <label for="case_count">{{ _("Cases") }}</label>
                <input id="case_count" type="number" name="case_count" min="1" max="200" required>
            </div>
            <div class="field">
                <label for="onset_date">{{ _("Onset date") }}</label>
                <input id="onset_date" type="date" name="onset_date">
            </div>
        </div>

        <div class="field-row">
            <label>{{ _("Symptoms") }}</label>
            <div class="inline-row" id="symptom-chips">
                {% for key, label in symptoms %}
                    <span class="chip" data-symptom="{{ key }}" onclick="toggleChip(this)">
                        <span class="check">✓</span> {{ label }}
                    </span>
                {% endfor %}
            </div>
        </div>

        <div class="field-row">
            <label>{{ _("Risk tier") }} <span style="font-weight:500;text-transform:none;color:var(--muted)">({{ _("clinical assessment, optional") }})</span></label>
            <div class="segmented" id="risk-tier">
                <span class="seg on" data-tier="" onclick="pickTier(this)">{{ _("Not assessed") }}</span>
                <span class="seg" data-tier="low" onclick="pickTier(this)">LOW</span>
                <span class="seg" data-tier="medium" onclick="pickTier(this)">MEDIUM</span>
                <span class="seg" data-tier="high" onclick="pickTier(this)">HIGH</span>
                <span class="seg" data-tier="severe" onclick="pickTier(this)">SEVERE</span>
            </div>
        </div>

        <div class="field">
            <label for="notes">{{ _("Notes") }} <span style="font-weight:500;text-transform:none;color:var(--muted)">({{ _("optional") }})</span></label>
            <textarea id="notes" name="notes" rows="2"></textarea>
        </div>

        {# Hidden inputs the JS keeps in sync with the chips + segmented control. #}
        <input type="hidden" id="symptoms-hidden" name="symptoms" value="">
        <input type="hidden" id="risk-tier-hidden" name="risk_tier" value="">

        <div class="meta-row">
            <span style="font-size:11px;color:var(--muted)">{{ _("Reviewed by the government dashboard within ~30s of submission.") }}</span>
            <div class="btn-row">
                <button type="reset" class="btn btn-light" onclick="resetForm()">{{ _("Reset") }}</button>
                <button type="submit" class="btn">{{ _("Submit report") }}</button>
            </div>
        </div>
    </form>
</section>
{% endblock %}

{% block scripts %}
<script>
  function toggleChip(el) {
    el.classList.toggle('on');
    syncSymptoms();
  }
  function syncSymptoms() {
    const on = Array.from(document.querySelectorAll('#symptom-chips .chip.on'))
                    .map(c => c.dataset.symptom);
    document.getElementById('symptoms-hidden').value = on.join(',');
  }
  function pickTier(el) {
    document.querySelectorAll('#risk-tier .seg').forEach(s => s.classList.remove('on'));
    el.classList.add('on');
    document.getElementById('risk-tier-hidden').value = el.dataset.tier;
  }
  function resetForm() {
    document.querySelectorAll('#symptom-chips .chip').forEach(c => c.classList.remove('on'));
    syncSymptoms();
    document.querySelectorAll('#risk-tier .seg').forEach(s => s.classList.remove('on'));
    const firstSeg = document.querySelector('#risk-tier .seg');
    if (firstSeg) { firstSeg.classList.add('on'); document.getElementById('risk-tier-hidden').value = ''; }
  }
</script>
{% endblock %}
```

Notes for the implementer:
- `symptoms` from the view is a list of `(key, label)` tuples — Jinja `{% for key, label in symptoms %}` unpacks them. This matches what the existing template uses (verify by inspection).
- The chips and segmented control are not native form controls; two hidden inputs (`symptoms`, `risk_tier`) carry the values to the server. The view handler already reads both from `request.form` — preserve those parameter names exactly.
- If the existing view sends `request.form.getlist('symptoms')` (multi-checkbox style) instead of a comma-separated string, switch the JS to render multiple `<input type="hidden" name="symptoms" value="X">` instead of one. Inspect the view function once before submitting this task.

- [ ] **Step 5: Confirm tests pass**

```bash
pytest tests/test_ui_chrome.py -v
pytest -q
```

Expected: all green (136 passed).

- [ ] **Step 6: Manual functional test**

Posting the form must still work end-to-end. Run:

```bash
python -c "
from app import app
c = app.test_client()
c.post('/login', data={'username':'dr.smith','password':'demo-medical-2026'})
r = c.get('/medical/report')
assert r.status_code == 200
assert b'form-grid-3' in r.data
assert b'segmented' in r.data
assert b'chip' in r.data
print('medical_report renders new layout')

# Functional check: POST a minimal report and confirm the server accepts it.
r2 = c.post('/medical/report', data={
    'station_id': '1',
    'case_count': '2',
    'symptoms': 'diarrhoea,fever',
    'onset_date': '2026-05-30',
    'risk_tier': '',
})
print('POST status:', r2.status_code)
assert r2.status_code in (200, 302), 'unexpected response'
print('medical_report POST still accepted')
"
```

- [ ] **Step 7: Commit**

```bash
git add App/backend/templates/medical_report.html App/backend/tests/test_ui_chrome.py
git commit -m "Convert medical_report.html to compact form (chips + segmented)"
```

---

## Task 7: Convert the three remaining templates (history + two details)

Apply `.panel`, `.kv`, `.reading-table`, `.btn*` to `medical_history.html`, `medical_report_detail.html`, and `dashboard_report_detail.html`. Layout choices follow spec §6.

**Files:**
- Modify: `App/backend/templates/medical_history.html`
- Modify: `App/backend/templates/medical_report_detail.html`
- Modify: `App/backend/templates/dashboard_report_detail.html`
- Modify: `App/backend/tests/test_ui_chrome.py`

- [ ] **Step 1: Extend the chrome-markers test for all three**

Append to `App/backend/tests/test_ui_chrome.py`:

```python
def test_medical_history_uses_panels(signed_in_med):
    resp = signed_in_med.get("/medical/history")
    body = resp.data
    # Two panels: the map and the reports table.
    assert body.count(b'class="panel"') >= 2


def test_medical_report_detail_uses_kv(signed_in_med):
    # Need a report row to exist. Skip if none — that's a fixture problem,
    # not a UI bug.
    from sqlalchemy import text as sql_text
    import sys
    db = sys.modules['database']
    with db.connection() as conn:
        row = conn.execute(sql_text(
            "SELECT report_id FROM illness_reports "
            "WHERE report_source='medical_portal' LIMIT 1"
        )).fetchone()
    if row is None:
        pytest.skip("no medical_portal report fixture available")
    resp = signed_in_med.get(f"/medical/reports/{row[0]}")
    assert resp.status_code == 200
    assert b'class="kv"' in resp.data


def test_dashboard_report_detail_uses_grid_and_actions(signed_in_gov):
    from sqlalchemy import text as sql_text
    import sys
    db = sys.modules['database']
    with db.connection() as conn:
        row = conn.execute(sql_text(
            "SELECT report_id FROM illness_reports LIMIT 1"
        )).fetchone()
    if row is None:
        pytest.skip("no report fixture available")
    resp = signed_in_gov.get(f"/dashboard/reports/{row[0]}")
    assert resp.status_code == 200
    body = resp.data
    assert b'class="grid-2-asym"' in body
    assert b'class="kv"' in body
    assert b'class="btn' in body
```

- [ ] **Step 2: Confirm it fails**

```bash
pytest tests/test_ui_chrome.py -v
```

Expected: the three new tests fail (the existing tests still pass).

- [ ] **Step 3: Read the three current templates and their views**

For each of the three:
- Read the current template's data bindings.
- Read the matching view function in `app.py` for the exact context-variable names.

This is the single most important defensive step in this task. The HTML is being rewritten; the view→template contract must stay byte-identical.

- [ ] **Step 4: Rewrite `medical_history.html`**

Replace the contents of `App/backend/templates/medical_history.html` with:

```html
{% extends "_base.html" %}

{% block title %}{{ _("Medical history") }} — {{ _("Water-safety pipeline") }}{% endblock %}

{% block head_extra %}
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css">
{% endblock %}

{% block extra_style %}
    /* Page-specific: the Leaflet map sizing. */
    #harare-map { height: 300px; width: 100%; }
{% endblock %}

{% block content %}
<div class="crumb"><a href="{{ url_for('medical_report_form') }}">← {{ _("File a report") }}</a></div>

<section class="panel">
    <h4>{{ _("Stations with medical reports") }}</h4>
    <div id="harare-map"></div>
</section>

<section class="panel">
    <h4>{{ _("Recent medical reports") }}</h4>
    <table class="reading-table" style="width:100%">
        <thead>
            <tr>
                <th>{{ _("Submitted") }}</th>
                <th>{{ _("Submitter") }}</th>
                <th>{{ _("Station") }}</th>
                <th>{{ _("Cases") }}</th>
                <th>{{ _("Symptoms") }}</th>
                <th>{{ _("Risk tier") }}</th>
                <th>{{ _("Onset") }}</th>
            </tr>
        </thead>
        <tbody>
            {% for r in reports %}
                <tr>
                    <td>{{ r.received_at[:16] }}</td>
                    <td>{{ r.submitter or '—' }}</td>
                    <td>{{ r.station_id or '—' }}</td>
                    <td>{{ r.case_count or '—' }}</td>
                    <td>{{ r.symptoms or '—' }}</td>
                    <td>
                        {% if r.risk_tier %}
                            <span class="pill pill-{{ r.risk_tier }}">{{ r.risk_tier|upper }}</span>
                        {% else %}
                            —
                        {% endif %}
                    </td>
                    <td>{{ r.onset_date or '—' }}</td>
                </tr>
            {% endfor %}
        </tbody>
    </table>
</section>
{% endblock %}

{% block scripts %}
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<script>
  const map = L.map('harare-map').setView([-17.8292, 31.0522], 12);
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '© OpenStreetMap'
  }).addTo(map);
  const stations = {{ stations_json|safe }};
  stations.forEach(s => {
    if (s.lat && s.lon) {
      L.circleMarker([s.lat, s.lon], {
        radius: Math.max(6, s.report_count * 3),
        color: '#1a2b47',
        fillColor: '#3eb1e8',
        fillOpacity: 0.6,
      }).bindPopup(`<b>${s.name}</b><br>${s.report_count} report(s)`).addTo(map);
    }
  });
</script>
{% endblock %}
```

Notes:
- `stations_json` is the existing view-side variable; if the view exposes a different name, adapt the template binding (not the view).
- Pill class uses `pill-{{ r.risk_tier }}` — the tier strings `low`, `medium`, `high`, `severe` map to the four `.pill-*` classes defined in `app.css`. `low` maps to `pill-low` which doesn't exist; map it to `pill-clear` explicitly:

Replace the pill block with:

```html
{% if r.risk_tier == 'low' %}<span class="pill pill-clear">LOW</span>
{% elif r.risk_tier == 'medium' %}<span class="pill pill-medium">MEDIUM</span>
{% elif r.risk_tier == 'high' %}<span class="pill pill-high">HIGH</span>
{% elif r.risk_tier == 'severe' %}<span class="pill pill-severe">SEVERE</span>
{% else %}—{% endif %}
```

- [ ] **Step 5: Rewrite `medical_report_detail.html`**

Replace with:

```html
{% extends "_base.html" %}

{% block title %}{{ _("Report") }} #{{ report.report_id }} — {{ _("Water-safety pipeline") }}{% endblock %}

{% block content %}
<div class="crumb">
    <a href="{{ url_for('medical_history') }}">← {{ _("Medical history") }}</a>
    &nbsp;›&nbsp;
    {{ _("Report") }} <span class="mono">#{{ report.report_id }}</span>
</div>

<section class="panel">
    <h4>{{ _("Report") }}</h4>
    <dl class="kv">
        <dt>{{ _("Source") }}</dt><dd>{{ report.report_source|upper }}</dd>
        <dt>{{ _("Submitter") }}</dt><dd>{{ report.submitter or '—' }}</dd>
        <dt>{{ _("Received") }}</dt><dd>{{ report.received_at }}</dd>
        <dt>{{ _("Station") }}</dt><dd>{% if report.station_id %}<span class="mono">STN-{{ report.station_id }}</span> · {{ station_name or '' }}{% else %}—{% endif %}</dd>
        <dt>{{ _("Case count") }}</dt><dd>{{ report.case_count or '—' }}</dd>
        <dt>{{ _("Symptoms") }}</dt><dd>{{ report.symptoms or '—' }}</dd>
        <dt>{{ _("Onset") }}</dt><dd>{{ report.onset_date or '—' }}</dd>
        <dt>{{ _("Risk tier") }}</dt>
        <dd>
            {% if report.risk_tier == 'low' %}<span class="pill pill-clear">LOW</span>
            {% elif report.risk_tier == 'medium' %}<span class="pill pill-medium">MEDIUM</span>
            {% elif report.risk_tier == 'high' %}<span class="pill pill-high">HIGH</span>
            {% elif report.risk_tier == 'severe' %}<span class="pill pill-severe">SEVERE</span>
            {% else %}—{% endif %}
        </dd>
    </dl>
</section>
{% endblock %}
```

- [ ] **Step 6: Rewrite `dashboard_report_detail.html`**

Replace with:

```html
{% extends "_base.html" %}

{% block title %}{{ _("Report") }} #{{ report.report_id }} — {{ _("Dashboard") }}{% endblock %}

{% block content %}
<div class="crumb">
    <a href="{{ url_for('dashboard') }}">← {{ _("Dashboard") }}</a>
    &nbsp;›&nbsp;
    {{ _("Report") }} <span class="mono">#{{ report.report_id }}</span>
    {% if station_name %} · {{ station_name }}{% endif %}
</div>

<div class="grid-2-asym">
    <div>
        <section class="panel">
            <h4>{{ _("Structured fields") }}</h4>
            <dl class="kv">
                <dt>{{ _("Source") }}</dt><dd>{{ report.report_source|upper }}</dd>
                <dt>{{ _("Submitter") }}</dt><dd>{{ report.submitter or report.reporter_phone or '—' }}</dd>
                <dt>{{ _("Received") }}</dt><dd>{{ report.received_at }}</dd>
                <dt>{{ _("Station") }}</dt><dd>{% if report.station_id %}<span class="mono">STN-{{ report.station_id }}</span>{% else %}—{% endif %}</dd>
                <dt>{{ _("Case count") }}</dt><dd>{{ report.case_count or '—' }}</dd>
                <dt>{{ _("Symptoms") }}</dt><dd>{{ report.symptoms or '—' }}</dd>
                <dt>{{ _("Onset") }}</dt><dd>{{ report.onset_date or '—' }}</dd>
                <dt>{{ _("Risk tier") }}</dt>
                <dd>
                    {% if tier %}
                        {% if tier == 'low' %}<span class="pill pill-clear">LOW</span>
                        {% elif tier == 'medium' %}<span class="pill pill-medium">MEDIUM</span>
                        {% elif tier == 'high' %}<span class="pill pill-high">HIGH</span>
                        {% elif tier == 'severe' %}<span class="pill pill-severe">SEVERE</span>{% endif %}
                        {% if not report.risk_tier %}<span style="color:var(--muted);font-size:10px">({{ _("estimated") }})</span>{% endif %}
                    {% else %}—{% endif %}
                </dd>
            </dl>
            {% if tier_rationale %}
                <p style="font-size:11px;color:var(--muted);margin-top:var(--space-2)">{{ tier_rationale }}</p>
            {% endif %}
        </section>

        {% if labelled_readings %}
        <section class="panel">
            <h4>{{ _("Labelled readings") }}</h4>
            <table class="reading-table">
                <thead>
                    <tr>
                        <th>#</th><th>{{ _("Recorded") }}</th>
                        <th>pH</th><th>{{ _("Turb") }}</th><th>{{ _("Temp") }}</th>
                        <th>{{ _("Rule") }}</th>
                    </tr>
                </thead>
                <tbody>
                    {% for r in labelled_readings %}
                        <tr>
                            <td>{{ r.reading_id }}</td>
                            <td>{{ r.recorded_at[:16] }}</td>
                            <td>{{ r.ph if r.ph is not none else '—' }}</td>
                            <td>{{ r.turbidity_ntu if r.turbidity_ntu is not none else '—' }}</td>
                            <td>{{ r.temperature_c if r.temperature_c is not none else '—' }}</td>
                            <td>{{ r.rule_description }}</td>
                        </tr>
                    {% endfor %}
                </tbody>
            </table>
        </section>
        {% endif %}
    </div>

    <div>
        <section class="panel">
            <h4>{{ _("Actions") }}</h4>
            {% for action_type, label, css in [
                ('close_borehole', _('Close borehole'), 'btn btn-danger'),
                ('dispatch_sample_team', _('Dispatch sample team'), 'btn btn-light'),
                ('dispatch_medical_team', _('Dispatch medical team'), 'btn btn-light')
            ] %}
                <form method="POST" action="{{ url_for('post_action') }}" style="margin-bottom:var(--space-2)">
                    <input type="hidden" name="action_type" value="{{ action_type }}">
                    <input type="hidden" name="station_id" value="{{ report.station_id }}">
                    <input type="hidden" name="related_report_id" value="{{ report.report_id }}">
                    <button type="submit" class="{{ css }}" style="width:100%">{{ label }}</button>
                </form>
            {% endfor %}
        </section>

        {% if interventions %}
        <section class="panel">
            <h4>{{ _("Interventions log") }}</h4>
            {% for iv in interventions %}
                <div class="row">
                    <span class="mono">{{ iv.triggered_at[11:16] }} {{ iv.action_type }}</span>
                    <span>{{ iv.triggered_by }}</span>
                </div>
            {% endfor %}
        </section>
        {% endif %}
    </div>
</div>
{% endblock %}
```

If the view function passes different variable names (e.g. `report.tier` vs the local variable `tier`), adapt the template bindings to match what the view returns — verify with `grep -n "render_template.*dashboard_report_detail" App/backend/app.py`.

- [ ] **Step 7: Confirm tests pass**

```bash
pytest tests/test_ui_chrome.py -v
pytest -q
```

Expected: green. The medical-history / detail tests should now pass; the dashboard-report-detail test may skip if no report fixture exists (that's fine).

- [ ] **Step 8: Manual visual sweep**

```bash
python -c "
from app import app
c = app.test_client()
c.post('/login', data={'username':'dr.smith','password':'demo-medical-2026'})
for path in ['/medical/report', '/medical/history']:
    r = c.get(path)
    assert r.status_code == 200, path
    print(path, 'OK,', len(r.data), 'bytes')

c2 = app.test_client()
c2.post('/login', data={'username':'official.jones','password':'demo-gov-2026'})
r = c2.get('/dashboard')
assert r.status_code == 200
print('/dashboard OK')
"
```

- [ ] **Step 9: Commit**

```bash
git add App/backend/templates/medical_history.html App/backend/templates/medical_report_detail.html App/backend/templates/dashboard_report_detail.html App/backend/tests/test_ui_chrome.py
git commit -m "Convert medical_history, medical_report_detail, dashboard_report_detail to new primitives"
```

---

## Task 8: Sweep — remove legacy CSS, drop `--warn`, final verification

Final cleanup pass. After Tasks 3-7, the per-template `extra_style` blocks should only contain genuinely page-specific layout (e.g., the map height in `medical_history.html`). Remove anything else. Also retire the `--warn` colour token if it's no longer referenced — the new design replaces it with `--medium-fg` / `--accent`.

**Files:**
- Modify: `App/backend/templates/_base.html` (if any orphan styles remain)
- Modify: all template files where `extra_style` blocks still contain shared rules
- Modify: `App/backend/static/app.css` (drop `--warn` if previously added and no longer used)

- [ ] **Step 1: Audit `--warn` usage**

```bash
cd /Users/tristanmartin/Desktop/GM2/GM2_Aqua_Solutions
grep -rn 'var(--warn)\|--warn:' App/backend/static App/backend/templates 2>&1 | grep -v __pycache__
```

If no results: `--warn` was already removed by the cascade of template rewrites. Skip Step 2.

If results in templates: those `extra_style` blocks held a local `--warn` definition that should now be either deleted (if unused) or migrated to one of the new tokens.

- [ ] **Step 2: Drop `--warn` references**

For each `extra_style` block still defining `--warn`, remove the `:root { --warn: …; }` declaration and replace any `var(--warn)` references inside that template with `var(--accent)` (links / highlights) or `var(--medium-fg)` (caution-amber).

- [ ] **Step 3: Audit orphan rules in `extra_style` blocks**

For each of the six converted templates, list what's still inside the `extra_style` block:

```bash
for f in App/backend/templates/login.html App/backend/templates/dashboard.html App/backend/templates/medical_report.html App/backend/templates/medical_history.html App/backend/templates/medical_report_detail.html App/backend/templates/dashboard_report_detail.html; do
    echo "=== $f ==="
    grep -A30 "block extra_style" "$f" | head -32
done
```

For each remaining rule, decide:
- **Truly page-specific layout** (e.g. `#harare-map { height: 300px; }`): keep in the template.
- **Component-shaped or token-shaped**: move to `app.css` (rare at this point, but check).
- **Orphan / no longer referenced**: delete.

If a rule resists categorisation, leave it with a `/* TODO post-launch: review */` comment rather than fighting it (spec §11).

- [ ] **Step 4: Final test run**

```bash
cd App/backend
pytest -q
```

Expected: all green. 136+ tests passed.

- [ ] **Step 5: Manual sweep across 6 templates × 3 locales**

Start Flask locally and click through every page in each of the three languages:

```bash
flask --app app run --port 5001
```

Open in a browser:
- `/login` → confirm login card, brand mark, no disclaimer.
- Sign in as `official.jones` / `demo-gov-2026` → `/dashboard`, `/dashboard/reports/<id>`.
- Sign out, sign in as `dr.smith` / `demo-medical-2026` → `/medical/report`, `/medical/history`, `/medical/reports/<id>`.

For each page, change the language picker to Shona, then Ndebele. Confirm:
- Layout is unchanged (only text changes).
- The disclaimer strip is visible on signed-in pages, hidden on login.
- The unverified-translation banner appears on sn/nd, hidden on en.
- No raw `_(` strings, no `{{ }}` placeholders, no broken images.

Ctrl-C when done.

- [ ] **Step 6: Commit**

```bash
cd /Users/tristanmartin/Desktop/GM2/GM2_Aqua_Solutions
git add App/backend/
git commit -m "Sweep: drop --warn legacy token and orphan extra_style rules"
```

If `git status` shows no changes after Steps 1-3, you can skip the commit — the sweep had nothing to do because earlier tasks were already clean.

---

## Done

After Task 8, the system meets the spec end-to-end. To verify before declaring complete:

1. `pytest -q` from `App/backend/` — 136+ tests pass.
2. `grep -rn 'var(--warn)\|--warn' App/backend/static App/backend/templates` — no results.
3. `wc -l App/backend/templates/*.html` — each template should be smaller than before (most of the CSS dissolved into `app.css`).
4. `git log --oneline | head -10` — eight task commits + the initial spec commit, telling a coherent narrative.
5. Visual sweep above shows every page in every locale with the new chrome.

The branch is then ready to merge per the standard finishing-a-development-branch workflow.
