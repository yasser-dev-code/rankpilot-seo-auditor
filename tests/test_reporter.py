"""Tests for CSV report generation (reporter.py)."""

import csv
from datetime import datetime

from rankpilot.analyzer import AuditResult
from rankpilot.checks import CheckResult, ExtraRow
from rankpilot.i18n import FAIL, PASS, Translator
from rankpilot.reporter import build_report_path, write_csv_report


def make_audit(url="https://example.com"):
    translator = Translator("en")
    audit = AuditResult(url=url, analyzed_at=datetime(2026, 11, 16, 23, 5, 12),
                        http_status=200)
    audit.results = [
        CheckResult("check_title", PASS, "title_ok", {"value": "Example"},
                    translator=translator),
        CheckResult("check_links", FAIL, "links_broken", {"broken": 1, "count": 2},
                    extra_rows=[ExtraRow(status=FAIL,
                                         details="https://example.com/gone -> 404",
                                         related_url="https://example.com/gone",
                                         http_status="404",
                                         check_key="csv_broken_link")],
                    translator=translator),
    ]
    return audit


def test_report_filename_contains_domain_and_timestamp(tmp_path):
    path = build_report_path("https://example.com/page",
                             datetime(2026, 11, 16, 23, 5, 12),
                             reports_dir=str(tmp_path))
    assert path.name == "seo-report-example.com-20261116-230512.csv"
    assert path.parent == tmp_path


def test_reports_directory_is_created(tmp_path):
    target = tmp_path / "nested" / "reports"
    path = build_report_path("https://example.com", datetime(2026, 1, 1),
                             reports_dir=str(target))
    assert target.is_dir()
    assert path.parent == target


def test_csv_is_valid_and_complete(tmp_path):
    translator = Translator("en")
    path = tmp_path / "report.csv"
    write_csv_report(make_audit(), path, translator)

    with open(path, newline="", encoding="utf-8-sig") as handle:
        rows = list(csv.reader(handle))

    assert rows[0] == ["Website", "Analysis date", "Check", "Status",
                       "Details", "Related URL", "HTTP status"]
    assert rows[1] == ["https://example.com", "2026-11-16 23:05:12",
                       "Page Title", "PASS", 'Title found: "Example"', "", ""]
    # Broken links appear as identifiable rows, not just a total number.
    assert rows[3] == ["https://example.com", "2026-11-16 23:05:12",
                       "Broken Internal Link", "FAIL",
                       "https://example.com/gone -> 404",
                       "https://example.com/gone", "404"]


def test_csv_uses_utf8_bom_for_excel(tmp_path):
    translator = Translator("fr")
    path = tmp_path / "report-fr.csv"
    write_csv_report(make_audit(), path, translator)

    raw = path.read_bytes()
    assert raw.startswith(b"\xef\xbb\xbf")

    with open(path, newline="", encoding="utf-8-sig") as handle:
        rows = list(csv.reader(handle))
    assert rows[0][0] == "Site web"
    assert rows[1][3] == "RÉUSSI"  # French accents decode correctly
