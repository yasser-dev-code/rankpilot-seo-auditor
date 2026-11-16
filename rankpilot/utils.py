"""URL validation and HTTP helpers shared across RankPilot."""

from __future__ import annotations

import re
from urllib.parse import urlparse, urlunparse

import requests

USER_AGENT = "RankPilot/1.0 (Website SEO Auditor)"
DEFAULT_TIMEOUT = 10  # seconds
ALLOWED_SCHEMES = {"http", "https"}

_SCHEME_RE = re.compile(r"^[a-zA-Z][a-zA-Z0-9+.-]*://")


class InvalidURLError(ValueError):
    """Raised when a user-provided URL cannot be accepted.

    The message is an i18n key so callers can localize the error.
    """


class FetchError(Exception):
    """Raised when the target page cannot be downloaded."""

    def __init__(self, message_key: str, detail: str = ""):
        super().__init__(detail or message_key)
        self.message_key = message_key
        self.detail = detail


def normalize_url(raw_url: str) -> str:
    """Validate a user-provided URL and return it in absolute form.

    A URL without a scheme is treated as HTTPS. Only http/https are accepted.
    Raises InvalidURLError (with an i18n key as message) otherwise.
    """
    if not raw_url or not raw_url.strip():
        raise InvalidURLError("err_url_empty")
    url = raw_url.strip()
    if not _SCHEME_RE.match(url):
        url = "https://" + url
    parsed = urlparse(url)
    if parsed.scheme.lower() not in ALLOWED_SCHEMES:
        raise InvalidURLError("err_url_scheme")
    host = parsed.hostname
    if not host or ("." not in host and host != "localhost"):
        raise InvalidURLError("err_url_invalid")
    return urlunparse(parsed)


def site_origin(url: str) -> str:
    """Return the origin (scheme + host + port) of an absolute URL."""
    parsed = urlparse(url)
    return f"{parsed.scheme}://{parsed.netloc}"


def make_session() -> requests.Session:
    """Create a requests session identifying RankPilot as the client."""
    session = requests.Session()
    session.headers.update({"User-Agent": USER_AGENT})
    return session


def fetch_page(session: requests.Session, url: str, timeout: int = DEFAULT_TIMEOUT) -> requests.Response:
    """Download a page, following redirects.

    Raises FetchError with an i18n message key on network-level failures.
    """
    try:
        return session.get(url, timeout=timeout, allow_redirects=True)
    except requests.exceptions.SSLError as exc:
        raise FetchError("err_ssl", str(exc)) from exc
    except requests.exceptions.Timeout as exc:
        raise FetchError("err_timeout", str(exc)) from exc
    except requests.exceptions.ConnectionError as exc:
        raise FetchError("err_connection", str(exc)) from exc
    except requests.exceptions.RequestException as exc:
        raise FetchError("err_fetch", str(exc)) from exc
