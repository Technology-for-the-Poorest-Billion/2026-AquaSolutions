# Design — UI upgrade (brand alignment, operational-console direction)

**Date:** 2026-05-31
**Status:** Approved (brainstorming complete; awaiting implementation plan).
**Scope:** Re-skin the Gen-1 Flask web portal to align with the Aqua Solutions brand identity, introducing shared design tokens, component primitives, and a trimmed logo. No information-architecture or feature changes — every page does the same job it does today, but looks like a real product instead of a developer mock-up.

## 1. Context

The Gen-1 portal currently uses a dark theme defined by inline CSS variables in `_base.html` and per-template `<style>` blocks. Recent commits added the Aqua Solutions logo to the login and signed-in pages, but the broader UI does not yet reflect the brand: the dark background fights the logo's light-bg-first design, the accents are a generic mint-green rather than the brand's teal-and-cyan, and component styling is duplicated across templates.

The brand identity (from `App/backend/static/aqua_solutions_logo.png`):
- **Water droplet** with a teal-to-blue gradient (top ≈ `#5fb5a8`, bottom ≈ `#3b8fd1`) and a subtle white highlight curve inside.
- **Wordmark** "AQUA" in navy (`#1a2b47`) + "SOLUTIONS" in cyan (`#3eb1e8`).
- **Tagline** "clean water for Africa" in script.
- **Signal lines** to the right (IoT/connectivity motif).

This redesign keeps the droplet + wordmark and drops the tagline and signal lines, then composes a coherent design system around those brand colors.

## 2. Key design decisions

| Decision | Choice | Rationale |
|---|---|---|
| Visual direction | **Operational console** (light bg + dark navy header strip + dense panels + monospace data) | Audience is government officials and clinicians, not consumers. The information density of the dashboard maps naturally to an ops-tool aesthetic (Grafana, Stripe Dashboard, GOV.UK). Light bg lets the brand logo sit naturally. |
| Theme | **Light** (page bg `--bg: #f1f3f5`, panels `--panel: #ffffff`) | The current dark theme fights the brand. The logo is designed for light. Medical/government dashboards conventionally light-themed. |
| Header treatment | **Dark navy strip** (`--ink: #1a2b47`) carrying the brand | Inverts to white "AQUA" + cyan "SOLUTIONS" on the dark strip; reverts to navy "AQUA" + cyan "SOLUTIONS" on light-card contexts (e.g., login card). Single rule via CSS cascade — no second image asset. |
| Logo asset | **Hybrid: cropped PNG droplet + CSS wordmark** | Keeps the brand droplet exact (gradient + highlight); lets the wordmark recolor for context without exporting two PNGs. One image asset to maintain. |
| CSS organization | **Extract to `static/app.css`** | The inline `<style>` block in `_base.html` will grow ~200 lines with tokens + primitives. A separate stylesheet is cacheable independently of HTML (HTML stays `Cache-Control: no-store` for the picker; CSS caches normally). |
| Information density | **Maintained / slightly increased** | The dashboard's two panels stay; rows get tighter, monospace columns align. No information removed. |
| Mobile | **Out of scope (desktop-first)** | Locked for v1 — the audience uses desktops; mobile waits for a future deliverable. |

## 3. Design tokens

All declared as CSS custom properties at `:root` in `static/app.css`. Everything else (buttons, pills, panels) is composition of these.

### Colour

| Token | Value | Role |
|---|---|---|
| `--ink` | `#1a2b47` | Navy. Header background, primary text, AQUA wordmark on light bg. |
| `--accent` | `#3eb1e8` | Brand cyan. SOLUTIONS wordmark, focus rings, links, panel underlines. |
| `--teal` | `#5fb5a8` | Droplet top. Reserved for sparing subtle accents. |
| `--blue` | `#3b8fd1` | Droplet bottom. Reserved. |
| `--bg` | `#f1f3f5` | Page background. |
| `--panel` | `#ffffff` | Card surfaces. |
| `--border` | `#d6dce3` | Card outlines + dividers. |
| `--muted` | `#6b7280` | Meta text, helper copy, breadcrumbs. |
| `--clear-bg`, `--clear-fg` | `#d6efe2`, `#0f5b3a` | CLEAR pill (low-risk status). Two separate CSS variables. |
| `--medium-bg`, `--medium-fg` | `#fff1cc`, `#8a5b00` | MEDIUM tier pill. Two separate CSS variables. |
| `--high-bg`, `--high-fg` | `#ffd7b3`, `#8a3a00` | HIGH tier pill. Two separate CSS variables. |
| `--severe-bg`, `--severe-fg` | `#fad9d9`, `#7a1c1c` | SEVERE / UNSAFE pill and the disclaimer strip background. Two separate CSS variables. |

