"""Language / i18n integration for the Gen-1 web portal.

Spec: docs/superpowers/specs/2026-05-30-i18n-design.md.

Owns the LANGUAGES allow-list, Babel registration, and the locale-selector.
Views in app.py just use flask_babel.gettext (imported as _) and
never look at the locale themselves.

Locale precedence (highest to lowest):
  1. URL ?lang= parameter
  2. user_preferences.language (signed-in users only)
  3. aqua_lang cookie
  4. Accept-Language header
  5. DEFAULT_LANGUAGE ("en")

Not yet implemented (land in later tasks per the plan):
- unverified_locale() helper for the machine-translation banner — Task 15
"""

from __future__ import annotations

import sys
from urllib.parse import urlparse

from flask import Blueprint, Flask, redirect, request, session
from flask_babel import Babel
from sqlalchemy import text

LANGUAGES: dict[str, str] = {
    "en": "English",
    "sn": "Shona",
    "nd": "isiNdebele",
}

DEFAULT_LANGUAGE = "en"

babel = Babel()


def _validate(code: str | None) -> str | None:
    """Return code if it is a supported language, else None."""
    return code if code in LANGUAGES else None


def _from_user_preferences(username: str) -> str | None:
    """Look up the stored language preference for a signed-in user.

    Returns the language code if it is in LANGUAGES, else None.

    Uses sys.modules["database"] rather than a module-level import so that
    the test suite's per-test re-import of database (which rotates the engine
    to a fresh temp DB) is respected even though language.py itself is not
    re-imported between tests.
    """
    db_mod = sys.modules["database"]
    with db_mod.connection() as conn:
        row = conn.execute(
            text("SELECT language FROM user_preferences WHERE username = :u"),
            {"u": username},
        ).fetchone()
    if row is None:
        return None
    return _validate(row[0])


def select_locale() -> str:
    """Return the locale for the current request.

    Implements five-layer precedence:
      1. URL ?lang= override
      2. Signed-in user's stored preference (user_preferences table)
      3. aqua_lang cookie
      4. Accept-Language header
      5. DEFAULT_LANGUAGE
    """
    # 1. URL override (?lang=)
    override = _validate(request.args.get("lang"))
    if override is not None:
        return override
    # 2. user_preferences.language (signed-in users only)
    username = session.get("username")
    if username is not None:
        pref = _from_user_preferences(username)
        if pref is not None:
            return pref
    # 3. cookie
    cookie = _validate(request.cookies.get("aqua_lang"))
    if cookie is not None:
        return cookie
    # 4. Accept-Language
    best = request.accept_languages.best_match(list(LANGUAGES.keys()))
    if best:
        return best
    # 5. default
    return DEFAULT_LANGUAGE


def current_lang() -> str:
    """Public helper — what locale was chosen for this request?"""
    return select_locale()


COOKIE_NAME = "aqua_lang"
COOKIE_MAX_AGE = 60 * 60 * 24 * 365  # 1 year

lang_bp = Blueprint("lang", __name__)


def _safe_redirect_target() -> str:
    """Return a safe local redirect path from the Referer header, or /dashboard."""
    referrer = request.referrer or ""
    if not referrer:
        return "/dashboard"
    parsed = urlparse(referrer)
    if parsed.netloc and parsed.netloc != request.host:
        return "/dashboard"
    return parsed.path or "/dashboard"


@lang_bp.post("/lang")
def set_lang_view():
    code = _validate(request.form.get("code"))
    if code is None:
        return "Invalid language code.", 400

    response = redirect(_safe_redirect_target(), code=302)
    response.set_cookie(COOKIE_NAME, code, max_age=COOKIE_MAX_AGE, samesite="Lax")

    username = session.get("username")
    if username is not None:
        # Use dynamic lookup so per-test DB rotation is respected
        # (language.py is not re-imported between tests).
        db_mod = sys.modules["database"]
        with db_mod.connection() as conn:
            with conn.begin():
                conn.execute(
                    text(
                        "INSERT INTO user_preferences (username, language) "
                        "VALUES (:u, :c) "
                        "ON CONFLICT (username) DO UPDATE SET language = excluded.language"
                    ),
                    {"u": username, "c": code},
                )
    return response


def init_babel(app: Flask) -> None:
    """Register Babel with the app, plus jinja globals for templates."""
    app.config.setdefault("BABEL_DEFAULT_LOCALE", DEFAULT_LANGUAGE)
    app.config.setdefault("BABEL_TRANSLATION_DIRECTORIES", "translations")
    babel.init_app(app, locale_selector=select_locale)
    app.register_blueprint(lang_bp)
    app.jinja_env.globals["LANGUAGES"] = LANGUAGES
    app.jinja_env.globals["current_lang"] = current_lang

    @app.after_request
    def _stamp_active_locale(response):
        response.headers["X-Active-Locale"] = current_lang()
        return response
