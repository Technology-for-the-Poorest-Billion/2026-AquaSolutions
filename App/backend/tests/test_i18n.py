"""Tests for the language / i18n integration."""

from __future__ import annotations

from pathlib import Path

from language import LANGUAGES, current_lang


def test_languages_dict_shape():
    assert LANGUAGES == {
        "en": "English",
        "sn": "Shona",
        "nd": "isiNdebele",
    }


def test_default_locale_is_english(client):
    """A bare GET with no cookie, no session, no Accept-Language picks en."""
    resp = client.get("/login")
    assert resp.status_code == 200
    # current_lang() must be callable from a request context;
    # for now we just verify the page rendered without an i18n error.
    assert b"Sign in" in resp.data


def test_current_lang_in_request_context(app):
    """current_lang() is callable inside any request context and returns en by default."""
    with app.test_request_context("/"):
        assert current_lang() == "en"


from sqlalchemy import text as sql_text


def _set_user_pref(username: str, language: str) -> None:
    # Import connection at call time so we always get the live module that
    # the current test's `app` fixture loaded (conftest re-imports database
    # per test; a module-level import would capture a stale reference).
    import sys
    db_mod = sys.modules["database"]
    with db_mod.connection() as conn:
        with conn.begin():
            conn.execute(
                sql_text(
                    "INSERT INTO user_preferences (username, language) "
                    "VALUES (:u, :c) "
                    "ON CONFLICT (username) DO UPDATE SET language = excluded.language"
                ),
                {"u": username, "c": language},
            )


def test_url_override_wins_over_everything(med_session):
    """?lang=en beats DB=sn, cookie=nd."""
    _set_user_pref("dr.smith", "sn")
    med_session.set_cookie("aqua_lang", "nd")
    # Hit a page; the response body itself doesn't tell us the locale,
    # so we use a debug header that we'll add to language.py.
    resp = med_session.get("/medical/report?lang=en")
    assert resp.headers.get("X-Active-Locale") == "en"


def test_db_wins_over_cookie_and_accept_language(med_session):
    _set_user_pref("dr.smith", "sn")
    med_session.set_cookie("aqua_lang", "nd")
    resp = med_session.get(
        "/medical/report",
        headers={"Accept-Language": "en"},
    )
    assert resp.headers.get("X-Active-Locale") == "sn"


def test_cookie_wins_when_anonymous(client):
    """No session, no DB row — cookie is what matters."""
    client.set_cookie("aqua_lang", "nd")
    resp = client.get("/login", headers={"Accept-Language": "en"})
    assert resp.headers.get("X-Active-Locale") == "nd"


def test_accept_language_falls_through_when_no_cookie(client):
    resp = client.get("/login", headers={"Accept-Language": "sn,en;q=0.5"})
    assert resp.headers.get("X-Active-Locale") == "sn"


def test_invalid_url_override_is_ignored(client):
    resp = client.get("/login?lang=zz")
    assert resp.headers.get("X-Active-Locale") == "en"


def test_invalid_db_value_is_ignored(med_session):
    """Defensive: if user_preferences somehow has 'zz', fall through to cookie."""
    _set_user_pref("dr.smith", "zz")
    med_session.set_cookie("aqua_lang", "nd")
    resp = med_session.get("/medical/report")
    assert resp.headers.get("X-Active-Locale") == "nd"


# ---------------------------------------------------------------------------
# Task 5: POST /lang route
# ---------------------------------------------------------------------------

def _db_connection():
    """Return the live database connection (dynamic lookup for test-isolation)."""
    import sys
    return sys.modules["database"].connection()


def test_post_lang_sets_cookie_and_redirects(client):
    resp = client.post("/lang", data={"code": "sn"})
    assert resp.status_code == 302
    assert resp.location.endswith("/dashboard")
    # Werkzeug 3.x: cookie is on the test-client jar after the response.
    assert client.get_cookie("aqua_lang").value == "sn"


def test_post_lang_rejects_invalid_code(client):
    resp = client.post("/lang", data={"code": "zz"})
    assert resp.status_code == 400


def test_post_lang_rejects_missing_code(client):
    resp = client.post("/lang", data={})
    assert resp.status_code == 400


