"""Audit orchestration: download the page and run all seven SEO checks."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

from bs4 import BeautifulSoup

import requests

from . import checks
from .i18n import PASS, Translator
from .link_checker import check_internal_links, extract_internal_links
from .utils import (DEFAULT_TIMEOUT, FetchError, make_session, fetch_page,
                    site_origin)


@dataclass
class AuditResult:
    """Everything produced by one RankPilot analysis."""

    url: str
    analyzed_at: datetime
    http_status: Optional[int] = None
    results: list = field(default_factory=list)   # list[checks.CheckResult]
    error_key: Optional[str] = None               # i18n key when the audit could not run
    error_detail: str = ""

    @property
    def succeeded(self) -> bool:
        return self.error_key is None


def _fetch_robots_text(session: requests.Session, url: str, timeout: int) -> Optional[str]:
    """Return the body of /robots.txt, or None when it is unavailable."""
    robots_url = f"{site_origin(url)}/robots.txt"
    try:
        response = session.get(robots_url, timeout=timeout, allow_redirects=True)
    except requests.exceptions.RequestException:
        return None
    if response.status_code == 200 and response.text.strip():
        return response.text
    return None


def _links_check(session: requests.Session, soup: BeautifulSoup, url: str,
                 t: Translator, timeout: int) -> checks.CheckResult:
    """Run the internal-links check and attach one CSV row per broken link."""
    links = extract_internal_links(soup, url)
    if not links:
        return checks.CheckResult("check_links", PASS, t.t("links_none"))

    results, truncated = check_internal_links(session, links, timeout)
    broken = [r for r in results if not r.ok]

    details = t.t("links_broken", broken=len(broken), count=len(results)) if broken \
        else t.t("links_ok", count=len(results))
    if truncated:
        details += t.t("links_truncated", limit=len(results))

    status = "FAIL" if broken else PASS
    extra_rows = [
        checks.ExtraRow(status="FAIL",
                        details=t.t("link_broken_item", url=r.url, status=r.status),
                        related_url=r.url,
                        http_status=r.status,
                        check_key="csv_broken_link")
        for r in broken
    ]
    return checks.CheckResult("check_links", status, details, extra_rows=extra_rows)


def analyze(url: str, translator: Translator,
            session: Optional[requests.Session] = None,
            timeout: int = DEFAULT_TIMEOUT) -> AuditResult:
    """Analyze one page and return the full audit result.

    Network and HTTP failures never raise: they are reported through
    ``AuditResult.error_key`` so the CLI can display a localized message.
    """
    session = session or make_session()
    audit = AuditResult(url=url, analyzed_at=datetime.now())

    try:
        response = fetch_page(session, url, timeout)
    except FetchError as exc:
        audit.error_key = exc.message_key
        audit.error_detail = exc.detail
        return audit

    audit.http_status = response.status_code
    if response.status_code >= 400:
        audit.error_key = "err_http_status"
        audit.error_detail = str(response.status_code)
        return audit

    # Informational (non-counted) row about the page download itself.
    audit.results.append(checks.CheckResult(
        "check_page", PASS,
        translator.t("page_ok", status=response.status_code),
        counted=False,
        http_status=str(response.status_code),
    ))

    soup = BeautifulSoup(response.text, "html.parser")
    robots_text = _fetch_robots_text(session, url, timeout)

    audit.results.append(checks.check_title(soup, translator))
    audit.results.append(checks.check_meta_description(soup, translator))
    audit.results.append(checks.check_h1(soup, translator))
    audit.results.append(checks.check_images(soup, translator))
    audit.results.append(_links_check(session, soup, url, translator, timeout))
    audit.results.append(checks.check_sitemap(session, url, robots_text, translator, timeout))
    audit.results.append(checks.check_robots(robots_text, url, translator))
    return audit
