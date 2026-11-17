"""Views of the RankPilot web application."""

from __future__ import annotations

import csv
import io

from django.contrib import messages
from django.core.paginator import Paginator
from django.http import HttpResponse, HttpResponseNotFound
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_GET, require_http_methods

from rankpilot.i18n import SUPPORTED_LANGUAGES
from rankpilot.reporter import csv_rows
from rankpilot.utils import FetchError, InvalidURLError

from .models import Analysis
from .security import SSRFError
from .services import localized_results, perform_analysis, rebuild_audit
from .translations import LANG_SESSION_KEY, WebTranslator

REPORTS_PER_PAGE = 10


def _translator(request) -> WebTranslator:
    lang = request.session.get(LANG_SESSION_KEY, "en")
    return WebTranslator(lang if lang in SUPPORTED_LANGUAGES else "en")


def _safe_next(request) -> str:
    target = request.GET.get("next", "")
    if target and url_has_allowed_host_and_scheme(target, allowed_hosts=None):
        return target
    return reverse("dashboard")


@require_GET
def dashboard(request):
    analyses = Analysis.objects.all()
    successful = analyses.filter(status=Analysis.STATUS_SUCCESS)

    stats = {
        "sites": analyses.values("domain").distinct().count(),
        "average_score": round(sum(a.score for a in successful if a.score is not None)
                               / successful.count()) if successful.count() else None,
        "issues": sum(a.issues for a in successful),
        "successful": successful.count(),
    }
    context = {
        "active": "dashboard",
        "stats": stats,
        "recent": analyses[:5],
    }
    return render(request, "dashboard.html", context)


@require_http_methods(["GET", "POST"])
def analyzer(request):
    t = _translator(request)
    if request.method == "GET":
        return render(request, "analyzer.html", {"active": "analyzer"})

    raw_url = (request.POST.get("url") or "").strip()
    try:
        analysis = perform_analysis(raw_url)
    except (InvalidURLError, SSRFError) as error:
        messages.error(request, t.t(str(error)))
        return redirect("analyzer")
    except FetchError as error:
        messages.error(request, t.t(error.message_key))
        return redirect("analyzer")

    if analysis.succeeded:
        messages.success(request, t.t("msg_analysis_saved"))
    else:
        messages.error(request, t.t("msg_analysis_failed"))
    return redirect("results", pk=analysis.pk)


@require_GET
def results(request, pk: int):
    t = _translator(request)
    analysis = get_object_or_404(Analysis, pk=pk)
    error_message = ""
    if analysis.error_key:
        if analysis.error_key == "err_http_status":
            error_message = t.t(analysis.error_key, status=analysis.http_status)
        else:
            error_message = t.t(analysis.error_key)
    context = {
        "active": "",
        "analysis": analysis,
        "error_message": error_message,
        "checks": localized_results(analysis, t) if analysis.succeeded else [],
    }
    return render(request, "results.html", context)


@require_GET
def reports(request):
    paginator = Paginator(Analysis.objects.all(), REPORTS_PER_PAGE)
    page = paginator.get_page(request.GET.get("page"))
    return render(request, "reports.html", {"active": "reports", "page": page})


@require_GET
def report_csv(request, pk: int):
    t = _translator(request)
    analysis = get_object_or_404(Analysis, pk=pk)
    if not analysis.succeeded:
        return HttpResponseNotFound(t.t("res_error_title"))

    audit = rebuild_audit(analysis, t)
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerows(csv_rows(audit, t))

    response = HttpResponse(buffer.getvalue().encode("utf-8-sig"),
                            content_type="text/csv; charset=utf-8")
    filename = f"seo-report-{analysis.domain}-{analysis.created_at:%Y%m%d-%H%M%S}.csv"
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response


@require_GET
def set_language(request):
    lang = request.GET.get("lang", "en")
    request.session[LANG_SESSION_KEY] = lang if lang in SUPPORTED_LANGUAGES else "en"
    return redirect(_safe_next(request))


@require_GET
def about(request):
    return render(request, "about.html", {"active": "about"})
