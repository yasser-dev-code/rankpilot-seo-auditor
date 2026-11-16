"""Tests for internal link extraction and broken-link detection."""

import pytest
import requests
from bs4 import BeautifulSoup

from rankpilot.link_checker import (check_internal_links, check_link,
                                    extract_internal_links)

BASE = "https://example.com/page/"


class FakeResponse:
    def __init__(self, status_code):
        self.status_code = status_code

    def close(self):
        pass


class FakeSession:
    """Session stub with per-URL HEAD/GET behavior."""

    def __init__(self, head_statuses=None, get_statuses=None, head_exception=None):
        self.head_statuses = head_statuses or {}
        self.get_statuses = get_statuses or {}
        self.head_exception = head_exception

    def head(self, url, timeout=None, allow_redirects=True):
        if self.head_exception:
            raise self.head_exception
        return FakeResponse(self.head_statuses.get(url, 404))

    def get(self, url, timeout=None, allow_redirects=True, stream=False):
        return FakeResponse(self.get_statuses.get(url, 404))


def soup(html):
    return BeautifulSoup(html, "html.parser")


# --- Internal link identification ------------------------------------------

def test_identifies_internal_links_and_resolves_relative_urls():
    html = """
    <body>
      <a href="/about">About</a>
      <a href="contact.html">Contact</a>
      <a href="https://example.com/pricing">Pricing</a>
    </body>
    """
    links = extract_internal_links(soup(html), BASE)
    assert links == [
        "https://example.com/about",
        "https://example.com/page/contact.html",
        "https://example.com/pricing",
    ]


def test_ignores_external_and_non_http_links():
    html = """
    <body>
      <a href="https://other.com/x">External</a>
      <a href="mailto:hi@example.com">Mail</a>
      <a href="tel:+123">Tel</a>
      <a href="javascript:void(0)">JS</a>
      <a href="data:text/plain,hi">Data</a>
      <a href="#section">Fragment only</a>
      <a href="/real#section">Real with fragment</a>
    </body>
    """
    links = extract_internal_links(soup(html), BASE)
    assert links == ["https://example.com/real"]


def test_removes_duplicates():
    html = '<a href="/a">A</a><a href="/a">A again</a><a href="/a#frag">A frag</a>'
    links = extract_internal_links(soup(html), BASE)
    assert links == ["https://example.com/a"]


# --- Broken link detection ---------------------------------------------------

def test_healthy_link_head_200():
    session = FakeSession(head_statuses={"https://example.com/ok": 200})
    result = check_link(session, "https://example.com/ok", timeout=5)
    assert result.ok is True
    assert result.status == "200"


def test_broken_link_404():
    session = FakeSession(head_statuses={"https://example.com/gone": 404},
                          get_statuses={"https://example.com/gone": 404})
    result = check_link(session, "https://example.com/gone", timeout=5)
    assert result.ok is False
    assert result.status == "404"


def test_get_fallback_when_head_rejected():
    # Server answers 405 to HEAD but 200 to GET: the link is not broken.
    session = FakeSession(head_statuses={"https://example.com/no-head": 405},
                          get_statuses={"https://example.com/no-head": 200})
    result = check_link(session, "https://example.com/no-head", timeout=5)
    assert result.ok is True
    assert result.status == "200"


def test_connection_error_marks_link_broken():
    session = FakeSession(head_exception=requests.exceptions.ConnectionError("boom"))
    result = check_link(session, "https://example.com/down", timeout=5)
    assert result.ok is False
    assert result.status == "ConnectionError"


def test_check_internal_links_reports_all_results():
    session = FakeSession(
        head_statuses={"https://example.com/a": 200, "https://example.com/b": 404},
        get_statuses={"https://example.com/b": 404},
    )
    results, truncated = check_internal_links(
        session, ["https://example.com/a", "https://example.com/b"], timeout=5)
    assert truncated is False
    assert [(r.url, r.ok) for r in results] == [
        ("https://example.com/a", True),
        ("https://example.com/b", False),
    ]


def test_check_internal_links_respects_limit():
    session = FakeSession(head_statuses={})
    urls = [f"https://example.com/p{i}" for i in range(10)]
    results, truncated = check_internal_links(session, urls, timeout=5, limit=4)
    assert truncated is True
    assert len(results) == 4
