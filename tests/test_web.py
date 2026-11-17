"""Django integration tests for the RankPilot web application.

External HTTP traffic is never performed: the engine call is replaced by
a prepared AuditResult, and SSRF tests use literal / mocked DNS answers.
"""

import re
from datetime import datetime

import pytest
import requests
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.test import Client
from django.urls import reverse

from auditor import security, services
from auditor.models import Analysis
from rankpilot.analyzer import AuditResult
from rankpilot.checks import CheckResult, ExtraRow
from rankpilot.i18n import Translator
from rankpilot.utils import FetchError

pytestmark = pytest.mark.django_db


def make_audit(url="https://example.com"):
    t = Translator("en")
    audit = AuditResult(url=url, analyzed_at=datetime(2026, 11, 16, 23, 5, 12),
                        http_status=200)
    audit.results = [
        CheckResult("check_page", "PASS", "page_ok", {"status": 200},
                    counted=False, http_status="200", translator=t),
        CheckResult("check_title", "PASS", "title_ok", {"value": "Example"}, translator=t),
        CheckResult("check_meta", "FAIL", "meta_missing", translator=t),
        CheckResult("check_h1", "PASS", "h1_ok", {"value": "Welcome"}, translator=t),
        CheckResult("check_images", "WARN", "images_empty_only",
                    {"empty": 1, "total": 2}, translator=t),
        CheckResult("check_links", "FAIL", "links_broken", {"broken": 1, "count": 2},
                    extra_rows=[ExtraRow(status="FAIL",
                                         details="https://example.com/gone -> 404",
                                         related_url="https://example.com/gone",
                                         http_status="404",
                                         check_key="csv_broken_link")],
                    translator=t),
        CheckResult("check_sitemap", "PASS", "sitemap_default",
                    {"url": "https://example.com/sitemap.xml"}, translator=t),
        CheckResult("check_robots", "PASS", "robots_ok",
                    {"url": "https://example.com/robots.txt"}, translator=t),
    ]
    return audit


@pytest.fixture
def mock_engine(monkeypatch):
    """Replace the engine call and DNS validation for happy-path tests."""
    monkeypatch.setattr(services, "analyze",
                        lambda url, translator, session=None: make_audit(url))
    monkeypatch.setattr(services, "assert_public_url", lambda url: None)


def submit(client, url):
    return client.post(reverse("analyzer"), {"url": url})


# --- Pages -------------------------------------------------------------------

def test_dashboard_loads_with_empty_state(client):
    response = client.get(reverse("dashboard"))
    assert response.status_code == 200
    assert b"No analyses yet" in response.content


def test_analyzer_page_loads(client):
    response = client.get(reverse("analyzer"))
    assert response.status_code == 200
    assert b'name="url"' in response.content
    assert b"csrfmiddlewaretoken" in response.content


def test_reports_page_loads_with_empty_state(client):
    response = client.get(reverse("reports"))
    assert response.status_code == 200
    assert b"No reports yet" in response.content


def test_about_page_loads(client):
    response = client.get(reverse("about"))
    assert response.status_code == 200


# --- Analysis submission -------------------------------------------------------

def test_successful_analysis_submission(client, mock_engine):
    response = submit(client, "https://example.com")
    assert response.status_code == 302

    analysis = Analysis.objects.get()
    assert analysis.url == "https://example.com"
    assert analysis.succeeded
    assert analysis.score == 64  # 4 PASS + 1 WARN + 2 FAIL over 7 checks
    assert analysis.passed == 4 and analysis.failed == 2 and analysis.warnings == 1
    assert analysis.broken_links == [{"url": "https://example.com/gone", "status": "404"}]
    assert analysis.page_title == "Example"

    results = client.get(response["Location"])
    assert results.status_code == 200
    assert b"Example" in results.content
    assert b"64" in results.content
    assert b"https://example.com/gone" in results.content