def test_post_lang_upserts_user_preferences_when_signed_in(med_session):
    resp = med_session.post("/lang", data={"code": "sn"})
    assert resp.status_code == 302
    with _db_connection() as conn:
        row = conn.execute(
            sql_text("SELECT language FROM user_preferences WHERE username='dr.smith'")
        ).fetchone()
    assert row is not None and row[0] == "sn"

    # Second submission upserts (no duplicate row).
    med_session.post("/lang", data={"code": "nd"})
    with _db_connection() as conn:
        rows = conn.execute(sql_text("SELECT * FROM user_preferences")).fetchall()
    assert len(rows) == 1
    assert rows[0][1] == "nd"


def test_post_lang_no_db_write_when_anonymous(client):
    client.post("/lang", data={"code": "sn"})
    with _db_connection() as conn:
        rows = conn.execute(sql_text("SELECT * FROM user_preferences")).fetchall()
    assert rows == []


def test_post_lang_redirects_to_safe_referrer(med_session):
    resp = med_session.post(
        "/lang",
        data={"code": "sn"},
        headers={"Referer": "http://localhost/medical/history"},
    )
    assert resp.status_code == 302
    assert resp.location.endswith("/medical/history")


def test_post_lang_ignores_external_referrer(med_session):
    resp = med_session.post(
        "/lang",
        data={"code": "sn"},
        headers={"Referer": "https://evil.example.com/x"},
    )
    assert resp.status_code == 302
    assert resp.location.endswith("/dashboard")


def test_login_page_strings_are_extractable(client):
    """The login button's text must be wrapped in _() so it appears in messages.pot."""
    resp = client.get("/login")
    # We still expect English text in the rendered page (no translations yet).
    assert b"Sign in" in resp.data


def test_estimator_rationale_is_wrapped(app):
    """The rationale string emitted by estimate_risk_tier passes through gettext.
    With only an English catalog the output is unchanged; the test asserts that
    no exception is raised under a request context (i.e. _() resolves)."""
    from estimator import estimate_risk_tier
    from datetime import date
    with app.test_request_context("/"):
        tier, rationale = estimate_risk_tier(
            symptoms=["diarrhoea", "vomiting", "fever"],
            onset_date=None,
            case_count=1,
        )
    assert tier == "high"
    assert isinstance(rationale, str)
    assert rationale  # non-empty


def test_unverified_locale_false_for_english(app):
    from language import unverified_locale
    with app.test_request_context("/"):
        assert unverified_locale("en") is False


def test_unverified_locale_true_for_fuzzy_shona(app):
    """sn was machine-translated and committed with #, fuzzy markers."""
    from language import unverified_locale
    with app.test_request_context("/"):
        assert unverified_locale("sn") is True


def test_unverified_locale_false_for_nonexistent_catalog(app):
    from language import unverified_locale
    with app.test_request_context("/"):
        # 'zz' isn't even an allowed code, but the helper must not raise.
        assert unverified_locale("zz") is False


def test_banner_renders_when_locale_is_unverified(med_session):
    """The yellow banner appears on every page when sn is active."""
    resp = med_session.get("/medical/report?lang=sn")
    # The banner copy is wrapped in _(); search for a stable class.
    assert b'class="unverified-banner"' in resp.data


def test_banner_does_not_render_for_english(med_session):
    resp = med_session.get("/medical/report?lang=en")
    assert b'class="unverified-banner"' not in resp.data


def test_messages_pot_contains_login_button(tmp_path):
    """After running pybabel extract, the catalog must contain known strings."""
    import subprocess
    import shutil
    backend = tmp_path / "backend"
    src = str(Path(__file__).resolve().parent.parent)  # App/backend
    shutil.copytree(src, backend, ignore=shutil.ignore_patterns("__pycache__", ".pytest_cache", "*.db", "*.db-*", "*.mo"))
    result = subprocess.run(
        ["pybabel", "extract", "-F", "babel.cfg", "-o", "translations/messages.pot", "."],
        cwd=backend,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    pot = (backend / "translations" / "messages.pot").read_text()
    assert 'msgid "Sign in"' in pot
    assert 'msgid "Username"' in pot
    assert 'msgid "Password"' in pot
