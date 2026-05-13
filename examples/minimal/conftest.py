"""pytest bootstrap for the Foundation (minimal) example.

Wires Django + makes the local `books` / `example_project` packages
importable when pytest is run from this directory.
"""

import os
import sys

ROOT = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.abspath(os.path.join(ROOT, "..", "..")))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "example_project.settings")
os.environ.setdefault("DJANGO_ALLOW_ASYNC_UNSAFE", "true")