def test_invalid_url_is_rejected_without_analysis(client):
    response = submit(client, "ftp://example.com/file")
    assert response.status_code == 302
    assert response["Location"] == reverse("analyzer")
    assert Analysis.objects.count() == 0

    follow = client.get(reverse("analyzer"))
    assert b"only http" in follow.content


def test_ssrf_loopback_address_is_blocked(client):
    response = submit(client, "http://127.0.0.1:8000/admin")
    assert response.status_code == 302
    assert Analysis.objects.count() == 0
    follow = client.get(reverse("analyzer"))
    assert b"private, local or reserved" in follow.content


def test_ssrf_private_network_address_is_blocked(client):
    assert submit(client, "http://192.168.0.10/").status_code == 302
    assert submit(client, "http://169.254.169.254/latest/meta-data/").status_code == 302
    assert submit(client, "http://10.0.0.5/").status_code == 302
    assert Analysis.objects.count() == 0


def test_ssrf_blocks_dns_resolving_to_private_address(monkeypatch):
    def fake_getaddrinfo(host, port, proto=None):
        import socket
        return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("192.168.1.50", port))]

    monkeypatch.setattr(security.socket, "getaddrinfo", fake_getaddrinfo)
    with pytest.raises(security.SSRFError):
        security.assert_public_url("https://example.com/")


def test_session_validates_every_request_before_connecting():
    session = security.SSRFSafeSession()
    request = requests.Request("GET", "http://127.0.0.1/secret").prepare()
    with pytest.raises(security.SSRFError):
        session.send(request)


def test_response_size_limit_is_enforced():
    class HugeResponse:
        def iter_content(self, chunk_size=1):
            for _ in range(10):
                yield b"x" * (1024 * 1024)

        def close(self):
            pass

    with pytest.raises(security.SSRFError):
        security.SSRFSafeSession._enforce_size_limit(HugeResponse())


def test_network_error_shows_message_and_stores_nothing(client, monkeypatch):
    def boom(url, translator, session=None):
        raise FetchError("err_timeout")

    monkeypatch.setattr(services, "analyze", boom)
    monkeypatch.setattr(services, "assert_public_url", lambda url: None)

    response = submit(client, "https://example.com")
    assert response.status_code == 302
    assert Analysis.objects.count() == 0
    follow = client.get(reverse("analyzer"))
    assert b"did not respond in time" in follow.content


def test_http_error_status_is_stored_as_failed_analysis(client, monkeypatch):
    def failed_audit(url, translator, session=None):
        return AuditResult(url=url, analyzed_at=datetime(2026, 1, 1),
                           http_status=404, error_key="err_http_status",
                           error_detail="404")

    monkeypatch.setattr(services, "analyze", failed_audit)
    monkeypatch.setattr(services, "assert_public_url", lambda url: None)

    response = submit(client, "https://example.com/missing")
    analysis = Analysis.objects.get()
    assert analysis.status == Analysis.STATUS_ERROR

    page = client.get(response["Location"])
    assert page.status_code == 200
    assert b"could not be completed" in page.content


# --- Results, reports, CSV -------------------------------------------------------

def test_results_page_renders_in_both_languages(client, mock_engine):
    submit(client, "https://example.com")
    analysis = Analysis.objects.get()

    english = client.get(reverse("results", kwargs={"pk": analysis.pk}))
    assert b"Meta Description" in english.content
    assert b"No meta description found." in english.content

    client.get(reverse("set_language"), {"lang": "fr", "next": "/"})
    french = client.get(reverse("results", kwargs={"pk": analysis.pk}))
    assert "Méta-description".encode() in french.content
    assert "Aucune méta-description trouvée.".encode() in french.content
    assert "ÉCHEC".encode() in french.content


def test_score_calculation():
    assert services.compute_score(make_audit().results) == 64
    assert services.compute_score([]) is None


def test_analysis_history_persists_across_clients(mock_engine):
    submit(Client(), "https://example.com")
    fresh = Client()
    response = fresh.get(reverse("reports"))
    assert b"example.com" in response.content


