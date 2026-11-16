"""Tests for the individual SEO checks (checks.py)."""

import pytest
from bs4 import BeautifulSoup

from rankpilot import checks
from rankpilot.i18n import FAIL, PASS, WARN, Translator


@pytest.fixture
def translator():
    return Translator("en")


def soup(html):
    return BeautifulSoup(html, "html.parser")


class FakeResponse:
    def __init__(self, status_code):
        self.status_code = status_code

    def close(self):
        pass


class FakeSession:
    """Session stub returning preconfigured statuses per URL."""

    def __init__(self, statuses):
        self.statuses = statuses

    def head(self, url, timeout=None, allow_redirects=True):
        return FakeResponse(self.statuses.get(url, 404))

    def get(self, url, timeout=None, allow_redirects=True, stream=False):
        return FakeResponse(self.statuses.get(url, 404))


# --- Check 1: Page Title -------------------------------------------------

def test_missing_title_is_fail(translator):
    result = checks.check_title(soup("<html><body><p>hi</p></body></html>"), translator)
    assert result.status == FAIL
    assert "No <title>" in result.details


def test_empty_title_is_fail(translator):
    result = checks.check_title(soup("<html><head><title>   </title></head></html>"), translator)
    assert result.status == FAIL


def test_valid_title_is_pass(translator):
    result = checks.check_title(soup("<html><head><title>My Site</title></head></html>"), translator)
    assert result.status == PASS
    assert "My Site" in result.details


# --- Check 2: Meta Description -------------------------------------------

def test_missing_meta_description_is_fail(translator):
    result = checks.check_meta_description(soup("<html><head></head></html>"), translator)
    assert result.status == FAIL


def test_empty_meta_description_is_fail(translator):
    html = '<html><head><meta name="description" content="  "></head></html>'
    result = checks.check_meta_description(soup(html), translator)
    assert result.status == FAIL


def test_valid_meta_description_is_pass(translator):
    html = '<html><head><meta name="description" content="A great site"></head></html>'
    result = checks.check_meta_description(soup(html), translator)
    assert result.status == PASS
    assert "A great site" in result.details


# --- Check 3: H1 Heading ---------------------------------------------------

def test_missing_h1_is_fail(translator):
    result = checks.check_h1(soup("<html><body><h2>Sub</h2></body></html>"), translator)
    assert result.status == FAIL


def test_single_h1_is_pass(translator):
    result = checks.check_h1(soup("<html><body><h1>Welcome</h1></body></html>"), translator)
    assert result.status == PASS
    assert "Welcome" in result.details


def test_multiple_h1_is_warn(translator):
    result = checks.check_h1(soup("<body><h1>One</h1><h1>Two</h1></body>"), translator)
    assert result.status == WARN


# --- Check 4: Image Alt Attributes -----------------------------------------

def test_no_images_is_pass(translator):
    result = checks.check_images(soup("<body><p>text</p></body>"), translator)
    assert result.status == PASS


def test_all_images_with_alt_is_pass(translator):
    result = checks.check_images(soup('<body><img src="a.png" alt="A"></body>'), translator)
    assert result.status == PASS


def test_image_without_alt_is_fail(translator):
    result = checks.check_images(soup('<body><img src="a.png"></body>'), translator)
    assert result.status == FAIL
    assert "no alt attribute" in result.details


def test_image_with_empty_alt_is_warn(translator):
    result = checks.check_images(soup('<body><img src="a.png" alt=""></body>'), translator)
    assert result.status == WARN


def test_missing_and_empty_alt_is_fail(translator):
    html = '<body><img src="a.png"><img src="b.png" alt=""></body>'
    result = checks.check_images(soup(html), translator)
    assert result.status == FAIL
    assert "1" in result.details


# --- Check 6: Sitemap -------------------------------------------------------

def test_sitemap_declared_in_robots_is_pass(translator):
    robots = "User-agent: *\nSitemap: https://example.com/sitemap.xml\n"
    session = FakeSession({"https://example.com/sitemap.xml": 200})
    result = checks.check_sitemap(session, "https://example.com/", robots, translator)
    assert result.status == PASS
    assert "robots.txt" in result.details


def test_sitemap_at_default_location_is_pass(translator):
    session = FakeSession({"https://example.com/sitemap.xml": 200})
    result = checks.check_sitemap(session, "https://example.com/", None, translator)
    assert result.status == PASS


def test_missing_sitemap_is_warn(translator):
    session = FakeSession({})
    result = checks.check_sitemap(session, "https://example.com/", "User-agent: *", translator)
    assert result.status == WARN


# --- Check 7: Robots.txt ----------------------------------------------------

def test_robots_present_is_pass(translator):
    result = checks.check_robots("User-agent: *", "https://example.com/", translator)
    assert result.status == PASS


def test_robots_missing_is_warn(translator):
    result = checks.check_robots(None, "https://example.com/", translator)
    assert result.status == WARN
