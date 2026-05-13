"""Minimal setup.py — only custom build commands for locale compilation.

All package metadata lives in pyproject.toml. This file exists solely to
ensure ``django-admin compilemessages`` runs during wheel/sdist builds.
"""

import logging
import os

from setuptools import Command, setup
from setuptools.command.build_py import build_py as _build_py

logger = logging.getLogger(__name__)


class compile_translations(Command):
    description = "compile message catalogs to MO files via django compilemessages"
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        locale_dir = os.path.join(os.path.dirname(__file__), "multiseek")
        if not os.path.isdir(locale_dir):
            logger.warning("multiseek directory not found, skipping compilemessages")
            return

        curdir = os.getcwd()
        os.chdir(locale_dir)
        try:
            from django.core.management import call_command

            call_command("compilemessages")
        except Exception as exc:
            logger.warning("compilemessages failed: %s", exc)
        finally:
            os.chdir(curdir)


class build_py(_build_py):
    """Run compilemessages before collecting Python files."""

    def run(self):
        self.run_command("compile_translations")
        _build_py.run(self)


setup(
    cmdclass={
        "compile_translations": compile_translations,
        "build_py": build_py,
    },
)
