"""The seven individual SEO checks executed by RankPilot.

Each check function receives what it needs (parsed HTML, or site-level
data already fetched by the analyzer) plus a Translator, and returns a
CheckResult. Checks never raise for expected content problems; they
report PASS / FAIL / WARN with localized details.
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
    """Outcome of a single SEO check."""

    check_key: str          # i18n key of the check name (e.g. "check_title")
    status: str             # PASS, FAIL or WARN
    details: str            # localized human-readable details
    counted: bool = True    # False for informational rows (page load)
    http_status: str = ""   # HTTP status of the analyzed page, when relevant
    extra_rows: list = field(default_factory=list)


def _clean_text(value: Optional[str]) -> str:
    return " ".join(value.split()) if value else ""


def check_title(soup: BeautifulSoup, t: Translator) -> CheckResult:
    """Check 1 — the page must have a non-empty <title> tag."""
    title_tag = soup.find("title")
    if title_tag is None:
        return CheckResult("check_title", FAIL, t.t("title_missing"))
    title = _clean_text(title_tag.get_text())
    if not title:
        return CheckResult("check_title", FAIL, t.t("title_empty"))
    return CheckResult("check_title", PASS, t.t("title_ok", value=title))


def check_meta_description(soup: BeautifulSoup, t: Translator) -> CheckResult:
    """Check 2 — the page must have a non-empty meta description."""
    meta = soup.find("meta", attrs={"name": lambda v: v and v.lower() == "description"})
    if meta is None:
        return CheckResult("check_meta", FAIL, t.t("meta_missing"))
    description = _clean_text(meta.get("content"))
    if not description:
        return CheckResult("check_meta", FAIL, t.t("meta_empty"))
    return CheckResult("check_meta", PASS, t.t("meta_ok", value=description))


def check_h1(soup: BeautifulSoup, t: Translator) -> CheckResult:
    """Check 3 — the page must have at least one H1 heading.

    Multiple H1 headings are reported as a warning.
    """
    headings = soup.find_all("h1")
    if not headings:
        return CheckResult("check_h1", FAIL, t.t("h1_missing"))
    first = _clean_text(headings[0].get_text())
    if len(headings) == 1:
        return CheckResult("check_h1", PASS, t.t("h1_ok", value=first))
    return CheckResult("check_h1", WARN, t.t("h1_multiple", count=len(headings), first=first))


def check_images(soup: BeautifulSoup, t: Translator) -> CheckResult:
    """Check 4 — images should carry an alt attribute.

    A missing alt attribute is a failure; an empty alt attribute is only a
    warning because it can be intentional for decorative images.
    """
    images = soup.find_all("img")
    total = len(images)
    if total == 0:
        return CheckResult("check_images", PASS, t.t("images_none"))

    missing = [img for img in images if not img.has_attr("alt")]
    empty = [img for img in images if img.has_attr("alt") and not img["alt"].strip()]

    if not missing and not empty:
        return CheckResult("check_images", PASS, t.t("images_ok", total=total))
    if missing and empty:
        return CheckResult(
            "check_images", FAIL,
            t.t("images_both", missing=len(missing), total=total, empty=len(empty)),
        )
    if missing:
        return CheckResult(
            "check_images", FAIL,
            t.t("images_missing_only", missing=len(missing), total=total),
        )
    return CheckResult(
        "check_images", WARN,
        t.t("images_empty_only", empty=len(empty), total=total),
    )


def check_sitemap(session: requests.Session, url: str, robots_text: Optional[str],
                  t: Translator, timeout: int = DEFAULT_TIMEOUT) -> CheckResult:
    """Check 6 — look for a sitemap declaration in robots.txt, then /sitemap.xml."""
    # 1. Sitemap declarations inside robots.txt
    if robots_text:
        for line in robots_text.splitlines():
            if line.strip().lower().startswith("sitemap:"):
                sitemap_url = line.split(":", 1)[1].strip()
                if sitemap_url and _url_reachable(session, sitemap_url, timeout):
                    return CheckResult("check_sitemap", PASS, t.t("sitemap_robots", url=sitemap_url))

    # 2. Standard location
    default_url = f"{site_origin(url)}/sitemap.xml"
    if _url_reachable(session, default_url, timeout):
        return CheckResult("check_sitemap", PASS, t.t("sitemap_default", url=default_url))

    return CheckResult("check_sitemap", WARN, t.t("sitemap_missing"))


def check_robots(robots_text: Optional[str], url: str, t: Translator) -> CheckResult:
    """Check 7 — the website should expose a robots.txt file at its root."""
    robots_url = f"{site_origin(url)}/robots.txt"
    if robots_text is not None:
        return CheckResult("check_robots", PASS, t.t("robots_ok", url=robots_url))
    return CheckResult("check_robots", WARN, t.t("robots_missing"))


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