Each status row defines **two** CSS custom properties (e.g. `--clear-bg: #d6efe2; --clear-fg: #0f5b3a;`) so a pill can use both via `background: var(--clear-bg); color: var(--clear-fg);`. The disclaimer strip deliberately reuses the SEVERE colour pair so the brand's safety-warning red is one consistent visual signal across the app.

### Typography

| Token | Value | Use |
|---|---|---|
| `--font-sans` | `-apple-system, BlinkMacSystemFont, "Segoe UI", "Helvetica Neue", sans-serif` | Body, labels, form fields, headings. |
| `--font-mono` | `ui-monospace, "SF Mono", Menlo, Consolas, monospace` | IDs, timestamps, measurements, status codes, anything that scans as data. |

No custom font files — inherits the OS native stack. Zero network cost, native rendering quality.

### Scale

| Token | Value |
|---|---|
| `--space-1` | 4px |
| `--space-2` | 8px |
| `--space-3` | 12px |
| `--space-4` | 16px |
| `--space-6` | 24px |
| `--radius-sm` | 3px |
| `--radius-md` | 6px |
| `--radius-lg` | 8px |

## 4. Component primitives

Each primitive is composed of tokens. All defined in `static/app.css`; templates use them by class name with zero per-page customisation unless explicitly noted.

### `.topbar`

`--ink` background, full-width, 8px vertical padding. Contains the brand mark (left) and a right cluster of `username · role` (mono), the language `<select>` (sized to fit the dark strip), and a Sign out link. Replaces the current top-right-only picker bar.

### `.disclaim` (disclaimer strip)

Slim strip under the topbar. `--severe-bg` background, `--severe-fg` text, 11px uppercase: "⚠ NOT a cholera detector — measures contamination indicators only". Always rendered on signed-in pages via a `{% block disclaimer %}` in `_base.html`; the login page overrides the block to empty (same pattern as the unverified-locale banner override).

### `.panel`

White card with `--border` outline, 14px padding. The atomic container for everything on every page. Title is `<h4>` with uppercase 11px, 2px `--accent` bottom border, 8px margin below.

### Buttons (`.btn`, `.btn-light`, `.btn-danger`)

Square (3px radius), 12px font, 600 weight, 6×12px padding.
- `.btn` — primary: `--ink` background, white text.
- `.btn-light` — secondary: white background, `--ink` outline + text.
- `.btn-danger` — destructive: `--severe-fg` background, white text.

### Pills (`.pill`, `.pill-clear`, `.pill-medium`, `.pill-high`, `.pill-severe`)

Monospace 10px, 700 weight, square (no radius), 1×6px padding. Background + foreground from the matching colour pair tokens.

### Chips (`.chip`, `.chip.on`)

Multi-select toggle. `off` = `--panel` background, `--border` outline, `--ink` text. `on` = `--ink` background, white text, leading ✓. Used for symptoms multi-select on `medical_report.html`.

### Segmented control (`.segmented`, `.seg`, `.seg.on`)

Single-pick row. Cells side-by-side with shared outline; `on` cell fills with `--ink` (or with a tier color when the segment represents a risk tier). Used for the Risk tier picker on `medical_report.html`.

### Form field (`.field`)

Uppercase 10px label above the input, 1px `--border` outline on the input, 6×8px padding, 3px radius. Focus state: `border-color: --accent`, `box-shadow: 0 0 0 2px rgba(62,177,232,0.18)` (cyan glow).

### Key-value list (`.kv`)

Two-column grid: 130px label column (uppercase 10px, `--muted`, 700 weight) + mono value column. Used on `medical_report_detail.html` and `dashboard_report_detail.html` for structured fields.

### Reading table (`.reading-table`)

`<thead>` strip in `--bg`, uppercase 10px labels with `--border` bottom; tbody cells in mono with 1px dotted `--border` dividers.

### Breadcrumb (`.crumb`)

`← Parent › Current · Context` in 11px. `--accent` link color for the back arrow; mono treatment for `#id` segments.

### Row patterns (`.row`)

Single-line item with flex space-between. Used for station-status rows and recent-illness rows. Hairline `--border` divider, 5px vertical padding. Hover state subtle gray.

## 5. Logo asset strategy

### Hybrid: cropped droplet + CSS wordmark

The trimmed brand mark is the droplet image + the text "AQUA SOLUTIONS" rendered in HTML.

**Image asset**:
- New file: `App/backend/static/aqua_solutions_drop.png`.
- Generated by a small one-shot script (`scripts/crop_logo.py`, using Pillow): crops the existing `aqua_solutions_logo.png` to the droplet's bounding box, removes the white background (sets near-white pixels to transparent).
- The original `aqua_solutions_logo.png` stays committed for archival purposes; the cropped version is what templates use going forward.

