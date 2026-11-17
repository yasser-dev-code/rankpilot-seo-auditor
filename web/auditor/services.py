"""Bridge between the shared RankPilot SEO engine and the Django app.

The web interface never reimplements SEO logic: it calls the very same
``rankpilot.analyzer.analyze`` used by the CLI, through an SSRF-safe
session, then persists a language-neutral snapshot of the results.
"""

from __future__ import annotations

from urllib.parse import urlparse

from rankpilot.analyzer import AuditResult, analyze
from rankpilot.checks import CheckResult, ExtraRow
from rankpilot.i18n import FAIL, PASS, WARN, Translator
from rankpilot.utils import normalize_url

from .models import Analysis
from .security import SSRFSafeSession, assert_public_url

SCORE_PASS = 1.0
SCORE_WARN = 0.5


def compute_score(results) -> int | None:
    """RankPilot SEO score out of 100.

    Each counted check contributes equally: PASS = full points,
    WARN = half points, FAIL = zero. The score is an internal quality
    indicator computed from the seven checks, not an official ranking.
    """
    counted = [r for r in results if r.counted]
    if not counted:
        return None
    points = sum(SCORE_PASS if r.status == PASS else
                 SCORE_WARN if r.status == WARN else 0.0
                 for r in counted)
    return round(100 * points / len(counted))


def _serialize_results(audit: AuditResult) -> list[dict]:
    serialized = []
    for result in audit.results:
        serialized.append({
            "check_key": result.check_key,
            "status": result.status,
            "detail_key": result.detail_key,
            "detail_params": result.detail_params,
            "counted": result.counted,
            "http_status": result.http_status,
            "truncated": result.truncated,
            "limit": result.limit,
            "extra_rows": [
                {"status": row.status, "url": row.related_url,
                 "http_status": row.http_status, "check_key": row.check_key}
                for row in result.extra_rows
            ],
        })
    return serialized


def _detected_content(audit: AuditResult) -> dict:
    """Pull the detected title / meta description / H1 out of the results."""
    content = {"page_title": "", "meta_description": "", "h1": ""}
    for result in audit.results:
        if result.check_key == "check_title" and result.status == PASS:
            content["page_title"] = result.detail_params.get("value", "")
        if result.check_key == "check_meta" and result.status == PASS:
            content["meta_description"] = result.detail_params.get("value", "")
        if result.check_key == "check_h1" and result.status in (PASS, WARN):
            content["h1"] = result.detail_params.get("value") or \
                result.detail_params.get("first", "")
    return content


def perform_analysis(raw_url: str) -> Analysis:
    """Validate, fetch, analyze and persist one website analysis.

    Raises InvalidURLError / SSRFError / FetchError for input, security
    and network problems; callers turn them into localized messages.
    A website that answers with an HTTP error status is stored as a
    failed analysis instead of raising.
    """
    url = normalize_url(raw_url)
    assert_public_url(url)

    audit = analyze(url, Translator("en"), session=SSRFSafeSession())
    domain = urlparse(url).hostname or url

    if not audit.succeeded:
        return Analysis.objects.create(
            url=url, domain=domain, status=Analysis.STATUS_ERROR,
            http_status=audit.http_status, error_key=audit.error_key,
        )

    counted = [r for r in audit.results if r.counted]
    broken_links = [
        {"url": row.related_url, "status": row.http_status}
        for result in audit.results
        for row in result.extra_rows
    ]
    content = _detected_content(audit)

    return Analysis.objects.create(
        url=url,
        domain=domain,
        status=Analysis.STATUS_SUCCESS,
        http_status=audit.http_status,
        score=compute_score(audit.results),
        passed=sum(1 for r in counted if r.status == PASS),
        failed=sum(1 for r in counted if r.status == FAIL),
        warnings=sum(1 for r in counted if r.status == WARN),
        results=_serialize_results(audit),
        broken_links=broken_links,
        page_title=content["page_title"],
        meta_description=content["meta_description"],
        h1=content["h1"],
    )


def rebuild_audit(analysis: Analysis, translator) -> AuditResult:
    """Rebuild an engine AuditResult from stored data (CSV downloads)."""
    results = [
        CheckResult(
            check_key=item["check_key"],
            status=item["status"],
            detail_key=item["detail_key"],
            detail_params=item.get("detail_params", {}),
            counted=item.get("counted", True),
            http_status=item.get("http_status", ""),
            truncated=item.get("truncated", False),
            limit=item.get("limit", 0),
            extra_rows=[
                ExtraRow(status=row["status"],
                         details=translator.t("link_broken_item",
                                              url=row["url"], status=row["http_status"]),
                         related_url=row["url"],
                         http_status=row["http_status"],
                         check_key=row.get("check_key"))
                for row in item.get("extra_rows", [])
            ],
            translator=translator._engine if hasattr(translator, "_engine") else translator,
        )
        for item in analysis.results
    ]
    return AuditResult(url=analysis.url, analyzed_at=analysis.created_at,
                       http_status=analysis.http_status, results=results)


def localized_results(analysis: Analysis, translator) -> list[dict]:
    """Render stored results for display in the request language."""
    rendered = []
    for item in analysis.results:
        if not item.get("counted", True):
            continue
        rendered.append({
            "check_key": item["check_key"],
            "name": translator.t(item["check_key"]),
            "status": item["status"],
            "status_label": translator.status_label(item["status"]),
            "details": translator.t(item["detail_key"], **item.get("detail_params", {}))
                       + (translator.t("links_truncated", limit=item["limit"])
                          if item.get("truncated") else ""),
            "extra_rows": [
                {"url": row["url"], "status": row["http_status"]}
                for row in item.get("extra_rows", [])
            ],
        })
    return rendered
