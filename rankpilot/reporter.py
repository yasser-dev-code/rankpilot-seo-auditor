"""CSV report generation.

Reports are written with UTF-8 BOM (``utf-8-sig``) so French accents open
correctly in Microsoft Excel. One row per check, plus one identifiable row
per broken internal link.
"""

from __future__ import annotations

import csv
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

from .analyzer import AuditResult
from .i18n import Translator

CSV_HEADER_KEYS = ("csv_website", "csv_date", "csv_check", "csv_status",
                   "csv_details", "csv_related_url", "csv_http_status")


def build_report_path(url: str, analyzed_at: datetime, reports_dir: str = "reports") -> Path:
    """Build a report path like reports/seo-report-example.com-20261116-230512.csv."""
    hostname = urlparse(url).hostname or "site"
    timestamp = analyzed_at.strftime("%Y%m%d-%H%M%S")
    directory = Path(reports_dir)
    directory.mkdir(parents=True, exist_ok=True)
    return directory / f"seo-report-{hostname}-{timestamp}.csv"


def write_csv_report(audit: AuditResult, path: Path, translator: Translator) -> Path:
    """Write the full CSV report for a successful audit and return its path."""
    date_text = audit.analyzed_at.strftime("%Y-%m-%d %H:%M:%S")

    with open(path, "w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.writer(handle)
        writer.writerow([translator.t(key) for key in CSV_HEADER_KEYS])

        for result in audit.results:
            writer.writerow([
                audit.url,
                date_text,
                translator.t(result.check_key),
                translator.status_label(result.status),
                result.details,
                "",
                result.http_status,
            ])
            for row in result.extra_rows:
                writer.writerow([
                    audit.url,
                    date_text,
                    translator.t(row.check_key or result.check_key),
                    translator.status_label(row.status),
                    row.details,
                    row.related_url,
                    row.http_status,
                ])
    return path
