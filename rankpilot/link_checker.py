"""Check 5 — extraction and HTTP verification of internal links.

Links are extracted from the analyzed page only; RankPilot never crawls
other pages recursively. Duplicate URLs are checked once, non-HTTP
schemes (mailto, tel, javascript, data, ...) are ignored, fragments are
removed, and relative URLs are resolved against the page URL.
"""

from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import urljoin, urlparse, urlunparse

import requests
from bs4 import BeautifulSoup

MAX_LINKS_CHECKED = 25  # keeps the audit fast and polite to the target site


@dataclass
class LinkCheckResult:
    """HTTP verification outcome for a single internal link."""

    url: str
    ok: bool
    status: str  # HTTP status code as text, or a short error label


def extract_internal_links(soup: BeautifulSoup, base_url: str) -> list[str]:
    """Return the unique internal http/https links found on the page.

    Internal means same scheme + host + port as ``base_url``. Fragments are
    removed and non-HTTP schemes are ignored.
    """
    base_parsed = urlparse(base_url)
    base_netloc = base_parsed.netloc.lower()

    seen: set[str] = set()
    links: list[str] = []
    for anchor in soup.find_all("a", href=True):
        href = anchor["href"].strip()
        if not href or href.startswith("#"):
            continue
        absolute = urljoin(base_url, href)
        parsed = urlparse(absolute)
        if parsed.scheme.lower() not in ("http", "https"):
            continue  # ignores mailto:, tel:, javascript:, data:, ftp:, ...
        if parsed.netloc.lower() != base_netloc:
            continue  # external link
        without_fragment = urlunparse(parsed._replace(fragment=""))
        if without_fragment in seen:
            continue
        seen.add(without_fragment)
        links.append(without_fragment)
    return links


def check_link(session: requests.Session, url: str, timeout: int) -> LinkCheckResult:
    """Check one URL with HEAD, falling back to GET when HEAD is rejected."""
    try:
        response = session.head(url, timeout=timeout, allow_redirects=True)
        if response.status_code >= 400:
            # Some servers answer HEAD incorrectly (404/405/501): retry with GET.
            response = session.get(url, timeout=timeout, allow_redirects=True, stream=True)
            response.close()
        return LinkCheckResult(url, response.status_code < 400, str(response.status_code))
    except requests.exceptions.RequestException as exc:
        return LinkCheckResult(url, False, type(exc).__name__)


def check_internal_links(session: requests.Session, links: list[str], timeout: int,
                         limit: int = MAX_LINKS_CHECKED) -> tuple[list[LinkCheckResult], bool]:
    """Verify up to ``limit`` unique links. Returns (results, was_truncated)."""
    truncated = len(links) > limit
    results = [check_link(session, url, timeout) for url in links[:limit]]
    return results, truncated