**Wordmark**:
- Rendered as plain HTML in the brand-mark partial (or inline in `_base.html`): `<span class="brand-mark"><img …><span class="wordmark"><span class="aqua">AQUA</span> <span class="solutions">SOLUTIONS</span></span></span>`.
- CSS controls colour per context:
  - Default (`.brand-mark .wordmark .aqua`) → `--ink` (navy).
  - Inside the dark topbar (`.topbar .brand-mark .wordmark .aqua`) → `white`.
  - `.solutions` is `--accent` everywhere.

**Result**:
- One image asset to maintain.
- Wordmark recolours via CSS — no per-context image variants.
- Implementation step has the Pillow crop in a script we commit alongside the asset, so the transformation is reproducible.

## 6. Per-page application

Each existing template gets the new chrome (topbar + disclaimer + panels). Page-specific layout stays in `extra_style` only where layout truly differs.

| Template | Changes | Stays |
|---|---|---|
| `_base.html` | New tokens via `static/app.css`; new `.topbar` layout; `{% block disclaimer %}` slot. Drops the old inline `<style>` block. | `unverified_banner` block, `head_extra`, `scripts`, `content` blocks. |
| `_lang_picker.html` | Smaller `<select>` sized for the dark header strip. | Form action `/lang`, `LANGUAGES` iteration. |
| `login.html` | Centered light card with brand mark above the title; overrides both `unverified_banner` and the new `disclaimer` block to empty. | Form fields, error message slot. |
| `dashboard.html` | Two `.panel` cards (Station status, Recent illness reports). Rows use `.row` + `.pill`. Action buttons inline per station row. | Auto-refresh `<meta>`, server data bindings, link targets to `/dashboard/reports/<id>`. |
| `medical_report.html` | 3-col header row (Station / Cases / Onset); symptoms as `.chip` toggles; risk tier as `.segmented`. Notes textarea full-width. Buttons right-aligned. | Form field `name=` attributes, validation flow, success/error message rendering. |
| `medical_history.html` | Same topbar/disclaimer chrome as the dashboard. Two panels: Leaflet map (panel-card style) on top, reports table below. | Leaflet 1.9.4 CDN init, station JSON binding. |
| `medical_report_detail.html` | Single-panel layout, `.kv` for structured fields, no action buttons. | Read-only server data. |
| `dashboard_report_detail.html` | Two-column layout: left = `.kv` block + reading table; right = action buttons + interventions log. | Action POST form fields, interventions render order, the 403 path for medical users. |

## 7. CSS architecture

**New file: `App/backend/static/app.css`**. Contains:
1. The `:root { --token: value; }` block.
2. `.topbar`, `.disclaim`, `.brand-mark`, `.crumb` (chrome).
3. `.panel`, `.row`, `.kv`, `.reading-table` (containers).
4. `.btn*`, `.pill*`, `.chip*`, `.segmented .seg*`, `.field` (interactive primitives).
5. Status/tier helper classes (`.tier-low`, `.tier-medium` etc.) used by the segmented control.

`_base.html`:
- Replaces the existing inline `<style>` block with `<link rel="stylesheet" href="{{ url_for('static', filename='app.css') }}">`.
- Keeps the `{% block extra_style %}` for genuinely page-specific layout.
- Adds `{% block disclaimer %}` (overridable like the `unverified_banner` block).

Per-template `{% block extra_style %}` blocks shrink dramatically. The map container in `medical_history.html` is the one place where significant page-specific CSS legitimately remains (Leaflet sizing + zoom controls).

The existing `Cache-Control: no-store` after-request hook applies to HTML only — `app.css` is served by Flask's static handler with default caching, so the browser caches it normally.

## 8. Implementation phasing

Eight phases, each committable on its own. Each phase keeps the existing 128 tests green.