def test_reports_pagination(client, mock_engine):
    for _ in range(12):
        submit(client, "https://example.com")
    assert Analysis.objects.count() == 12

    first = client.get(reverse("reports"))
    assert len(first.context["page"].object_list) == 10
    second = client.get(reverse("reports"), {"page": 2})
    assert len(second.context["page"].object_list) == 2


def test_csv_download_contains_rows_and_bom(client, mock_engine):
    submit(client, "https://example.com")
    analysis = Analysis.objects.get()

    response = client.get(reverse("report_csv", kwargs={"pk": analysis.pk}))
    assert response.status_code == 200
    assert response["Content-Type"].startswith("text/csv")
    raw = b"".join(response.streaming_content) if response.streaming else response.content
    assert raw.startswith(b"\xef\xbb\xbf")
    assert b"Page Title" in raw
    assert b"Broken Internal Link" in raw
    assert b"https://example.com/gone" in raw


def test_csv_download_in_french(client, mock_engine):
    submit(client, "https://example.com")
    analysis = Analysis.objects.get()
    client.get(reverse("set_language"), {"lang": "fr", "next": "/"})

    response = client.get(reverse("report_csv", kwargs={"pk": analysis.pk}))
    raw = response.content
    assert "Titre de la page".encode() in raw
    assert "Lien interne cassé".encode() in raw


def test_csv_download_for_failed_analysis_is_404(client, monkeypatch):
    def failed_audit(url, translator, session=None):
        return AuditResult(url=url, analyzed_at=datetime(2026, 1, 1),
                           http_status=500, error_key="err_http_status")

    monkeypatch.setattr(services, "analyze", failed_audit)
    monkeypatch.setattr(services, "assert_public_url", lambda url: None)
    submit(client, "https://example.com")

    response = client.get(reverse("report_csv", kwargs={"pk": Analysis.objects.get().pk}))
    assert response.status_code == 404


# --- Language switching & security behavior ----------------------------------------

def test_language_switch_persists_for_session(client):
    response = client.get(reverse("set_language"), {"lang": "fr", "next": "/analyze/"})
    assert response.status_code == 302

    page = client.get(reverse("analyzer"))
    assert "Analyser un site web".encode() in page.content
    assert client.session["rankpilot_lang"] == "fr"


def test_language_switch_ignores_unknown_language(client):
    client.get(reverse("set_language"), {"lang": "de", "next": "/"})
    assert client.session["rankpilot_lang"] == "en"


def test_language_switch_rejects_open_redirect(client):
    response = client.get(reverse("set_language"),
                          {"lang": "fr", "next": "https://evil.example.com/"})
    assert response["Location"] == reverse("dashboard")


def test_csrf_protection_is_enforced():
    client = Client(enforce_csrf_checks=True)
    response = client.post(reverse("analyzer"), {"url": "https://example.com"})
    assert response.status_code == 403


def test_analyzer_rejects_get_submission(client):
    response = client.delete(reverse("analyzer"))
    assert response.status_code == 405


# --- Language selector correctness -------------------------------------------

def _switch(client, lang):
    return client.get(reverse("set_language"), {"lang": lang, "next": "/"})


def _lang_options(html):
    """Map language code -> (class attribute, aria-current) of each selector option."""
    matches = re.findall(
        r'class="lang-option([^"]*)" aria-current="(\w+)" href="[^"]*lang=(\w{2})', html)
    return {lang: (classes, current) for classes, current, lang in matches}


def test_selecting_english_shows_english_on_every_page(client, mock_engine):
    submit(client, "https://example.com")
    analysis = Analysis.objects.get()
    _switch(client, "en")

    dash = client.get(reverse("dashboard")).content
    ana = client.get(reverse("analyzer")).content
    rep = client.get(reverse("reports")).content
    res = client.get(reverse("results", kwargs={"pk": analysis.pk})).content
    about = client.get(reverse("about")).content

    assert b"Dashboard" in dash and b"Websites Analyzed" in dash
    assert b"Analyze a Website" in ana and b"Website URL" in ana
    assert b"History of your SEO analyses" in rep
    assert b"SEO Analysis Results" in res and b"Individual Checks" in res
    assert b"About RankPilot" in about
    assert "Tableau de bord".encode() not in dash


