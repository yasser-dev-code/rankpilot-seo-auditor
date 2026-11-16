"""RankPilot — Website SEO Auditor: command-line entry point.

Usage examples:
    python main.py --url https://example.com --lang en
    python main.py --url https://example.com --lang fr
    python main.py            (interactive mode)
"""

from __future__ import annotations

import argparse
import sys

from rankpilot import __version__
from rankpilot.analyzer import AuditResult, analyze
from rankpilot.i18n import (DEFAULT_LANGUAGE, FAIL, PASS, SUPPORTED_LANGUAGES,
                            WARN, Translator)
from rankpilot.reporter import build_report_path, write_csv_report
from rankpilot.utils import DEFAULT_TIMEOUT, InvalidURLError, normalize_url

WIDTH = 58
THICK_RULE = "=" * WIDTH
THIN_RULE = "-" * WIDTH

# argparse emits a few built-in strings ("usage:", "options:", ...) through the
# gettext hook below so the whole help screen can be localized.
ARGPARSE_BOILERPLATE = {
    "en": {},
    "fr": {
        "usage: ": "usage : ",
        "%(heading)s:": "%(heading)s :",
        "options": "options",
        "positional arguments": "arguments positionnels",
        "show this help message and exit": "affiche ce message d'aide et quitte",
    },
}


def _detect_language(argv: list[str]) -> str:
    """Read --lang before argparse runs, so the help text is localized too."""
    for index, arg in enumerate(argv):
        if arg.startswith("--lang="):
            value = arg.split("=", 1)[1]
            return value if value in SUPPORTED_LANGUAGES else DEFAULT_LANGUAGE
        if arg == "--lang" and index + 1 < len(argv):
            value = argv[index + 1]
            return value if value in SUPPORTED_LANGUAGES else DEFAULT_LANGUAGE
    return DEFAULT_LANGUAGE


def build_parser(lang: str) -> argparse.ArgumentParser:
    import argparse as argparse_module

    table = ARGPARSE_BOILERPLATE.get(lang, {})
    argparse_module._ = lambda text: table.get(text, text)

    t = Translator(lang)
    parser = argparse.ArgumentParser(
        prog="rankpilot",
        description=t.t("help_description"),
    )
    parser.add_argument("--url", help=t.t("help_url"))
    parser.add_argument("--lang", choices=SUPPORTED_LANGUAGES, default=DEFAULT_LANGUAGE,
                        help=t.t("help_lang"))
    parser.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT,
                        help=t.t("help_timeout"))
    parser.add_argument("--reports-dir", default="reports", help=t.t("help_reports_dir"))
    parser.add_argument("--version", action="version",
                        version=f"RankPilot {__version__}", help=t.t("help_version"))
    return parser


def _prompt_url(t: Translator) -> str:
    """Interactive mode: ask the user for the URL to analyze."""
    print(THICK_RULE)
    print(f" {t.t('app_title')}")
    print(THICK_RULE)
    print()
    try:
        return input(f"{t.t('prompt_url')} {t.t('prompt_hint')}: ").strip()
    except (EOFError, KeyboardInterrupt):
        print()
        return ""


def _section(title: str) -> None:
    print(THIN_RULE)
    print(f" {title}")
    print(THIN_RULE)
    print()


def print_audit(audit: AuditResult, t: Translator, csv_path) -> None:
    """Render the full terminal report for a successful audit."""
    counted = [r for r in audit.results if r.counted]
    passed = sum(1 for r in counted if r.status == PASS)
    failed = sum(1 for r in counted if r.status == FAIL)
    warnings = sum(1 for r in counted if r.status == WARN)
    issues = failed + warnings

    label_width = max(len(t.t(r.check_key)) for r in counted) + 2

    print(THICK_RULE)
    print(f" {t.t('app_title')}")
    print(THICK_RULE)
    print()
    header_labels = [t.t("lbl_website"), t.t("lbl_date"), t.t("lbl_http_status")]
    header_width = max(len(label) for label in header_labels) + 2
    print(f"{t.t('lbl_website')}:".ljust(header_width) + audit.url)
    print(f"{t.t('lbl_date')}:".ljust(header_width)
          + audit.analyzed_at.strftime("%Y-%m-%d %H:%M:%S"))
    print(f"{t.t('lbl_http_status')}:".ljust(header_width) + str(audit.http_status))
    print()
    _section(t.t("sec_results"))

    for result in counted:
        name = t.t(result.check_key)
        status = t.status_label(result.status)
        print(f"{name + ':'.ljust(label_width - len(name))}{status}")
        if result.details:
            print(f"  {result.details}")
        for row in result.extra_rows:
            if row.related_url:
                print(f"  - {row.details}")
        print()

    _section(t.t("sec_summary"))
    summary_labels = [t.t("lbl_passed"), t.t("lbl_failed"), t.t("lbl_warnings")]
    summary_width = max(len(label) for label in summary_labels) + 2
    print(f"{t.t('lbl_passed')}:".ljust(summary_width) + str(passed))
    print(f"{t.t('lbl_failed')}:".ljust(summary_width) + str(failed))
    print(f"{t.t('lbl_warnings')}:".ljust(summary_width) + str(warnings))
    print()
    print(f"{t.t('lbl_issues')}: {issues}")
    print()
    print(f"{t.t('lbl_csv')}: {csv_path}")


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)

    # French accents and the em dash must survive any Windows console codepage.
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")

    parser = build_parser(_detect_language(argv))
    args = parser.parse_args(argv)
    t = Translator(args.lang)

    url = args.url
    if not url:
        url = _prompt_url(t)
        if not url:
            print(t.t("cancelled"))
            return 2

    try:
        url = normalize_url(url)
    except InvalidURLError as error:
        print(f"{t.t(str(error))}", file=sys.stderr)
        return 2

    audit = analyze(url, t, timeout=args.timeout)
    if not audit.succeeded:
        message = t.t(audit.error_key, status=audit.error_detail) \
            if audit.error_key == "err_http_status" else t.t(audit.error_key)
        print(f"{t.t('app_title')}", file=sys.stderr)
        print(f"{message}", file=sys.stderr)
        if audit.error_detail and audit.error_key != "err_http_status":
            print(f"{t.t('err_analysis_failed', detail=audit.error_detail[:200])}",
                  file=sys.stderr)
        return 1

    csv_path = build_report_path(audit.url, audit.analyzed_at, args.reports_dir)
    write_csv_report(audit, csv_path, t)
    print_audit(audit, t, csv_path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
