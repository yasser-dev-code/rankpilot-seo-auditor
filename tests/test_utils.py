"""Tests for URL validation helpers (utils.py)."""

import pytest

from rankpilot.utils import InvalidURLError, normalize_url, site_origin


def test_url_without_scheme_becomes_https():
    assert normalize_url("example.com") == "https://example.com"


def test_url_with_whitespace_is_trimmed():
    assert normalize_url("  https://example.com/path  ") == "https://example.com/path"


def test_http_scheme_is_preserved():
    assert normalize_url("http://example.com") == "http://example.com"


def test_query_and_path_are_preserved():
    url = "https://example.com/search?q=seo&page=2"
    assert normalize_url(url) == url


def test_ftp_scheme_is_rejected():
    with pytest.raises(InvalidURLError) as error:
        normalize_url("ftp://example.com/file")
    assert str(error.value) == "err_url_scheme"


def test_javascript_scheme_is_rejected():
    with pytest.raises(InvalidURLError):
        normalize_url("javascript:alert(1)")


def test_empty_url_is_rejected():
    with pytest.raises(InvalidURLError) as error:
        normalize_url("   ")
    assert str(error.value) == "err_url_empty"


def test_hostless_url_is_rejected():
    with pytest.raises(InvalidURLError) as error:
        normalize_url("https://")
    assert str(error.value) == "err_url_invalid"


def test_hostname_without_dot_is_rejected():
    with pytest.raises(InvalidURLError):
        normalize_url("https://intranet")


def test_localhost_is_accepted():
    assert normalize_url("http://localhost:8000") == "http://localhost:8000"


def test_site_origin():
    assert site_origin("https://example.com/a/b?c=1") == "https://example.com"
