"""End-to-end tests of the analyzer with fully mocked HTTP traffic."""

import pytest
import requests

from rankpilot.analyzer import analyze
from rankpilot.i18n import FAIL, PASS, WARN, Translator

PAGE_URL = "https://example.com/"
ROBOTS_URL = "https://example.com/robots.txt"
SITEMAP_URL = "https://example.com/sitemap.xml"

PAGE_HTML = """
<html>
<head><title>Test Page</title></head>
<body>
  <h1>Welcome to RankPilot tests</h1>
  <img src="logo.png">
  <a href="/good">Good link</a>
  <a href="https://example.com/bad">Bad link</a>
  <a href="mailto:hi@example.com">Mail</a>
  <a href="https://other-site.com/">External</a>
</body>
</html>
"""

ROBOTS_TEXT = "User-agent: *\nSitemap: https://example.com/sitemap.xml\n"


class FakeResponse:
    def __init__(self, status_code=200, text=""):
        self.status_code = status_code
        self.text = text

    def close(self):
        pass


class FakeSession:
    """Routes requests by URL; anything unrouted returns 404."""

    headers = {}

    def __init__(self, routes):
        self.routes = routes

    def _resolve(self, url):
        entry = self.routes.get(url, FakeResponse(404))
        if isinstance(entry, Exception):
            raise entry
        return entry

    def get(self, url, timeout=None, allow_redirects=True, stream=False):
        return self._resolve(url)

    def head(self, url, timeout=None, allow_redirects=True):
        return self._resolve(url)


def healthy_session():
    return FakeSession({
        PAGE_URL: FakeResponse(200, PAGE_HTML),
        ROBOTS_URL: FakeResponse(200, ROBOTS_TEXT),
        SITEMAP_URL: FakeResponse(200, "<urlset></urlset>"),
        "https://example.com/good": FakeResponse(200),
        "https://example.com/bad": FakeResponse(404),
    })


def test_full_audit_runs_all_seven_checks():
    audit = analyze(PAGE_URL, Translator("en"), session=healthy_session())
    assert audit.succeeded
    assert audit.http_status == 200

    by_key = {r.check_key: r for r in audit.results}
    assert by_key["check_page"].counted is False          # informational row
    assert by_key["check_title"].status == PASS
    assert by_key["check_meta"].status == FAIL            # no meta description
    assert by_key["check_h1"].status == PASS
    assert by_key["check_images"].status == FAIL          # <img> without alt
    assert by_key["check_links"].status == FAIL           # one broken link
    assert by_key["check_sitemap"].status == PASS
    assert by_key["check_robots"].status == PASS

    counted = [r for r in audit.results if r.counted]
    assert len(counted) == 7


def test_broken_links_are_recorded_as_csv_rows():
    audit = analyze(PAGE_URL, Translator("en"), session=healthy_session())
    links_result = next(r for r in audit.results if r.check_key == "check_links")
    assert len(links_result.extra_rows) == 1
    row = links_result.extra_rows[0]
    assert row.related_url == "https://example.com/bad"
    assert row.http_status == "404"
    assert row.check_key == "csv_broken_link"


def test_connection_error_is_reported_not_raised():
    session = FakeSession({PAGE_URL: requests.exceptions.ConnectionError("down")})
    audit = analyze(PAGE_URL, Translator("en"), session=session)
    assert not audit.succeeded
    assert audit.error_key == "err_connection"


def test_timeout_is_reported_not_raised():
    session = FakeSession({PAGE_URL: requests.exceptions.Timeout("slow")})
    audit = analyze(PAGE_URL, Translator("en"), session=session)
    assert not audit.succeeded
    assert audit.error_key == "err_timeout"


def test_http_error_status_aborts_analysis():
    session = FakeSession({PAGE_URL: FakeResponse(500, "boom")})
    audit = analyze(PAGE_URL, Translator("en"), session=session)
    assert not audit.succeeded
    assert audit.error_key == "err_http_status"
    assert audit.http_status == 500