def test_selecting_french_shows_french_on_every_page(client, mock_engine):
    submit(client, "https://example.com")
    analysis = Analysis.objects.get()
    _switch(client, "fr")

    dash = client.get(reverse("dashboard")).content
    ana = client.get(reverse("analyzer")).content
    rep = client.get(reverse("reports")).content
    res = client.get(reverse("results", kwargs={"pk": analysis.pk})).content
    about = client.get(reverse("about")).content

    assert "Tableau de bord".encode() in dash and "Sites web analysés".encode() in dash
    assert "Analyser un site web".encode() in ana and "URL du site web".encode() in ana
    assert "Historique de vos analyses SEO".encode() in rep
    assert "Résultats de l".encode() in res and "analyse SEO".encode() in res
    assert "Contrôles détaillés".encode() in res
    assert "À propos de RankPilot".encode() in about
    assert b"Dashboard" not in dash and b"Websites Analyzed" not in dash


def test_selector_highlights_the_active_language(client):
    options = _lang_options(client.get(reverse("dashboard")).content.decode())
    assert "active" in options["en"][0] and options["en"][1] == "true"
    assert "active" not in options["fr"][0] and options["fr"][1] == "false"

    _switch(client, "fr")
    options = _lang_options(client.get(reverse("dashboard")).content.decode())
    assert "active" in options["fr"][0] and options["fr"][1] == "true"
    assert "active" not in options["en"][0] and options["en"][1] == "false"


def test_french_persists_across_navigation_and_submission(client, mock_engine):
    _switch(client, "fr")
    assert "Tableau de bord".encode() in client.get(reverse("dashboard")).content

    response = submit(client, "https://example.com")
    analysis = Analysis.objects.get()
    results = client.get(response["Location"]).content
    assert "Résultats de l".encode() in results and "analyse SEO".encode() in results

    reports = client.get(reverse("reports")).content
    assert "Rapports".encode() in reports and "Terminée".encode() in reports
    assert client.session["rankpilot_lang"] == "fr"


def test_results_switch_language_without_rerunning_analysis(client, mock_engine, monkeypatch):
    submit(client, "https://example.com")
    analysis = Analysis.objects.get()

    calls = {"count": 0}
    original = services.analyze

    def counting_analyze(url, translator, session=None):
        calls["count"] += 1
        return original(url, translator, session=session)

    monkeypatch.setattr(services, "analyze", counting_analyze)

    english = client.get(reverse("results", kwargs={"pk": analysis.pk})).content
    assert b"Individual Checks" in english

    _switch(client, "fr")
    french = client.get(reverse("results", kwargs={"pk": analysis.pk})).content
    assert "Contrôles détaillés".encode() in french and "Méta-description".encode() in french
    assert calls["count"] == 0


# --- Favicon ------------------------------------------------------------------

def test_templates_reference_favicon_assets(client):
    for url in (reverse("dashboard"), reverse("analyzer"), reverse("reports"),
                reverse("about")):
        html = client.get(url).content.decode()
        for asset in ("favicons/favicon.svg", "favicons/favicon-32x32.png",
                      "favicons/favicon-16x16.png", "favicons/favicon.ico",
                      "favicons/apple-touch-icon.png"):
            assert asset in html


class FaviconServingTests(StaticLiveServerTestCase):
    def test_favicon_files_are_served(self):
        import urllib.request

        for path, prefix in (("static/favicons/favicon.svg", b"<svg"),
                             ("static/favicons/favicon-32x32.png", b"\x89PNG"),
                             ("static/favicons/favicon-16x16.png", b"\x89PNG"),
                             ("static/favicons/favicon.ico", b"\x00\x00"),
                             ("static/favicons/apple-touch-icon.png", b"\x89PNG")):
            with urllib.request.urlopen(f"{self.live_server_url}/{path}") as response:
                body = response.read()
            assert response.status == 200
            assert body.startswith(prefix)
