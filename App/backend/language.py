"""Language / i18n integration for the Gen-1 web portal.

Spec: docs/superpowers/specs/2026-05-30-i18n-design.md.

Owns the allow-list, the locale-selector callback (DB-first precedence
per spec §6), the POST /lang route, and the unverified_locale() helper.
Views in app.py just use flask_babel.gettext (imported as _) and never
look at the locale themselves.
"""

from __future__ import annotations

from flask import Flask, request
from flask_babel import Babel

LANGUAGES: dict[str, str] = {
    "en": "English",
    "sn": "Shona",
    "nd": "isiNdebele",
}

DEFAULT_LANGUAGE = "en"

babel = Babel()


def select_locale() -> str:
    """Return the locale for the current request. en until Task 5 fills in
    the real precedence layers."""
    return DEFAULT_LANGUAGE


def current_lang() -> str:
    """Public helper — what locale was chosen for this request?"""
    return select_locale()


def init_babel(app: Flask) -> None:
    """Register Babel with the app, plus jinja globals for templates."""
    app.config.setdefault("BABEL_DEFAULT_LOCALE", DEFAULT_LANGUAGE)
    app.config.setdefault("BABEL_TRANSLATION_DIRECTORIES", "translations")
    babel.init_app(app, locale_selector=select_locale)
    app.jinja_env.globals["LANGUAGES"] = LANGUAGES
    app.jinja_env.globals["current_lang"] = current_lang
