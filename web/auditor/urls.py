"""URL routes of the RankPilot web application."""

from django.urls import path

from . import views

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("analyze/", views.analyzer, name="analyzer"),
    path("results/<int:pk>/", views.results, name="results"),
    path("reports/", views.reports, name="reports"),
    path("reports/<int:pk>/csv/", views.report_csv, name="report_csv"),
    path("language/", views.set_language, name="set_language"),
    path("about/", views.about, name="about"),
]
