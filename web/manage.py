#!/usr/bin/env python
"""Django management entry point for the RankPilot web application."""

import os
import sys
from pathlib import Path


def main():
    # Make the repository root importable so the shared `rankpilot`
    # SEO engine package can be used by the Django application.
    repo_root = Path(__file__).resolve().parent.parent
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
