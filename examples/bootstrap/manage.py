#!/usr/bin/env python
"""Django management entry point for the Bootstrap 5 + jQuery example.

Prepends the multiseek source tree to sys.path so this project runs against
the in-repo package without an install step.
"""

import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parent.parent
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(HERE))

if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "example_project.settings")

    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)