def test_missing_sitemap_and_robots_produce_warnings():
    session = FakeSession({
        PAGE_URL: FakeResponse(200, "<html><head><title>T</title></head>"
                                    "<body><h1>H</h1></body></html>"),
    })
    audit = analyze(PAGE_URL, Translator("en"), session=session)
    by_key = {r.check_key: r for r in audit.results}
    assert by_key["check_sitemap"].status == WARN
    assert by_key["check_robots"].status == WARN


def test_malformed_html_does_not_crash():
    broken_html = "<html><head><title>Broken<h1>Mixed<img src=x></body>"
    session = FakeSession({PAGE_URL: FakeResponse(200, broken_html)})
    audit = analyze(PAGE_URL, Translator("en"), session=session)
    assert audit.succeeded
    assert len([r for r in audit.results if r.counted]) == 7


# --- Bilingual output ---------------------------------------------------------

def test_french_analysis_produces_french_details():
    audit = analyze(PAGE_URL, Translator("fr"), session=healthy_session())
    by_key = {r.check_key: r for r in audit.results}
    assert "Aucune méta-description" in by_key["check_meta"].details
    assert "cassé" in by_key["check_links"].details
    assert "robots.txt trouvé" in by_key["check_robots"].details


def test_english_and_french_status_labels_differ():
    english, french = Translator("en"), Translator("fr")
    assert english.status_label(PASS) == "PASS"
    assert french.status_label(PASS) == "RÉUSSI"
    assert english.status_label(FAIL) == "FAIL"
    assert french.status_label(FAIL) == "ÉCHEC"
    assert english.status_label(WARN) == "WARN"
    assert french.status_label(WARN) == "ALERTE"


def test_cli_renders_french_terminal_output(tmp_path, capsys, monkeypatch):
    """Running main() with --lang fr prints a fully French report."""
    import main as cli

    monkeypatch.setattr(cli, "analyze",
                        lambda url, t, timeout: analyze(PAGE_URL, t, session=healthy_session()))
    exit_code = cli.main(["--url", "example.com", "--lang", "fr",
                          "--reports-dir", str(tmp_path)])
    output = capsys.readouterr().out

    assert exit_code == 0
    assert "RANKPILOT — AUDITEUR SEO DE SITES WEB" in output
    assert "RÉSULTATS DE L'ANALYSE SEO" in output
    assert "RÉSUMÉ" in output
    assert "RÉUSSI" in output and "ÉCHEC" in output
    assert "Problèmes détectés" in output
    assert "Rapport CSV" in output


def test_cli_renders_english_terminal_output(tmp_path, capsys, monkeypatch):
    import main as cli

    monkeypatch.setattr(cli, "analyze",
                        lambda url, t, timeout: analyze(PAGE_URL, t, session=healthy_session()))
    exit_code = cli.main(["--url", "https://example.com", "--lang", "en",
                          "--reports-dir", str(tmp_path)])
    output = capsys.readouterr().out

    assert exit_code == 0
    assert "RANKPILOT — WEBSITE SEO AUDITOR" in output
    assert "SEO ANALYSIS RESULTS" in output
    assert "SUMMARY" in output
    assert "Checks Passed" in output


def test_cli_rejects_invalid_url(capsys):
    import main as cli

    exit_code = cli.main(["--url", "ftp://example.com"])
    assert exit_code == 2
    assert "only http" in capsys.readouterr().err


def test_cli_help_is_localized_in_french(capsys):
    import main as cli

    with pytest.raises(SystemExit) as exit_info:
        cli.main(["--help", "--lang", "fr"])
    output = capsys.readouterr().out

    assert exit_info.value.code == 0
    assert "usage :" in output
    assert "options :" in output
    assert "affiche ce message d'aide et quitte" in output
    assert "URL du site web à analyser" in output
