"""The seven individual SEO checks executed by RankPilot.

Each check function receives what it needs (parsed HTML, or site-level
data already fetched by the analyzer) plus a Translator, and returns a
CheckResult. Checks never raise for expected content problems; they
report PASS / FAIL / WARN.

Results store a translation key and parameters instead of a fixed
string, so the same analysis can be rendered in any supported language
(terminal, CSV or web interface).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

import requests
from bs4 import BeautifulSoup

from .i18n import FAIL, PASS, WARN, Translator
from .utils import DEFAULT_TIMEOUT, site_origin


@dataclass
class ExtraRow:
    """An extra CSV row attached to a check (e.g. one broken link)."""

    status: str
    details: str
    related_url: str = ""
    http_status: str = ""
    check_key: Optional[str] = None  # overrides the parent check name in the CSV


@dataclass
class CheckResult:
    """Outcome of a single SEO check.

    ``detail_key`` / ``detail_params`` describe the result in a
    language-neutral way; ``details`` renders them with the translator
    used during the analysis, while ``localized_details`` can render the
    same result in another language.
    """

    check_key: str          # i18n key of the check name (e.g. "check_title")
    status: str             # PASS, FAIL or WARN
    detail_key: str         # i18n key of the explanation
    detail_params: dict = field(default_factory=dict)
    counted: bool = True    # False for informational rows (page load)
    http_status: str = ""   # HTTP status of the analyzed page, when relevant
    truncated: bool = False # link list was capped at ``limit``
    limit: int = 0
    extra_rows: list = field(default_factory=list)
    translator: Optional[Translator] = field(default=None, repr=False, compare=False)

    @property
    def details(self) -> str:
        return self.localized_details(self.translator or Translator())

    def localized_details(self, translator: Translator) -> str:
        text = translator.t(self.detail_key, **self.detail_params)
        if self.truncated:
            text += translator.t("links_truncated", limit=self.limit)
        return text


def _clean_text(value: Optional[str]) -> str:
    return " ".join(value.split()) if value else ""


def check_title(soup: BeautifulSoup, t: Translator) -> CheckResult:
    """Check 1 — the page must have a non-empty <title> tag."""
    title_tag = soup.find("title")
    if title_tag is None:
        return CheckResult("check_title", FAIL, "title_missing", translator=t)
    title = _clean_text(title_tag.get_text())
    if not title:
        return CheckResult("check_title", FAIL, "title_empty", translator=t)
    return CheckResult("check_title", PASS, "title_ok", {"value": title}, translator=t)


def check_meta_description(soup: BeautifulSoup, t: Translator) -> CheckResult:
    """Check 2 — the page must have a non-empty meta description."""
    meta = soup.find("meta", attrs={"name": lambda v: v and v.lower() == "description"})
    if meta is None:
        return CheckResult("check_meta", FAIL, "meta_missing", translator=t)
    description = _clean_text(meta.get("content"))
    if not description:
        return CheckResult("check_meta", FAIL, "meta_empty", translator=t)
    return CheckResult("check_meta", PASS, "meta_ok", {"value": description}, translator=t)


def check_h1(soup: BeautifulSoup, t: Translator) -> CheckResult:
    """Check 3 — the page must have at least one H1 heading.

    Multiple H1 headings are reported as a warning.
    """
    headings = soup.find_all("h1")
    if not headings:
        return CheckResult("check_h1", FAIL, "h1_missing", translator=t)
    first = _clean_text(headings[0].get_text())
    if len(headings) == 1:
        return CheckResult("check_h1", PASS, "h1_ok", {"value": first}, translator=t)
    return CheckResult("check_h1", WARN, "h1_multiple",
                       {"count": len(headings), "first": first}, translator=t)


def check_images(soup: BeautifulSoup, t: Translator) -> CheckResult:
    """Check 4 — images should carry an alt attribute.

    A missing alt attribute is a failure; an empty alt attribute is only a
    warning because it can be intentional for decorative images.
    """
    images = soup.find_all("img")
    total = len(images)
    if total == 0:
        return CheckResult("check_images", PASS, "images_none", translator=t)

    missing = [img for img in images if not img.has_attr("alt")]
    empty = [img for img in images if img.has_attr("alt") and not img["alt"].strip()]

    if not missing and not empty:
        return CheckResult("check_images", PASS, "images_ok", {"total": total}, translator=t)
    if missing and empty:
        return CheckResult("check_images", FAIL, "images_both",
                           {"missing": len(missing), "total": total, "empty": len(empty)},
                           translator=t)
    if missing:
        return CheckResult("check_images", FAIL, "images_missing_only",
                           {"missing": len(missing), "total": total}, translator=t)
    return CheckResult("check_images", WARN, "images_empty_only",
                       {"empty": len(empty), "total": total}, translator=t)


def check_sitemap(session: requests.Session, url: str, robots_text: Optional[str],
                  t: Translator, timeout: int = DEFAULT_TIMEOUT) -> CheckResult:
    """Check 6 — look for a sitemap declaration in robots.txt, then /sitemap.xml."""
    # 1. Sitemap declarations inside robots.txt
    if robots_text:
        for line in robots_text.splitlines():
            if line.strip().lower().startswith("sitemap:"):
                sitemap_url = line.split(":", 1)[1].strip()
                if sitemap_url and _url_reachable(session, sitemap_url, timeout):
                    return CheckResult("check_sitemap", PASS, "sitemap_robots",
                                       {"url": sitemap_url}, translator=t)

    # 2. Standard location
    default_url = f"{site_origin(url)}/sitemap.xml"
    if _url_reachable(session, default_url, timeout):
        return CheckResult("check_sitemap", PASS, "sitemap_default",
                           {"url": default_url}, translator=t)

    return CheckResult("check_sitemap", WARN, "sitemap_missing", translator=t)


def check_robots(robots_text: Optional[str], url: str, t: Translator) -> CheckResult:
    """Check 7 — the website should expose a robots.txt file at its root."""
    robots_url = f"{site_origin(url)}/robots.txt"
    if robots_text is not None:
        return CheckResult("check_robots", PASS, "robots_ok", {"url": robots_url}, translator=t)
    return CheckResult("check_robots", WARN, "robots_missing", translator=t)


def _url_reachable(session: requests.Session, url: str, timeout: int) -> bool:
    """Return True when a URL answers with a success status (HEAD, then GET)."""
    try:
        response = session.head(url, timeout=timeout, allow_redirects=True)
        if response.status_code < 400:
            return True
        response = session.get(url, timeout=timeout, allow_redirects=True, stream=True)
        response.close()
        return response.status_code < 400
    except requests.exceptions.RequestException:
        return False