1. **Crop the logo.** Write `scripts/crop_logo.py` (Pillow); run it; commit `App/backend/static/aqua_solutions_drop.png`. Existing logo stays in place; nothing references the new asset yet.
2. **Add `static/app.css` with tokens + chrome.** Tokens, `.topbar`, `.disclaim`, `.brand-mark`, `.panel`, `.btn*`, `.pill*`. Wire into `_base.html` via `<link>`. The inline `<style>` block stays for now (both run; child templates use the old). Visual smoke shows nothing visibly changes.
3. **Refactor `_base.html` chrome.** Replace the old topbar block with the new `.topbar` markup using the brand mark. Add the `{% block disclaimer %}` slot. Drop the now-unused inline `<style>` block (most of it). Lang picker partial updated to sit in the dark header. After this step, every page renders the new topbar; bodies still look old.
4. **`login.html`** — convert to the new card layout. Override `unverified_banner` (already in place) and the new `disclaimer` block to empty. Validates the chrome on a sparse page before the dashboard rework.
5. **`dashboard.html`** — largest surface, most components. Convert to `.panel` + `.row` + `.pill`. Per-row action buttons inline.
6. **`medical_report.html`** — the compact-form rework: 3-col header, chip symptoms, segmented risk tier.
7. **`medical_history.html`, `medical_report_detail.html`, `dashboard_report_detail.html`** — chrome already in place; apply `.panel`, `.kv`, `.reading-table`, `.btn*` per the per-page table.
8. **Sweep** — remove the legacy `--warn` token, orphan CSS rules from `extra_style` blocks that are now covered by `app.css`, any leftover inline color literals. Final visual check across all 6 templates × 3 locales.

Each step commits to a feature branch (`feat/ui-upgrade`), then merges to `main` via `--no-ff` once the sweep is complete.

## 9. Out of scope (intentional)

- **Dashboard data visualization.** No charts, no graphs, no sparklines — just better-presented tables.
- **Real-time updates.** Page still uses `<meta http-equiv="refresh" content="30">`. No WebSockets, no SSE.
- **Mobile / responsive layout.** Desktop-first, no breakpoints below ~960px. Future work.
- **Accessibility audit.** Preserve existing ARIA labels and form semantics; do not expand into a full a11y pass (contrast, keyboard nav, screen-reader testing).
- **Animation / micro-interactions** beyond the existing onchange-submit picker.
- **Per-role colour theming** (medical vs government). One visual identity for both.
- **Component documentation site** / Storybook-style component browser.
- **Restyling of SMS auto-replies, Twilio templates, or any non-web surface.**
- **Replacing the existing language picker UX.** Picker stays a `<select>`; only its size and home (dark header) change.
- **Restructuring information architecture.** Every page does the same job, lays out the same data, in the same number of clicks.

## 10. Testing

- **Existing 128 tests stay green** after every phase. Content assertions still hold because no visible copy changes.
- **New structural test** (`tests/test_ui_chrome.py`): one parametrised test that walks every public route, signs in as appropriate, and asserts the response body contains stable structural markers:
  - `class="topbar"` and `class="brand-mark"` on **every** page (including `/login`).
  - `class="disclaim"` on every signed-in page; **absent on `/login`** (login overrides the `{% block disclaimer %}` to empty, same pattern as the unverified-locale banner).
  - `class="panel"` at least once on every page that renders data.
- **Tokens-present test**: fetch `/static/app.css` via the test client; assert `--ink`, `--accent`, `--bg`, and the four status-color pairs all appear. Guards against accidental deletion during the sweep.
- **Manual sweep** across all 6 templates × 3 locales after each phase that touches a template — picker → page → screenshot mentally.
- **No visual regression / screenshot testing.** Deliberately out of scope for the demo timeline. Flagged as a future addition once the UI stabilises.

## 11. Risks

- **The cropped PNG may not render perfectly transparent.** Pillow's "remove near-white" is heuristic; some droplet outline pixels may end up semi-opaque. *Mitigation:* the cropping script is committed alongside the asset, so it can be re-run with a tweaked threshold; if anti-aliased edge pixels are a real problem, fall back to hand-authored SVG (the deferred option from §5).
- **The brand cyan `#3eb1e8` is bright.** As a focus ring + link colour it works; if it ever lands on a large solid block, it may be visually loud. *Mitigation:* used sparingly (panel underlines 2px, focus rings, links, the SOLUTIONS wordmark) — never as a large surface.
- **Information density may feel cramped to users coming from the current dark theme.** *Mitigation:* spacing tokens are 4/8/12/16/24 — generous compared with most ops consoles; can dial up `--space-3` → `--space-4` per panel padding if pilot feedback reports cramped feel.
- **`extra_style` blocks may resist cleanup.** Some pages have one-off styles whose responsibilities are unclear. *Mitigation:* the phase 8 "sweep" task is explicitly allocated for this; any rule that resists removal stays and is flagged as `/* TODO post-launch */` rather than fought over.
- **The `Cache-Control: no-store` from the i18n work covers HTML.** A user on the demo may need to hard-refresh once at deploy time to pick up the new `app.css` because their cached HTML still references the old inline `<style>`. *Mitigation:* expected and documented; on a fresh load there is no inline style block to compete.
- **The new `feat/ui-upgrade` branch will conflict with any concurrent main-branch work.** None is currently in flight on the templates per the recent commit log, but a long-lived branch carries the usual risk. *Mitigation:* keep branch short (phase-per-commit), merge promptly after the sweep.
