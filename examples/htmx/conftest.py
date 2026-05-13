"""pytest bootstrap for the htmx example.

Makes ``example_project``, ``books``, ``htmx_fragments`` importable and
points Django at the example project's settings. The Django ORM check for
async context is relaxed for the same reason the parent test_project does
it — pytest-playwright (if ever wired up here) runs in an event loop.
"""

import os
import sys

ROOT = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.abspath(os.path.join(ROOT, "..", "..")))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "example_project.settings")
os.environ.setdefault("DJANGO_ALLOW_ASYNC_UNSAFE", "true")
