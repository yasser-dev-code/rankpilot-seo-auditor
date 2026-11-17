"""Persistence model for completed RankPilot SEO analyses."""

from __future__ import annotations

from django.db import models
from django.urls import reverse


class Analysis(models.Model):
    """One completed (or failed) SEO analysis of a website."""

    STATUS_SUCCESS = "success"
    STATUS_ERROR = "error"
    STATUS_CHOICES = [
        (STATUS_SUCCESS, "Success"),
        (STATUS_ERROR, "Error"),
    ]

    url = models.URLField(max_length=2048)
    domain = models.CharField(max_length=253, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    status = models.CharField(max_length=16, choices=STATUS_CHOICES,
                              default=STATUS_SUCCESS)
    http_status = models.PositiveIntegerField(null=True, blank=True)
    score = models.PositiveIntegerField(null=True, blank=True)
    passed = models.PositiveIntegerField(default=0)
    failed = models.PositiveIntegerField(default=0)
    warnings = models.PositiveIntegerField(default=0)
    error_key = models.CharField(max_length=64, blank=True, default="")

    # Language-neutral engine output: one entry per check with
    # check_key, status, detail_key, detail_params, http_status and
    # extra_rows (broken links: url + status).
    results = models.JSONField(default=list, blank=True)
    broken_links = models.JSONField(default=list, blank=True)

    page_title = models.TextField(blank=True, default="")
    meta_description = models.TextField(blank=True, default="")
    h1 = models.TextField(blank=True, default="")

    class Meta:
        ordering = ["-created_at"]
        verbose_name_plural = "analyses"

    def __str__(self) -> str:
        return f"{self.domain} @ {self.created_at:%Y-%m-%d %H:%M}"

    @property
    def succeeded(self) -> bool:
        return self.status == self.STATUS_SUCCESS

    @property
    def issues(self) -> int:
        return self.failed + self.warnings

    def get_absolute_url(self) -> str:
        return reverse("results", kwargs={"pk": self.pk})
