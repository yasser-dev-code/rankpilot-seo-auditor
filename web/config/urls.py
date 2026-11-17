"""Root URL configuration for the RankPilot web application."""

from django.urls import include, path

urlpatterns = [
    path("", include("auditor.urls")),
]
