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
