"""Tests for the language / i18n integration."""

from __future__ import annotations

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
