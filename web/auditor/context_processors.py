"""Template context: current language and translator."""

from __future__ import annotations

from rankpilot.i18n import SUPPORTED_LANGUAGES

from .translations import LANG_SESSION_KEY, WebTranslator


def i18n(request):
    """Expose the session language and a translator to every template."""
    lang = request.session.get(LANG_SESSION_KEY, "en")
    if lang not in SUPPORTED_LANGUAGES:
        lang = "en"
    translator = WebTranslator(lang)
    return {
        "t": translator,
        "lang": lang,
    }
